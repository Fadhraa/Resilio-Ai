import { NextRequest, NextResponse } from "next/server";
import { ChatRequest, ChatResponse } from "@/types/incident";

export async function POST(req: NextRequest) {
  try {
    const body: ChatRequest = await req.json();
    const query = (body.message || "").toLowerCase();

    let reply = "";
    let intent: ChatResponse["intent"] = "GENERAL_INQUIRY";
    let action_required: ChatResponse["action_required"] = "NONE";

    if (query.includes("stok") || query.includes("gudang")) {
      reply =
        "Halo! Berdasarkan data gudang SPPG hari ini: Stok Daging Ayam ada 80 kg (kurang 64 kg dari target 144 kg), Beras 500 kg (Aman), Telur 120 kg (Aman), dan Daging Sapi 50 kg (Aman).";
      intent = "GENERAL_INQUIRY";
    } else if (query.includes("split") || query.includes("kulkas") || query.includes("freezer")) {
      reply =
        "Pengiriman dibagi 2 tahap (Split Delivery) karena kapasitas freezer dapur yang tersisa hanya 20 kg. Batch 1 (20 kg) tiba H-1 sore jam 17:00, sedangkan Batch 2 (44 kg) tiba Hari-H jam 05:00 pagi dan langsung masuk proses masak subuh.";
      intent = "REQUEST_REVISION";
    } else if (query.includes("pemasok") || query.includes("supplier") || query.includes("halal")) {
      reply =
        "Pemasok pengganti yang direkomendasikan adalah PT Berkah Unggas Jaya (ID: SUP-ALT-02) dengan sertifikat Halal BPJPH aktif (No: ID32110000897650324) dan harga Rp 36.500/kg (di bawah pagu SOP Rp 42.000).";
      intent = "MANAGE_SUPPLIER";
    } else if (query.includes("setuju") || query.includes("po") || query.includes("pesan")) {
      reply =
        "Rekomendasi siap disetujui! Anda dapat mengesahkan pengadaan darurat ini melalui tombol [Buka Persetujuan] atau konfirmasi langsung dengan kuota 64 kg.";
      intent = "CONFIRM_APPROVAL";
      action_required = "APPROVAL_PENDING";
    } else if (query.includes("banjir") || query.includes("insiden") || query.includes("masalah")) {
      reply =
        "Laporan insiden: Truk PT Unggas Sejahtera Nusantara terhambat banjir Pantura estimasi 3 hari. Sistem merekomendasikan pengalihan ke PT Berkah Unggas Jaya.";
      intent = "REPORT_INCIDENT";
    } else {
      reply =
        "Halo! Saya Asisten AI ResilioAI SPPG. Anda dapat menanyakan tentang status stok gudang, verifikasi sertifikat halal pemasok, alasan jadwal kirim 2 kali, atau meminta pembuatan surat pesanan (PO).";
      intent = "GENERAL_INQUIRY";
    }

    const response: ChatResponse = {
      session_id: body.session_id || "SESSION-DEMO",
      reply,
      intent,
      action_required,
    };

    return NextResponse.json(response);
  } catch {
    return NextResponse.json(
      { error: "Format pesan obrolan tidak valid" },
      { status: 400 }
    );
  }
}

