"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  Database,
  FileText,
  Cpu,
  RefreshCw,
  Layers,
  ArrowRight,
  UserCheck,
  Building2,
  X,
  TrendingDown,
  TrendingUp,
  Warehouse,
  ChevronDown,
  Search,
  Bell,
  SlidersHorizontal,
  Plus,
  MoreVertical,
  Users,
  BarChart3,
  HelpCircle,
  Settings,
  FolderGit2,
  Check,
} from "lucide-react";
import {
  IncidentDecisionResponse,
  PipelineStreamEvent,
  PurchaseOrderResponse,
} from "@/types/incident";

export default function DashboardPage() {
  // Navigation & View States
  const [activeTab, setActiveTab] = useState<"visualizer" | "chart" | "matrix">(
    "visualizer"
  );
  const [tableFilter, setTableFilter] = useState<"all" | "mitigation" | "safe">(
    "all"
  );

  // Simulation & Pipeline States
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [currentStepMessage, setCurrentStepMessage] = useState<string>(
    "Sistem siaga. Klik '+ Simulasi Insiden' untuk menguji mitigasi otonom SPPG."
  );

  // Decision & Approval States
  const [decision, setDecision] = useState<IncidentDecisionResponse | null>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [approvedQty, setApprovedQty] = useState(64);
  const [approverNotes, setApproverNotes] = useState(
    "Disetujui mitigasi Split Delivery sesuai rekomendasi sistem untuk SPPG Wilayah I."
  );
  const [issuedPO, setIssuedPO] = useState<PurchaseOrderResponse | null>(null);
  const [isPoModalOpen, setIsPoModalOpen] = useState(false);

  // Pipeline Nodes Configuration
  const pipelineNodes = [
    {
      id: "deterministic_data_layer",
      name: "1. Data Layer & Defisit",
      type: "DETERMINISTIC",
      icon: Database,
      desc: "Kueri stok & formula defisit",
    },
    {
      id: "compliance_filter",
      name: "2. Filter Kepatuhan",
      type: "DETERMINISTIC",
      icon: ShieldCheck,
      desc: "Syarat mutlak Halal BPJPH & radius",
    },
    {
      id: "strategic_procurement_agent",
      name: "3. Strategic Agent",
      type: "COGNITIVE LLM",
      icon: Cpu,
      desc: "Alokasi vendor & Split Delivery",
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
      desc: "LangGraph checkpoint persetujuan",
    },
  ];

  // Table Data Skenario Pangan SPPG
  const inventoryTableItems = [
    {
      id: "ITEM-AYAM-01",
      name: "Daging Ayam Broiler Segar",
      category: "Protein Hewani",
      status: decision ? "Waiting Approval" : "Needs Mitigation",
      targetQty: "144.0 kg",
      stockActual: "80.0 kg",
      deficit: "64.0 kg",
      score: decision?.recommended_procurement?.feasibility_score
        ? `${decision.recommended_procurement.feasibility_score}/100`
        : "78.5/100",
      reviewer: "Budi Santoso, S.T.",
      urgent: true,
    },
    {
      id: "ITEM-BERAS-01",
      name: "Beras Premium Ramos (Cianjur)",
      category: "Karbohidrat Utama",
      status: "Done",
      targetQty: "450.0 kg",
      stockActual: "520.0 kg",
      deficit: "0.0 kg (Aman)",
      score: "96.0/100",
      reviewer: "Tim Gudang SPPG",
      urgent: false,
    },
    {
      id: "ITEM-TELUR-02",
      name: "Telur Ayam Negeri Grade A",
      category: "Protein Tambahan",
      status: "Done",
      targetQty: "120.0 kg",
      stockActual: "135.0 kg",
      deficit: "0.0 kg (Aman)",
      score: "92.0/100",
      reviewer: "Auditor Halal SPPG",
      urgent: false,
    },
    {
      id: "ITEM-SAYUR-05",
      name: "Sayur Bayam Hijau Segar",
      category: "Sayur & Serat",
      status: "Done",
      targetQty: "85.0 kg",
      stockActual: "90.0 kg",
      deficit: "0.0 kg (Aman)",
      score: "89.0/100",
      reviewer: "Kru Dapur Olah",
      urgent: false,
    },
  ];

  // Handler Trigger Simulasi Alur SSE
  const handleStartSimulation = async () => {
    setIsSimulating(true);
    setDecision(null);
    setIssuedPO(null);
    setCompletedNodes([]);
    setActiveNode("deterministic_data_layer");
    setStreamLogs([]);
    setCurrentStepMessage(
      "Membuka koneksi Server-Sent Events (SSE) ke Hybrid Agent Engine..."
    );

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
        if (payload.node) setActiveNode(payload.node);
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
          payload.message ||
            "Pipeline ditahan di Checkpoint LangGraph. Menunggu otorisasi Kepala SPPG."
        );
        setStreamLogs((prev) => [
          `[${new Date().toLocaleTimeString()}] CHECKPOINT: Menunggu otorisasi Kepala SPPG`,
          ...prev,
        ]);
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
      setCurrentStepMessage("Kendala koneksi ke server pipeline.");
    }
  };

  // Handler Otorisasi Persetujuan Kepala SPPG
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
        `PO resmi ${poData.po_number} berhasil diterbitkan dan dicatat ke audit log permanen.`
      );
    } catch {
      alert("Gagal memproses otorisasi");
    }
  };

  const filteredItems = inventoryTableItems.filter((item) => {
    if (tableFilter === "mitigation") return item.urgent;
    if (tableFilter === "safe") return !item.urgent;
    return true;
  });

  return (
    <div className="flex min-h-screen bg-slate-50/60 font-sans text-slate-900 antialiased">
      {/* =========================================================================
          1. FORMAL SIDEBAR (MENIRU PERSIS STRUKTUR SHADCN DASHBOARD-01)
      ========================================================================= */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-slate-200 bg-white">
        {/* Organization / Header */}
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 text-white shadow-xs">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="font-bold text-sm leading-tight text-slate-900 flex items-center gap-1.5">
                Resilio<span className="text-blue-700">AI</span>
              </div>
              <p className="text-[11px] font-medium text-slate-500">
                SPPG Wilayah Jawa Barat
              </p>
            </div>
          </div>
          <button className="text-slate-400 hover:text-slate-600">
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>

        {/* Primary Action Button (+ Quick Create) */}
        <div className="p-4">
          <button
            onClick={handleStartSimulation}
            disabled={isSimulating}
            className={`w-full flex items-center justify-center gap-2 rounded-lg py-2.5 px-3 text-xs font-semibold text-white shadow-xs transition-all active:scale-[0.98] ${
              isSimulating
                ? "bg-blue-400 cursor-not-allowed"
                : "bg-blue-700 hover:bg-blue-800 shadow-blue-700/20"
            }`}
          >
            {isSimulating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            <span>
              {isSimulating ? "Memproses Agen..." : "Simulasi Insiden Rantai Pasok"}
            </span>
          </button>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6 text-xs font-medium">
          {/* Main Menu */}
          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Menu Utama
            </div>
            <nav className="space-y-1">
              <button className="w-full flex items-center gap-2.5 rounded-md bg-blue-50 px-3 py-2 font-semibold text-blue-700">
                <BarChart3 className="h-4 w-4" />
                <span>Dashboard SPPG</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <Warehouse className="h-4 w-4 text-slate-400" />
                <span>Logistik & Gudang</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <Cpu className="h-4 w-4 text-slate-400" />
                <span>Hybrid LangGraph Agent</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <FileText className="h-4 w-4 text-slate-400" />
                <span>Purchase Orders (PO)</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <Users className="h-4 w-4 text-slate-400" />
                <span>Kru & Personel Dapur</span>
              </button>
            </nav>
          </div>

          {/* Compliance & Documents */}
          <div>
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Kepatuhan & Audit
            </div>
            <nav className="space-y-1">
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <Building2 className="h-4 w-4 text-slate-400" />
                <span>Katalog Rekanan Halal</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <FolderGit2 className="h-4 w-4 text-slate-400" />
                <span>Immutable Audit Logs</span>
              </button>
              <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
                <ShieldCheck className="h-4 w-4 text-slate-400" />
                <span>Pagu SOP Gizi 2026</span>
              </button>
            </nav>
          </div>
        </div>

        {/* Bottom Sidebar Footer & User Profile */}
        <div className="border-t border-slate-200 p-3 space-y-1 text-xs">
          <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100">
            <Settings className="h-4 w-4 text-slate-400" />
            <span>Pengaturan SPPG</span>
          </button>
          <button className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-100">
            <HelpCircle className="h-4 w-4 text-slate-400" />
            <span>Panduan SOP Gizi</span>
          </button>

          {/* Approver Profile Card */}
          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between px-2 py-1.5 rounded-lg bg-slate-50">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 rounded-full bg-blue-100 border border-blue-200 text-blue-800 flex items-center justify-center font-bold text-xs shrink-0">
                BS
              </div>
              <div className="truncate">
                <div className="text-xs font-bold text-slate-900 truncate">
                  Budi Santoso, S.T.
                </div>
                <div className="text-[10px] text-slate-500 truncate">
                  Kepala SPPG Wilayah I
                </div>
              </div>
            </div>
            <MoreVertical className="h-4 w-4 text-slate-400 shrink-0" />
          </div>
        </div>
      </aside>

      {/* =========================================================================
          2. MAIN CONTENT AREA (MENIRU PERSIS SHADCN DASHBOARD-01)
      ========================================================================= */}
      <div className="flex flex-1 flex-col overflow-x-hidden">
        {/* Top Header / Breadcrumb Bar */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500">
              SPPG Wilayah I
            </span>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-bold text-slate-900">
              Dashboard Mitigasi Krisis Rantai Pasok
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Real-time Status Badge */}
            <div className="hidden sm:flex items-center gap-2 rounded-full bg-slate-100 border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>LangGraph Checkpointer: Persisten</span>
            </div>

            <button className="p-2 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100">
              <Search className="h-4 w-4" />
            </button>
            <button className="p-2 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 relative">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500"></span>
            </button>

            {/* Mobile Simulation Button */}
            <button
              onClick={handleStartSimulation}
              disabled={isSimulating}
              className="lg:hidden flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-700 text-white text-xs font-semibold"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isSimulating ? "animate-spin" : ""}`} />
              <span>Simulasi</span>
            </button>
          </div>
        </header>

        {/* Dashboard Body */}
        <main className="flex-1 space-y-6 p-4 sm:p-6 lg:p-8">
          {/* =====================================================================
              ROW 1: 4 STAT CARDS (PERSIS GAYA SHADCN DASHBOARD-01)
          ===================================================================== */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Card 1 */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
              <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                <span>Target Menu Harian</span>
                <span className="flex items-center gap-1 font-semibold text-emerald-600 text-[11px]">
                  <TrendingUp className="h-3 w-3" /> +12.5%
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
                3.000 <span className="text-sm font-normal text-slate-500">Porsi</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Menu Utama: Nasi & Daging Ayam Broiler
              </p>
            </div>

            {/* Card 2 */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
              <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                <span>Stok Gudang Fisik</span>
                <span className="flex items-center gap-1 font-semibold text-blue-600 text-[11px]">
                  Rasio 55.5%
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
                80.0 <span className="text-sm font-normal text-slate-500">kg</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Total Kebutuhan: 144.0 kg (+20% safety margin)
              </p>
            </div>

            {/* Card 3 (Defisit - Alert Card) */}
            <div className="rounded-xl border border-red-200 bg-red-50/20 p-5 shadow-2xs">
              <div className="flex items-center justify-between text-xs font-medium text-red-600">
                <span>Defisit Kuantitas Kritis</span>
                <span className="flex items-center gap-1 font-semibold text-red-600 text-[11px]">
                  <TrendingDown className="h-3 w-3" /> Krisis
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-red-600">
                64.0 <span className="text-sm font-normal text-red-400">kg</span>
              </div>
              <p className="mt-1 text-xs font-medium text-red-600">
                Supplier Utama Terhambat Banjir Pantura
              </p>
            </div>

            {/* Card 4 (Freezer Storage Bottleneck) */}
            <div className="rounded-xl border border-amber-200 bg-amber-50/20 p-5 shadow-2xs">
              <div className="flex items-center justify-between text-xs font-medium text-amber-700">
                <span>Sisa Ruang Freezer Dingin</span>
                <span className="flex items-center gap-1 font-semibold text-amber-700 text-[11px]">
                  Restriksi Fisik
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-amber-800">
                20.0 <span className="text-sm font-normal text-amber-600">kg</span>
              </div>
              <p className="mt-1 text-xs font-medium text-amber-700">
                Mewajibkan Skema Split Delivery
              </p>
            </div>
          </div>

          {/* =====================================================================
              ROW 2: MIDDLE LARGE SECTION (CHARTS & PIPELINE VISUALIZER)
          ===================================================================== */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-2xs">
            {/* Header with Tabs (like "Total Visitors" in the reference) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-blue-700" />
                  LangGraph Hybrid Pipeline & Proyeksi Kebutuhan
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Visualisasi deterministik dan penalaran agen LLM secara real-time
                </p>
              </div>

              {/* View Switcher Tabs */}
              <div className="inline-flex rounded-lg bg-slate-100 p-1 text-xs font-medium text-slate-600">
                <button
                  onClick={() => setActiveTab("visualizer")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "visualizer"
                      ? "bg-white font-semibold text-slate-900 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  Live Pipeline Visualizer
                </button>
                <button
                  onClick={() => setActiveTab("chart")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "chart"
                      ? "bg-white font-semibold text-slate-900 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  Kurva Proyeksi Stok
                </button>
                <button
                  onClick={() => setActiveTab("matrix")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    activeTab === "matrix"
                      ? "bg-white font-semibold text-slate-900 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  Matriks 7 Parameter
                </button>
              </div>
            </div>

            {/* TAB CONTENT 1: LIVE PIPELINE VISUALIZER */}
            {activeTab === "visualizer" && (
              <div className="mt-6 space-y-5">
                {/* 5 Node Stream Flow */}
                <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
                  {pipelineNodes.map((node, index) => {
                    const isCompleted = completedNodes.includes(node.id);
                    const isActive = activeNode === node.id;
                    const Icon = node.icon;

                    return (
                      <div
                        key={node.id}
                        className={`relative rounded-xl border p-4 transition-all duration-300 ${
                          isActive
                            ? "border-blue-500 bg-blue-50/70 shadow-md shadow-blue-500/10 ring-2 ring-blue-500/20"
                            : isCompleted
                            ? "border-emerald-300 bg-emerald-50/50"
                            : "border-slate-200 bg-slate-50/60 opacity-70"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                              node.type === "DETERMINISTIC"
                                ? "bg-slate-200 text-slate-700"
                                : node.type === "COGNITIVE LLM"
                                ? "bg-indigo-100 text-indigo-800"
                                : "bg-amber-200 text-amber-900"
                            }`}
                          >
                            {node.type}
                          </span>
                          {isCompleted ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          ) : isActive ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className="font-mono text-xs text-slate-400">
                              0{index + 1}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <Icon
                            className={`h-4 w-4 ${
                              isActive
                                ? "text-blue-700"
                                : isCompleted
                                ? "text-emerald-700"
                                : "text-slate-400"
                            }`}
                          />
                          <h4 className="text-xs font-bold text-slate-900 truncate">
                            {node.name}
                          </h4>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-500 line-clamp-2">
                          {node.desc}
                        </p>
                      </div>
                    );
                  })}
                </div>

                {/* Stream Console / Status Ticker */}
                <div className="rounded-xl bg-slate-900 p-4 font-mono text-xs text-slate-200 shadow-inner">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2 truncate">
                      <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping"></span>
                      <span className="text-slate-400">SSE Event Stream:</span>
                      <span className="font-sans font-medium text-blue-300">
                        {currentStepMessage}
                      </span>
                    </div>

                    {decision && !issuedPO && (
                      <button
                        onClick={() => setIsApprovalModalOpen(true)}
                        className="ml-4 shrink-0 rounded-md bg-amber-500 px-3 py-1 font-sans text-xs font-bold text-slate-950 transition hover:bg-amber-400 active:scale-95"
                      >
                        Buka Otorisasi Kepala SPPG (HITL)
                      </button>
                    )}
                  </div>

                  {streamLogs.length > 0 && (
                    <div className="mt-2 max-h-24 space-y-1 overflow-y-auto text-[11px] text-slate-400">
                      {streamLogs.map((log, i) => (
                        <div key={i} className="flex items-center gap-1.5">
                          <span className="text-blue-400">›</span>
                          <span>{log}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB CONTENT 2: PROJECTION CHART (MENIRU PERSIS GELOMBANG DI REFERENSI GAMBAR) */}
            {activeTab === "chart" && (
              <div className="mt-6">
                <div className="h-56 w-full">
                  <svg
                    viewBox="0 0 900 220"
                    className="h-full w-full overflow-visible"
                  >
                    <defs>
                      <linearGradient
                        id="blueGrad"
                        x1="0%"
                        y1="0%"
                        x2="0%"
                        y2="100%"
                      >
                        <stop offset="0%" stopColor="#2563eb" stopOpacity="0.35" />
                        <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
                      </linearGradient>
                      <linearGradient
                        id="slateGrad"
                        x1="0%"
                        y1="0%"
                        x2="0%"
                        y2="100%"
                      >
                        <stop offset="0%" stopColor="#64748b" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#64748b" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal Grid lines */}
                    <line
                      x1="0"
                      y1="40"
                      x2="900"
                      y2="40"
                      stroke="#f1f5f9"
                      strokeDasharray="4 4"
                    />
                    <line
                      x1="0"
                      y1="100"
                      x2="900"
                      y2="100"
                      stroke="#f1f5f9"
                      strokeDasharray="4 4"
                    />
                    <line
                      x1="0"
                      y1="160"
                      x2="900"
                      y2="160"
                      stroke="#f1f5f9"
                      strokeDasharray="4 4"
                    />

                    {/* Area Waveform 1: Buffer Safety & Normal Demand */}
                    <path
                      d="M 0 160 Q 60 120, 120 145 T 240 100 T 360 140 T 480 80 T 600 130 T 720 90 T 840 110 L 900 120 L 900 220 L 0 220 Z"
                      fill="url(#slateGrad)"
                    />
                    <path
                      d="M 0 160 Q 60 120, 120 145 T 240 100 T 360 140 T 480 80 T 600 130 T 720 90 T 840 110 L 900 120"
                      fill="none"
                      stroke="#64748b"
                      strokeWidth="2"
                    />

                    {/* Area Waveform 2: Actual Stock Flow dengan Split Delivery */}
                    <path
                      d="M 0 190 Q 70 170, 140 130 T 280 160 T 420 90 T 560 140 T 700 70 T 840 130 L 900 95 L 900 220 L 0 220 Z"
                      fill="url(#blueGrad)"
                    />
                    <path
                      d="M 0 190 Q 70 170, 140 130 T 280 160 T 420 90 T 560 140 T 700 70 T 840 130 L 900 95"
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth="2.5"
                    />

                    {/* Timeline Axis Labels */}
                    <text x="20" y="215" fill="#94a3b8" fontSize="10">H-3 (Normal)</text>
                    <text x="220" y="215" fill="#94a3b8" fontSize="10">H-2 (Banjir Pantura)</text>
                    <text x="460" y="215" fill="#2563eb" fontWeight="bold" fontSize="10">H-1 (Batch 1: 20kg)</text>
                    <text x="680" y="215" fill="#2563eb" fontWeight="bold" fontSize="10">Hari-H 05:00 (Batch 2: 44kg)</text>
                    <text x="830" y="215" fill="#10b981" fontSize="10">Masak Pagi 3.000 Porsi</text>
                  </svg>
                </div>
                <div className="flex items-center justify-center gap-6 pt-3 text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-blue-600"></span>
                    <span>Alur Stok Bahan dengan Split Delivery</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-slate-400"></span>
                    <span>Garis Pagu Batas Safety Stock SOP</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT 3: 7 PARAMETER MATRIX SUMMARY */}
            {activeTab === "matrix" && (
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-600">
                    Formula Skoring Deterministik Python
                  </h4>
                  <div className="space-y-2 text-xs text-slate-700">
                    <div className="flex justify-between">
                      <span>1. Kuota Defisit (W1 = 25%)</span>
                      <span className="font-mono font-bold text-blue-700">100.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span>2. Lead Time vs Jam Masak (W2 = 20%)</span>
                      <span className="font-mono font-bold text-blue-700">85.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span>3. Kepatuhan Anggaran SOP (W3 = 15%)</span>
                      <span className="font-mono font-bold text-emerald-600">90.0</span>
                    </div>
                    <div className="flex justify-between font-bold text-blue-900">
                      <span>4. Halal BPJPH (W4 = 15% - Gating)</span>
                      <span className="font-mono text-emerald-600">100.0 (LOLOS)</span>
                    </div>
                    <div className="flex justify-between text-amber-800">
                      <span>5. Kesesuaian Freezer (W5 = 10%)</span>
                      <span className="font-mono font-bold text-amber-600">40.0 (Klausul)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>6. Kesiapan Dapur Olah (W6 = 10%)</span>
                      <span className="font-mono font-bold text-blue-700">80.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span>7. Keamanan Rute Logistik (W7 = 5%)</span>
                      <span className="font-mono font-bold text-blue-700">70.0</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                      Keputusan Feasibility Gate
                    </span>
                    <div className="mt-1 flex items-baseline gap-2">
                      <span className="text-3xl font-black font-mono text-blue-900">
                        78.5
                      </span>
                      <span className="text-xs text-slate-500 font-medium">/ 100</span>
                    </div>
                    <div className="mt-2">
                      <span className="inline-block rounded-md bg-amber-100 border border-amber-300 px-2 py-0.5 text-xs font-bold text-amber-900">
                        FEASIBLE WITH CONDITIONS
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-700 leading-relaxed">
                      Skor $\ge 60$ dan lolos audit keabsahan halal 100%. Diwajibkan
                      skema pengiriman terbagi (Split Delivery) 2 batch akibat kapasitas freezer SPPG hanya 20 kg.
                    </p>
                  </div>

                  {decision && !issuedPO && (
                    <button
                      onClick={() => setIsApprovalModalOpen(true)}
                      className="mt-4 w-full rounded-lg bg-blue-700 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-800 transition"
                    >
                      Buka Otorisasi Kepala SPPG
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* =====================================================================
              ROW 3: BOTTOM DATA TABLE (MENIRU PERSIS TABEL DI REFERENSI GAMBAR)
          ===================================================================== */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-2xs overflow-hidden">
            {/* Table Control Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 p-4">
              {/* Filter Tabs */}
              <div className="inline-flex rounded-lg bg-slate-100 p-1 text-xs font-medium text-slate-600">
                <button
                  onClick={() => setTableFilter("all")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    tableFilter === "all"
                      ? "bg-white font-semibold text-slate-900 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  Semua Bahan (4)
                </button>
                <button
                  onClick={() => setTableFilter("mitigation")}
                  className={`rounded-md px-3 py-1.5 transition-all flex items-center gap-1.5 ${
                    tableFilter === "mitigation"
                      ? "bg-white font-semibold text-red-700 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500"></span>
                  Perlu Mitigasi (1)
                </button>
                <button
                  onClick={() => setTableFilter("safe")}
                  className={`rounded-md px-3 py-1.5 transition-all ${
                    tableFilter === "safe"
                      ? "bg-white font-semibold text-emerald-700 shadow-xs"
                      : "hover:text-slate-900"
                  }`}
                >
                  Pasokan Aman (3)
                </button>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  <span>Kustomisasi Kolom</span>
                </button>
                <button
                  onClick={() => setIsApprovalModalOpen(true)}
                  disabled={!decision || !!issuedPO}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-xs transition ${
                    decision && !issuedPO
                      ? "bg-blue-700 text-white hover:bg-blue-800"
                      : "bg-slate-100 text-slate-400 cursor-not-allowed"
                  }`}
                >
                  <UserCheck className="h-3.5 w-3.5" />
                  <span>Otorisasi Pengadaan</span>
                </button>
              </div>
            </div>

            {/* The Data Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="border-b border-slate-200 bg-slate-50/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th scope="col" className="p-4 w-4">
                      <input
                        type="checkbox"
                        className="rounded border-slate-300 text-blue-600"
                        defaultChecked
                      />
                    </th>
                    <th scope="col" className="py-3 px-4">Bahan Pangan (Header)</th>
                    <th scope="col" className="py-3 px-4">Kategori Bahan</th>
                    <th scope="col" className="py-3 px-4">Status Rantai Pasok</th>
                    <th scope="col" className="py-3 px-4">Kebutuhan / Target</th>
                    <th scope="col" className="py-3 px-4">Skor Kelayakan</th>
                    <th scope="col" className="py-3 px-4">Penanggung Jawab</th>
                    <th scope="col" className="py-3 px-4 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredItems.map((item) => (
                    <tr
                      key={item.id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        item.urgent ? "bg-red-50/15" : ""
                      }`}
                    >
                      <td className="p-4">
                        <input
                          type="checkbox"
                          className="rounded border-slate-300 text-blue-600"
                          defaultChecked={item.urgent}
                        />
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">{item.name}</div>
                        <div className="font-mono text-[10px] text-slate-400">
                          {item.id}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-medium">{item.category}</td>
                      <td className="py-3.5 px-4">
                        {item.urgent ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 border border-amber-200">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-600 animate-pulse"></span>
                            {issuedPO ? "PO Diterbitkan" : item.status}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
                            <Check className="h-3 w-3" />
                            {item.status}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">{item.targetQty}</div>
                        <div className="text-[10px] text-slate-400">
                          Stok: {item.stockActual}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-700">
                        {item.score}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-900">
                          {item.reviewer}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {item.urgent ? "Otoritas Tunggal" : "Verified"}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {item.urgent && decision && !issuedPO ? (
                          <button
                            onClick={() => setIsApprovalModalOpen(true)}
                            className="rounded-md bg-blue-700 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-800"
                          >
                            Review
                          </button>
                        ) : (
                          <button className="text-slate-400 hover:text-slate-600 p-1">
                            <MoreVertical className="h-4 w-4" />
                          </button>
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
          3. HUMAN-IN-THE-LOOP APPROVAL MODAL (HITL GATE DIALOG)
      ========================================================================= */}
      {isApprovalModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
                <ShieldCheck className="h-5 w-5 text-blue-700" />
                <span>Otorisasi Pengadaan Darurat Kepala SPPG</span>
              </div>
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="rounded-md p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-lg border border-blue-200 bg-blue-50/70 p-3.5 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Tiket Insiden:</span>
                  <span className="font-mono font-bold text-slate-900">
                    {decision?.incident_id || "INC-2026-001"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Supplier Alternatif:</span>
                  <span className="font-bold text-blue-900">
                    {decision?.recommended_procurement?.supplier_name ||
                      "PT Berkah Unggas Jaya"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Skor Feasibility:</span>
                  <span className="font-mono font-bold text-emerald-700">
                    78.5 / 100 (Halal BPJPH Aktif)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Skema Logistik:</span>
                  <span className="font-semibold text-blue-700">
                    Split Delivery (Batch 1: 20kg • Batch 2: 44kg)
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
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                />
                <span className="mt-1 block text-[11px] text-slate-500">
                  Defisit kuantitas hasil kalkulasi matematika: 64.0 kg
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
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                ></textarea>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
              <button
                onClick={() => setIsApprovalModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Batal
              </button>
              <button
                onClick={handleApprove}
                className="rounded-lg bg-blue-700 px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition hover:bg-blue-800 active:scale-95 flex items-center gap-2"
              >
                <span>Setujui & Terbitkan Purchase Order</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          4. MODAL PURCHASE ORDER SUKSES
      ========================================================================= */}
      {isPoModalOpen && issuedPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-2xl border border-slate-200">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Purchase Order Resmi Diterbitkan!
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Siklus mitigasi insiden telah terekam ke dalam tabel audit log permanen.
            </p>

            <div className="my-5 space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-left text-xs">
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
                <span className="text-slate-500">Volume Disetujui:</span>
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
              className="w-full rounded-lg bg-blue-700 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-800 transition"
            >
              Tutup & Kembali ke Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
