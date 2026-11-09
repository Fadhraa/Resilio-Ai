"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  Warehouse,
  AlertTriangle,
  Lock,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-zinc-900 antialiased selection:bg-zinc-100">
      {/* 1. NAVBAR / HEADER */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-xs border-b border-zinc-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
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

          {/* Navigasi Utama */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-zinc-600">
            <a href="#masalah" className="hover:text-zinc-900 transition">
              Tantangan Dapur
            </a>
            <a href="#solusi" className="hover:text-zinc-900 transition">
              Solusi Cerdas AI
            </a>
            <a href="#cara-kerja" className="hover:text-zinc-900 transition">
              Cara Kerja
            </a>
            <a href="#kepatuhan" className="hover:text-zinc-900 transition">
              Jaminan Halal & SOP
            </a>
          </nav>

          {/* Tombol Masuk / Dashboard */}
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

      {/* 2. HERO SECTION */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 border-b border-zinc-100">
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
            Ketika truk pemasok ayam utama terjebak banjir di jalur logistik, <strong>ResilioAI</strong> bekerja otomatis dalam hitungan detik: menghitung kekurangan stok, memilih pemasok cadangan yang resmi bersertifikat Halal, dan membagi jadwal pengiriman agar muat di kulkas dapur SPPG.
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
                Hanya mitra resmi BPJPH yang disetujui
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

      {/* 3. TANTANGAN VS SOLUSI */}
      <section id="masalah" className="py-20 bg-zinc-50/50 border-b border-zinc-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Tantangan Nyata di Dapur Gizi
            </h2>
            <p className="text-2xl sm:text-3xl font-bold text-zinc-900 mt-1">
              Mengapa Menangani Krisis Secara Manual Sangat Berisiko?
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Masalah 1 */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                1. Keterlambatan Tiba-Tiba
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Truk supplier ayam utama terjebak banjir di jalur Pantura. Jika petugas baru tahu pada sore hari, butuh 4–6 jam menelepon vendor lain secara manual. Jadwal masak subuh terancam batal.
              </p>
            </div>

            {/* Masalah 2 */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4">
                <Warehouse className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                2. Kulkas Dapur Terbatas
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Kekurangan ayam adalah 64 kg, tetapi sisa ruang kulkas pendingin hanya muat 20 kg. Jika semua dikirim sekaligus, daging ayam akan membusuk di luar ruangan.
              </p>
            </div>

            {/* Masalah 3 */}
            <div className="p-6 rounded-2xl bg-white border border-zinc-200 shadow-2xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-900 mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-zinc-900">
                3. Risiko Halal & Keabsahan
              </h3>
              <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                Dalam situasi panik, petugas berisiko memesan dari sembarang toko yang belum tentu memiliki sertifikat Halal BPJPH aktif atau harganya melampaui batas anggaran negara.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CARA KERJA SISTEM */}
      <section id="cara-kerja" className="py-20 bg-white border-b border-zinc-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Alur Kerja Otomatis
            </h2>
            <p className="text-2xl sm:text-3xl font-bold text-zinc-900 mt-1">
              Bagaimana ResilioAI Menyelesaikan Masalah Tersebut?
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-5 rounded-xl border border-zinc-200 bg-zinc-50/50">
              <div className="font-mono text-xs font-bold text-zinc-400 mb-2">
                LANGKAH 01
              </div>
              <h4 className="text-sm font-bold text-zinc-900">
                Hitung Stok Pasti
              </h4>
              <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                Sistem menghitung presisi: Butuh 144 kg, ada 80 kg di gudang, berarti kurang 64 kg. Tanpa tebakan AI.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-zinc-200 bg-zinc-50/50">
              <div className="font-mono text-xs font-bold text-zinc-400 mb-2">
                LANGKAH 02
              </div>
              <h4 className="text-sm font-bold text-zinc-900">
                Saring Pemasok Halal
              </h4>
              <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                Otomatis menyaring mitra terdekat yang memiliki sertifikasi Halal BPJPH resmi dan harga masuk anggaran.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-zinc-200 bg-zinc-50/50">
              <div className="font-mono text-xs font-bold text-zinc-400 mb-2">
                LANGKAH 03
              </div>
              <h4 className="text-sm font-bold text-zinc-900">
                Bagi Jadwal Kirim (2 Kali)
              </h4>
              <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                Batch 1 (20 kg) tiba sore untuk kulkas, Batch 2 (44 kg) tiba subuh langsung dipotong dan dimasak.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-zinc-200 bg-zinc-50/50">
              <div className="font-mono text-xs font-bold text-zinc-400 mb-2">
                LANGKAH 04
              </div>
              <h4 className="text-sm font-bold text-zinc-900">
                Persetujuan Resmi Kepala SPPG
              </h4>
              <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed">
                Kepala SPPG meninjau dan klik setuju di layar. Surat Pesanan (PO) resmi langsung terbit dan tercatat.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. CALL TO ACTION (CTA) */}
      <section className="py-16 bg-zinc-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-8 sm:p-12 rounded-3xl bg-white border border-zinc-200 shadow-sm">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 tracking-tight">
              Ingin Melihat Langsung Cara Kerjanya?
            </h2>
            <p className="mt-3 text-sm text-zinc-600 max-w-xl mx-auto leading-relaxed">
              Buka dashboard simulasi untuk menguji skenario banjir Pantura dan melihat bagaimana asisten cerdas ini membantu operasional dapur gizi SPPG.
            </p>
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/dashboard"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white font-semibold text-xs transition active:scale-95"
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

      {/* 6. FOOTER */}
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
