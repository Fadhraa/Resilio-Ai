"""
Modul Data Terpusat SPPG (SQLite Persistent Store Bridge)

Menghubungkan lapisan aplikasi langsung ke basis data relasional SQLite resmi (resilio.db).
Menjamin ACID compliance, Zero Hallucination, dan meniadakan penggunaan berkas JSON statis di disk.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from app.data.sqlite_db import (
    get_all_inventory_items,
    get_all_suppliers,
    get_inventory_item_by_id,
    get_supplier_by_id_from_db,
    init_sqlite_db,
    reset_sqlite_to_default,
    upsert_inventory_item,
    upsert_supplier,
)
from app.models.schemas import InventoryItem, SupplierRecord

DATA_DIR = Path(__file__).resolve().parent

# ==========================================
# 1. DEFAULT DATASETS (SEED / FALLBACK)
# ==========================================
DEFAULT_INVENTORY: Dict[str, Dict] = {
    "ITEM-AYAM-01": {
        "item_id": "ITEM-AYAM-01",
        "item_name": "Daging Ayam Broiler Segar",
        "category": "PROTEIN",
        "current_stock_kg": 80.0,
        "safety_stock_kg": 30.0,
        "freezer_capacity_kg": 100.0,
        "freezer_occupied_kg": 80.0,
        "sop_max_price_per_kg": 42000.0,
    },
    "ITEM-BERAS-01": {
        "item_id": "ITEM-BERAS-01",
        "item_name": "Beras Premium Ramos",
        "category": "STAPLE",
        "current_stock_kg": 500.0,
        "safety_stock_kg": 150.0,
        "freezer_capacity_kg": 0.0,
        "freezer_occupied_kg": 0.0,
        "sop_max_price_per_kg": 16500.0,
    },
    "ITEM-TELUR-01": {
        "item_id": "ITEM-TELUR-01",
        "item_name": "Telur Ayam Ras Segar",
        "category": "PROTEIN",
        "current_stock_kg": 120.0,
        "safety_stock_kg": 50.0,
        "freezer_capacity_kg": 60.0,
        "freezer_occupied_kg": 40.0,
        "sop_max_price_per_kg": 31000.0,
    },
    "ITEM-WORTEL-01": {
        "item_id": "ITEM-WORTEL-01",
        "item_name": "Wortel Segar Brastagi",
        "category": "VEGETABLE",
        "current_stock_kg": 45.0,
        "safety_stock_kg": 20.0,
        "freezer_capacity_kg": 40.0,
        "freezer_occupied_kg": 25.0,
        "sop_max_price_per_kg": 18000.0,
    },
    "ITEM-SAPI-01": {
        "item_id": "ITEM-SAPI-01",
        "item_name": "Daging Sapi Segar (Has Luar)",
        "category": "PROTEIN",
        "current_stock_kg": 50.0,
        "safety_stock_kg": 25.0,
        "freezer_capacity_kg": 80.0,
        "freezer_occupied_kg": 40.0,
        "sop_max_price_per_kg": 135000.0,
    },
    "ITEM-TAHU-01": {
        "item_id": "ITEM-TAHU-01",
        "item_name": "Tahu Putih Segar",
        "category": "PROTEIN",
        "current_stock_kg": 50.0,
        "safety_stock_kg": 20.0,
        "freezer_capacity_kg": 40.0,
        "freezer_occupied_kg": 10.0,
        "sop_max_price_per_kg": 25000.0,
    },
    "ITEM-TEMPE-01": {
        "item_id": "ITEM-TEMPE-01",
        "item_name": "Tempe Kedelai Segar",
        "category": "PROTEIN",
        "current_stock_kg": 40.0,
        "safety_stock_kg": 15.0,
        "freezer_capacity_kg": 30.0,
        "freezer_occupied_kg": 10.0,
        "sop_max_price_per_kg": 22000.0,
    },
}

DEFAULT_SUPPLIERS: Dict[str, Dict] = {
    "SUP-UTAMA-01": {
        "supplier_id": "SUP-UTAMA-01",
        "supplier_name": "PT Unggas Sejahtera Nusantara",
        "category": "PROTEIN",
        "commodity": "DAGING_AYAM",
        "supported_items": ["ITEM-AYAM-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000123450124",
        "unit_price_idr": 37500.0,
        "daily_capacity_kg": 300.0,
        "lead_time_hours": 2.5,
        "distance_km": 12.0,
        "reliability_rating": 96.0,
        "is_active": True,
    },
    "SUP-ALT-02": {
        "supplier_id": "SUP-ALT-02",
        "supplier_name": "PT Berkah Unggas Jaya",
        "category": "PROTEIN",
        "commodity": "DAGING_AYAM",
        "supported_items": ["ITEM-AYAM-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000897650324",
        "unit_price_idr": 36500.0,
        "daily_capacity_kg": 140.0,
        "lead_time_hours": 4.0,
        "distance_km": 22.0,
        "reliability_rating": 95.0,
        "is_active": True,
    },
    "SUP-REG-04": {
        "supplier_id": "SUP-REG-04",
        "supplier_name": "CV Berkah Barokah Tahu",
        "category": "PROTEIN",
        "commodity": "TAHU",
        "supported_items": ["ITEM-TAHU-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000789010124",
        "unit_price_idr": 18000.0,
        "daily_capacity_kg": 200.0,
        "lead_time_hours": 2.5,
        "distance_km": 14.0,
        "reliability_rating": 95.0,
        "is_active": True,
    },
    "SUP-REG-05": {
        "supplier_id": "SUP-REG-05",
        "supplier_name": "CV Berkah Tempe Alami",
        "category": "PROTEIN",
        "commodity": "TEMPE",
        "supported_items": ["ITEM-TEMPE-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000789010224",
        "unit_price_idr": 16000.0,
        "daily_capacity_kg": 180.0,
        "lead_time_hours": 2.5,
        "distance_km": 15.0,
        "reliability_rating": 94.0,
        "is_active": True,
    },
    "SUP-TELUR-01": {
        "supplier_id": "SUP-TELUR-01",
        "supplier_name": "CV Sumber Telur Mandiri",
        "category": "PROTEIN",
        "commodity": "TELUR_AYAM",
        "supported_items": ["ITEM-TELUR-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000445560624",
        "unit_price_idr": 28500.0,
        "daily_capacity_kg": 500.0,
        "lead_time_hours": 2.0,
        "distance_km": 12.0,
        "reliability_rating": 93.0,
        "is_active": True,
    },
}

PORTION_REQUIREMENTS: Dict[str, float] = {
    "ITEM-AYAM-01": 0.04,
    "ITEM-BERAS-01": 0.10,
    "ITEM-TELUR-01": 0.05,
    "ITEM-WORTEL-01": 0.03,
    "ITEM-SAPI-01": 0.05,
    "ITEM-TAHU-01": 0.05,
    "ITEM-TEMPE-01": 0.05,
}


# ==========================================
# 2. SQLITE DATA ACCESS & SYNCHRONIZATION
# ==========================================

def load_inventory_from_sqlite() -> Dict[str, InventoryItem]:
    """Membaca data inventaris aktif langsung dari basis data SQLite resmi."""
    init_sqlite_db()
    items = get_all_inventory_items()
    if not items:
        # Seed awal jika tabel kosong
        for v in DEFAULT_INVENTORY.values():
            upsert_inventory_item(v)
        items = get_all_inventory_items()
    return {item["item_id"]: InventoryItem.model_validate(item) for item in items}


def load_suppliers_from_sqlite() -> Dict[str, SupplierRecord]:
    """Membaca katalog rekanan supplier aktif langsung dari basis data SQLite resmi."""
    init_sqlite_db()
    sups = get_all_suppliers(include_inactive=True)
    if not sups:
        # Seed awal jika tabel kosong
        for v in DEFAULT_SUPPLIERS.values():
            upsert_supplier(v)
        sups = get_all_suppliers(include_inactive=True)
    return {s["supplier_id"]: SupplierRecord.model_validate(s) for s in sups}


# Compatibility wrappers (mengalihkan persistensi ke SQLite secara murni)
def load_inventory_from_json(filepath: Optional[Path] = None) -> Dict[str, InventoryItem]:
    """Wrapper kompatibilitas: membaca inventaris langsung dari SQLite."""
    return load_inventory_from_sqlite()


def load_suppliers_from_json(filepath: Optional[Path] = None) -> Dict[str, SupplierRecord]:
    """Wrapper kompatibilitas: membaca rekanan langsung dari SQLite."""
    return load_suppliers_from_sqlite()


def save_inventory_to_json(filepath: Optional[Path] = None, data: Optional[Dict[str, InventoryItem]] = None) -> None:
    """Wrapper kompatibilitas: menyimpan inventaris langsung ke basis data SQLite."""
    source = data if data is not None else INVENTORY_DB
    for v in source.values():
        upsert_inventory_item(v.model_dump())


def save_suppliers_to_json(filepath: Optional[Path] = None, data: Optional[Dict[str, SupplierRecord]] = None) -> None:
    """Wrapper kompatibilitas: menyimpan rekanan langsung ke basis data SQLite."""
    source = data if data is not None else SUPPLIERS_DB
    for v in source.values():
        upsert_supplier(v.model_dump())


def reload_db_from_json() -> None:
    """Memperbarui memori INVENTORY_DB dan SUPPLIERS_DB dari basis data SQLite."""
    inv = load_inventory_from_sqlite()
    INVENTORY_DB.clear()
    INVENTORY_DB.update(inv)

    sups = load_suppliers_from_sqlite()
    SUPPLIERS_DB.clear()
    SUPPLIERS_DB.update(sups)


def reset_db_to_default() -> None:
    """Mereset data inventaris dan supplier langsung pada basis data SQLite."""
    reset_sqlite_to_default()
    reload_db_from_json()


# ==========================================
# 3. GLOBAL ACTIVE REPOSITORIES
# ==========================================
INVENTORY_DB: Dict[str, InventoryItem] = load_inventory_from_sqlite()
SUPPLIERS_DB: Dict[str, SupplierRecord] = load_suppliers_from_sqlite()
