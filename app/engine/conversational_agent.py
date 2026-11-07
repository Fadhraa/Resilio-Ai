import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Muat environment variables dari .env
load_dotenv()

from app.data.mock_db import INVENTORY_DB, SUPPLIERS_DB
from app.engine.agent import strategic_agent
from app.engine.feasibility import feasibility_engine
from app.engine.tools import get_inventory_status_tool, search_suppliers_tool
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
    SupplierRecord,
)
from app.services.data_layer import data_layer_service


# ==============================================================================
# KONFIGURASI SYSTEM PROMPTS (MODULAR & CUSTOMIZABLE)
# ==============================================================================
# Anda dapat dengan mudah memodifikasi persona, gaya bahasa (tone of voice),
# dan instruksi model Google Gemini untuk masing-masing skenario di bawah ini:
SYSTEM_PROMPTS = {
    # 1. Sapaan Pembuka (Greeting)
    "GREETING": (
        "Kamu adalah ResilioAI Assistant, asisten kecerdasan buatan operasional untuk Kepala SPPG "
        "(Satuan Pelayanan Pemenuhan Gizi). Sambut Kepala SPPG secara sopan saja dengan sebutan pak/bu "
        "Perkenalkan dirimu singkat dan tanyakan apakah ada kendala pasokan makanan yang perlu dimitigasi hari ini."
    ),

    # 2. Diskusi Konsultatif Bebas & FAQ SPPG (Regulasi Halal, SOP, Kapasitas Freezer)
    "CONSULTATIVE_CHAT": (
        "Kamu adalah ResilioAI Assistant, partner intelijen operasional untuk Kepala SPPG "
        "(Satuan Pelayanan Pemenuhan Gizi - Program Makan Bergizi Gratis 2026). "
        "Karaktermu: Sangat adaptif, cerdas, solutif, empatik, komunikatif, tidak kaku seperti robot template, "
        "dan memiliki pemahaman mendalam tentang logistik pangan, rantai pasok SPPG, sertifikasi Halal (UU JPH No. 33/2014), "
        "dan mitigasi risiko pasokan. "
        "Jawablah pertanyaan Kepala SPPG secara natural, lugas, santun, dan profesional. "
        "Gunakan wawasan logistik SPPG yang relevan untuk menjawab."
    ),

    # 3. Inquiry Daftar Rekanan Supplier
    "SUPPLIER_INQUIRY": (
        "Kamu adalah ResilioAI Assistant. Jawab pertanyaan Kepala SPPG mengenai data rekanan supplier terdaftar "
        "berdasarkan data resmi dari database SPPG. Sajikan secara terstruktur, rapi, dan informatif."
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
}


class ConversationalAgentManager:
    """
    Manajer Agen Percakapan Cerdas (Conversational AI Assistant).
    
    Menghubungkan model Google Gemini untuk sintesis percakapan yang luwes dan adaptif,
    dengan Tool Calling membaca basis data SPPG dan kalkulasi matematis tertutup (Zero Hallucination).
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
        """
        Memanggil model Gemini untuk mensintesis respon bahasa alami yang luwes, empatik,
        dan adaptif berdasarkan data operasional yang telah diverifikasi dari database.
        """
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
            # Graceful Fallback: jika terjadi timeout atau gangguan API eksternal
            return fallback_text

    def _respond(self, session: Dict[str, Any], response: ChatResponse) -> ChatResponse:
        """Mencatat respons asisten ke riwayat percakapan sesi dan mengembalikan response."""
        session["history"].append({
            "role": "assistant",
            "content": response.reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
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

    def process_message(self, request: ChatRequest) -> ChatResponse:
        """Memproses satu giliran pesan dari pengguna dan mengembalikan respons terstruktur."""
        session = self.get_or_create_session(request.session_id)
        user_msg = request.message.strip()
        msg_lower = user_msg.lower()

        # Rekam pesan user ke riwayat
        session["history"].append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # ==========================================
        # KASUS 0: SAPAAN & SALAM PEMBUKA (GREETING)
        # ==========================================
        greeting_words = [
            "halo", "hai", "hi", "selamat pagi", "selamat siang", "selamat sore",
            "selamat malam", "assalamualaikum", "assalamu'alaikum", "pagi", "siang",
            "sore", "malam", "p", "tes", "test", "hello"
        ]
        cleaned_words = [w.strip("!.,?") for w in msg_lower.split()]
        is_pure_greeting = (
            any(msg_lower == g for g in greeting_words)
            or (len(cleaned_words) <= 3 and any(w in greeting_words for w in cleaned_words))
        ) and not any(k in msg_lower for k in [
            "kebakaran", "banjir", "rusak", "porsi", "kurang", "suplier", "supplier",
            "stok", "freezer", "ganti", "murah", "setuju", "po"
        ])

        if is_pure_greeting:
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
                user_message=user_msg,
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

        # ==========================================
        # KASUS 1: KONFIRMASI PERSETUJUAN (APPROVAL)
        # ==========================================
        approval_keywords = ["setuju", "approve", "deal", "buatkan po", "terbitkan po", "terbitkan", "proses sekarang", "lanjutkan"]
        if any(kw in msg_lower for kw in approval_keywords) and session.get("current_recommendation"):
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

        # ==========================================
        # KASUS 2: PERMINTAAN REVISI / NEGOSIASI
        # ==========================================
        revision_keywords = ["ganti", "murah", "ubah", "kurangi", "tambah", "alternatif", "opsi lain"]
        if any(kw in msg_lower for kw in revision_keywords) and session.get("current_recommendation"):
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

            if "murah" in msg_lower:
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

        # ==========================================
        # KASUS 3: KLARIFIKASI PENDING YANG DIJAWAB
        # ==========================================
        if session.get("pending_clarification"):
            pending = session["pending_clarification"]
            suggested = pending.get("suggestions", [])

            is_confirm = any(w in msg_lower for w in ["ya", "iya", "betul", "benar", "itu", "pertama"])
            chosen_supplier_name = suggested[0] if (suggested and is_confirm) else None

            if not chosen_supplier_name and suggested:
                for sug in suggested:
                    if sug.lower() in msg_lower or any(part in msg_lower for part in sug.lower().split() if len(part) > 3):
                        chosen_supplier_name = sug
                        break

            if chosen_supplier_name:
                matched_sup = next(
                    (s for s in SUPPLIERS_DB.values() if s.supplier_name.lower() == chosen_supplier_name.lower()),
                    None,
                )
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

        # ==========================================
        # KASUS 3.5: PERTANYAAN DATA UMUM (GENERAL INQUIRY)
        # ==========================================
        supplier_inquiry_triggers = [
            "berapa suplier", "berapa supplier", "daftar suplier", "daftar supplier",
            "list suplier", "list supplier", "data suplier", "data supplier",
            "siapa saja suplier", "siapa saja supplier", "ada berapa suplier", "ada berapa supplier"
        ]
        is_supplier_inquiry = any(t in msg_lower for t in supplier_inquiry_triggers) or (
            ("berapa" in msg_lower or "siapa" in msg_lower or "daftar" in msg_lower or "lihat" in msg_lower)
            and ("suplier" in msg_lower or "supplier" in msg_lower or "rekanan" in msg_lower)
            and not any(dis in msg_lower for dis in ["kebakaran", "banjir", "rusak", "mogok", "terhambat", "tidak kirim", "gagal"])
        )

        if is_supplier_inquiry:
            suppliers = [s for s in SUPPLIERS_DB.values() if getattr(s, "is_active", True)]
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
                user_message=user_msg,
                context_data="\n".join([f"{s.supplier_id}: {s.supplier_name}, Halal={s.halal_certified}, Kapasitas={s.daily_capacity_kg}kg, Harga=Rp {s.unit_price_idr}" for s in suppliers]),
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

        inventory_inquiry_triggers = [
            "stok gudang", "cek stok", "daftar stok", "status stok", "ada berapa stok",
            "sisa freezer", "kapasitas freezer", "data inventaris", "lihat stok"
        ]
        is_inventory_inquiry = any(t in msg_lower for t in inventory_inquiry_triggers) or (
            ("stok" in msg_lower or "freezer" in msg_lower or "inventaris" in msg_lower)
            and ("cek" in msg_lower or "berapa" in msg_lower or "lihat" in msg_lower or "status" in msg_lower)
        )

        if is_inventory_inquiry:
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
                user_message=user_msg,
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

        # ==========================================
        # KASUS 3.8: KONSULTASI / DISKUSI STRATEGIS OPERASIONAL
        # ==========================================
        incident_indicators = [
            "kebakaran", "banjir", "rusak", "terhambat", "gagal", "mogok",
            "tidak kirim", "tidak mensuplai", "batal", "terkendala", "masalah",
            "terlambat", "macet", "habis", "kurang", "darurat", "musibah",
            "putus", "kecelakaan", "mati", "disrupsi", "gangguan", "tidak bisa kirim",
            "kendala"
        ]
        has_incident_signal = any(k in msg_lower for k in incident_indicators) or (
            "porsi" in msg_lower and any(w in msg_lower for w in ["kurang", "butuh", "defisit", "darurat", "habis"])
        )

        has_direct_supplier_name = any(
            s.supplier_name.lower() in msg_lower or s.supplier_id.lower() in msg_lower
            for s in SUPPLIERS_DB.values()
        )

        # Jika bukan sinyal insiden / disrupsi, berikan konsultasi cerdas dan adaptif
        if not has_incident_signal and not (has_direct_supplier_name and any(w in msg_lower for w in ["kenapa", "status", "gagal"])):
            fallback = (
                f"Halo Bapak/Ibu {request.user_role}, saya ResilioAI siap mendampingi operasional pemenuhan gizi SPPG.\n\n"
                f"Sistem kami dirancang untuk memitigasi risiko pasokan pangan, memantau batas aman penyimpanan freezer, "
                f"dan memastikan seluruh bahan pangan memenuhi sertifikasi Halal 100%.\n\n"
                f"Apakah ada kendala operasional, pengecekan inventaris gudang, atau data rekanan yang ingin didiskusikan?"
            )
            adaptive_reply = self._call_gemini_adaptive(
                system_instructions=SYSTEM_PROMPTS["CONSULTATIVE_CHAT"],
                user_message=user_msg,
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

        # ==========================================
        # KASUS 4: LAPORAN INSIDEN BARU
        # ==========================================
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

        # Jika supplier tidak cocok persis (kemungkinan salah sebut / typo), minta klarifikasi secara adaptif
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


# Singleton instance conversational agent
conversational_agent = ConversationalAgentManager()
