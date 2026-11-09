"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Send,
  Bot,
  User,
  RefreshCw,
  FileText,
  Check,
  X,
  Warehouse,
  Boxes,
  Activity,
  Layers,
  Truck,
  Building2,
  SlidersHorizontal,
} from "lucide-react";
import {
  IncidentDecisionResponse,
  PipelineStreamEvent,
  PurchaseOrderResponse,
  SupplierRecord,
  ChatResponse,
} from "@/types/incident";
import {
  mockIncidentDecision,
  mockPoSuccess,
  mockSuppliers,
  mockInventory,
} from "@/data/mockData";

export default function DashboardPage() {
  // Tab Navigasi Utama: Mitigasi Cepat | Asisten Obrolan | Katalog Rekanan
  const [activeTab, setActiveTab] = useState<"pipeline" | "chat" | "suppliers">(
    "pipeline"
  );

  // Waktu Nyata Sistem
  const [currentTime, setCurrentTime] = useState<string>("");
  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleDateString("id-ID", {
          weekday: "long",
          day: "numeric",
          month: "short",
          year: "numeric",
        }) +
          ", " +
          now.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) +
          " WIB"
      );
    };
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  // =========================================================================
  // TAB 1: STATUS & LOGIKA PIPELINE MITIGASI
  // =========================================================================
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [pipelineMessage, setPipelineMessage] = useState<string>(
    "Sistem siaga. Klik 'Jalankan Analisis Mitigasi' untuk mencari pemasok cadangan."
  );
  const [decision, setDecision] = useState<IncidentDecisionResponse | null>(null);
  const [issuedPO, setIssuedPO] = useState<PurchaseOrderResponse | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [isPoModalOpen, setIsPoModalOpen] = useState(false);
  const [approvedQty, setApprovedQty] = useState(64);
  const [approverNotes, setApproverNotes] = useState(
    "Disetujui untuk dikirim dalam 2 tahap agar muat di ruang pendingin freezer SPPG."
  );

  // 5 Tahapan LangGraph yang Transparan
  const steps = [
    {
      step: 1,
      id: "deterministic_data_layer",
      title: "1. Hitung Defisit Stok",
      desc: "Menghitung matematis: Kebutuhan 144 kg, stok gudang 80 kg, defisit 64 kg.",
    },
    {
      step: 2,
      id: "compliance_filter",
      title: "2. Saring Regulasi Halal",
      desc: "Memilih hanya rekanan terverifikasi Halal BPJPH aktif (UU JPH 33/2014).",
    },
    {
      step: 3,
      id: "strategic_procurement_agent",
      title: "3. Taktik Split Delivery",
      desc: "Sisa freezer 20 kg, maka jadwal kirim dibagi 2 kali agar ayam tidak busuk.",
    },
    {
      step: 4,
      id: "feasibility_scoring_engine",
      title: "4. Uji Kelayakan 7 Parameter",
      desc: "Harga Rp 36.500/kg aman di bawah pagu SOP dan tiba tepat sebelum jam masak.",
    },
    {
      step: 5,
      id: "human_approval_gate",
      title: "5. Otorisasi Kepala SPPG",
      desc: "Menahan eksekusi di checkpoint hingga Kepala SPPG menyetujui surat pesanan.",
    },
  ];

  // Eksekusi Simulasi Pipeline (dengan Fallback Cepat)
  const handleStartSimulation = async () => {
    setIsSimulating(true);
    setDecision(null);
    setIssuedPO(null);
    setCompletedSteps([]);
    setActiveStep(1);
    setStreamLogs([]);
    setPipelineMessage("Menghubungkan ke mesin intelijen rantai pasok SPPG...");

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
        const payload = JSON.parse(e.data) as NonNullable<PipelineStreamEvent["data"]>;
        if (payload?.node === "deterministic_data_layer") setActiveStep(1);
        if (payload?.node === "compliance_filter") setActiveStep(2);
        if (payload?.node === "strategic_procurement_agent") setActiveStep(3);
        if (payload?.node === "feasibility_scoring_engine") setActiveStep(4);

        if (payload?.message) {
          setPipelineMessage(payload.message);
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString("id-ID")}] ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("node_completed", (e) => {
        const payload = JSON.parse(e.data) as NonNullable<PipelineStreamEvent["data"]>;
        if (payload?.node === "deterministic_data_layer") setCompletedSteps((prev) => [...prev, 1]);
        if (payload?.node === "compliance_filter") setCompletedSteps((prev) => [...prev, 2]);
        if (payload?.node === "strategic_procurement_agent") setCompletedSteps((prev) => [...prev, 3]);
        if (payload?.node === "feasibility_scoring_engine") setCompletedSteps((prev) => [...prev, 4]);

        if (payload?.message) {
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString("id-ID")}] Selesai: ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("workflow_waiting_approval", async (e) => {
        const payload = JSON.parse(e.data) as NonNullable<PipelineStreamEvent["data"]>;
        setActiveStep(5);
        setPipelineMessage(
          payload?.message || "Analisis tuntas! Menunggu otorisasi persetujuan Kepala SPPG."
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
        setDecision(mockIncidentDecision);
        setCompletedSteps([1, 2, 3, 4]);
        setActiveStep(5);
        setPipelineMessage("Analisis selesai. Rekomendasi mitigasi siap dievaluasi Kepala SPPG.");
      };
    } catch {
      setIsSimulating(false);
      setDecision(mockIncidentDecision);
      setCompletedSteps([1, 2, 3, 4]);
      setActiveStep(5);
      setPipelineMessage("Analisis selesai. Rekomendasi mitigasi siap dievaluasi Kepala SPPG.");
    }
  };

  // Otorisasi Persetujuan Human-in-the-Loop
  const handleApprovePO = async () => {
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
      setIsApprovalModalOpen(false);
      setIsPoModalOpen(true);
      setPipelineMessage(
        `Surat Pesanan Resmi Nomor ${poData.po_number} berhasil diterbitkan.`
      );
    } catch {
      setIssuedPO(mockPoSuccess);
      setCompletedSteps((prev) => [...prev, 5]);
      setIsApprovalModalOpen(false);
      setIsPoModalOpen(true);
    }
  };

  // =========================================================================
  // TAB 2: LIVE CONVERSATIONAL COPILOT (CHAT AGENT)
  // =========================================================================
  interface ChatMessageItem {
    id: string;
    sender: "user" | "agent";
    text: string;
    timestamp: string;
    previewData?: any;
    actionRequired?: string;
  }

  const [chatMessages, setChatMessages] = useState<ChatMessageItem[]>([
    {
      id: "msg-1",
      sender: "agent",
      text: "Selamat bertugas, Bapak/Ibu Kepala SPPG. Saya adalah asisten intelijen operasional rantai pasok SPPG Wilayah I. Saya siap membantu pengecekan stok gudang, mitigasi darurat kendala pasokan, serta pendaftaran rekanan supplier baru.",
      timestamp: "08:00 WIB",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatSending, setIsChatSending] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isChatSending]);

  const handleSendChatMessage = async (presetMessage?: string) => {
    const textToSend = presetMessage || chatInput.trim();
    if (!textToSend || isChatSending) return;

    const userMsg: ChatMessageItem = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB",
    };

    setChatMessages((prev) => [...prev, userMsg]);
    if (!presetMessage) setChatInput("");
    setIsChatSending(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "sppg-web-session-01",
          message: textToSend,
          user_role: "Kepala SPPG",
        }),
      });

      const data: ChatResponse = await res.json();
      const agentMsg: ChatMessageItem = {
        id: `msg-${Date.now() + 1}`,
        sender: "agent",
        text: data.reply,
        timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB",
        previewData: data.preview_data,
        actionRequired: data.action_required,
      };

      setChatMessages((prev) => [...prev, agentMsg]);
    } catch {
      const errorMsg: ChatMessageItem = {
        id: `msg-${Date.now() + 1}`,
        sender: "agent",
        text: "Mohon maaf, koneksi ke asisten sedang mengalami gangguan singkat. Silakan ulangi instruksi Anda.",
        timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB",
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsChatSending(false);
    }
  };

  // =========================================================================
  // TAB 3: KATALOG REKANAN & INVENTARIS
  // =========================================================================
  const [supplierFilter, setSupplierFilter] = useState<string>("ALL");
  const filteredSuppliers = mockSuppliers.filter((s) => {
    if (supplierFilter === "HALAL") return s.halal_certified;
    if (supplierFilter === "CHICKEN") return s.commodity === "DAGING_AYAM";
    if (supplierFilter === "OTHER") return s.commodity !== "DAGING_AYAM";
    return true;
  });

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-900 antialiased">
      {/* =====================================================================
          1. HEADER INSTITUSIONAL SPPG RESMI
      ===================================================================== */}
      <header className="border-b border-slate-200 bg-white shadow-xs">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-700 text-white shadow-xs">
              <ShieldCheck className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-slate-900">
                  ResilioAI
                </span>
                <span className="rounded bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-800 border border-blue-200">
                  SPPG Wilayah I
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Sistem Ketahanan Rantai Pasok Program Makan Bergizi Gratis 2026
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 font-mono text-slate-700">
              <Clock className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
              <span>{currentTime || "Memuat waktu sistem..."}</span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true"></span>
              <span className="font-semibold">Sistem Siaga (Bebas Rekayasa)</span>
            </div>
          </div>
        </div>

        {/* Tab Navigasi Menu */}
        <div className="mx-auto flex max-w-7xl overflow-x-auto px-4 sm:px-6">
          <nav className="flex space-x-1 border-t border-slate-100 pt-1" aria-label="Tab Menu Navigasi">
            <button
              type="button"
              onClick={() => setActiveTab("pipeline")}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-semibold transition ${
                activeTab === "pipeline"
                  ? "border-blue-700 text-blue-700"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <Activity className="h-4 w-4" aria-hidden="true" />
              <span>Mitigasi Darurat Pasokan</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-semibold transition ${
                activeTab === "chat"
                  ? "border-blue-700 text-blue-700"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <Bot className="h-4 w-4" aria-hidden="true" />
              <span>Asisten Percakapan Intelijen</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("suppliers")}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-semibold transition ${
                activeTab === "suppliers"
                  ? "border-blue-700 text-blue-700"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <Warehouse className="h-4 w-4" aria-hidden="true" />
              <span>Katalog Rekanan & Inventaris</span>
            </button>
          </nav>
        </div>
      </header>

      {/* =====================================================================
          2. KONTEN UTAMA BERDASARKAN TAB AKTIF
      ===================================================================== */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {/* ===================================================================
            TAB 1: PIPELINE MITIGASI DARURAT LAPANGAN
        =================================================================== */}
        {activeTab === "pipeline" && (
          <div className="space-y-6">
            {/* Banner Disrupsi Aktif */}
            <section className="rounded-xl border border-red-200 bg-red-50/70 p-5 shadow-xs">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3.5">
                  <div className="rounded-lg bg-red-600 p-2 text-white">
                    <AlertTriangle className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-red-100 px-2 py-0.5 text-[11px] font-bold text-red-800">
                        DISRUPSI AKTIF TIER-1
                      </span>
                      <span className="text-xs text-red-700">Laporan Lapangan 07:15 WIB</span>
                    </div>
                    <h2 className="mt-1 text-sm font-bold text-slate-900">
                      Gudang Utama Daging Ayam Terkendala Banjir Jalur Pantura
                    </h2>
                    <p className="mt-1 text-xs text-slate-600 leading-relaxed max-w-2xl">
                      Armada <strong>PT Unggas Sejahtera Nusantara</strong> terhambat. Target produksi dapur adalah{" "}
                      <strong>3.000 porsi</strong> (kebutuhan 144 kg), stok aman gudang tersisa 80 kg, defisit bahan{" "}
                      <strong>64 kg</strong>.
                    </p>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={handleStartSimulation}
                    disabled={isSimulating}
                    className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition active:scale-95 ${
                      isSimulating
                        ? "bg-slate-400 cursor-not-allowed"
                        : "bg-blue-700 hover:bg-blue-800"
                    }`}
                  >
                    {isSimulating ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
                        <span>Menganalisis Alur...</span>
                      </>
                    ) : (
                      <>
                        <Activity className="h-4 w-4" aria-hidden="true" />
                        <span>Jalankan Analisis Mitigasi</span>
                      </>
                    )}
                  </button>
                  {decision && !issuedPO && (
                    <button
                      type="button"
                      onClick={() => setIsApprovalModalOpen(true)}
                      className="rounded-lg bg-emerald-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-emerald-800 active:scale-95"
                    >
                      Buka Otorisasi Kepala SPPG
                    </button>
                  )}
                </div>
              </div>

              {/* Status Bar */}
              <div className="mt-4 flex items-center gap-2 border-t border-red-200/60 pt-3 text-xs text-slate-700">
                <span className="font-semibold text-slate-900">Status Alur:</span>
                <span>{pipelineMessage}</span>
              </div>
            </section>

            {/* 5 Tahap Kerja Agen LangGraph */}
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Visualisasi Alur Kerja Multi-Agen (5 Tahap Transparan)
              </h3>

              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {steps.map((s) => {
                  const isDone = completedSteps.includes(s.step);
                  const isRunning = activeStep === s.step;

                  return (
                    <div
                      key={s.step}
                      className={`flex flex-col justify-between rounded-xl border p-4 transition-all ${
                        isRunning
                          ? "border-blue-600 bg-blue-50/50 shadow-xs"
                          : isDone
                          ? "border-emerald-300 bg-emerald-50/20"
                          : "border-slate-200 bg-slate-50/40 opacity-70"
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold tracking-wider text-slate-400">
                            TAHAP 0{s.step}
                          </span>
                          {isDone ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                          ) : isRunning ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" aria-hidden="true" />
                          ) : (
                            <span className="h-2 w-2 rounded-full bg-slate-300" aria-hidden="true"></span>
                          )}
                        </div>
                        <h4 className="text-xs font-bold text-slate-900">{s.title}</h4>
                        <p className="mt-1.5 text-[11px] text-slate-600 leading-relaxed">
                          {s.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Log Jejak Aktivitas */}
              {streamLogs.length > 0 && (
                <div className="mt-4 rounded-lg bg-slate-900 p-3.5 font-mono text-[11px] text-slate-300 max-h-24 overflow-y-auto space-y-1">
                  <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">
                    Jejak Audit Real-Time (LangGraph Stream):
                  </div>
                  {streamLogs.slice(0, 3).map((log, idx) => (
                    <div key={idx} className="flex items-start gap-1.5">
                      <span className="text-blue-400">›</span>
                      <span>{log}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Rekomendasi Solusi & Rencana Pengiriman Bertahap */}
            {decision && (
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Rincian Pemasok Terpilih */}
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs lg:col-span-1 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Rekomendasi Rekanan Terverifikasi
                    </h3>
                    <span className="rounded bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-700 border border-emerald-200">
                      Skor {decision.recommended_procurement?.feasibility_score}/100
                    </span>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-slate-500 text-[11px]">Nama Perusahaan:</span>
                      <div className="font-bold text-slate-900 text-sm">
                        {decision.recommended_procurement?.supplier_name}
                      </div>
                      <span className="font-mono text-[11px] text-slate-500">
                        {decision.recommended_procurement?.supplier_id}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 border-t border-slate-100 pt-2">
                      <div>
                        <span className="text-slate-500 text-[11px]">Harga Penawaran:</span>
                        <div className="font-bold text-slate-900">
                          Rp {decision.recommended_procurement?.unit_price_idr.toLocaleString("id-ID")} / kg
                        </div>
                        <span className="text-[10px] text-emerald-600 font-semibold">
                          Di Bawah Pagu SOP (Rp 40.000)
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 text-[11px]">Total Estimasi Biaya:</span>
                        <div className="font-bold text-slate-900">
                          Rp {decision.recommended_procurement?.total_estimated_cost_idr.toLocaleString("id-ID")}
                        </div>
                        <span className="text-[10px] text-slate-500">Untuk 64 kg bahan</span>
                      </div>
                    </div>

                    <div className="border-t border-slate-100 pt-2">
                      <span className="text-slate-500 text-[11px]">Sertifikasi Halal (UU JPH 33/2014):</span>
                      <div className="flex items-center gap-1.5 font-semibold text-emerald-700 mt-0.5">
                        <Check className="h-4 w-4" aria-hidden="true" />
                        <span>Terverifikasi Halal Aktif</span>
                      </div>
                    </div>
                  </div>

                  {!issuedPO ? (
                    <button
                      type="button"
                      onClick={() => setIsApprovalModalOpen(true)}
                      className="w-full rounded-lg bg-blue-700 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-blue-800 active:scale-95"
                    >
                      Buka Otorisasi Kepala SPPG
                    </button>
                  ) : (
                    <div className="rounded-lg bg-emerald-50 p-3 text-xs text-emerald-800 border border-emerald-200 font-semibold flex items-center justify-between">
                      <span>Surat Pesanan Resmi Aktif</span>
                      <span className="font-mono">{issuedPO.po_number}</span>
                    </div>
                  )}
                </section>

                {/* Rencana Pengiriman Bertahap (Split Delivery) */}
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Rencana Pengiriman Bertahap (Mitigasi Kapasitas Freezer)
                    </h3>
                    <span className="rounded bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700 border border-amber-200">
                      Kapasitas Freezer Tersisa: 20 kg
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">
                    {decision.recommended_procurement?.logistics_strategy.rationale}
                  </p>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 pt-2">
                    {decision.recommended_procurement?.logistics_strategy.batches.map((batch) => (
                      <div
                        key={batch.batch_no}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between font-bold text-slate-900">
                          <span className="rounded bg-blue-100 px-2 py-0.5 text-blue-800 font-mono">
                            BATCH #{batch.batch_no}
                          </span>
                          <span className="text-sm font-extrabold text-blue-900">
                            {batch.qty_kg} kg
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Jadwal Estimasi Tiba:{" "}
                          <strong className="text-slate-800">
                            {new Date(batch.eta).toLocaleTimeString("id-ID", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}{" "}
                            WIB
                          </strong>
                        </div>
                        <p className="text-[11px] text-slate-600 leading-normal">
                          {batch.batch_no === 1
                            ? "Dimasukkan langsung ke ruang pendingin freezer sore ini sebagai buffer persiapan."
                            : "Tiba subuh dan langsung diproses kru dapur olah tanpa membebani kapasitas pendingin."}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {/* Tabel Monitoring Bahan Baku Dapur */}
            <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Status Ketersediaan Pangan Dapur Hari Ini
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Data inventaris gudang dan status rantai pasok SPPG Wilayah I
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Komoditas Bahan</th>
                      <th className="py-3 px-4 font-semibold">Kategori</th>
                      <th className="py-3 px-4 font-semibold">Stok Aktual</th>
                      <th className="py-3 px-4 font-semibold">Kebutuhan Produksi</th>
                      <th className="py-3 px-4 font-semibold">Status Pasokan</th>
                      <th className="py-3 px-4 font-semibold text-right">Tindakan</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr className={decision && !issuedPO ? "bg-amber-50/40" : ""}>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        Daging Ayam Broiler Segar
                        <div className="text-[11px] font-mono font-normal text-slate-400">ITEM-AYAM-01</div>
                      </td>
                      <td className="py-3 px-4">Lauk Utama (Protein)</td>
                      <td className="py-3 px-4 font-mono font-semibold">80.0 kg</td>
                      <td className="py-3 px-4 font-mono font-semibold">144.0 kg (Defisit 64 kg)</td>
                      <td className="py-3 px-4">
                        {issuedPO ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700 border border-emerald-200">
                            <Check className="h-3 w-3" aria-hidden="true" />
                            PO Terbit (Siap Kirim)
                          </span>
                        ) : decision ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-800 border border-amber-200">
                            Menunggu Otorisasi
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-bold text-red-700 border border-red-200">
                            Pengiriman Terhambat
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {decision && !issuedPO ? (
                          <button
                            type="button"
                            onClick={() => setIsApprovalModalOpen(true)}
                            className="rounded-md bg-blue-700 px-3 py-1 font-semibold text-white hover:bg-blue-800"
                          >
                            Setujui
                          </button>
                        ) : (
                          <span className="text-slate-400 font-mono">-</span>
                        )}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        Beras Putih Ramos Premium
                        <div className="text-[11px] font-mono font-normal text-slate-400">ITEM-BERAS-01</div>
                      </td>
                      <td className="py-3 px-4">Makanan Pokok</td>
                      <td className="py-3 px-4 font-mono font-semibold">520.0 kg</td>
                      <td className="py-3 px-4 font-mono">450.0 kg (Surplus 70 kg)</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700">
                          Aman Terpenuhi
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">-</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        Telur Ayam Negeri Grade A
                        <div className="text-[11px] font-mono font-normal text-slate-400">ITEM-TELUR-01</div>
                      </td>
                      <td className="py-3 px-4">Lauk Tambahan</td>
                      <td className="py-3 px-4 font-mono font-semibold">135.0 kg</td>
                      <td className="py-3 px-4 font-mono">120.0 kg (Surplus 15 kg)</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700">
                          Aman Terpenuhi
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">-</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        Sayur Wortel & Bayam Segar
                        <div className="text-[11px] font-mono font-normal text-slate-400">ITEM-WORTEL-01</div>
                      </td>
                      <td className="py-3 px-4">Sayuran Sehat</td>
                      <td className="py-3 px-4 font-mono font-semibold">90.0 kg</td>
                      <td className="py-3 px-4 font-mono">85.0 kg (Surplus 5 kg)</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700">
                          Tiba Besok Jam 04.00
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">-</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* ===================================================================
            TAB 2: ASISTEN PERCAKAPAN INTELIJEN RESILIOAI
        =================================================================== */}
        {activeTab === "chat" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
            {/* Panel Kiri: Panduan & Pintasan Instruksi */}
            <div className="space-y-4 lg:col-span-1">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
                <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
                  <Bot className="h-4 w-4 text-blue-700" aria-hidden="true" />
                  <span className="text-xs font-bold text-slate-900">Pintasan Instruksi SPPG</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Pilih skenario operasional di bawah untuk mengirim instruksi otomatis ke mesin asisten:
                </p>

                <div className="space-y-2">
                  <button
                    type="button"
                    onClick={() => handleSendChatMessage("Katalog rekanan supplier kita saat ini ada apa saja ya?")}
                    className="w-full text-left rounded-lg border border-slate-200 p-2.5 text-xs hover:border-blue-600 hover:bg-blue-50/30 transition"
                  >
                    <div className="font-semibold text-slate-900">Katalog Rekanan Aktif</div>
                    <div className="text-[11px] text-slate-500">Cek daftar rekanan dan status Halal</div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSendChatMessage("Cek stok gudang dan sisa ruang pendingin freezer saat ini")}
                    className="w-full text-left rounded-lg border border-slate-200 p-2.5 text-xs hover:border-blue-600 hover:bg-blue-50/30 transition"
                  >
                    <div className="font-semibold text-slate-900">Cek Inventaris & Freezer</div>
                    <div className="text-[11px] text-slate-500">Pantau sisa kapasitas ruang dingin</div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleSendChatMessage(
                        "Daftarkan supplier baru CV Barokah Tahu, komoditas tahu, harga Rp 18.000, kapasitas 200 kg, halal ID3211"
                      )
                    }
                    className="w-full text-left rounded-lg border border-slate-200 p-2.5 text-xs hover:border-blue-600 hover:bg-blue-50/30 transition"
                  >
                    <div className="font-semibold text-slate-900">Daftarkan Rekanan Tahu Baru</div>
                    <div className="text-[11px] text-slate-500">Simulasi pendaftaran bertahap (HITL)</div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      handleSendChatMessage(
                        "Armada supplier ayam utama kita PT Unggas Sejahtera mogok karena banjir, tolong mitigasi daruratnya!"
                      )
                    }
                    className="w-full text-left rounded-lg border border-slate-200 p-2.5 text-xs hover:border-blue-600 hover:bg-blue-50/30 transition"
                  >
                    <div className="font-semibold text-slate-900">Lapor Insiden Disrupsi</div>
                    <div className="text-[11px] text-slate-500">Kalkulasi defisit dan rekomendasi cadangan</div>
                  </button>
                </div>
              </div>
            </div>

            {/* Panel Kanan: Kotak Percakapan Asisten */}
            <div className="flex flex-col rounded-xl border border-slate-200 bg-white shadow-xs lg:col-span-3 h-[620px]">
              {/* Header Chat */}
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-slate-50/50">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-700 text-white">
                    <Bot className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">ResilioAI Conversational Agent</h3>
                    <p className="text-[11px] text-slate-500">
                      Terhubung ke API Backend Resmi (Hybrid LangGraph & Deterministic Engine)
                    </p>
                  </div>
                </div>
                <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                  Online
                </span>
              </div>

              {/* Area Pesan Chat */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/30">
                {chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${
                      msg.sender === "user" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        msg.sender === "user"
                          ? "bg-slate-900 text-white"
                          : "bg-blue-700 text-white shadow-xs"
                      }`}
                    >
                      {msg.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>

                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-slate-900 text-white shadow-xs"
                          : "bg-white border border-slate-200 text-slate-800 shadow-xs"
                      }`}
                    >
                      <div className="whitespace-pre-line">{msg.text}</div>

                      {/* Kartu Aksi Konfirmasi (Jika Memerlukan Otorisasi Pimpinan) */}
                      {msg.actionRequired === "APPROVAL_PENDING" && (
                        <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleSendChatMessage("Setuju, tolong daftarkan rekanan ini")}
                            className="rounded-lg bg-emerald-700 px-3 py-1.5 text-[11px] font-bold text-white hover:bg-emerald-800 transition"
                          >
                            Setujui & Simpan
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSendChatMessage("Batal, jangan disimpan")}
                            className="rounded-lg border border-slate-300 px-3 py-1.5 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 transition"
                          >
                            Batalkan
                          </button>
                        </div>
                      )}

                      <div
                        className={`mt-1.5 text-[10px] ${
                          msg.sender === "user" ? "text-slate-400 text-right" : "text-slate-400"
                        }`}
                      >
                        {msg.timestamp}
                      </div>
                    </div>
                  </div>
                ))}

                {isChatSending && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-blue-700" />
                    <span>ResilioAI Agent sedang menganalisis data operasional...</span>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Input Chat Box */}
              <div className="border-t border-slate-200 p-3 bg-white">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendChatMessage();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ketik instruksi untuk Kepala SPPG (misal: 'Daftarkan supplier baru...', 'Cek sisa freezer')..."
                    className="flex-1 rounded-lg border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:outline-hidden"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isChatSending}
                    className="flex items-center gap-1.5 rounded-lg bg-blue-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-blue-800 disabled:bg-slate-300 disabled:cursor-not-allowed"
                  >
                    <span>Kirim</span>
                    <Send className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 3: KATALOG REKANAN SUPPLIER & INVENTARIS MASTER
        =================================================================== */}
        {activeTab === "suppliers" && (
          <div className="space-y-6">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Master Katalog Rekanan Supplier Terdaftar (SPPG Wilayah I)
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Mematuhi standar verifikasi sertifikasi Halal UU JPH No. 33/2014 & Pagu Anggaran SOP BGN
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Filter:</span>
                  <button
                    type="button"
                    onClick={() => setSupplierFilter("ALL")}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      supplierFilter === "ALL"
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Semua ({mockSuppliers.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setSupplierFilter("HALAL")}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      supplierFilter === "HALAL"
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Halal Terverifikasi
                  </button>
                  <button
                    type="button"
                    onClick={() => setSupplierFilter("CHICKEN")}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      supplierFilter === "CHICKEN"
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Daging Ayam
                  </button>
                </div>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Nama Rekanan / ID</th>
                      <th className="py-3 px-4 font-semibold">Komoditas</th>
                      <th className="py-3 px-4 font-semibold">Sertifikasi Halal</th>
                      <th className="py-3 px-4 font-semibold">Harga Penawaran</th>
                      <th className="py-3 px-4 font-semibold">Kapasitas Harian</th>
                      <th className="py-3 px-4 font-semibold">Estimasi Tiba & Jarak</th>
                      <th className="py-3 px-4 font-semibold text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {filteredSuppliers.map((s) => (
                      <tr key={s.supplier_id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900">{s.supplier_name}</div>
                          <div className="font-mono text-[11px] text-slate-400">{s.supplier_id}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-semibold text-slate-800">{s.commodity}</span>
                          <div className="text-[11px] text-slate-400">{s.category}</div>
                        </td>
                        <td className="py-3 px-4">
                          {s.halal_certified ? (
                            <div>
                              <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-800 border border-emerald-200">
                                <Check className="h-3 w-3" aria-hidden="true" />
                                Terverifikasi
                              </span>
                              {s.halal_cert_number && (
                                <div className="font-mono text-[10px] text-slate-400 mt-0.5">
                                  {s.halal_cert_number}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-600">
                              Non-Halal (Non-Prioritas)
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-slate-900">
                          Rp {s.unit_price_idr.toLocaleString("id-ID")} / kg
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold">
                          {s.daily_capacity_kg} kg/hari
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          {s.lead_time_hours} jam ({s.distance_km} km)
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700 border border-emerald-200">
                            Aktif
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* =====================================================================
          3. MODAL PERSETUJUAN KEPALA SPPG (HUMAN-IN-THE-LOOP)
      ===================================================================== */}
      {isApprovalModalOpen && decision && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="approval-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-fadeIn"
        >
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 id="approval-modal-title" className="font-bold text-slate-900 text-sm">
                  Otorisasi Pengadaan Darurat (Kepala SPPG)
                </h3>
                <p className="text-[11px] text-slate-500">
                  Tiket Insiden: <span className="font-mono">{decision.incident_id}</span>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsApprovalModalOpen(false)}
                className="rounded-md p-1 text-slate-400 hover:text-slate-600"
                aria-label="Tutup jendela otorisasi"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Komoditas yang Dibeli:</span>
                  <span className="font-bold text-slate-900">Daging Ayam Broiler Segar</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Rekanan Pengganti:</span>
                  <span className="font-bold text-slate-900">
                    {decision.recommended_procurement?.supplier_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Harga Penawaran:</span>
                  <span className="font-mono font-bold text-slate-900">
                    Rp {decision.recommended_procurement?.unit_price_idr.toLocaleString("id-ID")} / kg
                  </span>
                </div>
                <div className="flex justify-between border-t border-slate-200/60 pt-2">
                  <span className="text-slate-500">Total Kuantitas Disetujui:</span>
                  <span className="font-mono font-bold text-blue-900">{approvedQty} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Total Estimasi Anggaran:</span>
                  <span className="font-mono font-bold text-emerald-800">
                    Rp {(approvedQty * (decision.recommended_procurement?.unit_price_idr || 0)).toLocaleString("id-ID")}
                  </span>
                </div>
              </div>

              <div>
                <label htmlFor="approver-notes" className="block text-[11px] font-bold text-slate-700 mb-1">
                  Catatan Otorisasi Pimpinan SPPG:
                </label>
                <textarea
                  id="approver-notes"
                  rows={2}
                  value={approverNotes}
                  onChange={(e) => setApproverNotes(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-blue-600 focus:outline-hidden"
                />
              </div>

              <div className="rounded-lg bg-blue-50/70 p-3 text-[11px] text-blue-800 border border-blue-200 leading-relaxed">
                Taktik pengiriman bertahap (20 kg sore ini ke freezer, 44 kg subuh langsung olah) akan otomatis
                diterbitkan ke dalam Purchase Order resmi.
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-2 border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() => setIsApprovalModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
              >
                Batal
              </button>
              <button
                type="button"
                onClick={handleApprovePO}
                className="rounded-lg bg-emerald-700 px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-emerald-800 active:scale-95"
              >
                Setujui & Terbitkan Surat Pesanan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          4. MODAL SURAT PESANAN RESMI (PO ISSUED)
      ===================================================================== */}
      {isPoModalOpen && issuedPO && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="po-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-fadeIn"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-2xl border border-slate-200">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
              <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
            </div>
            <h3 id="po-modal-title" className="text-base font-bold text-slate-900">
              Surat Pesanan Resmi Berhasil Diterbitkan
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Rekanan pemasok telah menerima notifikasi dan siap mengantar bahan sesuai jadwal bertahap.
            </p>

            <div className="my-5 space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-left text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Nomor Dokumen PO:</span>
                <span className="font-mono font-bold text-blue-900">{issuedPO.po_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Pemasok Terpilih:</span>
                <span className="font-bold text-slate-900">
                  {issuedPO.supplier_name || "PT Berkah Unggas Jaya"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Kuantitas Pasokan:</span>
                <span className="font-mono font-bold text-slate-900">
                  {issuedPO.approved_qty_kg || 64.0} kg
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Otorisator:</span>
                <span className="font-semibold text-slate-800">
                  {issuedPO.approver_name || "Budi Santoso, S.T. (Kepala SPPG)"}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsPoModalOpen(false)}
              className="w-full rounded-lg bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition"
            >
              Tutup & Kembali ke Dasbor
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
