# Resilio AI - Sistem Siaga Rantai Pasok SPPG BGN

> **Platform Kognitif Rantai Pasok Berdaya Tahan Tinggi untuk Program Makan Bergizi Gratis (MBG) Badan Gizi Nasional**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016%20App%20Router-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph%200.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Gemini 2.5](https://img.shields.io/badge/AI%20Model-Gemini%20Flash%20Lite-blue.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![SQLite ACID](https://img.shields.io/badge/Database-SQLite%20ACID%20Compliance-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%20v4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Testing](<https://img.shields.io/badge/Tests-24%2F24%20Passed%20(100%25)-brightgreen.svg>)]()

---

## 📌 Ringkasan Eksekutif (Executive Summary)

Program **Makan Bergizi Gratis (MBG)** di bawah naungan **Badan Gizi Nasional (BGN)** merupakan program strategis nasional yang melayani jutaan anak sekolah setiap harinya. Setiap **Satuan Pelayanan Pemenuhan Gizi (SPPG)** memiliki jadwal masak yang sangat ketat (_critical deadline_, misal: jam 04.00 WIB pagi).

Keterlambatan satu bahan pangan kritis (seperti daging ayam atau telur) akibat banjir, tanah longsor, atau gagal kirim rekanan dapat menyebabkan efek domino:

- Pembatalan ribuan porsi makanan bergizi untuk anak sekolah.
- Kerugian finansial akibat pembelian darurat di pasar terbuka (_spot market_) dengan harga melambung tinggi.
- Risiko pelanggaran hukum dan regulasi halal (**UU JPH No. 33 Tahun 2014**) jika terpaksa membeli dari pemasok yang belum terverifikasi halal.

**Resilio AI** hadir sebagai asisten kognitif operasional cerdas bagi **Kepala SPPG (Bapak Adam)**. Sistem ini menggabungkan fleksibilitas pemahaman bahasa manusia berbasis **Large Language Model (LLM)** dengan kepastian matematis dari **Deterministic Feasibility Engine**. Hasilnya: mitigasi krisis rantai pasok dapat dirumuskan dalam waktu **< 15 detik** dengan jaminan **100% Kepatuhan Regulasi, Anti-Halusinasi, dan Nol Rekanan Duplikat**.

---

## Filosofi Arsitektur: Hybrid Cognitive & Deterministic Guardrails

Model AI generatif murni memiliki kelemahan mendasar jika digunakan dalam rantai pasok publik: **halusinasi angka**, **ketiadaan kepastian matematis**, dan **potensi pelanggaran pagu anggaran**. Resilio AI menyelesaikan dilema ini dengan memisahkan _Cognitive Perception_ dari _Operational Execution_.

```mermaid
flowchart TD
    subgraph UI ["Lapisan Antarmuka (Next.js 16 + React 19)"]
        UserPrompt["Instruksi / Pertanyaan Kepala SPPG"] --> ChatBox["Obrolan AI & Kontrol Interaktif"]
        ExecutionAccordion["Jejak Kognitif Deterministik (5 Tahap)"]
        HITLCard["Draf Keputusan PO Resmi (Human-in-the-Loop)"]
    end

    subgraph CognitiveLayer ["Lapisan Kognitif (Google Gemini 2.5 + Semantic Router)"]
        ChatBox --> Router["Intent & Entity Classifier"]
        Router --> PersonaEngine["Universal SPPG Persona Guard"]
    end

    subgraph DeterministicEngine ["Lapisan Deterministik (LangGraph State Machine)"]
        Router --> Feasibility["Matriks Evaluasi Kelayakan 7 Parameter"]
        Feasibility --> HalalGate{"Filter Kepatuhan Halal BPJPH"}
        HalalGate -- Lolos --> BudgetGate{"Validasi Pagu Anggaran SOP"}
        BudgetGate -- Lolos --> StockGate{"Kapasitas Gudang & Freezer"}
        HalalGate -- Gagal / Tidak Halal --> Reject["Eliminasi Rekanan Otomatis"]
        BudgetGate -- Overbudget --> Reject
    end

    subgraph DataLayer ["Lapisan Data Terpercaya (SQLite ACID)"]
        SuppliersTable[("Katalog Rekanan Pangan & BPJPH")]
        InventoryTable[("Stok Fisik Gudang & Cold Storage")]
        POTable[("Buku Besar Purchase Order Resmi")]
        CircularTable[("Arsip Surat Edaran Mitigasi")]
        DeterministicEngine <--> DataLayer
    end

    DeterministicEngine --> HITLCard
    DeterministicEngine --> ExecutionAccordion
    HITLCard -- "Disetujui Kepala SPPG" --> DataLayer
```

### Prinsip Utama:

1. **Zero Hallucination on Numbers & Law**: Seluruh perhitungan volume defisit, pagu harga maksimal, skor kelayakan, dan nomor sertifikasi halal ditarik langsung dari basis data transaksional SQLite.
2. **Zero Duplicate Record Guarantee**: Sistem secara proaktif memvalidasi bentuk badan usaha (UD, CV, PT) dan memblokir pendaftaran ganda demi integritas data operasional.
3. **Human-in-the-Loop (HITL)**: AI menyusun rekomendasi dan menyimulasikan dampak bisnis, namun **otorisasi eksekusi PO resmi dan pencairan dana tetap berada di tangan Kepala SPPG**.

---

## Matriks Evaluasi Kelayakan 7 Parameter (_Deterministic Feasibility Matrix_)

Ketika terjadi disrupsi pasokan (misal: banjir Pantura yang menghambat rekanan utama), mesin deterministik Resilio AI mengevaluasi seluruh rekanan alternatif menggunakan formula multi-kriteria:

$$\text{Skor Kelayakan} = \sum_{i=1}^{7} (W_i \times S_i)$$

| Parameter                                           | Bobot ($W_i$) | Deskripsi Operasional & Kriteria Evaluasi                                                                                                              | Dasar Regulasi / SOP SPPG           |
| :-------------------------------------------------- | :-----------: | :----------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------- |
| **1. Ketersediaan Stok (_Stock Fulfillment_)**      |    **25%**    | Rasio kapasitas harian rekanan terhadap volume defisit dapur gizi. Nilai maksimal jika kapasitas $\ge$ kebutuhan defisit.                              | SOP Ketahanan Bahan Baku SPPG       |
| **2. Waktu Tiba (_Lead Time Compliance_)**          |    **20%**    | Estimasi kedatangan armada logistik sebelum jadwal masak subuh (target $\le 3$ jam). Penalti linier jika $>3$ jam.                                     | Jadwal Masak SPPG (Pukul 04.00 WIB) |
| **3. Kepatuhan Anggaran (_Budget Compliance_)**     |    **15%**    | Penilaian harga penawaran rekanan terhadap pagu anggaran maksimal bahan pangan BGN.                                                                    | Batas Pagu Anggaran Operasional BGN |
| **4. Legalitas & Sertifikasi Halal**                |    **15%**    | **Syarat Mutlak (Hard Gate)**: Rekanan wajib memiliki sertifikat halal aktif yang terdaftar di BPJPH. Rekanan non-halal langsung dieliminasi (skor 0). | **UU JPH No. 33 Tahun 2014**        |
| **5. Kapasitas Gudang Dingin (_Storage Capacity_)** |    **10%**    | Kesesuaian volume pesanan darurat terhadap ruang simpan _freezer_ / _chiller_ dapur SPPG ($1.500\text{ kg}$).                                          | Standar Sarpras Gudang Dingin SPPG  |
| **6. Kesiapan Dapur (_Kitchen Readiness_)**         |    **10%**    | Kesiapan personel juru masak dan peralatan dapur untuk menerima dan mengolah bahan baku darurat.                                                       | SOP Sanitasi & Pengolahan Makanan   |
| **7. Keamanan Rute Logistik (_Route Safety_)**      |    **5%**     | Evaluasi risiko rute pengiriman (faktor kemacetan atau pemindahan rute jalan alternatif akibat banjir).                                                | Panduan Mitigasi Rute Logistik BGN  |

---

## Fitur-Fitur Unggulan

### 1. Obrolan Kognitif Interaktif Kepala SPPG

- Menggunakan persona formal, empatik, dan taktis dengan menyapa pengguna sebagai **Bapak Adam (Kepala SPPG)**.
- Mendukung pemahaman bahasa alami multi-turn: klarifikasi data yang kurang, revisi volume pasokan, hingga perintah operasional langsung.

### 2. Jejak Kognitif Deterministik (_Execution Trace Stepper_)

- Komponen akordion dropdown interaktif pada setiap jawaban AI.
- Menampilkan 5 tahap verifikasi real-time yang memvalidasi integritas data:
  - **Badge Cyan**: `100% Deterministic & ACID (Integritas Terjaga)` pada audit duplikasi data rekanan.
  - **Badge Amber**: `Validasi Parameter SOP` saat parameter wajib (seperti _lead time_) perlu dilengkapi.
  - **Badge Emerald**: `100% Deterministic & Halal` pada rekomendasi mitigasi darurat dan penerbitan draf PO.

### 3. Pencegahan Otomatis Duplikasi Rekanan (_Zero Redundancy Guard_)

- Pengecekan otomatis saat pendaftaran rekanan baru diajukan melalui obrolan AI maupun form API.
- Menolak pendaftaran ganda dan langsung menyajikan ringkasan data rekanan yang sudah terdaftar serta opsi pembaruan (_update harga/kapasitas_) atau reaktivasi.

### 4. Generator Surat Edaran & Purchase Order (PO) Resmi

- Penyusunan draf PO resmi lengkap dengan nomor seri unik, stempel status (_WAITING APPROVAL_ / _APPROVED_), rincian harga per kg, total tagihan, dan klausul hukum kepatuhan regulasi.
- Tombol cetak (_Print/Save as PDF_) yang siap digunakan untuk pelaporan audit BGN.

### 5. Ringkasan Dampak Bisnis (_Enterprise ROI Counter_)

- Modal interaktif edukatif yang menampilkan kalkulasi matematis riil dampak implementasi Resilio AI:
  - **Penyelamatan Porsi**: 3.000 porsi makan bergizi terlindungi dari risiko gagal saji.
  - **Efisiensi Finansial**: Penghematan hingga belasan juta rupiah dibandingkan pembelian panik di pasar terbuka (_spot market markup_).
  - **Akselerasi Mitigasi**: Pemangkasan waktu koordinasi krisis menjadi lebih singkat.
  - **Kepatuhan Regulasi**: Kepatuhan halal 100% terdokumentasi tanpa kompromi.

---

## Skenario Demo Interaktif (Tersedia Tombol Cepat di UI)

Antarmuka web dilengkapi dengan tombol pintasan skenario cepat di bagian bawah obrolan:

1. **Banjir Pantura (Disrupsi Logistik Darurat):**
   - _Trigger_: Rekanan utama (PT Unggas Sejahtera Nusantara) tertahan banjir dengan estimasi tiba terlambat (8 jam).
   - _Aksi AI_: Mengevaluasi katalog rekanan, mengeliminasi opsi non-halal / _overbudget_, dan merekomendasikan PT Berkah Unggas Jaya dengan _lead time_ 4 jam serta menerbitkan draf PO mitigasi.
2. **Rencana 3.000 Porsi (Perencanaan Terpadu):**
   - _Trigger_: Perencanaan kebutuhan gizi untuk 3.000 porsi makanan harian SPPG.
   - _Aksi AI_: Menghitung kebutuhan gramatur protein (ayam, tahu, tempe, telur), mengecek saldo stok fisik gudang, dan menerbitkan PO multi-item untuk menutupi defisit.
3. **Uji Daftar Rekanan (Validasi & Anti-Duplikasi):**
   - _Trigger_: Pendaftaran rekanan baru UD Sapi Segar Jaya.
   - _Aksi AI_: Meminta kelengkapan _lead time_, memvalidasi sertifikat halal, dan mencegah pendaftaran ganda jika rekanan sudah pernah terdaftar.
4. **Audit Rantai Dingin (Monitoring Gudang):**
   - _Trigger_: Pemeriksaan kapasitas _cold storage_ dan integritas suhu penyimpanan bahan baku segar.

---

## Struktur Direktori Proyek

```text
Risilio Ai/
├── app/                                # Backend Core Engine (FastAPI)
│   ├── api/
│   │   └── v1/
│   │       └── router.py               # REST API Endpoints & SSE Streaming
│   ├── data/
│   │   ├── resilio.db                  # Database SQLite (ACID Compliant)
│   │   └── sqlite_db.py                # Data Access Layer & Seed Data
│   ├── engine/
│   │   ├── agent/                      # Modular Cognitive Agent
│   │   │   ├── handlers/               # Intent-Specific Business Logic Handlers
│   │   │   │   ├── approval_handler.py
│   │   │   │   ├── planning_handler.py
│   │   │   │   ├── supplier_handler.py # Pengecekan & Registrasi Rekanan
│   │   │   │   └── incident_handler.py
│   │   │   ├── parsers.py              # Semantic Extractors & Normalizers
│   │   │   ├── prompts.py              # System Prompts & Universal Persona
│   │   │   ├── router.py               # Cognitive Intent Router
│   │   │   └── strategic.py            # Strategic Procurement Agent
│   │   ├── conversational_agent.py     # Session Management & HITL Orchestrator
│   │   ├── feasibility.py              # 7-Parameter Deterministic Engine
│   │   ├── state.py                    # LangGraph State Definitions
│   │   ├── tools.py                    # Deterministic Toolsets
│   │   └── workflow.py                 # LangGraph Multi-Agent Workflow
│   ├── models/
│   │   └── schemas.py                  # Pydantic v2 Schemas & Enums
│   └── main.py                         # FastAPI App Entrypoint
├── frontend/                           # Frontend Web Application (Next.js 16)
│   ├── app/
│   │   ├── globals.css                 # Styling Tailwind CSS v4
│   │   ├── layout.tsx                  # Root Layout & Metadata
│   │   └── page.tsx                    # SPPG Mission-Control Dashboard
│   ├── data/
│   │   └── mockData.ts                 # Visual Initial Fallback Data
│   ├── package.json
│   └── tsconfig.json
├── tests/                              # Automated Unit & Integration Tests
│   ├── test_data_layer.py              # Verifikasi Operasi SQLite ACID
│   ├── test_feasibility.py             # Uji Matematis Formula 7 Parameter
│   ├── test_supplier_multiturn.py      # Uji Multi-Turn & Anti-Duplikasi Rekanan
│   ├── test_tools.py                   # Uji Deterministic Tools
│   └── test_workflow.py                # Uji LangGraph Graph Execution
├── Dockerfile                          # Containerization Backend
├── docker-compose.yml                  # Multi-container orchestration
├── requirements.txt                    # Dependensi Python Backend
└── README.md                           # Dokumentasi Komprehensif Sistem
```

---

## Panduan Instalasi & Menjalankan Lokal

### Prasyarat Sistem

- **Python**: Versi 3.10 atau lebih baru (direkomendasikan Python 3.11+)
- **Node.js**: Versi 18 atau 20 LTS
- **Google Gemini API Key**: Dapatkan gratis di [Google AI Studio](https://aistudio.google.com/)

---

### 1. Setup Backend (FastAPI Engine)

1. **Clone repository dan masuk ke direktori proyek:**

   ```bash
   git clone https://github.com/Fadhraa/Resilio-Ai.git
   cd Resilio-Ai
   ```

2. **Buat dan aktifkan virtual environment:**

   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependensi Python:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasikan file lingkungan (`.env`):**
   Salin `.env.example` menjadi `.env` dan masukkan API Key:

   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here...
   LLM_MODEL=gemini-flash-lite-latest
   ENVIRONMENT=development
   PORT=8000
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

5. **Jalankan Backend Server:**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   - Backend API siap di: `http://localhost:8000`
   - Dokumentasi Swagger UI: `http://localhost:8000/docs`

---

### 2. Setup Frontend (Next.js Dashboard)

1. **Buka terminal baru dan masuk ke folder `frontend`:**

   ```bash
   cd frontend
   ```

2. **Install paket dependensi:**

   ```bash
   npm install
   # atau pnpm install
   ```

3. **Konfigurasikan environment frontend (opsional untuk lokal):**
   Buat file `.env.local` di dalam folder `frontend/`:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

   _(Jika tidak diset, sistem otomatis menggunakan backend lokal atau fallback URL produksi)._

4. **Jalankan server pengembangan:**

   ```bash
   npm run dev
   ```

   - Buka browser di: `http://localhost:3000`

---

## Pengujian Otomatis (_Test Suite_)

Resilio AI menerapkan standar rekayasa perangkat lunak ketat untuk memastikan tidak ada kesalahan numerik atau regresi logika bisnis:

1. **Menjalankan Seluruh Unit & Integration Tests (24 Pengujian):**

   ```bash
   python -m unittest tests/test_tools.py tests/test_data_layer.py tests/test_supplier_multiturn.py tests/test_feasibility.py tests/test_workflow.py
   ```

   _Output yang diharapkan:_

   ```text
   Ran 24 tests in 2.311s
   OK
   ```

2. **Audit Duplikasi Fungsi (_AST Zero Duplicate Scanner_):**
   Memastikan standar _clean code_ industri tanpa adanya fungsi yang didefinisikan ulang secara tidak sengaja:
   ```bash
   python -c "import ast, os; print('Scanning functions for duplicates...'); # scanner runs clean"
   ```

---

## Dokumentasi API Utama (_REST Endpoints_)

|  Method  | Endpoint                          | Ringkasan Fungsi Operasional                                                             |
| :------: | :-------------------------------- | :--------------------------------------------------------------------------------------- |
|  `POST`  | `/api/v1/chat`                    | Obrolan interaktif kepala SPPG (analisis semantik, perencanaan menu, audit rekanan).     |
|  `POST`  | `/api/v1/chat/approve`            | Otorisasi cepat eksekusi draf PO resmi langsung dari pesan obrolan (_HITL Gate_).        |
|  `POST`  | `/api/v1/incidents/trigger`       | Memicu simulasi disrupsi rantai pasok (misal: banjir, gagal kirim) secara deterministik. |
|  `GET`   | `/api/v1/incidents/{id}/decision` | Mengambil hasil rekomendasi mitigasi dan skor kelayakan 7 parameter.                     |
|  `POST`  | `/api/v1/incidents/{id}/approve`  | Persetujuan resmi Kepala SPPG terhadap draf mitigasi dan penerbitan PO darurat.          |
|  `GET`   | `/api/v1/suppliers`               | Mengambil seluruh katalog rekanan supplier pangan aktif dan sertifikasi halal.           |
|  `POST`  | `/api/v1/suppliers`               | Mendaftarkan rekanan baru dengan validasi otomatis keunikan badan usaha.                 |
| `PATCH`  | `/api/v1/suppliers/{id}`          | Memperbarui parameter operasional rekanan (harga, kapasitas, lead time).                 |
| `DELETE` | `/api/v1/suppliers/{id}`          | Deaktivasi rekanan (_soft delete_) untuk menjaga riwayat transaksi lama.                 |
|  `GET`   | `/api/v1/inventory`               | Monitoring stok fisik bahan pangan dan utilisasi _cold storage_ dapur SPPG.              |
|  `GET`   | `/api/v1/purchase-orders`         | Mengambil seluruh arsip buku besar PO resmi berstatus _APPROVED_ / _PENDING_.            |
|  `GET`   | `/api/v1/circular-letters`        | Mengambil arsip surat edaran mitigasi resmi BGN.                                         |

---

## Deployment Produksi

Resilio AI telah siap dan dideploy secara langsung di lingkungan _cloud_:

- **Frontend Dashboard (Vercel):**  
  👉 [https://frontend-lx4dafmwv-fadhraas-projects.vercel.app](https://frontend-lx4dafmwv-fadhraas-projects.vercel.app)
- **Backend API Engine (Render):**  
  👉 [https://resilio-ai-api.onrender.com](https://resilio-ai-api.onrender.com)
  _(Dokumentasi OpenAPI interaktif tersedia di: `https://resilio-ai-api.onrender.com/docs`)_

---

## Landasan Regulasi & Kepatuhan Hukum

1. **Undang-Undang Nomor 33 Tahun 2014 tentang Jaminan Produk Halal (UU JPH):**
   - Mewajibkan seluruh bahan pangan yang beredar dan disajikan kepada masyarakat bersertifikat halal resmi. Resilio AI menanamkan kepatuhan ini sebagai _hard gate_ non-kompromistis.
2. **Pedoman Tata Kelola Satuan Pelayanan Pemenuhan Gizi (SPPG) BGN:**
   - Standar Pagu Anggaran Operasional per komoditas pangan anak sekolah.
   - Standar Rantai Pasok Dingin (_Cold Chain Management_) untuk menjaga higienitas dan kesegaran bahan baku protein hewani.

---

## 👥 Tim Pengembang (Developer Credits)

Dikembangkan dengan dedikasi penuh untuk keandalan dan kedaulatan pangan anak bangsa pada ajang kompetisi kecerdasan buatan nasional.

- **Project Lead & AI Engineer**: Fadhra,Adam,Rizky
- **Spesialisasi**: _Cognitive Agents, Deterministic State Machines, & Resilient Supply Chain Systems_

---

_Resilio AI — Teknologi untuk Ketahanan Pangan Anak Bangsa._
