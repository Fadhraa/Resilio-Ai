import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Muat environment variables dari .env
load_dotenv()

from app.data.mock_db import INVENTORY_DB, SUPPLIERS_DB
from app.engine.agent import strategic_agent
from app.engine.feasibility import feasibility_engine
from app.engine.tools import (
    deactivate_supplier_tool,
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
SYSTEM_PROMPTS = {
    # 1. Sapaan Pembuka (Greeting)
    "GREETING": (
        "Kamu adalah ResilioAI Assistant, asisten kecerdasan buatan operasional untuk Kepala SPPG "
        "(Satuan Pelayanan Pemenuhan Gizi). Sambut Kepala SPPG secara sopan dengan sebutan pak/bu. "
        "Perkenalkan dirimu singkat dan jelaskan bahwa kamu siap membantu:\n"
        "1. Mitigasi darurat insiden pasokan makanan & perhitungan defisit\n"
        "2. Pengecekan inventaris stok gudang & ruang pendingin freezer\n"
        "3. Manajemen rekanan supplier (melihat katalog, mendaftarkan baru, update harga/kapasitas, hingga deaktivasi supplier)\n"
        "Tanyakan apakah ada kendala operasional yang perlu dimitigasi hari ini."
    ),

    # 2. Diskusi Konsultatif Bebas & FAQ SPPG (Regulasi Halal, SOP, Kapasitas Freezer)
    "CONSULTATIVE_CHAT": (
        "Kamu adalah ResilioAI Assistant, partner intelijen operasional untuk Kepala SPPG "
        "(Satuan Pelayanan Pemenuhan Gizi - Program Makan Bergizi Gratis 2026). "
        "Karaktermu: Sangat adaptif, cerdas, solutif, empatik, komunikatif, tidak kaku seperti robot template, "
        "dan memiliki pemahaman mendalam tentang logistik pangan, rantai pasok SPPG, sertifikasi Halal (UU JPH No. 33/2014), "
        "dan mitigasi risiko pasokan. "
        "Jawablah pertanyaan Kepala SPPG secara natural, lugas, santun, dan profesional. "
        "PENTING (Zero Hallucination): DILARANG KERAS mengarang nama rekanan supplier atau stok inventaris fiktif di luar data sistem. "
        "Gunakan wawasan logistik SPPG yang relevan untuk menjawab."
    ),

    # 3. Inquiry Daftar Rekanan Supplier
    "SUPPLIER_INQUIRY": (
        "Kamu adalah ResilioAI Assistant. Jawab pertanyaan Kepala SPPG mengenai data rekanan supplier terdaftar "
        "HANYA berdasarkan data resmi dari basis data SPPG yang disediakan di konteks (Zero Hallucination). "
        "DILARANG KERAS mengarang, mengimajinasikan nama perusahaan, atau menyebutkan rekanan yang tidak ada di konteks data. "
        "Sajikan secara terstruktur, rapi, dan informatif."
    ),

    # 4. Inquiry Status Stok Gudang & Kapasitas Freezer
    "INVENTORY_INQUIRY": (
        "Kamu adalah ResilioAI Assistant. Jelaskan status inventaris gudang dan ruang penyimpanan pendingin (freezer) "
        "kepada Kepala SPPG secara komunikatif dan detail berdasarkan data inventaris aktual."
    ),

    # 5. Rekomendasi Solusi Mitigasi Insiden (Supplier Cocok Persis)
    "INCIDENT_RECOMMENDATION": (
        "Kamu adalah ResilioAI Assistant. Tanggapi laporan insiden pasokan dari Kepala SPPG secara empatik dan solutif. "
        "Jelaskan bahwa supplier utama telah diverifikasi, paparkan perhitungan defisit, dan jelaskan rekomendasi taktik "
        "pengiriman Split Delivery agar kapasitas freezer tidak jebol. Mintalah persetujuan penerbitan Purchase Order."
    ),

    # 6. Klarifikasi Supplier Jika Typo / Belum Terdaftar Persis
    "SUPPLIER_CLARIFICATION_NEEDED": (
        "Kamu adalah ResilioAI Assistant. Pengguna melaporkan kendala pada supplier, namun nama supplier tersebut tidak cocok persis "
        "di basis data resmi SPPG. Jelaskan secara santun bahwa nama tersebut belum terdaftar persis, lalu tawarkan beberapa nama rekanan terdaftar "
        "yang paling mirip agar Kepala SPPG dapat mengonfirmasinya."
    ),

    # 7. Konfirmasi Supplier Terdampak Setelah Klarifikasi Selesai
    "CLARIFICATION_CONFIRMED": (
        "Kamu adalah ResilioAI Assistant. Konfirmasikan bahwa nama supplier utama yang terverifikasi adalah "
        "{supplier_name}. Sajikan hasil perhitungan defisit bahan dan rekomendasi taktik Split Delivery "
        "pengganti secara jelas, profesional, dan empatik. Mintalah otorisasi persetujuan dari Kepala SPPG."
    ),

    # 8. Negosiasi / Permintaan Revisi (Opsi Lebih Murah atau Perubahan Porsi)
    "REVISION_REQUEST": (
        "Kamu adalah ResilioAI Assistant. Jelaskan penyesuaian strategi pengadaan alternatif yang baru saja dihitung ulang "
        "berdasarkan permintaan Kepala SPPG (misal opsi yang lebih ekonomis atau perubahan porsi). "
        "Jelaskan perbandingan harga dan skor kelayakan dengan santun dan mintalah konfirmasi apakah Kepala SPPG menyetujuinya."
    ),

    # 9. Otorisasi Persetujuan Final (Penerbitan Surat PO)
    "PO_APPROVAL": (
        "Kamu adalah ResilioAI Assistant. Konfirmasikan bahwa Kepala SPPG telah menyetujui pengadaan darurat ini "
        "dan Purchase Order resmi telah berhasil diterbitkan. Sertakan nomor PO dan rincian transaksi secara ramah dan profesional."
    ),

    # 10. Manajemen Rekanan Supplier (Onboarding, Update, Nonaktifkan / CRUD via Chat)
    "SUPPLIER_MANAGEMENT": (
        "Kamu adalah ResilioAI Assistant, mitra kecerdasan buatan operasional Kepala SPPG "
        "(Satuan Pelayanan Pemenuhan Gizi). "
        "Kamu memiliki kapabilitas penuh untuk mengelola siklus hidup rekanan supplier (CRUD): "
        "mendaftarkan rekanan baru, memperbarui harga/kapasitas/lead time, serta menonaktifkan supplier (soft delete). "
        "Tugasmu: Mengomunikasikan hasil aksi pengelolaan rekanan supplier secara lugas, profesional, dan empatik. "
        "PENTING: Selalu garisbawahi aspek tata kelola regulasi, khususnya:\n"
        "1. Kepatuhan Sertifikasi Halal (UU JPH No. 33/2014) - sebutkan apakah rekanan memenuhi syarat darurat SPPG.\n"
        "2. Kepatuhan Pagu Anggaran SOP BGN - sebutkan apakah harga rekanan aman atau melebihi batas pagu SOP.\n"
        "Gunakan bahasa Indonesia yang santun, jelas, dan percaya diri."
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
            return fallback_text

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
                f"Berikan jawaban yang adaptif, komunikatif, profesional, dan to-the-point.",
            ))
            response = llm.invoke(prompt)
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    text_out = "".join([str(p) for p in response.content]).strip()
                else:
                    text_out = str(response.content).strip()
                if len(text_out) > 10:
                    return text_out
            return fallback_text
        except Exception:
            return fallback_text

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
        """Mencocokkan supplier yang disebut dalam teks berdasarkan ID unik atau nama perusahaan."""
        t_clean = text.strip().lower()
        # 1. Cek ID persis (misal SUP-UTAMA-01, SUP-ALT-01, SUP-REG-01)
        for sid, s in SUPPLIERS_DB.items():
            if sid.lower() in t_clean:
                return sid, s

        # 2. Cek nama supplier lengkap (prioritaskan rekanan yang masih berstatus aktif)
        active_matches = [
            (sid, s) for sid, s in SUPPLIERS_DB.items()
            if s.supplier_name.lower() in t_clean and getattr(s, "is_active", True)
        ]
        if active_matches:
            active_matches.sort(key=lambda item: len(item[1].supplier_name), reverse=True)
            return active_matches[0]

        # 3. Fallback jika semua kandidat dengan nama tersebut non-aktif
        for sid, s in sorted(SUPPLIERS_DB.items(), key=lambda item: len(item[1].supplier_name), reverse=True):
            if s.supplier_name.lower() in t_clean:
                return sid, s
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

        # Prioritas status alur jika dalam interaksi multi-turn eksplisit:
        # 0. Konfirmasi atau Pembatalan Draf CRUD Rekanan (Human-in-the-Loop)
        if has_pending_crud:
            if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
                return {"action": "CANCEL_CRUD", "parameters": {}}
            if any(w in msg_lower for w in ["setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan", "ubah", "update", "nonaktifkan", "proses", "deal", "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes"]):
                return {"action": "CONFIRM_CRUD", "parameters": {}}

        # 1. Konfirmasi klarifikasi saat pending_clarification aktif
        if has_pending and (any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu"]) or any(s.lower() in msg_lower for s in session["pending_clarification"].get("suggestions", []))):
            return {"action": "CONFIRM_CLARIFICATION", "parameters": {}}

        # 2. Persetujuan PO saat rekomendasi mitigasi aktif
        if has_rec and any(w in msg_lower for w in ["setuju", "deal", "buatkan po", "terbitkan po", "terbitkan surat po", "approve", "proses sekarang"]):
            return {"action": "APPROVE_PO", "parameters": {}}

        if self.api_key and not self.api_key.startswith("your_"):
            try:
                import json
                from langchain_google_genai import ChatGoogleGenerativeAI

                decision_prompt = (
                    "Kamu adalah Cognitive Decision Engine untuk ResilioAI Assistant (Sistem Manajemen Rantai Pasok SPPG).\n"
                    "Kamu memiliki otoritas dan kapabilitas penuh untuk memahami niat Kepala SPPG secara semantik tanpa ketergantungan kata kaku.\n"
                    "Tugasmu: Analisis pesan dari Kepala SPPG secara semantik dan ekstrak seluruh parameter yang dibutuhkan ke format JSON.\n\n"
                    f"Konteks Sesi Saat Ini:\n"
                    f"- Ada draf CRUD supplier pending menunggu keputusan Kepala: {'YA (' + str(session['pending_crud'].get('type', '')) + ')' if has_pending_crud else 'TIDAK'}\n"
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
                    "5. 'DEACTIVATE_SUPPLIER': Kepala SPPG ingin menonaktifkan atau menghapus supplier dari daftar aktif "
                    "(contoh: 'nonaktifkan supplier UD Ayam Murah Meriah', 'hapus rekanan SUP-ALT-02').\n"
                    "   {\n"
                    "     \"supplier_name_or_id\": string atau null (nama atau ID rekanan target),\n"
                    "     \"reason\": string (alasan penonaktifan)\n"
                    "   }\n"
                    "6. 'LIST_SUPPLIERS': Melihat, menanyakan, atau mengecek daftar supplier/rekanan/vendor pangan "
                    "(contoh: 'suplier kita saat ini ada apa aja', 'siapa aja rekanan kita', 'ada berapa suplier di data kita', 'spill vendor ayam').\n"
                    "   Ekstrak parameter: {\"commodity\": string atau null}\n"
                    "7. 'GET_INVENTORY': Mengecek stok gudang, sisa bahan, atau kapasitas freezer "
                    "(contoh: 'stok beras sisa berapa?', 'cek stok gudang dan sisa freezer').\n"
                    "   Ekstrak parameter: {\"item_name_or_id\": string atau null}\n"
                    "8. 'REPORT_INCIDENT': Melaporkan gangguan pasokan, disrupsi, kebakaran, banjir, gagal kirim, atau kekurangan porsi makanan.\n"
                    "9. 'REQUEST_REVISION': Meminta revisi rekomendasi insiden (contoh: 'bisa ganti ke supplier yang lebih murah?', 'ubah target jadi 2000 porsi').\n"
                    "10. 'APPROVE_PO': Menyetujui rekomendasi pengadaan darurat (contoh: 'setuju', 'deal', 'buatkan PO nya', 'terbitkan surat PO').\n"
                    "11. 'CONFIRM_CLARIFICATION': Mengonfirmasi pilihan rekanan dari pertanyaan klarifikasi (contoh: 'iya betul, PT Unggas Sejahtera yang kebakaran', 'ya benar').\n"
                    "12. 'GREETING': Sapaan pembuka murni (contoh: 'halo', 'hai', 'selamat pagi').\n"
                    "13. 'GENERAL_CHAT': Pertanyaan konsultatif umum tentang regulasi halal UU 33/2014, SOP SPPG, atau obrolan santai tanpa butuh data spesifik.\n\n"
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

        # 0. Konfirmasi atau Pembatalan Draf CRUD Rekanan (Human-in-the-Loop)
        if session.get("pending_crud"):
            if any(w in msg_lower for w in ["batal", "jangan", "batalkan", "tidak jadi", "cancel", "tunda", "gak jadi"]):
                return {"action": "CANCEL_CRUD", "parameters": {}}
            if any(w in msg_lower for w in ["setuju", "simpan", "ya", "iya", "oke", "ok", "daftarkan", "ubah", "update", "nonaktifkan", "proses", "deal", "lanjut", "lanjutkan", "benar", "betul", "confirm", "yes"]):
                return {"action": "CONFIRM_CRUD", "parameters": {}}

        # 1. Approval PO
        if session.get("current_recommendation") and any(w in msg_lower for w in ["setuju", "deal", "buatkan po", "terbitkan", "approve"]):
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

        # 4. Supplier Management
        if any(w in msg_lower for w in ["nonaktifkan", "non-aktifkan", "deaktivasi", "hapus supplier"]):
            return {"action": "DEACTIVATE_SUPPLIER", "parameters": {}}
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
            f"1. 🚨 **Lapor Gangguan Pasokan:** Ceritakan jika ada supplier terkendala atau musibah di lapangan.\n"
            f"2. 📦 **Cek Inventaris:** Tanyakan stok fisik bahan makanan atau sisa ruang freezer.\n"
            f"3. 🤝 **Katalog Rekanan:** Tanyakan daftar supplier terdaftar dan status sertifikasi Halal.\n\n"
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
        """Menangani permintaan daftar rekanan (LIST_SUPPLIERS)."""
        commodity_filter = params.get("commodity")
        suppliers = [s for s in SUPPLIERS_DB.values() if getattr(s, "is_active", True)]
        if commodity_filter:
            suppliers = [s for s in suppliers if commodity_filter.upper() in getattr(s, "commodity", "").upper()]

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
        """Menangani pengecekan stok inventaris dan freezer (GET_INVENTORY)."""
        items = list(INVENTORY_DB.values())
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

        # 1. DEACTIVATE PREVIEW
        if action == "DEACTIVATE_SUPPLIER":
            matched = None
            if params.get("supplier_name_or_id"):
                matched = self._match_supplier_in_text(str(params["supplier_name_or_id"]))
            if not matched:
                matched = self._match_supplier_in_text(user_msg)

            if not matched:
                fallback = (
                    "Mohon maaf Pak/Bu, saya tidak menemukan nama atau ID supplier yang Anda maksud untuk dinonaktifkan.\n\n"
                    "Mohon sebutkan nama lengkap atau ID supplier (misal: `SUP-ALT-02` atau `UD Ayam Murah Meriah`)."
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
            reason = params.get("reason") or "Penonaktifan administratif oleh pimpinan SPPG"
            session["pending_crud"] = {
                "type": "DEACTIVATE",
                "supplier_id": sid,
                "supplier_name": supplier.supplier_name,
                "reason": reason,
            }

            preview_text = (
                f"⚠️ **Konfirmasi Deaktivasi Rekanan (Preview Penonaktifan)**\n\n"
                f"Halo Bapak/Ibu Kepala SPPG, mohon konfirmasi sebelum rekanan dinonaktifkan dari sistem operasional:\n\n"
                f"• **Nama Rekanan:** **{supplier.supplier_name}** (`{sid}`)\n"
                f"• **Komoditas Pangan:** **{supplier.commodity}** [{supplier.category}]\n"
                f"• **Alasan:** {reason}\n"
                f"• **Dampak Operasional:** Status rekanan berubah menjadi **NON-AKTIF** (Soft Delete). "
                f"Rekanan tidak akan dialokasikan untuk pengadaan darurat SPPG. Histori audit transaksi masa lalu tetap tersimpan utuh.\n\n"
                f"---\n"
                f"Keputusan akhir berada di tangan Bapak/Ibu Kepala SPPG:\n"
                f"👉 Ketik **\"Setuju / Ya\"** untuk menonaktifkan rekanan ini.\n"
                f"👉 Ketik **\"Batal\"** jika ingin mempertahankan rekanan."
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=user_msg,
                context_data=f"Tahap: Preview Deaktivasi. Rekanan: {supplier.supplier_name} ({sid}). Alasan: {reason}. Menunggu keputusan Kepala SPPG.",
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
                    preview_data={"action": "PREVIEW_DEACTIVATE", "supplier_id": sid, "supplier_name": supplier.supplier_name},
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
        for it in INVENTORY_DB.values():
            if comm_lower in it.item_name.lower() or comm_lower in it.item_id.lower():
                matched_item = it
                break
        if not matched_item:
            for it in INVENTORY_DB.values():
                if create_payload.category.upper() == it.category.upper():
                    matched_item = it
                    break

        sop_max = matched_item.sop_max_price_per_kg if matched_item else 40000.0
        exceeds_sop = create_payload.unit_price_idr > sop_max
        pagu_status = "Sesuai Pagu Anggaran SOP BGN (Aman) ✅" if not exceeds_sop else f"Melebihi Pagu SOP {matched_item.item_name if matched_item else ''} (Maks: Rp {sop_max:,.2f}) ⚠️"
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
            cancel_msg = (
                f"❌ **Aksi Pengelolaan Rekanan Dibatalkan**\n\n"
                f"Instruksi draf {crud_type} telah dibatalkan sesuai arahan Bapak/Ibu Kepala SPPG. "
                f"Tidak ada data yang diubah atau disimpan ke dalam basis data resmi SPPG."
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data=f"Kepala SPPG membatalkan aksi {crud_type}. Tidak ada mutasi basis data.",
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

        elif crud_type == "DEACTIVATE":
            sid = pending["supplier_id"]
            reason = pending.get("reason", "Deaktivasi disetujui Kepala SPPG")
            res = deactivate_supplier_tool(supplier_id=sid, reason=reason)
            session["pending_crud"] = None

            fallback = (
                f"✅ **Otorisasi Diterima: Rekanan Berhasil Dinonaktifkan (Soft Delete)**\n\n"
                f"• Rekanan: **{pending.get('supplier_name', sid)}** (`{sid}`)\n"
                f"• Status Operasional: **NON-AKTIF**\n"
                f"• Alasan: {reason}\n\n"
                f"🛡️ *Histori transaksi dan audit trail masa lalu tetap tersimpan utuh di basis data.*"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["SUPPLIER_MANAGEMENT"],
                user_message=request.message,
                context_data=f"Aksi: Deaktivasi Disetujui Kepala SPPG. Hasil: {res}",
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
                    preview_data={"action": "DEACTIVATE", "result": res},
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

            fallback = (
                f"Laporan disrupsi untuk supplier **{matched_sup['supplier_name']}** berhasil diverifikasi.\n\n"
                f"📊 **Hasil Kalkulasi Kebutuhan ({target_portions:,} Porsi):**\n"
                f"• Defisit Bahan: **{metrics.deficit_kg} kg** (Stok aktual gudang: {metrics.current_stock_kg} kg)\n"
                f"• Kapasitas Freezer: **{metrics.freezer_available_kg} kg** (Kendala terdeteksi ⚠️)\n\n"
                f"🛡️ **Rekomendasi Mitigasi SPPG:**\n"
                f"• Supplier Pengganti: **{rec.supplier_name}** (Halal Aktif ✅)\n"
                f"• Total Biaya: Rp {rec.total_estimated_cost_idr:,.2f} (@ Rp {rec.unit_price_idr:,.2f}/kg)\n"
                f"• Skor Kelayakan: **{rec.feasibility_score}/100** [{rec.feasibility_status.value}]\n"
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
                    f"Skor: {rec.feasibility_score}, Strategi: {rec.logistics_strategy.strategy_type.value}"
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

        matched_sup = next(
            (s for s in SUPPLIERS_DB.values() if chosen_supplier_name and s.supplier_name.lower() == chosen_supplier_name.lower()),
            None,
        )
        if not matched_sup and chosen_supplier_name:
            matched_sup = next(
                (s for s in SUPPLIERS_DB.values() if chosen_supplier_name.lower() in s.supplier_name.lower()),
                None,
            )

        if not matched_sup:
            # Fallback ambil supplier pertama dari saran
            if suggested:
                matched_sup = next((s for s in SUPPLIERS_DB.values() if s.supplier_name == suggested[0]), None)

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
                f"• Skor Kelayakan: **{rec.feasibility_score}/100** [{rec.feasibility_status.value}]\n"
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
                    f"Skor: {rec.feasibility_score}, Strategi: {rec.logistics_strategy.strategy_type.value}"
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
                    },
                ),
            )

        return self._handle_consultative_chat(session, request)

    def _handle_revision(self, session: Dict[str, Any], request: ChatRequest, params: Dict[str, Any]) -> ChatResponse:
        """Menangani permintaan revisi atau opsi alternatif (REQUEST_REVISION)."""
        user_msg = request.message.strip()
        msg_lower = user_msg.lower()

        if "porsi" in msg_lower:
            new_portions = self._extract_portions(user_msg, default=session["incident_context"]["target_portions"])
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

        fallback = (
            f"🔄 Penyesuaian berhasil diperbarui sesuai arahan Anda:\n\n"
            f"• Target Porsi: {target_portions:,} porsi\n"
            f"• Defisit Dihitung: {metrics.deficit_kg} kg (Sisa freezer: {metrics.freezer_available_kg} kg)\n"
            f"• Rekanan Alternatif Baru: {new_rec.supplier_name}\n"
            f"• Harga Penawaran: Rp {new_rec.unit_price_idr:,.2f}/kg (Total: Rp {new_rec.total_estimated_cost_idr:,.2f})\n"
            f"• Skor Kelayakan: {new_rec.feasibility_score}/100 [{new_rec.feasibility_status.value}]\n"
            f"• Taktik: {new_rec.logistics_strategy.strategy_type.value}\n\n"
            f"Silakan ketik 'Setuju' untuk menerbitkan Purchase Order resmi, atau beri tahu jika ada penyesuaian lain."
        )
        adaptive_reply = self._call_gemini_adaptive(
            system_instructions=SYSTEM_PROMPTS["REVISION_REQUEST"],
            user_message=user_msg,
            context_data=(
                f"Target Porsi: {target_portions}, Defisit: {metrics.deficit_kg} kg, Rekanan Baru: {new_rec.supplier_name}, "
                f"Harga: Rp {new_rec.unit_price_idr}/kg (Total: Rp {new_rec.total_estimated_cost_idr}), Skor: {new_rec.feasibility_score}, "
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
                    reply="Purchase Order untuk insiden ini sudah berhasil diterbitkan sebelumnya.",
                    intent=ChatIntent.CONFIRM_APPROVAL,
                    action_required=ChatActionRequired.COMPLETED,
                    preview_data={"po_result": session["po_result"].model_dump() if session.get("po_result") else None},
                ),
            )

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
        else:
            return self._handle_consultative_chat(session, request)


# Singleton instance conversational agent
conversational_agent = ConversationalAgentManager()
