import difflib
import re
from typing import Any, Dict, List, Optional
from app.data.mock_db import INVENTORY_DB, SUPPLIERS_DB, save_suppliers_to_json
from app.models.schemas import (
    SupplierCreateRequest,
    SupplierRecord,
    SupplierUpdateRequest,
)

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


# ==============================================================================
# TOOL CRUD & GOVERNANCE GATEKEEPER SUPPLIER SPPG
# ==============================================================================

def register_supplier_tool(payload: SupplierCreateRequest) -> Dict[str, Any]:
    """
    Tool pendaftaran rekanan supplier baru ke basis data SPPG.
    
    Melakukan verifikasi tata kelola kepatuhan:
    1. Penomoran ID unik otomatis (SUP-REG-XX).
    2. Pengecekan pagu anggaran SOP (INVENTORY_DB).
    3. Evaluasi sertifikasi Halal (UU JPH No. 33/2014).
    """
    # 1. Generate ID unik terurut
    existing_reg_numbers = []
    for sid in SUPPLIERS_DB.keys():
        match = re.match(r"^SUP-REG-(\d+)$", sid)
        if match:
            existing_reg_numbers.append(int(match.group(1)))
    
    next_num = max(existing_reg_numbers, default=0) + 1
    new_id = f"SUP-REG-{next_num:02d}"

    # 2. Pengecekan Pagu Anggaran SOP (Price Governance)
    matched_item = None
    actual_supported_items = list(payload.supported_items)
    comm_lower = payload.commodity.lower()

    for it_id, it in INVENTORY_DB.items():
        if comm_lower in it.item_name.lower() or comm_lower in it_id.lower():
            if actual_supported_items == ["ITEM-AYAM-01"] and "ayam" not in comm_lower:
                actual_supported_items = [it_id]
            matched_item = it
            break

    if not matched_item:
        for i_id in actual_supported_items:
            if i_id in INVENTORY_DB:
                matched_item = INVENTORY_DB[i_id]
                break

    if not matched_item:
        for it in INVENTORY_DB.values():
            if payload.commodity.lower() in it.item_name.lower() or payload.category.upper() == it.category.upper():
                matched_item = it
                break

    exceeds_sop_ceiling = False
    sop_max_price = matched_item.sop_max_price_per_kg if matched_item else None
    price_warning = None

    if sop_max_price and payload.unit_price_idr > sop_max_price:
        exceeds_sop_ceiling = True
        diff = payload.unit_price_idr - sop_max_price
        price_warning = (
            f"Harga penawaran (Rp {payload.unit_price_idr:,.2f}) melebihi pagu anggaran SOP "
            f"untuk {matched_item.item_name} (Rp {sop_max_price:,.2f}) sebesar Rp {diff:,.2f} / kg."
        )

    # 3. Kepatuhan Sertifikasi Halal
    if payload.halal_certified:
        governance_status = "VERIFIED_ELIGIBLE"
        halal_note = "Sertifikasi Halal Aktif terverifikasi. Rekanan memenuhi syarat prioritas mitigasi darurat SPPG."
    else:
        governance_status = "NON_PRIORITY_UNCERTIFIED"
        halal_note = (
            "PERINGATAN REGULASI: Rekanan belum bersertifikat Halal. Sesuai UU JPH No. 33/2014 & SOP SPPG, "
            "rekanan ini TIDAK DAPAT dialokasikan untuk pengadaan darurat hingga sertifikasi dipenuhi."
        )

    # 4. Konstruksi Record dan Persistensi ke Database
    new_supplier = SupplierRecord(
        supplier_id=new_id,
        supplier_name=payload.supplier_name.strip(),
        category=payload.category.strip().upper(),
        commodity=payload.commodity.strip().upper(),
        supported_items=actual_supported_items,
        halal_certified=payload.halal_certified,
        halal_cert_number=payload.halal_cert_number.strip() if payload.halal_cert_number else None,
        unit_price_idr=payload.unit_price_idr,
        daily_capacity_kg=payload.daily_capacity_kg,
        lead_time_hours=payload.lead_time_hours,
        distance_km=payload.distance_km,
        reliability_rating=payload.reliability_rating,
        is_active=True,
    )
    SUPPLIERS_DB[new_id] = new_supplier
    save_suppliers_to_json()

    return {
        "status": "CREATED",
        "supplier_id": new_id,
        "supplier": new_supplier.model_dump(),
        "governance": {
            "governance_status": governance_status,
            "halal_certified": payload.halal_certified,
            "halal_note": halal_note,
            "exceeds_sop_ceiling": exceeds_sop_ceiling,
            "sop_max_price_per_kg": sop_max_price,
            "price_warning": price_warning,
        },
    }


def get_supplier_detail_tool(supplier_id: str) -> Dict[str, Any]:
    """Mengambil rincian profil lengkap satu rekanan supplier berdasarkan ID atau nama."""
    cleaned = supplier_id.strip().upper()
    for sid, s in SUPPLIERS_DB.items():
        if sid.upper() == cleaned or s.supplier_name.lower() == supplier_id.strip().lower():
            return {
                "status": "FOUND",
                "supplier": s.model_dump(),
            }

    return {
        "status": "NOT_FOUND",
        "message": f"Supplier '{supplier_id}' tidak terdaftar di basis data SPPG.",
    }


def update_supplier_tool(
    supplier_id: str,
    updates: SupplierUpdateRequest,
) -> Dict[str, Any]:
    """
    Memperbarui sebagian atribut data supplier rekanan (Partial Update).
    
    Nilai None pada payload updates diabaikan sehingga data eksisting tetap utuh.
    """
    cleaned = supplier_id.strip().upper()
    target_key = None
    target_supplier = None

    for sid, s in SUPPLIERS_DB.items():
        if sid.upper() == cleaned or s.supplier_name.lower() == supplier_id.strip().lower():
            target_key = sid
            target_supplier = s
            break

    if not target_supplier:
        return {
            "status": "NOT_FOUND",
            "message": f"Supplier '{supplier_id}' tidak ditemukan untuk diperbarui.",
        }

    update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)
    if not update_dict:
        return {
            "status": "NO_CHANGES",
            "supplier_id": target_key,
            "message": "Tidak ada atribut baru yang dikirimkan untuk diperbarui.",
            "supplier": target_supplier.model_dump(),
        }

    updated_supplier = target_supplier.model_copy(update=update_dict)
    SUPPLIERS_DB[target_key] = updated_supplier
    save_suppliers_to_json()

    return {
        "status": "UPDATED",
        "supplier_id": target_key,
        "updated_fields": list(update_dict.keys()),
        "supplier": updated_supplier.model_dump(),
    }


def deactivate_supplier_tool(
    supplier_id: str,
    reason: str = "Penonaktifan administratif oleh pimpinan SPPG",
) -> Dict[str, Any]:
    """
    Menonaktifkan rekanan supplier (Soft Delete).
    
    Prinsip: Tidak menghapus baris dari basis data agar integritas histori PO masa lalu terjaga.
    """
    cleaned = supplier_id.strip().upper()
    target_key = None
    target_supplier = None

    for sid, s in SUPPLIERS_DB.items():
        if sid.upper() == cleaned or s.supplier_name.lower() == supplier_id.strip().lower():
            target_key = sid
            target_supplier = s
            break

    if not target_supplier:
        return {
            "status": "NOT_FOUND",
            "message": f"Supplier '{supplier_id}' tidak ditemukan.",
        }

    updated = target_supplier.model_copy(update={"is_active": False})
    SUPPLIERS_DB[target_key] = updated
    save_suppliers_to_json()

    return {
        "status": "DEACTIVATED",
        "supplier_id": target_key,
        "supplier_name": updated.supplier_name,
        "is_active": False,
        "reason": reason,
        "message": f"Supplier {updated.supplier_name} ({target_key}) berhasil dinonaktifkan (Soft Delete).",
    }


def list_all_suppliers_tool(
    include_inactive: bool = False,
    commodity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Kueri seluruh daftar rekanan supplier dengan filter komoditas dan status keaktifan."""
    results = []
    target_comm = commodity.strip().upper() if commodity else None

    for s in SUPPLIERS_DB.values():
        if not include_inactive and not getattr(s, "is_active", True):
            continue
        if target_comm and getattr(s, "commodity", "").upper() != target_comm:
            continue
        results.append(s.model_dump())

    return results
