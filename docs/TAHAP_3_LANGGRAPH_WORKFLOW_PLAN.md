# RENCANA KERJA TAHAP 3: LANGGRAPH WORKFLOW & STRATEGIC AGENT

Dokumen ini merupakan panduan teknis implementasi **Tahap 3** untuk sistem **ResilioAI** (GTNIC 2026).

---

## 1. Tujuan Tahap 3
Membangun arsitektur **Hybrid Cyclic StateGraph** berbasis **LangGraph** yang menghubungkan modul deterministik (Tahap 1 & 2) dengan kemampuan kognitif **Large Language Model (Gemini)** serta gerbang otorisasi manusia (*Human-in-the-Loop*):
1. **Penalaran Strategis (Strategic Procurement Agent):** Memilih supplier rekanan optimal, merumuskan skema logistik adaptif (*Split-Delivery* bila sisa freezer terbatas), dan menyusun narasi rekomendasi keputusan.
2. **Evaluasi Tertutup (Looping Retry):** Bila skor kelayakan yang dihasilkan $< 60$, pipeline melakukan evaluasi ulang secara otomatis (maksimal 3x retry).
3. **Persistensi State & Human-in-the-Loop:** Menahan eksekusi di titik persetujuan pimpinan SPPG menggunakan LangGraph `interrupt()` dan menyimpan checkpoint state ke memory/database.
4. **Eksekusi PO & Jejak Audit:** Menerbitkan nomor Purchase Order resmi dan mencatat rantai log audit tak terhapuskan (*append-only*).

---

## 2. Struktur Modul & Berkas yang Dibangun

```
app/
└── engine/
    ├── __init__.py
    ├── state.py           # Definisi skema TypedDict ProcurementWorkflowState
    ├── agent.py           # Strategic Procurement Agent (Gemini & Heuristic Fallback)
    ├── workflow.py        # Konstruksi StateGraph, Nodes, Edges, dan Checkpointer
tests/
└── test_workflow.py       # Pengujian alur StateGraph end-to-end
```

---

## 3. Alur 7 Node Pipeline

1. **Ingestion Node:** Menerima parameter gangguan (item, supplier terdampak, catatan lapangan) dan memulai log audit.
2. **Data Layer Node:** Mengambil stok aktual gudang, sisa kapasitas pendingin, dan menghitung defisit bahan pangan ($Kebutuhan \times 1.2 - Stok$).
3. **Compliance Filter Node:** Mengeliminasi rekanan non-halal (zero tolerance) dan rekanan terdampak insiden.
4. **Strategic Procurement Agent (Gemini):** Menimbang trade-off kandidat dan merancang skema pengiriman (apakah Direct atau Split Delivery jika freezer terbatas).
5. **Feasibility Gate Node:** Menghitung skor matriks 7 parameter secara deterministik.
   - Jika skor $< 60$: looping kembali ke node agent (maks 3x).
   - Jika skor $\ge 60$: lanjut ke gerbang approval.
6. **Approval Gate Node (Interrupt):** Menghentikan alur sementara (*interrupt*), menunggu aksi *Approve* / *Reject* dari Kepala SPPG.
7. **Execution PO Node:** Menerbitkan nomor PO resmi dan menyimpan rekam jejak audit final.

---

## 4. Rencana Validasi Pengujian
- Memastikan graph dapat di-*compile* dengan checkpointer persisten.
- Memastikan workflow berhenti dengan mulus pada node interrupt ketika menunggu keputusan manusia.
- Memastikan eksekusi dapat di-*resume* dengan aman untuk menghasilkan data Purchase Order.
- Memastikan seluruh pengujian otomatis (Tahap 1 + 2 + 3) berjalan 100% lulus.

