import difflib
import re
from typing import Any, Dict, List, Optional
from app.data.mock_db import INVENTORY_DB, SUPPLIERS_DB
from app.data.sqlite_db import (
    deactivate_supplier_in_db,
    delete_supplier_permanently_from_db,
    get_all_inventory_items,
    get_all_suppliers,
    get_inventory_item_by_id,
    get_supplier_by_id_from_db,
    upsert_supplier,
)
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

    # Filter rekanan aktif dari basis data SQLite langsung
    db_sups = get_all_suppliers(include_inactive=False)
    candidate_pool: List[SupplierRecord] = [
        SupplierRecord.model_validate(s) for s in db_sups
        if not target_category or s["category"].upper() == target_category
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
        s_name_core = re.sub(r"^(pt|cv|ud)\.?\s+", "", s_name_lower).strip()

        # 1. Exact match pada ID atau nama lengkap (sama persis atau nama/ID supplier disebut lengkap di teks query)
        if (
            cleaned_query == s_id_lower
            or cleaned_query == s_name_lower
            or s_name_lower in cleaned_query
            or (len(s_name_core) >= 5 and s_name_core in cleaned_query)
            or (len(s_id_lower) >= 6 and s_id_lower in cleaned_query)
        ):
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
        # Prioritaskan nama yang paling spesifik / panjang (misal 'PT Unggas Sejahtera Nusantara' vs 'Unggas')
        exact_matches.sort(key=lambda s: len(s.supplier_name), reverse=True)
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
    Tool pembacaan status inventaris gudang dan ruang simpan pendingin SPPG langsung dari SQLite.
    """
    cleaned = item_id_or_name.strip().lower()
    inv_items = get_all_inventory_items()

    for item in inv_items:
        i_id = item["item_id"].lower()
        i_name = item["item_name"].lower()
        if (
            cleaned == i_id
            or cleaned == i_name
            or cleaned in i_name
            or any(part in cleaned for part in i_name.split())
        ):
            freezer_available = max(0.0, round(item["freezer_capacity_kg"] - item["freezer_occupied_kg"], 2))
            return {
                "status": "FOUND",
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "category": item["category"],
                "current_stock_kg": item["current_stock_kg"],
                "safety_stock_kg": item["safety_stock_kg"],
                "freezer_capacity_kg": item["freezer_capacity_kg"],
                "freezer_occupied_kg": item["freezer_occupied_kg"],
                "freezer_available_kg": freezer_available,
                "sop_max_price_per_kg": item["sop_max_price_per_kg"],
            }

    return {
        "status": "NOT_FOUND",
        "suggestions": [it["item_name"] for it in inv_items],
    }


# ==============================================================================
# TOOL CRUD & GOVERNANCE GATEKEEPER SUPPLIER SPPG
# ==============================================================================

def register_supplier_tool(payload: SupplierCreateRequest) -> Dict[str, Any]:
    """
    Tool pendaftaran rekanan supplier baru ke basis data SQLite SPPG.
    
    Melakukan verifikasi tata kelola kepatuhan:
    1. Penomoran ID unik otomatis (SUP-REG-XX) dari basis data SQLite.
    2. Pengecekan pagu anggaran SOP (tabel inventory di SQLite).
    3. Evaluasi sertifikasi Halal (UU JPH No. 33/2014).
    """
    # 1. Generate ID unik terurut langsung dari data SQLite
    all_sups = get_all_suppliers(include_inactive=True)
    existing_reg_numbers = []
    for s in all_sups:
        match = re.match(r"^SUP-REG-(\d+)$", s["supplier_id"])
        if match:
            existing_reg_numbers.append(int(match.group(1)))
    
    next_num = max(existing_reg_numbers, default=0) + 1
    new_id = f"SUP-REG-{next_num:02d}"

    # 2. Pengecekan Pagu Anggaran SOP (Price Governance) dari tabel inventory SQLite
    matched_item = None
    actual_supported_items = list(payload.supported_items)
    comm_lower = payload.commodity.lower()

    all_items = get_all_inventory_items()
    for it in all_items:
        if comm_lower in it["item_name"].lower() or comm_lower in it["item_id"].lower():
            if actual_supported_items == ["ITEM-AYAM-01"] and "ayam" not in comm_lower:
                actual_supported_items = [it["item_id"]]
            matched_item = it
            break

    if not matched_item:
        for i_id in actual_supported_items:
            for it in all_items:
                if it["item_id"] == i_id:
                    matched_item = it
                    break

    if not matched_item:
        for it in all_items:
            if payload.commodity.lower() in it["item_name"].lower() or payload.category.upper() == it["category"].upper():
                matched_item = it
                break

    exceeds_sop_ceiling = False
    sop_max_price = matched_item["sop_max_price_per_kg"] if matched_item else None
    price_warning = None

    if sop_max_price and payload.unit_price_idr > sop_max_price:
        exceeds_sop_ceiling = True
        diff = payload.unit_price_idr - sop_max_price
        price_warning = (
            f"Harga penawaran (Rp {payload.unit_price_idr:,.2f}) melebihi pagu anggaran SOP "
            f"untuk {matched_item['item_name']} (Rp {sop_max_price:,.2f}) sebesar Rp {diff:,.2f} / kg."
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

    # 4. Konstruksi Record dan Persistensi langsung ke SQLite
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
    upsert_supplier(new_supplier.model_dump())
    SUPPLIERS_DB[new_id] = new_supplier

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
    """Mengambil rincian profil lengkap satu rekanan supplier langsung dari SQLite."""
    s = get_supplier_by_id_from_db(supplier_id)
    if s:
        return {
            "status": "FOUND",
            "supplier": s,
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
    Memperbarui sebagian atribut data supplier rekanan langsung pada basis data SQLite (Partial Update).
    """
    existing = get_supplier_by_id_from_db(supplier_id)
    if not existing:
        return {
            "status": "NOT_FOUND",
            "message": f"Supplier '{supplier_id}' tidak ditemukan untuk diperbarui.",
        }

    target_key = existing["supplier_id"]
    update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)
    if not update_dict:
        return {
            "status": "NO_CHANGES",
            "supplier_id": target_key,
            "message": "Tidak ada atribut baru yang dikirimkan untuk diperbarui.",
            "supplier": existing,
        }

    updated_data = {**existing, **update_dict}
    upsert_supplier(updated_data)
    try:
        SUPPLIERS_DB[target_key] = SupplierRecord.model_validate(updated_data)
    except Exception:
        pass

    return {
        "status": "UPDATED",
        "supplier_id": target_key,
        "updated_fields": list(update_dict.keys()),
        "supplier": updated_data,
    }


def deactivate_supplier_tool(
    supplier_id: str,
    reason: str = "Penonaktifan administratif oleh pimpinan SPPG",
) -> Dict[str, Any]:
    """
    Menonaktifkan rekanan supplier (Soft Delete) langsung di basis data SQLite.
    Prinsip: Mengubah status is_active = 0 agar histori audit transaksi masa lalu tetap terjaga.
    """
    existing = get_supplier_by_id_from_db(supplier_id)
    if not existing:
        return {
            "status": "NOT_FOUND",
            "message": f"Supplier '{supplier_id}' tidak ditemukan.",
        }

    actual_sid = existing["supplier_id"]
    s_name = existing["supplier_name"]
    deactivate_supplier_in_db(actual_sid)
    if actual_sid in SUPPLIERS_DB:
        SUPPLIERS_DB[actual_sid] = SUPPLIERS_DB[actual_sid].model_copy(update={"is_active": False})

    return {
        "status": "DEACTIVATED",
        "supplier_id": actual_sid,
        "supplier_name": s_name,
        "is_active": False,
        "reason": reason,
        "message": f"Supplier {s_name} ({actual_sid}) berhasil dinonaktifkan (Soft Delete) dari basis data SQLite.",
    }


def delete_supplier_permanently_tool(supplier_id: str) -> Dict[str, Any]:
    """
    Menghapus rekanan supplier secara fisik dan permanen (Hard Delete) langsung dari SQLite.
    """
    existing = get_supplier_by_id_from_db(supplier_id)
    actual_sid = existing["supplier_id"] if existing else supplier_id
    supplier_name = existing["supplier_name"] if existing else supplier_id

    deleted = delete_supplier_permanently_from_db(actual_sid)
    if not deleted:
        return {
            "status": "NOT_FOUND",
            "message": f"Supplier '{supplier_id}' tidak ditemukan di basis data SQLite.",
        }

    SUPPLIERS_DB.pop(actual_sid, None)

    return {
        "status": "DELETED",
        "supplier_id": actual_sid,
        "supplier_name": supplier_name,
        "message": f"Supplier {supplier_name} ({actual_sid}) berhasil dihapus permanen dari basis data SQLite.",
    }


def list_all_suppliers_tool(
    include_inactive: bool = False,
    commodity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Kueri seluruh daftar rekanan supplier langsung dari SQLite dengan filter komoditas dan status keaktifan."""
    return get_all_suppliers(include_inactive=include_inactive, commodity=commodity)
