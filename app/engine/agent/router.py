"""
Cognitive Decision Engine & Semantic Router for ResilioAI Agent.
Mengarahkan niat Kepala SPPG (Bapak Adam) menggunakan Gemini LLM dengan graceful fallback deterministik.
"""

import json
import re
from typing import Any, Dict, Optional
from app.engine.agent.parsers import extract_portions


def decide_action(
    user_message: str,
    session: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash-lite",
) -> Dict[str, Any]:
    """
    Decision Router: Memahami konteks percakapan bebas Kepala SPPG menggunakan Gemini.
    Mengembalikan struktur aksi dan parameter. Jika LLM offline, beralih ke fallback deterministik yang aman.
    """
    has_pending_crud = bool(session.get("pending_crud"))
    has_pending = bool(session.get("pending_clarification"))
    has_rec = bool(session.get("current_recommendation"))
    msg_clean = user_message.strip()
    msg_lower = msg_clean.lower()

    # Deteksi apakah pesan pengguna merupakan inisiasi atau penyusunan menu pengadaan (Multi-Item)
    planning_keywords = [
        "rencana", "rencananya", "berencana", "menu", "porsi", "susun", "kebutuhan bahan",
        "pengadaan menu", "makanan bergizi", "bantu aku dalam membuat po", "membuat po", "buat po"
    ]
    commodity_keywords = [
        "ayam", "unggas", "telur", "tahu", "tempe", "sapi", "lembu", "ikan", "beras", "sayur", "wortel"
    ]
    is_planning_msg = any(w in msg_lower for w in planning_keywords) and (
        "porsi" in msg_lower or any(c in msg_lower for c in commodity_keywords)
    )

    revision_keywords = [
        "ganti supplier", "ganti rekanan", "ubah supplier", "ubah rekanan",
        "ganti ke", "ubah ke", "tukar", "pindah ke", "lebih murah", "alternatif lain",
        "supplier lain", "rekanan lain", "vendor lain", "mitra lain"
    ]
    is_revision_msg = any(w in msg_lower for w in revision_keywords) or (
        ("ganti" in msg_lower or "tukar" in msg_lower or "revisi" in msg_lower)
        and any(c in msg_lower for c in commodity_keywords + ["supplier", "rekanan", "vendor", "mitra"])
    )

    # Prioritas status alur jika dalam interaksi multi-turn eksplisit:
    # 0. Permintaan Revisi / Penggantian Rekanan Pangan (REQUEST_REVISION)
    if is_revision_msg:
        return {"action": "REQUEST_REVISION", "parameters": {}}

    # 0.5 Perencanaan Menu / Kebutuhan Porsi Multi-Item (PLAN_PROCUREMENT)
    if is_planning_msg:
        portions = extract_portions(user_message, default=3000)
        commodities = []
        if "telur" in msg_lower:
            commodities.append("telur")
        if "ayam" in msg_lower or "unggas" in msg_lower:
            commodities.append("ayam")
        if "tahu" in msg_lower:
            commodities.append("tahu")
        if "tempe" in msg_lower:
            commodities.append("tempe")
        if "sapi" in msg_lower or "lembu" in msg_lower:
            commodities.append("sapi")
        if "beras" in msg_lower:
            commodities.append("beras")
        if "sayur" in msg_lower or "wortel" in msg_lower:
            commodities.append("sayur")
        if "ikan" in msg_lower:
            commodities.append("ikan")
        return {
            "action": "PLAN_PROCUREMENT",
            "parameters": {
                "target_portions": portions,
                "commodities": commodities,
            }
        }

    # 1. Konfirmasi atau Pembatalan Draf CRUD Rekanan / Penerbitan PO (Human-in-the-Loop)
    if has_pending_crud:
        if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
            return {"action": "CANCEL_CRUD", "parameters": {}}
        if any(w in msg_lower for w in [
            "setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan",
            "nonaktifkan", "hapus", "permanen", "proses", "deal",
            "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes", "eksekusi", "delete", "terbitkan", "terbitkan po"
        ]):
            return {"action": "CONFIRM_CRUD", "parameters": {}}

    # 1.5 Pembatalan draf rekanan yang sedang dilengkapi (pending_supplier_draft)
    if session.get("pending_supplier_draft"):
        if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
            return {"action": "CANCEL_CRUD", "parameters": {}}

    # 2. Konfirmasi klarifikasi saat pending_clarification aktif
    if has_pending and (any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu"]) or any(s.lower() in msg_lower for s in session["pending_clarification"].get("suggestions", []))):
        return {"action": "CONFIRM_CLARIFICATION", "parameters": {}}

    # 3. Persetujuan PO saat rekomendasi mitigasi atau perencanaan pengadaan aktif
    if (has_rec or session.get("procurement_plan")) and any(
        w in msg_lower for w in ["buatkan po", "terbitkan po", "terbitkan surat po", "draf po", "bikin po", "po untuk rencana"]
    ):
        return {"action": "APPROVE_PO", "parameters": {}}

    if has_rec and any(w in msg_lower for w in ["setuju", "deal", "approve", "proses sekarang"]):
        return {"action": "APPROVE_PO", "parameters": {}}

    # 4. DOMAIN GUARDRAIL (SANGAT KETAT): Tolak permintaan pembuatan kode pemrograman
    coding_signals = [
        "code", "kode", "html", "javascript", "python", "css", "c++", "script",
        "hello world", "coding", "bikin web", "buatkan web", "pemrograman",
        "bikin program", "buat program", "tulis fungsi", "write code"
    ]
    if any(cs in msg_lower for cs in coding_signals):
        return {"action": "OUT_OF_DOMAIN", "parameters": {}}

    # Pemrosesan Semantik Berbasis Gemini LLM
    if api_key and not api_key.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            decision_prompt = (
                "Kamu adalah Cognitive Decision Engine untuk ResilioAI Assistant (Sistem Manajemen Rantai Pasok SPPG).\n"
                "Kamu memiliki otoritas dan kapabilitas penuh untuk memahami niat Kepala SPPG (Bapak Adam) secara semantik tanpa ketergantungan kata kaku.\n"
                "Tugasmu: Analisis pesan dari Kepala SPPG secara semantik dan ekstrak seluruh parameter yang dibutuhkan ke format JSON.\n\n"
                f"Konteks Sesi Saat Ini:\n"
                f"- Ada draf CRUD / PO pending menunggu keputusan Kepala: {'YA (' + str(session['pending_crud'].get('type', '')) + ')' if has_pending_crud else 'TIDAK'}\n"
                f"- Ada draf pendaftaran rekanan belum lengkap (menunggu data operasional dari Kepala): {'YA (' + str(session.get('pending_supplier_draft', {}).get('supplier_name', '')) + ')' if session.get('pending_supplier_draft') else 'TIDAK'}\n"
                f"- Ada draf rencana pengadaan menu aktif: {'YA (' + str(session.get('procurement_plan', {}).get('target_portions', '')) + ' porsi)' if session.get('procurement_plan') else 'TIDAK'}\n"
                f"- Ada klarifikasi supplier pending: {'YA' if has_pending else 'TIDAK'}\n"
                f"- Ada rekomendasi mitigasi aktif: {'YA' if has_rec else 'TIDAK'}\n\n"
                "Daftar Aksi & Spesifikasi Parameter:\n"
                "1. 'CONFIRM_CRUD': Kepala SPPG menyetujui/mengonfirmasi draf aksi CRUD pending (contoh: 'setuju', 'simpan', 'ya daftarkan', 'oke proses', 'lanjutkan').\n"
                "2. 'CANCEL_CRUD': Kepala SPPG membatalkan draf aksi CRUD pending (contoh: 'batal', 'jangan simpan', 'batalkan', 'tidak jadi').\n"
                "3. 'REGISTER_SUPPLIER': Kepala SPPG ingin menambahkan/mendaftarkan supplier baru ATAU sedang melengkapi data rekanan yang kurang (seperti waktu kirim/lead time, harga, kapasitas, dll).\n"
                "   {\n"
                "     \"supplier_name\": string atau null,\n"
                "     \"commodity\": string atau null,\n"
                "     \"category\": 'PROTEIN' | 'STAPLE' | 'VEGETABLE' | 'OTHER' atau null,\n"
                "     \"unit_price_idr\": float atau null,\n"
                "     \"daily_capacity_kg\": float atau null,\n"
                "     \"halal_certified\": boolean atau null,\n"
                "     \"halal_cert_number\": string atau null,\n"
                "     \"lead_time_hours\": float atau null (PENTING: HANYA isi jika disebutkan secara eksplisit dalam pesan. JANGAN pernah menebak atau mengasumsikan nilai jika tidak ada di pesan, biarkan null),\n"
                "     \"distance_km\": float atau null\n"
                "   }\n"
                "4. 'UPDATE_SUPPLIER': Kepala SPPG ingin mengubah data supplier (harga, kapasitas, durasi kirim).\n"
                "   {\n"
                "     \"supplier_name_or_id\": string atau null,\n"
                "     \"unit_price_idr\": float atau null,\n"
                "     \"daily_capacity_kg\": float atau null,\n"
                "     \"lead_time_hours\": float atau null,\n"
                "     \"halal_certified\": boolean atau null\n"
                "   }\n"
                "5. 'DEACTIVATE_SUPPLIER': Menghapus/menonaktifkan rekanan dari daftar aktif (contoh: 'hapus supplier SUP-REG-02').\n"
                "   {\n"
                "     \"supplier_name_or_id\": string atau null,\n"
                "     \"reason\": string\n"
                "   }\n"
                "6. 'LIST_SUPPLIERS': Melihat/menanyakan daftar supplier terdaftar.\n"
                "   {\"commodity\": string atau null}\n"
                "7. 'GET_INVENTORY': Mengecek stok gudang, sisa bahan, atau freezer.\n"
                "   {\"item_name_or_id\": string atau null}\n"
                "8. 'REPORT_INCIDENT': Melaporkan gangguan pasokan, disrupsi, kebakaran, gagal kirim.\n"
                "9. 'REQUEST_REVISION': Meminta revisi draf atau penggantian rekanan (contoh: 'ganti supplier ayamnya ke PT Berkah Unggas Jaya', 'untuk ayam apa bisa diganti supplier lain?', 'bisa cari supplier yang lebih murah?').\n"
                "10. 'APPROVE_PO': Menyetujui atau meminta penerbitan PO resmi.\n"
                "11. 'CONFIRM_CLARIFICATION': Mengonfirmasi pilihan rekanan dari pertanyaan klarifikasi.\n"
                "12. 'CLEAR_DOCUMENTS': Menghapus seluruh arsip Surat Edaran dan PO.\n"
                "13. 'DELETE_DOCUMENT': Menghapus salah satu dokumen spesifik berdasarkan nomor/ID.\n"
                "   {\"identifier\": string atau null}\n"
                "14. 'EXPLAIN_CAPABILITIES': Bertanya kapabilitas sistem asisten.\n"
                "15. 'OUT_OF_DOMAIN': Permintaan di luar domain logistik pangan SPPG.\n"
                "16. 'GREETING': Sapaan pembuka murni.\n"
                "17. 'GENERAL_CHAT': Pertanyaan konsultatif umum tentang regulasi halal UU 33/2014, SOP SPPG.\n"
                "18. 'PLAN_PROCUREMENT': Merencanakan pengadaan atau menyusun menu/porsi makanan bergizi "
                "(contoh: 'saya berencana membuat 3000 porsi makanan bergizi dengan ayam dan telur bantu susun PO nya').\n"
                "   {\n"
                "     \"target_portions\": integer,\n"
                "     \"commodities\": list of string\n"
                "   }\n\n"
                "Keluarkan HANYA JSON murni: {\"action\": \"...\", \"parameters\": {...}}"
            )

            llm = ChatGoogleGenerativeAI(
                model=model_name,
                transport="rest",
                google_api_key=api_key,
                timeout=8,
            )
            res = llm.invoke([("system", decision_prompt), ("user", user_message)])
            raw_content = str(res.content).strip()
            raw_content = re.sub(r"^```json\s*", "", raw_content)
            raw_content = re.sub(r"^```\s*", "", raw_content)
            raw_content = re.sub(r"\s*```$", "", raw_content).strip()
            parsed = json.loads(raw_content)
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
        except Exception:
            pass

    return fallback_decide_action(user_message, session)


def fallback_decide_action(user_message: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback router deterministik jika LLM offline atau timeout (Graceful Fallback)."""
    msg_lower = user_message.lower().strip()

    # Deteksi apakah pesan pengguna merupakan inisiasi atau penyusunan menu pengadaan (Multi-Item)
    planning_keywords = [
        "rencana", "rencananya", "berencana", "menu", "porsi", "susun", "kebutuhan bahan",
        "pengadaan menu", "makanan bergizi", "bantu aku dalam membuat po", "membuat po", "buat po"
    ]
    commodity_keywords = [
        "ayam", "unggas", "telur", "tahu", "tempe", "sapi", "lembu", "ikan", "beras", "sayur", "wortel"
    ]
    has_incident = any(k in msg_lower for k in ["kebakaran", "banjir", "rusak", "terhambat", "gagal", "mogok", "tidak kirim", "darurat", "musibah", "disrupsi"])
    is_planning_msg = not has_incident and any(w in msg_lower for w in planning_keywords) and (
        "porsi" in msg_lower or any(c in msg_lower for c in commodity_keywords)
    )

    revision_keywords = [
        "ganti supplier", "ganti rekanan", "ubah supplier", "ubah rekanan",
        "ganti ke", "ubah ke", "tukar", "pindah ke", "lebih murah", "alternatif lain",
        "supplier lain", "rekanan lain", "vendor lain", "mitra lain"
    ]
    is_revision_msg = any(w in msg_lower for w in revision_keywords) or (
        ("ganti" in msg_lower or "tukar" in msg_lower or "revisi" in msg_lower)
        and any(c in msg_lower for c in commodity_keywords + ["supplier", "rekanan", "vendor", "mitra"])
    )

    # 0. Permintaan Revisi / Penggantian Rekanan Pangan (REQUEST_REVISION)
    if is_revision_msg:
        return {"action": "REQUEST_REVISION", "parameters": {}}

    # 0.5 Perencanaan Kebutuhan Menu & Porsi Bergizi (Multi-Item)
    if is_planning_msg:
        portions = extract_portions(user_message, default=3000)
        commodities = []
        if "telur" in msg_lower:
            commodities.append("telur")
        if "ayam" in msg_lower or "unggas" in msg_lower:
            commodities.append("ayam")
        if "tahu" in msg_lower:
            commodities.append("tahu")
        if "tempe" in msg_lower:
            commodities.append("tempe")
        if "sapi" in msg_lower or "lembu" in msg_lower:
            commodities.append("sapi")
        if "beras" in msg_lower:
            commodities.append("beras")
        if "wortel" in msg_lower or "sayur" in msg_lower:
            commodities.append("sayur")
        return {
            "action": "PLAN_PROCUREMENT",
            "parameters": {
                "target_portions": portions,
                "commodities": commodities or ["ayam"],
            },
        }

    # 1. Konfirmasi atau Pembatalan Draf CRUD Rekanan / Penerbitan PO (Human-in-the-Loop)
    if session.get("pending_crud"):
        if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
            return {"action": "CANCEL_CRUD", "parameters": {}}
        if any(w in msg_lower for w in [
            "setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan",
            "nonaktifkan", "hapus", "permanen", "proses", "deal",
            "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes", "eksekusi", "delete", "terbitkan"
        ]):
            return {"action": "CONFIRM_CRUD", "parameters": {}}

    # 1.5 Melengkapi data draf rekanan yang masih kurang (pending_supplier_draft)
    if session.get("pending_supplier_draft"):
        if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
            return {"action": "CANCEL_CRUD", "parameters": {}}
        if not has_incident and not any(w in msg_lower for w in ["stok", "freezer", "gudang", "ruang pendingin", "bisa apa"]):
            return {"action": "REGISTER_SUPPLIER", "parameters": {}}

    # 2. Approval PO (Mitigasi Darurat atau Draf Perencanaan Pengadaan)
    if (session.get("current_recommendation") or session.get("procurement_plan")) and any(
        w in msg_lower for w in ["setuju", "deal", "buatkan po", "terbitkan", "approve", "buatkan po untuk rencana", "buatkan draf po", "terbitkan po"]
    ):
        return {"action": "APPROVE_PO", "parameters": {}}

    # 3. Manajemen CRUD Rekanan
    if any(k in msg_lower for k in ["tambah", "daftarkan", "mitra baru", "supplier baru", "rekanan baru"]):
        return {"action": "REGISTER_SUPPLIER", "parameters": {}}
    if any(k in msg_lower for k in ["update", "ubah harga", "ubah kapasitas", "naikkan harga", "turunkan"]):
        return {"action": "UPDATE_SUPPLIER", "parameters": {}}
    if any(k in msg_lower for k in ["hapus suplier", "hapus supplier", "hapus rekanan", "nonaktifkan", "coret", "putus kontrak"]):
        return {"action": "DEACTIVATE_SUPPLIER", "parameters": {}}

    # 4. Arsip Dokumen
    if any(k in msg_lower for k in ["bersihkan dokumen", "hapus semua dokumen", "clear document", "hapus arsip", "kosongkan surat"]):
        return {"action": "CLEAR_DOCUMENTS", "parameters": {}}
    if any(k in msg_lower for k in ["hapus salah satu", "hapus dokumen", "hapus surat", "hapus po"]):
        return {"action": "DELETE_DOCUMENT", "parameters": {}}

    # 5. Inquiry Katalog & Stok
    if any(w in msg_lower for w in ["suplier", "supplier", "vendor", "rekanan", "mitra"]) and any(w in msg_lower for w in ["siapa", "apa aja", "daftar", "list", "ada berapa", "spill", "cek"]):
        return {"action": "LIST_SUPPLIERS", "parameters": {}}
    if any(w in msg_lower for w in ["stok", "freezer", "gudang", "ruang pendingin", "sisa bahan", "inventaris"]):
        return {"action": "GET_INVENTORY", "parameters": {}}

    # 6. Sapaan & Kapabilitas
    if any(w in msg_lower for w in ["bisa apa", "fitur apa", "bisa crud", "kemampuan"]):
        return {"action": "EXPLAIN_CAPABILITIES", "parameters": {}}
    if any(w in msg_lower for w in ["halo", "hai", "selamat pagi", "assalamualaikum"]):
        return {"action": "GREETING", "parameters": {}}

    # 7. Insiden / Darurat
    if has_incident:
        return {"action": "REPORT_INCIDENT", "parameters": {}}

    return {"action": "GENERAL_CHAT", "parameters": {}}

