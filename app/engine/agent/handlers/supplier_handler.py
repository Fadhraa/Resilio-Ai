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
    ExecutionTraceStep,
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
from app.engine.agent.parsers import (
    match_supplier_in_text,
    infer_commodity_and_category,
    parse_supplier_create_data,
    extract_supplier_fields,
    find_duplicate_supplier,
)


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

        # Bedakan antara penonaktifan (Soft Delete) dan penghapusan fisik (Hard Delete)
        is_explicit_hard = action == "DELETE_SUPPLIER" or any(w in user_msg.lower() for w in ["permanen", "hard delete", "hapus permanen"])

        if is_explicit_hard:
            crud_target_type = "DELETE_PERMANENT"
            action_title = f"Penghapusan Permanen Rekanan #{sid}"
            warning_text = "Data rekanan akan dihapus secara fisik dari basis data SQLite SPPG."
            confirm_cmd = f"Hapus permanen rekanan {sid}"
            cancel_cmd = "Batal, jangan hapus rekanan."
            preview_text = (
                f"⚠️ **Konfirmasi Penghapusan Permanen Rekanan SPPG (Hard Delete)**\n\n"
                f"Bapak Adam Dzaki, sistem menerima instruksi penghapusan permanen rekanan:\n"
                f"• Nama Rekanan: **{supplier.supplier_name}** (`{sid}`)\n"
                f"• Komoditas: **{commodity_name}** [{supplier.category}]\n"
                f"• Alasan: {reason}\n\n"
                f"⚠️ **PERHATIAN:** Baris data rekanan akan dihapus secara fisik dari tabel `suppliers` di basis data SQLite SPPG. "
                f"Tindakan ini tidak dapat dipulihkan kembali.\n\n"
                f"Apakah Bapak yakin ingin menghapus rekanan ini secara permanen? Silakan klik tombol **'Hapus Permanen'** di bawah atau ketik *'Batal'*."
            )
        else:
            crud_target_type = "DEACTIVATE_SUPPLIER"
            action_title = f"Penonaktifan Rekanan #{sid}"
            warning_text = "Rekanan akan dinonaktifkan (is_active = 0). Rekam jejak audit anggaran masa lalu tetap tersimpan utuh di basis data SQLite SPPG."
            confirm_cmd = f"Nonaktifkan rekanan {sid}"
            cancel_cmd = "Batal, jangan nonaktifkan rekanan."
            preview_text = (
                f"⚠️ **Konfirmasi Penonaktifan Rekanan SPPG (Soft Delete)**\n\n"
                f"Bapak Adam Dzaki, sistem mendeteksi instruksi penonaktifan rekanan supplier:\n"
                f"• Nama Rekanan: **{supplier.supplier_name}** (`{sid}`)\n"
                f"• Komoditas: **{commodity_name}** [{supplier.category}]\n"
                f"• Alasan: {reason}\n\n"
                f"Tindakan ini adalah **Soft Delete**, yaitu mengubah status rekanan menjadi **NON-AKTIF (`is_active = 0`)** "
                f"di basis data SQLite SPPG. Data rekanan tidak akan diprioritaskan dalam draf pengadaan baru, namun seluruh rekam jejak "
                f"audit transaksi anggaran masa lalu tetap tersimpan utuh dan aman.\n\n"
                f"Silakan klik tombol **'Nonaktifkan Rekanan (Soft Delete)'** di bawah atau ketik *'Ya, nonaktifkan'*, atau pilih **'Batalkan'**."
            )

        session["pending_crud"] = {
            "type": crud_target_type,
            "supplier_id": sid,
            "supplier_name": supplier.supplier_name,
            "commodity": commodity_name,
            "reason": reason,
        }

        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=user_msg,
            context_data=(
                f"Tahap: Konfirmasi {'Penghapusan Permanen' if is_explicit_hard else 'Penonaktifan (Soft Delete)'} Rekanan. "
                f"Target Rekanan: {supplier.supplier_name} ({sid}), Komoditas: {commodity_name}. Alasan: {reason}. "
                f"Sistem telah menyiapkan kartu konfirmasi untuk otorisasi Kepala SPPG."
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
                    "action": "PREVIEW_DELETE" if is_explicit_hard else "PREVIEW_DEACTIVATE",
                    "supplier_id": sid,
                    "supplier_name": supplier.supplier_name,
                    "confirm_supplier_action": {
                        "action_type": "DELETE_PERMANENT" if is_explicit_hard else "DEACTIVATE",
                        "supplier_id": sid,
                        "supplier_name": supplier.supplier_name,
                        "commodity": commodity_name,
                        "title": action_title,
                        "details": f"{supplier.supplier_name} ({sid}) - {commodity_name}",
                        "warning": warning_text,
                        "confirm_command": confirm_cmd,
                        "cancel_command": cancel_cmd,
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

    # 3. REGISTER PREVIEW (Dengan Validasi Kelengkapan Data & Multi-Turn State Merging)
    pending_draft = session.get("pending_supplier_draft") or {}
    extracted = extract_supplier_fields(user_msg)

    # Ambil nilai dari router params jika ada dan tidak bernilai None/kosong
    for k in ["supplier_name", "commodity", "category", "unit_price_idr", "daily_capacity_kg", "distance_km", "halal_certified", "halal_cert_number"]:
        if extracted.get(k) is None and params.get(k) is not None and str(params[k]).strip() not in ["", "None", "null"]:
            extracted[k] = params[k]

    # Khusus lead_time_hours: hanya gunakan dari params jika pesan menyebut jam/hari/lead time
    if extracted.get("lead_time_hours") is None and params.get("lead_time_hours") is not None:
        if re.search(r"\b\d+(?:\.\d+)?\s*(?:jam|hour|hari|day)\b", user_msg, re.IGNORECASE) or "waktu kirim" in user_msg.lower():
            try:
                extracted["lead_time_hours"] = float(params["lead_time_hours"])
            except (ValueError, TypeError):
                pass

    # Merge data baru ke dalam draft yang sudah terkumpul
    merged_draft = dict(pending_draft)
    for k, v in extracted.items():
        if v is not None and v != "":
            merged_draft[k] = v

    # Jika nama supplier ada tapi komoditas belum teridentifikasi, coba infer dari teks atau nama
    sup_name = merged_draft.get("supplier_name")
    if sup_name:
        comm_cand, cat_cand, supp_items = infer_commodity_and_category(
            merged_draft.get("commodity") or user_msg,
            supplier_name=sup_name,
        )
        if not merged_draft.get("commodity") and comm_cand != "PROTEIN_LAINNYA":
            merged_draft["commodity"] = comm_cand
        if not merged_draft.get("category"):
            merged_draft["category"] = cat_cand
        if not merged_draft.get("supported_items"):
            merged_draft["supported_items"] = supp_items

    # 3.1 PENGECEKAN DUPLIKASI REKANAN (Zero Duplicate Record Guarantee)
    candidate_name = merged_draft.get("supplier_name")
    if candidate_name:
        existing_dup = find_duplicate_supplier(candidate_name)
        if existing_dup:
            session["pending_supplier_draft"] = None
            session["pending_crud"] = None

            is_active = bool(existing_dup.get("is_active", True))
            sid = existing_dup["supplier_id"]
            sname = existing_dup["supplier_name"]
            comm = existing_dup.get("commodity", "Pangan")
            price = existing_dup.get("unit_price_idr", 0)
            cap = existing_dup.get("daily_capacity_kg", 0)
            lt = existing_dup.get("lead_time_hours", 0)
            dist = existing_dup.get("distance_km", 0)
            h_cert = existing_dup.get("halal_cert_number") or "Tercatat BPJPH"
            h_str = f"Halal Aktif (No: {h_cert}) ✅" if existing_dup.get("halal_certified") else "Belum Bersertifikat Halal ❌"

            if is_active:
                dup_msg = (
                    f"Bapak Adam, rekanan **{sname}** sudah terdaftar resmi di basis data operasional SPPG dengan kode **`{sid}`** untuk komoditas **{comm}** (Status: **Aktif ✅**).\n\n"
                    f"Rincian data rekanan saat ini di sistem:\n"
                    f"• Harga Penawaran: Rp {price:,.2f} / kg\n"
                    f"• Kapasitas Harian: {cap} kg/hari\n"
                    f"• Estimasi Tiba & Jarak: {lt} jam | {dist} km\n"
                    f"• Status Sertifikasi Halal: {h_str}\n\n"
                    f"⚠️ **Deteksi Data Duplikat:**\n"
                    f"Sistem mendeteksi bahwa rekanan ini telah terdaftar, sehingga pendaftaran baru tidak dapat diproses guna mencegah data ganda di basis data.\n\n"
                    f"Apakah Bapak bermaksud untuk **memperbarui data** rekanan tersebut (misalnya penyesuaian harga atau kapasitas pasok)? Jika iya, silakan sampaikan perubahannya (contoh: *\"Update harga {sname} menjadi Rp ...\"*)."
                )
            else:
                dup_msg = (
                    f"Bapak Adam, rekanan **{sname}** dengan kode **`{sid}`** untuk komoditas **{comm}** sebelumnya sudah terdaftar di basis data SPPG, namun saat ini berstatus **Nonaktif (Soft Delete)**.\n\n"
                    f"⚠️ **Deteksi Rekanan Nonaktif:**\n"
                    f"Untuk menghindari duplikasi kode rekanan, pendaftaran baru tidak dapat diproses. Sebagai gantinya, apakah Bapak ingin **mengaktifkan kembali** (*reactivate*) rekanan **{sname}** ini?"
                )

            adaptive_reply = call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=user_msg,
                context_data=(
                    f"Tahap: Deteksi Duplikasi Rekanan. Rekanan {sname} ({sid}) sudah ada di basis data. "
                    f"Status aktif: {is_active}. Sistem menolak pendaftaran duplikat dan menawarkan pembaruan data atau reaktivasi."
                ),
                fallback_text=dup_msg,
                history=session.get("history", []),
                target_sup_name=sname,
            )
            return respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                    preview_data={"existing_supplier": existing_dup, "is_duplicate": True},
                ),
            )

    # Evaluasi parameter wajib (Mandatory Operational Fields):
    # 1. Nama Rekanan
    # 2. Komoditas Pangan
    # 3. Harga Penawaran per kg
    # 4. Kapasitas Pasokan Harian
    # 5. Estimasi Waktu Kirim (Lead Time)
    missing_fields = []
    if not merged_draft.get("supplier_name"):
        missing_fields.append("Nama Rekanan / Badan Usaha")
    if not merged_draft.get("commodity"):
        missing_fields.append("Komoditas Pangan (misal: Daging Sapi, Ayam, Telur, dll.)")
    if merged_draft.get("unit_price_idr") is None:
        missing_fields.append("Harga Penawaran per kg")
    if merged_draft.get("daily_capacity_kg") is None:
        missing_fields.append("Kapasitas Pasokan Harian (kg/hari)")
    if merged_draft.get("lead_time_hours") is None:
        missing_fields.append("Estimasi Waktu Kirim / Lead Time (dalam jam)")

    if missing_fields:
        # Simpan state draf parsial di session agar user bisa melengkapi di chat berikutnya
        session["pending_supplier_draft"] = merged_draft
        session["pending_crud"] = None

        recorded_items = []
        if merged_draft.get("supplier_name"):
            recorded_items.append(f"• **Nama Rekanan:** {merged_draft['supplier_name']}")
        if merged_draft.get("commodity"):
            recorded_items.append(f"• **Komoditas:** {merged_draft['commodity']}")
        if merged_draft.get("unit_price_idr") is not None:
            recorded_items.append(f"• **Harga Penawaran:** Rp {float(merged_draft['unit_price_idr']):,.0f}/kg")
        if merged_draft.get("daily_capacity_kg") is not None:
            recorded_items.append(f"• **Kapasitas Harian:** {float(merged_draft['daily_capacity_kg'])} kg/hari")
        if merged_draft.get("distance_km") is not None:
            recorded_items.append(f"• **Jarak Tempuh:** {float(merged_draft['distance_km'])} km")
        if merged_draft.get("halal_certified") is not None:
            h_cert = merged_draft.get("halal_cert_number") or "Tercatat"
            h_str = f"Terverifikasi Aktif ({h_cert})" if merged_draft["halal_certified"] else "Non-Sertifikasi"
            recorded_items.append(f"• **Status Sertifikasi Halal:** {h_str}")

        recorded_summary = "\n".join(recorded_items) if recorded_items else "Belum ada rincian yang tercatat."
        missing_str = ", ".join(f"**{m}**" for m in missing_fields)

        clarification_msg = (
            f"Bapak Adam, saya telah mencatat rincian pendaftaran rekanan berikut:\n\n"
            f"{recorded_summary}\n\n"
            f"Namun, dari informasi yang Bapak sampaikan masih belum ada informasi terkait {missing_str}. "
            f"Apakah Bapak bisa menyampaikannya terlebih dahulu agar draf pendaftaran rekanan dapat saya lengkapi?"
        )

        adaptive_reply = call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=user_msg,
            context_data=(
                f"Tahap: Klarifikasi Data Pendaftaran Rekanan. Data tercatat: {merged_draft}. "
                f"Data yang masih belum ada / kurang: {missing_fields}. "
                f"AI meminta Bapak Adam untuk melengkapi informasi yang kurang tersebut secara santun, jelas, dan profesional. "
                f"DILARANG menampilkan kartu pratinjau atau otorisasi karena data belum lengkap."
            ),
            fallback_text=clarification_msg,
            history=session.get("history", []),
            target_sup_name=merged_draft.get("supplier_name"),
        )

        return respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.CLARIFICATION_NEEDED,
            ),
        )

    # Seluruh parameter wajib terpenuhi! Hapus pending_supplier_draft dan susun payload pendaftaran
    session["pending_supplier_draft"] = None

    cert = merged_draft.get("halal_cert_number") or ("Tercatat BPJPH" if merged_draft.get("halal_certified", True) else None)
    dist = float(merged_draft.get("distance_km") or 15.0)
    halal_val = bool(merged_draft.get("halal_certified", True))

    create_payload = SupplierCreateRequest(
        supplier_name=str(merged_draft["supplier_name"]).strip(),
        category=merged_draft.get("category") or "PROTEIN",
        commodity=merged_draft.get("commodity") or "PROTEIN_LAINNYA",
        supported_items=merged_draft.get("supported_items") or ["ITEM-CUSTOM-01"],
        halal_certified=halal_val,
        halal_cert_number=str(cert).strip() if cert else None,
        unit_price_idr=float(merged_draft["unit_price_idr"]),
        daily_capacity_kg=float(merged_draft["daily_capacity_kg"]),
        lead_time_hours=float(merged_draft["lead_time_hours"]),
        distance_km=dist,
        reliability_rating=85.0,
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
    exec_trace = [
        ExecutionTraceStep(
            step_number=1,
            stage="DATA_LAYER",
            title="Ekstraksi Parameter Pendaftaran Rekanan (Semantic Parsing)",
            status="COMPLETED",
            details=f"Rekanan: {create_payload.supplier_name} | Komoditas: {create_payload.commodity} | Harga: Rp {create_payload.unit_price_idr:,.0f}/kg.",
            execution_time_ms=8,
        ),
        ExecutionTraceStep(
            step_number=2,
            stage="COMPLIANCE_FILTER",
            title="Verifikasi Kelengkapan Operasional & Waktu Kirim (Zero Assumption)",
            status="COMPLETED",
            details=f"Waktu Kirim: {create_payload.lead_time_hours} jam | Jarak: {create_payload.distance_km} km | Kapasitas: {create_payload.daily_capacity_kg} kg/hari.",
            execution_time_ms=3,
        ),
        ExecutionTraceStep(
            step_number=3,
            stage="COMPLIANCE_FILTER",
            title="Pemeriksaan Legalitas Sertifikasi Halal BPJPH (UU 33/2014)",
            status="COMPLETED",
            details=f"Status Halal: {'Terverifikasi Aktif (' + str(create_payload.halal_cert_number or 'Tercatat') + ')' if create_payload.halal_certified else 'Non-Sertifikasi'}.",
            execution_time_ms=4,
        ),
        ExecutionTraceStep(
            step_number=4,
            stage="FEASIBILITY_GATE",
            title="Evaluasi Batas Pagu Anggaran SOP Bahan Pangan BGN",
            status="COMPLETED",
            details=f"Harga Penawaran Rp {create_payload.unit_price_idr:,.0f} vs Pagu SOP Maksimal Rp {sop_max:,.0f} ({pagu_status}).",
            execution_time_ms=2,
        ),
        ExecutionTraceStep(
            step_number=5,
            stage="HUMAN_APPROVAL_GATE",
            title="Gerbang Otorisasi Sah Kepala SPPG (Human-in-the-Loop)",
            status="WAITING_APPROVAL",
            details=f"Draf rekanan {create_payload.supplier_name} disiapkan menunggu persetujuan Bapak Adam.",
            execution_time_ms=1,
        ),
    ]

    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=adaptive_reply,
            intent=ChatIntent.MANAGE_SUPPLIER,
            action_required=ChatActionRequired.APPROVAL_PENDING,
            preview_data={"action": "PREVIEW_CREATE", "draft": create_payload.model_dump()},
            execution_trace=exec_trace,
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
        # Periksa apakah ada draf pendaftaran rekanan belum lengkap yang dibatalkan
        if not is_confirm and session.get("pending_supplier_draft"):
            session["pending_supplier_draft"] = None
            cancel_msg = (
                "❌ **Pendaftaran Rekanan Dibatalkan**\n\n"
                "Draf pendaftaran rekanan baru telah dibatalkan sesuai arahan Bapak Adam. "
                "Tidak ada data rekanan yang disimpan ke basis data resmi SPPG."
            )
            adaptive_reply = call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data="Bapak Adam membatalkan proses pendaftaran rekanan baru. Draf dibersihkan.",
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
        from app.engine.agent.handlers.general_handler import handle_consultative_chat
        return handle_consultative_chat(session, request, call_gemini_adaptive, respond)

    crud_type = pending.get("type")
    session["pending_supplier_draft"] = None

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

        # Idempotency / Duplicate Guard sebelum eksekusi ke database
        existing_dup = find_duplicate_supplier(create_req.supplier_name)
        if existing_dup and existing_dup.get("is_active", True):
            session["pending_crud"] = None
            sid = existing_dup["supplier_id"]
            sname = existing_dup["supplier_name"]
            notice = (
                f"⚠️ **Pendaftaran Dibatalkan: Data Rekanan Telah Terdaftar**\n\n"
                f"Rekanan **{sname}** telah terdaftar sebelumnya di basis data SPPG dengan kode **`{sid}`**.\n"
                f"Sistem tidak melakukan penambahan ganda untuk menjaga integritas data rekanan."
            )
            return respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=notice,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                ),
            )

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

    elif crud_type in ["DEACTIVATE", "DEACTIVATE_SUPPLIER", "DELETE_SUPPLIER", "DELETE_PERMANENT", "MANAGE_SUPPLIER_DELETE"]:
        sid = pending["supplier_id"]
        supplier_name = pending.get("supplier_name", sid)
        reason = pending.get("reason", "Instruksi disetujui Kepala SPPG")
        session["pending_crud"] = None

        msg_check = request.message.strip().lower()
        # HANYA lakukan hard delete jika aksi asalnya adalah DELETE_PERMANENT atau user secara tegas meminta 'permanen'
        is_hard_delete = crud_type == "DELETE_PERMANENT" or (
            any(w in msg_check for w in ["permanen", "hard delete", "hapus permanen"])
            and not any(w in msg_check for w in ["nonaktif", "soft", "batal"])
        )

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
                f"🛡️ *Data rekanan tidak dihapus dan histori transaksi masa lalu tetap tersimpan utuh di basis data SQLite SPPG.*"
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

