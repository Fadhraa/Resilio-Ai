"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Send,
  Bot,
  User,
  RotateCcw,
  FileText,
  Warehouse,
  Boxes,
  Truck,
  Building2,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  Printer,
  X,
  Search,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Loader2,
  Info,
} from "lucide-react";
import {
  ChatResponse,
  CircularLetter,
  ExecutionTraceStep,
  InventoryItem,
  PurchaseOrderResponse,
  SupplierRecord,
} from "@/types/incident";
import {
  mockCircularLetters,
  mockInventory,
  mockPurchaseOrdersList,
  mockSuppliers,
} from "@/data/mockData";

export const LIVE_PIPELINE_STEPS = [
  {
    number: 1,
    title: "Kueri Data Inventaris & Defisit Riil (SQLite ACID)",
    description:
      "Mengekstrak stok fisik gudang dan menghitung defisit kebutuhan porsi gizi.",
  },
  {
    number: 2,
    title: "Filter Syarat Mutlak Kepatuhan Halal (UU JPH 33/2014)",
    description:
      "Menyaring rekanan resmi berizin halal aktif dan mengeliminasi non-halal.",
  },
  {
    number: 3,
    title: "Sintesis Strategi Logistik Agen Kognitif",
    description:
      "Merumuskan alokasi pasokan darurat dan evaluasi kapasitas ruang simpan dingin.",
  },
  {
    number: 4,
    title: "Validasi Deterministik Matriks 7 Parameter Feasibility",
    description:
      "Menghitung formula skor kelayakan matematis dan memvalidasi batas pagu SOP.",
  },
  {
    number: 5,
    title: "Penyusunan Keputusan & Gerbang Otorisasi Kepala SPPG",
    description:
      "Menyiapkan draf PO resmi yang menunggu persetujuan otorisasi manusia.",
  },
];

const getTraceBadge = (trace: ExecutionTraceStep[]) => {
  const isDuplicateCheck = trace.some(
    (s) =>
      s.stage === "INTEGRITY_GATE" ||
      s.title?.toLowerCase().includes("duplikasi") ||
      s.details?.toLowerCase().includes("duplikasi"),
  );
  if (isDuplicateCheck) {
    return {
      label: "100% Deterministic & ACID (Integritas Terjaga)",
      className: "text-cyan-800 bg-cyan-100/80 border-cyan-200",
      icon: <ShieldCheck className="h-3 w-3 text-cyan-600" />,
    };
  }

  const isParameterValidation = trace.some(
    (s) =>
      s.stage === "PARAMETER_AUDIT" ||
      s.stage === "HUMAN_CLARIFICATION_GATE" ||
      s.title?.toLowerCase().includes("kelengkapan"),
  );
  if (isParameterValidation) {
    return {
      label: "Validasi Parameter SOP",
      className: "text-amber-800 bg-amber-100/80 border-amber-200",
      icon: <Clock className="h-3 w-3 text-amber-600" />,
    };
  }

  return {
    label: "100% Deterministic & Halal",
    className: "text-emerald-700 bg-emerald-100/80 border-emerald-200",
    icon: <ShieldCheck className="h-3 w-3 text-emerald-600" />,
  };
};

function FormattedMessage({ content }: { content: string }) {
  if (!content) return null;

  // Bersihkan karakter LaTeX atau math delimiters jika ada
  const cleanContent = content
    .replace(/\\\(|\\\)/g, "")
    .replace(/\\\[|\\\]/g, "")
    .replace(/\$\$/g, "")
    .replace(/\$(.*?)\$/g, "$1")
    .replace(/\\textbf\{(.*?)\}/g, "**$1**")
    .replace(/\\textit\{(.*?)\}/g, "*$1*");

  const lines = cleanContent.split("\n");

  const parseInline = (text: string) => {
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|`.*?`|\*.*?\*)/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(
          <strong key={match.index} className="font-semibold text-inherit">
            {token.slice(2, -2)}
          </strong>,
        );
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(
          <code
            key={match.index}
            className="rounded bg-black/10 px-1 py-0.5 font-mono text-[11px] text-inherit"
          >
            {token.slice(1, -1)}
          </code>,
        );
      } else if (token.startsWith("*") && token.endsWith("*")) {
        parts.push(
          <em key={match.index} className="italic text-inherit">
            {token.slice(1, -1)}
          </em>,
        );
      }
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts;
  };

  return (
    <div className="space-y-1.5 leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }

        if (trimmed === "---") {
          return <hr key={idx} className="my-2 border-slate-200" />;
        }

        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={idx} className="font-bold text-slate-900 mt-2 mb-1">
              {parseInline(trimmed.slice(4))}
            </h4>
          );
        }

        // Bullet list (•, *, -)
        const bulletMatch = trimmed.match(/^[\*\-•]\s+(.*)$/);
        if (bulletMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className="text-blue-600 font-bold select-none leading-5">
                •
              </span>
              <div className="flex-1">{parseInline(bulletMatch[1])}</div>
            </div>
          );
        }

        // Numbered list (1., 2., etc.)
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className="font-semibold text-blue-700 select-none leading-5 min-w-[16px]">
                {numMatch[1]}.
              </span>
              <div className="flex-1">{parseInline(numMatch[2])}</div>
            </div>
          );
        }

        // Regular paragraph
        return <p key={idx}>{parseInline(line)}</p>;
      })}
    </div>
  );
}

export default function DashboardPage() {
  // =========================================================================
  // 1. STATE NAVIGASI & LAYOUT (GEMINI WEB STYLE)
  // =========================================================================
  const [activeTab, setActiveTab] = useState<
    "chat" | "circular_letters" | "suppliers" | "inventory"
  >("chat");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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
          now.toLocaleTimeString("id-ID", {
            hour: "2-digit",
            minute: "2-digit",
          }) +
          " WIB",
      );
    };
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  // =========================================================================
  // 2. STATE CHAT WORKSPACE
  // =========================================================================
  const [chatMessages, setChatMessages] = useState<
    Array<{
      role: "user" | "assistant";
      text: string;
      previewData?: Record<string, any>;
      intent?: string;
      executionTrace?: ExecutionTraceStep[];
    }>
  >([]);
  const [expandedTraces, setExpandedTraces] = useState<Record<number, boolean>>(
    {},
  );
  const [liveStep, setLiveStep] = useState<number>(1);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState(`SES-SPPG-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isRoiModalOpen, setIsRoiModalOpen] = useState(true);

  // Menangani tombol "Mulai Uji Coba" dari Modal ROI: isi teks skenario dan fokuskan kursor
  const handleStartSimulation = () => {
    setActiveTab("chat");
    setInputMessage(
      "Armada supplier ayam utama PT Unggas Sejahtera Nusantara terjebak banjir di jalur Pantura, tolong segera mitigasi darurat dan carikan alternatif halal.",
    );
    setIsRoiModalOpen(false);
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  };

  // Cognitive Execution Stepper Progress Timer saat isSending aktif
  useEffect(() => {
    if (!isSending) {
      setLiveStep(1);
      return;
    }
    setLiveStep(1);
    const t1 = setTimeout(() => setLiveStep(2), 400);
    const t2 = setTimeout(() => setLiveStep(3), 1000);
    const t3 = setTimeout(() => setLiveStep(4), 1700);
    const t4 = setTimeout(() => setLiveStep(5), 2400);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [isSending]);

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  // Scroll otomatis saat ada pesan baru atau sedang memproses respons
  useEffect(() => {
    scrollToBottom("smooth");
  }, [chatMessages, isSending]);

  // Scroll otomatis ke percakapan terakhir saat pengguna kembali/membuka tab Chat
  useEffect(() => {
    if (activeTab === "chat") {
      const timer = setTimeout(() => {
        scrollToBottom("auto");
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [activeTab]);

  // Auto-resize tinggi textarea saat teks input bertambah (membesar ke bawah, maks 140px)
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const newHeight = Math.min(textareaRef.current.scrollHeight, 140);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [inputMessage]);

  const handleStartNewChat = () => {
    setChatMessages([]);
    setSessionId(`SES-SPPG-${Date.now()}`);
    setActiveTab("chat");
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || isSending) return;

    const userMsg = text.trim();
    if (!textToSend) {
      setInputMessage("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }

    setChatMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setIsSending(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMsg,
          user_role: "Bapak Adam Dzaki (Kepala SPPG)",
        }),
      });

      if (res.ok) {
        const data: ChatResponse = await res.json();
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.reply,
            previewData: data.preview_data,
            intent: data.intent,
            executionTrace: data.execution_trace,
          },
        ]);
        if (data.preview_data) {
          loadData();
        }
      } else {
        throw new Error("Gagal menerima respons server");
      }
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Mohon maaf, terjadi kendala koneksi dengan mesin kognitif. Silakan coba kembali dalam beberapa saat.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // =========================================================================
  // 3. STATE DATA ARSIP (SURAT EDARAN, PO, REKANAN, INVENTARIS)
  // =========================================================================
  const [circularLetters, setCircularLetters] = useState<CircularLetter[]>(
    mockCircularLetters as CircularLetter[],
  );
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrderResponse[]>(
    mockPurchaseOrdersList as PurchaseOrderResponse[],
  );
  const [suppliers, setSuppliers] = useState<SupplierRecord[]>(mockSuppliers);
  const [inventory, setInventory] = useState<InventoryItem[]>(mockInventory);

  // Filter & Search Dokumen
  const [documentFilter, setDocumentFilter] = useState<"ALL" | "SE" | "PO">(
    "ALL",
  );
  const [searchDocQuery, setSearchDocQuery] = useState("");

  // Modal Dokumen Resmi
  const [selectedDoc, setSelectedDoc] = useState<{
    type: "SE" | "PO";
    data: any;
  } | null>(null);

  // Ambil data terbaru dari backend proxy
  const loadData = async () => {
    try {
      const [resSE, resPO, resSuppliers, resInv] = await Promise.all([
        fetch("/api/circular-letters").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/purchase-orders").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/suppliers").then((r) => (r.ok ? r.json() : null)),
        fetch("/api/inventory").then((r) => (r.ok ? r.json() : null)),
      ]);
      if (resSE && Array.isArray(resSE)) setCircularLetters(resSE);
      if (resPO && Array.isArray(resPO)) setPurchaseOrders(resPO);
      if (resSuppliers && Array.isArray(resSuppliers))
        setSuppliers(resSuppliers);
      if (resInv && Array.isArray(resInv)) setInventory(resInv);
    } catch {
      // Gunakan fallback mockData yang sudah terpasang
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900 antialiased">
      {/* =====================================================================
          SIDEBAR KIRI (GEMINI STYLE)
          ===================================================================== */}
      <aside
        className={`flex flex-col border-r border-slate-200 bg-white transition-all duration-200 ease-in-out ${
          isSidebarOpen ? "w-72" : "w-16"
        }`}
      >
        {/* Header Sidebar */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-100">
          {isSidebarOpen ? (
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-700 text-white shadow-sm">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div className="flex flex-col truncate">
                <span className="font-semibold text-sm tracking-tight text-slate-900">
                  Resilio AI
                </span>
                <span className="text-[11px] text-slate-500 truncate">
                  Sistem Siaga SPPG BGN
                </span>
              </div>
            </div>
          ) : (
            <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-xl bg-blue-700 text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
          )}

          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 focus:outline-none"
            title={isSidebarOpen ? "Tutup Sidebar" : "Buka Sidebar"}
            aria-label="Toggle Sidebar"
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="h-5 w-5" />
            ) : (
              <PanelLeftOpen className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Tombol Aksi Utama: Obrolan Baru */}
        <div className="p-3">
          <button
            onClick={handleStartNewChat}
            className={`flex items-center gap-3 w-full rounded-2xl bg-blue-50 text-blue-700 hover:bg-blue-100 font-medium text-sm transition-colors border border-blue-200/60 shadow-xs ${
              isSidebarOpen
                ? "px-4 py-3 justify-start"
                : "h-11 w-11 justify-center p-0 mx-auto"
            }`}
            title="Mulai Percakapan Baru"
          >
            <Plus className="h-5 w-5 shrink-0" />
            {isSidebarOpen && <span>Percakapan Baru</span>}
          </button>
        </div>

        {/* Daftar Navigasi Item Menu */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
          {isSidebarOpen && (
            <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Navigasi Operasional
            </div>
          )}

          {/* Menu 1: Obrolan AI */}
          <button
            onClick={() => setActiveTab("chat")}
            className={`flex items-center gap-3 w-full rounded-xl text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            } ${isSidebarOpen ? "px-3.5 py-2.5 justify-start" : "h-10 w-10 justify-center p-0 mx-auto"}`}
            title="Obrolan AI (Asisten Siaga Pangan)"
          >
            <Bot className="h-4 w-4 shrink-0" />
            {isSidebarOpen && <span className="truncate">Obrolan AI</span>}
          </button>

          {/* Menu 2: Arsip Surat Edaran & PO */}
          <button
            onClick={() => setActiveTab("circular_letters")}
            className={`flex items-center gap-3 w-full rounded-xl text-sm font-medium transition-colors ${
              activeTab === "circular_letters"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            } ${isSidebarOpen ? "px-3.5 py-2.5 justify-start" : "h-10 w-10 justify-center p-0 mx-auto"}`}
            title="Arsip Surat Edaran & PO"
          >
            <FileText className="h-4 w-4 shrink-0" />
            {isSidebarOpen && (
              <div className="flex flex-1 items-center justify-between truncate">
                <span className="truncate">Arsip Surat Edaran & PO</span>
                <span className="ml-2 rounded-full bg-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700">
                  {circularLetters.length + purchaseOrders.length}
                </span>
              </div>
            )}
          </button>

          {/* Menu 3: Katalog Rekanan Supplier */}
          <button
            onClick={() => setActiveTab("suppliers")}
            className={`flex items-center gap-3 w-full rounded-xl text-sm font-medium transition-colors ${
              activeTab === "suppliers"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            } ${isSidebarOpen ? "px-3.5 py-2.5 justify-start" : "h-10 w-10 justify-center p-0 mx-auto"}`}
            title="Katalog Rekanan Supplier"
          >
            <Building2 className="h-4 w-4 shrink-0" />
            {isSidebarOpen && (
              <div className="flex flex-1 items-center justify-between truncate">
                <span className="truncate">Katalog Rekanan</span>
                <span className="ml-2 rounded-full bg-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700">
                  {suppliers.length}
                </span>
              </div>
            )}
          </button>

          {/* Menu 4: Monitoring Stok Gudang */}
          <button
            onClick={() => setActiveTab("inventory")}
            className={`flex items-center gap-3 w-full rounded-xl text-sm font-medium transition-colors ${
              activeTab === "inventory"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-700 hover:bg-slate-100"
            } ${isSidebarOpen ? "px-3.5 py-2.5 justify-start" : "h-10 w-10 justify-center p-0 mx-auto"}`}
            title="Monitoring Stok Gudang"
          >
            <Warehouse className="h-4 w-4 shrink-0" />
            {isSidebarOpen && <span className="truncate">Stok & Gudang</span>}
          </button>
        </div>

        {/* Footer Sidebar: Profil Pengguna */}
        <div className="p-3 border-t border-slate-100">
          <div
            className={`flex items-center gap-3 rounded-xl p-2 bg-slate-50 ${
              isSidebarOpen ? "justify-start" : "justify-center p-1"
            }`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-800 font-semibold text-xs border border-blue-200">
              AD
            </div>
            {isSidebarOpen && (
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-slate-900 truncate">
                  Bapak Adam Dzaki
                </span>
                <span className="text-[11px] text-slate-500 truncate">
                  Kepala SPPG Wilayah I
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* =====================================================================
          MAIN WORKSPACE CANVAS
          ===================================================================== */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-white">
        {/* Top Header Bar */}
        <header className="flex h-14 items-center justify-between border-b border-slate-200 px-6 bg-white shrink-0">
          <div className="flex items-center gap-3">
            <span className="hidden md:inline text-xs text-slate-500 font-mono">
              Resilio Cognitive Engine (SQLite ACID)
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
              <span className="font-mono">
                {currentTime || "Memuat waktu..."}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setIsRoiModalOpen(true)}
              className="flex items-center justify-center h-8 w-8 rounded-lg border border-slate-200 bg-slate-50 text-slate-600 hover:text-blue-700 hover:bg-blue-50 hover:border-blue-300 transition-all cursor-pointer shadow-2xs"
              title="Ringkasan Eksekutif & Dampak Bisnis (ROI)"
            >
              <Info className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* ===================================================================
            VIEW 1: OBROLAN AI (GEMINI WEB STYLE)
            =================================================================== */}
        {activeTab === "chat" && (
          <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden relative">
            {/* Scrollable Message Thread */}
            <div className="flex-1 overflow-y-auto px-4 py-6 md:px-12 lg:px-24">
              <div className="max-w-3xl mx-auto space-y-6">
                {chatMessages.length === 0 ? (
                  /* Welcome Canvas (Gemini Style) */
                  <div className="pt-12 md:pt-20 text-left space-y-8">
                    <div className="space-y-3">
                      <div className="inline-flex items-center gap-2 text-blue-700 font-semibold text-sm">
                        <span>Resilio AI Copilot</span>
                      </div>
                      <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-900">
                        Selamat bertugas, Bapak Adam Dzaki.
                      </h1>
                      <p className="text-slate-600 text-sm md:text-base leading-relaxed max-w-2xl">
                        Sistem asistensi kognitif terpadu untuk mendeteksi
                        defisit pangan, memverifikasi kepatuhan sertifikasi
                        Halal (UU JPH 33/2014), dan menyusun strategi logistik
                        darurat SPPG secara otomatis.
                      </p>
                    </div>

                    {/* Quick Suggestion Cards */}
                    <div className="space-y-2.5 pt-4">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        Pintasan Instruksi Cepat
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <button
                          onClick={() =>
                            handleSendMessage(
                              "🚨 Laporkan gangguan: Supplier utama PT Unggas Sejahtera Nusantara gagal kirim daging ayam karena kendala armada. Tolong carikan rekanan cadangan yang halal dan buatkan draf mitigasinya.",
                            )
                          }
                          className="flex flex-col text-left p-4 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-blue-50/50 hover:border-blue-300 transition-all shadow-2xs group"
                        >
                          <div className="flex items-center justify-between w-full mb-2">
                            <span className="text-xs font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                              Insiden Darurat
                            </span>
                            <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                          </div>
                          <p className="text-xs font-medium text-slate-800 line-clamp-2">
                            Laporkan gangguan pasokan ayam potong dan minta
                            solusi mitigasi
                          </p>
                        </button>

                        <button
                          onClick={() =>
                            handleSendMessage(
                              "Tolong periksa status stok gudang saat ini, apakah kapasitas freezer kita cukup untuk cadangan stok?",
                            )
                          }
                          className="flex flex-col text-left p-4 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-blue-50/50 hover:border-blue-300 transition-all shadow-2xs group"
                        >
                          <div className="flex items-center justify-between w-full mb-2">
                            <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                              Gudang & Freezer
                            </span>
                            <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                          </div>
                          <p className="text-xs font-medium text-slate-800 line-clamp-2">
                            Periksa ketersediaan stok fisik dan sisa kapasitas
                            ruang pendingin
                          </p>
                        </button>

                        <button
                          onClick={() =>
                            handleSendMessage(
                              "Saya ingin mendaftarkan rekanan baru: CV Berkah Barokah Tahu, komoditas Tahu, harga Rp 18.000 per kg, kapasitas 200 kg per hari, sertifikat Halal ID3211.",
                            )
                          }
                          className="flex flex-col text-left p-4 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-blue-50/50 hover:border-blue-300 transition-all shadow-2xs group"
                        >
                          <div className="flex items-center justify-between w-full mb-2">
                            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                              Rekanan Baru
                            </span>
                            <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                          </div>
                          <p className="text-xs font-medium text-slate-800 line-clamp-2">
                            Daftarkan mitra supplier baru dengan verifikasi pagu
                            SOP otomatis
                          </p>
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Conversation Stream */
                  chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3.5 ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      {msg.role === "assistant" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-700 text-white mt-1">
                          <Bot className="h-4 w-4" />
                        </div>
                      )}

                      <div
                        className={`flex flex-col max-w-2xl ${
                          msg.role === "user" ? "items-end" : "w-full"
                        }`}
                      >
                        {/* Cognitive Execution Stepper / Audit Trace Dropdown (Diletakkan di LUAR dan di ATAS kotak output AI) */}
                        {msg.role === "assistant" &&
                          msg.executionTrace &&
                          msg.executionTrace.length > 0 && (
                            <div className="mb-2.5 rounded-xl border border-blue-200/90 bg-blue-50/70 p-2.5 transition-all text-xs shadow-2xs">
                              <div
                                onClick={() =>
                                  setExpandedTraces((prev) => ({
                                    ...prev,
                                    [idx]: !prev[idx],
                                  }))
                                }
                                className="flex items-center justify-between cursor-pointer select-none text-blue-900 font-semibold gap-2"
                                title="Klik untuk membuka/menutup jejak alur kognitif deterministik"
                              >
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <span className="font-semibold text-xs text-blue-950">
                                    Jejak Kognitif Deterministik (
                                    {msg.executionTrace.length} Tahap Selesai)
                                  </span>
                                  {(() => {
                                    const badge = getTraceBadge(
                                      msg.executionTrace,
                                    );
                                    return (
                                      <span
                                        className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border ${badge.className}`}
                                      >
                                        {badge.icon}
                                        {badge.label}
                                      </span>
                                    );
                                  })()}
                                </div>
                                <div className="flex items-center gap-1 text-[11px] font-medium text-blue-700 hover:text-blue-900 shrink-0">
                                  <span>
                                    {expandedTraces[idx]
                                      ? "Tutup Jejak"
                                      : "Lihat Jejak"}
                                  </span>
                                  <ChevronRight
                                    className={`h-3.5 w-3.5 transition-transform duration-200 ${
                                      expandedTraces[idx] ? "rotate-90" : ""
                                    }`}
                                  />
                                </div>
                              </div>

                              {expandedTraces[idx] && (
                                <div className="mt-2.5 pt-2 border-t border-blue-200/60 space-y-2">
                                  {msg.executionTrace.map((step) => (
                                    <div
                                      key={step.step_number}
                                      className="flex items-start gap-2.5 bg-white/80 rounded-lg p-2 border border-blue-100/80 shadow-2xs"
                                    >
                                      <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white mt-0.5 shadow-2xs">
                                        <CheckCircle2 className="h-3.5 w-3.5" />
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2 flex-wrap">
                                          <span className="font-semibold text-slate-900 text-xs">
                                            {step.step_number}. {step.title}
                                          </span>
                                          <div className="flex items-center gap-1">
                                            <span className="text-[10px] font-mono text-slate-600 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
                                              {step.execution_time_ms} ms
                                            </span>
                                          </div>
                                        </div>
                                        <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                                          {step.details}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                        {/* Kotak Output Utama (Message Bubble) */}
                        <div
                          className={`rounded-2xl p-4 text-sm leading-relaxed ${
                            msg.role === "user"
                              ? "bg-slate-900 text-white rounded-br-xs"
                              : "bg-slate-50 border border-slate-200 text-slate-900 rounded-tl-xs shadow-2xs w-full"
                          }`}
                        >
                          {/* Teks Pesan Terformat (Anti-Slop, Markdown & Bebas Kode LaTeX) */}
                          <FormattedMessage content={msg.text} />

                          {/* Interactive Card: Draf Rekanan Pangan */}
                          {msg.previewData?.draft && (
                            <div className="mt-4 rounded-xl border border-blue-200 bg-white p-3.5 shadow-xs space-y-3">
                              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                                <span className="font-semibold text-xs text-blue-900">
                                  Pratinjau Draf Rekanan Baru
                                </span>
                                <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                                  Halal Terverifikasi
                                </span>
                              </div>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div>
                                  <span className="text-slate-500">
                                    Nama Rekanan:
                                  </span>
                                  <div className="font-medium text-slate-900">
                                    {msg.previewData.draft.supplier_name}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-slate-500">
                                    Komoditas:
                                  </span>
                                  <div className="font-medium text-slate-900">
                                    {msg.previewData.draft.commodity}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-slate-500">
                                    Penawaran Harga:
                                  </span>
                                  <div className="font-mono font-medium text-slate-900">
                                    Rp{" "}
                                    {msg.previewData.draft.unit_price_idr?.toLocaleString(
                                      "id-ID",
                                    )}
                                    /kg
                                  </div>
                                </div>
                                <div>
                                  <span className="text-slate-500">
                                    Kapasitas Harian:
                                  </span>
                                  <div className="font-medium text-slate-900">
                                    {msg.previewData.draft.daily_capacity_kg}{" "}
                                    kg/hari
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2 pt-1">
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      "Setuju, daftarkan rekanan ini.",
                                    )
                                  }
                                  className="flex-1 rounded-lg bg-blue-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-800 transition-colors"
                                >
                                  Otorisasi & Simpan ke Basis Data
                                </button>
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      "Batal, jangan daftarkan.",
                                    )
                                  }
                                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                                >
                                  Batalkan
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Interactive Card: Draf Multi-Item Purchase Order (Perencanaan Menu Bergizi) */}
                          {msg.previewData?.confirm_multi_po && (
                            <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50/50 p-3.5 shadow-xs space-y-3">
                              <div className="flex items-center justify-between border-b border-blue-100 pb-2">
                                <span className="font-semibold text-xs text-blue-950 flex items-center gap-1.5">
                                  <FileText className="h-4 w-4 text-blue-700" />
                                  {msg.previewData.confirm_multi_po.title ||
                                    "Draf Purchase Order Resmi SPPG"}
                                </span>
                                <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-200">
                                  Menunggu Otorisasi
                                </span>
                              </div>

                              <div className="space-y-2">
                                {msg.previewData.confirm_multi_po.po_list?.map(
                                  (po: any, pIdx: number) => (
                                    <div
                                      key={pIdx}
                                      className="rounded-lg border border-slate-200 bg-white p-2.5 text-xs space-y-1"
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="font-semibold text-slate-900">
                                          {po.supplier_name}
                                        </span>
                                        <span className="font-mono text-[11px] font-semibold text-blue-700">
                                          {po.po_number}
                                        </span>
                                      </div>
                                      <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-600 pt-0.5">
                                        <div>
                                          <span className="text-slate-400">
                                            Komoditas:{" "}
                                          </span>
                                          <span className="font-medium text-slate-800">
                                            {po.item_name || po.commodity}
                                          </span>
                                        </div>
                                        <div>
                                          <span className="text-slate-400">
                                            Kuantitas:{" "}
                                          </span>
                                          <span className="font-semibold text-slate-900">
                                            {po.approved_qty_kg} kg
                                          </span>
                                        </div>
                                        <div className="text-right">
                                          <span className="text-slate-400">
                                            Nilai:{" "}
                                          </span>
                                          <span className="font-mono font-semibold text-slate-900">
                                            Rp{" "}
                                            {po.total_amount_idr?.toLocaleString(
                                              "id-ID",
                                            )}
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  ),
                                )}

                                <div className="flex items-center justify-between pt-1 border-t border-blue-100 text-xs">
                                  <span className="font-semibold text-slate-700">
                                    Total Anggaran Pengadaan:
                                  </span>
                                  <span className="font-mono font-bold text-sm text-blue-800">
                                    Rp{" "}
                                    {msg.previewData.confirm_multi_po.total_budget?.toLocaleString(
                                      "id-ID",
                                    )}
                                  </span>
                                </div>

                                {msg.previewData.confirm_multi_po.warning && (
                                  <p className="text-[11px] text-slate-500 font-medium">
                                    ℹ️{" "}
                                    {msg.previewData.confirm_multi_po.warning}
                                  </p>
                                )}
                              </div>

                              <div className="flex items-center gap-2 pt-1">
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      msg.previewData?.confirm_multi_po
                                        ?.confirm_command ||
                                        "Setujui terbitkan seluruh PO pengadaan",
                                    )
                                  }
                                  className="flex-1 rounded-lg bg-blue-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-800 transition-colors shadow-2xs cursor-pointer"
                                >
                                  Setujui & Terbitkan Seluruh PO Resmi
                                </button>
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      msg.previewData?.confirm_multi_po
                                        ?.cancel_command ||
                                        "Batal, jangan terbitkan PO",
                                    )
                                  }
                                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
                                >
                                  Batalkan
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Interactive Card: Penerbitan Multi PO Resmi yang Berhasil Disimpan */}
                          {msg.previewData?.po_results &&
                            Array.isArray(msg.previewData.po_results) && (
                              <div className="mt-4 space-y-2.5">
                                {msg.previewData.po_results.map(
                                  (poItem: any, idx: number) => (
                                    <div
                                      key={idx}
                                      className="rounded-xl border border-emerald-200 bg-white p-3.5 shadow-xs space-y-2.5"
                                    >
                                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                                        <span className="font-semibold text-xs text-emerald-900 flex items-center gap-1.5">
                                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                                          Purchase Order Resmi Diterbitkan #
                                          {idx + 1}
                                        </span>
                                        <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                                          Tersimpan di SQLite
                                        </span>
                                      </div>
                                      <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div>
                                          <span className="text-slate-500">
                                            Nomor Dokumen:
                                          </span>
                                          <div className="font-mono font-semibold text-slate-900">
                                            {poItem.po_number}
                                          </div>
                                        </div>
                                        <div>
                                          <span className="text-slate-500">
                                            Pemasok Terpilih:
                                          </span>
                                          <div className="font-medium text-slate-900">
                                            {poItem.supplier_name}
                                          </div>
                                        </div>
                                        <div>
                                          <span className="text-slate-500">
                                            Total Kuantitas:
                                          </span>
                                          <div className="font-semibold text-slate-900">
                                            {poItem.approved_qty_kg} kg (
                                            {poItem.item_name || poItem.item_id}
                                            )
                                          </div>
                                        </div>
                                        <div>
                                          <span className="text-slate-500">
                                            Nilai Kontrak:
                                          </span>
                                          <div className="font-mono font-semibold text-emerald-700">
                                            Rp{" "}
                                            {poItem.total_amount_idr?.toLocaleString(
                                              "id-ID",
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                      <button
                                        onClick={() =>
                                          setSelectedDoc({
                                            type: "PO",
                                            data: poItem,
                                          })
                                        }
                                        className="w-full rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                                      >
                                        <Printer className="h-3.5 w-3.5" />
                                        Buka Dokumen Resmi & Cetak PDF
                                      </button>
                                    </div>
                                  ),
                                )}
                              </div>
                            )}

                          {/* Interactive Card: Draf PO Tunggal & Mitigasi */}
                          {msg.previewData?.po_result &&
                            !msg.previewData?.po_results && (
                              <div className="mt-4 rounded-xl border border-emerald-200 bg-white p-3.5 shadow-xs space-y-3">
                                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                                  <span className="font-semibold text-xs text-emerald-900">
                                    Dokumen Purchase Order Resmi Diterbitkan
                                  </span>
                                  <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                                    Otorisasi Sah
                                  </span>
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                  <div>
                                    <span className="text-slate-500">
                                      Nomor Dokumen:
                                    </span>
                                    <div className="font-mono font-semibold text-slate-900">
                                      {msg.previewData.po_result.po_number}
                                    </div>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">
                                      Pemasok Terpilih:
                                    </span>
                                    <div className="font-medium text-slate-900">
                                      {msg.previewData.po_result.supplier_name}
                                    </div>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">
                                      Total Kuantitas:
                                    </span>
                                    <div className="font-semibold text-slate-900">
                                      {
                                        msg.previewData.po_result
                                          .approved_qty_kg
                                      }{" "}
                                      kg
                                    </div>
                                  </div>
                                  <div>
                                    <span className="text-slate-500">
                                      Nilai Kontrak:
                                    </span>
                                    <div className="font-mono font-semibold text-emerald-700">
                                      Rp{" "}
                                      {msg.previewData.po_result.total_amount_idr?.toLocaleString(
                                        "id-ID",
                                      )}
                                    </div>
                                  </div>
                                </div>
                                <button
                                  onClick={() => {
                                    setSelectedDoc({
                                      type: "PO",
                                      data: msg.previewData?.po_result,
                                    });
                                  }}
                                  className="w-full rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors flex items-center justify-center gap-1.5"
                                >
                                  <Printer className="h-3.5 w-3.5" />
                                  Buka Dokumen Resmi & Cetak PDF
                                </button>
                              </div>
                            )}

                          {/* Interactive Card: Konfirmasi Penghapusan Dokumen (Human-in-the-Loop) */}
                          {msg.previewData?.confirm_delete && (
                            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50/60 p-3.5 shadow-xs space-y-3">
                              <div className="flex items-center justify-between border-b border-rose-100 pb-2">
                                <span className="font-semibold text-xs text-rose-900 flex items-center gap-1.5">
                                  <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                                  {msg.previewData.confirm_delete.title ||
                                    "Konfirmasi Penghapusan Dokumen"}
                                </span>
                                <span className="rounded-md bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-800 border border-rose-200">
                                  Otorisasi Diperlukan
                                </span>
                              </div>
                              <div className="space-y-1.5 text-xs text-slate-700">
                                <div>
                                  <span className="text-slate-500 font-medium">
                                    Target Dokumen:{" "}
                                  </span>
                                  <span className="font-semibold text-slate-900">
                                    {msg.previewData.confirm_delete.details}
                                  </span>
                                </div>
                                {msg.previewData.confirm_delete.warning && (
                                  <p className="text-[11px] text-rose-700 font-medium">
                                    ⚠️ {msg.previewData.confirm_delete.warning}
                                  </p>
                                )}
                              </div>
                              <div className="flex items-center gap-2 pt-1">
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      msg.previewData?.confirm_delete
                                        ?.confirm_command ||
                                        "Ya, lanjutkan hapus.",
                                    )
                                  }
                                  className="flex-1 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 transition-colors shadow-2xs cursor-pointer"
                                >
                                  Ya, Hapus Permanen
                                </button>
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      msg.previewData?.confirm_delete
                                        ?.cancel_command ||
                                        "Batal, jangan dihapus.",
                                    )
                                  }
                                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
                                >
                                  Batalkan
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Interactive Card: Konfirmasi Pengelolaan Rekanan (Hapus / Nonaktifkan) */}
                          {msg.previewData?.confirm_supplier_action && (
                            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50/70 p-3.5 shadow-xs space-y-3">
                              <div className="flex items-center justify-between border-b border-rose-100 pb-2">
                                <span className="font-semibold text-xs text-rose-900 flex items-center gap-1.5">
                                  <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                                  {msg.previewData.confirm_supplier_action
                                    .title || "Konfirmasi Pengelolaan Rekanan"}
                                </span>
                                <span className="rounded-md bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-800 border border-rose-200">
                                  Otorisasi Diperlukan
                                </span>
                              </div>
                              <div className="space-y-1.5 text-xs text-slate-700">
                                <div>
                                  <span className="text-slate-500 font-medium">
                                    Rekanan:{" "}
                                  </span>
                                  <span className="font-semibold text-slate-900">
                                    {
                                      msg.previewData.confirm_supplier_action
                                        .supplier_name
                                    }{" "}
                                    (
                                    {
                                      msg.previewData.confirm_supplier_action
                                        .supplier_id
                                    }
                                    )
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500 font-medium">
                                    Komoditas:{" "}
                                  </span>
                                  <span className="font-medium text-slate-900">
                                    {
                                      msg.previewData.confirm_supplier_action
                                        .commodity
                                    }
                                  </span>
                                </div>
                                <p className="text-[11px] text-slate-600 font-medium">
                                  {msg.previewData?.confirm_supplier_action
                                    ?.warning ||
                                    "Konfirmasi tindakan pengelolaan rekanan pada basis data SQLite."}
                                </p>
                              </div>
                              <div className="flex flex-wrap items-center gap-2 pt-1">
                                {msg.previewData?.confirm_supplier_action
                                  ?.action_type === "DELETE_PERMANENT" ? (
                                  <button
                                    onClick={() =>
                                      handleSendMessage(
                                        `Hapus permanen rekanan ${msg.previewData?.confirm_supplier_action?.supplier_id}`,
                                      )
                                    }
                                    className="flex-1 min-w-[140px] rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 transition-colors shadow-2xs cursor-pointer"
                                  >
                                    Hapus Permanen (Database)
                                  </button>
                                ) : (
                                  <button
                                    onClick={() =>
                                      handleSendMessage(
                                        `Nonaktifkan rekanan ${msg.previewData?.confirm_supplier_action?.supplier_id}`,
                                      )
                                    }
                                    className="flex-1 min-w-[140px] rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700 transition-colors shadow-2xs cursor-pointer"
                                  >
                                    Nonaktifkan Rekanan (Soft Delete)
                                  </button>
                                )}
                                <button
                                  onClick={() =>
                                    handleSendMessage(
                                      "Batal, jangan lakukan perubahan pada rekanan.",
                                    )
                                  }
                                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
                                >
                                  Batalkan
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {msg.role === "user" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white mt-1">
                          <User className="h-4 w-4" />
                        </div>
                      )}
                    </div>
                  ))
                )}

                {isSending && (
                  <div className="flex gap-3.5 justify-start">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-700 text-white mt-1">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col max-w-2xl w-full">
                      {/* Live Cognitive Stepper Container (Animasi Checklist Vertikal Saat Agen Berpikir) */}
                      <div className="rounded-2xl border border-blue-200 bg-white p-4 shadow-2xs space-y-3">
                        <div className="flex items-center justify-between border-b border-blue-100 pb-2.5">
                          <div className="flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-blue-600 animate-pulse" />
                            <span className="font-semibold text-xs text-blue-950">
                              Resilio Cognitive Engine — Eksekusi Pipeline
                              Multi-Tahap
                            </span>
                          </div>
                          <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                            <span className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
                            </span>
                            Tahap {liveStep} dari 5
                          </span>
                        </div>

                        {/* Checklist Vertikal Berjenjang */}
                        <div className="space-y-2">
                          {LIVE_PIPELINE_STEPS.map((step) => {
                            const isCompleted = step.number < liveStep;
                            const isCurrent = step.number === liveStep;

                            return (
                              <div
                                key={step.number}
                                className={`flex items-start gap-2.5 p-2 rounded-xl transition-all duration-300 ${
                                  isCurrent
                                    ? "bg-blue-50/80 border border-blue-300/80 shadow-2xs"
                                    : isCompleted
                                      ? "bg-slate-50/70 border border-slate-200/70"
                                      : "opacity-45 border border-transparent"
                                }`}
                              >
                                {isCompleted ? (
                                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white mt-0.5 shadow-2xs">
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                  </div>
                                ) : isCurrent ? (
                                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white mt-0.5 shadow-2xs">
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  </div>
                                ) : (
                                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-white text-[10px] font-bold text-slate-400 mt-0.5">
                                    {step.number}
                                  </div>
                                )}

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between gap-2">
                                    <span
                                      className={`text-xs ${
                                        isCurrent
                                          ? "font-bold text-blue-950"
                                          : isCompleted
                                            ? "font-semibold text-slate-800"
                                            : "font-medium text-slate-400"
                                      }`}
                                    >
                                      {step.number}. {step.title}
                                    </span>
                                    {isCompleted && (
                                      <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                                        Selesai
                                      </span>
                                    )}
                                    {isCurrent && (
                                      <span className="text-[10px] font-medium text-blue-700 bg-blue-100/70 px-1.5 py-0.5 rounded border border-blue-200 animate-pulse">
                                        Memproses...
                                      </span>
                                    )}
                                  </div>
                                  <p
                                    className={`text-[11px] mt-0.5 leading-relaxed ${
                                      isCurrent
                                        ? "text-blue-900/80"
                                        : isCompleted
                                          ? "text-slate-500"
                                          : "text-slate-400"
                                    }`}
                                  >
                                    {step.description}
                                  </p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Bottom Floating Input Bar (Gemini Style) */}
            <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent">
              <div className="max-w-3xl mx-auto">
                {/* 1-Click Interactive Demo Chips (GTNIC 2026 Live Pitching Bar) */}
                <div className="mb-2.5 flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 shrink-0 flex items-center gap-1 pl-1">
                    Skenario Demo:
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      handleSendMessage(
                        "Armada supplier ayam utama PT Unggas Sejahtera Nusantara terjebak banjir di jalur Pantura, tolong segera mitigasi darurat dan carikan alternatif halal.",
                      )
                    }
                    disabled={isSending}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50/80 px-2.5 py-1 text-[11px] font-semibold text-rose-800 hover:bg-rose-100 hover:border-rose-300 transition-all cursor-pointer shadow-2xs disabled:opacity-50"
                    title="Klik untuk langsung mensimulasikan insiden banjir & mitigasi darurat"
                  >
                    <AlertTriangle className="h-3 w-3 text-rose-600" />
                    <span>🚨 Banjir Pantura</span>
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleSendMessage(
                        "Bantu susun draf PO untuk pengadaan menu 3000 porsi ayam dan telur hari ini",
                      )
                    }
                    disabled={isSending}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-[11px] font-semibold text-blue-800 hover:bg-blue-100 hover:border-blue-300 transition-all cursor-pointer shadow-2xs disabled:opacity-50"
                    title="Klik untuk langsung menyusun perencanaan 3000 porsi ayam + telur"
                  >
                    <FileText className="h-3 w-3 text-blue-600" />
                    <span>🍲 Rencana 3000 Porsi</span>
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleSendMessage(
                        "Tolong daftarkan supplier baru UD Sapi Segar Jaya, komoditas daging Sapi, harga Rp 44.000 per kg, kapasitas harian 200 kg, jarak 12 km, halal aktif nomor sertifikat ID-HALAL-2026-0088",
                      )
                    }
                    disabled={isSending}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50/80 px-2.5 py-1 text-[11px] font-semibold text-amber-800 hover:bg-amber-100 hover:border-amber-300 transition-all cursor-pointer shadow-2xs disabled:opacity-50"
                    title="Klik untuk menguji validasi multi-turn pendaftaran rekanan baru"
                  >
                    <Plus className="h-3 w-3 text-amber-600" />
                    <span>📝 Uji Daftar Rekanan</span>
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleSendMessage(
                        "Cek sisa stok bahan baku dan kapasitas freezer gudang SPPG",
                      )
                    }
                    disabled={isSending}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50/80 px-2.5 py-1 text-[11px] font-semibold text-emerald-800 hover:bg-emerald-100 hover:border-emerald-300 transition-all cursor-pointer shadow-2xs disabled:opacity-50"
                    title="Klik untuk kueri langsung stok & kapasitas cold chain SQLite ACID"
                  >
                    <Warehouse className="h-3 w-3 text-emerald-600" />
                    <span>❄️ Audit Rantai Dingin</span>
                  </button>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white px-4 py-2.5 shadow-sm focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-100 transition-all"
                >
                  <textarea
                    ref={textareaRef}
                    rows={1}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (inputMessage.trim() && !isSending) {
                          handleSendMessage();
                        }
                      }
                    }}
                    placeholder="Tanyakan status inventaris, laporkan insiden, atau beri instruksi..."
                    disabled={isSending}
                    className="flex-1 max-h-[140px] resize-none overflow-y-auto bg-transparent py-1 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none leading-relaxed"
                  />
                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || isSending}
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-700 text-white hover:bg-blue-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors self-end mb-0.5"
                    title="Kirim Instruksi (Enter untuk kirim, Shift+Enter untuk baris baru)"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </form>
                <div className="text-center mt-2 text-[11px] text-slate-400">
                  Resilio AI memproses keputusan dengan Matrix 7 Parameter
                  Deterministik & Transparansi Regulasi BGN.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===================================================================
            VIEW 2: ARSIP SURAT EDARAN & PURCHASE ORDER
            =================================================================== */}
        {activeTab === "circular_letters" && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  Arsip Dokumen Resmi & Purchase Order SPPG
                </h2>
                <p className="text-sm text-slate-500">
                  Daftar seluruh Surat Edaran penetapan mitigasi darurat dan
                  surat pesanan yang telah diotorisasi.
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 border border-slate-200">
                <button
                  onClick={() => setDocumentFilter("ALL")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    documentFilter === "ALL"
                      ? "bg-white text-slate-900 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Semua ({circularLetters.length + purchaseOrders.length})
                </button>
                <button
                  onClick={() => setDocumentFilter("SE")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    documentFilter === "SE"
                      ? "bg-white text-slate-900 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Surat Edaran ({circularLetters.length})
                </button>
                <button
                  onClick={() => setDocumentFilter("PO")}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    documentFilter === "PO"
                      ? "bg-white text-slate-900 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Purchase Order ({purchaseOrders.length})
                </button>
              </div>
            </div>

            {/* Search Bar Dokumen */}
            <div className="relative max-w-md">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Cari nomor surat, rekanan, atau perihal..."
                value={searchDocQuery}
                onChange={(e) => setSearchDocQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>

            {/* Grid Dokumen Surat Edaran */}
            {(documentFilter === "ALL" || documentFilter === "SE") && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-700" />
                  <span>Surat Edaran Mitigasi (SE)</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {circularLetters
                    .filter(
                      (se) =>
                        se.title
                          .toLowerCase()
                          .includes(searchDocQuery.toLowerCase()) ||
                        se.letter_number
                          .toLowerCase()
                          .includes(searchDocQuery.toLowerCase()) ||
                        (se.supplier_name &&
                          se.supplier_name
                            .toLowerCase()
                            .includes(searchDocQuery.toLowerCase())),
                    )
                    .map((se) => (
                      <div
                        key={se.letter_id}
                        className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-blue-300 transition-all flex flex-col justify-between space-y-4"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-blue-800 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                              {se.letter_number}
                            </span>
                            <span className="text-xs text-slate-400 font-mono">
                              {se.issued_date}
                            </span>
                          </div>
                          <h4 className="font-semibold text-sm text-slate-900 leading-snug">
                            {se.title}
                          </h4>
                          <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                            {se.content_text}
                          </p>
                        </div>

                        <div className="border-t border-slate-100 pt-3 flex items-center justify-between">
                          <div className="text-xs text-slate-500">
                            Pemasok:{" "}
                            <strong className="text-slate-700">
                              {se.supplier_name || "-"}
                            </strong>
                          </div>
                          <button
                            onClick={() =>
                              setSelectedDoc({ type: "SE", data: se })
                            }
                            className="rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors flex items-center gap-1.5"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            Lihat Lembar Resmi
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Grid Dokumen Purchase Order */}
            {(documentFilter === "ALL" || documentFilter === "PO") && (
              <div className="space-y-3 pt-4">
                <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                  <Printer className="h-4 w-4 text-emerald-700" />
                  <span>Surat Pesanan / Purchase Order (PO)</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {purchaseOrders
                    .filter(
                      (po) =>
                        po.po_number
                          .toLowerCase()
                          .includes(searchDocQuery.toLowerCase()) ||
                        (po.supplier_name &&
                          po.supplier_name
                            .toLowerCase()
                            .includes(searchDocQuery.toLowerCase())),
                    )
                    .map((po) => (
                      <div
                        key={po.po_number}
                        className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-emerald-300 transition-all flex flex-col justify-between space-y-4"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                              {po.po_number}
                            </span>
                            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                              {po.status}
                            </span>
                          </div>
                          <div className="text-sm font-semibold text-slate-900">
                            Pesanan Pasokan: {po.item_id} ({po.approved_qty_kg}{" "}
                            kg)
                          </div>
                          <div className="text-xs text-slate-600 space-y-1">
                            <div>
                              Rekanan: <strong>{po.supplier_name}</strong>
                            </div>
                            <div>
                              Nilai Kontrak:{" "}
                              <strong className="font-mono text-emerald-700">
                                Rp{" "}
                                {po.total_amount_idr?.toLocaleString("id-ID")}
                              </strong>
                            </div>
                          </div>
                        </div>

                        <div className="border-t border-slate-100 pt-3 flex items-center justify-between">
                          <span className="text-[11px] text-slate-400 font-mono">
                            Otorisator: {po.approver_name}
                          </span>
                          <button
                            onClick={() =>
                              setSelectedDoc({ type: "PO", data: po })
                            }
                            className="rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition-colors flex items-center gap-1.5"
                          >
                            <Printer className="h-3.5 w-3.5" />
                            Lembar PO & Cetak
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===================================================================
            VIEW 3: KATALOG REKANAN SUPPLIER
            =================================================================== */}
        {activeTab === "suppliers" && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6">
            <div className="border-b border-slate-200 pb-5">
              <h2 className="text-xl font-bold text-slate-900">
                Katalog Rekanan Pemasok Bahan Pangan SPPG
              </h2>
              <p className="text-sm text-slate-500">
                Data mitra supplier terverifikasi sertifikasi Halal BPJPH dan
                kepatuhan pagu SOP.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {suppliers.map((sup) => (
                <div
                  key={sup.supplier_id}
                  className={`rounded-2xl border p-5 shadow-xs flex flex-col justify-between space-y-4 ${
                    sup.is_active === false
                      ? "border-dashed border-slate-300 bg-slate-50/75 opacity-75"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {sup.supplier_id}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {sup.is_active === false ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 border border-slate-300">
                            <AlertTriangle className="h-3 w-3 text-slate-400" />
                            Non-Aktif
                          </span>
                        ) : sup.halal_certified ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            Halal Aktif
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700 border border-rose-200">
                            <AlertTriangle className="h-3 w-3" />
                            Tanpa Sertifikat
                          </span>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-slate-900">
                        {sup.supplier_name}
                      </h4>
                      <span className="text-xs text-blue-700 font-medium">
                        Komoditas: {sup.commodity}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-600">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Harga Satuan:</span>
                        <span className="font-mono font-semibold text-slate-900">
                          Rp {sup.unit_price_idr?.toLocaleString("id-ID")}/kg
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">
                          Kapasitas Harian:
                        </span>
                        <span className="font-medium text-slate-900">
                          {sup.daily_capacity_kg} kg/hari
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">
                          Waktu Kirim & Jarak:
                        </span>
                        <span className="font-medium text-slate-900">
                          {sup.lead_time_hours} jam ({sup.distance_km} km)
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-100 pt-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-500">Skor Keandalan:</span>
                      <span className="font-bold text-blue-700">
                        {sup.reliability_rating}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-blue-600 h-full rounded-full"
                        style={{ width: `${sup.reliability_rating}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===================================================================
            VIEW 4: MONITORING STOK GUDANG & FREEZER
            =================================================================== */}
        {activeTab === "inventory" && (
          <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-6">
            <div className="border-b border-slate-200 pb-5">
              <h2 className="text-xl font-bold text-slate-900">
                Monitoring Stok Gudang & Kapasitas Ruang Pendingin
              </h2>
              <p className="text-sm text-slate-500">
                Pemantauan fisik stok bahan pangan dan kesiapan ruang
                penyimpanan dingin SPPG.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {inventory.map((item) => {
                const stockPercent = Math.min(
                  100,
                  Math.round(
                    (item.current_stock_kg / (item.safety_stock_kg * 3)) * 100,
                  ),
                );
                const freezerPercent =
                  item.freezer_capacity_kg > 0
                    ? Math.round(
                        (item.freezer_occupied_kg / item.freezer_capacity_kg) *
                          100,
                      )
                    : 0;

                return (
                  <div
                    key={item.item_id}
                    className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {item.item_id}
                      </span>
                      <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                        {item.category}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-slate-900">
                        {item.item_name}
                      </h4>
                      <div className="text-xs text-slate-500 font-mono">
                        Pagu Maks SOP: Rp{" "}
                        {item.sop_max_price_per_kg?.toLocaleString("id-ID")}/kg
                      </div>
                    </div>

                    {/* Bar Stok Fisik */}
                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Stok Gudang:</span>
                        <span className="font-semibold text-slate-900">
                          {item.current_stock_kg} kg (Batas Aman:{" "}
                          {item.safety_stock_kg} kg)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            item.current_stock_kg <= item.safety_stock_kg
                              ? "bg-rose-600"
                              : "bg-emerald-600"
                          }`}
                          style={{ width: `${stockPercent}%` }}
                        />
                      </div>
                    </div>

                    {/* Bar Freezer (jika ada) */}
                    {item.freezer_capacity_kg > 0 && (
                      <div className="space-y-1.5 text-xs border-t border-slate-100 pt-3">
                        <div className="flex justify-between">
                          <span className="text-slate-500">
                            Ruang Dingin (Freezer):
                          </span>
                          <span className="font-medium text-slate-700">
                            {item.freezer_occupied_kg} /{" "}
                            {item.freezer_capacity_kg} kg ({freezerPercent}%)
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              freezerPercent >= 80
                                ? "bg-amber-500"
                                : "bg-blue-600"
                            }`}
                            style={{ width: `${freezerPercent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ===================================================================
            MODAL DOKUMEN RESMI (KOP SURAT SPPG & PRINT ACTION)
            =================================================================== */}
        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
            <div className="relative w-full max-w-2xl rounded-2xl bg-white p-8 shadow-2xl overflow-y-auto max-h-[90vh]">
              {/* Tombol Tutup */}
              <button
                onClick={() => setSelectedDoc(null)}
                className="absolute right-5 top-5 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Kop Surat Resmi */}
              <div className="text-center border-b-2 border-slate-900 pb-4 mb-6 space-y-1">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-700">
                  BADAN GIZI NASIONAL REPUBLIK INDONESIA
                </div>
                <div className="text-base font-extrabold uppercase tracking-tight text-slate-950">
                  SATUAN PELAYANAN PEMENUHAN GIZI (SPPG) WILAYAH I
                </div>
                <div className="text-[11px] text-slate-500">
                  Jalan Raya Sukabumi No. 42, Jawa Barat | Layanan Darurat
                  Pangan: (0266) 554321
                </div>
              </div>

              {/* Lembar Dokumen Surat Edaran */}
              {selectedDoc.type === "SE" && (
                <div className="space-y-4 text-xs leading-relaxed text-slate-800">
                  <div className="text-center space-y-1 pb-2">
                    <div className="font-bold text-sm uppercase text-slate-950 underline">
                      SURAT EDARAN KEPALA SPPG
                    </div>
                    <div className="font-mono text-slate-600">
                      Nomor: {selectedDoc.data.letter_number}
                    </div>
                    <div className="font-semibold text-slate-800">
                      TENTANG: {selectedDoc.data.title.toUpperCase()}
                    </div>
                  </div>

                  <p className="text-justify indent-6">
                    {selectedDoc.data.content_text}
                  </p>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
                    <div className="font-semibold text-slate-900">
                      Rincian Alokasi Pasokan Mitigasi:
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        ID Bahan:{" "}
                        <strong>{selectedDoc.data.item_id || "-"}</strong>
                      </div>
                      <div>
                        Defisit Ditanggulangi:{" "}
                        <strong>{selectedDoc.data.deficit_kg || 0} kg</strong>
                      </div>
                      <div>
                        Rekanan Ditunjuk:{" "}
                        <strong>{selectedDoc.data.supplier_name || "-"}</strong>
                      </div>
                      <div>
                        Status Regulasi:{" "}
                        <strong className="text-emerald-700">
                          Terverifikasi Halal BPJPH
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="pt-8 flex justify-end">
                    <div className="text-center space-y-12">
                      <div>
                        Sukabumi, {selectedDoc.data.issued_date}
                        <br />
                        <strong>Kepala SPPG Wilayah I</strong>
                      </div>
                      <div className="font-bold underline text-slate-950">
                        {selectedDoc.data.signer_name ||
                          "Bapak Adam Dzaki, S.T., M.M."}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Lembar Dokumen Purchase Order */}
              {selectedDoc.type === "PO" && (
                <div className="space-y-4 text-xs leading-relaxed text-slate-800">
                  <div className="text-center space-y-1 pb-2">
                    <div className="font-bold text-sm uppercase text-slate-950 underline">
                      SURAT PESANAN RESMI (PURCHASE ORDER)
                    </div>
                    <div className="font-mono text-slate-600">
                      Nomor PO: {selectedDoc.data.po_number}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 border border-slate-200 rounded-xl p-3 bg-slate-50">
                    <div>
                      Pemasok: <strong>{selectedDoc.data.supplier_name}</strong>
                    </div>
                    <div>
                      Komoditas: <strong>{selectedDoc.data.item_id}</strong>
                    </div>
                    <div>
                      Volume Total:{" "}
                      <strong>{selectedDoc.data.approved_qty_kg} kg</strong>
                    </div>
                    <div>
                      Harga Satuan:{" "}
                      <strong>
                        Rp{" "}
                        {selectedDoc.data.unit_price_idr?.toLocaleString(
                          "id-ID",
                        )}
                        /kg
                      </strong>
                    </div>
                    <div className="col-span-2 text-sm font-bold text-emerald-800 pt-1 border-t border-slate-200">
                      Total Nilai Kontrak: Rp{" "}
                      {selectedDoc.data.total_amount_idr?.toLocaleString(
                        "id-ID",
                      )}
                    </div>
                  </div>

                  {selectedDoc.data.logistics_strategy?.batches && (
                    <div className="space-y-2">
                      <div className="font-semibold text-slate-900">
                        Jadwal Distribusi Bertahap (Split Delivery):
                      </div>
                      <div className="space-y-1">
                        {selectedDoc.data.logistics_strategy.batches.map(
                          (b: any) => (
                            <div
                              key={b.batch_no}
                              className="flex items-center justify-between border border-slate-100 rounded-lg p-2 bg-white"
                            >
                              <span>
                                Batch #{b.batch_no} ({b.qty_kg} kg)
                              </span>
                              <span className="font-mono text-slate-500">
                                Estimasi Tiba: {b.eta}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                  )}

                  <div className="pt-8 flex justify-end">
                    <div className="text-center space-y-12">
                      <div>
                        Ditetapkan oleh:
                        <br />
                        <strong>Kepala Satuan Pelayanan Pemenuhan Gizi</strong>
                      </div>
                      <div className="font-bold underline text-slate-950">
                        {selectedDoc.data.approver_name ||
                          "Bapak Adam Dzaki, S.T., M.M."}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-8 border-t border-slate-200 pt-4 flex items-center justify-end gap-3">
                <button
                  onClick={() => window.print()}
                  className="rounded-xl bg-blue-700 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-800 transition-colors flex items-center gap-2"
                >
                  <Printer className="h-4 w-4" />
                  Cetak Dokumen / Unduh PDF
                </button>
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Tutup
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ===================================================================
            MODAL RINGKASAN EKSEKUTIF & DAMPAK BISNIS (ENTERPRISE ROI BRIEFING)
            =================================================================== */}
        {isRoiModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
            <div className="relative w-full max-w-2xl rounded-2xl bg-white p-6 md:p-8 shadow-2xl overflow-y-auto max-h-[92vh] border border-slate-100">
              {/* Tombol Tutup Silang di Kanan Atas */}
              <button
                type="button"
                onClick={() => setIsRoiModalOpen(false)}
                className="absolute right-5 top-5 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
                title="Tutup Ringkasan"
              >
                <X className="h-5 w-5" />
              </button>

              {/* Header Modal */}
              <div className="space-y-2 border-b border-slate-100 pb-5">
                <h2 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">
                  ResilioAI: Dampak Bisnis
                </h2>
                <p className="text-xs md:text-sm text-slate-600 leading-relaxed">
                  Sistem agen kognitif hibrida yang mentransformasi mitigasi
                  disrupsi logistik bahan pangan segar SPPG menjadi instan,
                  deterministik, dan patuh regulasi nasional.
                </p>
              </div>

              {/* 4 Pilar Metrik ROI Utama (Enterprise Metrics Grid) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 my-6">
                {/* Metrik 1: Efisiensi Waktu */}
                <div className="rounded-xl border border-emerald-200/90 bg-gradient-to-br from-emerald-50/70 to-emerald-100/30 p-4 shadow-2xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-950 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-emerald-600" />
                      Efisiensi Waktu Tanggap
                    </span>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full border border-emerald-200">
                      99.2% Lebih Cepat
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-emerald-900 tracking-tight">
                    &lt; 2 Menit
                  </div>
                  <p className="text-[11px] text-emerald-800/80 leading-relaxed">
                    Memangkas siklus mitigasi krisis rantai pasok manual dari{" "}
                    <strong>4–6 jam</strong> via telepon menjadi hitungan detik
                    tanpa risiko keterlambatan jam makan bergizi.
                  </p>
                </div>

                {/* Metrik 2: Kepatuhan Halal Mutlak */}
                <div className="rounded-xl border border-blue-200/90 bg-gradient-to-br from-blue-50/70 to-blue-100/30 p-4 shadow-2xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-blue-950 flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
                      Integritas Halal Mutlak
                    </span>
                    <span className="text-[10px] font-bold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-full border border-blue-200">
                      UU JPH No. 33/2014
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-blue-900 tracking-tight">
                    100% Terverifikasi
                  </div>
                  <p className="text-[11px] text-blue-800/80 leading-relaxed">
                    Filter deterministik mengeliminasi secara mutlak rekanan
                    non-halal. Hanya supplier ber-ID sertifikat BPJPH resmi yang
                    dapat diterbitkan PO-nya.
                  </p>
                </div>

                {/* Metrik 3: Pengendalian Anggaran SOP */}
                <div className="rounded-xl border border-indigo-200/90 bg-gradient-to-br from-indigo-50/70 to-indigo-100/30 p-4 shadow-2xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-indigo-950 flex items-center gap-1.5">
                      <Boxes className="h-3.5 w-3.5 text-indigo-600" />
                      Tata Kelola Anggaran SOP
                    </span>
                    <span className="text-[10px] font-bold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded-full border border-indigo-200">
                      Pagu Aman BGN
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-indigo-900 tracking-tight">
                    Rp 0 Overbudget
                  </div>
                  <p className="text-[11px] text-indigo-800/80 leading-relaxed">
                    Sistem otomatis memvalidasi penawaran harga terhadap pagu
                    biaya masukan Badan Gizi Nasional untuk mencegah
                    pembengkakan anggaran saat pengadaan darurat.
                  </p>
                </div>

                {/* Metrik 4: Keandalan Data & AI Tanpa Halusinasi */}
                <div className="rounded-xl border border-amber-200/90 bg-gradient-to-br from-amber-50/70 to-amber-100/30 p-4 shadow-2xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-amber-950 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-amber-600" />
                      Arsitektur Kognitif Sah
                    </span>
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded-full border border-amber-200">
                      Human-in-the-Loop
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-amber-900 tracking-tight">
                    0% Halusinasi Numerik
                  </div>
                  <p className="text-[11px] text-amber-800/80 leading-relaxed">
                    Kalkulasi defisit riil dan skoring kelayakan 7 parameter
                    diproses deterministik via SQLite ACID, dengan gerbang
                    pengesahan wajib oleh Kepala SPPG.
                  </p>
                </div>
              </div>

              {/* Komparasi Singkat Operasional (Before vs After) */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-2 text-xs">
                <span className="font-semibold text-slate-800 block text-[11px] uppercase tracking-wider">
                  Komparasi Nilai Operasional SPPG:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-600 text-[11px]">
                  <div className="flex items-start gap-2 bg-white rounded-lg p-2.5 border border-slate-200/70">
                    <span className="text-rose-500 font-bold shrink-0">✕</span>
                    <div>
                      <strong className="text-slate-800">
                        Operasional Manual:
                      </strong>{" "}
                      4–6 jam via telepon, rawan kecolongan supplier non-halal,
                      risiko mark-up anggaran saat darurat.
                    </div>
                  </div>
                  <div className="flex items-start gap-2 bg-white rounded-lg p-2.5 border border-blue-200/80">
                    <span className="text-emerald-600 font-bold shrink-0">
                      ✓
                    </span>
                    <div>
                      <strong className="text-slate-900">
                        Dengan Resilio AI:
                      </strong>{" "}
                      &lt; 2 menit penyelesaian krisis, 100% kepatuhan regulasi,
                      draf PO multi-item terverifikasi otomatis.
                    </div>
                  </div>
                </div>
              </div>

              {/* Catatan Lingkungan Simulasi (Synthetic Sandbox Disclaimer) */}
              <div className="mt-3.5 rounded-xl border border-amber-200/90 bg-amber-50/70 p-3 text-xs flex items-start gap-2.5">
                <Info className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" />
                <div className="space-y-0.5 text-[11px] leading-relaxed text-amber-900">
                  <span className="font-semibold text-amber-950 block">
                    Catatan Lingkungan Simulasi (Synthetic Sandbox Environment):
                  </span>
                  <p className="text-amber-900/90">
                    Seluruh entitas rekanan, nomor registrasi halal, dan
                    inventaris gudang pada sistem ini menggunakan data simulasi
                    sintetis yang dikalibrasi presisi sesuai standar pagu Badan
                    Gizi Nasional (BGN) & UU JPH No. 33/2014 demi kepatuhan
                    etika data dan pengujian operasional yang aman.
                  </p>
                </div>
              </div>

              {/* Footer Modal: Tombol Tunggal "Mulai Uji Coba Simulasi" */}
              <div className="mt-6 border-t border-slate-100 pt-4 flex items-center justify-end">
                <button
                  type="button"
                  onClick={handleStartSimulation}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-blue-700 px-6 py-2.5 text-xs md:text-sm font-semibold text-white shadow-md hover:bg-blue-800 transition-all cursor-pointer"
                >
                  <span>Mulai Uji Coba Simulasi</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
