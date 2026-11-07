# RENCANA KERJA TAHAP 4: CONVERSATIONAL CHATBOT API & INTERACTIVE APPROVAL ENGINE

Dokumen ini merupakan panduan teknis implementasi **Tahap 4** untuk sistem **ResilioAI** (GTNIC 2026).

---

## 1. Tujuan Tahap 4
Menyediakan antarmuka API publik berbasis **FastAPI v1** yang siap dikonsumsi oleh frontend Next.js dan dilengkapi kemampuan **Conversational AI Agent (Chatbot)**:
1. **Tool-Using AI Agent:** Agen memiliki akses ke *Database Read Tools* untuk memeriksa keberadaan rekanan supplier dan stok bahan pangan secara mandiri sebelum menjalankan SOP mitigasi.
2. **Pencegahan Halusinasi & Typo:** Menggunakan pencocokan kemiripan (*similarity matching*) bawaan Python (`difflib`) tanpa membebani memori server (aman untuk tier gratis Render).
3. **Multi-Turn Revision Loop:** Kepala SPPG dapat bernegosiasi atau meminta penyesuaian strategi (ganti supplier, ubah jumlah porsi) secara percakapan langsung sebelum Purchase Order resmi diterbitkan.
4. **Penyediaan Endpoint Formal PRD:** Mendukung endpoint standar `/trigger`, `/stream` (SSE), `/decision`, dan `/approve` sesuai spesifikasi kontrak PRD.

---

## 2. Struktur Modul & Berkas yang Dibangun

```
app/
├── api/
│   └── v1/
│       └── router.py              # Endpoint publik /api/v1 (Chat, Trigger, Stream, Decision, Approve)
├── engine/
│   ├── tools.py                   # DB Read Tools (Pencari Supplier & Stok dengan difflib)
│   └── conversational_agent.py    # Pengelola percakapan multi-turn & negosiasi revisi
├── models/
│   └── schemas.py                 # Penambahan skema ChatRequest, ChatResponse, ChatIntent
main.py                            # Pemasangan api_router ke aplikasi utama FastAPI
chat_simulate.py                   # Simulator obrolan interaktif langsung di terminal
tests/
└── test_api.py                    # Pengujian unit & integrasi endpoint FastAPI
```

---

## 3. Spesifikasi Kontrak API Utama

### 3.1 `POST /api/v1/chat`
Endpoint percakapan Kepala SPPG:
- **Request Body:**
  ```json
  {
    "session_id": "sesi-sppg-001",
    "message": "Hari ini SPPG A mau membuat 5.000 porsi makanan bergizi namun supplier ayam A kebakaran sehingga tidak mensuplai, apa yang harus dilakukan?",
    "user_role": "Kepala SPPG"
  }
  ```
- **Response Body:**
  ```json
  {
    "session_id": "sesi-sppg-001",
    "reply": "Saya telah memeriksa basis data. Supplier 'A' tidak terdaftar, namun ditemukan rekanan utama Anda 'PT Unggas Sejahtera Nusantara (SUP-UTAMA-01)'. Apakah yang Anda maksud rekanan tersebut?",
    "intent": "REPORT_INCIDENT",
    "action_required": "CLARIFICATION_NEEDED",
    "preview_data": null
  }
  ```

### 3.2 `POST /api/v1/chat/approve`
Endpoint otorisasi cepat:
- **Request Body:**
  ```json
  {
    "session_id": "sesi-sppg-001",
    "action": "APPROVE",
    "approver_name": "Budi Santoso (Kepala SPPG)",
    "approver_notes": "Disetujui via UI chat."
  }
  ```
- **Response Body:** Data draf Purchase Order resmi (`PO-SPPG-2026-xxxx`).

---

## 4. Validasi & Pengujian
- Pengujian otomatis dengan `TestClient` FastAPI (100% lulus).
- CLI interaktif `chat_simulate.py` untuk mendemonstrasikan pengalaman percakapan bahasa alami di terminal.

