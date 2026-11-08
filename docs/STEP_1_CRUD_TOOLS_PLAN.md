# Dokumen Teknis: Step 1 - Supplier CRUD Tools & Governance Gatekeeper

## 🎯 Tujuan & Lingkup Pekerjaan
Membangun kumpulan fungsi tools deterministik (*pure Python tools*) di `app/engine/tools.py` untuk mengelola siklus hidup data rekanan supplier SPPG (Create, Read, Update, Deactivate / Soft Delete) dengan validasi Pydantic terstruktur (`SupplierCreateRequest`, `SupplierUpdateRequest`) dan audit kepatuhan regulasi SPPG (UU JPH No. 33/2014 & pagu anggaran SOP).

---

## 🏗️ Spesifikasi Teknis Tools yang Dibangun

### 1. `register_supplier_tool(payload: SupplierCreateRequest) -> Dict[str, Any]`
* **Fungsi:** Mendaftarkan badan usaha / peternak rekanan baru ke basis data SPPG.
* **Logika Kerja:**
  1. Generate ID unik otomatis berbasis sequence: `SUP-REG-01`, `SUP-REG-02`, dst.
  2. **Price Governance Check:** Memeriksa harga penawaran terhadap pagu SOP dari inventaris (`INVENTORY_DB`). Jika melebihi pagu (misal ayam > Rp 42.000/kg), tandai flag peringatan `exceeds_sop_ceiling = True`.
  3. **Halal Compliance Gate:** Jika `halal_certified == False`, tandai status tata kelola `governance_status = "NON_PRIORITY_UNCERTIFIED"` (tidak akan diikutsertakan dalam pengadaan darurat).
  4. Simpan objek `SupplierRecord` ke dalam `SUPPLIERS_DB`.
  5. Mengembalikan hasil registrasi lengkap dengan metadata audit.

### 2. `get_supplier_detail_tool(supplier_id: str) -> Dict[str, Any]`
* **Fungsi:** Mengambil data profil lengkap satu rekanan berdasarkan ID.
* **Logika Kerja:**
  1. Cari `supplier_id` di `SUPPLIERS_DB` (case-insensitive).
  2. Jika ditemukan, kembalikan seluruh profil rekanan beserta status keaktifan (`is_active`).
  3. Jika tidak ditemukan, kembalikan status `NOT_FOUND` dengan pesan error terstruktur.

### 3. `update_supplier_tool(supplier_id: str, updates: SupplierUpdateRequest) -> Dict[str, Any]`
* **Fungsi:** Memperbarui data penawaran harga, kapasitas harian, sertifikat halal, atau jarak pengiriman rekanan.
* **Logika Kerja:**
  1. Validasi keberadaan `supplier_id`.
  2. Lakukan *partial update* hanya pada atribut yang dikirimkan (nilai yang bernilai `None` diabaikan).
  3. Simpan perubahan ke `SUPPLIERS_DB` dan catat timestamp pembaruan.
  4. Kembalikan data profil supplier yang telah diperbarui.

### 4. `deactivate_supplier_tool(supplier_id: str, reason: str) -> Dict[str, Any]`
* **Fungsi:** Menonaktifkan rekanan dari alur operasional pengadaan (*Soft Delete*).
* **Prinsip Standar Industri:**
  * **Tidak menghapus baris data secara permanen (*Hard Delete*)** demi menjaga integritas data riwayat Purchase Order (PO) masa lalu.
  * Mengubah `is_active = False` dan menyematkan catatan alasan penonaktifan (`deactivation_reason`).
  * Rekanan yang non-aktif otomatis diabaikan oleh `get_eligible_suppliers()`.

### 5. `list_all_suppliers_tool(include_inactive: bool = False, commodity: Optional[str] = None) -> List[Dict[str, Any]]`
* **Fungsi:** Mengambil daftar seluruh rekanan dengan filter fleksibel (komoditas, status aktif).

---

## 🧪 Rencana Pengujian Unit (`tests/test_tools.py`)
1. `test_register_supplier_success_with_halal`: Pendaftaran berhasil dengan verifikasi halal dan penomoran ID otomatis.
2. `test_register_supplier_exceeds_sop_price_warning`: Pendaftaran supplier dengan harga di atas pagu memicu peringatan anggaran.
3. `test_get_supplier_detail_success_and_not_found`: Kueri detail supplier valid dan penanganan supplier yang tidak ada.
4. `test_update_supplier_partial_fields`: Pembaruan parsial (misal harga & kapasitas) tanpa mengubah data lain.
5. `test_deactivate_supplier_soft_delete`: Verifikasi status `is_active = False` dan pencatatan alasan.
6. `test_deactivated_supplier_excluded_from_eligibility`: Memastikan supplier yang dinonaktifkan tidak lolos pada fungsi `get_eligible_suppliers()`.

