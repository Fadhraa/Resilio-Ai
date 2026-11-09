"""
Supplier Management & CRUD Handler for ResilioAI Cognitive Agent.
Menangani:
1. Menampilkan katalog rekanan terdaftar dari SQLite.
2. Draf preview pendaftaran baru (Register), pembaruan data (Update), dan penonaktifan/penghapusan (Soft/Hard Delete).
3. Otorisasi konfirmasi CRUD oleh Kepala SPPG (Human-in-the-Loop).
"""

from datetime import datetime, timezone
import re
from typing import Any, Callable, Dict, List, Optional
from app.data.sqlite_db import get_all_suppliers, get_all_inventory_items
from app.models.schemas import (
    ChatActionRequired,
    ChatIntent,
    ChatRequest,
    ChatResponse,
    SupplierCreateRequest,
    SupplierRecord,
    SupplierUpdateRequest,
)
from app.engine.tools import (
    deactivate_supplier_tool,
    delete_supplier_permanently_tool,
    register_supplier_tool,
    update_supplier_tool,
)
from app.engine.agent.prompts import SYSTEM_PROMPTS
from app.engine.agent.parsers import match_supplier_in_text, infer_commodity_and_category, parse_supplier_create_data


def handle_list_suppliers(
    session: Dict[str, Any],
    request: ChatRequest,
    params: Dict[str, Any],
    call_gemini_adaptive: Callable[..., str],
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
    """Menangani permintaan daftar rekanan (LIST_SUPPLIERS) langsung dari SQLite."""
    commodity_filter = params.get("commodity")
    db_sups = get_all_suppliers(include_inactive=False, commodity=commodity_filter)
    suppliers = [SupplierRecord.model_validate(s) for s in db_sups]

    lines = [f"Saat ini terdapat **{len(suppliers)} rekanan supplier** yang terdaftar di basis data SPPG:\n"]
    for idx, s in enumerate(suppliers, 1):
        halal_badge = "Halal Aktif ✅" if s.halal_certified else "Belum Halal ❌"
        is_utama = " (Supplier Utama SPPG)" if "utama" in s.supplier_id.lower() else ""
        comm = getattr(s, "commodity", s.category)
        lines.append(
            f"{idx}. **{s.supplier_name}** (`{s.supplier_id}`){is_utama}\n"
            f"   • Komoditas: **{comm}** [{s.category}] | Sertifikasi: {halal_badge}\n"
            f"   • Kapasitas Harian: {s.daily_capacity_kg} kg/hari | Harga: Rp {s.unit_price_idr:,.2f}/kg\n"
            f"   • Estimasi Tiba: {s.lead_time_hours} jam | Jarak: {s.distance_km} km | Rating: {s.reliability_rating}/100"
        )
    fallback = "\n".join(lines)
    adaptive_reply = call_gemini_adaptive(
        system_instructions=SYSTEM_PROMPTS["SUPPLIER_INQUIRY"],
        user_message=request.message,
        context_data="\n".join([f"{s.supplier_id}: {s.supplier_name}, Komoditas={s.commodity}, Halal={s.halal_certified}, Kapasitas={s.daily_capacity_kg}kg, Harga=Rp {s.unit_price_idr}" for s in suppliers]),
        fallback_text=fallback,
        history=session.get("history", []),
    )
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=adaptive_reply,
            intent=ChatIntent.GENERAL_INQUIRY,
            action_required=ChatActionRequired.NONE,
            preview_data={"suppliers": [s.model_dump() for s in suppliers]},
        ),
    )


def handle_supplier_management(
    session: Dict[str, Any],
    request: ChatRequest,
    action: str,
    params: Dict[str, Any],
    call_gemini_adaptive: Callable[..., str],
    respond: Callable[..., ChatResponse],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash-lite",
) -> ChatResponse:
    """Menangani pembuatan draf preview CRUD supplier (REGISTER_SUPPLIER, UPDATE_SUPPLIER, DEACTIVATE_SUPPLIER)."""
    user_msg = request.message.strip()

    # 1. DEACTIVATE / DELETE PREVIEW (Human-in-the-Loop)
    if action in ["DEACTIVATE_SUPPLIER", "DELETE_SUPPLIER"]:
        matched = None
        if params.get("supplier_name_or_id"):
            matched = match_supplier_in_text(str(params["supplier_name_or_id"]))
        if not matched:
            matched = match_supplier_in_text(user_msg)

        if not matched:
            return respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=(
                        "Bapak Adam, saya tidak menemukan nama atau ID rekanan supplier yang dimaksud dalam basis data SPPG.\n\n"
                        "Mohon sebutkan nama lengkap atau ID rekanan (contoh: `SUP-REG-02` atau `Ternak Rumahan Pak Budi`)."
                    ),
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                ),
            )

        sid, supplier = matched
        reason = params.get("reason") or "Penonaktifan administratif oleh pimpinan SPPG"
        commodity_name = getattr(supplier, "commodity", supplier.category)

        session["pending_crud"] = {
            "type": "MANAGE_SUPPLIER_DELETE",
            "supplier_id": sid,
            "supplier_name": supplier.supplier_name,
            "commodity": commodity_name,
            "reason": reason,
        }

        preview_text = (
            f"⚠️ **Konfirmasi Pengelolaan Rekanan SPPG**\n\n"
            f"Bapak Adam Dzaki, sistem mendeteksi instruksi penghapusan atau penonaktifan rekanan:\n"
            f"• Nama Rekanan: **{supplier.supplier_name}** (`{sid}`)\n"
            f"• Komoditas Pangan: **{commodity_name}** [{supplier.category}]\n"
            f"• Alasan: {reason}\n\n"
            f"Mohon konfirmasi jenis tindakan yang ingin diterapkan pada basis data SQLite SPPG:\n"
            f"1. **Hapus Permanen (Database)**: Menghapus baris rekanan secara fisik dari tabel suppliers di SQLite.\n"
            f"2. **Nonaktifkan Saja (Soft Delete)**: Mengubah status menjadi NON-AKTIF (`is_active = 0`) agar rekam jejak audit anggaran masa lalu tetap tersimpan.\n\n"
            f"Silakan klik salah satu tombol aksi di bawah atau ketik pilihan Bapak (*'Hapus permanen'* / *'Nonaktifkan'* / *'Batal'*)."
        )
        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=user_msg,
            context_data=(
                f"Tahap: Konfirmasi Penghapusan/Penonaktifan Rekanan. "
                f"Target Rekanan: {supplier.supplier_name} ({sid}), Komoditas: {commodity_name}. Alasan: {reason}. "
                f"Sistem telah menyiapkan opsi Hapus Permanen (Database) dan Nonaktifkan Saja (Soft Delete) via kartu konfirmasi."
            ),
            fallback_text=preview_text,
            history=session.get("history", []),
            target_sup_name=supplier.supplier_name,
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={
                    "action": "PREVIEW_DEACTIVATE",
                    "supplier_id": sid,
                    "supplier_name": supplier.supplier_name,
                    "confirm_supplier_action": {
                        "action_type": "DELETE_OR_DEACTIVATE",
                        "supplier_id": sid,
                        "supplier_name": supplier.supplier_name,
                        "commodity": commodity_name,
                        "title": f"Penghapusan Rekanan #{sid}",
                        "details": f"{supplier.supplier_name} ({sid}) - {commodity_name}",
                        "warning": "Penghapusan permanen akan menghapus data dari basis data SQLite SPPG.",
                    }
                },
            ),
        )

    # 2. UPDATE PREVIEW
    if action == "UPDATE_SUPPLIER":
        matched = None
        if params.get("supplier_name_or_id"):
            matched = match_supplier_in_text(str(params["supplier_name_or_id"]))
        if not matched:
            matched = match_supplier_in_text(user_msg)

        if not matched:
            fallback = (
                "Saya belum dapat mengidentifikasi rekanan yang ingin Anda perbarui datanya.\n\n"
                "Mohon sebutkan nama rekanan terdaftar atau ID-nya beserta data yang ingin diubah "
                "(misal: *'Update harga PT Berkah Unggas Jaya menjadi Rp 36.500'*)."
            )
            return respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=fallback,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                ),
            )

        sid, supplier = matched
        new_price = None
        if params.get("unit_price_idr") is not None:
            try:
                new_price = float(params["unit_price_idr"])
            except (ValueError, TypeError):
                pass
        if new_price is None:
            price_match = re.search(r"(?:harga|rp|menjadi|jadi|sebesar|@)\s*([0-9\.\,]+)", user_msg, re.IGNORECASE)
            if price_match:
                try:
                    new_price = float(price_match.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    pass

        new_capacity = None
        if params.get("daily_capacity_kg") is not None:
            try:
                new_capacity = float(params["daily_capacity_kg"])
            except (ValueError, TypeError):
                pass
        if new_capacity is None:
            cap_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:kg|kilo)", user_msg, re.IGNORECASE)
            if cap_match:
                try:
                    new_capacity = float(cap_match.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    pass

        new_lead_time = None
        if params.get("lead_time_hours") is not None:
            try:
                new_lead_time = float(params["lead_time_hours"])
            except (ValueError, TypeError):
                pass
        if new_lead_time is None:
            lt_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*jam", user_msg, re.IGNORECASE)
            if lt_match:
                try:
                    new_lead_time = float(lt_match.group(1).replace(",", "."))
                except ValueError:
                    pass

        updates_dict = {}
        if new_price is not None:
            updates_dict["unit_price_idr"] = new_price
        if new_capacity is not None:
            updates_dict["daily_capacity_kg"] = new_capacity
        if new_lead_time is not None:
            updates_dict["lead_time_hours"] = new_lead_time

        if not updates_dict:
            fallback = f"Tidak ada data perubahan baru yang terdeteksi untuk rekanan **{supplier.supplier_name}**."
            return respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=fallback,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                ),
            )

        session["pending_crud"] = {
            "type": "UPDATE",
            "supplier_id": sid,
            "supplier_name": supplier.supplier_name,
            "updates": updates_dict,
        }

        changes_desc = []
        if new_price is not None:
            changes_desc.append(f"• Harga Penawaran: Rp {supplier.unit_price_idr:,.2f} ➡️ **Rp {new_price:,.2f} / kg**")
        if new_capacity is not None:
            changes_desc.append(f"• Kapasitas Harian: {supplier.daily_capacity_kg} kg ➡️ **{new_capacity} kg/hari**")
        if new_lead_time is not None:
            changes_desc.append(f"• Estimasi Tiba: {supplier.lead_time_hours} jam ➡️ **{new_lead_time} jam**")

        preview_text = (
            f"📋 **Konfirmasi Pembaruan Data Rekanan (Preview Perubahan)**\n\n"
            f"Halo Bapak/Ibu Kepala SPPG, mohon tinjau draf rencana perubahan data rekanan berikut:\n\n"
            f"• **Rekanan Target:** **{supplier.supplier_name}** (`{sid}`)\n"
            f"• **Komoditas Pangan:** **{supplier.commodity}**\n"
            f"• **Rencana Perubahan:**\n"
            + "\n".join(changes_desc) + "\n\n"
            f"---\n"
            f"Keputusan akhir berada di tangan Bapak/Ibu Kepala SPPG:\n"
            f"👉 Ketik **\"Setuju / Simpan\"** untuk menerapkan pembaruan ke basis data resmi SPPG.\n"
            f"👉 Ketik **\"Batal\"** untuk membatalkan perubahan ini."
        )
        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=user_msg,
            context_data=f"Tahap: Preview Update. Rekanan: {supplier.supplier_name} ({sid}). Perubahan: {changes_desc}. Menunggu persetujuan Kepala SPPG.",
            fallback_text=preview_text,
            history=session.get("history", []),
            target_sup_name=supplier.supplier_name,
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={"action": "PREVIEW_UPDATE", "supplier_id": sid, "updates": updates_dict},
            ),
        )

    # 3. REGISTER PREVIEW
    create_payload = None

    p_name = params.get("supplier_name")
    p_price = params.get("unit_price_idr") or params.get("price")
    p_cap = params.get("daily_capacity_kg") or params.get("capacity")

    if p_name and p_price and p_cap:
        try:
            p_halal = params.get("halal_certified")
            if p_halal is None:
                p_halal = True

            comm_raw = params.get("commodity")
            if comm_raw and str(comm_raw).strip().upper() not in ["NONE", "NULL", ""]:
                comm, cat, supp_items = infer_commodity_and_category(str(comm_raw), supplier_name=str(p_name))
            else:
                comm, cat, supp_items = infer_commodity_and_category(user_msg, supplier_name=str(p_name))

            cert = params.get("halal_cert_number") or params.get("cert_number")
            lead_t = float(params.get("lead_time_hours") or 3.0)
            dist = float(params.get("distance_km") or 15.0)

            create_payload = SupplierCreateRequest(
                supplier_name=str(p_name).strip(),
                category=cat,
                commodity=comm,
                supported_items=supp_items,
                halal_certified=bool(p_halal),
                halal_cert_number=str(cert).strip() if cert else None,
                unit_price_idr=float(p_price),
                daily_capacity_kg=float(p_cap),
                lead_time_hours=lead_t,
                distance_km=dist,
                reliability_rating=85.0,
            )
        except Exception:
            create_payload = None

    if not create_payload:
        create_payload = parse_supplier_create_data(user_msg, api_key=api_key, model_name=model_name)

    if not create_payload:
        fallback = (
            "Untuk mendaftarkan rekanan supplier baru ke basis data SPPG, mohon lengkapi informasi berikut:\n\n"
            "1. **Nama Rekanan/Badan Usaha** (misal: *CV Berkah Jaya Pangan*)\n"
            "2. **Komoditas Pangan** (misal: *Daging Ayam, Daging Sapi, Beras, Telur, Tahu*)\n"
            "3. **Harga Penawaran per kg** (misal: *Rp 18.000*)\n"
            "4. **Kapasitas Pasokan Harian** (misal: *200 kg*)\n"
            "5. **Status Sertifikasi Halal** (Nomor sertifikat halal jika ada)\n\n"
            "Contoh format perintah:\n"
            "👉 *\"Daftarkan supplier baru CV Berkah Tahu, tahu Rp 18.000, kapasitas 200 kg, halal ID3211\"*"
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=fallback,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.CLARIFICATION_NEEDED,
            ),
        )

    # Evaluasi Pagu SOP & Sertifikasi Halal untuk Preview
    matched_item = None
    comm_lower = create_payload.commodity.lower()
    db_items = get_all_inventory_items()
    for it in db_items:
        it_name = it.get("item_name", "").lower()
        it_id = it.get("item_id", "").lower()
        if comm_lower in it_name or comm_lower in it_id:
            matched_item = it
            break
    if not matched_item:
        for it in db_items:
            if create_payload.category.upper() == it.get("category", "").upper():
                matched_item = it
                break

    sop_max = matched_item.get("sop_max_price_per_kg", 40000.0) if matched_item else 40000.0
    exceeds_sop = create_payload.unit_price_idr > sop_max
    pagu_status = "Sesuai Pagu Anggaran SOP BGN (Aman) ✅" if not exceeds_sop else f"Melebihi Pagu SOP {matched_item.get('item_name', '') if matched_item else ''} (Maks: Rp {sop_max:,.2f}) ⚠️"
    halal_badge = f"Terverifikasi Aktif (No: {create_payload.halal_cert_number or 'Tercatat'}) ✅" if create_payload.halal_certified else "Belum Memiliki Sertifikat Halal ❌"

    session["pending_crud"] = {
        "type": "CREATE",
        "payload": create_payload.model_dump(),
    }

    preview_text = (
        f"📋 **Konfirmasi Draft Rekanan Baru (Preview Data)**\n\n"
        f"Halo Bapak/Ibu Kepala SPPG, draf data rekanan baru telah disiapkan untuk ditinjau:\n\n"
        f"• **Nama Rekanan:** **{create_payload.supplier_name}**\n"
        f"• **Komoditas Pangan:** **{create_payload.commodity}** [{create_payload.category}]\n"
        f"• **Harga Penawaran:** Rp {create_payload.unit_price_idr:,.2f} / kg\n"
        f"• **Kapasitas Pasokan:** {create_payload.daily_capacity_kg} kg/hari\n"
        f"• **Estimasi Tiba & Jarak:** {create_payload.lead_time_hours} jam | {create_payload.distance_km} km\n\n"
        f"🛡️ **Tinjauan Kepatuhan Regulasi SPPG:**\n"
        f"• **Sertifikasi Halal (UU JPH No. 33/2014):** {halal_badge}\n"
        f"• **Pagu Anggaran SOP BGN:** {pagu_status}\n\n"
        f"---\n"
        f"Keputusan akhir berada di tangan Bapak/Ibu Kepala SPPG:\n"
        f"👉 Ketik **\"Setuju / Simpan\"** untuk meresmikan ke basis data resmi SPPG.\n"
        f"👉 Ketik **\"Batal\"** jika ingin membatalkan pendaftaran ini."
    )

    adaptive_reply = call_gemini_adaptive(
        system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
        user_message=user_msg,
        context_data=(
            f"Tahap: Preview Draft Pendaftaran. Rekanan: {create_payload.supplier_name}, "
            f"Komoditas: {create_payload.commodity}, Harga: Rp {create_payload.unit_price_idr}, "
            f"Kapasitas: {create_payload.daily_capacity_kg} kg, Halal: {create_payload.halal_certified}. "
            f"Menunggu keputusan akhir persetujuan Kepala SPPG."
        ),
        fallback_text=preview_text,
        history=session.get("history", []),
        target_sup_name=create_payload.supplier_name,
    )
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=adaptive_reply,
            intent=ChatIntent.MANAGE_SUPPLIER,
            action_required=ChatActionRequired.APPROVAL_PENDING,
            preview_data={"action": "PREVIEW_CREATE", "draft": create_payload.model_dump()},
        ),
    )


def handle_crud_confirmation(
    session: Dict[str, Any],
    request: ChatRequest,
    is_confirm: bool,
    call_gemini_adaptive: Callable[..., str],
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
    """Menangani eksekusi atau pembatalan draf CRUD setelah keputusan Kepala SPPG (Human-in-the-Loop)."""
    pending = session.get("pending_crud")
    if not pending:
        from app.engine.agent.handlers.general_handler import handle_consultative_chat
        return handle_consultative_chat(session, request, call_gemini_adaptive, respond)

    crud_type = pending.get("type")

    # 1. JIKA KEPALA SPPG MEMBATALKAN
    if not is_confirm:
        session["pending_crud"] = None
        if crud_type == "APPROVE_MULTI_PO":
            cancel_msg = (
                "❌ **Penerbitan Purchase Order Dibatalkan**\n\n"
                "Instruksi penerbitan Purchase Order (PO) telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                "Tidak ada pesanan pengadaan yang diterbitkan atau disimpan ke basis data SQLite SPPG."
            )
        elif crud_type in ["CLEAR_ALL_DOCUMENTS", "DELETE_DOCUMENT"]:
            cancel_msg = (
                "❌ **Penghapusan Dokumen Dibatalkan**\n\n"
                "Instruksi penghapusan arsip dokumen telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                "Seluruh berkas Surat Edaran dan Purchase Order tetap aman dan tersimpan di basis data SPPG."
            )
        else:
            cancel_msg = (
                f"❌ **Aksi Pengelolaan Rekanan Dibatalkan**\n\n"
                f"Instruksi draf {crud_type} telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                f"Tidak ada data rekanan yang diubah atau dihapus dari basis data resmi SPPG."
            )
        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=request.message,
            context_data=f"Bapak Adam membatalkan aksi {crud_type}. Tidak ada mutasi basis data.",
            fallback_text=cancel_msg,
            history=session.get("history", []),
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
            ),
        )

    # 2. JIKA KEPALA SPPG MENYETUJUI / MENGONFIRMASI
    if crud_type == "CREATE":
        payload_dict = pending["payload"]
        create_req = SupplierCreateRequest(**payload_dict)
        res = register_supplier_tool(payload=create_req)
        session["pending_crud"] = None

        s = res["supplier"]
        gov = res["governance"]
        halal_badge = "Sertifikat Halal Aktif (UU JPH No. 33/2014) ✅" if gov["halal_certified"] else "Belum Halal (Non-Prioritas) ❌"
        pagu_status = "Sesuai Pagu SOP BGN ✅" if not gov["exceeds_sop_ceiling"] else f"Melebihi Pagu SOP (Peringatan: {gov['price_warning']}) ⚠️"

        fallback = (
            f"✅ **Otorisasi Diterima: Rekanan Baru Resmi Terdaftar di Basis Data SPPG!**\n\n"
            f"• ID Registrasi: `{res['supplier_id']}`\n"
            f"• Nama Rekanan: **{s['supplier_name']}**\n"
            f"• Komoditas: **{s['commodity']}** [{s['category']}]\n"
            f"• Harga Penawaran: Rp {s['unit_price_idr']:,.2f} / kg\n"
            f"• Kapasitas Harian: {s['daily_capacity_kg']} kg/hari\n"
            f"• Estimasi Tiba: {s['lead_time_hours']} jam | Jarak: {s['distance_km']} km\n\n"
            f"🛡️ **Status Tata Kelola:**\n"
            f"• Sertifikasi: {halal_badge}\n"
            f"• Kepatuhan Anggaran: {pagu_status}\n\n"
            f"💾 *Data telah diverifikasi dan disimpan permanen ke dalam basis data operasional SPPG.*"
        )
        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=request.message,
            context_data=f"Aksi: Pendaftaran Resmi Disetujui Kepala SPPG. Hasil: {res}",
            fallback_text=fallback,
            history=session.get("history", []),
            target_sup_name=s["supplier_name"],
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
                preview_data={"action": "CREATE", "result": res},
            ),
        )

    elif crud_type == "UPDATE":
        sid = pending["supplier_id"]
        up_dict = pending["updates"]
        update_req = SupplierUpdateRequest(**up_dict)
        res = update_supplier_tool(supplier_id=sid, updates=update_req)
        session["pending_crud"] = None

        updated_s = res.get("supplier", {})
        fallback = (
            f"✅ **Otorisasi Diterima: Data Rekanan Berhasil Diperbarui!**\n\n"
            f"• Rekanan: **{updated_s.get('supplier_name', sid)}** (`{sid}`)\n"
            f"• Harga Penawaran: Rp {updated_s.get('unit_price_idr', 0):,.2f} / kg\n"
            f"• Kapasitas Harian: {updated_s.get('daily_capacity_kg', 0)} kg/hari\n"
            f"• Bidang diperbarui: {', '.join(res.get('updated_fields', []))}\n\n"
            f"💾 *Pembaruan data telah disetujui Kepala SPPG dan disimpan permanen.*"
        )
        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=request.message,
            context_data=f"Aksi: Update Disetujui Kepala SPPG. Hasil: {res}",
            fallback_text=fallback,
            history=session.get("history", []),
            target_sup_name=updated_s.get("supplier_name", sid),
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
                preview_data={"action": "UPDATE", "result": res},
            ),
        )

    elif crud_type in ["DEACTIVATE", "DELETE_SUPPLIER", "MANAGE_SUPPLIER_DELETE"]:
        sid = pending["supplier_id"]
        supplier_name = pending.get("supplier_name", sid)
        reason = pending.get("reason", "Instruksi disetujui Kepala SPPG")
        session["pending_crud"] = None

        msg_check = request.message.strip().lower()
        is_hard_delete = any(w in msg_check for w in ["permanen", "hard", "hapus permanen", "hapus"]) and not any(w in msg_check for w in ["nonaktif", "soft", "batal"])

        if is_hard_delete:
            res = delete_supplier_permanently_tool(supplier_id=sid)
            reply = (
                f"✅ **Otorisasi Diterima: Rekanan Berhasil Dihapus Permanen dari Basis Data SQLite!**\n\n"
                f"• Rekanan: **{supplier_name}** (`{sid}`)\n"
                f"• Status Basis Data: **DIHAPUS SECARA FISIK DARI TABEL SUPPLIERS**\n"
                f"• Otorisator: Bapak Adam Dzaki (Kepala SPPG)\n\n"
                f"💾 *Data rekanan telah dihapus permanen dari basis data SQLite SPPG.*"
            )
            action_name = "DELETE_PERMANENT"
        else:
            res = deactivate_supplier_tool(supplier_id=sid, reason=reason)
            reply = (
                f"✅ **Otorisasi Diterima: Rekanan Berhasil Dinonaktifkan (Soft Delete)!**\n\n"
                f"• Rekanan: **{supplier_name}** (`{sid}`)\n"
                f"• Status Operasional: **NON-AKTIF (`is_active = 0`)**\n"
                f"• Alasan: {reason}\n"
                f"• Otorisator: Bapak Adam Dzaki (Kepala SPPG)\n\n"
                f"🛡️ *Histori transaksi masa lalu tetap tersimpan utuh di basis data SQLite SPPG.*"
            )
            action_name = "DEACTIVATE"

        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
                preview_data={"action": action_name, "result": res},
            ),
        )

    elif crud_type == "CLEAR_ALL_DOCUMENTS":
        session["pending_crud"] = None
        from app.data.sqlite_db import clear_all_documents
        res = clear_all_documents()
        se_cleared = res.get("circular_letters_cleared", 0)
        po_cleared = res.get("purchase_orders_cleared", 0)
        fallback = (
            f"✅ **Otorisasi Diterima: Arsip Dokumen Berhasil Dikosongkan!**\n\n"
            f"Berdasarkan persetujuan Bapak Adam, seluruh riwayat dokumen resmi telah dibersihkan:\n"
            f"• Surat Edaran terhapus: {se_cleared} dokumen\n"
            f"• Purchase Order terhapus: {po_cleared} dokumen\n\n"
            f"💾 *Tabel dokumen kini berada dalam kondisi bersih (0 rekord) untuk simulasi baru.*"
        )
        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=fallback,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
            ),
        )

    elif crud_type == "DELETE_DOCUMENT":
        session["pending_crud"] = None
        doc_type = pending.get("doc_type", "SE")
        identifier = pending.get("identifier", "")
        title_or_name = pending.get("title_or_name", "")
        from app.data.sqlite_db import delete_circular_letter_by_id, delete_purchase_order_by_number
        if doc_type == "PO" or identifier.startswith("PO-"):
            success = delete_purchase_order_by_number(identifier)
            doc_label = "Purchase Order (PO)"
        else:
            success = delete_circular_letter_by_id(identifier)
            doc_label = "Surat Edaran (SE)"

        if success:
            fallback = (
                f"✅ **Otorisasi Diterima: Dokumen Berhasil Dihapus!**\n\n"
                f"Dokumen resmi berikut telah dihapus secara permanen dari basis data SPPG:\n"
                f"• Jenis: **{doc_label}**\n"
                f"• Nomor: `{identifier}`\n"
                f"• Keterangan: {title_or_name}\n\n"
                f"💾 *Penghapusan telah disahkan oleh Bapak Adam Dzaki.*"
            )
        else:
            fallback = (
                f"⚠️ Dokumen `{identifier}` tidak ditemukan atau sudah terhapus sebelumnya di basis data."
            )

        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=fallback,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.NONE,
            ),
        )

    elif crud_type == "APPROVE_MULTI_PO":
        po_list = pending.get("po_list", [])
        total_budget = pending.get("total_budget", 0.0)
        target_portions = pending.get("target_portions", 3000)
        session["pending_crud"] = None

        from app.data.sqlite_db import save_circular_letter, save_purchase_order

        saved_pos = []
        for p in po_list:
            try:
                save_purchase_order(p)
                letter_id = f"SE-SPPG-{p['po_number'].replace('PO-', '')}"
                letter_num = f"{p['po_number'].split('-')[-1]}/SE/SPPG-PENGADAAN/{datetime.now(timezone.utc).strftime('%m/%Y')}"
                save_circular_letter({
                    "letter_id": letter_id,
                    "letter_number": letter_num,
                    "title": f"Surat Penetapan Pengadaan {p.get('item_name', p['item_id'])} - {p['supplier_name']}",
                    "incident_id": p.get("incident_id", request.session_id),
                    "item_id": p["item_id"],
                    "deficit_kg": p["approved_qty_kg"],
                    "supplier_id": p["supplier_id"],
                    "supplier_name": p["supplier_name"],
                    "issued_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "signer_name": request.user_role,
                    "signer_role": "Kepala Satuan Pelayanan Pemenuhan Gizi (SPPG)",
                    "content_text": (
                        f"Berdasarkan rencana kebutuhan {target_portions:,} porsi dan persetujuan Kepala SPPG, "
                        f"ditetapkan pengadaan bahan pangan {p.get('item_name', p['item_id'])} sejumlah "
                        f"{p['approved_qty_kg']} kg kepada {p['supplier_name']} dengan nilai kontrak Rp {p['total_amount_idr']:,.2f}."
                    ),
                    "status": "ISSUED",
                })
                saved_pos.append(p)
            except Exception:
                pass

        session["is_approved"] = True
        session["saved_pos"] = saved_pos

        fallback_text = (
            f"✅ **Otorisasi Diterima: Seluruh Purchase Order Resmi Berhasil Diterbitkan!**\n\n"
            f"Persetujuan telah dicatat secara resmi ke dalam basis data SQLite SPPG, Bapak Adam:\n\n"
            + "\n".join([
                f"• **{p['supplier_name']}** (`{p['po_number']}`)\n"
                f"  Komoditas: {p.get('item_name', p['item_id'])} | Kuantitas: **{p['approved_qty_kg']} kg** | Nilai: **Rp {p['total_amount_idr']:,.2f}**"
                for p in saved_pos
            ])
            + f"\n\nTotal alokasi anggaran: **Rp {total_budget:,.2f}** (Sesuai Pagu SOP BGN).\n\n"
            f"Tim logistik gudang telah diinstruksikan untuk bersiap menyambut kedatangan bahan pangan dengan protokol ketat suhu rantai dingin dan verifikasi sertifikat Halal.\n\n"
            f"Dokumen resmi telah diarsipkan di menu *'Arsip Surat Edaran & PO'* dan siap untuk dicetak atau diunduh."
        )

        context_data = (
            f"Status: Seluruh PO Pengadaan Multi-Item Berhasil Disahkan & Disimpan ke SQLite.\n"
            f"Total PO: {len(saved_pos)} dokumen, Nilai Total: Rp {total_budget:,.2f}.\n"
            + "\n".join([f"- {p['po_number']}: {p['supplier_name']}, {p['approved_qty_kg']} kg, Rp {p['total_amount_idr']:,.2f}" for p in saved_pos])
        )

        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["PO_APPROVAL"],
            user_message=request.message,
            context_data=context_data,
            fallback_text=fallback_text,
            history=session.get("history", []),
            target_sup_name=saved_pos[0]["supplier_name"] if saved_pos else None,
        )

        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.CONFIRM_APPROVAL,
                action_required=ChatActionRequired.COMPLETED,
                preview_data={
                    "action": "MULTI_PO_APPROVED",
                    "po_results": saved_pos,
                    "po_result": saved_pos[0] if saved_pos else None,
                },
            ),
        )

    from app.engine.agent.handlers.general_handler import handle_consultative_chat
    return handle_consultative_chat(session, request, call_gemini_adaptive, respond)

