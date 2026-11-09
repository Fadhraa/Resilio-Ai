import { NextRequest, NextResponse } from "next/server";
import { ChatRequest, ChatResponse } from "@/types/incident";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_API_URL ||
  "http://127.0.0.1:8000/api/v1";

/**
 * Next.js API Gateway Proxy ke Python Backend ResilioAI.
 * 
 * Standar Arsitektur Industri 2026:
 * - Frontend Next.js bertindak murni sebagai API Gateway/Proxy ke backend Python.
 * - Tidak ada regex hardcoded atau string-matching 'if (msg.includes(...))' yang mensimulasikan AI palsu.
 * - Seluruh penalaran kognitif (intent detection, ekstraksi parameter, verifikasi kepatuhan SPPG)
 *   dieksekusi secara murni oleh LLM Gemini 3.5 Flash-Lite / 2.5 Flash di backend Python,
 *   dan seluruh mutasi data dilakukan secara ACID pada basis data SQLite resmi.
 */
export async function POST(req: NextRequest) {
  try {
    const payload: ChatRequest = await req.json();

    // 1. Forward request ke backend Python resmi (FastAPI di port 8000)
    try {
      const controller = new AbortController();
      // Berikan timeout 20 detik agar LLM Gemini memiliki waktu berpikir dan mensintesis respon semantik
      const timeoutId = setTimeout(() => controller.abort(), 20000);

      const backendRes = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (backendRes.ok) {
        const data: ChatResponse = await backendRes.json();
        return NextResponse.json(data);
      }
    } catch {
      // Backend offline atau koneksi timeout
    }

    // 2. Jika backend Python di port 8000 offline, berikan notifikasi jujur dan transparan
    // daripada melakukan simulasi regex palsu yang tidak menyentuh database SQLite.
    const offlineNotice: ChatResponse = {
      session_id: payload.session_id,
      reply: `⚠️ **Server Backend ResilioAI (Port 8000) Belum Aktif**\n\nSeluruh keputusan dan penalaran bahasa alami (termasuk deteksi niat penghapusan rekanan, analisis inventaris, dan kepatuhan regulasi gizi SPPG) diproses murni oleh model LLM Gemini dan basis data SQLite di backend Python.\n\nSilakan jalankan backend di terminal:\n\`\`\`powershell\n.venv\\Scripts\\python.exe -m uvicorn main:app --port 8000 --reload\n\`\`\`\nSetelah server aktif, silakan kirimkan kembali instruksi Anda.`,
      intent: "GENERAL_INQUIRY",
      action_required: "NONE",
    };

    return NextResponse.json(offlineNotice);
  } catch (error) {
    return NextResponse.json(
      { error: "Gagal memproses permintaan chat" },
      { status: 500 }
    );
  }
}
