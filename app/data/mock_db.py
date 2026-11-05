from typing import Dict
from app.models.schemas import InventoryItem, SupplierRecord

# ==========================================
# 1. MASTER INVENTARIS BAHAN PANGAN SPPG
# ==========================================
INVENTORY_DB: Dict[str, InventoryItem] = {
    "ITEM-AYAM-01": InventoryItem(
        item_id="ITEM-AYAM-01",
        item_name="Daging Ayam Broiler Segar",
        category="PROTEIN",
        current_stock_kg=80.0,
        safety_stock_kg=30.0,
        freezer_capacity_kg=100.0,
        freezer_occupied_kg=80.0,
        sop_max_price_per_kg=42000.0,
    ),
    "ITEM-BERAS-01": InventoryItem(
        item_id="ITEM-BERAS-01",
        item_name="Beras Premium Ramos",
        category="STAPLE",
        current_stock_kg=500.0,
        safety_stock_kg=150.0,
        freezer_capacity_kg=0.0,
        freezer_occupied_kg=0.0,
        sop_max_price_per_kg=16500.0,
    ),
    "ITEM-TELUR-01": InventoryItem(
        item_id="ITEM-TELUR-01",
        item_name="Telur Ayam Ras Segar",
        category="PROTEIN",
        current_stock_kg=120.0,
        safety_stock_kg=50.0,
        freezer_capacity_kg=60.0,
        freezer_occupied_kg=40.0,
        sop_max_price_per_kg=31000.0,
    ),
    "ITEM-WORTEL-01": InventoryItem(
        item_id="ITEM-WORTEL-01",
        item_name="Wortel Segar Brastagi",
        category="VEGETABLE",
        current_stock_kg=45.0,
        safety_stock_kg=20.0,
        freezer_capacity_kg=40.0,
        freezer_occupied_kg=25.0,
        sop_max_price_per_kg=18000.0,
    ),
}

# Standar gramasi kebutuhan per porsi makanan SPPG (kg/porsi)
PORTION_REQUIREMENTS: Dict[str, float] = {
    "ITEM-AYAM-01": 0.04,   # 40 gram daging per porsi
    "ITEM-BERAS-01": 0.10,  # 100 gram beras per porsi
    "ITEM-TELUR-01": 0.05,  # 1 butir (~50g) per porsi
    "ITEM-WORTEL-01": 0.03, # 30 gram sayur per porsi
}

# ==========================================
# 2. KATALOG SUPPLIER REKANAN SPPG
# ==========================================
SUPPLIERS_DB: Dict[str, SupplierRecord] = {
    "SUP-UTAMA-01": SupplierRecord(
        supplier_id="SUP-UTAMA-01",
        supplier_name="PT Unggas Sejahtera Nusantara",
        category="PROTEIN",
        halal_certified=True,
        halal_cert_number="ID32110000123450124",
        unit_price_idr=37500.0,
        daily_capacity_kg=300.0,
        lead_time_hours=2.5,
        distance_km=12.0,
        reliability_rating=96.0,
    ),
    "SUP-ALT-01": SupplierRecord(
        supplier_id="SUP-ALT-01",
        supplier_name="CV Berkah Ternak Barokah",
        category="PROTEIN",
        halal_certified=True,
        halal_cert_number="ID32110000543210224",
        unit_price_idr=39500.0,
        daily_capacity_kg=150.0,
        lead_time_hours=3.5,
        distance_km=18.0,
        reliability_rating=92.0,
    ),
    "SUP-ALT-02": SupplierRecord(
        supplier_id="SUP-ALT-02",
        supplier_name="PT Berkah Unggas Jaya",
        category="PROTEIN",
        halal_certified=True,
        halal_cert_number="ID32110000897650324",
        unit_price_idr=38000.0,
        daily_capacity_kg=120.0,
        lead_time_hours=4.0,
        distance_km=22.0,
        reliability_rating=95.0,
    ),
    "SUP-ALT-03": SupplierRecord(
        supplier_id="SUP-ALT-03",
        supplier_name="UD Ayam Murah Meriah (Uncertified)",
        category="PROTEIN",
        halal_certified=False,  # Hard-gate control: Wajib terfilter!
        halal_cert_number=None,
        unit_price_idr=32000.0,
        daily_capacity_kg=200.0,
        lead_time_hours=2.0,
        distance_km=10.0,
        reliability_rating=70.0,
    ),
    "SUP-ALT-04": SupplierRecord(
        supplier_id="SUP-ALT-04",
        supplier_name="PT Logistik Pangan Antar-Kota",
        category="PROTEIN",
        halal_certified=True,
        halal_cert_number="ID32110000999990424",
        unit_price_idr=40000.0,
        daily_capacity_kg=250.0,
        lead_time_hours=12.0,
        distance_km=180.0,  # Melebihi radius toleransi logistik standar
        reliability_rating=88.0,
    ),
}

