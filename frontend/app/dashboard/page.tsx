"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
  Users,
  BarChart3,
  HelpCircle,
  Check,
  LogOut,
  MessageSquare,
  Send,
  AlertTriangle,
  TrendingDown,
  Search,
  Printer,
  Calendar,
} from "lucide-react";
import {
  IncidentDecisionResponse,
  PipelineStreamEvent,
  PurchaseOrderResponse,
  SupplierRecord,
  SupplierCreateRequest,
} from "@/types/incident";
import {
  mockInventoryList,
  mockSuppliersList,
  mockPurchaseOrdersList,
} from "@/data/mockData";

export default function DashboardPage() {
  const router = useRouter();

  // Navigation Menu Aktif
  const [activeMenu, setActiveMenu] = useState<
    "overview" | "inventory" | "chat" | "po" | "suppliers" | "team" | "guide"
  >("overview");

  // Tab alur kerja di halaman overview
  const [activeTab, setActiveTab] = useState<"workflow" | "delivery" | "audit">(
    "workflow"
  );
  const [tableFilter, setTableFilter] = useState<"all" | "problem" | "safe">(
    "all"
  );

  // Status proses AI & SSE
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
  const [selectedPoForPrint, setSelectedPoForPrint] = useState<PurchaseOrderResponse | null>(null);

  // State Kurun Waktu Rekapitulasi Laporan Berkala
  const [recapPeriod, setRecapPeriod] = useState<"today" | "7d" | "30d" | "month">("today");
  const [isPrintingRecap, setIsPrintingRecap] = useState(false);

  // State Manajemen Pemasok
  const [suppliers, setSuppliers] = useState<SupplierRecord[]>(mockSuppliersList);
  const [supplierSearch, setSupplierSearch] = useState("");
  const [isAddSupplierModalOpen, setIsAddSupplierModalOpen] = useState(false);
  const [newSupplierName, setNewSupplierName] = useState("");
  const [newSupplierCommodity, setNewSupplierCommodity] = useState("DAGING_AYAM");
  const [newSupplierHalal, setNewSupplierHalal] = useState(true);
  const [newSupplierHalalNo, setNewSupplierHalalNo] = useState("ID32110000");
  const [newSupplierPrice, setNewSupplierPrice] = useState(37000);
  const [newSupplierCapacity, setNewSupplierCapacity] = useState(200);

  // State Chat Asisten AI
  const [chatMessages, setChatMessages] = useState<
    Array<{ sender: "user" | "ai"; text: string; time: string }>
  >([
    {
      sender: "ai",
      text: "Halo Bapak Budi Santoso! Saya Asisten AI ResilioAI SPPG. Ada laporan truk pemasok ayam utama terjebak banjir di jalur Pantura. Anda dapat bertanya tentang status stok gudang, mengecek sertifikasi halal pemasok, atau meminta alur pengiriman 2 tahap.",
      time: "Baru saja",
    },
  ]);
  const [inputChat, setInputChat] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Logout Handler
  const handleLogout = () => {
    if (confirm("Apakah Anda yakin ingin keluar dari sistem?")) {
      router.push("/");
    }
  };

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
      desc: "Harga Rp 36.500/kg (masuk anggaran) & tiba sebelum jam masak.",
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
      currentStock: "500 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tidak Perlu Tambahan",
      responsible: "Petugas Gudang",
      hasProblem: false,
    },
    {
      id: "ITEM-TELUR-01",
      name: "Telur Ayam Ras Segar",
      category: "Lauk Tambahan",
      target: "120 kg",
      currentStock: "120 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tidak Perlu Tambahan",
      responsible: "Petugas Gudang",
      hasProblem: false,
    },
    {
      id: "ITEM-WORTEL-01",
      name: "Wortel Segar Brastagi",
      category: "Sayuran Sehat",
      target: "40 kg",
      currentStock: "45 kg",
      need: "Stok Cukup",
      status: "Aman",
      solution: "Tiba Besok Jam 04.00",
      responsible: "Kru Dapur Olah",
      hasProblem: false,
    },
  ];

  // Menjalankan simulasi pencarian solusi
  const handleStartSimulation = async () => {
    setActiveMenu("overview");
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
        const payload = JSON.parse(e.data) as NonNullable<
          PipelineStreamEvent["data"]
        >;
        if (payload?.node === "deterministic_data_layer") setActiveStep(1);
        if (payload?.node === "compliance_filter") setActiveStep(2);
        if (payload?.node === "strategic_procurement_agent") setActiveStep(3);
        if (payload?.node === "feasibility_scoring_engine") setActiveStep(4);

        if (payload?.message) {
          setStatusMessage(payload.message);
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("node_completed", (e) => {
        const payload = JSON.parse(e.data) as NonNullable<
          PipelineStreamEvent["data"]
        >;
        if (payload?.node === "deterministic_data_layer") {
          setCompletedSteps((prev) => [...prev, 1]);
        }
        if (payload?.node === "compliance_filter") {
          setCompletedSteps((prev) => [...prev, 2]);
        }
        if (payload?.node === "strategic_procurement_agent") {
          setCompletedSteps((prev) => [...prev, 3]);
        }
        if (payload?.node === "feasibility_scoring_engine") {
          setCompletedSteps((prev) => [...prev, 4]);
        }

        if (payload?.message) {
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] Selesai: ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("workflow_waiting_approval", async (e) => {
        const payload = JSON.parse(e.data) as NonNullable<
          PipelineStreamEvent["data"]
        >;
        setActiveStep(5);
        setStatusMessage(
          payload?.message ||
            "Pencarian selesai! Menunggu persetujuan Anda sebagai Kepala SPPG."
        );
        eventSource.close();
        setIsSimulating(false);

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

  // Fungsi Cetak Dokumen Resmi PDF (Kop Surat SPPG)
  const handlePrintPo = (po?: PurchaseOrderResponse | null) => {
    setIsPrintingRecap(false);
    if (po) {
      setSelectedPoForPrint(po);
    } else if (issuedPO) {
      setSelectedPoForPrint(issuedPO);
    } else if (mockPurchaseOrdersList.length > 0) {
      setSelectedPoForPrint(mockPurchaseOrdersList[0]);
    }
    // Beri jeda 150ms agar state dokumen ter-update sebelum dialog cetak peramban terbuka
    setTimeout(() => {
      window.print();
    }, 150);
  };

  // Fungsi Cetak Laporan Rekapitulasi Berkala (PDF)
  const handlePrintRecap = () => {
    setIsPrintingRecap(true);
    setTimeout(() => {
      window.print();
    }, 150);
  };

  // Data Rekapitulasi Berdasarkan Kurun Waktu Pilihan
  const recapData = {
    today: {
      label: "Hari Ini (Operasional Real-Time)",
      badge: "Hari Ini",
      portions: "3.000",
      portionsUnit: "Porsi",
      portionsDesc: "Target Menu: Nasi & Daging Ayam",
      stockAyam: "80.0",
      stockUnit: "kg",
      stockDesc: "Kebutuhan harian dapur: 144 kg",
      deficit: "64.0",
      deficitUnit: "kg",
      deficitDesc: "Penyebab: Banjir di Jalur Pantura",
      freezer: "20.0",
      freezerUnit: "kg",
      freezerDesc: "Solusi: 2 Kali Pengiriman Bertahap",
      totalPoValue: "Rp 2.336.000",
      poCount: 1,
      totalDisruption: 1,
      efficiency: "Hemat Rp 5.500/kg dari pagu SOP",
    },
    "7d": {
      label: "7 Hari Terakhir (Mingguan)",
      badge: "7 Hari Terakhir",
      portions: "21.000",
      portionsUnit: "Porsi",
      portionsDesc: "100% Target Pemenuhan Program Gizi",
      stockAyam: "1.008",
      stockUnit: "kg",
      stockDesc: "Total pasokan masuk dapur (rata-rata 144 kg/hr)",
      deficit: "0.0",
      deficitUnit: "kg",
      deficitDesc: "1 Insiden Logistik Sukses Dimitigasi AI",
      freezer: "100%",
      freezerUnit: "Aman",
      freezerDesc: "SOP Kulkas 2-Tahap Berjalan Lancar",
      totalPoValue: "Rp 14.850.000",
      poCount: 3,
      totalDisruption: 1,
      efficiency: "Efisiensi 13.2% di bawah pagu anggaran",
    },
    "30d": {
      label: "30 Hari Terakhir (Bulanan)",
      badge: "30 Hari Terakhir",
      portions: "90.000",
      portionsUnit: "Porsi",
      portionsDesc: "Nol Gangguan Jadwal Makan Siswa",
      stockAyam: "4.320",
      stockUnit: "kg",
      stockDesc: "Total pasokan dari rekanan resmi terverifikasi",
      deficit: "0.0",
      deficitUnit: "kg",
      deficitDesc: "4 Insiden Terdeteksi & Termitigasi Cepat",
      freezer: "100%",
      freezerUnit: "Patuh",
      freezerDesc: "Nol Pembusukan Bahan (Zero Food Waste)",
      totalPoValue: "Rp 63.600.000",
      poCount: 8,
      totalDisruption: 4,
      efficiency: "Penghematan Total Rp 8.400.000",
    },
    month: {
      label: "Bulan Berjalan (November 2026)",
      badge: "November 2026",
      portions: "60.000",
      portionsUnit: "Porsi",
      portionsDesc: "20 Hari Efektif Sekolah / Program Gizi",
      stockAyam: "2.880",
      stockUnit: "kg",
      stockDesc: "Semua bahan berlabel Halal MUI/BPJPH",
      deficit: "0.0",
      deficitUnit: "kg",
      deficitDesc: "2 Insiden Banjir Cuaca Ekstrem Teratasi",
      freezer: "Optimal",
      freezerUnit: "Kapasitas",
      freezerDesc: "Kapasitas 120 kg/siklus termanfaatkan",
      totalPoValue: "Rp 42.400.000",
      poCount: 5,
      totalDisruption: 2,
      efficiency: "Rasio Keberhasilan Mitigasi AI: 100%",
    },
  }[recapPeriod];

  // Mengirim Pesan Chat ke Asisten AI
  const handleSendChat = async (textToSend?: string) => {
    const text = textToSend || inputChat;
    if (!text.trim()) return;

    const userMsg = {
      sender: "user" as const,
      text,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setInputChat("");
    setIsChatLoading(true);

    try {
      const res = await fetch("/api/mock/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "SESSION-BUDI-01",
          message: text,
          user_role: "Kepala SPPG",
        }),
      });

      const data = await res.json();

      setChatMessages((prev) => [
        ...prev,
        {
          sender: "ai" as const,
          text: data.reply,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "ai" as const,
          text: "Maaf, terjadi kendala saat memproses jawaban asisten AI.",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Mendaftarkan Pemasok Baru
  const handleAddSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: SupplierCreateRequest = {
        supplier_name: newSupplierName,
        category: "PROTEIN",
        commodity: newSupplierCommodity,
        supported_items: ["ITEM-AYAM-01"],
        halal_certified: newSupplierHalal,
        halal_cert_number: newSupplierHalal ? newSupplierHalalNo : undefined,
        unit_price_idr: Number(newSupplierPrice),
        daily_capacity_kg: Number(newSupplierCapacity),
      };

      const res = await fetch("/api/mock/suppliers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (data.supplier) {
        setSuppliers((prev) => [data.supplier, ...prev]);
        setIsAddSupplierModalOpen(false);
        alert(`Pemasok ${data.supplier.supplier_name} berhasil didaftarkan!`);
      }
    } catch {
      alert("Gagal mendaftarkan pemasok.");
    }
  };

  const filteredFoodItems = foodItems.filter((item) => {
    if (tableFilter === "problem") return item.hasProblem;
    if (tableFilter === "safe") return !item.hasProblem;
    return true;
  });

  const filteredSuppliers = suppliers.filter((s) =>
    s.supplier_name.toLowerCase().includes(supplierSearch.toLowerCase()) ||
    s.commodity.toLowerCase().includes(supplierSearch.toLowerCase())
  );

  return (
    <>
      {/* TAMPILAN INTERAKTIF DASHBOARD (DISEMBUNYIKAN SAAT MENCETAK KE PDF) */}
      <div className="flex min-h-screen bg-zinc-50/50 font-sans text-zinc-900 antialiased print:hidden">
      {/* 1. SIDEBAR KIRI: MINIMALIS, FORMAL PUTIH */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-zinc-200 bg-white">
        {/* Nama Lembaga / SPPG */}
        <div className="flex h-16 items-center justify-between border-b border-zinc-200 px-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-white font-bold text-xs">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="font-bold text-sm leading-tight text-zinc-900">
                ResilioAI
              </div>
              <p className="text-[11px] text-zinc-500">Dapur Gizi SPPG Wilayah I</p>
            </div>
          </Link>
          <ChevronDown className="h-4 w-4 text-zinc-400" />
        </div>

        {/* Tombol Utama */}
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

        {/* Menu Navigasi Lengkap & Berfungsi */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-6 text-xs font-medium">
          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Menu Utama
            </div>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveMenu("overview")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "overview"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <BarChart3 className="h-4 w-4 text-zinc-700" />
                <span>Ringkasan Dapur</span>
              </button>

              <button
                onClick={() => setActiveMenu("inventory")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "inventory"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <Warehouse className="h-4 w-4 text-zinc-600" />
                <span>Stok Bahan Makanan</span>
              </button>

              <button
                onClick={() => setActiveMenu("chat")}
                className={`w-full flex items-center justify-between rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "chat"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <MessageSquare className="h-4 w-4 text-zinc-600" />
                  <span>Asisten Chat AI</span>
                </div>
                <span className="text-[10px] font-bold bg-zinc-200 text-zinc-800 px-1.5 py-0.2 rounded-full">
                  LangGraph
                </span>
              </button>

              <button
                onClick={() => setActiveMenu("po")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "po"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <FileText className="h-4 w-4 text-zinc-600" />
                <span>Surat Pesanan (PO)</span>
              </button>

              <button
                onClick={() => setActiveMenu("suppliers")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "suppliers"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <Building2 className="h-4 w-4 text-zinc-600" />
                <span>Daftar Pemasok Halal</span>
              </button>
            </nav>
          </div>

          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Pengaturan & Bantuan
            </div>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveMenu("team")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "team"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <Users className="h-4 w-4 text-zinc-600" />
                <span>Petugas Dapur</span>
              </button>
              <button
                onClick={() => setActiveMenu("guide")}
                className={`w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-left transition ${
                  activeMenu === "guide"
                    ? "bg-zinc-100 font-bold text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                }`}
              >
                <HelpCircle className="h-4 w-4 text-zinc-600" />
                <span>Panduan Sederhana</span>
              </button>
            </nav>
          </div>
        </div>

        {/* Profil Penanggung Jawab & Logout */}
        <div className="border-t border-zinc-200 p-3 text-xs space-y-2">
          <div className="flex items-center justify-between px-2.5 py-2 rounded-lg bg-zinc-50 border border-zinc-200">
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
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 rounded-lg border border-zinc-200 py-2 text-xs font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition"
          >
            <LogOut className="h-3.5 w-3.5 text-zinc-500" />
            <span>Keluar Akun (Logout)</span>
          </button>
        </div>
      </aside>

      {/* 2. KONTEN UTAMA */}
      <div className="flex flex-1 flex-col overflow-x-hidden">
        {/* Header Atas */}
        <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 text-xs">
            <Link href="/" className="text-zinc-500 hover:text-zinc-800">
              Beranda
            </Link>
            <span className="text-zinc-300">/</span>
            <span className="font-semibold text-zinc-900 capitalize">
              {activeMenu === "overview" && "Dashboard Pemantauan Dapur SPPG"}
              {activeMenu === "inventory" && "Katalog Stok Bahan Gudang SPPG"}
              {activeMenu === "chat" && "Obrolan Interaktif dengan Asisten AI LangGraph"}
              {activeMenu === "po" && "Daftar & Arsip Surat Pesanan Resmi"}
              {activeMenu === "suppliers" && "Katalog Pemasok Resmi Bersertifikat Halal"}
              {activeMenu === "team" && "Daftar Personel & Petugas Dapur"}
              {activeMenu === "guide" && "Panduan Operasional & Standar SOP SPPG"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs text-zinc-600">
              <span className="h-2 w-2 rounded-full bg-zinc-900"></span>
              <span>Backend AI LangGraph Terhubung</span>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Keluar</span>
            </button>
          </div>
        </header>

        {/* Isi Dashboard Sesuai Menu Aktif */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {/* ===================================================================
              MENU 1: RINGKASAN DAPUR (OVERVIEW)
          =================================================================== */}
          {activeMenu === "overview" && (
            <div className="space-y-6">
              {/* FILTER KURUN WAKTU REKAPITULASI LAPORAN (PERIODIC RECAP BAR) */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-zinc-200 shadow-2xs">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-bold text-zinc-900 flex items-center gap-1.5">
                      <Calendar className="h-4 w-4 text-zinc-800" />
                      Rekapitulasi Pemantauan &amp; Ketahanan Dapur SPPG
                    </h2>
                    <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-zinc-100 text-zinc-800 border border-zinc-200">
                      {recapData.badge}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    Ringkasan performa pemenuhan makanan bergizi, logistik darurat, dan serapan anggaran
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {/* Selector Rentang Waktu */}
                  <div className="inline-flex rounded-lg border border-zinc-200 bg-zinc-50 p-1 text-xs font-medium text-zinc-600">
                    <button
                      onClick={() => setRecapPeriod("today")}
                      className={`rounded-md px-3 py-1.5 transition-all text-xs ${
                        recapPeriod === "today"
                          ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                          : "hover:text-zinc-900"
                      }`}
                    >
                      Hari Ini
                    </button>
                    <button
                      onClick={() => setRecapPeriod("7d")}
                      className={`rounded-md px-3 py-1.5 transition-all text-xs ${
                        recapPeriod === "7d"
                          ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                          : "hover:text-zinc-900"
                      }`}
                    >
                      7 Hari
                    </button>
                    <button
                      onClick={() => setRecapPeriod("30d")}
                      className={`rounded-md px-3 py-1.5 transition-all text-xs ${
                        recapPeriod === "30d"
                          ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                          : "hover:text-zinc-900"
                      }`}
                    >
                      30 Hari
                    </button>
                    <button
                      onClick={() => setRecapPeriod("month")}
                      className={`rounded-md px-3 py-1.5 transition-all text-xs ${
                        recapPeriod === "month"
                          ? "bg-white font-semibold text-zinc-900 shadow-2xs"
                          : "hover:text-zinc-900"
                      }`}
                    >
                      Bulan Ini
                    </button>
                  </div>

                  {/* Tombol Cetak Dokumen Rekapitulasi Berkala */}
                  <button
                    onClick={handlePrintRecap}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-900 px-3 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition shadow-2xs"
                    title="Cetak Laporan Rekapitulasi Resmi (PDF)"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    <span>Cetak Rekap (PDF)</span>
                  </button>
                </div>
              </div>

              {/* BARIS 1: 4 KARTU INFORMASI DINAMIS */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
                  <div className="text-xs font-medium text-zinc-500">
                    {recapPeriod === "today" ? "Target Masak Hari Ini" : "Total Porsi Makanan Disajikan"}
                  </div>
                  <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900 font-mono">
                    {recapData.portions}{" "}
                    <span className="text-sm font-normal text-zinc-500 font-sans">
                      {recapData.portionsUnit}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    {recapData.portionsDesc}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
                  <div className="text-xs font-medium text-zinc-500">
                    {recapPeriod === "today" ? "Stok Ayam Ada di Gudang" : "Total Pasokan Bahan Masuk"}
                  </div>
                  <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900 font-mono">
                    {recapData.stockAyam}{" "}
                    <span className="text-sm font-normal text-zinc-500 font-sans">
                      {recapData.stockUnit}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    {recapData.stockDesc}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
                  <div className="flex items-center justify-between text-xs font-medium text-zinc-500">
                    <span>{recapPeriod === "today" ? "Kekurangan Bahan" : "Status Insiden Logistik"}</span>
                    <span className="font-semibold text-zinc-900 text-[11px] px-1.5 py-0.5 rounded bg-zinc-100 flex items-center gap-1">
                      {recapPeriod === "today" ? (
                        <>
                          <TrendingDown className="h-3 w-3" /> Kurang 64 kg
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Termitigasi 100%
                        </>
                      )}
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900 font-mono">
                    {recapData.deficit}{" "}
                    <span className="text-sm font-normal text-zinc-500 font-sans">
                      {recapData.deficitUnit}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-600">
                    {recapData.deficitDesc}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-2xs">
                  <div className="text-xs font-medium text-zinc-500">
                    {recapPeriod === "today" ? "Sisa Ruang Kulkas / Freezer" : "Kepatuhan SOP & Ruang Kulkas"}
                  </div>
                  <div className="mt-2 text-2xl font-bold tracking-tight text-zinc-900 font-mono">
                    {recapData.freezer}{" "}
                    <span className="text-sm font-normal text-zinc-500 font-sans">
                      {recapData.freezerUnit}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-600">
                    {recapData.freezerDesc}
                  </p>
                </div>
              </div>

              {/* BARIS 2: ALUR KERJA OTOMATIS */}
              <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
                  <div>
                    <h2 className="text-sm font-bold text-zinc-900 flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-zinc-900" />
                      Penyelesaian Otomatis oleh Asisten AI LangGraph
                    </h2>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      Asisten memeriksa stok, menyaring pemasok resmi, dan membuat jadwal kirim.
                    </p>
                  </div>

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

                {/* TAB 1 */}
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

                {/* TAB 2 */}
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

                {/* TAB 3 */}
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
                            <strong>Kesesuaian Anggaran:</strong> Harga penawaran Rp 36.500/kg (masih di bawah pagu resmi Rp 42.000/kg).
                          </span>
                        </li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              {/* BARIS 3: TABEL DAFTAR BAHAN MAKANAN */}
              <div className="rounded-xl border border-zinc-200 bg-white shadow-2xs overflow-hidden">
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
            </div>
          )}

          {/* ===================================================================
              MENU 2: STOK BAHAN MAKANAN (INVENTORY DARI BRANCH AI)
          =================================================================== */}
          {activeMenu === "inventory" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-zinc-200">
                <div>
                  <h2 className="text-base font-bold text-zinc-900">
                    Katalog Inventaris Gudang Dapur SPPG
                  </h2>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    Data stok aktual, safety buffer, kapasitas kulkas pendingin, dan pagu SOP resmi
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-zinc-100 border border-zinc-200 font-semibold text-zinc-800">
                    Total: {mockInventoryList.length} Komoditas
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockInventoryList.map((item) => {
                  const isLow = item.current_stock_kg <= item.safety_stock_kg;
                  const hasFreezer = item.freezer_capacity_kg > 0;
                  const freezerRatio = hasFreezer
                    ? Math.round((item.freezer_occupied_kg / item.freezer_capacity_kg) * 100)
                    : 0;

                  return (
                    <div
                      key={item.item_id}
                      className="p-5 rounded-xl border border-zinc-200 bg-white shadow-2xs space-y-3"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-zinc-100 text-zinc-700 uppercase">
                            {item.category}
                          </span>
                          <h3 className="font-bold text-sm text-zinc-900 mt-1">
                            {item.item_name}
                          </h3>
                          <p className="text-[10px] font-mono text-zinc-400">
                            {item.item_id}
                          </p>
                        </div>
                        {isLow ? (
                          <span className="text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded">
                            Stok Kritis
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold text-zinc-700 bg-zinc-100 px-2 py-0.5 rounded">
                            Stok Aman
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-zinc-100 text-xs">
                        <div>
                          <span className="text-[11px] text-zinc-500">Stok Saat Ini:</span>
                          <div className="font-bold text-zinc-900 font-mono">
                            {item.current_stock_kg} kg
                          </div>
                        </div>
                        <div>
                          <span className="text-[11px] text-zinc-500">Batas Aman (SOP):</span>
                          <div className="font-medium text-zinc-700 font-mono">
                            {item.safety_stock_kg} kg
                          </div>
                        </div>
                      </div>

                      {hasFreezer ? (
                        <div className="pt-2 border-t border-zinc-100 space-y-1">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-zinc-500">Ruang Kulkas Terpakai:</span>
                            <span className="font-bold text-zinc-800">
                              {item.freezer_occupied_kg} / {item.freezer_capacity_kg} kg ({freezerRatio}%)
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-zinc-900 rounded-full"
                              style={{ width: `${Math.min(freezerRatio, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      ) : (
                        <div className="pt-2 border-t border-zinc-100 text-[11px] text-zinc-400">
                          Bahan kering (Gudang Suhu Ruang)
                        </div>
                      )}

                      <div className="pt-2 border-t border-zinc-100 flex justify-between items-center text-[11px]">
                        <span className="text-zinc-500">Pagu SOP Maksimal:</span>
                        <span className="font-bold font-mono text-zinc-900">
                          Rp {item.sop_max_price_per_kg.toLocaleString("id-ID")}/kg
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ===================================================================
              MENU 3: ASISTEN CHAT AI (CONVERSATIONAL AGENT /CHAT DARI BRANCH AI)
          =================================================================== */}
          {activeMenu === "chat" && (
            <div className="h-[calc(100vh-8.5rem)] flex flex-col bg-white rounded-xl border border-zinc-200 overflow-hidden shadow-2xs">
              {/* Header Chat */}
              <div className="p-4 border-b border-zinc-200 flex items-center justify-between bg-zinc-50/70">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-zinc-900 text-white flex items-center justify-center font-bold text-xs">
                    AI
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-zinc-900">
                      Asisten Kognitif ResilioAI (SPPG)
                    </h3>
                    <p className="text-[11px] text-zinc-500">
                      Tersambung ke API Agen Percakapan LangGraph • Model: Gemini 2.5 Flash
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-[11px] font-medium text-zinc-600">Online</span>
                </div>
              </div>

              {/* Chat Messages Body */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-xl rounded-2xl p-4 text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-zinc-900 text-white rounded-br-xs"
                          : "bg-zinc-100 text-zinc-900 rounded-bl-xs border border-zinc-200"
                      }`}
                    >
                      <p>{msg.text}</p>
                      <span
                        className={`block text-[10px] mt-1.5 ${
                          msg.sender === "user" ? "text-zinc-400" : "text-zinc-500"
                        }`}
                      >
                        {msg.time}
                      </span>
                    </div>
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-zinc-100 text-zinc-500 text-xs rounded-2xl px-4 py-2.5 flex items-center gap-2">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Asisten AI sedang berpikir...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Prompt Chips */}
              <div className="px-4 py-2 bg-zinc-50/50 border-t border-zinc-100 flex items-center gap-2 overflow-x-auto text-xs">
                <span className="text-[11px] text-zinc-400 shrink-0">Coba Tanya:</span>
                <button
                  onClick={() => handleSendChat("Cek stok gudang hari ini")}
                  className="px-2.5 py-1 rounded-md bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-100 shrink-0 text-[11px]"
                >
                  &quot;Cek stok gudang hari ini&quot;
                </button>
                <button
                  onClick={() => handleSendChat("Kenapa pengiriman harus dibagi 2 kali?")}
                  className="px-2.5 py-1 rounded-md bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-100 shrink-0 text-[11px]"
                >
                  &quot;Kenapa harus kirim 2 kali?&quot;
                </button>
                <button
                  onClick={() => handleSendChat("Siapa rekomendasi pemasok pengganti yang halal?")}
                  className="px-2.5 py-1 rounded-md bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-100 shrink-0 text-[11px]"
                >
                  &quot;Pemasok halal pengganti?&quot;
                </button>
              </div>

              {/* Chat Input Bar */}
              <div className="p-3 border-t border-zinc-200 bg-white flex items-center gap-2">
                <input
                  type="text"
                  value={inputChat}
                  onChange={(e) => setInputChat(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                  placeholder="Ketik pesan pertanyaan atau instruksi mitigasi di sini..."
                  className="flex-1 text-xs border border-zinc-300 rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-zinc-900 focus:border-zinc-900"
                />
                <button
                  onClick={() => handleSendChat()}
                  disabled={!inputChat.trim() || isChatLoading}
                  className="px-4 py-2.5 rounded-lg bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 disabled:bg-zinc-300 transition flex items-center gap-1.5"
                >
                  <span>Kirim</span>
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* ===================================================================
              MENU 4: SURAT PESANAN (PO)
          =================================================================== */}
          {activeMenu === "po" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-zinc-200">
                <div>
                  <h2 className="text-base font-bold text-zinc-900">
                    Arsip Surat Pesanan Resmi (Purchase Orders)
                  </h2>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    Seluruh PO hasil persetujuan Kepala SPPG yang tercatat dalam log audit permanen
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-zinc-100 border border-zinc-200 font-semibold text-zinc-800">
                    Total: {mockPurchaseOrdersList.length} PO Terbit
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-zinc-200 shadow-2xs overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-zinc-600">
                    <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                      <tr>
                        <th className="py-3 px-4">Nomor Pesanan (PO)</th>
                        <th className="py-3 px-4">Nama Pemasok Rekanan</th>
                        <th className="py-3 px-4">Bahan Pangan</th>
                        <th className="py-3 px-4">Kuantitas</th>
                        <th className="py-3 px-4">Harga Satuan</th>
                        <th className="py-3 px-4">Total Biaya (IDR)</th>
                        <th className="py-3 px-4">Skema Pengiriman</th>
                        <th className="py-3 px-4 text-right">Aksi</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {mockPurchaseOrdersList.map((po) => (
                        <tr key={po.po_number} className="hover:bg-zinc-50/60 transition">
                          <td className="py-3.5 px-4 font-mono font-bold text-zinc-900">
                            {po.po_number}
                          </td>
                          <td className="py-3.5 px-4 font-medium text-zinc-900">
                            {po.supplier_name}
                          </td>
                          <td className="py-3.5 px-4">{po.item_id}</td>
                          <td className="py-3.5 px-4 font-bold font-mono">
                            {po.approved_qty_kg} kg
                          </td>
                          <td className="py-3.5 px-4 font-mono">
                            Rp {po.unit_price_idr?.toLocaleString("id-ID")}
                          </td>
                          <td className="py-3.5 px-4 font-bold font-mono text-zinc-900">
                            Rp {po.total_amount_idr?.toLocaleString("id-ID")}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-zinc-100 text-zinc-800">
                              {po.logistics_strategy?.strategy_type || "DIRECT_DELIVERY"}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={() => handlePrintPo(po)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-zinc-200 text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 text-xs font-semibold transition shadow-2xs"
                              title="Cetak Surat Pesanan Resmi (PDF)"
                            >
                              <Printer className="h-3.5 w-3.5 text-zinc-600" />
                              <span>Cetak PDF</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              MENU 5: DAFTAR PEMASOK HALAL (SUPPLIERS CRUD DARI BRANCH AI)
          =================================================================== */}
          {activeMenu === "suppliers" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-zinc-200">
                <div>
                  <h2 className="text-base font-bold text-zinc-900">
                    Katalog Mitra Pemasok Resmi SPPG
                  </h2>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    Daftar mitra terdaftar, status sertifikat halal BPJPH, harga penawaran, dan kapasitas kirim harian
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsAddSupplierModalOpen(true)}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold transition"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Daftarkan Pemasok Baru</span>
                  </button>
                </div>
              </div>

              {/* Pencarian Pemasok */}
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-zinc-400" />
                <input
                  type="text"
                  value={supplierSearch}
                  onChange={(e) => setSupplierSearch(e.target.value)}
                  placeholder="Cari nama pemasok atau jenis komoditas (misal Daging Ayam, Sapi, Telur)..."
                  className="w-full bg-white border border-zinc-200 rounded-xl pl-9 pr-4 py-2.5 text-xs text-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900"
                />
              </div>

              {/* Tabel Pemasok */}
              <div className="bg-white rounded-xl border border-zinc-200 shadow-2xs overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-zinc-600">
                    <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
                      <tr>
                        <th className="py-3 px-4">ID Pemasok</th>
                        <th className="py-3 px-4">Nama Badan Usaha</th>
                        <th className="py-3 px-4">Komoditas</th>
                        <th className="py-3 px-4">Sertifikat Halal</th>
                        <th className="py-3 px-4">Harga / kg</th>
                        <th className="py-3 px-4">Kapasitas Harian</th>
                        <th className="py-3 px-4">Waktu Kirim</th>
                        <th className="py-3 px-4">Rating</th>
                        <th className="py-3 px-4 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {filteredSuppliers.map((sup) => (
                        <tr key={sup.supplier_id} className="hover:bg-zinc-50/60 transition">
                          <td className="py-3.5 px-4 font-mono font-bold text-zinc-900">
                            {sup.supplier_id}
                          </td>
                          <td className="py-3.5 px-4 font-medium text-zinc-900">
                            {sup.supplier_name}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-zinc-100 text-zinc-700">
                              {sup.commodity}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            {sup.halal_certified ? (
                              <div>
                                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold text-[11px]">
                                  <Check className="h-3 w-3" /> Halal Aktif
                                </span>
                                <div className="text-[10px] font-mono text-zinc-400">
                                  {sup.halal_cert_number}
                                </div>
                              </div>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-red-600 font-semibold text-[11px]">
                                <AlertTriangle className="h-3 w-3" /> Tidak Bersertifikat
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 font-mono font-bold text-zinc-900">
                            Rp {sup.unit_price_idr.toLocaleString("id-ID")}
                          </td>
                          <td className="py-3.5 px-4 font-mono">
                            {sup.daily_capacity_kg} kg/hari
                          </td>
                          <td className="py-3.5 px-4 text-zinc-600">
                            {sup.lead_time_hours} jam ({sup.distance_km} km)
                          </td>
                          <td className="py-3.5 px-4 font-mono font-bold">
                            {sup.reliability_rating}/100
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            {sup.is_active ? (
                              <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                                Aktif
                              </span>
                            ) : (
                              <span className="text-[10px] font-semibold text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded">
                                Non-aktif
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              MENU 6: PETUGAS DAPUR (TEAM)
          =================================================================== */}
          {activeMenu === "team" && (
            <div className="space-y-6">
              <div className="bg-white p-5 rounded-xl border border-zinc-200">
                <h2 className="text-base font-bold text-zinc-900">
                  Daftar Petugas & Personel Dapur SPPG Wilayah I
                </h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Struktur personel yang memiliki wewenang operasional dan persetujuan pengadaan
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-2xs space-y-3">
                  <div className="h-12 w-12 rounded-full bg-zinc-900 text-white flex items-center justify-center font-bold text-sm">
                    BS
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-900">Budi Santoso, S.T.</h3>
                    <p className="text-xs text-zinc-500">Kepala SPPG Wilayah I</p>
                  </div>
                  <div className="text-xs text-zinc-600 pt-2 border-t border-zinc-100 space-y-1">
                    <div>Wewenang: Otoritas Tunggal PO</div>
                    <div className="text-[11px] text-zinc-400">budi.santoso@sppg.go.id</div>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-2xs space-y-3">
                  <div className="h-12 w-12 rounded-full bg-zinc-200 text-zinc-800 flex items-center justify-center font-bold text-sm">
                    SR
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-900">Siti Rahmawati</h3>
                    <p className="text-xs text-zinc-500">Koordinator Gudang & Stok</p>
                  </div>
                  <div className="text-xs text-zinc-600 pt-2 border-t border-zinc-100 space-y-1">
                    <div>Wewenang: Input & Audit Fisik</div>
                    <div className="text-[11px] text-zinc-400">siti.gudang@sppg.go.id</div>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-2xs space-y-3">
                  <div className="h-12 w-12 rounded-full bg-zinc-200 text-zinc-800 flex items-center justify-center font-bold text-sm">
                    UF
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-900">Ustadz Fauzi, S.Ag.</h3>
                    <p className="text-xs text-zinc-500">Auditor Kepatuhan Halal</p>
                  </div>
                  <div className="text-xs text-zinc-600 pt-2 border-t border-zinc-100 space-y-1">
                    <div>Wewenang: Verifikasi BPJPH</div>
                    <div className="text-[11px] text-zinc-400">fauzi.halal@sppg.go.id</div>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 shadow-2xs space-y-3">
                  <div className="h-12 w-12 rounded-full bg-zinc-200 text-zinc-800 flex items-center justify-center font-bold text-sm">
                    AH
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-900">Chef Ahmad</h3>
                    <p className="text-xs text-zinc-500">Kepala Kru Pengolahan Dapur</p>
                  </div>
                  <div className="text-xs text-zinc-600 pt-2 border-t border-zinc-100 space-y-1">
                    <div>Wewenang: Jadwal Masak Subuh</div>
                    <div className="text-[11px] text-zinc-400">ahmad.dapur@sppg.go.id</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ===================================================================
              MENU 7: PANDUAN SEDERHANA (GUIDE / SOP)
          =================================================================== */}
          {activeMenu === "guide" && (
            <div className="space-y-6 max-w-4xl">
              <div className="bg-white p-5 rounded-xl border border-zinc-200">
                <h2 className="text-base font-bold text-zinc-900">
                  Panduan Operasional & Mitigasi Cerdas SPPG
                </h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Penjelasan praktis bagaimana asisten AI bekerja mendampingi pengambil keputusan
                </p>
              </div>

              <div className="space-y-4">
                <div className="bg-white p-5 rounded-xl border border-zinc-200 space-y-2">
                  <h3 className="text-xs font-bold text-zinc-900">
                    1. Mengapa Perhitungan Defisit Bebas Halusinasi?
                  </h3>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    Sistem tidak membiarkan AI menebak jumlah kekurangan bahan. Kalkulasi defisit dilakukan secara murni oleh rumus matematika tertutup:
                    <br />
                    <code className="text-zinc-800 bg-zinc-100 px-2 py-0.5 rounded text-[11px] mt-1 inline-block">
                      Defisit = (Kebutuhan Porsi x 1.2 Safety Factor) - Stok Fisik Gudang
                    </code>
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 space-y-2">
                  <h3 className="text-xs font-bold text-zinc-900">
                    2. Apa itu Syarat Mutlak Sertifikasi Halal (Gating Parameter)?
                  </h3>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    Sesuai UU JPH No. 33 Tahun 2014, pasokan bahan gizi anak wajib 100% Halal. Jika rekanan tidak memiliki sertifikat Halal BPJPH yang aktif, sistem otomatis memberikan skor 0 dan rekanan langsung dieliminasi tanpa pengecualian.
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 space-y-2">
                  <h3 className="text-xs font-bold text-zinc-900">
                    3. Kenapa Pengiriman Harus Dibagi 2 Tahap (Split Delivery)?
                  </h3>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    Kapasitas kulkas pendingin dapur hanya muat 20 kg, sedangkan defisit bahan mencapai 64 kg. Jika semua dikirim sekaligus, 44 kg daging ayam akan membusuk di luar kulkas. Agen AI mengatur Batch 1 (20 kg) tiba sore untuk masuk kulkas, dan Batch 2 (44 kg) tiba subuh jam 05.00 langsung masuk wajan penggorengan.
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-zinc-200 space-y-2">
                  <h3 className="text-xs font-bold text-zinc-900">
                    4. Mengapa Masih Butuh Persetujuan Kepala SPPG (Human-in-the-Loop)?
                  </h3>
                  <p className="text-xs text-zinc-600 leading-relaxed">
                    AI hanya bertindak sebagai asisten analis. Pengeluaran anggaran negara dan penerbitan Surat Pesanan (PO) secara hukum tetap mewajibkan tanda tangan / klik persetujuan dari Kepala SPPG sebagai pemegang otoritas anggaran.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* MODAL PERSETUJUAN KEPALA SPPG */}
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
                    Rp 36.500 / kg (Hemat Rp 5.500 dari pagu)
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

      {/* MODAL SURAT PESANAN */}
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

            <div className="flex gap-2">
              <button
                onClick={() => setIsPoModalOpen(false)}
                className="flex-1 rounded-lg border border-zinc-200 py-2.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 transition"
              >
                Tutup
              </button>
              <button
                onClick={() => handlePrintPo(issuedPO)}
                className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-zinc-900 py-2.5 text-xs font-semibold text-white hover:bg-zinc-800 transition shadow-xs"
              >
                <Printer className="h-4 w-4" />
                <span>Cetak PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DAFTARKAN PEMASOK BARU (MATCHING SUPPLIER CREATE REQUEST DARI BRANCH AI) */}
      {isAddSupplierModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-zinc-200">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="font-bold text-zinc-900 text-sm">
                Daftarkan Rekanan Pemasok Baru (Onboarding SPPG)
              </div>
              <button
                onClick={() => setIsAddSupplierModalOpen(false)}
                className="rounded-md p-1 text-zinc-400 hover:text-zinc-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddSupplier} className="mt-4 space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-zinc-700 mb-1">
                  Nama Badan Usaha / Rekanan *
                </label>
                <input
                  type="text"
                  required
                  value={newSupplierName}
                  onChange={(e) => setNewSupplierName(e.target.value)}
                  placeholder="Contoh: PT Unggas Mandiri Sejahtera"
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Jenis Komoditas Pangan
                  </label>
                  <select
                    value={newSupplierCommodity}
                    onChange={(e) => setNewSupplierCommodity(e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900"
                  >
                    <option value="DAGING_AYAM">DAGING_AYAM</option>
                    <option value="DAGING_SAPI">DAGING_SAPI</option>
                    <option value="TELUR_AYAM">TELUR_AYAM</option>
                    <option value="BERAS">BERAS</option>
                    <option value="TAHU">TAHU</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Sertifikasi Halal BPJPH
                  </label>
                  <select
                    value={newSupplierHalal ? "yes" : "no"}
                    onChange={(e) => setNewSupplierHalal(e.target.value === "yes")}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900"
                  >
                    <option value="yes">Bersertifikat Halal Aktif</option>
                    <option value="no">Belum Bersertifikat</option>
                  </select>
                </div>
              </div>

              {newSupplierHalal && (
                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Nomor Sertifikat Halal Resmi
                  </label>
                  <input
                    type="text"
                    value={newSupplierHalalNo}
                    onChange={(e) => setNewSupplierHalalNo(e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900 font-mono"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Harga Penawaran per kg (IDR)
                  </label>
                  <input
                    type="number"
                    required
                    value={newSupplierPrice}
                    onChange={(e) => setNewSupplierPrice(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900 font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-zinc-700 mb-1">
                    Kapasitas Kirim (kg/hari)
                  </label>
                  <input
                    type="number"
                    required
                    value={newSupplierCapacity}
                    onChange={(e) => setNewSupplierCapacity(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900 font-mono"
                  />
                </div>
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-3 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={() => setIsAddSupplierModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-zinc-600 hover:bg-zinc-100 text-xs font-semibold"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold shadow-xs"
                >
                  Daftarkan Pemasok
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>

      {/* ===================================================================
          DOKUMEN RESMI KOP SURAT SPPG (HANYA DITAMPILKAN SAAT CETAK / EXPORT PDF)
      =================================================================== */}
      <div className="hidden print:block min-h-screen bg-white text-zinc-900 p-8 font-sans">
        {isPrintingRecap ? (
          /* ==========================================================
             DOKUMEN 1: LAPORAN REKAPITULASI BERKALA KETAHANAN SPPG
          ========================================================== */
          <div>
            {/* KOP SURAT PEMERINTAH / SPPG */}
            <div className="border-b-2 border-zinc-900 pb-4 mb-6 text-center relative">
              <div className="text-[11px] font-bold tracking-widest uppercase text-zinc-600">
                Kementerian Koordinator Bidang Pemberdayaan Masyarakat
              </div>
              <div className="text-lg font-black tracking-wide uppercase text-zinc-900">
                Badan Gizi Nasional (BGN) Republik Indonesia
              </div>
              <div className="text-sm font-bold text-zinc-800">
                Satuan Pelayanan Program Gizi (SPPG) Wilayah I
              </div>
              <p className="text-[11px] text-zinc-500 mt-1">
                Jl. Pangan Sejahtera No. 12, Jawa Barat | Sistem Terpadu Pemantauan &amp; Ketahanan Logistik Bahan Makanan
              </p>
            </div>

            {/* JUDUL REKAPITULASI */}
            <div className="text-center mb-6">
              <h2 className="text-base font-bold uppercase tracking-wider underline">
                Laporan Rekapitulasi Berkala Ketahanan Rantai Pasok Pangan
              </h2>
              <p className="text-xs text-zinc-600 font-semibold mt-1">
                Kurun Waktu: {recapData.label}
              </p>
              <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                Dicetak Pada: {new Date().toLocaleDateString("id-ID", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
              </p>
            </div>

            {/* RINGKASAN METRIK REKAP */}
            <div className="grid grid-cols-4 gap-3 text-xs mb-6 border border-zinc-300 rounded-lg p-3.5 bg-zinc-50">
              <div className="border-r border-zinc-200 pr-2">
                <span className="text-zinc-500 block text-[11px]">Realisasi Porsi:</span>
                <span className="text-base font-bold text-zinc-900 font-mono">{recapData.portions} Porsi</span>
                <span className="text-[10px] text-zinc-500 block">100% Target Pemenuhan</span>
              </div>
              <div className="border-r border-zinc-200 pr-2">
                <span className="text-zinc-500 block text-[11px]">Pasokan Masuk:</span>
                <span className="text-base font-bold text-zinc-900 font-mono">{recapData.stockAyam} kg</span>
                <span className="text-[10px] text-zinc-500 block">100% Sertifikasi Halal</span>
              </div>
              <div className="border-r border-zinc-200 pr-2">
                <span className="text-zinc-500 block text-[11px]">Insiden Diminimalkan:</span>
                <span className="text-base font-bold text-zinc-900 font-mono">{recapData.totalDisruption} Insiden</span>
                <span className="text-[10px] text-emerald-700 font-semibold block">0 Menit Terlambat</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[11px]">Realisasi Pagu PO:</span>
                <span className="text-base font-bold text-zinc-900 font-mono">{recapData.totalPoValue}</span>
                <span className="text-[10px] text-zinc-500 block">{recapData.efficiency}</span>
              </div>
            </div>

            {/* TABEL LOG ARSIP SURAT PESANAN (PO) */}
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-800 mb-2">
                Daftar Transaksi Surat Pesanan Resmi (Purchase Orders) Terbit
              </h3>
              <table className="w-full text-xs border border-zinc-300">
                <thead className="bg-zinc-100 border-b border-zinc-300 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="p-2 border-r border-zinc-300 text-left">Nomor Registrasi PO</th>
                    <th className="p-2 border-r border-zinc-300 text-left">Mitra Rekanan Ditunjuk</th>
                    <th className="p-2 border-r border-zinc-300 text-left">Komoditas Bahan</th>
                    <th className="p-2 border-r border-zinc-300 text-center">Volume (Kg)</th>
                    <th className="p-2 border-r border-zinc-300 text-right">Harga Satuan</th>
                    <th className="p-2 text-right">Total Anggaran</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200">
                  {mockPurchaseOrdersList.map((po, idx) => (
                    <tr key={po.po_number || idx}>
                      <td className="p-2 border-r border-zinc-300 font-mono font-semibold">{po.po_number}</td>
                      <td className="p-2 border-r border-zinc-300 font-medium">{po.supplier_name}</td>
                      <td className="p-2 border-r border-zinc-300">{po.item_id}</td>
                      <td className="p-2 border-r border-zinc-300 text-center font-mono">{po.approved_qty_kg} kg</td>
                      <td className="p-2 border-r border-zinc-300 text-right font-mono">Rp {po.unit_price_idr?.toLocaleString("id-ID")}</td>
                      <td className="p-2 text-right font-bold font-mono">Rp {po.total_amount_idr?.toLocaleString("id-ID")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* CATATAN RESMI AUDIT KEPATUHAN */}
            <div className="border border-zinc-200 rounded p-3 mb-8 text-[11px] bg-zinc-50 leading-relaxed">
              <p className="font-bold text-zinc-900 mb-0.5">Catatan Integritas &amp; Kepatuhan Kebijakan SPPG:</p>
              <p className="text-zinc-700">
                Laporan ini diterbitkan secara otomatis dari log audit sistem Resilio-Ai. Seluruh alur mitigasi darurat memenuhi 7 parameter evaluasi (Gating Halal BPJPH/MUI, kepatuhan batas pagu harga SOP, penyesuaian kapasitas ruang pendingin freezer 2-tahap, serta kelayakan armada distribusi) dan telah disahkan oleh Pejabat Pembuat Komitmen (PPK) SPPG.
              </p>
            </div>

            {/* LEMBAR PENGESAHAN LAPORAN BERKALA */}
            <div className="grid grid-cols-3 gap-6 text-xs pt-4 text-center">
              <div>
                <p className="text-zinc-600">Diverifikasi Ahli Gizi,</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">( Siti Rahmawati, S.Gz )</p>
                <p className="text-[10px] text-zinc-500">Ahli Gizi SPPG Wilayah I</p>
              </div>

              <div>
                <p className="text-zinc-600">Petugas Gudang &amp; Logistik,</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">( Ahmad Fauzi )</p>
                <p className="text-[10px] text-zinc-500">Penanggung Jawab Inventaris</p>
              </div>

              <div>
                <p className="text-zinc-600">Mengetahui &amp; Menyetujui,</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">( Budi Santoso, S.T. )</p>
                <p className="text-[10px] text-zinc-500">Kepala SPPG Wilayah I</p>
              </div>
            </div>

            <div className="mt-8 pt-3 border-t border-zinc-200 text-center text-[10px] text-zinc-400 font-mono">
              Dokumen Rekapitulasi Resmi Resilio-Ai • Bukti Akuntabilitas SPPG GTNIC 2026
            </div>
          </div>
        ) : (
          /* ==========================================================
             DOKUMEN 2: SURAT PESANAN BAHAN MAKANAN DARURAT (PO)
          ========================================================== */
          <div>
            {/* KOP SURAT PEMERINTAH / SPPG */}
            <div className="border-b-2 border-zinc-900 pb-4 mb-6 text-center relative">
              <div className="text-[11px] font-bold tracking-widest uppercase text-zinc-600">
                Kementerian Koordinator Bidang Pemberdayaan Masyarakat
              </div>
              <div className="text-lg font-black tracking-wide uppercase text-zinc-900">
                Badan Gizi Nasional (BGN) Republik Indonesia
              </div>
              <div className="text-sm font-bold text-zinc-800">
                Satuan Pelayanan Program Gizi (SPPG) Wilayah I
              </div>
              <p className="text-[11px] text-zinc-500 mt-1">
                Jl. Pangan Sejahtera No. 12, Jawa Barat | Layanan Darurat Rantai Pasok Pangan Terpadu
              </p>
            </div>

            {/* JUDUL DOKUMEN & METADATA */}
            <div className="text-center mb-6">
              <h2 className="text-base font-bold uppercase tracking-wider underline">
                Surat Pesanan Bahan Makanan Darurat (Purchase Order)
              </h2>
              <p className="text-xs text-zinc-500 font-mono mt-0.5">
                Nomor Registrasi: {selectedPoForPrint?.po_number || issuedPO?.po_number || "PO-2026-003"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs mb-6 border border-zinc-200 rounded-lg p-3.5 bg-zinc-50/50">
              <div>
                <div className="text-zinc-500">Pemasok Alternatif Ditunjuk:</div>
                <div className="font-bold text-zinc-900 text-sm">
                  {selectedPoForPrint?.supplier_name || "PT Berkah Unggas Jaya"}
                </div>
                <div className="text-zinc-600">ID Rekanan: {selectedPoForPrint?.supplier_id || "SUP-ALT-02"}</div>
                <div className="text-zinc-600 font-medium">Sertifikat Halal: ID32110000123450124 (Terverifikasi BPJPH)</div>
              </div>
              <div className="text-right">
                <div className="text-zinc-500">Tanggal &amp; Waktu Persetujuan:</div>
                <div className="font-semibold text-zinc-900">
                  {selectedPoForPrint?.generated_at
                    ? new Date(selectedPoForPrint.generated_at).toLocaleString("id-ID", { dateStyle: "full", timeStyle: "short" })
                    : new Date().toLocaleString("id-ID", { dateStyle: "full", timeStyle: "short" })}
                </div>
                <div className="text-zinc-600 mt-1">
                  Dasar Penunjukan: <span className="font-semibold text-zinc-800">Resilio-Ai Multicriteria Scoring (94.2/100)</span>
                </div>
                <div className="text-zinc-500 text-[11px]">Kategori: Mitigasi Banjir Jalur Distribusi Utama</div>
              </div>
            </div>

            {/* TABEL RINCIAN PESANAN BARANG */}
            <table className="w-full text-xs border border-zinc-300 mb-6">
              <thead className="bg-zinc-100 border-b border-zinc-300 font-bold uppercase text-[11px]">
                <tr>
                  <th className="p-2.5 border-r border-zinc-300 text-center w-12">No</th>
                  <th className="p-2.5 border-r border-zinc-300 text-left">Kode &amp; Nama Komoditas</th>
                  <th className="p-2.5 border-r border-zinc-300 text-center w-28">Kuantitas</th>
                  <th className="p-2.5 border-r border-zinc-300 text-right w-36">Harga Satuan</th>
                  <th className="p-2.5 text-right w-40">Total Pembayaran</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-zinc-200">
                  <td className="p-2.5 border-r border-zinc-300 text-center font-mono">1</td>
                  <td className="p-2.5 border-r border-zinc-300">
                    <div className="font-bold text-zinc-900">
                      {selectedPoForPrint?.item_id || "ITEM-AYAM-01"} - Daging Ayam Segar Karkas
                    </div>
                    <div className="text-[11px] text-zinc-500">Standar Mutu Pangan Segar Dapur SPPG</div>
                  </td>
                  <td className="p-2.5 border-r border-zinc-300 text-center font-bold font-mono">
                    {selectedPoForPrint?.approved_qty_kg || 64} kg
                  </td>
                  <td className="p-2.5 border-r border-zinc-300 text-right font-mono">
                    Rp {selectedPoForPrint?.unit_price_idr?.toLocaleString("id-ID") || "36.500"}
                  </td>
                  <td className="p-2.5 text-right font-bold font-mono text-zinc-900">
                    Rp {selectedPoForPrint?.total_amount_idr?.toLocaleString("id-ID") || "2.336.000"}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr className="bg-zinc-50 font-bold border-t border-zinc-300">
                  <td colSpan={4} className="p-2.5 border-r border-zinc-300 text-right uppercase">
                    Total Beban Anggaran Pengadaan:
                  </td>
                  <td className="p-2.5 text-right font-mono text-sm text-zinc-900">
                    Rp {selectedPoForPrint?.total_amount_idr?.toLocaleString("id-ID") || "2.336.000"}
                  </td>
                </tr>
              </tfoot>
            </table>

            {/* LOGISTIK & INSTRUKSI PENGIRIMAN 2 TAHAP */}
            <div className="border border-zinc-300 rounded-lg p-3.5 mb-8 text-xs bg-zinc-50">
              <div className="font-bold text-zinc-900 mb-1.5 flex items-center justify-between">
                <span>Skema Pengiriman Bertahap (Menyesuaikan Kapasitas Ruang Kulkas Dapur 20.0 Kg):</span>
                <span className="font-mono text-[11px] text-zinc-600">Strategi: TWO_STAGE_STAGGERED</span>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-2">
                <div className="border border-zinc-200 bg-white rounded p-2.5">
                  <div className="font-semibold text-zinc-900">Pengiriman Tahap 1: 20.0 kg</div>
                  <div className="text-[11px] text-zinc-600 mt-0.5">Estimasi Tiba: Pukul 17:00 WIB Hari Ini</div>
                  <div className="text-[11px] text-zinc-500">Peruntukan: Persiapan masak malam (langsung masuk kulkas)</div>
                </div>
                <div className="border border-zinc-200 bg-white rounded p-2.5">
                  <div className="font-semibold text-zinc-900">Pengiriman Tahap 2: 44.0 kg</div>
                  <div className="text-[11px] text-zinc-600 mt-0.5">Estimasi Tiba: Pukul 05:00 WIB Besok Subuh</div>
                  <div className="text-[11px] text-zinc-500">Peruntukan: Pengolahan utama pagi hari (langsung masak)</div>
                </div>
              </div>
            </div>

            {/* LEMBAR PENGESAHAN DAN TANDA TANGAN */}
            <div className="grid grid-cols-3 gap-6 text-xs pt-4 text-center">
              <div>
                <p className="text-zinc-600">Diterima &amp; Diperiksa Oleh,</p>
                <p className="font-semibold text-zinc-800">Petugas Logistik SPPG</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">( Ahmad Fauzi )</p>
                <p className="text-[10px] text-zinc-500">NIP. 19880412 201503 1 002</p>
              </div>

              <div>
                <p className="text-zinc-600">Mitra Pemasok,</p>
                <p className="font-semibold text-zinc-800">{selectedPoForPrint?.supplier_name || "PT Berkah Unggas Jaya"}</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">( Perwakilan Rekanan )</p>
                <p className="text-[10px] text-zinc-500">Stempel &amp; Tanda Tangan</p>
              </div>

              <div>
                <p className="text-zinc-600">Disetujui Oleh,</p>
                <p className="font-semibold text-zinc-800">Kepala SPPG Wilayah I</p>
                <div className="h-16 flex items-end justify-center">
                  <span className="border-b border-zinc-400 w-36 inline-block"></span>
                </div>
                <p className="font-bold text-zinc-900 mt-1">
                  ( {selectedPoForPrint?.approver_name || issuedPO?.approver_name || "Budi Santoso, S.T."} )
                </p>
                <p className="text-[10px] text-zinc-500">Penanggung Jawab Operasional</p>
              </div>
            </div>

            <div className="mt-8 pt-3 border-t border-zinc-200 text-center text-[10px] text-zinc-400 font-mono">
              Dicetak secara otomatis melalui Sistem Ketahanan Rantai Pasok Pangan Resilio-Ai • GTNIC 2026
            </div>
          </div>
        )}
      </div>
    </>
  );
}
