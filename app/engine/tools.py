import difflib
import re
from typing import Any, Dict, List, Optional
from app.data.mock_db import INVENTORY_DB, SUPPLIERS_DB
from app.models.schemas import SupplierRecord

# Pemetaan sinonim domain pangan SPPG
DOMAIN_SYNONYMS = {
    "ayam": ["unggas", "ayam", "poultry", "ternak"],
    "unggas": ["ayam", "unggas", "poultry", "ternak"],
    "daging": ["protein", "daging", "sapi", "kambing"],
    "telur": ["telur", "egg"],
    "beras": ["beras", "padi", "staple"],
}


def search_suppliers_tool(
    query: str,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tool pencarian basis data supplier rekanan SPPG.
    
    Menggunakan zero-overhead matching (exact match, domain synonyms, dan difflib)
    untuk mendeteksi salah ucap / typo dari pengguna tanpa dependensi eksternal yang berat.
    """
    cleaned_query = query.strip().lower()
    target_category = category.strip().upper() if category else None

    # Filter rekanan aktif berdasarkan kategori terlebih dahulu jika ada
    candidate_pool: List[SupplierRecord] = [
        s for s in SUPPLIERS_DB.values()
        if (not target_category or s.category.upper() == target_category)
        and getattr(s, "is_active", True)
    ]

    exact_matches: List[SupplierRecord] = []
    partial_matches: List[SupplierRecord] = []

    # Ekstrak kata-kata relevan dari query
    query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", cleaned_query))

    # Perluas kata pencarian dengan sinonim domain (misal 'ayam' mencakup 'unggas')
    expanded_words = set(query_words)
    for word in query_words:
        if word in DOMAIN_SYNONYMS:
            expanded_words.update(DOMAIN_SYNONYMS[word])

    for s in candidate_pool:
        s_name_lower = s.supplier_name.lower()
        s_id_lower = s.supplier_id.lower()

        # 1. Exact match pada ID atau nama lengkap
        if cleaned_query == s_id_lower or cleaned_query == s_name_lower:
            exact_matches.append(s)
            continue

        # 2. Substring match
        if any(w in s_name_lower for w in query_words if len(w) > 4):
            partial_matches.append(s)
            continue

        # 3. Domain synonym match (misal mencari ayam -> menemukan supplier unggas)
        if any(w in s_name_lower for w in expanded_words):
            partial_matches.append(s)

    if exact_matches:
        return {
            "status": "EXACT_MATCH_FOUND",
            "count": len(exact_matches),
            "suppliers": [s.model_dump() for s in exact_matches],
            "suggestions": [],
        }

    # Jika ada partial/synonym matches, urutkan: supplier utama & halal teratas
    if partial_matches:
        # Prioritaskan supplier utama (SUP-UTAMA) dan yang rating reliabilitas tinggi
        sorted_partial = sorted(
            partial_matches,
            key=lambda s: (0 if "utama" in s.supplier_id.lower() else 1, -s.reliability_rating),
        )
        return {
            "status": "PARTIAL_MATCH_FOUND",
            "count": len(sorted_partial),
            "suppliers": [s.model_dump() for s in sorted_partial],
            "suggestions": [s.supplier_name for s in sorted_partial],
        }

    # 4. Fuzzy similarity matching
    supplier_names = {s.supplier_name.lower(): s for s in candidate_pool}
    close_names = difflib.get_close_matches(cleaned_query, list(supplier_names.keys()), n=3, cutoff=0.2)
    suggested_suppliers = [supplier_names[name] for name in close_names]

    if suggested_suppliers:
        return {
            "status": "FUZZY_SUGGESTION",
            "count": len(suggested_suppliers),
            "suppliers": [s.model_dump() for s in suggested_suppliers],
            "suggestions": [s.supplier_name for s in suggested_suppliers],
        }

    # Fallback: Kembalikan daftar rekanan terdaftar pada kategori tersebut
    fallback_names = [s.supplier_name for s in candidate_pool]
    return {
        "status": "NOT_FOUND",
        "count": 0,
        "suppliers": [],
        "suggestions": fallback_names,
    }


def get_inventory_status_tool(item_id_or_name: str) -> Dict[str, Any]:
    """
    Tool pembacaan status inventaris gudang dan ruang simpan pendingin SPPG.
    """
    cleaned = item_id_or_name.strip().lower()

    for item in INVENTORY_DB.values():
        if (
            cleaned == item.item_id.lower()
            or cleaned == item.item_name.lower()
            or cleaned in item.item_name.lower()
            or any(part in cleaned for part in item.item_name.lower().split())
        ):
            freezer_available = max(0.0, round(item.freezer_capacity_kg - item.freezer_occupied_kg, 2))
            return {
                "status": "FOUND",
                "item_id": item.item_id,
                "item_name": item.item_name,
                "category": item.category,
                "current_stock_kg": item.current_stock_kg,
                "safety_stock_kg": item.safety_stock_kg,
                "freezer_capacity_kg": item.freezer_capacity_kg,
                "freezer_occupied_kg": item.freezer_occupied_kg,
                "freezer_available_kg": freezer_available,
                "sop_max_price_per_kg": item.sop_max_price_per_kg,
            }

    return {
        "status": "NOT_FOUND",
        "suggestions": [it.item_name for it in INVENTORY_DB.values()],
    }
