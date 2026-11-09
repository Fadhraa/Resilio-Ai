"""
General & Consultative Chat Handler for ResilioAI Cognitive Agent.
Menangani:
1. Sapaan pembuka (GREETING).
2. Konsultasi bebas & FAQ SOP SPPG (CONSULTATIVE_CHAT).
3. Domain guardrail penolakan pembuatan kode / di luar mandat SPPG (OUT_OF_DOMAIN).
4. Penjelasan kapabilitas CRUD dan operasional SPPG (EXPLAIN_CAPABILITIES).
"""

from typing import Any, Callable, Dict
from app.engine.agent.prompts import SYSTEM_PROMPTS
from app.models.schemas import ChatActionRequired, ChatIntent, ChatRequest, ChatResponse


def handle_greeting(
    session: Dict[str, Any],
    request: ChatRequest,
    call_gemini_adaptive: Callable[..., str],
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
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
    adaptive_reply = call_gemini_adaptive(
        system_instructions=SYSTEM_PROMPTS["GREETING"],
        user_message=request.message,
        context_data=f"Pengguna: {request.user_role}. Sesi baru dimulai.",
        fallback_text=fallback,
    )
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=adaptive_reply,
            intent=ChatIntent.GENERAL_INQUIRY,
            action_required=ChatActionRequired.NONE,
        ),
    )


def handle_consultative_chat(
    session: Dict[str, Any],
    request: ChatRequest,
    call_gemini_adaptive: Callable[..., str],
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
    """Menangani konsultasi bebas dan FAQ umum SPPG (GENERAL_CHAT)."""
    fallback = (
        f"Halo Bapak/Ibu {request.user_role}, saya ResilioAI siap mendampingi operasional pemenuhan gizi SPPG.\n\n"
        f"Sistem kami dirancang untuk memitigasi risiko pasokan pangan, memantau batas aman penyimpanan freezer, "
        f"dan memastikan seluruh bahan pangan memenuhi sertifikasi Halal 100%.\n\n"
        f"Apakah ada kendala operasional, pengecekan inventaris gudang, atau data rekanan yang ingin didiskusikan?"
    )
    adaptive_reply = call_gemini_adaptive(
        system_instructions=SYSTEM_PROMPTS["CONSULTATIVE_CHAT"],
        user_message=request.message,
        context_data=f"User Role: {request.user_role}. Sesi percakapan aktif.",
        fallback_text=fallback,
        history=session.get("history", []),
    )
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=adaptive_reply,
            intent=ChatIntent.GENERAL_INQUIRY,
            action_required=ChatActionRequired.NONE,
        ),
    )


def handle_out_of_domain(
    session: Dict[str, Any],
    request: ChatRequest,
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
    """Menolak permintaan pembuatan kode pemrograman atau tugas di luar mandat SPPG (Domain Guardrail)."""
    reply = (
        "Mohon maaf, Bapak Adam. Sebagai Asisten Operasional SPPG (Satuan Pelayanan Pemenuhan Gizi - Badan Gizi Nasional), "
        "tugas dan wewenang saya dibatasi secara ketat hanya pada manajemen rantai pasok bahan pangan, pemantauan stok gudang, "
        "verifikasi kepatuhan sertifikasi Halal (UU JPH No. 33/2014), dan mitigasi risiko logistik SPPG.\n\n"
        "Saya tidak memiliki otorisasi untuk membuat kode pemrograman atau menangani tugas teknis di luar mandat gizi pangan nasional.\n\n"
        "Silakan instruksikan apabila ada kebutuhan terkait pengecekan stok dapur, audit rekanan pangan, atau pelaporan kendala pengiriman."
    )
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=reply,
            intent=ChatIntent.GENERAL_INQUIRY,
            action_required=ChatActionRequired.NONE,
        ),
    )


def handle_explain_capabilities(
    session: Dict[str, Any],
    request: ChatRequest,
    respond: Callable[..., ChatResponse],
) -> ChatResponse:
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
    return respond(
        session,
        ChatResponse(
            session_id=request.session_id,
            reply=reply,
            intent=ChatIntent.GENERAL_INQUIRY,
            action_required=ChatActionRequired.NONE,
        ),
    )

