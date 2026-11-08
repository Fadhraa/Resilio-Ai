import json
from pathlib import Path
from typing import Dict, Optional
from app.models.schemas import InventoryItem, SupplierRecord

DATA_DIR = Path(__file__).resolve().parent
SUPPLIERS_JSON_PATH = DATA_DIR / "suppliers.json"
INVENTORY_JSON_PATH = DATA_DIR / "inventory.json"

# ==========================================
# 1. DEFAULT DATASETS (FALLBACK & SEED)
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
    "SUP-ALT-01": {
        "supplier_id": "SUP-ALT-01",
        "supplier_name": "CV Berkah Ternak Barokah",
        "category": "PROTEIN",
        "commodity": "DAGING_AYAM",
        "supported_items": ["ITEM-AYAM-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000543210224",
        "unit_price_idr": 39500.0,
        "daily_capacity_kg": 150.0,
        "lead_time_hours": 3.5,
        "distance_km": 18.0,
        "reliability_rating": 92.0,
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
        "unit_price_idr": 38000.0,
        "daily_capacity_kg": 120.0,
        "lead_time_hours": 4.0,
        "distance_km": 22.0,
        "reliability_rating": 95.0,
        "is_active": True,
    },
    "SUP-ALT-03": {
        "supplier_id": "SUP-ALT-03",
        "supplier_name": "UD Ayam Murah Meriah (Uncertified)",
        "category": "PROTEIN",
        "commodity": "DAGING_AYAM",
        "supported_items": ["ITEM-AYAM-01"],
        "halal_certified": False,
        "halal_cert_number": None,
        "unit_price_idr": 32000.0,
        "daily_capacity_kg": 200.0,
        "lead_time_hours": 2.0,
        "distance_km": 10.0,
        "reliability_rating": 70.0,
        "is_active": True,
    },
    "SUP-ALT-04": {
        "supplier_id": "SUP-ALT-04",
        "supplier_name": "PT Logistik Pangan Antar-Kota",
        "category": "PROTEIN",
        "commodity": "DAGING_AYAM",
        "supported_items": ["ITEM-AYAM-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000999990424",
        "unit_price_idr": 40000.0,
        "daily_capacity_kg": 250.0,
        "lead_time_hours": 12.0,
        "distance_km": 180.0,
        "reliability_rating": 88.0,
        "is_active": True,
    },
    "SUP-SAPI-01": {
        "supplier_id": "SUP-SAPI-01",
        "supplier_name": "PT Lembu Barokah Nusantara",
        "category": "PROTEIN",
        "commodity": "DAGING_SAPI",
        "supported_items": ["ITEM-SAPI-01"],
        "halal_certified": True,
        "halal_cert_number": "ID32110000778890524",
        "unit_price_idr": 128000.0,
        "daily_capacity_kg": 200.0,
        "lead_time_hours": 3.0,
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
# 2. JSON PERSISTENCE & MANAGEMENT ENGINE
# ==========================================
def load_inventory_from_json(filepath: Optional[Path] = None) -> Dict[str, InventoryItem]:
    """Membaca inventaris dari berkas JSON, atau inisialisasi dari default seed jika belum ada."""
    target_path = filepath or INVENTORY_JSON_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: InventoryItem.model_validate(v) for k, v in data.items()}
        except Exception:
            pass

    # Inisialisasi dari DEFAULT_INVENTORY jika berkas belum ada atau rusak
    res = {k: InventoryItem.model_validate(v) for k, v in DEFAULT_INVENTORY.items()}
    save_inventory_to_json(target_path, res)
    return res


def load_suppliers_from_json(filepath: Optional[Path] = None) -> Dict[str, SupplierRecord]:
    """Membaca katalog supplier dari berkas JSON, atau inisialisasi dari default seed jika belum ada."""
    target_path = filepath or SUPPLIERS_JSON_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: SupplierRecord.model_validate(v) for k, v in data.items()}
        except Exception:
            pass

    # Inisialisasi dari DEFAULT_SUPPLIERS jika berkas belum ada atau rusak
    res = {k: SupplierRecord.model_validate(v) for k, v in DEFAULT_SUPPLIERS.items()}
    save_suppliers_to_json(target_path, res)
    return res


def save_inventory_to_json(filepath: Optional[Path] = None, data: Optional[Dict[str, InventoryItem]] = None) -> None:
    """Menyimpan data inventaris aktif ke berkas JSON dengan format rapi (indent=2)."""
    target_path = filepath or INVENTORY_JSON_PATH
    source = data if data is not None else INVENTORY_DB
    dumped = {k: v.model_dump() for k, v in source.items()}
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(dumped, f, indent=2, ensure_ascii=False)


def save_suppliers_to_json(filepath: Optional[Path] = None, data: Optional[Dict[str, SupplierRecord]] = None) -> None:
    """Menyimpan data supplier aktif ke berkas JSON dengan format rapi (indent=2)."""
    target_path = filepath or SUPPLIERS_JSON_PATH
    source = data if data is not None else SUPPLIERS_DB
    dumped = {k: v.model_dump() for k, v in source.items()}
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(dumped, f, indent=2, ensure_ascii=False)


def reload_db_from_json() -> None:
    """Memperbarui memori INVENTORY_DB dan SUPPLIERS_DB dari berkas JSON."""
    inv = load_inventory_from_json()
    INVENTORY_DB.clear()
    INVENTORY_DB.update(inv)

    sups = load_suppliers_from_json()
    SUPPLIERS_DB.clear()
    SUPPLIERS_DB.update(sups)


def reset_db_to_default() -> None:
    """Mereset data inventaris dan supplier kembali ke seed bawaan dan menyimpannya ke JSON."""
    INVENTORY_DB.clear()
    INVENTORY_DB.update({k: InventoryItem.model_validate(v) for k, v in DEFAULT_INVENTORY.items()})
    save_inventory_to_json()

    SUPPLIERS_DB.clear()
    SUPPLIERS_DB.update({k: SupplierRecord.model_validate(v) for k, v in DEFAULT_SUPPLIERS.items()})
    save_suppliers_to_json()


# ==========================================
# 3. GLOBAL ACTIVE REPOSITORIES
# ==========================================
INVENTORY_DB: Dict[str, InventoryItem] = load_inventory_from_json()
SUPPLIERS_DB: Dict[str, SupplierRecord] = load_suppliers_from_json()
