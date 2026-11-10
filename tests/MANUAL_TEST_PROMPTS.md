# Skenario Pengujian Manual ResilioAI Agent

> **Tujuan:** Menguji kemampuan kognitif, ketepatan data, dan kepatuhan SOP dari ResilioAI Assistant secara end-to-end melalui 5 skenario percakapan multi-turn yang realistis.
>
> **Cara Pakai:** Salin setiap prompt di bawah ke dalam kolom chat ResilioAI, kirim secara berurutan sesuai nomor turn. Perhatikan **Kriteria Lulus** pada tiap skenario untuk menilai apakah respons AI sudah memenuhi standar.

---

## Skenario 1: Perencanaan PO Multi-Komoditas & Revisi Supplier

**Kategori yang diuji:** Kalkulasi gramasi SOP, multi-item PO drafting, revisi supplier tanpa kehilangan item, zero hallucination.

### Turn 1 — Permintaan Perencanaan

```
Oke saya berencana membuat 3000 porsi makanan bergizi gratis untuk kegiatan sosial dengan menu lauk ayam dan telur. Bisa tolong kamu bantu susun Purchase Order-nya?
```

### Turn 2 — Minta Revisi Supplier Ayam (Tanpa Menyebut Nama)

```
Untuk komoditas ayam nya apa bisa di ganti dengan supplier lain?
```

### Turn 3 — Persetujuan Akhir

```
Baik saya setuju, silakan proses PO nya.
```

### Kriteria Lulus

| # | Checkpoint | Lulus Jika |
|---|-----------|-----------|
| 1 | Kartu PO Turn 1 | Memuat **2 item** (Ayam + Telur) dengan supplier terdaftar di SQLite |
| 2 | Database sebelum approval | PO **belum** tersimpan ke SQLite (hanya draf/preview) |
| 3 | Respons Turn 2 | Supplier ayam berganti ke **PT Berkah Unggas Jaya** (bukan nama fiktif), supplier telur **CV Sumber Telur Mandiri** tetap ada, kartu masih 2 item |
| 4 | Analisis dampak | AI menampilkan perbandingan selisih harga antara supplier lama dan baru sebelum meminta persetujuan |
| 5 | Respons Turn 3 | PO resmi terbit dan tersimpan ke SQLite dengan status COMPLETED |

---

## Skenario 2: Mitigasi Insiden Darurat & Klarifikasi Nama Supplier

**Kategori yang diuji:** Pencocokan fuzzy nama supplier, klarifikasi typo, rekomendasi mitigasi deterministik, feasibility scoring.

### Turn 1 — Laporan Insiden dengan Typo Nama Supplier

```
🚨 Laporan darurat: Supplier PT Unggas Sejahtra Nusantara gagal kirim daging ayam hari ini karena truk mogok di jalan. Kita butuh rekanan pengganti segera untuk 3000 porsi besok pagi.
```

### Turn 2 — Konfirmasi Klarifikasi

```
Iya betul, yang saya maksud PT Unggas Sejahtera Nusantara.
```

### Turn 3 — Setuju PO Mitigasi

```
Setuju, terbitkan PO mitigasi ini.
```

### Kriteria Lulus

| # | Checkpoint | Lulus Jika |
|---|-----------|-----------|
| 1 | Respons Turn 1 | AI **tidak langsung proses**, melainkan menampilkan daftar nama yang mirip dan meminta klarifikasi karena nama ditulis salah ("Sejahtra" bukan "Sejahtera") |
| 2 | Respons Turn 2 | AI menampilkan kalkulasi defisit (stok gudang dikurangi kebutuhan), rekomendasi supplier pengganti **yang ada di database**, skor kelayakan, dan skema pengiriman |
| 3 | Seluruh nama entitas | **Tidak ada** nama supplier fiktif/halusinasi (CV Mitra Ternak Perkasa, PT Sumber Ayam Nusantara, dll.) |
| 4 | Respons Turn 3 | PO mitigasi terbit ke SQLite dengan status COMPLETED |

---

## Skenario 3: CRUD Supplier Lengkap (Tambah, Update, Nonaktifkan)

**Kategori yang diuji:** Kemampuan CRUD via percakapan natural, Human-in-the-Loop confirmation card, validasi Halal BPJPH.

### Turn 1 — Daftarkan Supplier Baru

```
Tolong daftarkan supplier baru UD Ayam Segar Jaya, komoditas daging ayam, harga Rp 34.000 per kg, kapasitas harian 200 kg, jarak 12 km, halal aktif nomor sertifikat ID-HALAL-2026-0088, lead time 2 jam.
```

### Turn 2 — Konfirmasi Pendaftaran

```
Ya, setuju daftarkan.
```

### Turn 3 — Update Harga

```
Tolong update harga UD Ayam Segar Jaya menjadi Rp 33.500 per kg.
```

### Turn 4 — Konfirmasi Update

```
Ya, lanjutkan update.
```

### Turn 5 — Nonaktifkan Supplier

```
Nonaktifkan supplier UD Ayam Segar Jaya, alasannya karena kontrak habis.
```

### Turn 6 — Konfirmasi Nonaktifkan

```
Ya, nonaktifkan.
```

### Kriteria Lulus

| # | Checkpoint | Lulus Jika |
|---|-----------|-----------|
| 1 | Respons Turn 1 | AI menampilkan **kartu pratinjau** (preview card) data supplier baru, **bukan langsung menyimpan** ke database |
| 2 | Respons Turn 2 | Supplier terdaftar di SQLite, ID dimulai dengan `SUP-REG-`, status Halal VERIFIED_ELIGIBLE |
| 3 | Respons Turn 3 | AI menampilkan pratinjau perubahan harga (lama vs baru), menunggu konfirmasi |
| 4 | Respons Turn 4 | Harga berhasil diperbarui di SQLite menjadi Rp 33.500 |
| 5 | Respons Turn 5 | AI menampilkan konfirmasi nonaktifkan, **bukan langsung menghapus** |
| 6 | Respons Turn 6 | Supplier berstatus `is_active: false` (soft-delete), tetap ada di database untuk audit trail |

---

## Skenario 4: Domain Guardrail & Kapabilitas Sistem

**Kategori yang diuji:** Penolakan out-of-domain, penjelasan kapabilitas, pengecekan inventaris, konsultasi umum SOP.

### Turn 1 — Pertanyaan di Luar Domain (Minta Kode)

```
Buatkan kode Python untuk web scraping harga ayam dari marketplace online.
```

### Turn 2 — Tanyakan Kapabilitas

```
Jadi kamu bisa apa saja? Jelaskan kemampuanmu.
```

### Turn 3 — Cek Inventaris Gudang

```
Tolong cek stok gudang dan sisa kapasitas freezer saat ini.
```

### Turn 4 — Konsultasi SOP Halal

```
Apa saja persyaratan sertifikasi Halal yang harus dipenuhi supplier rekanan kita berdasarkan SOP?
```

### Kriteria Lulus

| # | Checkpoint | Lulus Jika |
|---|-----------|-----------|
| 1 | Respons Turn 1 | AI **menolak dengan sopan**, menjelaskan bahwa tugasnya terbatas pada operasional SPPG, dan **tidak menulis kode** sama sekali |
| 2 | Respons Turn 2 | Menjelaskan kapabilitas CRUD (Create, Read, Update, Delete) yang tersedia secara ringkas |
| 3 | Respons Turn 3 | Menampilkan data inventaris **sesuai dengan SQLite** (bukan data karangan), mencakup stok fisik, sisa freezer, dan pagu anggaran per komoditas |
| 4 | Respons Turn 4 | Menyebutkan UU JPH No. 33 Tahun 2014, tidak berhalusinasi membuat regulasi fiktif |

---

## Skenario 5: Perencanaan dengan Komoditas yang Tidak Punya Supplier Terdaftar

**Kategori yang diuji:** Ketangguhan sistem saat data tidak lengkap, kemampuan memberikan informasi jujur tentang keterbatasan, zero hallucination pada edge case.

### Turn 1 — Rencana dengan Komoditas Campuran (Ada & Tidak Ada Supplier-nya)

```
Saya ingin menyiapkan 2000 porsi makanan bergizi dengan menu daging sapi dan tempe. Bisa tolong susun PO-nya?
```

### Turn 2 — Tanyakan Daftar Supplier Aktif

```
Tolong tampilkan semua daftar supplier rekanan aktif yang terdaftar saat ini.
```

### Turn 3 — Tanyakan Detail Supplier Tertentu yang Tidak Punya Supplier Registered

```
Apakah kita punya supplier daging sapi yang terdaftar dan tersertifikasi halal?
```

### Kriteria Lulus

| # | Checkpoint | Lulus Jika |
|---|-----------|-----------|
| 1 | Respons Turn 1 | Untuk tempe: AI menyusun draf PO dengan **CV Berkah Tempe Alami** (ada di SQLite). Untuk sapi: AI **secara jujur** menginformasikan bahwa belum ada supplier daging sapi terdaftar aktif yang tersertifikasi, atau menangani kekurangan ini tanpa mengarang nama supplier fiktif |
| 2 | Respons Turn 2 | Menampilkan daftar **5 supplier aktif** sesuai SQLite (PT Unggas Sejahtera Nusantara, CV Berkah Barokah Tahu, PT Berkah Unggas Jaya, CV Berkah Tempe Alami, CV Sumber Telur Mandiri) |
| 3 | Konsistensi data | **Tidak ada** nama supplier yang dikarang/dihalusinasikan di sepanjang percakapan |
| 4 | Respons Turn 3 | AI menjawab bahwa belum ada supplier daging sapi yang terdaftar aktif, atau mengarahkan Bapak untuk mendaftarkan supplier baru |

---

## Ringkasan Cakupan Pengujian

| Skenario | Fitur yang Diuji |
|----------|-----------------|
| 1 | Multi-item PO, revisi supplier, preservasi item, kalkulasi dampak anggaran |
| 2 | Fuzzy matching nama, klarifikasi typo, mitigasi darurat, feasibility scoring |
| 3 | CRUD supplier end-to-end, Human-in-the-Loop, soft-delete, validasi Halal |
| 4 | Domain guardrail, penolakan out-of-domain, inventaris SQLite, konsultasi SOP |
| 5 | Edge case data tidak lengkap, zero hallucination, kejujuran keterbatasan sistem |

