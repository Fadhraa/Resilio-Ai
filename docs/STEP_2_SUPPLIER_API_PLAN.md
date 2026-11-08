# Dokumen Teknis: Step 2 - Endpoint REST API CRUD Supplier

## 🎯 Tujuan & Lingkup Pekerjaan
Menyediakan antarmuka **RESTful API v1** yang standar, terstruktur, dan tervalidasi di `app/api/v1/router.py` agar rekan tim (*frontend Next.js*) dapat mengelola data rekanan supplier secara langsung melalui antarmuka web (Dashboard/Tabel Supplier), melengkapi interaksi via Chat AI.

---

## 🛣️ Rincian Endpoint yang Dibangun

### 1. `GET /api/v1/suppliers` (Daftar Rekanan)
* **Deskripsi:** Mengambil katalog seluruh rekanan supplier yang terdaftar.
* **Query Parameters:**
  * `commodity` (`Optional[str]`): Filter komoditas spesifik (misal `DAGING_AYAM`, `DAGING_SAPI`, `TELUR_AYAM`).
  * `include_inactive` (`bool = False`): Jika `False`, hanya menampilkan rekanan aktif. Jika `True`, menyertakan rekanan yang di-soft delete.
* **Response:** `200 OK` dengan array JSON profil supplier.

### 2. `GET /api/v1/suppliers/{supplier_id}` (Detail Rekanan)
* **Deskripsi:** Mengambil data spesifik satu rekanan.
* **Path Parameter:** `supplier_id` (misal `SUP-UTAMA-01`, `SUP-REG-01`).
* **Response:**
  * `200 OK`: Data profil lengkap supplier.
  * `404 Not Found`: Jika ID tidak terdaftar di basis data.

### 3. `POST /api/v1/suppliers` (Registrasi Rekanan Baru)
* **Deskripsi:** Mendaftarkan mitra supplier baru dengan verifikasi regulasi Halal dan pagu SOP otomatis.
* **Request Body:** `SupplierCreateRequest`.
* **Integrasi Engine:** Memanggil fungsi deterministik `register_supplier_tool`.
* **Response:**
  * `201 Created`: ID baru (`SUP-REG-XX`), data profil, dan catatan audit kepatuhan (*Halal note & SOP price warning*).
  * `422 Unprocessable Entity`: Jika payload gagal validasi Pydantic.

### 4. `PATCH /api/v1/suppliers/{supplier_id}` (Pembaruan Parsial Rekanan)
* **Deskripsi:** Memperbarui satu atau beberapa atribut rekanan (harga penawaran, kapasitas harian, sertifikat halal, dll).
* **Path Parameter:** `supplier_id`.
* **Request Body:** `SupplierUpdateRequest`.
* **Integrasi Engine:** Memanggil fungsi `update_supplier_tool`.
* **Response:**
  * `200 OK`: Data profil terbaru beserta daftar atribut yang diperbarui.
  * `404 Not Found`: Jika `supplier_id` tidak ditemukan.

### 5. `DELETE /api/v1/suppliers/{supplier_id}` (Soft-Delete / Deaktivasi)
* **Deskripsi:** Menonaktifkan rekanan dari alur operasional SPPG (*is_active = False*) tanpa menghapus baris fisik basis data.
* **Path Parameter:** `supplier_id`.
* **Query Parameter:** `reason` (`Optional[str]`): Alasan penonaktifan.
* **Integrasi Engine:** Memanggil fungsi `deactivate_supplier_tool`.
* **Response:**
  * `200 OK`: Konfirmasi deaktivasi dan status keaktifan terbaru.
  * `404 Not Found`: Jika `supplier_id` tidak ditemukan.

---

## 🧪 Rencana Pengujian Integrasi API (`tests/test_api.py`)
Menambahkan skenario uji `test_suppliers_rest_crud_lifecycle`:
1. `POST /api/v1/suppliers` $\rightarrow$ 201 Created.
2. `GET /api/v1/suppliers/{id}` $\rightarrow$ 200 OK.
3. `GET /api/v1/suppliers?commodity=DAGING_SAPI` $\rightarrow$ 200 OK.
4. `PATCH /api/v1/suppliers/{id}` $\rightarrow$ 200 OK.
5. `DELETE /api/v1/suppliers/{id}` $\rightarrow$ 200 OK (soft-delete).
6. `GET /api/v1/suppliers/SUP-TIDAK-ADA` $\rightarrow$ 404 Not Found.

