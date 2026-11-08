# Rencana Implementasi Step 3: Integrasi CRUD Rekanan ke Conversational AI Agent

## 1. Latar Belakang & Tujuan
Pada **Step 1** dan **Step 2**, kita telah berhasil membangun:
1. **Deterministic CRUD Tools & Governance Gatekeeper** di [`app/engine/tools.py`](file:///d:/coding/Risilio%20Ai/app/engine/tools.py).
2. **REST API Endpoints** di [`app/api/v1/router.py`](file:///d:/coding/Risilio%20Ai/app/api/v1/router.py).

Pada **Step 3**, kita mengintegrasikan kapabilitas manajemen supplier ini langsung ke dalam dialog natural **Conversational AI Agent (`ConversationalAgentManager`)** di [`app/engine/conversational_agent.py`](file:///d:/coding/Risilio%20Ai/app/engine/conversational_agent.py). Tujuannya agar **Kepala SPPG** dapat menambahkan, memperbarui, mencari, atau menonaktifkan supplier cukup dengan perintah percakapan sehari-hari tanpa harus membuka dashboard teknis.

---

## 2. Arsitektur & Prinsip Best Practice (GTNIC 2026)

```
[ Kepala SPPG / User Chat ]
           │
           ▼
[ Intent Classifier / Router ]
           │
   ┌───────┴────────────────────────┐
   │ Intent: MANAGE_SUPPLIER         │ (Intent lain: INCIDENT / INQUIRY / CONFIRM)
   ▼                                ▼
[ Deterministic Entity Parser & Tool Dispatch ]
   │
   ├─► register_supplier_tool(...)   (Validasi Halal & Pagu SOP)
   ├─► update_supplier_tool(...)     (Partial update kapasitas/harga)
   ├─► deactivate_supplier_tool(...) (Soft delete aman audit)
   └─► list_all_suppliers_tool(...)  (Filter komoditas)
           │
           ▼ (Hasil Eksekusi Deterministik + Audit Note)
[ Gemini 3.5 Flash-Lite Augmented Synthesis ]
   │
   ▼
[ Respon Empatik, Tegas Tata Kelola, & Rangkuman Aksi ]
```

### Standar Industri & Best Practice:
1. **Augmented Tool Execution (Zero Hallucination)**: LLM tidak mengarang status penyimpanan atau manipulasi data di memori. Agen memanggil fungsi deterministik Python terlebih dahulu, lalu menyuntikkan hasil nyata ke prompt Gemini untuk sintesis bahasa alami.
2. **Strict Governance & Compliance Awareness**: Agen selalu menggarisbawahi status sertifikasi Halal (UU JPH No. 33/2014) dan kepatuhan pagu harga SOP BGN saat merespons pendaftaran supplier.
3. **No Code Duplication**: Menggunakan kembali fungsi-fungsi yang telah diuji di `app/engine/tools.py` (`register_supplier_tool`, `update_supplier_tool`, dll.) tanpa membuat duplikasi fungsi di layer agen.
4. **Resilient Natural Language Parsing**: Mampu mengekstraksi parameter entitas supplier (nama, harga, kapasitas, nomor halal, lead time, komoditas) dari kalimat santai maupun formal.

---

## 3. Komponen yang Akan Diubah / Ditambahkan

### A. `app/engine/conversational_agent.py`
1. **Perluasan `ChatIntent` Enum**:
   - Menambahkan enum `MANAGE_SUPPLIER = "MANAGE_SUPPLIER"`.
2. **System Prompt Baru di `SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"]`**:
   - Persona asisten Kepala SPPG yang cekatan, teliti terhadap tata kelola anggaran (pagu SOP) dan sertifikasi Halal, serta memberikan konfirmasi jelas dan ramah.
3. **Integrasi Tool Execution**:
   - Saat intent `MANAGE_SUPPLIER` terdeteksi, agen mengekstrak entitas tindakan (daftar baru, update harga/kapasitas, nonaktifkan, atau lihat daftar) dan memanggil tool deterministik terkait.
   - Hasil tool diberikan kepada Gemini untuk menghasilkan jawaban komprehensif.

### B. `tests/test_api.py`
1. **Penambahan Test Case Integrasi Chat**:
   - `test_conversational_supplier_management_flow`:
     - Pengujian dialog pendaftaran supplier baru via `/api/v1/chat`.
     - Pengujian pembaruan harga supplier via `/api/v1/chat`.
     - Pengujian penonaktifan supplier via `/api/v1/chat`.
     - Verifikasi respons status HTTP 200, intent `MANAGE_SUPPLIER`, dan mutasi data riil di `SUPPLIERS_DB`.

---

## 4. Rencana Pengujian & Verifikasi
- Menjalankan test suite lengkap `tests/test_api.py` dan `tests/test_tools.py`.
- Memastikan 24+ pengujian unit dan integrasi lulus 100% (`OK`).
- Menguji skrip simulasi interaktif `chat_simulate.py` jika diperlukan.

