"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  FileText,
  RefreshCw,
  UserCheck,
  Building2,
  X,
  Warehouse,
  ChevronDown,
  Plus,
  MoreVertical,
  Users,
  BarChart3,
  HelpCircle,
  Check,
} from "lucide-react";
import {
  IncidentDecisionResponse,
  PipelineStreamEvent,
  PurchaseOrderResponse,
} from "@/types/incident";

export default function DashboardPage() {
  // Tab tampilan alur kerja
  const [activeTab, setActiveTab] = useState<"workflow" | "delivery" | "audit">(
    "workflow"
  );
  const [tableFilter, setTableFilter] = useState<"all" | "problem" | "safe">(
    "all"
  );

  // Status proses AI
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>(
    "Sistem siap. Klik '+ Jalankan Solusi Otomatis' untuk mencari pemasok cadangan."
  );

  // Status keputusan & persetujuan
  const [decision, setDecision] = useState<IncidentDecisionResponse | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [approvedQty, setApprovedQty] = useState(64);
  const [approverNotes, setApproverNotes] = useState(
    "Disetujui untuk dikirim 2 kali agar muat di kulkas penyimpanan SPPG."
  );
  const [issuedPO, setIssuedPO] = useState<PurchaseOrderResponse | null>(null);
  const [isPoModalOpen, setIsPoModalOpen] = useState(false);

  // 5 Langkah sederhana alur kerja AI
  const steps = [
    {
      step: 1,
      id: "deterministic_data_layer",
      title: "1. Hitung Kekurangan Stok",
      desc: "Menghitung otomatis: Butuh 144 kg, ada 80 kg, kurang 64 kg.",
    },
    {
      step: 2,
      id: "compliance_filter",
      title: "2. Saring Pemasok Halal & Dekat",
      desc: "Memilih hanya pemasok resmi yang punya sertifikat halal aktif.",
    },
    {
      step: 3,
      id: "strategic_procurement_agent",
      title: "3. Atur Pengiriman Bertahap",
      desc: "Kulkas hanya muat 20 kg, jadi pengiriman dibagi 2 kali.",
    },
    {
      step: 4,
      id: "feasibility_scoring_engine",
      title: "4. Periksa Harga & Waktu Tiba",
      desc: "Harga Rp 38.000/kg (masuk anggaran) & tiba sebelum jam masak.",
    },
    {
      step: 5,
      id: "human_approval_gate",
      title: "5. Persetujuan Kepala SPPG",
      desc: "Menunggu Anda menyetujui sebelum surat pesanan resmi terbit.",
    },
  ];

  // Daftar bahan makanan dapur hari ini
  const foodItems = [
    {
      id: "ITEM-AYAM-01",
      name: "Daging Ayam Potong Segar",
      category: "Lauk Utama (Protein)",
      target: "144 kg (3.000 Porsi)",
      currentStock: "80 kg",
      need: "Kurang 64 kg",
      status: decision ? "Menunggu Persetujuan" : "Pengiriman Terhambat",
      solution: "Kirim 2 Kali (Sore & Subuh)",
      responsible: "Budi Santoso (Kepala SPPG)",
      hasProblem: true,
    },
    {
      id: "ITEM-BERAS-01",
      name: "Beras Putih Ramos",
      category: "Makanan Pokok",
      target: "450 kg",
      currentStock: "520 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tidak Perlu Tambahan",
      responsible: "Petugas Gudang",
      hasProblem: false,
    },
    {
      id: "ITEM-TELUR-02",
      name: "Telur Ayam Negeri Grade A",
      category: "Lauk Tambahan",
      target: "120 kg",
      currentStock: "135 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tidak Perlu Tambahan",
      responsible: "Petugas Gudang",
      hasProblem: false,
    },
    {
      id: "ITEM-SAYUR-05",
      name: "Sayur Bayam Hijau Segar",
      category: "Sayuran Sehat",
      target: "85 kg",
      currentStock: "90 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tiba Besok Jam 04.00",
      responsible: "Kru Dapur Olah",
      hasProblem: false,
    },
  ];

  // Menjalankan simulasi pencarian solusi
  const handleStartSimulation = async () => {
    setIsSimulating(true);
    setDecision(null);
    setIssuedPO(null);
    setCompletedSteps([]);
    setActiveStep(1);
    setStreamLogs([]);
    setStatusMessage("Menghubungkan ke asisten pintar...");

    try {
      const triggerRes = await fetch("/api/mock/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_id: "ITEM-AYAM-01",
          disruption_type: "WEATHER_FLOOD",
          affected_supplier_id: "SUP-UTAMA-01",
          estimated_duration_days: 3,
        }),
      });

      const triggerData = await triggerRes.json();
      const streamUrl = triggerData.stream_url || "/api/mock/stream";

      const eventSource = new EventSource(streamUrl);

      eventSource.addEventListener("node_started", (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        if (payload.node === "deterministic_data_layer") setActiveStep(1);
        if (payload.node === "compliance_filter") setActiveStep(2);
        if (payload.node === "strategic_procurement_agent") setActiveStep(3);
        if (payload.node === "feasibility_scoring_engine") setActiveStep(4);

        if (payload.message) {
          setStatusMessage(payload.message);
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("node_completed", (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        if (payload.node === "deterministic_data_layer") {
          setCompletedSteps((prev) => [...prev, 1]);
        }
        if (payload.node === "compliance_filter") {
          setCompletedSteps((prev) => [...prev, 2]);
        }
        if (payload.node === "strategic_procurement_agent") {
          setCompletedSteps((prev) => [...prev, 3]);
        }
        if (payload.node === "feasibility_scoring_engine") {
          setCompletedSteps((prev) => [...prev, 4]);
        }

        if (payload.message) {
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] Selesai: ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("workflow_waiting_approval", async (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        setActiveStep(5);
        setStatusMessage(
          payload.message ||
            "Pencarian selesai! Menunggu persetujuan Anda sebagai Kepala SPPG."
        );
        eventSource.close();
        setIsSimulating(false);

        // Ambil data rekomendasi lengkap
        const decRes = await fetch("/api/mock/decision");
        const decData: IncidentDecisionResponse = await decRes.json();
        setDecision(decData);
      });

      eventSource.onerror = () => {
        eventSource.close();
        setIsSimulating(false);
      };
    } catch {
      setIsSimulating(false);
      setStatusMessage("Terjadi kendala saat menghubungkan ke sistem.");
    }
  };

  // Persetujuan surat pesanan oleh Kepala SPPG
  const handleApprove = async () => {
    try {
      const res = await fetch("/api/mock/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          incident_id: decision?.incident_id || "INC-2026-001",
          action: "APPROVE",
          approved_qty_kg: approvedQty,
          approver_name: "Budi Santoso, S.T. (Kepala SPPG)",
          approver_notes: approverNotes,
        }),
      });

      const poData: PurchaseOrderResponse = await res.json();
      setIssuedPO(poData);
      setCompletedSteps((prev) => [...prev, 5]);
      setActiveStep(null);
      setIsApprovalModalOpen(false);
      setIsPoModalOpen(true);
      setStatusMessage(
        `Surat Pesanan Resmi No. ${poData.po_number} berhasil dibuat. Bahan siap dikirim!`
      );
    } catch {
      alert("Gagal memproses persetujuan");
    }
  };

  // Filter daftar tabel
  const filteredFoodItems = foodItems.filter((item) => {
    if (tableFilter === "problem") return item.hasProblem;
    if (tableFilter === "safe") return !item.hasProblem;
    return true;
  });

  return (
    <div className="flex min-h-screen bg-zinc-50/50 font-sans text-zinc-900 antialiased">
      {/* =========================================================================
          1. SIDEBAR KIRI: MINIMALIS, FORMAL PUTIH
      ========================================================================= */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-zinc-200 bg-white">
        {/* Nama Lembaga / SPPG */}
        <div className="flex h-16 items-center justify-between border-b border-zinc-200 px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white font-bold text-xs">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="font-bold text-sm leading-tight text-zinc-900">
                ResilioAI
              </div>
              <p className="text-[11px] text-zinc-500">Dapur Gizi SPPG Wilayah I</p>
            </div>
          </div>
          <ChevronDown className="h-4 w-4 text-zinc-400" />
        </div>

        {/* Tombol Utama (+ Jalankan Solusi Otomatis) */}
        <div className="p-4 border-b border-zinc-100">
          <button
            onClick={handleStartSimulation}
            disabled={isSimulating}
            className={`w-full flex items-center justify-center gap-2 rounded-lg py-2.5 px-3 text-xs font-semibold text-white transition-all shadow-xs ${
              isSimulating
                ? "bg-zinc-400 cursor-not-allowed"
                : "bg-zinc-900 hover:bg-zinc-800 active:scale-[0.98]"
            }`}
          >
            {isSimulating ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Plus className="h-3.5 w-3.5" />
            )}
            <span>
              {isSimulating ? "Sedang Memeriksa..." : "Jalankan Solusi Otomatis"}
            </span>
          </button>
        </div>

        {/* Menu Navigasi Sederhana */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-6 text-xs font-medium">
          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Menu Utama
            </div>
            <nav className="space-y-1">
              <button className="w-full flex items-center gap-2.5 rounded-md bg-zinc-100 px-3 py-2 font-semibold text-zinc-900">
                <BarChart3 className="h-4 w-4 text-zinc-700" />
                <span>Ringkasan Dapur</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900">
                <Warehouse className="h-4 w-4 text-zinc-400" />
                <span>Stok Bahan Makanan</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900">
                <FileText className="h-4 w-4 text-zinc-400" />
                <span>Surat Pesanan (PO)</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900">
                <Building2 className="h-4 w-4 text-zinc-400" />
                <span>Daftar Pemasok Halal</span>
              </button>
            </nav>
          </div>

          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Pengaturan & Bantuan
            </div>
            <nav className="space-y-1">
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900">
                <Users className="h-4 w-4 text-zinc-400" />
                <span>Petugas Dapur</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900">
                <HelpCircle className="h-4 w-4 text-zinc-400" />
                <span>Panduan Sederhana</span>
              </button>
            </nav>
          </div>
        </div>

        {/* Profil Penanggung Jawab */}
        <div className="border-t border-zinc-200 p-3 text-xs">
          <div className="flex items-center justify-between px-2 py-2 rounded-lg bg-zinc-50 border border-zinc-200">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 rounded-full bg-zinc-200 text-zinc-800 flex items-center justify-center font-bold text-xs shrink-0">
                BS
              </div>
              <div className="truncate">
                <div className="text-xs font-bold text-zinc-900 truncate">
                  Budi Santoso, S.T.
                </div>
                <div className="text-[10px] text-zinc-500 truncate">
                  Kepala SPPG Wilayah I
                </div>
              </div>
            </div>
            <MoreVertical className="h-4 w-4 text-zinc-400 shrink-0" />
          </div>
        </div>
      </aside>

      {/* =========================================================================
          2. KONTEN UTAMA: PUTIH BERSIH & FORMAL
      ========================================================================= */}
      <div className="flex flex-1 flex-col overflow-x-hidden">
        {/* Header Atas */}
        <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-zinc-500">Dapur Gizi SPPG</span>
            <span className="text-zinc-300">/</span>
            <span className="font-semibold text-zinc-900">
              Pemantauan Kebutuhan Masak Hari Ini
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs text-zinc-600">
              <span className="h-2 w-2 rounded-full bg-zinc-900"></span>
              <span>Sistem Pemantauan Aktif</span>
            </div>

            <button
              onClick={handleStartSimulation}
              disabled={isSimulating}
              className="lg:hidden flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 text-white text-xs font-semibold"
            >
              <RefreshCw
                className={`h-3 w-3 ${isSimulating ? "animate-spin" : ""}`}
              />
              <span>Solusi AI</span>
            </button>
          </div>
        </header>

        {/* Isi Dashboard */}
        <main className="flex-1 space-y-6 p-4 sm:p-6 lg:p-8">
          {/* =====================================================================
              BARIS 1: 4 KARTU INFORMASI PENTING (BERSIH & JELAS)
          ===================================================================== */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Kartu 1: Target Porsi */}
            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
              <div className="text-xs font-medium text-zinc-500">
                Target Masak Hari Ini
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900">
                3.000 <span className="text-sm font-normal text-zinc-500">Porsi</span>
              </div>
              <p className="mt-1 text-xs text-zinc-500">
                Menu Utama: Nasi & Daging Ayam
              </p>
            </div>

            {/* Kartu 2: Stok Tersedia */}
            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
              <div className="text-xs font-medium text-zinc-500">
                Stok Ayam Ada di Gudang
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900">
                80.0 <span className="text-sm font-normal text-zinc-500">kg</span>
              </div>
              <p className="mt-1 text-xs text-zinc-500">
                Total yang dibutuhkan dapur: 144 kg
              </p>
            </div>

            {/* Kartu 3: Kekurangan Bahan (Peringatan Jelas) */}
            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
              <div className="flex items-center justify-between text-xs font-medium text-zinc-500">
                <span>Kekurangan Bahan</span>
                <span className="font-semibold text-zinc-900 text-[11px] px-1.5 py-0.5 rounded bg-zinc-100">
                  Perlu Ditambah
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900">
                64.0 <span className="text-sm font-normal text-zinc-500">kg</span>
              </div>
              <p className="mt-1 text-xs text-zinc-600">
                Penyebab: Truk pemasok utama terhambat banjir
              </p>
            </div>

            {/* Kartu 4: Kapasitas Kulkas */}
            <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
              <div className="text-xs font-medium text-zinc-500">
                Sisa Ruang Kulkas / Freezer
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900">
                20.0 <span className="text-sm font-normal text-zinc-500">kg</span>
              </div>
              <p className="mt-1 text-xs text-zinc-600">
                Solusi: Bahan dikirim 2 kali agar muat
              </p>
            </div>
          </div>

          {/* =====================================================================
              BARIS 2: KARTU TENGAH (ALUR KERJA OTOMATIS AI)
          ===================================================================== */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs">
            {/* Header Bagian Tengah */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
              <div>
                <h2 className="text-sm font-bold text-zinc-900 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-zinc-900" />
                  Penyelesaian Otomatis oleh Asisten AI
                </h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Asisten memeriksa stok, menyaring pemasok resmi, dan membuat jadwal kirim.
                </p>
              </div>

              {/* Tab Pilihan */}
              <div className="inline-flex rounded-lg border border-zinc-200 bg-zinc-50 p-1 text-xs font-medium text-zinc-600">
                <button
                  onClick={() => setActiveTab("workflow")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "workflow"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  5 Langkah Kerja AI
                </button>
                <button
                  onClick={() => setActiveTab("delivery")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "delivery"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  Rencana Pengiriman (2 Kali)
                </button>
                <button
                  onClick={() => setActiveTab("audit")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "audit"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  Riwayat Pengecekan
                </button>
              </div>
            </div>

            {/* TAB 1: 5 LANGKAH KERJA SEDERHANA */}
            {activeTab === "workflow" && (
              <div className="mt-6 space-y-5">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
                  {steps.map((s) => {
                    const isDone = completedSteps.includes(s.step);
                    const isRunning = activeStep === s.step;

                    return (
                      <div
                        key={s.step}
                        className={`rounded-xl border p-4 transition-all ${
                          isRunning
                            ? "border-zinc-900 bg-zinc-50 shadow-xs"
                            : isDone
                            ? "border-zinc-300 bg-white"
                            : "border-zinc-200 bg-zinc-50/50 opacity-60"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold text-zinc-400">
                            LANGKAH 0{s.step}
                          </span>
                          {isDone ? (
                            <CheckCircle2 className="h-4 w-4 text-zinc-900" />
                          ) : isRunning ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-zinc-900" />
                          ) : (
                            <span className="h-2 w-2 rounded-full bg-zinc-300"></span>
                          )}
                        </div>

                        <h4 className="text-xs font-bold text-zinc-900">
                          {s.title}
                        </h4>
                        <p className="mt-1 text-[11px] text-zinc-500 leading-relaxed">
                          {s.desc}
                        </p>
                      </div>
                    );
                  })}
                </div>

                {/* Status Ticker Sederhana */}
                <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-xs text-zinc-700 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-zinc-900 shrink-0"></span>
                      <span className="font-semibold text-zinc-900">
                        Status Saat Ini:
                      </span>
                      <span className="text-zinc-600">{statusMessage}</span>
                    </div>

                    {decision && !issuedPO && (
                      <button
                        onClick={() => setIsApprovalModalOpen(true)}
                        className="rounded-lg bg-zinc-900 px-4 py-2 font-semibold text-xs text-white hover:bg-zinc-800 transition active:scale-95 shrink-0"
                      >
                        Buka Persetujuan Kepala SPPG
                      </button>
                    )}
                  </div>

                  {streamLogs.length > 0 && (
                    <div className="pt-2 border-t border-zinc-200/60 max-h-20 overflow-y-auto space-y-1 text-[11px] text-zinc-500 font-mono">
                      {streamLogs.slice(0, 3).map((log, idx) => (
                        <div key={idx} className="flex items-center gap-1.5">
                          <span className="text-zinc-400">›</span>
                          <span>{log}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: RENCANA PENGIRIMAN 2 KALI */}
            {activeTab === "delivery" && (
              <div className="mt-6 space-y-4">
                <div className="rounded-lg border border-zinc-200 p-4 bg-zinc-50/50">
                  <div className="font-bold text-xs text-zinc-900">
                    Kenapa Pengiriman Harus Dibagi 2 Kali?
                  </div>
                  <p className="mt-1 text-xs text-zinc-600 leading-relaxed">
                    Kekurangan bahan adalah <strong>64 kg</strong>, tetapi kulkas pendingin
                    dapur saat ini hanya muat <strong>20 kg</strong>. Jika semua dikirim
                    sekaligus, ayam akan rusak di suhu luar. Maka asisten AI membaginya
                    menjadi 2 tahap pengiriman:
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-zinc-200 bg-white p-4">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-zinc-900">
                        Pengiriman 1 (Sore Hari)
                      </span>
                      <span className="font-bold px-2 py-0.5 rounded bg-zinc-100 text-zinc-900">
                        20 kg
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-zinc-600">
                      <strong>Waktu Tiba:</strong> Sore ini, jam 17.00 WIB.
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      Langsung disimpan di kulkas freezer untuk persiapan malam.
                    </p>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-white p-4">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-zinc-900">
                        Pengiriman 2 (Subuh Hari Masak)
                      </span>
                      <span className="font-bold px-2 py-0.5 rounded bg-zinc-100 text-zinc-900">
                        44 kg
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-zinc-600">
                      <strong>Waktu Tiba:</strong> Besok subuh, jam 05.00 WIB.
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      Langsung dipotong dan masuk wajan masak pagi (tidak butuh kulkas).
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: RIWAYAT PENGECEKAN RESMI */}
            {activeTab === "audit" && (
              <div className="mt-6 space-y-3">
                <div className="rounded-xl border border-zinc-200 bg-white p-4 text-xs space-y-2">
                  <div className="font-bold text-zinc-900">
                    Bukti Pemeriksaan Sistem (Bebas Rekayasa):
                  </div>
                  <ul className="space-y-2 text-zinc-600">
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-zinc-900 shrink-0 mt-0.5" />
                      <span>
                        <strong>Hitungan Matematis:</strong> Kebutuhan 144 kg - Stok 80 kg = Kurang 64 kg.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-zinc-900 shrink-0 mt-0.5" />
                      <span>
                        <strong>Sertifikat Halal:</strong> Pemasok pengganti (PT Berkah Unggas Jaya) terdaftar aktif di BPJPH.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-zinc-900 shrink-0 mt-0.5" />
                      <span>
                        <strong>Kesesuaian Anggaran:</strong> Harga penawaran Rp 38.000/kg (masih di bawah pagu resmi Rp 40.000/kg).
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* =====================================================================
              BARIS 3: TABEL DAFTAR BAHAN MAKANAN HARI INI
          ===================================================================== */}
          <div className="rounded-xl border border-zinc-200 bg-white shadow-2xs overflow-hidden">
            {/* Header Kontrol Tabel */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-200 p-4">
              <div className="inline-flex rounded-lg border border-zinc-200 bg-zinc-50 p-1 text-xs font-medium text-zinc-600">
                <button
                  onClick={() => setTableFilter("all")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    tableFilter === "all"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  Semua Bahan (4)
                </button>
                <button
                  onClick={() => setTableFilter("problem")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    tableFilter === "problem"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  Perlu Tindakan (1)
                </button>
                <button
                  onClick={() => setTableFilter("safe")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    tableFilter === "safe"
                      ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                      : "hover:text-zinc-900"
                  }`}
                >
                  Stok Aman (3)
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsApprovalModalOpen(true)}
                  disabled={!decision || !!issuedPO}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                    decision && !issuedPO
                      ? "bg-zinc-900 text-white hover:bg-zinc-800"
                      : "bg-zinc-100 text-zinc-400 cursor-not-allowed"
                  }`}
                >
                  <UserCheck className="h-3.5 w-3.5" />
                  <span>Persetujuan Pesanan</span>
                </button>
              </div>
            </div>

            {/* Tabel Data */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-zinc-600">
                <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                  <tr>
                    <th scope="col" className="py-3 px-4">Nama Bahan Makanan</th>
                    <th scope="col" className="py-3 px-4">Kategori</th>
                    <th scope="col" className="py-3 px-4">Status Pengiriman</th>
                    <th scope="col" className="py-3 px-4">Kebutuhan / Stok</th>
                    <th scope="col" className="py-3 px-4">Rencana Tindakan</th>
                    <th scope="col" className="py-3 px-4">Penanggung Jawab</th>
                    <th scope="col" className="py-3 px-4 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {filteredFoodItems.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-zinc-50/60 transition-colors"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-zinc-900">{item.name}</div>
                        <div className="text-[10px] text-zinc-400">{item.id}</div>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-zinc-700">
                        {item.category}
                      </td>
                      <td className="py-3.5 px-4">
                        {item.hasProblem ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-0.5 text-[11px] font-bold text-zinc-900 border border-zinc-300">
                            {issuedPO ? "Pesanan Selesai" : item.status}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-0.5 text-[11px] font-semibold text-zinc-700">
                            <Check className="h-3 w-3" />
                            {item.status}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-zinc-900">{item.target}</div>
                        <div className="text-[10px] text-zinc-500">
                          {item.need}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-zinc-800">
                        {item.solution}
                      </td>
                      <td className="py-3.5 px-4 text-zinc-700">
                        {item.responsible}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {item.hasProblem && decision && !issuedPO ? (
                          <button
                            onClick={() => setIsApprovalModalOpen(true)}
                            className="rounded-md bg-zinc-900 px-3 py-1 text-xs font-semibold text-white hover:bg-zinc-800"
                          >
                            Setujui
                          </button>
                        ) : (
                          <span className="text-zinc-400 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* =========================================================================
          3. DIALOG PERSETUJUAN KEPALA SPPG (SEDERHANA & JELAS)
      ========================================================================= */}
      {isApprovalModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-zinc-200">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="font-bold text-zinc-900 text-sm">
                Persetujuan Pesanan Pengganti (Kepala SPPG)
              </div>
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="rounded-md p-1 text-zinc-400 hover:text-zinc-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Bahan yang Dibeli:</span>
                  <span className="font-bold text-zinc-900">Daging Ayam Potong Segar</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Pemasok Pengganti:</span>
                  <span className="font-bold text-zinc-900">
                    PT Berkah Unggas Jaya (100% Halal)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Harga Satuan:</span>
                  <span className="font-bold text-zinc-900">
                    Rp 38.000 / kg (Hemat Rp 2.000 dari pagu)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Cara Pengiriman:</span>
                  <span className="font-semibold text-zinc-900">
                    2 Kali (20 kg Sore Ini + 44 kg Subuh Besok)
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Jumlah yang Disetujui untuk Dipesan (kg)
                </label>
                <input
                  type="number"
                  value={approvedQty}
                  onChange={(e) => setApprovedQty(Number(e.target.value))}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm font-semibold focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900"
                />
                <span className="mt-1 block text-[11px] text-zinc-500">
                  Kekurangan stok di dapur: 64 kg.
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Catatan Persetujuan
                </label>
                <textarea
                  value={approverNotes}
                  onChange={(e) => setApproverNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-xs focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900"
                ></textarea>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3 border-t border-zinc-100 pt-4">
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-zinc-600 hover:text-zinc-900"
              >
                Batal
              </button>
              <button
                onClick={handleApprove}
                className="rounded-lg bg-zinc-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-zinc-800 active:scale-95"
              >
                Setujui & Buat Surat Pesanan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          4. MODAL SURAT PESANAN BERHASIL DIBUAT
      ========================================================================= */}
      {isPoModalOpen && issuedPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-2xl border border-zinc-200">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-900">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-zinc-900">
              Surat Pesanan Resmi Berhasil Diterbitkan!
            </h3>
            <p className="mt-1 text-xs text-zinc-500">
              Pemasok telah menerima notifikasi dan siap mengantar bahan sesuai jadwal.
            </p>

            <div className="my-5 space-y-2 rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-left text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Nomor Pesanan:</span>
                <span className="font-bold text-zinc-900">
                  {issuedPO.po_number}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Disetujui Oleh:</span>
                <span className="font-semibold text-zinc-900">
                  {issuedPO.approver_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Jumlah Pesanan:</span>
                <span className="font-bold text-zinc-900">
                  {issuedPO.approved_qty_kg} kg
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Waktu Terbit:</span>
                <span className="text-zinc-600">
                  {new Date(issuedPO.generated_at).toLocaleString("id-ID")}
                </span>
              </div>
            </div>

            <button
              onClick={() => setIsPoModalOpen(false)}
              className="w-full rounded-lg bg-zinc-900 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800 transition"
            >
              Tutup & Kembali ke Tampilan Utama
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
