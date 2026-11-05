"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  Truck,
  Cpu,
  RefreshCw,
  Layers,
  ArrowRight,
  UserCheck,
  Building2,
  X,
  Package,
  AlertCircle,
  TrendingDown,
  Warehouse,
} from "lucide-react";
import {
  IncidentDecisionResponse,
  PipelineStreamEvent,
  PurchaseOrderResponse,
} from "@/types/incident";

export default function DashboardPage() {
  // State manajemen simulasi & pipeline
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [currentStepMessage, setCurrentStepMessage] = useState<string>(
    "Sistem siaga. Klik 'Mulai Simulasi Insiden' untuk menguji mitigasi otonom."
  );

  // State data keputusan & PO
  const [decision, setDecision] = useState<IncidentDecisionResponse | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [approvedQty, setApprovedQty] = useState(64);
  const [approverNotes, setApproverNotes] = useState(
    "Disetujui skema pengiriman bertahap (split delivery) sesuai rekomendasi sistem."
  );
  const [issuedPO, setIssuedPO] = useState<PurchaseOrderResponse | null>(null);
  const [isPoModalOpen, setIsPoModalOpen] = useState(false);

  // Daftar tahapan LangGraph pipeline
  const pipelineNodes = [
    {
      id: "deterministic_data_layer",
      name: "1. Data Layer & Defisit",
      type: "DETERMINISTIC",
      icon: Database,
      desc: "Kueri stok aktual & defisit matematika",
    },
    {
      id: "compliance_filter",
      name: "2. Filter Kepatuhan",
      type: "DETERMINISTIC",
      icon: ShieldCheck,
      desc: "Syarat mutlak Halal & radius aman",
    },
    {
      id: "strategic_procurement_agent",
      name: "3. Strategic Agent",
      type: "COGNITIVE LLM",
      icon: Cpu,
      desc: "Penalaran alokasi & Split Delivery",
    },
    {
      id: "feasibility_scoring_engine",
      name: "4. Feasibility Engine",
      type: "DETERMINISTIC",
      icon: Layers,
      desc: "Skoring matematis 7 parameter",
    },
    {
      id: "human_approval_gate",
      name: "5. Human Approval",
      type: "HITL GATE",
      icon: UserCheck,
      desc: "LangGraph interrupt otorisasi",
    },
  ];

  // Fungsi untuk memicu simulasi aliran SSE
  const handleStartSimulation = async () => {
    setIsSimulating(true);
    setDecision(null);
    setIssuedPO(null);
    setCompletedNodes([]);
    setActiveNode("deterministic_data_layer");
    setStreamLogs([]);
    setCurrentStepMessage("Memulai koneksi Server-Sent Events (SSE) ke Hybrid Engine...");

    try {
      // Panggil mock trigger API
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

      // Buka koneksi EventSource (SSE)
      const eventSource = new EventSource(streamUrl);

      eventSource.addEventListener("node_started", (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        if (payload.node) {
          setActiveNode(payload.node);
        }
        if (payload.message) {
          setCurrentStepMessage(payload.message);
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] MEMULAI: ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("node_completed", (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        if (payload.node) {
          setCompletedNodes((prev) => [...prev, payload.node!]);
        }
        if (payload.message) {
          setStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] SELESAI: ${payload.message}`,
            ...prev,
          ]);
        }
      });

      eventSource.addEventListener("workflow_waiting_approval", async (e) => {
        const payload: PipelineStreamEvent["data"] = JSON.parse(e.data);
        setActiveNode("human_approval_gate");
        setCurrentStepMessage(
          payload.message || "Pipeline ditahan di checkpoint. Menunggu persetujuan Kepala SPPG."
        );
        setStreamLogs((prev) => [
          `[${new Date().toLocaleTimeString()}] CHECKPOINT: Menunggu otorisasi manusia`,
          ...prev,
        ]);
        eventSource.close();
        setIsSimulating(false);

        // Ambil data keputusan lengkap
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
      setCurrentStepMessage("Terjadi kendala koneksi ke stream pipeline.");
    }
  };

  // Eksekusi Otorisasi Persetujuan (Approve)
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
      setCompletedNodes((prev) => [...prev, "human_approval_gate"]);
      setActiveNode(null);
      setIsApprovalModalOpen(false);
      setIsPoModalOpen(true);
      setCurrentStepMessage(
        `Purchase Order resmi berhasil diterbitkan: ${poData.po_number}. Alur selesai.`
      );
    } catch {
      alert("Gagal memproses otorisasi");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* 1. TOP NAVBAR / HEADER (SPPG THEME) */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-700 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">
                  Resilio<span className="text-blue-700">AI</span>
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-800 border border-blue-200">
                  GTNIC 2026
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Satuan Pelayanan Pemenuhan Gizi (SPPG) • Wilayah Operasional I
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Sistem Aktif • Mode Hibrida (Deterministic + LangGraph)
            </div>

            <button
              onClick={handleStartSimulation}
              disabled={isSimulating}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 shadow-sm ${
                isSimulating
                  ? "bg-blue-400 text-white cursor-not-allowed"
                  : "bg-blue-700 hover:bg-blue-800 text-white shadow-blue-600/20 active:scale-95"
              }`}
            >
              <RefreshCw
                className={`w-4 h-4 ${isSimulating ? "animate-spin" : ""}`}
              />
              {isSimulating ? "Memproses Alur Agen..." : "Simulasi Insiden Rantai Pasok"}
            </button>
          </div>
        </div>
      </header>

      {/* 2. MAIN CONTAINER */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* KPI METRIC STRIP (SHADCN DASHBOARD STYLE) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold uppercase tracking-wider">
                Target Menu Harian
              </span>
              <Package className="w-4 h-4 text-blue-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">3.000</span>
              <span className="text-sm font-medium text-slate-500">Porsi</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Menu: Daging Ayam Broiler Segar
            </p>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold uppercase tracking-wider">
                Stok Gudang Fisik
              </span>
              <Warehouse className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900">80.0</span>
              <span className="text-sm font-medium text-slate-500">kg</span>
            </div>
            <p className="mt-1 text-xs text-emerald-600 font-medium">
              Kebutuhan Produksi: 144.0 kg
            </p>
          </div>

          <div className="p-5 bg-white rounded-xl border border-red-200 bg-red-50/20 shadow-2xs">
            <div className="flex items-center justify-between text-red-600">
              <span className="text-xs font-semibold uppercase tracking-wider">
                Defisit Kuantitas
              </span>
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-red-600">64.0</span>
              <span className="text-sm font-medium text-red-500">kg</span>
            </div>
            <p className="mt-1 text-xs text-red-600 font-medium flex items-center gap-1">
              <TrendingDown className="w-3.5 h-3.5" /> Supplier Utama Terhambat Banjir
            </p>
          </div>

          <div className="p-5 bg-white rounded-xl border border-amber-200 bg-amber-50/20 shadow-2xs">
            <div className="flex items-center justify-between text-amber-700">
              <span className="text-xs font-semibold uppercase tracking-wider">
                Sisa Ruang Freezer
              </span>
              <AlertCircle className="w-4 h-4" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-700">20.0</span>
              <span className="text-sm font-medium text-amber-600">kg</span>
            </div>
            <p className="mt-1 text-xs text-amber-700 font-medium">
              Restriksi Fisik Gudang Dingin
            </p>
          </div>
        </div>

        {/* 3. REAL-TIME PIPELINE VISUALIZER (NILAI JUAL UTAMA) */}
        <section className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-700" />
                LangGraph Hybrid Cyclic Pipeline Visualizer
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Pemantauan real-time status eksekusi tiap node agen berbasis Server-Sent Events (SSE)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5 ${
                  isSimulating
                    ? "bg-blue-100 text-blue-800 border border-blue-200 animate-pulse"
                    : activeNode === "human_approval_gate"
                    ? "bg-amber-100 text-amber-800 border border-amber-200"
                    : completedNodes.length === 5
                    ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isSimulating
                      ? "bg-blue-600"
                      : activeNode === "human_approval_gate"
                      ? "bg-amber-600"
                      : completedNodes.length === 5
                      ? "bg-emerald-600"
                      : "bg-slate-400"
                  }`}
                ></span>
                {isSimulating
                  ? "Agent Sedang Bekerja"
                  : activeNode === "human_approval_gate"
                  ? "Menunggu Otorisasi (HITL)"
                  : completedNodes.length === 5
                  ? "Siklus Mitigasi Selesai"
                  : "Status: Standby"}
              </span>
            </div>
          </div>

          {/* DIAGRAM ALUR NODE */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-5 gap-3">
            {pipelineNodes.map((node, index) => {
              const isCompleted = completedNodes.includes(node.id);
              const isActive = activeNode === node.id;
              const Icon = node.icon;

              return (
                <div
                  key={node.id}
                  className={`relative p-4 rounded-xl border transition-all duration-300 ${
                    isActive
                      ? "bg-blue-50/80 border-blue-500 shadow-md shadow-blue-500/10 ring-2 ring-blue-500/20"
                      : isCompleted
                      ? "bg-emerald-50/60 border-emerald-300"
                      : "bg-slate-50 border-slate-200 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded tracking-wider uppercase ${
                        node.type === "DETERMINISTIC"
                          ? "bg-slate-200 text-slate-700"
                          : node.type === "COGNITIVE LLM"
                          ? "bg-indigo-100 text-indigo-800 font-semibold"
                          : "bg-amber-200 text-amber-900"
                      }`}
                    >
                      {node.type}
                    </span>

                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    ) : isActive ? (
                      <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                    ) : (
                      <span className="text-xs text-slate-400 font-mono">
                        0{index + 1}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Icon
                      className={`w-4 h-4 ${
                        isActive
                          ? "text-blue-700"
                          : isCompleted
                          ? "text-emerald-700"
                          : "text-slate-500"
                      }`}
                    />
                    <h4 className="text-xs font-bold text-slate-900 truncate">
                      {node.name}
                    </h4>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                    {node.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* STATUS TICKER / LOG BANNER */}
          <div className="mt-4 p-4 rounded-lg bg-slate-900 text-slate-200 font-mono text-xs space-y-2">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2 truncate">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping"></span>
                <span className="text-slate-400">Stream Status:</span>
                <span className="text-blue-300 font-sans font-medium">
                  {currentStepMessage}
                </span>
              </div>
              {decision && !issuedPO && (
                <button
                  onClick={() => setIsApprovalModalOpen(true)}
                  className="shrink-0 ml-4 px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-sans font-bold rounded text-xs transition"
                >
                  Buka Otorisasi Kepala SPPG
                </button>
              )}
            </div>

            {streamLogs.length > 0 && (
              <div className="max-h-24 overflow-y-auto space-y-1 text-[11px] text-slate-400 pt-1">
                {streamLogs.slice(0, 4).map((log, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="text-blue-400">›</span>
                    <span>{log}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* 4. DUA KOLOM KONTEN: MATRIKS KELAYAKAN & STRATEGI PENGADAAN */}
        {decision && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fadeIn">
            {/* KOLOM KIRI: MATRIKS SKOR 7 PARAMETER & AUDIT TRAIL */}
            <div className="lg:col-span-5 space-y-6">
              {/* KARTU MATRIKS SKORING */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Layers className="w-4 h-4 text-blue-700" />
                      Matriks Skoring Kelayakan Deterministik
                    </h3>
                    <p className="text-xs text-slate-500">
                      Formula 7 parameter berbobot tanpa halusinasi
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-black text-blue-700 font-mono">
                      {decision.recommended_procurement?.feasibility_score}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      /100
                    </span>
                  </div>
                </div>

                <div className="mt-3">
                  <span className="inline-block text-xs font-semibold px-2.5 py-1 rounded-md bg-amber-100 text-amber-800 border border-amber-200">
                    {decision.recommended_procurement?.feasibility_status}
                  </span>
                  <p className="text-xs text-slate-600 mt-2">
                    Skor antara 60–79 mewajibkan klausul pengiriman terbagi (
                    <em>split delivery</em>) karena keterbatasan kapasitas penyimpanan dingin.
                  </p>
                </div>

                {/* BREAKDOWN BILAH PROGRES */}
                <div className="mt-5 space-y-3">
                  {decision.recommended_procurement?.scoring_breakdown && (
                    <>
                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span>1. Pemenuhan Kuota Defisit (25%)</span>
                          <span className="font-mono font-bold">100%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600 rounded-full w-full"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span>2. Lead Time vs Jam Masak (20%)</span>
                          <span className="font-mono font-bold">85%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600 rounded-full w-[85%]"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span>3. Kepatuhan Anggaran SOP (15%)</span>
                          <span className="font-mono font-bold">90%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-600 rounded-full w-[90%]"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span className="flex items-center gap-1 text-blue-900 font-bold">
                            <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                            4. Kepatuhan Sertifikat Halal (15%) - Gating
                          </span>
                          <span className="font-mono font-bold text-emerald-600">
                            100% (Lolos Mutlak)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-600 rounded-full w-full"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-amber-800 mb-1">
                          <span>5. Kesesuaian Freezer Gudang (10%)</span>
                          <span className="font-mono font-bold text-amber-700">
                            40% (Restriksi)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full w-[40%]"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span>6. Kesiapan Olah Dapur (10%)</span>
                          <span className="font-mono font-bold">80%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600 rounded-full w-[80%]"></div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                          <span>7. Keamanan Rute Logistik (5%)</span>
                          <span className="font-mono font-bold">70%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600 rounded-full w-[70%]"></div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* AUDIT TRAIL LOG */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-blue-700" />
                  Jejak Audit Keputusan (Immutable Audit Trail)
                </h3>
                <div className="space-y-3">
                  {decision.audit_trail.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-bold text-blue-900">
                          {step.stage}
                        </span>
                        <span className="text-[10px] text-emerald-700 font-semibold px-1.5 py-0.5 rounded bg-emerald-100">
                          {step.status}
                        </span>
                      </div>
                      <p className="text-slate-600 text-[11px]">{step.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* KOLOM KANAN: REKOMENDASI SUPPLIER & STRATEGI SPLIT DELIVERY */}
            <div className="lg:col-span-7 space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6">
                <div className="flex items-start justify-between pb-5 border-b border-slate-100">
                  <div>
                    <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">
                      Rekomendasi Supplier Alternatif
                    </span>
                    <h3 className="text-xl font-bold text-slate-900 mt-1 flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-slate-700" />
                      {decision.recommended_procurement?.supplier_name}
                    </h3>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                      ID: {decision.recommended_procurement?.supplier_id} • Halal BPJPH Aktif
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Total Biaya Est.</span>
                    <div className="text-lg font-bold text-slate-900 font-mono">
                      Rp{" "}
                      {decision.recommended_procurement?.total_estimated_cost_idr.toLocaleString(
                        "id-ID"
                      )}
                    </div>
                    <span className="text-[11px] text-emerald-600 font-medium">
                      Rp 38.000/kg (Pagu SOP: Rp 40.000)
                    </span>
                  </div>
                </div>

                {/* MITIGASI SPLIT DELIVERY CARD */}
                <div className="mt-5 p-5 rounded-xl bg-blue-50/70 border border-blue-200">
                  <div className="flex items-center gap-2 text-blue-900 font-bold text-sm">
                    <Truck className="w-4 h-4 text-blue-700" />
                    Penalaran Logistik Agen: Pengiriman Bertahap (Split Delivery)
                  </div>
                  <p className="text-xs text-slate-700 mt-2 leading-relaxed">
                    {decision.recommended_procurement?.logistics_strategy.rationale}
                  </p>

                  {/* TIMELINE JADWAL PENGIRIMAN */}
                  <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {decision.recommended_procurement?.logistics_strategy.batches.map(
                      (batch) => (
                        <div
                          key={batch.batch_no}
                          className="p-3.5 rounded-lg bg-white border border-blue-200 shadow-2xs"
                        >
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-blue-950">
                              Batch {batch.batch_no}
                            </span>
                            <span className="font-bold text-blue-700 font-mono bg-blue-100 px-2 py-0.5 rounded">
                              {batch.qty_kg} kg
                            </span>
                          </div>
                          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-600">
                            <Clock className="w-3.5 h-3.5 text-slate-400" />
                            <span>
                              {batch.batch_no === 1
                                ? "H-1 Pukul 17:00 WIB (Freezer)"
                                : "Hari-H Pukul 05:00 WIB (Masak Subuh)"}
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>

                {/* TOMBOL AKSI HUMAN-IN-THE-LOOP */}
                <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-5 border-t border-slate-100">
                  <div className="text-xs text-slate-500 flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-amber-600" />
                    <span>
                      Otorisasi diwajibkan sebelum sistem menerbitkan Purchase Order.
                    </span>
                  </div>

                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <button
                      onClick={() => setIsApprovalModalOpen(true)}
                      className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-sm transition shadow-sm shadow-blue-600/20 active:scale-95 flex items-center justify-center gap-2"
                    >
                      <span>Tinjau & Otorisasi Pengadaan</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 5. MODAL HUMAN-IN-THE-LOOP (HITL GATE) */}
      {isApprovalModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 text-slate-900 font-bold text-base">
                <ShieldCheck className="w-5 h-5 text-blue-700" />
                Otorisasi Pengadaan Darurat Kepala SPPG
              </div>
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Tiket Insiden:</span>
                  <span className="font-mono font-bold">
                    {decision?.incident_id}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Kandidat Supplier:</span>
                  <span className="font-semibold text-slate-900">
                    {decision?.recommended_procurement?.supplier_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Skema Pengiriman:</span>
                  <span className="font-semibold text-blue-700">
                    Split Delivery (2 Batch)
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kuantitas Bahan yang Disetujui (kg)
                </label>
                <input
                  type="number"
                  value={approvedQty}
                  onChange={(e) => setApprovedQty(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Defisit aktual yang dihitung sistem: 64.0 kg
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Catatan Otorisasi Kepala SPPG
                </label>
                <textarea
                  value={approverNotes}
                  onChange={(e) => setApproverNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                ></textarea>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-800"
              >
                Batal
              </button>
              <button
                onClick={handleApprove}
                className="px-5 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-sm shadow-sm transition active:scale-95"
              >
                Setujui & Terbitkan Purchase Order
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. MODAL PURCHASE ORDER SUKSES */}
      {isPoModalOpen && issuedPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">
              Purchase Order Resmi Diterbitkan!
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Siklus mitigasi insiden telah terekam ke dalam tabel audit log permanen.
            </p>

            <div className="my-5 p-4 rounded-xl bg-slate-50 border border-slate-200 text-left space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Nomor PO:</span>
                <span className="font-mono font-bold text-blue-700">
                  {issuedPO.po_number}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Pejabat Pengesah:</span>
                <span className="font-semibold text-slate-800">
                  {issuedPO.approver_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Volume:</span>
                <span className="font-mono font-semibold">
                  {issuedPO.approved_qty_kg} kg
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Waktu Terbit:</span>
                <span className="font-mono text-slate-600">
                  {new Date(issuedPO.generated_at).toLocaleString("id-ID")}
                </span>
              </div>
            </div>

            <button
              onClick={() => setIsPoModalOpen(false)}
              className="w-full py-2.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-sm transition"
            >
              Tutup & Kembali ke Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
