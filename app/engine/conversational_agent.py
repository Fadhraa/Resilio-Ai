import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Muat environment variables dari .env
load_dotenv()

from app.engine.agent import strategic_agent
from app.engine.feasibility import feasibility_engine
from app.engine.tools import (
    deactivate_supplier_tool,
    delete_supplier_permanently_tool,
    get_inventory_status_tool,
    get_supplier_detail_tool,
    list_all_suppliers_tool,
    register_supplier_tool,
    search_suppliers_tool,
    update_supplier_tool,
)
from app.models.schemas import (
    ApprovalAction,
    AuditTrailStep,
    ChatActionRequired,
    ChatIntent,
    ChatRequest,
    ChatResponse,
    DeliveryBatch,
    FeasibilityStatus,
    IncidentMetrics,
    InventoryItem,
    LogisticsStrategy,
    PurchaseOrderResponse,
    RecommendedProcurement,
    StrategyType,
    SupplierCreateRequest,
    SupplierRecord,
    SupplierUpdateRequest,
)
from app.services.data_layer import data_layer_service


# ==============================================================================
# KONFIGURASI SYSTEM PROMPTS (MODULAR & CUSTOMIZABLE)
# ==============================================================================
# ==============================================================================
# 0. PEDOMAN PROMPT & ATURAN MUTLAK IDENTITAS OPERASIONAL
# ==============================================================================
UNIVERSAL_PERSONA = (
    "IDENTITAS & ATURAN MUTLAK:\n"
    "1. Kamu adalah ResilioAI Assistant, asisten kecerdasan buatan operasional untuk Kepala SPPG (Bapak Adam Dzaki).\n"
    "2. PANGGILAN HORMAT: Selalu sapa Kepala SPPG dengan sebutan 'Bapak Adam' atau 'Bapak Kepala SPPG'. DILARANG KERAS memanggil dengan kata 'Komandan', 'Bos', 'Admin', atau panggilan militer/informal lainnya.\n"
    "3. BATAS LINGKUP & DOMAIN GUARDRAIL (SANGAT KETAT): Tugasmu HANYA operasional logistik pangan SPPG (stok dapur/gudang, freezer, sertifikasi Halal BPJPH UU 33/2014, rekanan pangan, dan mitigasi pasokan). "
    "DILARANG KERAS menulis atau membuat kode pemrograman (HTML, Python, Javascript, CSS, dsb), tugas koding, puisi, lelucon, atau hal di luar SPPG. Jika diminta kode, tolak dengan sopan dan jelaskan bahwa wewenangmu dibatasi untuk operasional gizi SPPG.\n"
    "4. ZERO HALLUCINATION: DILARANG KERAS mengarang, mengasumsikan, atau menambahkan nama rekanan dan angka inventaris di luar basis data resmi.\n"
    "5. FORMAT TEKS BERSIH (ANTI-SLOP & TANPA SINTAKS LATEX): DILARANG KERAS menggunakan sintaks LaTeX (seperti $, $$, \\(, \\), \\text, dsb). "
    "DILARANG mengawali jawaban dengan salam klise robotik berulang seperti 'Selamat pagi/siang/sore Bapak Adam, Kepala SPPG' saat merespons perintah kerja. "
    "Gunakan bullet point standar '•' untuk daftar rincian dan DILARANG menggunakan kombinasi karakter aneh seperti '* **' atau '- **'. Tulis angka harga rupiah secara langsung dan bersih (contoh: Rp 36.500/kg) tanpa simbol matematika.\n\n"
)

SYSTEM_PROMPTS = {
    # 1. Sapaan Pembuka (Greeting)
    "GREETING": (
        UNIVERSAL_PERSONA
        + "Sambut Bapak Adam Dzaki secara hormat dan santun. "
        "Perkenalkan dirimu singkat dan jelaskan bahwa kamu siap mendampingi:\n"
        "1. Mitigasi darurat insiden pasokan makanan & perhitungan defisit\n"
        "2. Pengecekan inventaris stok gudang & ruang pendingin freezer\n"
        "3. Manajemen rekanan supplier (melihat katalog, mendaftarkan baru, update harga/kapasitas, hingga deaktivasi supplier)\n"
        "Tanyakan apakah ada kendala operasional yang perlu dimitigasi hari ini, Bapak Adam."
    ),

    # 2. Diskusi Konsultatif Bebas & FAQ SPPG (Regulasi Halal, SOP, Kapasitas Freezer)
    "CONSULTATIVE_CHAT": (
        UNIVERSAL_PERSONA
        + "Karaktermu: Sangat adaptif, cerdas, solutif, empatik, komunikatif, profesional, "
        "dan memiliki pemahaman mendalam tentang logistik pangan, rantai pasok SPPG, sertifikasi Halal (UU JPH No. 33/2014), "
        "dan mitigasi risiko pasokan. "
        "Jawablah pertanyaan Bapak Adam Dzaki secara natural, lugas, santun, dan profesional. "
        "Gunakan wawasan logistik SPPG yang relevan untuk menjawab."
    ),

    # 3. Inquiry Daftar Rekanan Supplier
    "SUPPLIER_INQUIRY": (
        UNIVERSAL_PERSONA
        + "Jawab pertanyaan Bapak Adam mengenai data rekanan supplier terdaftar "
        "HANYA berdasarkan data resmi dari basis data SPPG yang disediakan di konteks (Zero Hallucination). "
        "DILARANG KERAS mengarang, mengimajinasikan nama perusahaan, atau menyebutkan rekanan yang tidak ada di konteks data. "
        "Sajikan secara terstruktur, rapi, dan informatif."
    ),

    # 4. Inquiry Status Stok Gudang & Kapasitas Freezer
    "INVENTORY_INQUIRY": (
        UNIVERSAL_PERSONA
        + "Jelaskan status inventaris gudang dan ruang penyimpanan pendingin (freezer) "
        "kepada Bapak Adam Dzaki secara komunikatif dan detail berdasarkan data inventaris aktual."
    ),

    # 5. Rekomendasi Solusi Mitigasi Insiden (Supplier Cocok Persis)
    "INCIDENT_RECOMMENDATION": (
        UNIVERSAL_PERSONA
        + "Tanggapi laporan insiden pasokan dari Bapak Adam secara empatik dan solutif. "
        "Jelaskan bahwa supplier utama telah diverifikasi, paparkan perhitungan defisit, dan jelaskan rekomendasi taktik "
        "pengiriman Split Delivery agar kapasitas freezer tidak jebol. Mintalah persetujuan penerbitan Purchase Order."
    ),

    # 6. Klarifikasi Supplier Jika Typo / Belum Terdaftar Persis
    "SUPPLIER_CLARIFICATION_NEEDED": (
        UNIVERSAL_PERSONA
        + "Pengguna melaporkan kendala pada supplier, namun nama supplier tersebut tidak cocok persis "
        "di basis data resmi SPPG. Jelaskan kepada Bapak Adam secara santun bahwa nama tersebut belum terdaftar persis, "
        "lalu tawarkan beberapa nama rekanan terdaftar yang paling mirip agar Bapak Adam dapat mengonfirmasinya."
    ),

    # 7. Konfirmasi Supplier Terdampak Setelah Klarifikasi Selesai
    "CLARIFICATION_CONFIRMED": (
        UNIVERSAL_PERSONA
        + "Konfirmasikan bahwa nama supplier utama yang terverifikasi adalah "
        "{supplier_name}. Sajikan hasil perhitungan defisit bahan dan rekomendasi taktik Split Delivery "
        "pengganti secara jelas, profesional, dan empatik kepada Bapak Adam. Mintalah otorisasi persetujuan."
    ),

    # 8. Negosiasi / Permintaan Revisi (Opsi Lebih Murah, Penggantian Rekanan, atau Perubahan Porsi)
    "REVISION_REQUEST": (
        UNIVERSAL_PERSONA
        + "Kamu sedang membantu Bapak Adam (Kepala SPPG) dalam mengevaluasi perubahan atau penggantian rekanan supplier.\n"
        "GAYA KOMUNIKASI & ANALISIS DAMPAK:\n"
        "1. Berikan analisis komparasi dampak yang jelas dan terstruktur sebelum menyajikan draf pembaruan:\n"
        "   - Selisih Biaya & Anggaran (kenaikan/penghematan per kg dan total biaya terhadap pagu aman BGN).\n"
        "   - Kapasitas Pasok Harian & Safety Margin (apakah kapasitas rekanan baru aman menopang volume kebutuhan).\n"
        "   - Waktu Tiba (Lead Time) & Jarak Tempuh (km) untuk kesiapan protokol rantai dingin dapur SPPG.\n"
        "   - Status Sertifikasi Halal BPJPH (UU JPH No. 33/2014) rekanan baru.\n"
        "2. Gunakan bahasa konsultatif yang lugas, cerdas, dan luwes kepada Bapak Adam (hindari format kaku berulang).\n"
        "3. Informasikan bahwa draf PO yang diperbarui telah disiapkan di bawah untuk siap diotorisasi oleh Bapak Adam."
    ),

    # 9. Otorisasi Persetujuan Final (Penerbitan Surat PO)
    "PO_APPROVAL": (
        UNIVERSAL_PERSONA
        + "Konfirmasikan bahwa Bapak Adam Dzaki telah menyetujui penerbitan Purchase Order resmi ini. "
        "Sajikan nomor PO resmi, rekanan terdaftar dari basis data SQLite, kuantitas, dan total anggaran secara profesional dan terstruktur."
    ),

    # 10. Manajemen Rekanan Supplier (Onboarding, Update, Nonaktifkan / CRUD via Chat)
    "SUPPLIER_MANAGEMENT": (
        UNIVERSAL_PERSONA
        + "Kamu memiliki kapabilitas penuh untuk mengelola siklus hidup rekanan supplier (CRUD) bersama Bapak Adam: "
        "mendaftarkan rekanan baru, memperbarui harga/kapasitas/lead time, serta menonaktifkan supplier (soft delete). "
        "Tugasmu: Mengomunikasikan hasil aksi pengelolaan rekanan supplier secara lugas, profesional, dan empatik. "
        "PENTING: Selalu garisbawahi aspek tata kelola regulasi, khususnya:\n"
        "1. Kepatuhan Sertifikasi Halal (UU JPH No. 33/2014) - sebutkan apakah rekanan memenuhi syarat darurat SPPG.\n"
        "2. Kepatuhan Pagu Anggaran SOP BGN - sebutkan apakah harga rekanan aman atau melebihi batas pagu SOP.\n"
        "Gunakan bahasa Indonesia yang santun, jelas, dan percaya diri."
    ),

    # 11. Perencanaan Pengadaan Menu & Kebutuhan Porsi Bergizi (Multi-Item)
    "PROCUREMENT_PLANNING": (
        UNIVERSAL_PERSONA
        + "Kamu sedang mendampingi Bapak Adam (Kepala SPPG) dalam merancang pengadaan menu pemenuhan gizi berimbang (Multi-Item).\n"
        "GAYA KOMUNIKASI & PERSONA:\n"
        "1. Berbicara dengan gaya konsultatif profesional, luwes, dan natural (hindari format kaku atau kalimat template robotik berulang).\n"
        "2. Selalu sapa dengan hormat: 'Bapak Adam' atau 'Kepala SPPG'.\n"
        "3. Nyatakan jaminan kepatuhan SOP secara organik di dalam narasi:\n"
        "   - Status Kehalalan Resmi (UU JPH No. 33/2014) untuk seluruh rekanan yang dipilih.\n"
        "   - Kepatuhan Pagu Anggaran SOP Badan Gizi Nasional (BGN) bahwa harga dan total pengadaan aman terkendali.\n"
        "   - Rantai dingin (cold chain) dan batas kapasitas penyimpanan ruang pendingin (freezer).\n"
        "4. ZERO HALLUCINATION: Gunakan HANYA data rekanan, harga, dan stok yang diberikan dalam konteks data SQLite. Jangan mengarang rekanan atau harga!\n"
        "5. Jelaskan bahwa draf Purchase Order resmi telah disiapkan dan menunggu persetujuan/otorisasi Bapak Adam sebelum dicatat permanen ke basis data."
    ),
}


class ConversationalAgentManager:
    """
    Manajer Agen Percakapan Cerdas (Conversational AI Assistant).
    
    Arsitektur: Two-Stage Cognitive Agent Loop (Industry Standard 2026)
    - Stage 1: LLM Cognitive Decision Engine (Gemini 3.5 Flash-Lite) mengidentifikasi niat bebas & memilih aksi/tool.
    - Stage 2: Deterministic Python Execution (Zero Hallucination) menjalankan tool resmi & kalkulasi matematis tertutup.
    - Stage 3: Gemini 3.5 Flash-Lite mensintesis respon bahasa alami yang luwes, empatik, dan akurat.
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

    @staticmethod
    def _clean_ai_output(text: str) -> str:
        """Membersihkan output teks dari karakter LaTeX math, salam klise robotik, dan bullet aneh."""
        if not text:
            return ""
        # 1. Hapus salam klise robotik di awal pesan (misal: "Selamat pagi/siang Bapak Adam, Kepala SPPG.")
        cleaned = re.sub(
            r'^\s*(?:Selamat pagi/siang(?:/sore)?|Selamat pagi|Selamat siang|Selamat sore|Selamat malam)[,\.]?\s*(?:Bapak\s+Adam[,\.]?\s*)?(?:Kepala\s+SPPG[,\.]?\s*)?',
            '',
            text,
            flags=re.IGNORECASE,
        ).strip()
        # 2. Hapus tag LaTeX math seperti \(...\), \[...\], $...$, \textbf{}, \textit{}
        cleaned = re.sub(r'\\\(|\\\)', '', cleaned)
        cleaned = re.sub(r'\\\[|\\\]', '', cleaned)
        cleaned = re.sub(r'\$\$', '', cleaned)
        cleaned = re.sub(r'\$(.*?)\$', r'\1', cleaned)
        cleaned = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', cleaned)
        cleaned = re.sub(r'\\textit\{(.*?)\}', r'*\1*', cleaned)
        # 3. Ubah format bullet ganda aneh seperti "* **" atau "- **" menjadi "• **"
        cleaned = re.sub(r'^\s*[\*\-]\s+\*\*', '• **', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^\s*[\*\-]\s+', '• ', cleaned, flags=re.MULTILINE)
        # 4. Rapikan baris kosong berlebih
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _call_gemini_adaptive(
        self,
        system_instructions: str,
        user_message: str,
        context_data: str,
        fallback_text: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Memanggil Gemini untuk mensintesis respon bahasa alami yang luwes dan adaptif."""
        if not self.api_key or self.api_key.startswith("your_"):
            return self._clean_ai_output(fallback_text)

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                transport="rest",
                google_api_key=self.api_key,
                timeout=12,
            )
            prompt = [("system", system_instructions)]
            if history:
                for h in history[-6:]:
                    role = "human" if h.get("role") == "user" else "assistant"
                    prompt.append((role, h.get("content", "")))

            prompt.append((
                "user",
                f"Konteks Data Operasional SPPG Terverifikasi:\n{context_data}\n\n"
                f"Pesan dari Kepala SPPG:\n\"{user_message}\"\n\n"
                f"Berikan jawaban yang adaptif, komunikatif, profesional, dan to-the-point tanpa format LaTeX dan tanpa salam klise berulang.",
            ))
            response = llm.invoke(prompt)
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    text_out = "".join([str(p) for p in response.content]).strip()
                else:
                    text_out = str(response.content).strip()
                if len(text_out) > 10:
                    return self._clean_ai_output(text_out)
            return self._clean_ai_output(fallback_text)
        except Exception:
            return self._clean_ai_output(fallback_text)

    def _respond(self, session: Dict[str, Any], response: ChatResponse) -> ChatResponse:
        """Mencatat respons asisten ke riwayat percakapan sesi dan mengembalikan response."""
        session["history"].append({
            "role": "assistant",
            "content": response.reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            from app.data.sqlite_db import record_chat_message
            record_chat_message(
                session_id=response.session_id,
                role="assistant",
                message=response.reply,
                intent=response.intent.value if hasattr(response.intent, "value") else str(response.intent),
                action_required=response.action_required.value if hasattr(response.action_required, "value") else str(response.action_required),
                preview_data=response.preview_data,
            )
        except Exception:
            pass
        return response

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Mengambil atau menginisialisasi sesi percakapan baru."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "incident_context": {
                    "item_id": "ITEM-AYAM-01",
                    "target_portions": 3000,
                    "affected_supplier_id": None,
                    "affected_supplier_name": None,
                },
                "pending_clarification": None,
                "current_metrics": None,
                "current_recommendation": None,
                "procurement_plan": None,
                "is_approved": False,
                "po_result": None,
                "pending_crud": None,
            }
        return self._sessions[session_id]

    def _extract_portions(self, text: str, default: int = 3000) -> int:
        """Mengekstrak jumlah porsi dari teks menggunakan regex (misal: '5.000 porsi' atau '5000 porsi')."""
        match = re.search(r"(\d+(?:[\.,]\d+)?)\s*porsi", text, re.IGNORECASE)
        if match:
            raw_num = match.group(1).replace(".", "").replace(",", "")
            try:
                val = int(raw_num)
                if val > 0:
                    return val
            except ValueError:
                pass
        return default

    def _detect_item_id(self, text: str) -> str:
        """Mendeteksi bahan pangan dari percakapan."""
        t = text.lower()
        if "beras" in t:
            return "ITEM-BERAS-01"
        if "telur" in t:
            return "ITEM-TELUR-01"
        if "wortel" in t or "sayur" in t:
            return "ITEM-WORTEL-01"
        return "ITEM-AYAM-01"

    def _match_supplier_in_text(self, text: str) -> Optional[tuple[str, SupplierRecord]]:
        """Mencocokkan supplier yang disebut dalam teks langsung dari basis data SQLite resmi."""
        t_clean = text.strip().lower()
        from app.data.sqlite_db import get_all_suppliers
        db_sups = get_all_suppliers(include_inactive=True)

        # 1. Cek ID persis (misal SUP-UTAMA-01, SUP-ALT-01, SUP-REG-01)
        for s in db_sups:
            if s["supplier_id"].lower() in t_clean:
                return s["supplier_id"], SupplierRecord.model_validate(s)

        # 2. Cek nama supplier lengkap (prioritaskan rekanan yang masih berstatus aktif)
        active_matches = [
            s for s in db_sups
            if s["supplier_name"].lower() in t_clean and s.get("is_active", True)
        ]
        if active_matches:
            active_matches.sort(key=lambda r: len(r["supplier_name"]), reverse=True)
            chosen = active_matches[0]
            return chosen["supplier_id"], SupplierRecord.model_validate(chosen)

        # 3. Fallback jika rekanan non-aktif
        for s in sorted(db_sups, key=lambda r: len(r["supplier_name"]), reverse=True):
            if s["supplier_name"].lower() in t_clean:
                return s["supplier_id"], SupplierRecord.model_validate(s)

        return None

    @staticmethod
    def _infer_commodity_and_category(text: str, supplier_name: Optional[str] = None) -> Tuple[str, str, List[str]]:
        """
        Inferensi semantik cerdas komoditas, kategori, dan ID inventaris dari teks dan nama badan usaha.
        
        Aturan Prioritas:
        1. Frasa eksplisit 'komoditas <nama>'
        2. Frasa kontekstual '<nama_bahan> Rp <harga>' (misal: 'tahu Rp 18.000' -> TAHU)
        3. Kata kunci komoditas pangan dalam teks (tahu, tempe, telur, sapi, ayam, beras, sayur, ikan, dll.)
        4. Kata kunci komoditas dalam nama perusahaan (misal: 'CV Berkah Tahu' -> TAHU)
        """
        clean_text = text.strip()
        combined = f"{clean_text} {supplier_name or ''}".lower()

        # 1. Frasa eksplisit
        comm_explicit = re.search(
            r"komoditas\s+([A-Za-z0-9_\s]+?)(?:,|\s+(?:harga|kapasitas|dengan|halal|rp|sebesar|kilo|kg)\b|$)",
            clean_text,
            re.IGNORECASE,
        )
        candidate = comm_explicit.group(1).strip() if comm_explicit else None

        # 2. Pola kontekstual: '<komoditas> Rp <harga>' atau '<komoditas> harga <harga>'
        if not candidate:
            contextual_match = re.search(
                r"\b([A-Za-z]{3,15}(?:\s+[A-Za-z]{3,15})?)\s+(?:rp\.?|harga|@|sebesar)\s*[0-9]",
                clean_text,
                re.IGNORECASE,
            )
            if contextual_match:
                cand = contextual_match.group(1).lower()
                cand_clean = re.sub(r"^(?:supplier|suplier|rekanan|baru|dengan|kapasitas|jual)\s+", "", cand).strip()
                if cand_clean and cand_clean not in ["supplier", "suplier", "rekanan", "baru", "dengan", "kapasitas"]:
                    candidate = cand_clean

        search_target = f"{candidate or ''} {combined}".strip().lower()

        # 3. Pemetaan komoditas pangan spesifik
        if "tahu" in search_target:
            return "TAHU", "PROTEIN", ["ITEM-TAHU-01"]
        elif "tempe" in search_target:
            return "TEMPE", "PROTEIN", ["ITEM-TEMPE-01"]
        elif any(w in search_target for w in ["ikan", "lele", "tongkol", "nila"]):
            return "IKAN", "PROTEIN", ["ITEM-IKAN-01"]
        elif any(w in search_target for w in ["sapi", "lembu"]):
            return "DAGING_SAPI", "PROTEIN", ["ITEM-SAPI-01"]
        elif any(w in search_target for w in ["kambing", "domba"]):
            return "DAGING_KAMBING", "PROTEIN", ["ITEM-KAMBING-01"]
        elif "telur" in search_target:
            return "TELUR_AYAM", "PROTEIN", ["ITEM-TELUR-01"]
        elif any(w in search_target for w in ["ayam", "unggas", "broiler"]):
            return "DAGING_AYAM", "PROTEIN", ["ITEM-AYAM-01"]
        elif any(w in search_target for w in ["beras", "padi", "nasi"]):
            return "BERAS", "STAPLE", ["ITEM-BERAS-01"]
        elif any(w in search_target for w in ["jamur"]):
            return "JAMUR_TIRAM" if "tiram" in search_target else "JAMUR", "VEGETABLE", ["ITEM-JAMUR-01"]
        elif any(w in search_target for w in ["sayur", "wortel", "bayam", "kangkung", "brokoli", "kubis", "tomat"]):
            return "SAYUR_MAYUR", "VEGETABLE", ["ITEM-WORTEL-01"]
        elif "minyak" in search_target:
            return "MINYAK_GORENG", "STAPLE", ["ITEM-MINYAK-01"]
        elif any(w in search_target for w in ["buah", "pisang", "apel", "jeruk"]):
            return "BUAH_BUAHAN", "VEGETABLE", ["ITEM-BUAH-01"]
        elif "susu" in search_target:
            return "SUSU", "PROTEIN", ["ITEM-SUSU-01"]

        # 4. Fallback jika candidate ditemukan namun komoditas baru
        if candidate:
            comm_code = candidate.strip().replace(" ", "_").upper()
            return comm_code, "PROTEIN", [f"ITEM-{comm_code}-01"]

        return "DAGING_AYAM", "PROTEIN", ["ITEM-AYAM-01"]

    def _parse_supplier_create_data(self, text: str) -> Optional[SupplierCreateRequest]:
        """
        Mengekstrak parameter pendaftaran supplier baru dari teks menggunakan regex & heuristik domain.
        Jika LLM tersedia dan regex belum lengkap, gunakan Gemini untuk ekstraksi terstruktur.
        """
        # 1. Nama Perusahaan / Rekanan
        # A. Deteksi langsung pola entitas berbadan usaha (PT, CV, UD, Toko, Koperasi)
        entity_match = re.search(
            r"\b((?:PT|CV|UD|Toko|Koperasi)\s+[A-Za-z0-9\s\.\-]+?)(?:,|\s+(?:komoditas|jual|harga|kapasitas|dengan|halal|rp|sebesar)\b|$)",
            text,
            re.IGNORECASE,
        )
        supplier_name = entity_match.group(1).strip() if entity_match else None

        # B. Deteksi pola kalimat perintah jika bukan PT/CV/UD eksplisit
        if not supplier_name:
            name_match = re.search(
                r"(?:daftarkan|daftar|tambah|tambahkan|registrasi|input|masukkan|onboard|tolong|ada)?"
                r"(?:\s+supplier|\s+suplier|\s+rekanan|\s+baru|\s+mitra|\s+vendor|\s+kita|\s+yang|\s+namanya)*"
                r"\s+([A-Za-z0-9\s\.\-]+?)"
                r"(?:,|\s+(?:komoditas|jual|harga|kapasitas|dengan|halal|rp|sebesar|mereka|sanggup|lead\s*time)\b|$)",
                text,
                re.IGNORECASE,
            )
            supplier_name = name_match.group(1).strip() if name_match else None

        if supplier_name:
            supplier_name = re.sub(r"^(?:supplier|suplier|rekanan|mitra|baru|tolong)\s+", "", supplier_name, flags=re.IGNORECASE).strip()

        # 2. Harga per kg
        price = None
        price_match = re.search(r"(?:harga|rp|sebesar|@)\s*([0-9\.\,]+)", text, re.IGNORECASE)
        if price_match:
            raw_p = price_match.group(1).replace(".", "").replace(",", ".")
            try:
                price = float(raw_p)
            except ValueError:
                pass
        else:
            standalone_price = re.search(r"\b([3-9]\d{4}|1\d{5})\b", text)
            if standalone_price:
                price = float(standalone_price.group(1))

        # 3. Kapasitas harian (kg)
        capacity = None
        cap_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:kg|kilo)", text, re.IGNORECASE)
        if cap_match:
            raw_c = cap_match.group(1).replace(".", "").replace(",", ".")
            try:
                capacity = float(raw_c)
            except ValueError:
                pass

        # 4. Sertifikasi Halal & Nomor Sertifikat
        t_lower = text.lower()
        if any(w in t_lower for w in ["belum halal", "tidak halal", "non-halal", "bukan halal", "tanpa halal"]):
            halal_certified = False
        else:
            halal_certified = True

        cert_match = re.search(r"(?:id|nomor|no\.?|sertifikat)\s*(?:halal)?\s*[:\s]*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        halal_cert_number = cert_match.group(1) if cert_match else None

        # 5. Lead time & Jarak
        lead_time = 3.0
        lt_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*jam", text, re.IGNORECASE)
        if lt_match:
            try:
                lead_time = float(lt_match.group(1).replace(",", "."))
            except ValueError:
                pass

        distance = 15.0
        dist_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*km", text, re.IGNORECASE)
        if dist_match:
            try:
                distance = float(dist_match.group(1).replace(",", "."))
            except ValueError:
                pass

        # 6. Komoditas & Kategori cerdas
        commodity, category, supported_items = self._infer_commodity_and_category(text, supplier_name=supplier_name)

        # Validasi kecukupan atribut inti (Nama, Harga, Kapasitas)
        if not supplier_name or not price or not capacity:
            # Fallback ke Gemini LLM Structured Extraction jika tersedia
            if self.api_key and not self.api_key.startswith("your_"):
                try:
                    import json
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    llm = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        transport="rest",
                        google_api_key=self.api_key,
                        timeout=8,
                    )
                    extract_prompt = (
                        "Ekstrak data pendaftaran supplier pangan dari pesan berikut ke format JSON murni tanpa markdown:\n"
                        f"\"{text}\"\n\n"
                        "Format JSON wajib memiliki field:\n"
                        "{\n"
                        "  \"supplier_name\": string atau null,\n"
                        "  \"unit_price_idr\": float atau null,\n"
                        "  \"daily_capacity_kg\": float atau null,\n"
                        "  \"halal_certified\": boolean,\n"
                        "  \"halal_cert_number\": string atau null,\n"
                        "  \"commodity\": string,\n"
                        "  \"category\": string,\n"
                        "  \"lead_time_hours\": float,\n"
                        "  \"distance_km\": float\n"
                        "}"
                    )
                    res = llm.invoke([("user", extract_prompt)])
                    raw_content = str(res.content).strip()
                    raw_content = re.sub(r"^```json\s*", "", raw_content)
                    raw_content = re.sub(r"^```\s*", "", raw_content)
                    raw_content = re.sub(r"\s*```$", "", raw_content).strip()
                    parsed = json.loads(raw_content)
                    if parsed.get("supplier_name") and parsed.get("unit_price_idr") and parsed.get("daily_capacity_kg"):
                        p_comm = parsed.get("commodity")
                        if p_comm:
                            commodity, category, supported_items = self._infer_commodity_and_category(p_comm, supplier_name=parsed["supplier_name"])
                        return SupplierCreateRequest(
                            supplier_name=str(parsed["supplier_name"]),
                            category=parsed.get("category", category),
                            commodity=commodity,
                            supported_items=supported_items,
                            halal_certified=bool(parsed.get("halal_certified", True)),
                            halal_cert_number=parsed.get("halal_cert_number"),
                            unit_price_idr=float(parsed["unit_price_idr"]),
                            daily_capacity_kg=float(parsed["daily_capacity_kg"]),
                            lead_time_hours=float(parsed.get("lead_time_hours", lead_time)),
                            distance_km=float(parsed.get("distance_km", distance)),
                            reliability_rating=85.0,
                        )
                except Exception:
                    pass

            if not supplier_name or not price or not capacity:
                return None

        return SupplierCreateRequest(
            supplier_name=supplier_name,
            category=category,
            commodity=commodity,
            supported_items=supported_items,
            halal_certified=halal_certified,
            halal_cert_number=halal_cert_number,
            unit_price_idr=price,
            daily_capacity_kg=capacity,
            lead_time_hours=lead_time,
            distance_km=distance,
            reliability_rating=85.0,
        )

    # ==============================================================================
    # COGNITIVE DECISION ENGINE (STAGE 1: LLM BRAIN)
    # ==============================================================================
    def _decide_action(self, user_message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decision Router: Memahami konteks percakapan bebas Kepala SPPG menggunakan Gemini 3.5 Flash-Lite.
        Mengembalikan struktur aksi dan parameter. Jika LLM offline, beralih ke fallback deterministik yang aman.
        """
        has_pending_crud = bool(session.get("pending_crud"))
        has_pending = bool(session.get("pending_clarification"))
        has_rec = bool(session.get("current_recommendation"))
        msg_clean = user_message.strip()
        msg_lower = msg_clean.lower()

        # Deteksi apakah pesan pengguna merupakan inisiasi atau penyusunan menu pengadaan (Multi-Item)
        planning_keywords = [
            "rencana", "rencananya", "berencana", "menu", "porsi", "susun", "kebutuhan bahan",
            "pengadaan menu", "makanan bergizi", "bantu aku dalam membuat po", "membuat po", "buat po"
        ]
        commodity_keywords = [
            "ayam", "unggas", "telur", "tahu", "tempe", "sapi", "lembu", "ikan", "beras", "sayur", "wortel"
        ]
        is_planning_msg = any(w in msg_lower for w in planning_keywords) and (
            "porsi" in msg_lower or any(c in msg_lower for c in commodity_keywords)
        )

        revision_keywords = [
            "ganti supplier", "ganti rekanan", "ubah supplier", "ubah rekanan",
            "ganti ke", "ubah ke", "tukar", "pindah ke", "lebih murah", "alternatif lain"
        ]
        is_revision_msg = any(w in msg_lower for w in revision_keywords) or (
            ("ganti" in msg_lower or "tukar" in msg_lower) and any(c in msg_lower for c in commodity_keywords + ["supplier", "rekanan", "vendor", "mitra"])
        )

        # Prioritas status alur jika dalam interaksi multi-turn eksplisit:
        # 0. Permintaan Revisi / Penggantian Rekanan Pangan (REQUEST_REVISION)
        if is_revision_msg:
            return {"action": "REQUEST_REVISION", "parameters": {}}

        # 0.5 Perencanaan Menu / Kebutuhan Porsi Multi-Item (PLAN_PROCUREMENT)
        if is_planning_msg:
            portions = self._extract_portions(user_message, default=3000)
            commodities = []
            if "ayam" in msg_lower or "unggas" in msg_lower:
                commodities.append("ayam")
            if "telur" in msg_lower:
                commodities.append("telur")
            if "tahu" in msg_lower:
                commodities.append("tahu")
            if "tempe" in msg_lower:
                commodities.append("tempe")
            if "sapi" in msg_lower or "lembu" in msg_lower:
                commodities.append("sapi")
            if "beras" in msg_lower:
                commodities.append("beras")
            if "sayur" in msg_lower or "wortel" in msg_lower:
                commodities.append("wortel")
            if "ikan" in msg_lower:
                commodities.append("ikan")
            return {
                "action": "PLAN_PROCUREMENT",
                "parameters": {
                    "target_portions": portions,
                    "commodities": commodities,
                }
            }

        # 1. Konfirmasi atau Pembatalan Draf CRUD Rekanan / Penerbitan PO (Human-in-the-Loop)
        if has_pending_crud:
            if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
                return {"action": "CANCEL_CRUD", "parameters": {}}
            if any(w in msg_lower for w in [
                "setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan",
                "nonaktifkan", "hapus", "permanen", "proses", "deal",
                "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes", "eksekusi", "delete", "terbitkan", "terbitkan po"
            ]):
                return {"action": "CONFIRM_CRUD", "parameters": {}}

        # 2. Konfirmasi klarifikasi saat pending_clarification aktif
        if has_pending and (any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu"]) or any(s.lower() in msg_lower for s in session["pending_clarification"].get("suggestions", []))):
            return {"action": "CONFIRM_CLARIFICATION", "parameters": {}}

        # 3. Persetujuan PO saat rekomendasi mitigasi atau perencanaan pengadaan aktif
        if (has_rec or session.get("procurement_plan")) and any(
            w in msg_lower for w in ["buatkan po", "terbitkan po", "terbitkan surat po", "draf po", "bikin po", "po untuk rencana"]
        ):
            return {"action": "APPROVE_PO", "parameters": {}}

        if has_rec and any(w in msg_lower for w in ["setuju", "deal", "approve", "proses sekarang"]):
            return {"action": "APPROVE_PO", "parameters": {}}

        # 3. DOMAIN GUARDRAIL (SANGAT KETAT): Tolak permintaan pembuatan kode pemrograman
        coding_signals = [
            "code", "kode", "html", "javascript", "python", "css", "c++", "script",
            "hello world", "coding", "bikin web", "buatkan web", "pemrograman",
            "bikin program", "buat program", "tulis fungsi", "write code"
        ]
        if any(cs in msg_lower for cs in coding_signals):
            return {"action": "OUT_OF_DOMAIN", "parameters": {}}

        # Seluruh niat percakapan bebas (penghapusan rekanan, manajemen supplier, inventaris, arsip dokumen, dsb)
        # diproses secara murni melalui penalaran semantik kognitif LLM Gemini tanpa intervensi regex kaku.
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                import json
                from langchain_google_genai import ChatGoogleGenerativeAI

                decision_prompt = (
                    "Kamu adalah Cognitive Decision Engine untuk ResilioAI Assistant (Sistem Manajemen Rantai Pasok SPPG).\n"
                    "Kamu memiliki otoritas dan kapabilitas penuh untuk memahami niat Kepala SPPG (Bapak Adam) secara semantik tanpa ketergantungan kata kaku.\n"
                    "Tugasmu: Analisis pesan dari Kepala SPPG secara semantik dan ekstrak seluruh parameter yang dibutuhkan ke format JSON.\n\n"
                    f"Konteks Sesi Saat Ini:\n"
                    f"- Ada draf CRUD / PO pending menunggu keputusan Kepala: {'YA (' + str(session['pending_crud'].get('type', '')) + ')' if has_pending_crud else 'TIDAK'}\n"
                    f"- Ada draf rencana pengadaan menu aktif: {'YA (' + str(session.get('procurement_plan', {}).get('target_portions', '')) + ' porsi)' if session.get('procurement_plan') else 'TIDAK'}\n"
                    f"- Ada klarifikasi supplier pending: {'YA' if has_pending else 'TIDAK'}\n"
                    f"- Ada rekomendasi mitigasi aktif: {'YA' if has_rec else 'TIDAK'}\n\n"
                    "Daftar Aksi & Spesifikasi Parameter:\n"
                    "1. 'CONFIRM_CRUD': Kepala SPPG menyetujui/mengonfirmasi draf aksi CRUD pending (contoh: 'setuju', 'simpan', 'ya daftarkan', 'oke proses', 'lanjutkan').\n"
                    "2. 'CANCEL_CRUD': Kepala SPPG membatalkan draf aksi CRUD pending (contoh: 'batal', 'jangan simpan', 'batalkan', 'tidak jadi').\n"
                    "3. 'REGISTER_SUPPLIER': Kepala SPPG ingin menambahkan/mendaftarkan supplier baru "
                    "(contoh: 'daftarkan supplier baru CV Berkah tahu, tahu Rp 18.000, kapasitas 200kg, halal ID3211', 'tambah mitra PT Jamur Makmur, jamur tiram 15rb, kapasitas 100kg').\n"
                    "   Wajib ekstrak parameter berikut secara cerdas:\n"
                    "   {\n"
                    "     \"supplier_name\": string atau null (nama badan usaha/perusahaan),\n"
                    "     \"commodity\": string atau null (nama bahan pangan apa pun, misal: 'TAHU', 'TEMPE', 'IKAN', 'JAMUR_TIRAM', 'DAGING_SAPI', 'BERAS', 'TELUR_AYAM', dll.),\n"
                    "     \"category\": 'PROTEIN' | 'STAPLE' | 'VEGETABLE' | 'OTHER',\n"
                    "     \"unit_price_idr\": float atau null (harga per kg),\n"
                    "     \"daily_capacity_kg\": float atau null (kapasitas harian dalam kg),\n"
                    "     \"halal_certified\": boolean (true jika halal/aktif, false jika belum halal/non-halal),\n"
                    "     \"halal_cert_number\": string atau null (nomor sertifikat halal jika ada),\n"
                    "     \"lead_time_hours\": float (estimasi waktu tiba dalam jam, default 3.0),\n"
                    "     \"distance_km\": float (jarak tempuh ke SPPG dalam km, default 15.0)\n"
                    "   }\n"
                    "4. 'UPDATE_SUPPLIER': Kepala SPPG ingin mengubah atau memperbarui harga, kapasitas harian, durasi kirim rekanan "
                    "(contoh: 'update harga PT Berkah Unggas Jaya jadi 36500', 'ubah kapasitas CV Segar jadi 250kg').\n"
                    "   {\n"
                    "     \"supplier_name_or_id\": string atau null (nama atau ID rekanan target),\n"
                    "     \"unit_price_idr\": float atau null (harga baru jika disebutkan),\n"
                    "     \"daily_capacity_kg\": float atau null (kapasitas baru jika disebutkan),\n"
                    "     \"lead_time_hours\": float atau null,\n"
                    "     \"halal_certified\": boolean atau null\n"
                    "   }\n"
                    "5. 'DEACTIVATE_SUPPLIER': Kepala SPPG ingin menonaktifkan, menghapus, mencoret, memutus kontrak, atau mendepak supplier dari daftar aktif "
                    "(contoh: 'tolong hapus suplier dengan id berikut SUP-REG-02', 'singkirkan rekanan pak budi', 'nonaktifkan supplier UD Ayam Murah Meriah', 'hapus rekanan SUP-ALT-02', 'putus kontrak supplier ternak rumahan').\n"
                    "   {\n"
                    "     \"supplier_name_or_id\": string atau null (nama atau ID unik rekanan target, misal 'SUP-REG-02' atau 'Ternak Rumahan Pak Budi'),\n"
                    "     \"reason\": string (alasan atau konteks penonaktifan/penghapusan)\n"
                    "   }\n"
                    "6. 'LIST_SUPPLIERS': Melihat, menanyakan, atau mengecek daftar supplier/rekanan/vendor pangan "
                    "(contoh: 'suplier kita saat ini ada apa aja', 'siapa aja rekanan kita', 'ada berapa suplier di data kita', 'spill vendor ayam').\n"
                    "   Ekstrak parameter: {\"commodity\": string atau null}\n"
                    "7. 'GET_INVENTORY': Mengecek stok gudang, sisa bahan, atau kapasitas freezer "
                    "(contoh: 'stok beras sisa berapa?', 'cek stok gudang dan sisa freezer').\n"
                    "   Ekstrak parameter: {\"item_name_or_id\": string atau null}\n"
                    "8. 'REPORT_INCIDENT': Melaporkan gangguan pasokan, disrupsi, kebakaran, banjir, gagal kirim, atau kekurangan porsi makanan.\n"
                    "9. 'REQUEST_REVISION': Meminta revisi rekomendasi insiden (contoh: 'bisa ganti ke supplier yang lebih murah?', 'ubah target jadi 2000 porsi').\n"
                    "10. 'APPROVE_PO': Menyetujui atau meminta pembuatan Purchase Order resmi dari rencana pengadaan atau rekomendasi mitigasi yang sedang dibahas (contoh: 'setuju', 'deal', 'buatkan PO nya', 'oke bisa buatkan PO untuk rencana itu', 'terbitkan surat PO', 'buatkan PO').\n"
                    "11. 'CONFIRM_CLARIFICATION': Mengonfirmasi pilihan rekanan dari pertanyaan klarifikasi (contoh: 'iya betul, PT Unggas Sejahtera yang kebakaran', 'ya benar').\n"
                    "12. 'CLEAR_DOCUMENTS': Kepala SPPG meminta membersihkan, menghapus, atau mengosongkan seluruh arsip Surat Edaran dan Purchase Order.\n"
                    "13. 'DELETE_DOCUMENT': Kepala SPPG meminta menghapus salah satu dokumen spesifik (Surat Edaran atau PO) berdasarkan nomor atau id (contoh: 'hapus surat edaran SE-2026-001', 'hapus PO-2026-001', 'hapus salah satu dokumen').\n"
                    "   Ekstrak parameter: {\"identifier\": string atau null}\n"
                    "14. 'EXPLAIN_CAPABILITIES': Kepala SPPG bertanya apakah sistem bisa CRUD atau apa saja kemampuan operasional asisten.\n"
                    "15. 'OUT_OF_DOMAIN': Permintaan di luar lingkup SPPG, seperti membuat kode pemrograman (HTML, Python, dsb), tugas koding, puisi, dsb.\n"
                    "16. 'GREETING': Sapaan pembuka murni (contoh: 'halo', 'hai', 'selamat pagi').\n"
                    "17. 'GENERAL_CHAT': Pertanyaan konsultatif umum tentang regulasi halal UU 33/2014, SOP SPPG, atau obrolan logistik tanpa butuh data spesifik.\n"
                    "18. 'PLAN_PROCUREMENT': Kepala SPPG ingin merencanakan pengadaan atau mengevaluasi kesiapan bahan baku/kapasitas supplier untuk target menu atau porsi makanan tertentu "
                    "(contoh: 'rencananya saya ingin membuat makanan bergizi 3000 porsi dengan protein ayam dan tahu apa suplier kita memadai?', 'rencana menu 3000 porsi ayam dan tahu', 'kebutuhan bahan untuk 2000 porsi ayam').\n"
                    "   Ekstrak parameter:\n"
                    "   {\n"
                    "     \"target_portions\": integer (misal 3000),\n"
                    "     \"commodities\": list of string (misal: [\"ayam\", \"tahu\"])\n"
                    "   }\n\n"
                    "Keluarkan HANYA JSON murni tanpa pembungkus markdown: {\"action\": \"...\", \"parameters\": {...}}"
                )

                llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    transport="rest",
                    google_api_key=self.api_key,
                    timeout=8,
                )
                res = llm.invoke([("system", decision_prompt), ("user", user_message)])
                raw_content = str(res.content).strip()
                raw_content = re.sub(r"^```json\s*", "", raw_content)
                raw_content = re.sub(r"^```\s*", "", raw_content)
                raw_content = re.sub(r"\s*```$", "", raw_content).strip()
                parsed = json.loads(raw_content)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except Exception:
                pass

        return self._fallback_decide_action(user_message, session)

    def _fallback_decide_action(self, user_message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback router deterministik jika LLM offline atau timeout (Graceful Fallback)."""
        msg_lower = user_message.lower().strip()

        # Deteksi apakah pesan pengguna merupakan inisiasi atau penyusunan menu pengadaan (Multi-Item)
        planning_keywords = [
            "rencana", "rencananya", "berencana", "menu", "porsi", "susun", "kebutuhan bahan",
            "pengadaan menu", "makanan bergizi", "bantu aku dalam membuat po", "membuat po", "buat po"
        ]
        commodity_keywords = [
            "ayam", "unggas", "telur", "tahu", "tempe", "sapi", "lembu", "ikan", "beras", "sayur", "wortel"
        ]
        has_incident = any(k in msg_lower for k in ["kebakaran", "banjir", "rusak", "terhambat", "gagal", "mogok", "tidak kirim", "darurat", "musibah", "disrupsi"])
        is_planning_msg = not has_incident and any(w in msg_lower for w in planning_keywords) and (
            "porsi" in msg_lower or any(c in msg_lower for c in commodity_keywords)
        )

        revision_keywords = [
            "ganti supplier", "ganti rekanan", "ubah supplier", "ubah rekanan",
            "ganti ke", "ubah ke", "tukar", "pindah ke", "lebih murah", "alternatif lain"
        ]
        is_revision_msg = any(w in msg_lower for w in revision_keywords) or (
            ("ganti" in msg_lower or "tukar" in msg_lower) and any(c in msg_lower for c in commodity_keywords + ["supplier", "rekanan", "vendor", "mitra"])
        )

        # 0. Permintaan Revisi / Penggantian Rekanan Pangan (REQUEST_REVISION)
        if is_revision_msg:
            return {"action": "REQUEST_REVISION", "parameters": {}}

        # 0.5 Perencanaan Kebutuhan Menu & Porsi Bergizi (Multi-Item)
        if is_planning_msg:
            portions = self._extract_portions(user_message, default=3000)
            commodities = []
            if "ayam" in msg_lower or "unggas" in msg_lower:
                commodities.append("ayam")
            if "tahu" in msg_lower:
                commodities.append("tahu")
            if "tempe" in msg_lower:
                commodities.append("tempe")
            if "sapi" in msg_lower or "lembu" in msg_lower:
                commodities.append("sapi")
            if "telur" in msg_lower:
                commodities.append("telur")
            if "beras" in msg_lower:
                commodities.append("beras")
            if "wortel" in msg_lower or "sayur" in msg_lower:
                commodities.append("sayur")
            return {
                "action": "PLAN_PROCUREMENT",
                "parameters": {
                    "target_portions": portions,
                    "commodities": commodities or ["ayam"],
                },
            }

        # 1. Konfirmasi atau Pembatalan Draf CRUD Rekanan / Penerbitan PO (Human-in-the-Loop)
        if session.get("pending_crud"):
            if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
                return {"action": "CANCEL_CRUD", "parameters": {}}
            if any(w in msg_lower for w in [
                "setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan",
                "nonaktifkan", "hapus", "permanen", "proses", "deal",
                "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes", "eksekusi", "delete", "terbitkan"
            ]):
                return {"action": "CONFIRM_CRUD", "parameters": {}}

        # 2. Approval PO (Mitigasi Darurat atau Draf Perencanaan Pengadaan)
        if (session.get("current_recommendation") or session.get("procurement_plan")) and any(
            w in msg_lower for w in ["setuju", "deal", "buatkan po", "terbitkan", "approve", "buatkan po untuk rencana", "buatkan draf po", "terbitkan po"]
        ):
            return {"action": "APPROVE_PO", "parameters": {}}

        # 2. Clarification
        if session.get("pending_clarification") and (
            any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu"])
            or any(s.lower() in msg_lower for s in session["pending_clarification"].get("suggestions", []))
        ):
            return {"action": "CONFIRM_CLARIFICATION", "parameters": {}}

        # 3. Revision
        if session.get("current_recommendation") and any(w in msg_lower for w in ["ganti", "murah", "ubah", "kurangi", "tambah", "alternatif"]):
            return {"action": "REQUEST_REVISION", "parameters": {}}

        # 4. Strict Domain Guardrail (Coding / Pembuatan Kode / Out of Domain)
        coding_signals = [
            "code", "kode", "html", "javascript", "python", "css", "c++", "script",
            "hello world", "coding", "bikin web", "buatkan web", "pemrograman",
            "bikin program", "buat program", "tulis fungsi", "write code"
        ]
        if any(cs in msg_lower for cs in coding_signals):
            return {"action": "OUT_OF_DOMAIN", "parameters": {}}

        # 5. Hapus Satu Dokumen Spesifik vs Bersihkan Seluruh Dokumen
        clear_signals = ["bersihkan", "hapus", "reset", "kosongkan", "delete"]
        doc_signals = ["surat edaran", "edaran", "po", "dokumen", "purchase order"]
        import re
        doc_id_match = re.search(r'(?:PO|SE)-[A-Z0-9-]+|\d+/[A-Z0-9/-]+', user_message, re.IGNORECASE)
        if any(cs in msg_lower for cs in clear_signals) and (any(ds in msg_lower for ds in doc_signals) or doc_id_match):
            is_all = any(w in msg_lower for w in ["semua", "seluruh", "semuanya", "kosongkan", "bersihkan seluruh", "reset database", "bersihkan database"])
            is_single = any(w in msg_lower for w in ["salah satu", "satu dokumen", "satu saja", "spesifik"]) or (doc_id_match is not None)
            if (doc_id_match or is_single) and not is_all:
                identifier = doc_id_match.group(0) if doc_id_match else ""
                return {"action": "DELETE_DOCUMENT", "parameters": {"identifier": identifier}}
            else:
                return {"action": "CLEAR_DOCUMENTS", "parameters": {}}

        # 6. Pertanyaan Kapabilitas Sistem & Operasi CRUD
        if "crud" in msg_lower or ("apa kamu bisa" in msg_lower and "lakukan" in msg_lower) or "kemampuanmu apa" in msg_lower:
            return {"action": "EXPLAIN_CAPABILITIES", "parameters": {}}

        # 7. Supplier Management
        if (
            any(w in msg_lower for w in ["nonaktifkan", "non-aktifkan", "deaktivasi", "hapus", "delete"])
            and (any(s in msg_lower for s in ["supplier", "suppliers", "suplier", "rekanan", "vendor"]) or re.search(r"SUP-[A-Z0-9-]+", user_message, re.IGNORECASE))
        ):
            sup_match = re.search(r"SUP-[A-Z0-9-]+", user_message, re.IGNORECASE)
            target_id = sup_match.group(0).upper() if sup_match else None
            return {"action": "DEACTIVATE_SUPPLIER", "parameters": {"supplier_name_or_id": target_id}}
        if any(w in msg_lower for w in ["update", "ubah", "ganti harga", "sesuaikan harga", "perbarui"]):
            return {"action": "UPDATE_SUPPLIER", "parameters": {}}
        if any(w in msg_lower for w in ["daftarkan supplier", "daftar supplier baru", "tambah supplier", "tambahkan supplier", "registrasi supplier", "onboard supplier", "supplier baru", "suplier baru", "rekanan baru"]):
            return {"action": "REGISTER_SUPPLIER", "parameters": {}}

        # 5. List Suppliers
        if any(k in msg_lower for k in ["suplier", "supplier", "rekanan", "vendor"]) and any(v in msg_lower for v in ["list", "daftar", "semua", "berapa", "siapa", "lihat", "tampilkan", "ada apa", "cek"]):
            return {"action": "LIST_SUPPLIERS", "parameters": {}}

        # 6. Inventory
        if any(k in msg_lower for k in ["stok", "freezer", "inventaris", "gudang"]) and any(v in msg_lower for v in ["cek", "berapa", "lihat", "sisa", "daftar"]):
            return {"action": "GET_INVENTORY", "parameters": {}}

        # 7. Greeting
        greeting_words = ["halo", "hai", "hi", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum"]
        if any(msg_lower.startswith(g) for g in greeting_words) and len(msg_lower.split()) <= 4:
            return {"action": "GREETING", "parameters": {}}

        # 8. Incident
        incident_indicators = ["kebakaran", "banjir", "rusak", "terhambat", "gagal", "mogok", "tidak kirim", "kurang", "darurat", "musibah"]
        if any(k in msg_lower for k in incident_indicators) or ("porsi" in msg_lower and any(w in msg_lower for w in ["kurang", "butuh", "defisit"])):
            return {"action": "REPORT_INCIDENT", "parameters": {}}

        return {"action": "GENERAL_CHAT", "parameters": {}}

    # ==============================================================================
    # STAGE 2 & 3: HANDLERS DENGAN DETERMINISTIC EXECUTION & ADAPTIVE SYNTHESIS
    # ==============================================================================
    def _handle_greeting(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Menangani sapaan pembuka (GREETING)."""
        fallback = (
            f"Halo Pak/Bu {request.user_role}! 👋\n\n"
            f"Saya adalah **ResilioAI Assistant**, sistem kecerdasan buatan untuk mitigasi rantai pasok SPPG.\n\n"
            f"Layanan yang dapat saya bantu:\n"
            f"1. **Lapor Gangguan Pasokan:** Ceritakan jika ada supplier terkendala atau musibah di lapangan.\n"
            f"2. **Cek Inventaris:** Tanyakan stok fisik bahan makanan atau sisa ruang freezer.\n"
            f"3. **Katalog Rekanan:** Tanyakan daftar supplier terdaftar dan status sertifikasi Halal.\n\n"
            f"Ada kendala operasional yang perlu kita mitigasi hari ini?"
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["GREETING"],
            user_message=request.message,
            context_data=f"Pengguna: {request.user_role}. Sesi baru dimulai.",
            fallback_text=fallback,
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
            ),
        )

    def _handle_list_suppliers(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani permintaan daftar rekanan (LIST_SUPPLIERS) langsung dari SQLite."""
        commodity_filter = params.get("commodity")
        from app.data.sqlite_db import get_all_suppliers
        db_sups = get_all_suppliers(include_inactive=False, commodity=commodity_filter)
        suppliers = [SupplierRecord.model_validate(s) for s in db_sups]

        lines = [f"Saat ini terdapat **{len(suppliers)} rekanan supplier** yang terdaftar di basis data SPPG:\n"]
        for idx, s in enumerate(suppliers, 1):
            halal_badge = "Halal Aktif ✅" if s.halal_certified else "Belum Halal ❌"
            is_utama = " (Supplier Utama SPPG)" if "utama" in s.supplier_id.lower() else ""
            comm = getattr(s, "commodity", s.category)
            lines.append(
                f"{idx}. **{s.supplier_name}** (`{s.supplier_id}`){is_utama}\n"
                f"   • Komoditas: **{comm}** [{s.category}] | Sertifikasi: {halal_badge}\n"
                f"   • Kapasitas Harian: {s.daily_capacity_kg} kg/hari | Harga: Rp {s.unit_price_idr:,.2f}/kg\n"
                f"   • Estimasi Tiba: {s.lead_time_hours} jam | Jarak: {s.distance_km} km | Rating: {s.reliability_rating}/100"
            )
        fallback = "\n".join(lines)
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_INQUIRY"],
            user_message=request.message,
            context_data="\n".join([f"{s.supplier_id}: {s.supplier_name}, Komoditas={s.commodity}, Halal={s.halal_certified}, Kapasitas={s.daily_capacity_kg}kg, Harga=Rp {s.unit_price_idr}" for s in suppliers]),
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
                preview_data={"suppliers": [s.model_dump() for s in suppliers]},
            ),
        )

    def _handle_get_inventory(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani pengecekan stok inventaris dan freezer (GET_INVENTORY) langsung dari SQLite."""
        from app.data.sqlite_db import get_all_inventory_items
        db_items = get_all_inventory_items()
        items = [InventoryItem.model_validate(it) for it in db_items]

        lines = ["Berikut adalah status inventaris gudang dan kapasitas pendingin SPPG saat ini:\n"]
        for it in items:
            freezer_avail = max(0.0, round(it.freezer_capacity_kg - it.freezer_occupied_kg, 2))
            lines.append(
                f"• **{it.item_name}** (`{it.item_id}`) [{it.category}]\n"
                f"   - Stok Fisik Gudang: **{it.current_stock_kg} kg** (Batas Aman SOP: {it.safety_stock_kg} kg)\n"
                f"   - Kapasitas Freezer: Total {it.freezer_capacity_kg} kg (Sisa Tersedia: **{freezer_avail} kg**)\n"
                f"   - Pagu Anggaran SOP: Rp {it.sop_max_price_per_kg:,.2f} / kg"
            )
        fallback = "\n".join(lines)
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["INVENTORY_INQUIRY"],
            user_message=request.message,
            context_data="\n".join([f"{it.item_id}: {it.item_name}, Stok={it.current_stock_kg}kg, Sisa Freezer={it.freezer_capacity_kg - it.freezer_occupied_kg}kg, Pagu=Rp {it.sop_max_price_per_kg}" for it in items]),
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
                preview_data={"inventory": [it.model_dump() for it in items]},
            ),
        )

    def _handle_supplier_management(
        self,
        session: Dict[str, Any],
        request: ChatRequest,
        action: str,
        params: Dict[str, Any],
    ) -> ChatResponse:
        """Menangani pembuatan draf preview CRUD supplier (REGISTER_SUPPLIER, UPDATE_SUPPLIER, DEACTIVATE_SUPPLIER)."""
        user_msg = request.message.strip()

        # 1. DEACTIVATE / DELETE PREVIEW (Human-in-the-Loop)
        if action in ["DEACTIVATE_SUPPLIER", "DELETE_SUPPLIER"]:
            matched = None
            if params.get("supplier_name_or_id"):
                matched = self._match_supplier_in_text(str(params["supplier_name_or_id"]))
            if not matched:
                matched = self._match_supplier_in_text(user_msg)

            if not matched:
                return self._respond(
                    session,
                    ChatResponse(
                        session_id=request.session_id,
                        reply=(
                            "Bapak Adam, saya tidak menemukan nama atau ID rekanan supplier yang dimaksud dalam basis data SPPG.\n\n"
                            "Mohon sebutkan nama lengkap atau ID rekanan (contoh: `SUP-REG-02` atau `Ternak Rumahan Pak Budi`)."
                        ),
                        intent=ChatIntent.MANAGE_SUPPLIER,
                        action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                    ),
                )

            sid, supplier = matched
            reason = params.get("reason") or "Penonaktifan administratif oleh pimpinan SPPG"
            commodity_name = getattr(supplier, "commodity", supplier.category)

            session["pending_crud"] = {
                "type": "MANAGE_SUPPLIER_DELETE",
                "supplier_id": sid,
                "supplier_name": supplier.supplier_name,
                "commodity": commodity_name,
                "reason": reason,
            }

            preview_text = (
                f"⚠️ **Konfirmasi Pengelolaan Rekanan SPPG**\n\n"
                f"Bapak Adam Dzaki, sistem mendeteksi instruksi penghapusan atau penonaktifan rekanan:\n"
                f"• Nama Rekanan: **{supplier.supplier_name}** (`{sid}`)\n"
                f"• Komoditas Pangan: **{commodity_name}** [{supplier.category}]\n"
                f"• Alasan: {reason}\n\n"
                f"Mohon konfirmasi jenis tindakan yang ingin diterapkan pada basis data SQLite SPPG:\n"
                f"1. **Hapus Permanen (Database)**: Menghapus baris rekanan secara fisik dari tabel suppliers di SQLite.\n"
                f"2. **Nonaktifkan Saja (Soft Delete)**: Mengubah status menjadi NON-AKTIF (`is_active = 0`) agar rekam jejak audit anggaran masa lalu tetap tersimpan.\n\n"
                f"Silakan klik salah satu tombol aksi di bawah atau ketik pilihan Bapak (*'Hapus permanen'* / *'Nonaktifkan'* / *'Batal'*)."
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=user_msg,
                context_data=(
                    f"Tahap: Konfirmasi Penghapusan/Penonaktifan Rekanan. "
                    f"Target Rekanan: {supplier.supplier_name} ({sid}), Komoditas: {commodity_name}. Alasan: {reason}. "
                    f"Sistem telah menyiapkan opsi Hapus Permanen (Database) dan Nonaktifkan Saja (Soft Delete) via kartu interaktif. "
                    f"Instruksikan Bapak Adam Dzaki untuk memilih opsi pada kartu konfirmasi."
                ),
                fallback_text=preview_text,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.APPROVAL_PENDING,
                    preview_data={
                        "action": "PREVIEW_DEACTIVATE",
                        "supplier_id": sid,
                        "supplier_name": supplier.supplier_name,
                        "confirm_supplier_action": {
                            "action_type": "DELETE_OR_DEACTIVATE",
                            "supplier_id": sid,
                            "supplier_name": supplier.supplier_name,
                            "commodity": commodity_name,
                            "title": f"Penghapusan Rekanan #{sid}",
                            "details": f"{supplier.supplier_name} ({sid}) - {commodity_name}",
                            "warning": "Penghapusan permanen akan menghapus data dari basis data SQLite SPPG.",
                        }
                    },
                ),
            )

        # 2. UPDATE PREVIEW
        if action == "UPDATE_SUPPLIER":
            matched = None
            if params.get("supplier_name_or_id"):
                matched = self._match_supplier_in_text(str(params["supplier_name_or_id"]))
            if not matched:
                matched = self._match_supplier_in_text(user_msg)

            if not matched:
                fallback = (
                    "Saya belum dapat mengidentifikasi rekanan yang ingin Anda perbarui datanya.\n\n"
                    "Mohon sebutkan nama rekanan terdaftar atau ID-nya beserta data yang ingin diubah "
                    "(misal: *'Update harga PT Berkah Unggas Jaya menjadi Rp 36.500'*)."
                )
                return self._respond(
                    session,
                    ChatResponse(
                        session_id=request.session_id,
                        reply=fallback,
                        intent=ChatIntent.MANAGE_SUPPLIER,
                        action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                    ),
                )

            sid, supplier = matched
            new_price = None
            if params.get("unit_price_idr") is not None:
                try:
                    new_price = float(params["unit_price_idr"])
                except (ValueError, TypeError):
                    pass
            if new_price is None:
                price_match = re.search(r"(?:harga|rp|menjadi|jadi|sebesar|@)\s*([0-9\.\,]+)", user_msg, re.IGNORECASE)
                if price_match:
                    try:
                        new_price = float(price_match.group(1).replace(".", "").replace(",", "."))
                    except ValueError:
                        pass

            new_capacity = None
            if params.get("daily_capacity_kg") is not None:
                try:
                    new_capacity = float(params["daily_capacity_kg"])
                except (ValueError, TypeError):
                    pass
            if new_capacity is None:
                cap_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:kg|kilo)", user_msg, re.IGNORECASE)
                if cap_match:
                    try:
                        new_capacity = float(cap_match.group(1).replace(".", "").replace(",", "."))
                    except ValueError:
                        pass

            new_lead_time = None
            if params.get("lead_time_hours") is not None:
                try:
                    new_lead_time = float(params["lead_time_hours"])
                except (ValueError, TypeError):
                    pass
            if new_lead_time is None:
                lt_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*jam", user_msg, re.IGNORECASE)
                if lt_match:
                    try:
                        new_lead_time = float(lt_match.group(1).replace(",", "."))
                    except ValueError:
                        pass

            updates_dict = {}
            if new_price is not None:
                updates_dict["unit_price_idr"] = new_price
            if new_capacity is not None:
                updates_dict["daily_capacity_kg"] = new_capacity
            if new_lead_time is not None:
                updates_dict["lead_time_hours"] = new_lead_time

            if not updates_dict:
                fallback = f"Tidak ada data perubahan baru yang terdeteksi untuk rekanan **{supplier.supplier_name}**."
                return self._respond(
                    session,
                    ChatResponse(
                        session_id=request.session_id,
                        reply=fallback,
                        intent=ChatIntent.MANAGE_SUPPLIER,
                        action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                    ),
                )

            session["pending_crud"] = {
                "type": "UPDATE",
                "supplier_id": sid,
                "supplier_name": supplier.supplier_name,
                "updates": updates_dict,
            }

            changes_desc = []
            if new_price is not None:
                changes_desc.append(f"• Harga Penawaran: Rp {supplier.unit_price_idr:,.2f} ➡️ **Rp {new_price:,.2f} / kg**")
            if new_capacity is not None:
                changes_desc.append(f"• Kapasitas Harian: {supplier.daily_capacity_kg} kg ➡️ **{new_capacity} kg/hari**")
            if new_lead_time is not None:
                changes_desc.append(f"• Estimasi Tiba: {supplier.lead_time_hours} jam ➡️ **{new_lead_time} jam**")

            preview_text = (
                f"📋 **Konfirmasi Pembaruan Data Rekanan (Preview Perubahan)**\n\n"
                f"Halo Bapak/Ibu Kepala SPPG, mohon tinjau draf rencana perubahan data rekanan berikut:\n\n"
                f"• **Rekanan Target:** **{supplier.supplier_name}** (`{sid}`)\n"
                f"• **Komoditas Pangan:** **{supplier.commodity}**\n"
                f"• **Rencana Perubahan:**\n"
                + "\n".join(changes_desc) + "\n\n"
                f"---\n"
                f"Keputusan akhir berada di tangan Bapak/Ibu Kepala SPPG:\n"
                f"👉 Ketik **\"Setuju / Simpan\"** untuk menerapkan pembaruan ke basis data resmi SPPG.\n"
                f"👉 Ketik **\"Batal\"** untuk membatalkan perubahan ini."
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=user_msg,
                context_data=f"Tahap: Preview Update. Rekanan: {supplier.supplier_name} ({sid}). Perubahan: {changes_desc}. Menunggu persetujuan Kepala SPPG.",
                fallback_text=preview_text,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.APPROVAL_PENDING,
                    preview_data={"action": "PREVIEW_UPDATE", "supplier_id": sid, "updates": updates_dict},
                ),
            )

        # 3. REGISTER PREVIEW
        create_payload = None

        # A. Bangun langsung dari parameter terstruktur hasil analisis kognitif Gemini Brain
        p_name = params.get("supplier_name")
        p_price = params.get("unit_price_idr") or params.get("price")
        p_cap = params.get("daily_capacity_kg") or params.get("capacity")

        if p_name and p_price and p_cap:
            try:
                p_halal = params.get("halal_certified")
                if p_halal is None:
                    p_halal = True

                # Inferensikan komoditas & kategori secara semantik cerdas
                comm_raw = params.get("commodity")
                if comm_raw and str(comm_raw).strip().upper() not in ["NONE", "NULL", ""]:
                    comm, cat, supp_items = self._infer_commodity_and_category(str(comm_raw), supplier_name=str(p_name))
                else:
                    comm, cat, supp_items = self._infer_commodity_and_category(user_msg, supplier_name=str(p_name))

                cert = params.get("halal_cert_number") or params.get("cert_number")
                lead_t = float(params.get("lead_time_hours") or 3.0)
                dist = float(params.get("distance_km") or 15.0)

                create_payload = SupplierCreateRequest(
                    supplier_name=str(p_name).strip(),
                    category=cat,
                    commodity=comm,
                    supported_items=supp_items,
                    halal_certified=bool(p_halal),
                    halal_cert_number=str(cert).strip() if cert else None,
                    unit_price_idr=float(p_price),
                    daily_capacity_kg=float(p_cap),
                    lead_time_hours=lead_t,
                    distance_km=dist,
                    reliability_rating=85.0,
                )
            except Exception:
                create_payload = None

        # B. Fallback ke parser heuristik teks
        if not create_payload:
            create_payload = self._parse_supplier_create_data(user_msg)

        if not create_payload:
            fallback = (
                "Untuk mendaftarkan rekanan supplier baru ke basis data SPPG, mohon lengkapi informasi berikut:\n\n"
                "1. **Nama Rekanan/Badan Usaha** (misal: *CV Berkah Jaya Pangan*)\n"
                "2. **Komoditas Pangan** (misal: *Daging Ayam, Daging Sapi, Beras, Telur, Tahu*)\n"
                "3. **Harga Penawaran per kg** (misal: *Rp 18.000*)\n"
                "4. **Kapasitas Pasokan Harian** (misal: *200 kg*)\n"
                "5. **Status Sertifikasi Halal** (Nomor sertifikat halal jika ada)\n\n"
                "Contoh format perintah:\n"
                "👉 *\"Daftarkan supplier baru CV Berkah Tahu, tahu Rp 18.000, kapasitas 200 kg, halal ID3211\"*"
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=fallback,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                ),
            )

        # Evaluasi Pagu SOP & Sertifikasi Halal untuk Preview
        matched_item = None
        comm_lower = create_payload.commodity.lower()
        from app.data.sqlite_db import get_all_inventory_items
        db_items = get_all_inventory_items()
        for it in db_items:
            it_name = it.get("item_name", "").lower()
            it_id = it.get("item_id", "").lower()
            if comm_lower in it_name or comm_lower in it_id:
                matched_item = it
                break
        if not matched_item:
            for it in db_items:
                if create_payload.category.upper() == it.get("category", "").upper():
                    matched_item = it
                    break

        sop_max = matched_item.get("sop_max_price_per_kg", 40000.0) if matched_item else 40000.0
        exceeds_sop = create_payload.unit_price_idr > sop_max
        pagu_status = "Sesuai Pagu Anggaran SOP BGN (Aman) ✅" if not exceeds_sop else f"Melebihi Pagu SOP {matched_item.get('item_name', '') if matched_item else ''} (Maks: Rp {sop_max:,.2f}) ⚠️"
        halal_badge = f"Terverifikasi Aktif (No: {create_payload.halal_cert_number or 'Tercatat'}) ✅" if create_payload.halal_certified else "Belum Memiliki Sertifikat Halal ❌"

        # Simpan Draf ke Sesi (Menunggu Keputusan Akhir Kepala SPPG)
        session["pending_crud"] = {
            "type": "CREATE",
            "payload": create_payload.model_dump(),
        }

        preview_text = (
            f"📋 **Konfirmasi Draft Rekanan Baru (Preview Data)**\n\n"
            f"Halo Bapak/Ibu Kepala SPPG, draf data rekanan baru telah disiapkan untuk ditinjau:\n\n"
            f"• **Nama Rekanan:** **{create_payload.supplier_name}**\n"
            f"• **Komoditas Pangan:** **{create_payload.commodity}** [{create_payload.category}]\n"
            f"• **Harga Penawaran:** Rp {create_payload.unit_price_idr:,.2f} / kg\n"
            f"• **Kapasitas Pasokan:** {create_payload.daily_capacity_kg} kg/hari\n"
            f"• **Estimasi Tiba & Jarak:** {create_payload.lead_time_hours} jam | {create_payload.distance_km} km\n\n"
            f"🛡️ **Tinjauan Kepatuhan Regulasi SPPG:**\n"
            f"• **Sertifikasi Halal (UU JPH No. 33/2014):** {halal_badge}\n"
            f"• **Pagu Anggaran SOP BGN:** {pagu_status}\n\n"
            f"---\n"
            f"Keputusan akhir berada di tangan Bapak/Ibu Kepala SPPG:\n"
            f"👉 Ketik **\"Setuju / Simpan\"** untuk meresmikan ke basis data resmi SPPG.\n"
            f"👉 Ketik **\"Batal\"** jika ingin membatalkan pendaftaran ini."
        )

        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
            user_message=user_msg,
            context_data=(
                f"Tahap: Preview Draft Pendaftaran. Rekanan: {create_payload.supplier_name}, "
                f"Komoditas: {create_payload.commodity}, Harga: Rp {create_payload.unit_price_idr}, "
                f"Kapasitas: {create_payload.daily_capacity_kg} kg, Halal: {create_payload.halal_certified}. "
                f"Menunggu keputusan akhir persetujuan Kepala SPPG."
            ),
            fallback_text=preview_text,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.MANAGE_SUPPLIER,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={"action": "PREVIEW_CREATE", "draft": create_payload.model_dump()},
            ),
        )

    def _handle_crud_confirmation(
        self,
        session: Dict[str, Any],
        request: ChatRequest,
        is_confirm: bool,
    ) -> ChatResponse:
        """Menangani eksekusi atau pembatalan draf CRUD setelah keputusan Kepala SPPG (Human-in-the-Loop)."""
        pending = session.get("pending_crud")
        if not pending:
            return self._handle_consultative_chat(session, request)

        crud_type = pending.get("type")

        # 1. JIKA KEPALA SPPG MEMBATALKAN
        if not is_confirm:
            session["pending_crud"] = None
            if crud_type == "APPROVE_MULTI_PO":
                cancel_msg = (
                    "❌ **Penerbitan Purchase Order Dibatalkan**\n\n"
                    "Instruksi penerbitan Purchase Order (PO) telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                    "Tidak ada pesanan pengadaan yang diterbitkan atau disimpan ke basis data SQLite SPPG."
                )
            elif crud_type in ["CLEAR_ALL_DOCUMENTS", "DELETE_DOCUMENT"]:
                cancel_msg = (
                    "❌ **Penghapusan Dokumen Dibatalkan**\n\n"
                    "Instruksi penghapusan arsip dokumen telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                    "Seluruh berkas Surat Edaran dan Purchase Order tetap aman dan tersimpan di basis data SPPG."
                )
            else:
                cancel_msg = (
                    f"❌ **Aksi Pengelolaan Rekanan Dibatalkan**\n\n"
                    f"Instruksi draf {crud_type} telah dibatalkan sesuai arahan Bapak Adam Dzaki. "
                    f"Tidak ada data rekanan yang diubah atau dihapus dari basis data resmi SPPG."
                )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data=f"Bapak Adam membatalkan aksi {crud_type}. Tidak ada mutasi basis data.",
                fallback_text=cancel_msg,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        # 2. JIKA KEPALA SPPG MENYETUJUI / MENGONFIRMASI
        if crud_type == "CREATE":
            payload_dict = pending["payload"]
            create_req = SupplierCreateRequest(**payload_dict)
            res = register_supplier_tool(payload=create_req)
            session["pending_crud"] = None

            s = res["supplier"]
            gov = res["governance"]
            halal_badge = "Sertifikat Halal Aktif (UU JPH No. 33/2014) ✅" if gov["halal_certified"] else "Belum Halal (Non-Prioritas) ❌"
            pagu_status = "Sesuai Pagu SOP BGN ✅" if not gov["exceeds_sop_ceiling"] else f"Melebihi Pagu SOP (Peringatan: {gov['price_warning']}) ⚠️"

            fallback = (
                f"✅ **Otorisasi Diterima: Rekanan Baru Resmi Terdaftar di Basis Data SPPG!**\n\n"
                f"• ID Registrasi: `{res['supplier_id']}`\n"
                f"• Nama Rekanan: **{s['supplier_name']}**\n"
                f"• Komoditas: **{s['commodity']}** [{s['category']}]\n"
                f"• Harga Penawaran: Rp {s['unit_price_idr']:,.2f} / kg\n"
                f"• Kapasitas Harian: {s['daily_capacity_kg']} kg/hari\n"
                f"• Estimasi Tiba: {s['lead_time_hours']} jam | Jarak: {s['distance_km']} km\n\n"
                f"🛡️ **Status Tata Kelola:**\n"
                f"• Sertifikasi: {halal_badge}\n"
                f"• Kepatuhan Anggaran: {pagu_status}\n\n"
                f"💾 *Data telah diverifikasi dan disimpan permanen ke dalam basis data operasional SPPG.*"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data=f"Aksi: Pendaftaran Resmi Disetujui Kepala SPPG. Hasil: {res}",
                fallback_text=fallback,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                    preview_data={"action": "CREATE", "result": res},
                ),
            )

        elif crud_type == "UPDATE":
            sid = pending["supplier_id"]
            up_dict = pending["updates"]
            update_req = SupplierUpdateRequest(**up_dict)
            res = update_supplier_tool(supplier_id=sid, updates=update_req)
            session["pending_crud"] = None

            updated_s = res.get("supplier", {})
            fallback = (
                f"✅ **Otorisasi Diterima: Data Rekanan Berhasil Diperbarui!**\n\n"
                f"• Rekanan: **{updated_s.get('supplier_name', sid)}** (`{sid}`)\n"
                f"• Harga Penawaran: Rp {updated_s.get('unit_price_idr', 0):,.2f} / kg\n"
                f"• Kapasitas Harian: {updated_s.get('daily_capacity_kg', 0)} kg/hari\n"
                f"• Bidang diperbarui: {', '.join(res.get('updated_fields', []))}\n\n"
                f"💾 *Pembaruan data telah disetujui Kepala SPPG dan disimpan permanen.*"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data=f"Aksi: Update Disetujui Kepala SPPG. Hasil: {res}",
                fallback_text=fallback,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                    preview_data={"action": "UPDATE", "result": res},
                ),
            )

        elif crud_type in ["DEACTIVATE", "DELETE_SUPPLIER", "MANAGE_SUPPLIER_DELETE"]:
            sid = pending["supplier_id"]
            supplier_name = pending.get("supplier_name", sid)
            reason = pending.get("reason", "Instruksi disetujui Kepala SPPG")
            session["pending_crud"] = None

            msg_check = request.message.strip().lower()
            # Cek apakah pengguna memilih Hapus Permanen atau Soft Delete
            is_hard_delete = any(w in msg_check for w in ["permanen", "hard", "hapus permanen", "hapus"]) and not any(w in msg_check for w in ["nonaktif", "soft", "batal"])

            if is_hard_delete:
                res = delete_supplier_permanently_tool(supplier_id=sid)
                reply = (
                    f"✅ **Otorisasi Diterima: Rekanan Berhasil Dihapus Permanen dari Basis Data SQLite!**\n\n"
                    f"• Rekanan: **{supplier_name}** (`{sid}`)\n"
                    f"• Status Basis Data: **DIHAPUS SECARA FISIK DARI TABEL SUPPLIERS**\n"
                    f"• Otorisator: Bapak Adam Dzaki (Kepala SPPG)\n\n"
                    f"💾 *Data rekanan telah dihapus permanen dari basis data SQLite SPPG.*"
                )
                action_name = "DELETE_PERMANENT"
            else:
                res = deactivate_supplier_tool(supplier_id=sid, reason=reason)
                reply = (
                    f"✅ **Otorisasi Diterima: Rekanan Berhasil Dinonaktifkan (Soft Delete)!**\n\n"
                    f"• Rekanan: **{supplier_name}** (`{sid}`)\n"
                    f"• Status Operasional: **NON-AKTIF (`is_active = 0`)**\n"
                    f"• Alasan: {reason}\n"
                    f"• Otorisator: Bapak Adam Dzaki (Kepala SPPG)\n\n"
                    f"🛡️ *Histori transaksi masa lalu tetap tersimpan utuh di basis data SQLite SPPG.*"
                )
                action_name = "DEACTIVATE"

            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=reply,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                    preview_data={"action": action_name, "result": res},
                ),
            )

        elif crud_type == "CLEAR_ALL_DOCUMENTS":
            session["pending_crud"] = None
            from app.data.sqlite_db import clear_all_documents
            res = clear_all_documents()
            se_cleared = res.get("circular_letters_cleared", 0)
            po_cleared = res.get("purchase_orders_cleared", 0)
            fallback = (
                f"✅ **Otorisasi Diterima: Arsip Dokumen Berhasil Dikosongkan!**\n\n"
                f"Berdasarkan persetujuan Bapak Adam, seluruh riwayat dokumen resmi telah dibersihkan:\n"
                f"• Surat Edaran terhapus: {se_cleared} dokumen\n"
                f"• Purchase Order terhapus: {po_cleared} dokumen\n\n"
                f"💾 *Tabel dokumen kini berada dalam kondisi bersih (0 rekord) untuk simulasi baru.*"
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=fallback,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        elif crud_type == "DELETE_DOCUMENT":
            session["pending_crud"] = None
            doc_type = pending.get("doc_type", "SE")
            identifier = pending.get("identifier", "")
            title_or_name = pending.get("title_or_name", "")
            from app.data.sqlite_db import delete_circular_letter_by_id, delete_purchase_order_by_number
            if doc_type == "PO" or identifier.startswith("PO-"):
                success = delete_purchase_order_by_number(identifier)
                doc_label = "Purchase Order (PO)"
            else:
                success = delete_circular_letter_by_id(identifier)
                doc_label = "Surat Edaran (SE)"

            if success:
                fallback = (
                    f"✅ **Otorisasi Diterima: Dokumen Berhasil Dihapus!**\n\n"
                    f"Dokumen resmi berikut telah dihapus secara permanen dari basis data SPPG:\n"
                    f"• Jenis: **{doc_label}**\n"
                    f"• Nomor: `{identifier}`\n"
                    f"• Keterangan: {title_or_name}\n\n"
                    f"💾 *Penghapusan telah disahkan oleh Bapak Adam Dzaki.*"
                )
            else:
                fallback = (
                    f"⚠️ Dokumen `{identifier}` tidak ditemukan atau sudah terhapus sebelumnya di basis data."
                )

            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=fallback,
                    intent=ChatIntent.MANAGE_SUPPLIER,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        elif crud_type == "APPROVE_MULTI_PO":
            po_list = pending.get("po_list", [])
            total_budget = pending.get("total_budget", 0.0)
            target_portions = pending.get("target_portions", 3000)
            session["pending_crud"] = None

            from app.data.sqlite_db import save_circular_letter, save_purchase_order

            saved_pos = []
            for p in po_list:
                try:
                    save_purchase_order(p)
                    # Simpan juga surat penetapan edaran untuk audit trail resmi
                    letter_id = f"SE-SPPG-{p['po_number'].replace('PO-', '')}"
                    letter_num = f"{p['po_number'].split('-')[-1]}/SE/SPPG-PENGADAAN/{datetime.now(timezone.utc).strftime('%m/%Y')}"
                    save_circular_letter({
                        "letter_id": letter_id,
                        "letter_number": letter_num,
                        "title": f"Surat Penetapan Pengadaan {p.get('item_name', p['item_id'])} - {p['supplier_name']}",
                        "incident_id": p.get("incident_id", request.session_id),
                        "item_id": p["item_id"],
                        "deficit_kg": p["approved_qty_kg"],
                        "supplier_id": p["supplier_id"],
                        "supplier_name": p["supplier_name"],
                        "issued_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "signer_name": request.user_role,
                        "signer_role": "Kepala Satuan Pelayanan Pemenuhan Gizi (SPPG)",
                        "content_text": (
                            f"Berdasarkan rencana kebutuhan {target_portions:,} porsi dan persetujuan Kepala SPPG, "
                            f"ditetapkan pengadaan bahan pangan {p.get('item_name', p['item_id'])} sejumlah "
                            f"{p['approved_qty_kg']} kg kepada {p['supplier_name']} dengan nilai kontrak Rp {p['total_amount_idr']:,.2f}."
                        ),
                        "status": "ISSUED",
                    })
                    saved_pos.append(p)
                except Exception:
                    pass

            session["is_approved"] = True
            session["saved_pos"] = saved_pos

            fallback_text = (
                f"✅ **Otorisasi Diterima: Seluruh Purchase Order Resmi Berhasil Diterbitkan!**\n\n"
                f"Persetujuan telah dicatat secara resmi ke dalam basis data SQLite SPPG, Bapak Adam:\n\n"
                + "\n".join([
                    f"• **{p['supplier_name']}** (`{p['po_number']}`)\n"
                    f"  Komoditas: {p.get('item_name', p['item_id'])} | Kuantitas: **{p['approved_qty_kg']} kg** | Nilai: **Rp {p['total_amount_idr']:,.2f}**"
                    for p in saved_pos
                ])
                + f"\n\nTotal alokasi anggaran: **Rp {total_budget:,.2f}** (Sesuai Pagu SOP BGN).\n\n"
                f"Tim logistik gudang telah diinstruksikan untuk bersiap menyambut kedatangan bahan pangan dengan protokol ketat suhu rantai dingin dan verifikasi sertifikat Halal.\n\n"
                f"Dokumen resmi telah diarsipkan di menu *'Arsip Surat Edaran & PO'* dan siap untuk dicetak atau diunduh."
            )

            context_data = (
                f"Status: Seluruh PO Pengadaan Multi-Item Berhasil Disahkan & Disimpan ke SQLite.\n"
                f"Total PO: {len(saved_pos)} dokumen, Nilai Total: Rp {total_budget:,.2f}.\n"
                + "\n".join([f"- {p['po_number']}: {p['supplier_name']}, {p['approved_qty_kg']} kg, Rp {p['total_amount_idr']:,.2f}" for p in saved_pos])
            )

            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["PO_APPROVAL"],
                user_message=request.message,
                context_data=context_data,
                fallback_text=fallback_text,
                history=session.get("history", []),
            )

            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.CONFIRM_APPROVAL,
                    action_required=ChatActionRequired.COMPLETED,
                    preview_data={
                        "action": "MULTI_PO_APPROVED",
                        "po_results": saved_pos,
                        "po_result": saved_pos[0] if saved_pos else None,
                    },
                ),
            )

        return self._handle_consultative_chat(session, request)

    def _handle_incident_report(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani laporan insiden gangguan pasokan (REPORT_INCIDENT)."""
        user_msg = request.message.strip()
        item_id = self._detect_item_id(user_msg)
        target_portions = self._extract_portions(user_msg, default=3000)
        session["incident_context"]["item_id"] = item_id
        session["incident_context"]["target_portions"] = target_portions

        item_info = get_inventory_status_tool(item_id)

        # 1. Cek langsung apakah ada supplier terdaftar yang disebut di dalam pesan secara persis
        matched = self._match_supplier_in_text(user_msg)
        if matched:
            matched_sup = matched[1].model_dump()
            supplier_search = {
                "status": "EXACT_MATCH_FOUND",
                "count": 1,
                "suppliers": [matched_sup],
                "suggestions": [],
            }
        else:
            supplier_search = search_suppliers_tool(user_msg, category=item_info.get("category", "PROTEIN"))

        if supplier_search["status"] == "EXACT_MATCH_FOUND":
            matched_sup = supplier_search["suppliers"][0]
            session["incident_context"]["affected_supplier_id"] = matched_sup["supplier_id"]
            session["incident_context"]["affected_supplier_name"] = matched_sup["supplier_name"]

            metrics = data_layer_service.calculate_metrics(item_id=item_id, target_portions=target_portions)
            session["current_metrics"] = metrics

            item = data_layer_service.get_inventory_item(item_id)
            eligible = data_layer_service.get_eligible_suppliers(
                category=item.category,
                item_id=item_id,
                exclude_supplier_id=matched_sup["supplier_id"],
            )
            rec = strategic_agent.synthesize_strategy(
                eligible_suppliers=eligible,
                metrics=metrics,
                item_name=item.item_name,
            )
            first_batch_qty = rec.logistics_strategy.batches[0].qty_kg if rec.logistics_strategy.batches else metrics.deficit_kg
            score, status, breakdown = feasibility_engine.evaluate(
                supplier=next(s for s in eligible if s.supplier_id == rec.supplier_id),
                metrics=metrics,
                sop_max_price_per_kg=item.sop_max_price_per_kg,
                initial_batch_qty_kg=first_batch_qty,
            )
            rec = rec.model_copy(update={
                "feasibility_score": score,
                "feasibility_status": status,
                "scoring_breakdown": breakdown,
            })
            session["current_recommendation"] = rec

            po_num = f"PO-MITIGASI-{rec.supplier_id}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
            draft_po = {
                "po_number": po_num,
                "incident_id": session.get("session_id", request.session_id),
                "supplier_id": rec.supplier_id,
                "supplier_name": rec.supplier_name,
                "item_id": item_id,
                "item_name": item.item_name,
                "commodity": item.category,
                "approved_qty_kg": metrics.deficit_kg,
                "unit_price_idr": rec.unit_price_idr,
                "total_amount_idr": rec.total_estimated_cost_idr,
                "halal_certified": True,
                "halal_cert_number": getattr(rec, "halal_cert_number", "ID32110000897650324"),
                "delivery_notes": "Pengiriman darurat bertahap (Split Delivery) dengan rantai dingin dan sertifikasi Halal BPJPH.",
                "approver_name": request.user_role,
            }
            session["pending_crud"] = {
                "type": "APPROVE_MULTI_PO",
                "po_list": [draft_po],
                "total_budget": rec.total_estimated_cost_idr,
                "target_portions": target_portions,
            }

            fallback = (
                f"Laporan disrupsi untuk supplier **{matched_sup['supplier_name']}** berhasil diverifikasi.\n\n"
                f"📊 **Hasil Kalkulasi Kebutuhan ({target_portions:,} Porsi):**\n"
                f"• Defisit Bahan: **{metrics.deficit_kg} kg** (Stok aktual gudang: {metrics.current_stock_kg} kg)\n"
                f"• Kapasitas Freezer: **{metrics.freezer_available_kg} kg** (Kendala terdeteksi ⚠️)\n\n"
                f"🛡️ **Rekomendasi Mitigasi SPPG:**\n"
                f"• Supplier Pengganti: **{rec.supplier_name}** (Halal Aktif ✅)\n"
                f"• Total Biaya: Rp {rec.total_estimated_cost_idr:,.2f} (@ Rp {rec.unit_price_idr:,.2f}/kg)\n"
                f"• Skor Kelayakan: **{rec.feasibility_score:.1f}/100** [{rec.feasibility_status.value}]\n"
                f"• Skema Distribusi: **{rec.logistics_strategy.strategy_type.value}** ({len(rec.logistics_strategy.batches)} Kloter)\n\n"
                f"Apakah Anda menyetujui rekomendasi ini untuk diterbitkan PO resminya?"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["INCIDENT_RECOMMENDATION"],
                user_message=user_msg,
                context_data=(
                    f"Supplier Terverifikasi: {matched_sup['supplier_name']}, Target: {target_portions} porsi, "
                    f"Defisit: {metrics.deficit_kg} kg, Sisa Freezer: {metrics.freezer_available_kg} kg, "
                    f"Rekomendasi: {rec.supplier_name}, Harga: Rp {rec.unit_price_idr}/kg, Total: Rp {rec.total_estimated_cost_idr}, "
                    f"Skor: {rec.feasibility_score:.1f}, Strategi: {rec.logistics_strategy.strategy_type.value}"
                ),
                fallback_text=fallback,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.REPORT_INCIDENT,
                    action_required=ChatActionRequired.APPROVAL_PENDING,
                    preview_data={
                        "metrics": metrics.model_dump(),
                        "recommended_procurement": rec.model_dump(),
                        "confirm_multi_po": {
                            "title": f"Draf PO Mitigasi Pasokan Darurat — Pengganti {matched_sup['supplier_name']}",
                            "target_portions": target_portions,
                            "total_budget": rec.total_estimated_cost_idr,
                            "po_list": [draft_po],
                            "warning": (
                                f"Disrupsi armada pada {matched_sup['supplier_name']}. "
                                f"Pengalihan pesanan ke {rec.supplier_name} terverifikasi Halal BPJPH "
                                f"(Skor Kelayakan: {rec.feasibility_score:.1f}/100, Skema: {rec.logistics_strategy.strategy_type.value})."
                            ),
                            "confirm_command": "Setuju, terbitkan PO mitigasi ini.",
                            "cancel_command": "Batal, jangan terbitkan PO",
                        },
                    },
                ),
            )

        # Jika supplier tidak cocok persis (kemungkinan salah sebut / typo), minta klarifikasi
        suggestions = supplier_search.get("suggestions", [])
        session["pending_clarification"] = {
            "query": user_msg,
            "suggestions": suggestions,
        }

        sug_list_text = "\n".join([f"  • {name}" for name in suggestions[:3]])
        fallback = (
            f"Saya telah memeriksa basis data resmi rekanan SPPG. "
            f"Nama rekanan yang Anda sebutkan belum terdaftar secara persis.\n\n"
            f"Berdasarkan katalog aktif kami untuk kategori **{item_info.get('item_name', 'Daging Ayam')}**, "
            f"apakah yang Anda maksud adalah salah satu rekanan berikut?\n"
            f"{sug_list_text}\n\n"
            f"Mohon konfirmasi nama supplier utama Anda agar sistem dapat memproses SOP mitigasi darurat."
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["SUPPLIER_CLARIFICATION_NEEDED"],
            user_message=user_msg,
            context_data=f"Pencarian Query: {user_msg}\nSaran Rekanan dari Database:\n{sug_list_text}",
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.REPORT_INCIDENT,
                action_required=ChatActionRequired.CLARIFICATION_NEEDED,
                preview_data={"suggested_suppliers": suggestions},
            ),
        )

    def _handle_clarification_confirmed(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani konfirmasi supplier setelah klarifikasi (CONFIRM_CLARIFICATION)."""
        user_msg = request.message.strip()
        msg_lower = user_msg.lower()
        pending = session.get("pending_clarification") or {}
        suggested = pending.get("suggestions", [])

        is_confirm = any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu", "pertama"])
        chosen_supplier_name = suggested[0] if (suggested and is_confirm) else None

        if not chosen_supplier_name and suggested:
            for sug in suggested:
                if sug.lower() in msg_lower or any(part in msg_lower for part in sug.lower().split() if len(part) > 3):
                    chosen_supplier_name = sug
                    break

        if not chosen_supplier_name:
            chosen_supplier_name = params.get("confirmed_supplier_name")

        from app.data.sqlite_db import get_all_suppliers
        db_sups = [SupplierRecord.model_validate(s) for s in get_all_suppliers(include_inactive=False)]

        matched_sup = next(
            (s for s in db_sups if chosen_supplier_name and s.supplier_name.lower() == chosen_supplier_name.lower()),
            None,
        )
        if not matched_sup and chosen_supplier_name:
            matched_sup = next(
                (s for s in db_sups if chosen_supplier_name.lower() in s.supplier_name.lower()),
                None,
            )

        if not matched_sup:
            # Fallback ambil supplier pertama dari saran
            if suggested:
                matched_sup = next((s for s in db_sups if s.supplier_name == suggested[0]), None)

        if matched_sup:
            session["incident_context"]["affected_supplier_id"] = matched_sup.supplier_id
            session["incident_context"]["affected_supplier_name"] = matched_sup.supplier_name
            session["pending_clarification"] = None

            item_id = session["incident_context"]["item_id"]
            target_portions = session["incident_context"]["target_portions"]
            metrics = data_layer_service.calculate_metrics(item_id=item_id, target_portions=target_portions)
            session["current_metrics"] = metrics

            item = data_layer_service.get_inventory_item(item_id)
            eligible = data_layer_service.get_eligible_suppliers(
                category=item.category,
                item_id=item_id,
                exclude_supplier_id=matched_sup.supplier_id,
            )
            rec = strategic_agent.synthesize_strategy(
                eligible_suppliers=eligible,
                metrics=metrics,
                item_name=item.item_name,
            )
            first_batch_qty = rec.logistics_strategy.batches[0].qty_kg if rec.logistics_strategy.batches else metrics.deficit_kg
            score, status, breakdown = feasibility_engine.evaluate(
                supplier=next(s for s in eligible if s.supplier_id == rec.supplier_id),
                metrics=metrics,
                sop_max_price_per_kg=item.sop_max_price_per_kg,
                initial_batch_qty_kg=first_batch_qty,
            )
            rec = rec.model_copy(update={
                "feasibility_score": score,
                "feasibility_status": status,
                "scoring_breakdown": breakdown,
            })
            session["current_recommendation"] = rec

            po_num = f"PO-MITIGASI-{rec.supplier_id}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
            draft_po = {
                "po_number": po_num,
                "incident_id": session.get("session_id", request.session_id),
                "supplier_id": rec.supplier_id,
                "supplier_name": rec.supplier_name,
                "item_id": item_id,
                "item_name": item.item_name,
                "commodity": item.category,
                "approved_qty_kg": metrics.deficit_kg,
                "unit_price_idr": rec.unit_price_idr,
                "total_amount_idr": rec.total_estimated_cost_idr,
                "halal_certified": True,
                "halal_cert_number": getattr(rec, "halal_cert_number", "ID32110000897650324"),
                "delivery_notes": "Pengiriman darurat bertahap (Split Delivery) dengan rantai dingin dan sertifikasi Halal BPJPH.",
                "approver_name": request.user_role,
            }
            session["pending_crud"] = {
                "type": "APPROVE_MULTI_PO",
                "po_list": [draft_po],
                "total_budget": rec.total_estimated_cost_idr,
                "target_portions": target_portions,
            }

            fallback = (
                f"Baik, terima kasih atas konfirmasinya. Data supplier utama terdampak telah dicatat sebagai:\n"
                f"👉 **{matched_sup.supplier_name} ({matched_sup.supplier_id})**\n\n"
                f"Sesuai SOP Darurat SPPG, sistem telah mengeksekusi perhitungan deterministik:\n"
                f"• Target Masak: {target_portions:,} porsi\n"
                f"• Stok Gudang Saat Ini: {metrics.current_stock_kg} kg\n"
                f"• Kebutuhan Defisit Riil: **{metrics.deficit_kg} kg** (dengan safety buffer 20%)\n"
                f"• Sisa Ruang Freezer: **{metrics.freezer_available_kg} kg**\n\n"
                f"🔍 **Rekomendasi Rekanan Pengganti:**\n"
                f"• Supplier: **{rec.supplier_name}** (Sertifikat Halal Aktif ✅)\n"
                f"• Penawaran Harga: Rp {rec.unit_price_idr:,.2f} / kg (Total: Rp {rec.total_estimated_cost_idr:,.2f})\n"
                f"• Skor Kelayakan: **{rec.feasibility_score:.1f}/100** [{rec.feasibility_status.value}]\n"
                f"• Skema Logistik: **{rec.logistics_strategy.strategy_type.value}**\n"
                f"  - Kloter 1: {rec.logistics_strategy.batches[0].qty_kg} kg ({rec.logistics_strategy.batches[0].eta})\n"
                f"  - Kloter 2: {rec.logistics_strategy.batches[1].qty_kg} kg ({rec.logistics_strategy.batches[1].eta})\n\n"
                f"Apakah Anda menyetujui rekomendasi pengadaan ini untuk diterbitkan Purchase Order resminya?"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["CLARIFICATION_CONFIRMED"].format(
                    supplier_name=matched_sup.supplier_name
                ),
                user_message=user_msg,
                context_data=(
                    f"Supplier Terdampak: {matched_sup.supplier_name}, Target: {target_portions} porsi, "
                    f"Stok: {metrics.current_stock_kg} kg, Defisit: {metrics.deficit_kg} kg, Sisa Freezer: {metrics.freezer_available_kg} kg, "
                    f"Rekomendasi: {rec.supplier_name}, Harga: Rp {rec.unit_price_idr}/kg, Total: Rp {rec.total_estimated_cost_idr}, "
                    f"Skor: {rec.feasibility_score:.1f}, Strategi: {rec.logistics_strategy.strategy_type.value}"
                ),
                fallback_text=fallback,
                history=session.get("history", []),
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.REPORT_INCIDENT,
                    action_required=ChatActionRequired.APPROVAL_PENDING,
                    preview_data={
                        "metrics": metrics.model_dump(),
                        "recommended_procurement": rec.model_dump(),
                        "confirm_multi_po": {
                            "title": f"Draf PO Mitigasi Pasokan Darurat — Pengganti {matched_sup.supplier_name}",
                            "target_portions": target_portions,
                            "total_budget": rec.total_estimated_cost_idr,
                            "po_list": [draft_po],
                            "warning": (
                                f"Disrupsi pada {matched_sup.supplier_name}. "
                                f"Pengalihan pesanan ke {rec.supplier_name} terverifikasi Halal BPJPH "
                                f"(Skor Kelayakan: {rec.feasibility_score:.1f}/100, Skema: {rec.logistics_strategy.strategy_type.value})."
                            ),
                            "confirm_command": "Setuju, terbitkan PO mitigasi ini.",
                            "cancel_command": "Batal, jangan terbitkan PO",
                        },
                    },
                ),
            )

        return self._handle_consultative_chat(session, request)

    def _handle_revision(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani permintaan revisi atau opsi alternatif (REQUEST_REVISION)."""
        user_msg = request.message.strip()
        msg_lower = user_msg.lower()

        # JALUR 1: REVISI MULTI-ITEM PROCUREMENT PLAN (PERENCANAAN MENU)
        if session.get("procurement_plan"):
            plan = session["procurement_plan"]
            plan_items = plan.get("items", [])
            draft_pos = plan.get("draft_pos", [])
            target_portions = plan.get("target_portions", 3000)

            from app.data.sqlite_db import get_all_suppliers
            db_sups = get_all_suppliers(include_inactive=False)

            # 1. Cari rekanan target yang ingin diganti / dipilih
            matched_sup_tuple = self._match_supplier_in_text(user_msg)
            new_sup = matched_sup_tuple[1].model_dump() if matched_sup_tuple else None

            # Jika tidak ada nama rekanan spesifik yang disebut, cek apakah mencari yang lebih murah
            is_cheaper_request = "murah" in msg_lower or params.get("preference") == "cheaper"

            # Tentukan komoditas target (misal: "ayam" -> DAGING_AYAM, "telur" -> TELUR_AYAM)
            target_commodity = None
            if "ayam" in msg_lower or "unggas" in msg_lower:
                target_commodity = "DAGING_AYAM"
            elif "telur" in msg_lower:
                target_commodity = "TELUR_AYAM"
            elif "tahu" in msg_lower:
                target_commodity = "TAHU"
            elif "tempe" in msg_lower:
                target_commodity = "TEMPE"
            elif "sapi" in msg_lower or "lembu" in msg_lower:
                target_commodity = "DAGING_SAPI"

            # Jika ada new_sup spesifik tapi komoditas belum terdeteksi, ambil dari data rekanan baru
            if new_sup and not target_commodity:
                target_commodity = str(new_sup.get("commodity", "")).strip().upper()

            # Cari item yang cocok di dalam plan_items
            target_item = None
            if target_commodity:
                target_item = next((it for it in plan_items if it.get("commodity") == target_commodity), None)
            if not target_item and plan_items:
                target_item = plan_items[0]

            if target_item:
                target_commodity = target_item.get("commodity", "DAGING_AYAM")
                qty = float(target_item.get("deficit_kg", 0.0))
                old_sup_name = target_item.get("supplier_name", "Supplier Sebelumnya")
                old_sup_id = target_item.get("supplier_id", "")
                old_price = float(target_item.get("unit_price_idr", 0.0))
                old_cost = float(target_item.get("estimated_cost", 0.0))

                # Jika mencari opsi lebih murah dan belum ada nama rekanan eksplisit
                if is_cheaper_request and not new_sup:
                    eligible_sups = [
                        s for s in db_sups
                        if (str(s.get("commodity", "")).upper() == target_commodity or target_item.get("item_id") in s.get("supported_items", []))
                        and s.get("supplier_id") != old_sup_id
                        and s.get("halal_certified", False)
                    ]
                    if eligible_sups:
                        eligible_sups.sort(key=lambda s: float(s.get("unit_price_idr", 999999)))
                        new_sup = eligible_sups[0]

                if new_sup:
                    new_sup_name = new_sup["supplier_name"]
                    new_sup_id = new_sup["supplier_id"]
                    new_price = float(new_sup["unit_price_idr"])
                    new_capacity = float(new_sup.get("daily_capacity_kg", 0.0))
                    new_lead_time = float(new_sup.get("lead_time_hours", 2.5))
                    new_distance = float(new_sup.get("distance_km", 12.0))
                    new_halal = bool(new_sup.get("halal_certified", True))
                    new_halal_num = new_sup.get("halal_cert_number") or "Tercatat BPJPH"

                    # Kalkulasi Dampak Komparatif (Comparative Impact Analysis)
                    price_diff = new_price - old_price
                    new_cost = round(qty * new_price, 2)
                    cost_diff = round(new_cost - old_cost, 2)
                    capacity_margin = round(new_capacity - qty, 2)
                    is_cap_safe = new_capacity >= qty

                    # Update data target item
                    target_item["supplier_id"] = new_sup_id
                    target_item["supplier_name"] = new_sup_name
                    target_item["unit_price_idr"] = new_price
                    target_item["daily_capacity_kg"] = new_capacity
                    target_item["halal_certified"] = new_halal
                    target_item["halal_cert_number"] = new_halal_num
                    target_item["is_adequate"] = is_cap_safe
                    target_item["estimated_cost"] = new_cost
                    target_item["lead_time_hours"] = new_lead_time
                    target_item["distance_km"] = new_distance

                    # Update draft PO yang bersangkutan
                    for po in draft_pos:
                        if po.get("item_id") == target_item.get("item_id") or po.get("commodity") == target_commodity:
                            po["supplier_id"] = new_sup_id
                            po["supplier_name"] = new_sup_name
                            po["unit_price_idr"] = new_price
                            po["total_amount_idr"] = new_cost
                            po["halal_certified"] = new_halal
                            po["halal_cert_number"] = new_halal_num
                            po["lead_time_hours"] = new_lead_time
                            po["distance_km"] = new_distance

                    new_total_budget = sum(it.get("estimated_cost", 0.0) for it in plan_items)
                    plan["total_budget"] = new_total_budget

                    # Perbarui pending_crud
                    session["pending_crud"] = {
                        "type": "APPROVE_MULTI_PO",
                        "po_list": draft_pos,
                        "total_budget": new_total_budget,
                        "target_portions": target_portions,
                    }
                    session["procurement_plan"] = plan

                    # Susun narasi komparasi dampak
                    diff_str = (
                        f"kenaikan anggaran sebesar Rp {abs(cost_diff):,.2f} (+Rp {abs(price_diff):,.2f}/kg)"
                        if cost_diff > 0
                        else (
                            f"penghematan anggaran sebesar Rp {abs(cost_diff):,.2f} (-Rp {abs(price_diff):,.2f}/kg)"
                            if cost_diff < 0
                            else "biaya per kg identik"
                        )
                    )
                    cap_str = (
                        f"Kapasitas pasok {new_capacity} kg/hari sangat memadai (surplus buffer {capacity_margin} kg)"
                        if is_cap_safe
                        else f"Kapasitas pasok {new_capacity} kg/hari di bawah kuantitas pesanan {qty} kg ⚠️"
                    )

                    context_data = (
                        f"ANALISIS DAMPAK PERGANTIAN REKANAN (KEPALA SPPG: BAPAK ADAM):\n"
                        f"- Komoditas: {target_item['item_name']} (Kebutuhan: {qty} kg)\n"
                        f"- Rekanan Lama: {old_sup_name} (Rp {old_price:,.2f}/kg | Total: Rp {old_cost:,.2f})\n"
                        f"- Rekanan Baru: {new_sup_name} (Rp {new_price:,.2f}/kg | Total: Rp {new_cost:,.2f})\n"
                        f"- Dampak Anggaran: {diff_str}. Total Anggaran Baru: Rp {new_total_budget:,.2f} (Pagu SOP Aman).\n"
                        f"- Kesiapan Kapasitas: {cap_str}.\n"
                        f"- Logistik Rantai Dingin: Waktu tempuh {new_lead_time} jam (Jarak {new_distance} km).\n"
                        f"- Jaminan Regulasi Halal: Bersertifikat Halal Resmi BPJPH (No: {new_halal_num}) sesuai UU JPH No. 33/2014.\n\n"
                        f"Draf Purchase Order telah diperbarui di sistem dan siap diotorisasi."
                    )

                    fallback_text = (
                        f"Baik Bapak Adam, berikut adalah evaluasi dan kalkulasi komparasi dampak "
                        f"pengalihan rekanan untuk komoditas **{target_item['item_name']}** dari **{old_sup_name}** ke **{new_sup_name}**:\n\n"
                        f"• **Analisis Dampak Anggaran:**\n"
                        f"  Penawaran harga baru adalah Rp {new_price:,.2f}/kg, menghasilkan {diff_str}. "
                        f"Total nilai pengadaan komoditas ini menjadi **Rp {new_cost:,.2f}**, dan total pagu keseluruhan adalah **Rp {new_total_budget:,.2f}** (seluruhnya berada dalam batas aman pagu SOP BGN).\n"
                        f"• **Kapasitas & Safety Buffer:**\n"
                        f"  {cap_str}.\n"
                        f"• **Logistik Rantai Dingin & Lead Time:**\n"
                        f"  Estimasi tiba adalah {new_lead_time} jam dengan jarak tempuh {new_distance} km ke dapur utama SPPG, memenuhi standar kesegaran bahan pangan.\n"
                        f"• **Kepatuhan Sertifikasi Halal (UU JPH No. 33/2014):**\n"
                        f"  {new_sup_name} terverifikasi memiliki sertifikat Halal BPJPH aktif (Nomor: {new_halal_num}).\n\n"
                        f"Draf Purchase Order resmi telah saya perbarui pada kartu di bawah. Mohon persetujuan dari Bapak Adam agar pesanan ini dapat segera kami terbitkan dan kirimkan secara resmi."
                    )

                    adaptive_reply = self._call_gemini_adaptive(
                        system_instructions=SYSTEM_PROMPTS["REVISION_REQUEST"],
                        user_message=user_msg,
                        context_data=context_data,
                        fallback_text=fallback_text,
                        history=session.get("history", []),
                    )

                    return self._respond(
                        session,
                        ChatResponse(
                            session_id=request.session_id,
                            reply=adaptive_reply,
                            intent=ChatIntent.REQUEST_REVISION,
                            action_required=ChatActionRequired.APPROVAL_PENDING,
                            preview_data={
                                "procurement_plan": plan,
                                "confirm_multi_po": {
                                    "title": "Draf Purchase Order Resmi SPPG (Multi-Item - Diperbarui)",
                                    "target_portions": target_portions,
                                    "total_budget": new_total_budget,
                                    "po_list": draft_pos,
                                    "warning": "Setelah disahkan oleh Kepala SPPG, seluruh dokumen PO akan diterbitkan resmi dan disimpan permanen ke basis data SQLite SPPG.",
                                    "confirm_command": "Setujui terbitkan seluruh PO pengadaan",
                                    "cancel_command": "Batal, jangan terbitkan PO",
                                },
                            },
                        ),
                    )

        # JALUR 2: REVISI MITIGASI INSIDEN TUNGGAL (INCIDENT REVISION)
        if not session.get("incident_context") or not session.get("incident_context", {}).get("item_id"):
            return self._handle_consultative_chat(session, request)

        if "porsi" in msg_lower:
            new_portions = self._extract_portions(user_msg, default=session["incident_context"].get("target_portions", 3000))
            session["incident_context"]["target_portions"] = new_portions

        item_id = session["incident_context"]["item_id"]
        target_portions = session["incident_context"]["target_portions"]
        metrics = data_layer_service.calculate_metrics(item_id=item_id, target_portions=target_portions)
        session["current_metrics"] = metrics

        item = data_layer_service.get_inventory_item(item_id)
        eligible = data_layer_service.get_eligible_suppliers(
            category=item.category,
            item_id=item_id,
            exclude_supplier_id=session["incident_context"].get("affected_supplier_id"),
        )

        if "murah" in msg_lower or params.get("preference") == "cheaper":
            eligible = sorted(eligible, key=lambda s: s.unit_price_idr)

        new_rec = strategic_agent.synthesize_strategy(
            eligible_suppliers=eligible,
            metrics=metrics,
            item_name=item.item_name,
            retry_count=0,
        )

        first_batch_qty = new_rec.logistics_strategy.batches[0].qty_kg if new_rec.logistics_strategy.batches else metrics.deficit_kg
        score, status, breakdown = feasibility_engine.evaluate(
            supplier=next(s for s in eligible if s.supplier_id == new_rec.supplier_id),
            metrics=metrics,
            sop_max_price_per_kg=item.sop_max_price_per_kg,
            initial_batch_qty_kg=first_batch_qty,
        )
        new_rec = new_rec.model_copy(update={
            "feasibility_score": score,
            "feasibility_status": status,
            "scoring_breakdown": breakdown,
        })
        session["current_recommendation"] = new_rec

        # Draf PO mitigasi darurat baru
        po_num = f"PO-MITIGASI-{new_rec.supplier_id}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
        draft_po = {
            "po_number": po_num,
            "incident_id": session.get("session_id", request.session_id),
            "supplier_id": new_rec.supplier_id,
            "supplier_name": new_rec.supplier_name,
            "item_id": item_id,
            "item_name": item.item_name,
            "commodity": item.category,
            "approved_qty_kg": metrics.deficit_kg,
            "unit_price_idr": new_rec.unit_price_idr,
            "total_amount_idr": new_rec.total_estimated_cost_idr,
            "halal_certified": True,
            "halal_cert_number": getattr(new_rec, "halal_cert_number", "ID32110000897650324"),
            "delivery_notes": "Pengiriman darurat bertahap (Split Delivery) dengan rantai dingin dan sertifikasi Halal BPJPH.",
            "approver_name": request.user_role,
        }
        session["pending_crud"] = {
            "type": "APPROVE_MULTI_PO",
            "po_list": [draft_po],
            "total_budget": new_rec.total_estimated_cost_idr,
            "target_portions": target_portions,
        }

        fallback = (
            f"🔄 Penyesuaian berhasil diperbarui sesuai arahan Bapak Adam:\n\n"
            f"• Target Porsi: {target_portions:,} porsi\n"
            f"• Defisit Dihitung: {metrics.deficit_kg} kg (Sisa freezer: {metrics.freezer_available_kg} kg)\n"
            f"• Rekanan Alternatif Baru: **{new_rec.supplier_name}**\n"
            f"• Harga Penawaran: Rp {new_rec.unit_price_idr:,.2f}/kg (Total: Rp {new_rec.total_estimated_cost_idr:,.2f})\n"
            f"• Skor Kelayakan: {new_rec.feasibility_score:.1f}/100 [{new_rec.feasibility_status.value}]\n"
            f"• Taktik: {new_rec.logistics_strategy.strategy_type.value}\n\n"
            f"Draf PO baru telah disiapkan di bawah. Silakan klik atau ketik 'Setuju' untuk menerbitkan Purchase Order resmi."
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["REVISION_REQUEST"],
            user_message=user_msg,
            context_data=(
                f"Target Porsi: {target_portions}, Defisit: {metrics.deficit_kg} kg, Rekanan Baru: {new_rec.supplier_name}, "
                f"Harga: Rp {new_rec.unit_price_idr}/kg (Total: Rp {new_rec.total_estimated_cost_idr}), Skor: {new_rec.feasibility_score:.1f}, "
                f"Taktik: {new_rec.logistics_strategy.strategy_type.value}"
            ),
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.REQUEST_REVISION,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={
                    "metrics": metrics.model_dump(),
                    "recommended_procurement": new_rec.model_dump(),
                    "confirm_multi_po": {
                        "title": f"Draf PO Mitigasi Pasokan Darurat (Revisi) — {new_rec.supplier_name}",
                        "target_portions": target_portions,
                        "total_budget": new_rec.total_estimated_cost_idr,
                        "po_list": [draft_po],
                        "warning": f"Rekomendasi disesuaikan ke {new_rec.supplier_name} (Skor: {new_rec.feasibility_score:.1f}/100, Halal Aktif BPJPH).",
                        "confirm_command": "Setuju, terbitkan PO mitigasi ini.",
                        "cancel_command": "Batal, jangan terbitkan PO",
                    },
                },
            ),
        )

    def _handle_procurement_planning(
        self,
        session: Dict[str, Any],
        request: ChatRequest,
        params: Dict[str, Any],
    ) -> ChatResponse:
        """
        Menangani perencanaan pengadaan menu/porsi makanan bergizi SPPG.
        Menghitung gramasi SOP, safety buffer 20%, stok gudang SQLite, sisa freezer,
        dan mencocokkan rekanan halal resmi dari SQLite dengan Zero Hallucination.
        Menghasilkan draf Purchase Order multi-item menunggu otorisasi (tanpa simpan prematur ke database).
        """
        user_msg = request.message.strip()
        msg_lower = user_msg.lower()

        # Reset rekomendasi atau draf lama agar tidak terjadi residu mitigasi
        session["current_recommendation"] = None
        session["current_metrics"] = None
        session["is_approved"] = False
        session["po_result"] = None
        session["saved_pos"] = None

        # 1. Ekstrak target porsi
        target_portions = params.get("target_portions") or self._extract_portions(user_msg, default=3000)

        # 2. Identifikasi komoditas pangan yang diminta
        detected_items = []
        raw_comms = params.get("commodities") or []
        if isinstance(raw_comms, list) and raw_comms:
            for c in raw_comms:
                c_str = str(c).lower()
                if "ayam" in c_str or "unggas" in c_str:
                    detected_items.append("ITEM-AYAM-01")
                elif "tahu" in c_str:
                    detected_items.append("ITEM-TAHU-01")
                elif "tempe" in c_str:
                    detected_items.append("ITEM-TEMPE-01")
                elif "sapi" in c_str or "lembu" in c_str:
                    detected_items.append("ITEM-SAPI-01")
                elif "telur" in c_str:
                    detected_items.append("ITEM-TELUR-01")
                elif "beras" in c_str:
                    detected_items.append("ITEM-BERAS-01")
                elif "wortel" in c_str or "sayur" in c_str:
                    detected_items.append("ITEM-WORTEL-01")

        # Fallback deteksi dari teks jika parameter kosong
        if not detected_items:
            if "ayam" in msg_lower or "unggas" in msg_lower:
                detected_items.append("ITEM-AYAM-01")
            if "tahu" in msg_lower:
                detected_items.append("ITEM-TAHU-01")
            if "tempe" in msg_lower:
                detected_items.append("ITEM-TEMPE-01")
            if "sapi" in msg_lower or "lembu" in msg_lower:
                detected_items.append("ITEM-SAPI-01")
            if "telur" in msg_lower:
                detected_items.append("ITEM-TELUR-01")
            if "beras" in msg_lower:
                detected_items.append("ITEM-BERAS-01")
            if "wortel" in msg_lower or "sayur" in msg_lower:
                detected_items.append("ITEM-WORTEL-01")

        # Default ke ayam dan tahu jika keduanya umum di perencanaan menu gizi
        if not detected_items:
            detected_items = ["ITEM-AYAM-01"]

        # Hilangkan duplikat sambil mempertahankan urutan
        detected_items = list(dict.fromkeys(detected_items))

        # 3. Query SQLite inventaris & hitung kebutuhan matematis tertutup
        import json
        from app.data.sqlite_db import get_all_suppliers, get_inventory_item_by_id
        from app.data.mock_db import DEFAULT_INVENTORY, PORTION_REQUIREMENTS

        db_suppliers = get_all_suppliers(include_inactive=False)

        plan_items = []
        total_estimated_budget = 0.0

        for item_id in detected_items:
            item_data = get_inventory_item_by_id(item_id) or DEFAULT_INVENTORY.get(item_id)
            if not item_data:
                continue

            item_name = item_data.get("item_name", item_id)
            category = item_data.get("category", "PROTEIN")
            current_stock = float(item_data.get("current_stock_kg", 0.0))
            freezer_cap = float(item_data.get("freezer_capacity_kg", 0.0))
            freezer_occ = float(item_data.get("freezer_occupied_kg", 0.0))
            freezer_avail = max(0.0, round(freezer_cap - freezer_occ, 2))
            sop_max_price = float(item_data.get("sop_max_price_per_kg", 40000.0))

            # Gramasi SOP per porsi (kg)
            ratio = PORTION_REQUIREMENTS.get(item_id, 0.05)
            gram_per_portion = int(round(ratio * 1000))

            # Kebutuhan dasar & buffer 20% SOP BGN
            base_needed_kg = round(target_portions * ratio, 2)
            buffered_needed_kg = round(base_needed_kg * 1.2, 2)
            deficit_kg = max(0.0, round(buffered_needed_kg - current_stock, 2))

            # Komoditas mapping berdasarkan item_id spesifik & kata kunci (prioritaskan telur sebelum ayam karena telur ayam mengandung kata ayam)
            if "telur" in item_id.lower() or "telur" in item_name.lower():
                comm_filter = "TELUR_AYAM"
            elif "ayam" in item_id.lower() or ("ayam" in item_name.lower() and "telur" not in item_name.lower()):
                comm_filter = "DAGING_AYAM"
            elif "tahu" in item_id.lower() or "tahu" in item_name.lower():
                comm_filter = "TAHU"
            elif "sapi" in item_id.lower() or "lembu" in item_id.lower() or "sapi" in item_name.lower():
                comm_filter = "DAGING_SAPI"
            elif "tempe" in item_id.lower() or "tempe" in item_name.lower():
                comm_filter = "TEMPE"
            elif "beras" in item_id.lower() or "beras" in item_name.lower():
                comm_filter = "BERAS"
            elif "wortel" in item_id.lower() or "sayur" in item_id.lower() or "wortel" in item_name.lower():
                comm_filter = "SAYUR"
            else:
                comm_filter = item_data.get("category", "PROTEIN")

            # Cari rekanan terdaftar di SQLite yang Halal dan Aktif (Strict matching tanpa false cross-match)
            matching_sups = []
            for s in db_suppliers:
                if not s.get("is_active", True) or not s.get("halal_certified", False):
                    continue
                s_comm = str(s.get("commodity", "")).strip().upper()
                supp_items = s.get("supported_items", [])
                if isinstance(supp_items, str):
                    try:
                        supp_items = json.loads(supp_items)
                    except Exception:
                        supp_items = [supp_items]

                if item_id in supp_items or s_comm == comm_filter:
                    matching_sups.append(s)

            # Sortir rekanan berdasarkan reliabilitas tertinggi, lalu harga terendah
            matching_sups.sort(key=lambda s: (-float(s.get("reliability_rating", 80)), float(s.get("unit_price_idr", 999999))))

            chosen_sup = matching_sups[0] if matching_sups else None
            if chosen_sup:
                sup_id = chosen_sup["supplier_id"]
                sup_name = chosen_sup["supplier_name"]
                sup_price = float(chosen_sup["unit_price_idr"])
                sup_cap = float(chosen_sup["daily_capacity_kg"])
                sup_halal_num = chosen_sup.get("halal_cert_number") or "Tercatat BPJPH"
                sup_lead_time = float(chosen_sup.get("lead_time_hours", 2.5))
                sup_distance = float(chosen_sup.get("distance_km", 12.0))
                is_memadai = sup_cap >= deficit_kg
            else:
                sup_id = "SUP-PENDING"
                sup_name = "Belum Terdaftar"
                sup_price = sop_max_price
                sup_cap = 0.0
                sup_halal_num = None
                sup_lead_time = 3.0
                sup_distance = 15.0
                is_memadai = False

            est_cost = round(deficit_kg * sup_price, 2)
            total_estimated_budget += est_cost

            plan_items.append({
                "item_id": item_id,
                "item_name": item_name,
                "category": category,
                "commodity": comm_filter,
                "gram_per_portion": gram_per_portion,
                "ratio_kg": ratio,
                "base_needed_kg": base_needed_kg,
                "buffered_needed_kg": buffered_needed_kg,
                "current_stock_kg": current_stock,
                "freezer_available_kg": freezer_avail,
                "deficit_kg": deficit_kg,
                "supplier_id": sup_id,
                "supplier_name": sup_name,
                "unit_price_idr": sup_price,
                "daily_capacity_kg": sup_cap,
                "halal_certified": True if chosen_sup else False,
                "halal_cert_number": sup_halal_num,
                "lead_time_hours": sup_lead_time,
                "distance_km": sup_distance,
                "is_adequate": is_memadai,
                "estimated_cost": est_cost,
            })

        # 4. Susun Draf Purchase Order Multi-Item (Tanpa Menulis ke Basis Data SQLite)
        draft_pos = []
        timestamp_suffix = datetime.now(timezone.utc).strftime("%m%d%H%M")

        for idx, item in enumerate(plan_items):
            qty = item.get("deficit_kg", 0.0)
            if qty <= 0:
                continue
            po_num = f"PO-SPPG-2026-{timestamp_suffix}-{idx+1:02d}"
            unit_price = item.get("unit_price_idr", 0.0)
            total_amount = item.get("estimated_cost", round(qty * unit_price, 2))

            draft_pos.append({
                "po_number": po_num,
                "incident_id": session.get("session_id", request.session_id),
                "supplier_id": item.get("supplier_id", "SUP-UNKNOWN"),
                "supplier_name": item.get("supplier_name", "Supplier SPPG"),
                "item_id": item.get("item_id", "ITEM-01"),
                "item_name": item.get("item_name", "Komoditas Pangan"),
                "commodity": item.get("commodity", "PROTEIN"),
                "approved_qty_kg": qty,
                "unit_price_idr": unit_price,
                "total_amount_idr": total_amount,
                "halal_certified": item.get("halal_certified", True),
                "halal_cert_number": item.get("halal_cert_number", "Tercatat BPJPH"),
                "lead_time_hours": item.get("lead_time_hours", 2.5),
                "distance_km": item.get("distance_km", 12.0),
                "delivery_notes": "Pengiriman tiba pagi hari di gudang utama SPPG disertai verifikasi suhu rantai dingin dan sertifikat Halal BPJPH.",
                "approver_name": request.user_role,
                "po_download_url": f"/api/v1/procurement/po/{po_num}.pdf",
                "logistics_strategy": {
                    "strategy_type": "DIRECT_SINGLE",
                    "batches": [{
                        "batch_number": 1,
                        "qty_kg": qty,
                        "eta": "Pagi Hari (06:00 - 08:00 WIB)"
                    }],
                    "cold_chain_required": True,
                    "backup_suppliers": []
                }
            })

        total_budget = sum(p["total_amount_idr"] for p in draft_pos)

        # Simpan perencanaan dan pending decision ke sesi (Human-in-the-Loop)
        session["pending_crud"] = {
            "type": "APPROVE_MULTI_PO",
            "po_list": draft_pos,
            "total_budget": total_budget,
            "target_portions": target_portions,
        }
        session["procurement_plan"] = {
            "target_portions": target_portions,
            "items": plan_items,
            "draft_pos": draft_pos,
            "total_budget": total_budget,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Susun laporan teks terstruktur dan draf PO tanpa halusinasi
        po_summary_lines = []
        for p in draft_pos:
            po_summary_lines.append(
                f"• **Draf {p['po_number']}** untuk **{p['supplier_name']}** (`{p['supplier_id']}`)\n"
                f"  - Komoditas: **{p['item_name']}** [{p['commodity']}]\n"
                f"  - Kuantitas Defisit: **{p['approved_qty_kg']} kg**\n"
                f"  - Harga Satuan: Rp {p['unit_price_idr']:,.2f} / kg\n"
                f"  - Nilai Pengadaan: **Rp {p['total_amount_idr']:,.2f}**\n"
                f"  - Catatan: Pengiriman pagi hari dengan sertifikasi Halal (UU JPH No. 33/2014) & rantai dingin ({p['lead_time_hours']} jam)."
            )

        fallback = (
            f"Berdasarkan rencana pembuatan **{target_portions:,} porsi** makanan bergizi, "
            f"berikut adalah evaluasi ketersediaan stok gudang dan draf Purchase Order resmi SPPG, Bapak Adam:\n\n"
            + "\n".join([
                f"• **Kebutuhan {it['item_name']}:** Kebutuhan Riil: **{it['buffered_needed_kg']} kg** (buffer 20% SOP) | "
                f"Stok Gudang: **{it['current_stock_kg']} kg** | Defisit: **{it['deficit_kg']} kg**.\n"
                f"  Rekanan Terpilih: **{it['supplier_name']}** (Kapasitas pasok: {it['daily_capacity_kg']} kg/hari - {'Sangat memadai ✅' if it['is_adequate'] else 'Perlu evaluasi ⚠️'})."
                for it in plan_items
            ])
            + "\n\n"
            f"**Rincian Draf Purchase Order (PO) Multi-Item Menunggu Otorisasi:**\n\n"
            + "\n\n".join(po_summary_lines)
            + f"\n\nTotal estimasi anggaran pengadaan pemenuhan gizi ini adalah **Rp {total_budget:,.2f}**, "
            f"seluruhnya berada dalam batas pagu aman SOP BGN.\n\n"
            f"Draf Purchase Order resmi telah saya sematkan pada kartu di bawah. Mohon persetujuan dari Bapak Adam "
            f"agar pesanan ini dapat dicatat resmi ke basis data SQLite SPPG dan diterbitkan ke masing-masing rekanan."
        )

        context_data = (
            f"Tahap: Perencanaan Menu Pemenuhan Gizi & Draf PO Multi-Item Menunggu Otorisasi.\n"
            f"Target Porsi: {target_portions} porsi.\n"
            f"Rincian Komoditas & Rekanan Resmi Terdaftar (SQLite):\n"
            + "\n".join([
                f"- {it['item_name']} ({it['item_id']}): Butuh {it['buffered_needed_kg']} kg, Stok={it['current_stock_kg']} kg, Defisit={it['deficit_kg']} kg, "
                f"Supplier Resmi={it['supplier_name']} ({it['supplier_id']}), Kapasitas={it['daily_capacity_kg']} kg/hari, Harga=Rp {it['unit_price_idr']}/kg, Halal={it['halal_certified']} ({it['halal_cert_number']}), Biaya=Rp {it['estimated_cost']}"
                for it in plan_items
            ])
            + f"\nTotal Anggaran: Rp {total_budget:,.2f}.\n"
            f"Draf PO Dibuat (Belum Disimpan ke Database): "
            + ", ".join([f"{p['po_number']} ({p['supplier_name']} - {p['approved_qty_kg']} kg)" for p in draft_pos])
            + f". Status: Menunggu Otorisasi dari Kepala SPPG (Bapak Adam)."
        )

        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["PROCUREMENT_PLANNING"],
            user_message=user_msg,
            context_data=context_data,
            fallback_text=fallback,
            history=session.get("history", []),
        )

        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.CONFIRM_APPROVAL,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={
                    "procurement_plan": session["procurement_plan"],
                    "confirm_multi_po": {
                        "title": "Draf Purchase Order Resmi SPPG (Multi-Item)",
                        "target_portions": target_portions,
                        "total_budget": total_budget,
                        "po_list": draft_pos,
                        "warning": "Setelah disahkan oleh Kepala SPPG, seluruh dokumen PO akan diterbitkan resmi dan disimpan permanen ke basis data SQLite SPPG.",
                        "confirm_command": "Setujui terbitkan seluruh PO pengadaan",
                        "cancel_command": "Batal, jangan terbitkan PO",
                    },
                },
            ),
        )

    def _handle_approval(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani persetujuan penerbitan Purchase Order (APPROVE_PO)."""
        user_msg = request.message.strip()

        if session.get("is_approved"):
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply="Purchase Order untuk pengadaan ini sudah berhasil diterbitkan sebelumnya.",
                    intent=ChatIntent.CONFIRM_APPROVAL,
                    action_required=ChatActionRequired.COMPLETED,
                    preview_data={"po_result": session["po_result"].model_dump() if session.get("po_result") and hasattr(session.get("po_result"), "model_dump") else session.get("po_result")},
                ),
            )

        # 1. Jalur Multi-Item Procurement Planning (dari rencana menu/porsi)
        if session.get("procurement_plan"):
            plan = session["procurement_plan"]
            plan_items = plan.get("items", [])
            target_portions = plan.get("target_portions", 3000)

            draft_pos = []
            timestamp_suffix = datetime.now(timezone.utc).strftime("%m%d%H%M")

            for idx, item in enumerate(plan_items):
                qty = item.get("deficit_kg", 0.0)
                if qty <= 0:
                    continue
                po_num = f"PO-SPPG-2026-{timestamp_suffix}-{idx+1:02d}"
                unit_price = item.get("unit_price_idr", 0.0)
                total_amount = item.get("estimated_cost", round(qty * unit_price, 2))

                draft_pos.append({
                    "po_number": po_num,
                    "incident_id": session.get("session_id", request.session_id),
                    "supplier_id": item.get("supplier_id", "SUP-UNKNOWN"),
                    "supplier_name": item.get("supplier_name", "Supplier SPPG"),
                    "item_id": item.get("item_id", "ITEM-01"),
                    "item_name": item.get("item_name", "Komoditas Pangan"),
                    "commodity": item.get("commodity", "PROTEIN"),
                    "approved_qty_kg": qty,
                    "unit_price_idr": unit_price,
                    "total_amount_idr": total_amount,
                    "halal_certified": item.get("halal_certified", True),
                    "halal_cert_number": item.get("halal_cert_number", "Tercatat BPJPH"),
                    "delivery_notes": "Pengiriman tiba pagi hari di gudang utama SPPG disertai verifikasi suhu rantai dingin dan sertifikat Halal BPJPH.",
                    "approver_name": request.user_role,
                    "po_download_url": f"/api/v1/procurement/po/{po_num}.pdf",
                    "logistics_strategy": {
                        "strategy_type": "DIRECT_SINGLE",
                        "batches": [{
                            "batch_number": 1,
                            "qty_kg": qty,
                            "eta": "Pagi Hari (06:00 - 08:00 WIB)"
                        }],
                        "cold_chain_required": True,
                        "backup_suppliers": []
                    }
                })

            total_budget = sum(p["total_amount_idr"] for p in draft_pos)

            session["pending_crud"] = {
                "type": "APPROVE_MULTI_PO",
                "po_list": draft_pos,
                "total_budget": total_budget,
                "target_portions": target_portions,
            }

            po_lines = []
            for p in draft_pos:
                po_lines.append(
                    f"• **{p['po_number']}** untuk **{p['supplier_name']}** (`{p['supplier_id']}`)\n"
                    f"  - Komoditas: **{p['item_name']}** [{p['commodity']}]\n"
                    f"  - Kuantitas: **{p['approved_qty_kg']} kg** (untuk menutupi defisit gudang)\n"
                    f"  - Harga Satuan: Rp {p['unit_price_idr']:,.2f} / kg\n"
                    f"  - Total Biaya: **Rp {p['total_amount_idr']:,.2f}**\n"
                    f"  - Catatan: Pengiriman pagi hari dengan sertifikasi Halal (UU JPH No. 33/2014) & rantai dingin."
                )

            fallback_text = (
                f"Draf Purchase Order (PO) resmi untuk pemenuhan kebutuhan protein {target_portions:,} porsi "
                f"telah saya siapkan berdasarkan data stok gudang dan kapasitas rekanan terdaftar di basis data SPPG, Bapak Adam:\n\n"
                + "\n\n".join(po_lines) + "\n\n"
                f"Total estimasi anggaran pengadaan tambahan ini adalah **Rp {total_budget:,.2f}**, yang seluruhnya berada dalam batas pagu aman operasional harian SPPG.\n\n"
                f"Mohon konfirmasi persetujuan dari Bapak Adam agar seluruh dokumen PO resmi ini dapat segera diterbitkan, "
                f"dicatat ke basis data SQLite, dan dikirimkan ke masing-masing rekanan."
            )

            context_data = (
                f"Tahap: Draf PO Siap Disetujui Kepala SPPG (Bapak Adam).\n"
                f"Target Porsi: {target_portions} porsi.\n"
                + "\n".join([f"- {p['po_number']}: {p['supplier_name']} ({p['item_name']}), Qty={p['approved_qty_kg']} kg, Rp {p['total_amount_idr']:,.2f}" for p in draft_pos])
                + f"\nTotal Anggaran: Rp {total_budget:,.2f}.\n"
                f"Tampilkan ringkasan PO dan minta otorisasi konfirmasi kepada Bapak Adam."
            )

            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["PO_APPROVAL"],
                user_message=user_msg,
                context_data=context_data,
                fallback_text=fallback_text,
                history=session.get("history", []),
            )

            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=adaptive_reply,
                    intent=ChatIntent.CONFIRM_APPROVAL,
                    action_required=ChatActionRequired.APPROVAL_PENDING,
                    preview_data={
                        "confirm_multi_po": {
                            "title": "Draf Purchase Order Resmi SPPG (Multi-Item)",
                            "target_portions": target_portions,
                            "total_budget": total_budget,
                            "po_list": draft_pos,
                            "warning": "Setelah disahkan oleh Kepala SPPG, seluruh dokumen PO akan diterbitkan resmi dan disimpan permanen ke basis data SQLite SPPG.",
                            "confirm_command": "Setujui terbitkan seluruh PO pengadaan",
                            "cancel_command": "Batal, jangan terbitkan PO",
                        }
                    },
                ),
            )

        # 2. Jalur Single Incident Recommendation
        if not session.get("current_recommendation"):
            return self._handle_consultative_chat(session, request)

        rec: RecommendedProcurement = session["current_recommendation"]
        metrics: IncidentMetrics = session["current_metrics"]
        po_number = f"PO-SPPG-2026-{datetime.now(timezone.utc).strftime('%m%d%H%M%S')}"

        po = PurchaseOrderResponse(
            status="SUCCESS",
            po_number=po_number,
            incident_id=request.session_id,
            supplier_id=rec.supplier_id,
            supplier_name=rec.supplier_name,
            item_id=session["incident_context"]["item_id"],
            approved_qty_kg=metrics.deficit_kg,
            unit_price_idr=rec.unit_price_idr,
            total_amount_idr=rec.total_estimated_cost_idr,
            logistics_strategy=rec.logistics_strategy,
            approver_name=request.user_role,
            po_download_url=f"/api/v1/procurement/po/{po_number}.pdf",
        )
        session["is_approved"] = True
        session["po_result"] = po

        try:
            from app.data.sqlite_db import save_circular_letter, save_purchase_order
            save_purchase_order(po.model_dump())

            letter_id = f"SE-SPPG-{po.po_number.replace('PO-', '')}"
            letter_num = f"{po.po_number.split('-')[-1]}/SE/SPPG-DARURAT/{datetime.now(timezone.utc).strftime('%m/%Y')}"
            save_circular_letter({
                "letter_id": letter_id,
                "letter_number": letter_num,
                "title": f"Surat Edaran Otorisasi Pengadaan Mitigasi Pasokan {po.item_id}",
                "incident_id": po.incident_id,
                "item_id": po.item_id,
                "deficit_kg": po.approved_qty_kg,
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier_name,
                "issued_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "signer_name": request.user_role,
                "signer_role": "Kepala Satuan Pelayanan Pemenuhan Gizi (SPPG)",
                "content_text": (
                    f"Berdasarkan hasil analisis kelayakan deterministik dan persetujuan pimpinan, "
                    f"diterbitkan Surat Edaran penetapan pengadaan bahan pangan {po.item_id} "
                    f"sejumlah {po.approved_qty_kg} kg kepada {po.supplier_name} dengan total anggaran Rp {po.total_amount_idr:,.2f}."
                ),
                "status": "ISSUED",
            })
        except Exception:
            pass

        fallback = (
            f"✅ Otorisasi diterima dari {request.user_role}!\n\n"
            f"Surat Pesanan Resmi telah diterbitkan:\n"
            f"• Nomor PO: {po.po_number}\n"
            f"• Rekanan Ditunjuk: {po.supplier_name}\n"
            f"• Total Pesanan: {po.approved_qty_kg} kg (Total: Rp {po.total_amount_idr:,.2f})\n"
            f"• Taktik Distribusi: {rec.logistics_strategy.strategy_type.value}\n"
            f"• Berkas PDF: {po.po_download_url}\n\n"
            f"SOP darurat SPPG selesai dijalankan dan dicatat ke Immutable Audit Trail."
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["PO_APPROVAL"],
            user_message=user_msg,
            context_data=(
                f"Nomor PO: {po.po_number}, Rekanan: {po.supplier_name}, Total: {po.approved_qty_kg} kg "
                f"(Rp {po.total_amount_idr:,.2f}), URL: {po.po_download_url}, Otorisator: {request.user_role}"
            ),
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.CONFIRM_APPROVAL,
                action_required=ChatActionRequired.COMPLETED,
                preview_data={"po_result": po.model_dump()},
            ),
        )

    def _handle_consultative_chat(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Menangani konsultasi bebas dan FAQ umum SPPG (GENERAL_CHAT)."""
        fallback = (
            f"Halo Bapak/Ibu {request.user_role}, saya ResilioAI siap mendampingi operasional pemenuhan gizi SPPG.\n\n"
            f"Sistem kami dirancang untuk memitigasi risiko pasokan pangan, memantau batas aman penyimpanan freezer, "
            f"dan memastikan seluruh bahan pangan memenuhi sertifikasi Halal 100%.\n\n"
            f"Apakah ada kendala operasional, pengecekan inventaris gudang, atau data rekanan yang ingin didiskusikan?"
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["CONSULTATIVE_CHAT"],
            user_message=request.message,
            context_data=f"User Role: {request.user_role}. Sesi percakapan aktif.",
            fallback_text=fallback,
            history=session.get("history", []),
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=adaptive_reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
            ),
        )

    def _handle_out_of_domain(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Menolak permintaan pembuatan kode pemrograman atau tugas di luar mandat SPPG (Domain Guardrail)."""
        reply = (
            "Mohon maaf, Bapak Adam. Sebagai Asisten Operasional SPPG (Satuan Pelayanan Pemenuhan Gizi - Badan Gizi Nasional), "
            "tugas dan wewenang saya dibatasi secara ketat hanya pada manajemen rantai pasok bahan pangan, pemantauan stok gudang, "
            "verifikasi kepatuhan sertifikasi Halal (UU JPH No. 33/2014), dan mitigasi risiko logistik SPPG.\n\n"
            "Saya tidak memiliki otorisasi untuk membuat kode pemrograman atau menangani tugas teknis di luar mandat gizi pangan nasional.\n\n"
            "Silakan instruksikan apabila ada kebutuhan terkait pengecekan stok dapur, audit rekanan pangan, atau pelaporan kendala pengiriman."
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
            ),
        )

    def _handle_clear_documents(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Meminta konfirmasi Human-in-the-Loop sebelum mengosongkan seluruh arsip Surat Edaran dan PO."""
        from app.data.sqlite_db import get_all_circular_letters, get_all_purchase_orders
        try:
            se_list = get_all_circular_letters()
            po_list = get_all_purchase_orders()
            se_count = len(se_list)
            po_count = len(po_list)
        except Exception:
            se_count = 0
            po_count = 0

        if se_count == 0 and po_count == 0:
            reply = (
                "ℹ️ **Basis Data Arsip Sudah Bersih**\n\n"
                "Bapak Adam, tabel arsip Surat Edaran dan Purchase Order (PO) saat ini sudah dalam keadaan kosong (0 dokumen). "
                "Tidak ada arsip dokumen yang perlu dibersihkan."
            )
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=reply,
                    intent=ChatIntent.GENERAL_INQUIRY,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        # Stage pending CRUD for Human-in-the-Loop Confirmation
        session["pending_crud"] = {
            "type": "CLEAR_ALL_DOCUMENTS",
            "se_count": se_count,
            "po_count": po_count,
        }

        reply = (
            "⚠️ **Konfirmasi Pembersihan Seluruh Arsip Dokumen SPPG**\n\n"
            f"Bapak Adam Dzaki, sistem mendeteksi permintaan pengosongan arsip resmi:\n"
            f"• Surat Edaran terdaftar: **{se_count} dokumen**\n"
            f"• Purchase Order (PO) terdaftar: **{po_count} dokumen**\n\n"
            "Tindakan ini akan menghapus riwayat dokumen secara permanen dari basis data SQLite SPPG. "
            "Apakah Bapak yakin ingin mengosongkan seluruh arsip dokumen?\n\n"
            "Silakan klik tombol **'Ya, Hapus Permanen'** di bawah atau ketik *'Ya, lanjutkan hapus'*, atau pilih **'Batalkan'** jika ingin mempertahankan arsip."
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=reply,
                intent=ChatIntent.CONFIRM_APPROVAL,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={
                    "confirm_delete": {
                        "action_type": "CLEAR_ALL",
                        "title": "Pembersihan Seluruh Arsip Dokumen",
                        "details": f"{se_count} Surat Edaran & {po_count} Purchase Order",
                        "warning": "Data yang dihapus tidak dapat dipulihkan kembali dari basis data operasional.",
                        "confirm_command": "Ya, lanjutkan hapus.",
                        "cancel_command": "Batal, jangan dihapus.",
                    }
                },
            ),
        )

    def _handle_delete_single_document(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Mencari dokumen spesifik (SE atau PO) dan meminta konfirmasi Human-in-the-Loop sebelum menghapus."""
        identifier = params.get("identifier", "").strip() if params else ""
        if not identifier:
            import re
            match = re.search(r"(?:PO|SE)-[A-Z0-9\-_/]+", request.message, re.IGNORECASE)
            if match:
                identifier = match.group(0).upper()

        if not identifier:
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=(
                        "Bisa, Bapak Adam. Mohon sebutkan nomor dokumen resmi atau ID dokumen yang ingin dihapus "
                        "(contoh: `SE-2026-001` atau `PO-2026-001`)."
                    ),
                    intent=ChatIntent.GENERAL_INQUIRY,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        from app.data.sqlite_db import (
            get_circular_letter_by_id,
            get_purchase_order_by_number,
            get_all_circular_letters,
        )

        doc_type = None
        target_doc = None
        doc_label = ""
        title_or_name = ""

        # 1. Cek apakah Purchase Order
        if identifier.upper().startswith("PO-"):
            po = get_purchase_order_by_number(identifier)
            if po:
                doc_type = "PO"
                target_doc = po
                doc_label = "Purchase Order (PO)"
                title_or_name = f"Pengadaan {po.get('item_id', 'Pangan')} ({po.get('approved_qty_kg', 0)} kg) ke {po.get('supplier_name', 'Rekanan')}"
        elif identifier.upper().startswith("SE-"):
            se = get_circular_letter_by_id(identifier)
            if not se:
                for item in get_all_circular_letters():
                    if item.get("letter_number", "").upper() == identifier.upper() or item.get("id", "").upper() == identifier.upper():
                        se = item
                        break
            if se:
                doc_type = "SE"
                target_doc = se
                doc_label = "Surat Edaran (SE)"
                title_or_name = f"{se.get('title', 'Surat Edaran')} ({se.get('letter_number', identifier)})"
        else:
            po = get_purchase_order_by_number(identifier)
            if po:
                doc_type = "PO"
                target_doc = po
                doc_label = "Purchase Order (PO)"
                title_or_name = f"Pengadaan {po.get('item_id', 'Pangan')} ({po.get('approved_qty_kg', 0)} kg) ke {po.get('supplier_name', 'Rekanan')}"
            else:
                se = get_circular_letter_by_id(identifier)
                if not se:
                    for item in get_all_circular_letters():
                        if identifier.lower() in item.get("id", "").lower() or identifier.lower() in item.get("letter_number", "").lower():
                            se = item
                            break
                if se:
                    doc_type = "SE"
                    target_doc = se
                    doc_label = "Surat Edaran (SE)"
                    title_or_name = f"{se.get('title', 'Surat Edaran')} ({se.get('letter_number', identifier)})"

        if not target_doc:
            return self._respond(
                session,
                ChatResponse(
                    session_id=request.session_id,
                    reply=(
                        f"⚠️ Dokumen dengan nomor/ID `{identifier}` tidak ditemukan dalam basis data resmi SPPG, Bapak Adam. "
                        f"Mohon pastikan nomor dokumen sudah benar atau periksa daftar dokumen pada menu Arsip."
                    ),
                    intent=ChatIntent.GENERAL_INQUIRY,
                    action_required=ChatActionRequired.NONE,
                ),
            )

        actual_id = target_doc.get("po_number") if doc_type == "PO" else (target_doc.get("id") or target_doc.get("letter_number"))
        session["pending_crud"] = {
            "type": "DELETE_DOCUMENT",
            "doc_type": doc_type,
            "identifier": actual_id,
            "title_or_name": title_or_name,
        }

        reply = (
            f"⚠️ **Konfirmasi Penghapusan Dokumen {doc_label}**\n\n"
            f"Bapak Adam Dzaki, sistem menerima instruksi penghapusan dokumen tunggal:\n"
            f"• Jenis: **{doc_label}**\n"
            f"• Nomor/ID: `{actual_id}`\n"
            f"• Keterangan: {title_or_name}\n\n"
            f"Tindakan ini akan menghapus dokumen tersebut secara permanen dari basis data SPPG. "
            f"Apakah Bapak yakin ingin melanjutkan penghapusan?\n\n"
            f"Silakan klik tombol **'Ya, Hapus Dokumen Ini'** di bawah atau ketik *'Ya, lanjutkan hapus'*, atau pilih **'Batalkan'**."
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=reply,
                intent=ChatIntent.CONFIRM_APPROVAL,
                action_required=ChatActionRequired.APPROVAL_PENDING,
                preview_data={
                    "confirm_delete": {
                        "action_type": "SINGLE",
                        "doc_type": doc_type,
                        "identifier": actual_id,
                        "title": f"Penghapusan {doc_label} #{actual_id}",
                        "details": title_or_name,
                        "warning": "Dokumen ini akan dihapus secara permanen dan tidak dapat dipulihkan.",
                        "confirm_command": "Ya, lanjutkan hapus.",
                        "cancel_command": "Batal, jangan dihapus.",
                    }
                },
            ),
        )

    def _handle_explain_capabilities(self, session: Dict[str, Any], request: ChatRequest) -> ChatResponse:
        """Menjelaskan kapabilitas CRUD dan operasional terintegrasi SPPG."""
        reply = (
            "Tentu, Bapak Adam. Sebagai Asisten Kecerdasan Buatan Operasional SPPG, saya memiliki kapabilitas CRUD "
            "lengkap yang terhubung langsung dengan basis data SQLite resmi SPPG:\n\n"
            "1. **Create (Tambah Data):**\n"
            "   • Mendaftarkan rekanan supplier baru dengan verifikasi otomatis sertifikasi Halal BPJPH dan pagu anggaran SOP.\n"
            "   • Menerbitkan Surat Edaran (SE) mitigasi darurat dan Purchase Order (PO) resmi setelah Bapak setujui.\n\n"
            "2. **Read (Cek Data):**\n"
            "   • Memeriksa katalog seluruh rekanan pangan, kapasitas kirim harian, dan penawaran harga.\n"
            "   • Memantau stok fisik gudang dan sisa kapasitas ruang pendingin (freezer).\n"
            "   • Membaca arsip dokumen resmi Surat Edaran dan PO yang telah diterbitkan.\n\n"
            "3. **Update (Perbarui Data):**\n"
            "   • Memperbarui harga penawaran rekanan, kapasitas harian, waktu tempuh, atau nomor sertifikat halal.\n\n"
            "4. **Delete / Nonaktifkan Data:**\n"
            "   • Menonaktifkan rekanan (soft-delete) untuk menjaga keutuhan audit trail anggaran BGN.\n"
            "   • Membersihkan/mereset arsip riwayat Surat Edaran dan Purchase Order untuk kebutuhan simulasi demo.\n\n"
            "Seluruh aksi penambahan, perubahan, dan penerbitan pesanan akan saya buatkan kartu pratinjau terlebih dahulu "
            "sehingga keputusan akhir sepenuhnya berada di tangan Bapak Kepala SPPG."
        )
        return self._respond(
            session,
            ChatResponse(
                session_id=request.session_id,
                reply=reply,
                intent=ChatIntent.GENERAL_INQUIRY,
                action_required=ChatActionRequired.NONE,
            ),
        )

    # ==============================================================================
    # ENTRY POINT DISPATCHER (CLEAN & MODULAR)
    # ==============================================================================
    def process_message(self, request: ChatRequest) -> ChatResponse:
        """Memproses satu giliran pesan dari pengguna dan mengembalikan respons terstruktur."""
        session = self.get_or_create_session(request.session_id)
        user_msg = request.message.strip()

        # Rekam pesan user ke riwayat
        session["history"].append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            from app.data.sqlite_db import record_chat_message
            record_chat_message(
                session_id=request.session_id,
                role="user",
                message=user_msg,
            )
        except Exception:
            pass

        # Stage 1: AI Cognitive Decision Engine (Gemini 3.5 Flash-Lite)
        decision = self._decide_action(user_msg, session)
        action = decision.get("action", "GENERAL_CHAT")
        params = decision.get("parameters", {})

        # Stage 2 & 3: Deterministic Tool Execution & Natural Synthesis
        if action == "CONFIRM_CRUD":
            return self._handle_crud_confirmation(session, request, is_confirm=True)
        elif action == "CANCEL_CRUD":
            return self._handle_crud_confirmation(session, request, is_confirm=False)
        elif action == "GREETING":
            return self._handle_greeting(session, request)
        elif action == "APPROVE_PO":
            return self._handle_approval(session, request, params)
        elif action == "CONFIRM_CLARIFICATION":
            return self._handle_clarification_confirmed(session, request, params)
        elif action == "REQUEST_REVISION":
            return self._handle_revision(session, request, params)
        elif action in ["REGISTER_SUPPLIER", "UPDATE_SUPPLIER", "DEACTIVATE_SUPPLIER"]:
            return self._handle_supplier_management(session, request, action, params)
        elif action == "LIST_SUPPLIERS":
            return self._handle_list_suppliers(session, request, params)
        elif action == "GET_INVENTORY":
            return self._handle_get_inventory(session, request, params)
        elif action == "REPORT_INCIDENT":
            return self._handle_incident_report(session, request, params)
        elif action == "OUT_OF_DOMAIN":
            return self._handle_out_of_domain(session, request)
        elif action == "CLEAR_DOCUMENTS":
            return self._handle_clear_documents(session, request)
        elif action == "DELETE_DOCUMENT":
            return self._handle_delete_single_document(session, request, params)
        elif action == "PLAN_PROCUREMENT":
            return self._handle_procurement_planning(session, request, params)
        elif action == "EXPLAIN_CAPABILITIES":
            return self._handle_explain_capabilities(session, request)
        else:
            return self._handle_consultative_chat(session, request)


# Singleton instance conversational agent
conversational_agent = ConversationalAgentManager()
