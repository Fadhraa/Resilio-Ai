"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  Warehouse,
  AlertTriangle,
  Lock,
  Clock,
  Scale,
  FileText,
  Bot,
  Truck,
  Layers,
  Coins,
  Check,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-zinc-900 antialiased selection:bg-zinc-100 scroll-smooth">
      {/* ===================================================================
          1. NAVBAR / HEADER UTAMA DENGAN 4 MENU SESUAI PERMINTAAN
      =================================================================== */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-xs border-b border-zinc-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo ResilioAI */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 text-white font-bold text-sm shadow-xs">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="font-bold text-base leading-tight text-zinc-900">
                Resilio<span className="text-zinc-600">AI</span>
              </div>
              <p className="text-[11px] text-zinc-500 font-medium">
                Dapur Gizi SPPG Mandiri
              </p>
            </div>
          </Link>

          {/* Navigasi Utama: 4 Menu Sesuai Permintaan User */}
          <nav className="hidden md:flex items-center gap-7 text-xs font-semibold text-zinc-600">
            <a
              href="#tantangan-dapur"
              className="hover:text-zinc-900 transition py-1 border-b-2 border-transparent hover:border-zinc-900"
            >
              Tantangan Dapur
            </a>
            <a
              href="#solusi-cerdas-ai"
              className="hover:text-zinc-900 transition py-1 border-b-2 border-transparent hover:border-zinc-900"
            >
              Solusi Cerdas AI
            </a>
            <a
              href="#cara-kerja"
              className="hover:text-zinc-900 transition py-1 border-b-2 border-transparent hover:border-zinc-900"
            >
              Cara Kerja
            </a>
            <a
              href="#jaminan-halal-sop"
              className="hover:text-zinc-900 transition py-1 border-b-2 border-transparent hover:border-zinc-900"
            >
              Jaminan Halal &amp; SOP
            </a>
          </nav>

          {/* Tombol Aksi Masuk / Buka Dashboard */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-zinc-700 hover:text-zinc-900 hover:bg-zinc-100 transition"
            >
              Masuk
            </Link>
            <Link
              href="/register"
              className="hidden sm:inline-flex px-3.5 py-1.5 rounded-lg border border-zinc-300 text-xs font-semibold text-zinc-900 hover:bg-zinc-50 transition"
            >
              Daftar Petugas
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold transition active:scale-95 shadow-xs"
            >
              <span>Buka Dashboard</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ===================================================================
          2. HERO SECTION: PENJELASAN SINGKAT & FORMAL
      =================================================================== */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 border-b border-zinc-100 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Badge Lembaga */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-200 bg-zinc-50 text-xs font-medium text-zinc-700 mb-6">
            <span className="h-2 w-2 rounded-full bg-zinc-900"></span>
            <span>Program Satuan Pelayanan Pemenuhan Gizi (SPPG) • GTNIC 2026</span>
          </div>

          {/* Judul Besar */}
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-zinc-900 leading-[1.15]">
            Jaga Pasokan Makanan Ribuan Anak Tetap Aman, Bahkan Saat Terjadi Bencana.
          </h1>

          {/* Penjelasan Sederhana untuk Orang Awam */}
          <p className="mt-6 max-w-3xl mx-auto text-base sm:text-lg text-zinc-600 leading-relaxed">
            Ketika truk pemasok bahan makanan utama terhambat banjir atau bencana di jalur logistik, <strong>ResilioAI</strong> bekerja otomatis dalam hitungan detik: menghitung kekurangan stok pasti, memilih pemasok cadangan yang resmi bersertifikat Halal, dan membagi jadwal pengiriman agar muat di kulkas dapur SPPG.
          </p>

          {/* Tombol Tindakan */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white font-semibold text-sm transition shadow-sm active:scale-95"
            >
              <span>Coba Simulasi di Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-800 font-semibold text-sm transition"
            >
              <Lock className="h-4 w-4 text-zinc-500" />
              <span>Masuk sebagai Petugas SPPG</span>
            </Link>
          </div>

          {/* Fakta Kunci SPPG */}
          <div className="mt-14 pt-8 border-t border-zinc-200/60 grid grid-cols-2 md:grid-cols-4 gap-6 text-left">
            <div>
              <div className="text-2xl font-bold text-zinc-900 font-mono">
                3.000 Porsi
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">
                Target masak harian terjadwal ketat
              </p>
            </div>
            <div>
              <div className="text-2xl font-bold text-zinc-900 font-mono">
                &lt; 6 Detik
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">
                Solusi otomatis vs 4–6 jam cara manual
              </p>
            </div>
            <div>
              <div className="text-2xl font-bold text-zinc-900 font-mono">
                100% Halal
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">
                Wajib sertifikat resmi BPJPH / MUI
              </p>
            </div>
            <div>
              <div className="text-2xl font-bold text-zinc-900 font-mono">
                Zero Salah
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">
                Hitungan angka stok akurat bebas tebakan
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          MENU 1: TANTANGAN DAPUR (#tantangan-dapur)
      =================================================================== */}
      <section
        id="tantangan-dapur"
        className="py-20 bg-zinc-50/50 border-b border-zinc-200 scroll-mt-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 bg-zinc-100 border border-zinc-200 px-3 py-1 rounded-full">
              Bagian 1 • Tantangan Dapur
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 mt-3">
              Krisis Nyata yang Sering Dihadapi Dapur Program Gizi
            </h2>
            <p className="text-xs sm:text-sm text-zinc-600 mt-2 leading-relaxed">
              Mengapa menangani gangguan rantai pasok secara konvensional dan telepon manual sangat berbahaya bagi kelangsungan makan ribuan siswa?
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tantangan 1: Keterlambatan Tiba-Tiba */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs hover:shadow-xs transition">
              <div className="w-11 h-11 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4 border border-zinc-200">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                1. Hambatan Logistik &amp; Banjir
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Truk supplier ayam utama terjebak banjir di jalur Pantura. Jika petugas baru mengetahui pada sore hari, butuh <strong>4 hingga 6 jam</strong> mencari telepon vendor lain secara manual. Jadwal masak subuh terancam batal dan ribuan porsi makanan tidak tersaji.
              </p>
              <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-semibold text-zinc-500">
                <Clock className="h-3.5 w-3.5" />
                <span>Waktu kritis: Kurang dari 12 jam sebelum masak</span>
              </div>
            </div>

            {/* Tantangan 2: Kulkas Dapur Terbatas */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs hover:shadow-xs transition">
              <div className="w-11 h-11 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4 border border-zinc-200">
                <Warehouse className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                2. Kapasitas Kulkas / Freezer Terbatas
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Dapur SPPG kekurangan <strong>64 kg ayam</strong>, namun sisa ruang pendingin (*freezer*) yang tersedia hanya muat <strong>20 kg</strong>. Jika vendor darurat mengirim sekaligus 64 kg, maka 44 kg daging ayam akan membusuk di luar ruangan dan menimbulkan kerugian besar.
              </p>
              <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-semibold text-zinc-500">
                <Layers className="h-3.5 w-3.5" />
                <span>Kendala fisik: Batas sisa kulkas hanya 20 kg</span>
              </div>
            </div>

            {/* Tantangan 3: Risiko Halal & Keabsahan Pagu */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs hover:shadow-xs transition">
              <div className="w-11 h-11 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4 border border-zinc-200">
                <Scale className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                3. Jeratan Hukum &amp; Keabsahan Halal
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Dalam situasi panik, staf lapangan rawan memesan dari sembarang pedagang pasar tanpa sertifikat Halal BPJPH yang sah, atau membeli dengan harga tinggi di atas pagu anggaran negara. Hal ini berisiko menjadi temuan pelanggaran audit hukum oleh BPK.
              </p>
              <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-semibold text-zinc-500">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Standar ketat: Sertifikat Halal &amp; Pagu Anggaran</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          MENU 2: SOLUSI CERDAS AI (#solusi-cerdas-ai)
      =================================================================== */}
      <section
        id="solusi-cerdas-ai"
        className="py-20 bg-white border-b border-zinc-200 scroll-mt-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 bg-zinc-100 border border-zinc-200 px-3 py-1 rounded-full">
              Bagian 2 • Solusi Cerdas AI
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 mt-3">
              Kecerdasan Buatan yang Nyata, Terstruktur, &amp; Akuntabel
            </h2>
            <p className="text-xs sm:text-sm text-zinc-600 mt-2 leading-relaxed">
              Resilio-Ai bukan sekadar chatbot biasa, melainkan sistem agen mandiri berbasis <em>LangGraph</em> yang memadukan perhitungan angka pasti dengan logika logistik teruji.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Solusi 1 */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50 hover:bg-white transition shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-xs font-bold mb-4 font-mono">
                01
              </div>
              <h3 className="text-sm font-bold text-zinc-900">
                Hitungan Defisit Pasti (Anti-Halusinasi)
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Sistem menghitung presisi matematika murni: 3.000 porsi butuh 144 kg ayam, stok gudang ada 80 kg, maka kekurangan adalah tepat <strong>64 kg</strong>. Nol asumsi yang mengada-ada.
              </p>
            </div>

            {/* Solusi 2 */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50 hover:bg-white transition shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-xs font-bold mb-4 font-mono">
                02
              </div>
              <h3 className="text-sm font-bold text-zinc-900">
                Skor 7 Parameter Multi-Kriteria
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Menilai otomatis seluruh pemasok alternatif terdaftar berdasarkan: Halal (wajib 100%), kecukupan stok, waktu tempuh, harga di bawah pagu SOP, kesesuaian kulkas, dan riwayat mutu.
              </p>
            </div>

            {/* Solusi 3 */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50 hover:bg-white transition shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-xs font-bold mb-4 font-mono">
                03
              </div>
              <h3 className="text-sm font-bold text-zinc-900">
                Pengiriman 2 Tahap (Staggered Logistics)
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                AI otomatis membagi kiriman: <strong>Batch 1 (20 kg)</strong> tiba sore pukul 17:00 WIB untuk kulkas, dan <strong>Batch 2 (44 kg)</strong> tiba subuh pukul 05:00 WIB langsung diolah koki dapur.
              </p>
            </div>

            {/* Solusi 4 */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50 hover:bg-white transition shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-xs font-bold mb-4 font-mono">
                04
              </div>
              <h3 className="text-sm font-bold text-zinc-900">
                Asisten AI Interaktif Lapangan
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Staf dapur dapat bertanya langsung dalam bahasa Indonesia sehari-hari melalui fitur chat AI, mulai dari cek sisa stok gudang hingga verifikasi status mitra pengganti.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          MENU 3: CARA KERJA (#cara-kerja)
      =================================================================== */}
      <section
        id="cara-kerja"
        className="py-20 bg-zinc-50/50 border-b border-zinc-200 scroll-mt-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 bg-zinc-100 border border-zinc-200 px-3 py-1 rounded-full">
              Bagian 3 • Cara Kerja Sistem
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 mt-3">
              5 Langkah Kerja Alur Otomatis LangGraph
            </h2>
            <p className="text-xs sm:text-sm text-zinc-600 mt-2 leading-relaxed">
              Dari deteksi insiden bencana hingga terbitnya Surat Pesanan Resmi siap cetak, semuanya berjalan otomatis dengan otorisasi manusia di akhir alur.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Langkah 1 */}
            <div className="p-5 rounded-2xl bg-white border border-zinc-200 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-zinc-400">
                    LANGKAH 01
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
                    <AlertTriangle className="h-3.5 w-3.5" />
                  </div>
                </div>
                <h4 className="text-xs font-bold text-zinc-900 leading-snug">
                  Deteksi Insiden Logistik
                </h4>
                <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                  Menerima laporan truk terjebak banjir dan langsung menghitung kekurangan bahan (butuh 144 kg, kurang 64 kg).
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-zinc-100 text-[10px] font-semibold text-zinc-400">
                Waktu: 0.8 Detik
              </div>
            </div>

            {/* Langkah 2 */}
            <div className="p-5 rounded-2xl bg-white border border-zinc-200 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-zinc-400">
                    LANGKAH 02
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
                    <ShieldCheck className="h-3.5 w-3.5" />
                  </div>
                </div>
                <h4 className="text-xs font-bold text-zinc-900 leading-snug">
                  Penyaringan Ketat Halal
                </h4>
                <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                  Menyaring database mitra pemasok. Vendor tanpa nomor sertifikat Halal BPJPH resmi langsung dieliminasi.
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-zinc-100 text-[10px] font-semibold text-zinc-400">
                Gating: Mutlak 100%
              </div>
            </div>

            {/* Langkah 3 */}
            <div className="p-5 rounded-2xl bg-white border border-zinc-200 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-zinc-400">
                    LANGKAH 03
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
                    <Scale className="h-3.5 w-3.5" />
                  </div>
                </div>
                <h4 className="text-xs font-bold text-zinc-900 leading-snug">
                  Penilaian 7 Parameter
                </h4>
                <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                  Memilih rekanan terbaik: PT Berkah Unggas Jaya meraih skor 94.2/100 dengan harga Rp 36.500/kg (di bawah pagu SOP).
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-zinc-100 text-[10px] font-semibold text-zinc-400">
                Peringkat 1 Terpilih
              </div>
            </div>

            {/* Langkah 4 */}
            <div className="p-5 rounded-2xl bg-white border border-zinc-200 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-zinc-400">
                    LANGKAH 04
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-900">
                    <Truck className="h-3.5 w-3.5" />
                  </div>
                </div>
                <h4 className="text-xs font-bold text-zinc-900 leading-snug">
                  Susun Jadwal 2 Tahap
                </h4>
                <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                  Menyesuaikan sisa kapasitas freezer dapur (20 kg): Batch 1 tiba sore 17:00 WIB, Batch 2 tiba subuh 05:00 WIB.
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-zinc-100 text-[10px] font-semibold text-zinc-400">
                Bebas Pembusukan
              </div>
            </div>

            {/* Langkah 5 */}
            <div className="p-5 rounded-2xl bg-white border border-zinc-900 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-zinc-900">
                    LANGKAH 05
                  </span>
                  <div className="w-7 h-7 rounded-lg bg-zinc-900 text-white flex items-center justify-center">
                    <FileText className="h-3.5 w-3.5" />
                  </div>
                </div>
                <h4 className="text-xs font-bold text-zinc-900 leading-snug">
                  Persetujuan &amp; Terbit PO
                </h4>
                <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                  Kepala SPPG meninjau dan klik setuju. Surat Pesanan resmi No. PO-2026-003 langsung terbit siap cetak PDF.
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-zinc-100 text-[10px] font-semibold text-zinc-900">
                Sah &amp; Legal
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          MENU 4: JAMINAN HALAL & SOP (#jaminan-halal-sop)
      =================================================================== */}
      <section
        id="jaminan-halal-sop"
        className="py-20 bg-white border-b border-zinc-200 scroll-mt-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 bg-zinc-100 border border-zinc-200 px-3 py-1 rounded-full">
              Bagian 4 • Jaminan Halal &amp; SOP
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 mt-3">
              Perlindungan Hukum, Standar Halal, &amp; Tertib Anggaran
            </h2>
            <p className="text-xs sm:text-sm text-zinc-600 mt-2 leading-relaxed">
              Memastikan setiap gram bahan makanan anak-anak aman dikonsumsi dan setiap rupiah pengeluaran darurat dapat dipertanggungjawabkan di hadapan auditor negara.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pilar 1: Sertifikasi Halal BPJPH */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center shrink-0">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">
                    Sertifikasi Halal Mutlak (Gating Parameter 100%)
                  </h3>
                  <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                    Sistem secara permanen memblokir vendor yang tidak memiliki nomor sertifikat Halal BPJPH/MUI yang masih aktif. Tidak ada kompromi kehalalan meskipun vendor menawarkan harga murah.
                  </p>
                  <ul className="mt-3 space-y-1 text-xs text-zinc-700">
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Verifikasi nomor sertifikat resmi BPJPH Kemenag</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Rantai pasok rumah potong hewan terstandarisasi</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Pilar 2: Kepatuhan Pagu Anggaran SOP */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center shrink-0">
                  <Coins className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">
                    Kepatuhan Batas Pagu Biaya SOP Negara
                  </h3>
                  <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                    Mencegah lonjakan harga sepihak saat darurat. Pemasok yang direkomendasikan sistem (Rp 36.500/kg) selalu patuh berada di bawah batas pagu belanja SOP (Rp 42.000/kg), menghemat anggaran pengadaan negara.
                  </p>
                  <ul className="mt-3 space-y-1 text-xs text-zinc-700">
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Anti-markup harga dalam kondisi bencana</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Laporan efisiensi belanja otomatis tercatat</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Pilar 3: Human-in-the-Loop Governance */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center shrink-0">
                  <Lock className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">
                    Otoritas Manusia Tetap Tertinggi (Human-in-the-Loop)
                  </h3>
                  <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                    AI hanya bertindak sebagai asisten analis cerdas. Secara hukum, pengeluaran anggaran negara dan penerbitan Surat Pesanan (PO) tetap mewajibkan otorisasi tanda tangan atau klik persetujuan dari Kepala SPPG sebagai PPK.
                  </p>
                  <ul className="mt-3 space-y-1 text-xs text-zinc-700">
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Kepala SPPG memegang hak veto atas rekomendasi AI</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Fleksibilitas penyesuaian kuantitas sebelum terbit PO</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Pilar 4: Jejak Audit Permanen BPK */}
            <div className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50/50">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">
                    Jejak Rekam Audit Tak Terhapuskan (BPK Ready)
                  </h3>
                  <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                    Seluruh riwayat evaluasi 7 parameter, waktu deteksi banjir, identitas pemberi persetujuan, dan berkas surat pesanan tercatat dalam log audit permanen yang siap diekspor ke PDF saat pemeriksaan auditor.
                  </p>
                  <ul className="mt-3 space-y-1 text-xs text-zinc-700">
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Transparansi mutlak dokumen darurat SPPG</span>
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 text-zinc-900" />
                      <span>Format Kop Surat resmi pemerintah siap cetak</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          5. CALL TO ACTION (CTA)
      =================================================================== */}
      <section className="py-20 bg-zinc-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-8 sm:p-12 rounded-3xl bg-white border border-zinc-200 shadow-sm">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-zinc-900 text-white mb-4">
              <Bot className="h-6 w-6" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 tracking-tight">
              Ingin Menguji Skenario Banjir Pantura Secara Langsung?
            </h2>
            <p className="mt-3 text-xs sm:text-sm text-zinc-600 max-w-xl mx-auto leading-relaxed">
              Buka dashboard simulasi sekarang untuk melihat bagaimana asisten cerdas Resilio-Ai menyelesaikan krisis pasokan, membagi jadwal kirim, dan menerbitkan surat pesanan resmi.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/dashboard"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white font-semibold text-xs transition active:scale-95 shadow-xs"
              >
                <span>Buka Dashboard Simulasi</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/login"
                className="w-full sm:w-auto px-6 py-3 rounded-xl border border-zinc-300 text-zinc-800 font-semibold text-xs hover:bg-zinc-50 transition"
              >
                Masuk Akun Petugas
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          6. FOOTER RESMI
      =================================================================== */}
      <footer className="border-t border-zinc-200 bg-white py-8 text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-zinc-900" />
            <span className="font-bold text-zinc-900">ResilioAI</span>
            <span>• Satuan Pelayanan Pemenuhan Gizi (SPPG) Wilayah I</span>
          </div>
          <p>© 2026 ResilioAI • Kategori Lomba AI Agent Development (GTNIC 2026).</p>
        </div>
      </footer>
    </div>
  );
}
