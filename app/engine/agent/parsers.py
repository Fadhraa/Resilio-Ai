"""
Parsers & Data Extraction Utilities for ResilioAI Cognitive Agent.
Termasuk:
- Pembersihan format output (anti-slop, no LaTeX).
- Database Verification Guardrail: Verifikasi keabsahan rekanan terhadap basis data SQLite sebelum output disajikan.
- Ekstraksi porsi, deteksi inventaris, inferensi komoditas, dan matching supplier.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import SupplierCreateRequest, SupplierRecord


def clean_ai_output(text: str) -> str:
    """Membersihkan output teks dari karakter LaTeX math, salam klise robotik, dan bullet aneh."""
    if not text:
        return ""
    # 1. Hapus salam klise robotik di awal pesan (misal: "Selamat pagi/siang Bapak Adam, Kepala SPPG.")
    cleaned = re.sub(
        r'^\s*(?:Selamat pagi/siang(?:/sore)?|Selamat pagi|Selamat siang|Selamat sore|Selamat malam)[,\.]?\s*(?:Bapak\s+Adam[,\.]?\s*)?(?:Kepala\s+SPPG[,\.]?\s*)?',
        '',
        text,
        flags=re.IGNORECASE,
    ).strip()
    # 2. Hapus tag LaTeX math seperti \(...\), \[...\], $...$, \textbf{}, \textit{}
    cleaned = re.sub(r'\\\(|\\\)', '', cleaned)
    cleaned = re.sub(r'\\\[|\\\]', '', cleaned)
    cleaned = re.sub(r'\$\$', '', cleaned)
    cleaned = re.sub(r'\$(.*?)\$', r'\1', cleaned)
    cleaned = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', cleaned)
    cleaned = re.sub(r'\\textit\{(.*?)\}', r'*\1*', cleaned)
    # 3. Ubah format bullet ganda aneh seperti "* **" atau "- **" menjadi "• **"
    cleaned = re.sub(r'^\s*[\*\-]\s+\*\*', '• **', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*[\*\-]\s+', '• ', cleaned, flags=re.MULTILINE)
    # 4. Rapikan baris kosong berlebih
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def verify_and_sanitize_suppliers(
    text: str,
    valid_suppliers: Optional[List[Dict[str, Any]]] = None,
    target_sup_name: Optional[str] = None,
) -> str:
    """
    Database Verification Guardrail (Post-Generation / Pre-Output Verification):
    Memverifikasi setiap penyebutan badan usaha (PT, CV, UD) di dalam teks luaran AI
    terhadap basis data resmi SQLite SPPG.
    Jika AI menyebutkan nama fiktif / halusinasi (tidak ada di database SQLite),
    nama tersebut langsung digantikan dengan rekanan resmi yang valid dari database.
    """
    if not text:
        return ""
    if valid_suppliers is None:
        try:
            from app.data.sqlite_db import get_all_suppliers
            valid_suppliers = get_all_suppliers(include_inactive=False)
        except Exception:
            valid_suppliers = []

    valid_names = [s["supplier_name"] for s in valid_suppliers]
    
    # Cari pola nama entitas usaha: PT / CV / UD diikuti kata-kata nama perusahaan
    pattern = r'\b(PT|CV|UD)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){1,4})'
    
    def _replace_fake(match):
        full_name = match.group(0).strip()
        # Cek apakah nama ini cocok dengan salah satu supplier terdaftar di SQLite
        is_valid = any(
            v.lower() in full_name.lower() or full_name.lower() in v.lower()
            for v in valid_names
        )
        if not is_valid:
            # Terdeteksi halusinasi! Gunakan target_sup_name jika ada, atau nama supplier valid pertama
            replacement = target_sup_name if target_sup_name else (valid_names[0] if valid_names else full_name)
            return replacement
        return full_name

    sanitized = re.sub(pattern, _replace_fake, text)
    return sanitized


def extract_portions(text: str, default: int = 3000) -> int:
    """Ekstraksi target porsi makanan dari teks percakapan."""
    m = re.search(r'(\d+[\.\d]*)\s*porsi', text.lower())
    if m:
        try:
            return int(m.group(1).replace('.', ''))
        except ValueError:
            pass
    m2 = re.search(r'\b(\d{3,5})\b', text)
    if m2:
        try:
            val = int(m2.group(1))
            if 500 <= val <= 20000:
                return val
        except ValueError:
            pass
    return default


def detect_item_id(text: str) -> str:
    """Deteksi ID komoditas bahan pangan berdasarkan teks input."""
    t_clean = text.lower()
    if "telur" in t_clean:
        return "ITEM-TELUR-01"
    if "ayam" in t_clean or "unggas" in t_clean:
        return "ITEM-AYAM-01"
    if "sapi" in t_clean or "daging sapi" in t_clean or "lembu" in t_clean:
        return "ITEM-SAPI-01"
    if "tahu" in t_clean:
        return "ITEM-TAHU-01"
    if "tempe" in t_clean:
        return "ITEM-TEMPE-01"
    if "beras" in t_clean:
        return "ITEM-BERAS-01"
    if "sayur" in t_clean or "wortel" in t_clean:
        return "ITEM-WORTEL-01"
    return "ITEM-AYAM-01"


def match_supplier_in_text(text: str) -> Optional[Tuple[str, SupplierRecord]]:
    """Mencocokkan supplier yang disebut dalam teks langsung dari basis data SQLite resmi."""
    t_clean = text.strip().lower()
    from app.data.sqlite_db import get_all_suppliers
    db_sups = get_all_suppliers(include_inactive=True)

    # 1. Cek ID persis (misal SUP-UTAMA-01, SUP-ALT-02, SUP-REG-01)
    for s in db_sups:
        if s["supplier_id"].lower() in t_clean:
            return s["supplier_id"], SupplierRecord.model_validate(s)

    # 2. Cek nama supplier lengkap (prioritaskan rekanan yang masih berstatus aktif)
    active_matches = [
        s for s in db_sups
        if s["supplier_name"].lower() in t_clean and s.get("is_active", True)
    ]
    if active_matches:
        active_matches.sort(key=lambda r: len(r["supplier_name"]), reverse=True)
        chosen = active_matches[0]
        return chosen["supplier_id"], SupplierRecord.model_validate(chosen)

    # 3. Fallback jika rekanan non-aktif
    for s in sorted(db_sups, key=lambda r: len(r["supplier_name"]), reverse=True):
        if s["supplier_name"].lower() in t_clean:
            return s["supplier_id"], SupplierRecord.model_validate(s)

    return None


def infer_commodity_and_category(text: str, supplier_name: Optional[str] = None) -> Tuple[str, str, List[str]]:
    """Inferensi semantik komoditas, kategori, dan ID inventaris dari teks dan nama badan usaha."""
    clean_text = text.strip()
    combined = f"{clean_text} {supplier_name or ''}".lower()

    # 1. Frasa eksplisit
    comm_explicit = re.search(
        r"komoditas\s+([A-Za-z0-9_\s]+?)(?:,|\s+(?:harga|kapasitas|dengan|halal|rp|sebesar|kilo|kg)\b|$)",
        clean_text,
        re.IGNORECASE,
    )
    if comm_explicit:
        raw = comm_explicit.group(1).strip().upper().replace(" ", "_")
        if "AYAM" in raw and "TELUR" not in raw:
            return "DAGING_AYAM", "PROTEIN", ["ITEM-AYAM-01"]
        if "TELUR" in raw:
            return "TELUR_AYAM", "PROTEIN", ["ITEM-TELUR-01"]
        if "TAHU" in raw:
            return "TAHU", "PROTEIN", ["ITEM-TAHU-01"]
        if "TEMPE" in raw:
            return "TEMPE", "PROTEIN", ["ITEM-TEMPE-01"]
        if "SAPI" in raw or "LEMBU" in raw:
            return "DAGING_SAPI", "PROTEIN", ["ITEM-SAPI-01"]
        if "BERAS" in raw:
            return "BERAS", "STAPLE", ["ITEM-BERAS-01"]
        if "WORTEL" in raw or "SAYUR" in raw:
            return "SAYUR", "VEGETABLE", ["ITEM-WORTEL-01"]
        return raw, "PROTEIN", [f"ITEM-{raw}-01"]

    # 2. Frasa kontekstual
    price_pattern = re.search(r"([a-z]+)\s*(?:rp|sebesar|\:|\-)?\s*[\d\.]+\s*(?:rb|ribu|k|per kg|\/kg)", clean_text.lower())
    if price_pattern:
        cand = price_pattern.group(1).strip()
        if cand in ["ayam", "unggas"]:
            return "DAGING_AYAM", "PROTEIN", ["ITEM-AYAM-01"]
        if cand in ["telur"]:
            return "TELUR_AYAM", "PROTEIN", ["ITEM-TELUR-01"]
        if cand in ["tahu"]:
            return "TAHU", "PROTEIN", ["ITEM-TAHU-01"]
        if cand in ["tempe"]:
            return "TEMPE", "PROTEIN", ["ITEM-TEMPE-01"]
        if cand in ["sapi", "lembu"]:
            return "DAGING_SAPI", "PROTEIN", ["ITEM-SAPI-01"]

    # 3. Deteksi kata kunci
    if "telur" in combined:
        return "TELUR_AYAM", "PROTEIN", ["ITEM-TELUR-01"]
    if "ayam" in combined or "unggas" in combined or "broiler" in combined:
        return "DAGING_AYAM", "PROTEIN", ["ITEM-AYAM-01"]
    if "tahu" in combined:
        return "TAHU", "PROTEIN", ["ITEM-TAHU-01"]
    if "tempe" in combined:
        return "TEMPE", "PROTEIN", ["ITEM-TEMPE-01"]
    if "sapi" in combined or "lembu" in combined:
        return "DAGING_SAPI", "PROTEIN", ["ITEM-SAPI-01"]
    if "beras" in combined:
        return "BERAS", "STAPLE", ["ITEM-BERAS-01"]
    if "sayur" in combined or "wortel" in combined:
        return "SAYUR", "VEGETABLE", ["ITEM-WORTEL-01"]
    if "ikan" in combined:
        return "IKAN", "PROTEIN", ["ITEM-IKAN-01"]

    return "PROTEIN_LAINNYA", "PROTEIN", ["ITEM-CUSTOM-01"]


def parse_supplier_create_data(
    text: str,
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash-lite",
) -> Optional[SupplierCreateRequest]:
    """Ekstraksi terstruktur pendaftaran supplier baru dari teks percakapan bebas."""
    clean_text = text.strip()
    name_match = re.search(
        r"(?:tambah(?:kan)?|daftar(?:kan)?|supplier baru|rekanan baru)\s+([A-Za-z0-9\.\s]+?)(?:,|\s+(?:komoditas|harga|kapasitas|dengan|halal|rp|sebesar)\b|$)",
        clean_text,
        re.IGNORECASE,
    )
    supplier_name = name_match.group(1).strip() if name_match else None

    price = None
    price_match = re.search(r"(?:harga|rp|sebesar)\s*[:\.]?\s*([\d\.]+)\s*(?:rb|ribu|k)?", clean_text, re.IGNORECASE)
    if price_match:
        try:
            val_str = price_match.group(1).replace(".", "")
            price = float(val_str)
            if "rb" in clean_text.lower() or "ribu" in clean_text.lower() or "k" in clean_text.lower():
                if price < 1000:
                    price *= 1000
        except ValueError:
            price = None

    capacity = None
    cap_match = re.search(r"(?:kapasitas|pasok|supply|stok)\s*[:\.]?\s*([\d\.]+)\s*(?:kg|kilo|ton)?", clean_text, re.IGNORECASE)
    if cap_match:
        try:
            val_str = cap_match.group(1).replace(".", "")
            capacity = float(val_str)
            if "ton" in clean_text.lower():
                capacity *= 1000
        except ValueError:
            capacity = None

    halal_certified = True
    if re.search(r"\b(non-halal|tidak halal|belum halal|tanpa sertifikat)\b", clean_text, re.IGNORECASE):
        halal_certified = False

    halal_cert_number = None
    cert_match = re.search(r"(?:no|nomor|sertifikat|id)\s*[:\.]?\s*(ID[0-9]+|[0-9]{10,})", clean_text, re.IGNORECASE)
    if cert_match:
        halal_cert_number = cert_match.group(1).strip()
    elif halal_certified:
        halal_cert_number = "Tercatat BPJPH"

    lead_time = 3.0
    lt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:jam|hour)", clean_text, re.IGNORECASE)
    if lt_match:
        try:
            lead_time = float(lt_match.group(1))
        except ValueError:
            pass

    distance = 15.0
    dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilo)", clean_text, re.IGNORECASE)
    if dist_match:
        try:
            distance = float(dist_match.group(1))
        except ValueError:
            pass

    commodity, category, supported_items = infer_commodity_and_category(clean_text, supplier_name)

    if (not supplier_name or not price or not capacity) and api_key and not api_key.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                transport="rest",
                google_api_key=api_key,
                timeout=8,
            )
            extract_prompt = (
                "Ekstrak data pendaftaran supplier pangan dari pesan berikut ke format JSON murni tanpa markdown:\n"
                f"\"{text}\"\n\n"
                "Format JSON wajib memiliki field:\n"
                "{\n"
                "  \"supplier_name\": string atau null,\n"
                "  \"unit_price_idr\": float atau null,\n"
                "  \"daily_capacity_kg\": float atau null,\n"
                "  \"halal_certified\": boolean,\n"
                "  \"halal_cert_number\": string atau null,\n"
                "  \"commodity\": string,\n"
                "  \"category\": string,\n"
                "  \"lead_time_hours\": float,\n"
                "  \"distance_km\": float\n"
                "}"
            )
            res = llm.invoke([("user", extract_prompt)])
            raw_content = str(res.content).strip()
            raw_content = re.sub(r"^```json\s*", "", raw_content)
            raw_content = re.sub(r"^```\s*", "", raw_content)
            raw_content = re.sub(r"\s*```$", "", raw_content).strip()
            parsed = json.loads(raw_content)
            if parsed.get("supplier_name") and parsed.get("unit_price_idr") and parsed.get("daily_capacity_kg"):
                p_comm = parsed.get("commodity")
                if p_comm:
                    commodity, category, supported_items = infer_commodity_and_category(p_comm, supplier_name=parsed["supplier_name"])
                return SupplierCreateRequest(
                    supplier_name=str(parsed["supplier_name"]),
                    category=parsed.get("category", category),
                    commodity=commodity,
                    supported_items=supported_items,
                    halal_certified=bool(parsed.get("halal_certified", True)),
                    halal_cert_number=parsed.get("halal_cert_number"),
                    unit_price_idr=float(parsed["unit_price_idr"]),
                    daily_capacity_kg=float(parsed["daily_capacity_kg"]),
                    lead_time_hours=float(parsed.get("lead_time_hours", lead_time)),
                    distance_km=float(parsed.get("distance_km", distance)),
                    reliability_rating=85.0,
                )
        except Exception:
            pass

    if not supplier_name or not price or not capacity:
        return None

    return SupplierCreateRequest(
        supplier_name=supplier_name,
        category=category,
        commodity=commodity,
        supported_items=supported_items,
        halal_certified=halal_certified,
        halal_cert_number=halal_cert_number,
        unit_price_idr=price,
        daily_capacity_kg=capacity,
        lead_time_hours=lead_time,
        distance_km=distance,
        reliability_rating=85.0,
    )
