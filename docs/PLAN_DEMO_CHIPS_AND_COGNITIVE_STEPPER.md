# Rencana Kerja: 1-Click Interactive Demo Chips & Cognitive Execution Stepper (Tahap 1)

**Target Kompetisi:** GTNIC 2026 – AI Agent Development (Enterprise Productivity)  
**Studi Kasus:** Satuan Pelayanan Pemenuhan Gizi (SPPG) / Program Pemenuhan Pangan Skala Besar  
**Tujuan Dokumen:** Panduan teknis dan desain implementasi dua fitur strategis untuk memaksimalkan skor penjurian (*Agentic Architecture*, *Technical Rigor*, dan *Live Pitching Experience*).

---

## 1. Latar Belakang & Nilai Tambah bagi Penjurian Lomba

Dalam kompetisi agen AI tingkat enterprise, juri mengevaluasi produk melalui demonstrasi langsung (*live demo* berdurasi 3–5 menit). Dua tantangan utama yang dihadapi peserta adalah:
1. **Risiko Presentasi Manual:** Mengetik skenario panjang secara manual rawan salah ketik (*typo*), memakan waktu presentasi, dan terasa lambat bagi juri.
2. **Persepsi "Just Another Wrapper":** Jika agen hanya menampilkan balasan teks atau kartu hasil akhir tanpa memperlihatkan proses kognitif di belakang layar, juri bisa salah mengira bahwa aplikasi hanyalah antarmuka percakapan biasa (*chat wrapper*), bukan arsitektur agen hibrida dengan auditabilitas tinggi (*Stateful Multi-Stage Pipeline*).

### Solusi Strategis ResilioAI:
- **Fitur 1: 1-Click Interactive Demo Chips:** Baris tombol skenario operasional yang memungkinkan presenter/juri memicu skenario kritis enterprise (bencana rantai pasok, penyusunan menu gizi, validasi rekanan) hanya dengan satu klik.
- **Fitur 2: Cognitive Execution Stepper / Audit Trace:** Komponen visual interaktif pada setiap pesan balasan AI yang menampilkan jejak eksekusi multi-tahap (Kueri Database ACID, Filter Regulasi Halal, Skoring 7 Parameter, hingga Gerbang Otorisasi Manusia).

---

## 2. Rincian Desain Fitur 1: 1-Click Interactive Demo Chips

### 2.1 Lokasi & Penempatan pada Antarmuka
Diletakkan tepat di atas formulir input pesan pada tab **Obrolan AI** (`frontend/app/page.tsx`), sehingga mudah diakses kapan saja tanpa menutupi riwayat percakapan.

### 2.2 Daftar 4 Skenario Presets Enterprise
| No | Label Chip & Ikon | Teks Pesan Otomatis | Aspek Penjurian yang Ditonjolkan |
| :--- | :--- | :--- | :--- |
| **1** | 🚨 **Disrupsi Banjir Pantura** | *"Armada supplier ayam utama PT Unggas Sejahtera terjebak banjir di jalur Pantura, segera mitigasi"* | **Emergency Response:** Menunjukkan deteksi insiden otomatis, kalkulasi defisit stok, eliminasi supplier non-halal, skoring kelayakan 7 parameter, dan split-delivery. |
| **2** | 🍲 **Pengadaan 3000 Porsi Gizi** | *"Bantu susun draf PO untuk pengadaan menu 3000 porsi ayam dan telur hari ini"* | **Multi-Item Planning:** Perencanaan kebutuhan gabungan, kalkulasi gramasi gizi standar BGN, pembagian 2 dokumen PO terpisah dengan mitigasi pagu harga aman. |
| **3** | 📝 **Uji Registrasi Rekanan** | *"Tolong daftarkan supplier baru UD Sapi Segar Jaya, komoditas daging Sapi, harga Rp 44.000 per kg, kapasitas harian 200 kg, jarak 12 km, halal aktif nomor sertifikat ID-HALAL-2026-0088"* | **Multi-Turn Robustness:** AI secara cerdas menahan kartu, meminta data waktu kirim yang belum ada, lalu menyatukan data saat dikirim pesan susulan *"waktu kirimnya 2 jam"*. |
| **4** | ❄️ **Audit Rantai Dingin** | *"Cek sisa stok bahan baku dan kapasitas ruang pendingin freezer gudang"* | **Zero Hallucination:** Kueri langsung ke basis data SQLite tanpa halusinasi inventaris. |

### 2.3 Interaksi Pengguna (UX Behavior)
- Pengguna dapat mengklik chip untuk langsung mengeksekusi pesan (`handleSendMessage(prompt)`).
- Terdapat opsi tombol kecil *"Salin ke Input"* jika pengguna ingin mengubah parameter sebelum mengirim.
- Desain chip: Kapsul modern dengan *subtle background* (Tailwind: `bg-slate-50 border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-all text-xs font-medium text-slate-700`).

---

## 3. Rincian Desain Fitur 2: Cognitive Stepper / Execution Trace

### 3.1 Kontrak Data Backend (Pydantic Schema)
Tambahkan skema jejak kognitif pada `app/models/schemas.py`:

```python
class ExecutionTraceStep(BaseModel):
    step_number: int  # 1, 2, 3, 4, 5
    stage: str  # "DATA_LAYER", "COMPLIANCE_FILTER", "STRATEGIC_REASONING", "FEASIBILITY_GATE", "HUMAN_APPROVAL_GATE"
    title: str  # misal: "Verifikasi Basis Data SQLite SPPG (ACID)"
    status: str  # "COMPLETED" | "WAITING_APPROVAL" | "FLAGGED"
    details: str  # Rincian fakta numerik hasil eksekusi deterministik
    execution_time_ms: int  # Durasi eksekusi node (misal: 14 ms)

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: ChatIntent
    action_required: ChatActionRequired
    preview_data: Optional[Dict[str, Any]] = None
    execution_trace: Optional[List[ExecutionTraceStep]] = None  # <-- Field Baru
```

### 3.2 Metadata Jejak per Skenario
1. **Skenario Insiden & Mitigasi (`incident_handler.py`):**
   - Step 1: `Ingestion & Entity Matching` (Mencocokkan nama armada/supplier ke SQLite).
   - Step 2: `Deterministic Data Layer` (Kueri stok aktual, sisa freezer, kalkulasi defisit kuantitas).
   - Step 3: `Compliance Filter` (Verifikasi kepatuhan sertifikat halal UU 33/2014 & eliminasi rekanan berisiko).
   - Step 4: `Strategic Agent Synthesis` (Alokasi pengadaan cadangan & skema logistik split-delivery).
   - Step 5: `7-Parameter Feasibility Scoring` (Perhitungan skor deterministik matriks 7 parameter).
   - Step 6: `Human-in-the-Loop Interrupt` (Menahan status menunggu otorisasi Kepala SPPG).

2. **Skenario Perencanaan Pengadaan Menu (`planning_handler.py`):**
   - Step 1: `Nutritional Need Calculation` (Kalkulasi gramasi standar BGN untuk 3000 porsi).
   - Step 2: `Inventory Deduction` (Pemotongan sisa stok di gudang dan freezer).
   - Step 3: `Multi-Supplier Matching` (Pemilihan rekanan terdaftar resmi untuk ayam dan telur).
   - Step 4: `Budget Compliance Check` (Validasi pagu anggaran maksimal SOP BGN).
   - Step 5: `Draft PO Staging` (Penerbitan nomor draf PO menunggu persetujuan).

3. **Skenario Registrasi Rekanan (`supplier_handler.py`):**
   - Step 1: `Multi-Field Semantic Extraction` (Ekstraksi 5 parameter wajib pendaftaran).
   - Step 2: `Operational Completeness Verification` (Pemeriksaan kelengkapan waktu kirim).
   - Step 3: `Halal BPJPH Verification` (Pemeriksaan nomor sertifikat halal aktif).
   - Step 4: `SOP Ceiling Evaluation` (Perbandingan harga penawaran terhadap pagu SOP bahan).
   - Step 5: `Pending State Staging` (Penyimpanan draf ke session untuk otorisasi manusia).

### 3.3 Visualisasi Stepper di Frontend (`frontend/app/page.tsx`)
- Tepat di atas balasan asisten AI, muncul bilah info ringkas:
  `⚡ Jejak Kognitif Agen: 5 Node Selesai (100% Deterministic & Halal Verified) • [Lihat Detail ▼]`
- Saat diklik (toggle accordion):
  Menampilkan tampilan visual vertikal yang bersih:
  - 🟢 **Step 1:** Verifikasi Basis Data SQLite SPPG (Selesai, 12ms)
    *Stok ayam: 80 kg | Freezer tersedia: 20 kg | Defisit: 64 kg.*
  - 🟢 **Step 2:** Filter Kepatuhan Regulasi Halal UU 33/2014 (Selesai, 4ms)
    *1 supplier non-halal dieliminasi dari daftar kandidat darurat.*
  - 🟢 **Step 3:** Penalaran Strategis Logistik Agen (Selesai, 450ms)
    *Skema split-delivery dirumuskan: Batch 1 (20 kg) & Batch 2 (44 kg).*
  - 🟢 **Step 4:** Validasi Matriks 7 Parameter Feasibility (Selesai, 2ms)
    *Skor Kelayakan: 88.5/100 (Status: FEASIBLE).*
  - 🟡 **Step 5:** Gerbang Otorisasi Kepala SPPG (Menunggu Keputusan)
    *Draf PO resmi disiapkan, menunggu klik otorisasi dari Bapak Adam.*

---

## 4. Tahapan Pengerjaan & Rencana Implementasi

### Tahap 1: Backend Model & Handler Tracing
- [ ] Memperbarui `app/models/schemas.py` untuk menambahkan skema `ExecutionTraceStep` dan field `execution_trace` di `ChatResponse`.
- [ ] Menambahkan utilitas pembentuk trace di `app/engine/agent/handlers/`:
  - `incident_handler.py`: Menyuntikkan 5 tahap eksekusi mitigasi bencana.
  - `planning_handler.py`: Menyuntikkan 5 tahap eksekusi perencanaan multi-item gizi.
  - `supplier_handler.py`: Menyuntikkan tahap validasi pendaftaran rekanan.
- [ ] Menjalankan verifikasi AST untuk memastikan **0 fungsi duplikat** di seluruh modul backend.

### Tahap 2: Frontend Types & State Integration
- [ ] Memperbarui antarmuka TypeScript di `frontend/types/incident.ts` agar mengenali `ExecutionTraceStep` dan `execution_trace`.
- [ ] Mengintegrasikan penanganan `execution_trace` pada pemanggilan API chat di `frontend/app/page.tsx`.

### Tahap 3: Pembuatan Komponen UI di Frontend
- [ ] **Komponen Preset Chips:** Menambahkan baris tombol interaktif 4 skenario demo enterprise di atas kolom teks input chat.
- [ ] **Komponen Cognitive Stepper Accordion:** Menambahkan accordion jejak audit visual pada pesan balasan asisten AI.
- [ ] Memastikan desain responsif, ramah layar laptop presentasi, dan mematuhi estetika profesional (*Tailwind Slate / Modern Enterprise Palette*).

### Tahap 4: Verifikasi & Skenario Pengujian Live Demo
- [ ] Pengujian Unit Backend: Menjalankan test suite (`test_tools.py`, `test_data_layer.py`, `test_supplier_multiturn.py`) memastikan tidak ada regresi.
- [ ] Pengujian End-to-End Chat: Memverifikasi klik tiap chip demo memicu alur secara instan dan menampilkan jejak kognitif yang akurat.
- [ ] Pengujian AST Integrity: Memastikan standar kompetisi terpenuhi dengan 0 fungsi berulang.

---

## 5. Kriteria Keberhasilan (Acceptance Criteria)

1. **Efisiensi Presentasi:** Presenter dapat memicu skenario lengkap insiden logistik hanya dengan **1 klik chip**, tanpa mengetik manual.
2. **Transparansi Kognitif:** Setiap rekomendasi mitigasi atau perencanaan menampilkan jejak audit 5 tahap dengan bukti numerik nyata (bukan teks generik).
3. **Kepatuhan Regulasi Terlihat Jelas:** Status verifikasi halal dan formula 7 parameter kelayakan terpampang eksplisit di stepper jejak kognitif.
4. **Stabilitas Sistem:** Seluruh unit test lulus 100% dan tidak ada *layout breaking* pada antarmuka pengguna.

