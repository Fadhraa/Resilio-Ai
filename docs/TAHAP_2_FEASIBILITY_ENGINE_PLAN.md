# RENCANA KERJA TAHAP 2: FEASIBILITY SCORING ENGINE

Dokumen ini merupakan panduan teknis implementasi **Tahap 2** untuk sistem **ResilioAI** (GTNIC 2026).

---

## 1. Tujuan Tahap 2
Membangun mesin evaluasi kelayakan supplier & mitigasi logistik (**Feasibility Scoring Engine**) berbasis formula matematis 7 parameter berbobot:
1. **Audit Kepatuhan & Transparansi:** Skor kelayakan dapat direproduksi dan diaudit oleh tim kepatuhan internal/eksternal.
2. **Deterministic Gating:** Menyediakan gerbang *hard-gate* untuk regulasi sertifikasi Halal dan batas toleransi pagu anggaran.
3. **Penyedia Umpan Balik untuk Agent:** Memberikan evaluasi numerik bagi LangGraph Agent untuk memutuskan apakah mitigasi lolos langsung, lolos bersyarat (*Split-Delivery*), atau perlu diulang (*retry loop*).

---

## 2. Struktur Modul & File yang Dibangun

```
.gitignore                     # Menjaga repositori bersih dari file temporary & cache
app/
├── engine/
│   ├── __init__.py
│   └── feasibility.py         # FeasibilityEngine & fungsi skoring 7 parameter
tests/
└── test_feasibility.py        # Pengujian unit otomatis (unittest)
```

---

## 3. Spesifikasi Matematis 7 Parameter Berbobot

$$\text{Total Score} = \sum_{i=1}^{7} (W_i \times S_i)$$

| No | Parameter | Bobot ($W_i$) | Metode Evaluasi Subskor ($S_i \in [0, 100]$) |
| :--- | :--- | :---: | :--- |
| 1 | **Stock Fulfillment** | 25% | Rasio pasokan harian terhadap defisit: $\min(100.0, \frac{\text{capacity}}{\text{deficit}} \times 100)$. |
| 2 | **Time Lead Compliance** | 20% | Kedekatan waktu tiba dengan jam mulai masak SPPG (ideal $\le 3$ jam bernilai 100, melandai hingga 6 jam). |
| 3 | **Budget Compliance** | 15% | Kepatuhan terhadap pagu anggaran SOP ($\text{unit\_price} \le \text{sop\_max\_price} \implies 100$). |
| 4 | **Halal & Legal** | 15% | **Gating Parameter:** Bernilai 100 jika halal aktif. Jika 0, total skor langsung 0.0! |
| 5 | **Storage Compatibility** | 10% | Rasio kesesuaian muatan batch kirim terhadap sisa kapasitas freezer. |
| 6 | **Kitchen Capacity** | 10% | Kesiapan personel dan alat pengolahan dapur SPPG. |
| 7 | **Route Safety** | 5% | Indeks keandalan rute berdasarkan jarak tempuh logistik dan rating historis supplier. |

### Klasifikasi Keputusan:
- $\ge 80.0$: **FEASIBLE**
- $60.0 - 79.9$: **FEASIBLE WITH CONDITIONS** (Mewajibkan skema *Split-Delivery*)
- $< 60.0$: **NOT FEASIBLE** (Memicu *retry loop* pada agent, maksimal 3x)

