# RENCANA KERJA TAHAP 1: DATA LAYER & DETERMINISTIC PIPELINE

Dokumen ini merupakan panduan teknis implementasi **Tahap 1** untuk sistem **ResilioAI** (GTNIC 2026).

---

## 1. Tujuan Tahap 1
Membangun fondasi data operasional Satuan Pelayanan Pemenuhan Gizi (SPPG) yang deterministik, presisi matematis, dan berprinsip *Zero Hallucination*:
1. **Penyedia Data Inventaris:** Mengambil stok fisik, kapasitas pendingin (*freezer*), dan pagu SOP anggaran.
2. **Kalkulasi Defisit & Financial Risk:** Menghitung kebutuhan riil berdasarkan target porsi makan bergizi dengan margin pengaman 20%.
3. **Hard-Constraint Filter Supplier:** Memfilter katalog rekanan supplier agar hanya yang bersertifikat Halal aktif dan memenuhi kriteria radius yang diproses ke tahap penalaran LLM.

---

## 2. Struktur Modul & File yang Dibangun

```
app/
├── data/
│   ├── __init__.py
│   └── mock_db.py          # Master data inventaris SPPG & katalog rekanan
├── services/
│   ├── __init__.py
│   └── data_layer.py       # Layanan deterministik kueri & kalkulasi
tests/
├── __init__.py
└── test_data_layer.py      # Pengujian unit otomatis (pytest)
```

---

## 3. Spesifikasi Teknis Implementasi

### 3.1 Dataset Operasional (`app/data/mock_db.py`)
- **Item Pangan:**
  - `ITEM-AYAM-01` (Daging Ayam Broiler Segar, stok 80 kg, safety stock 30 kg, freezer terpakai 80 kg dari 100 kg, SOP max price Rp 42.000/kg).
  - Bahan pendukung: Beras, Telur, Wortel.
- **Katalog Rekanan Supplier:**
  - `SUP-UTAMA-01` (PT Unggas Sejahtera Nusantara - Supplier utama yang mengalami disrupsi).
  - `SUP-ALT-01` (CV Berkah Ternak Barokah - Halal aktif, harga kompetitif, kapasitas memadai).
  - `SUP-ALT-02` (PT Sumber Protein Jaya - Halal aktif, performa tinggi).
  - `SUP-ALT-03` (UD Non Halal Control - Kontrol pengujian, tanpa sertifikat halal, wajib terfilter).

### 3.2 Logika Deterministik (`app/services/data_layer.py`)
- **Formula Defisit:**
  $$\text{Kebutuhan Total} = \text{target\_portions} \times \text{rasio\_kg\_per\_porsi}$$
  $$\text{Defisit (kg)} = \max\Big(0.0, (\text{Kebutuhan Total} \times 1.2) - \text{Stok Aktual}\Big)$$
- **Kapasitas Freezer Tersedia:**
  $$\text{Sisa Freezer (kg)} = \max(0.0, \text{Kapasitas Total} - \text{Kapasitas Terpakai})$$
- **Paparan Risiko Finansial:**
  $$\text{Financial Risk Exposure (IDR)} = \text{Defisit} \times \text{sop\_max\_price\_per\_kg}$$
- **Filter Kepatuhan Supplier:**
  - `halal_certified == True` (*Strict Zero-Tolerance*).
  - `supplier_id != affected_supplier_id`.
  - `distance_km <= max_distance_km`.

---

## 4. Validasi & Pengujian (`tests/test_data_layer.py`)
Pengujian otomatis dilakukan untuk memastikan:
- Untuk 3.000 porsi ayam, defisit menghasilkan tepat **64.0 kg**.
- Sisa kapasitas freezer terhitung tepat **20.0 kg**.
- Supplier non-halal `SUP-ALT-03` wajib dieliminasi dari kandidat rekomendasi.
- Supplier utama `SUP-UTAMA-01` tidak boleh muncul dalam daftar supplier alternatif.

