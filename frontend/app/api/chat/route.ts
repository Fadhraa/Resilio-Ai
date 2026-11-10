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

    // 1. Coba forward ke backend Python resmi (FastAPI di port 8000)
    // Mendukung fallback baik ke 127.0.0.1 maupun localhost (antisipasi perbedaan IPv4 / IPv6 di Windows)
    const candidates = [
      BACKEND_URL,
      "http://127.0.0.1:8000/api/v1",
      "http://localhost:8000/api/v1",
    ];
    const uniqueTargets = Array.from(new Set(candidates));

    for (const target of uniqueTargets) {
      try {
        const controller = new AbortController();
        // Berikan batas waktu 35 detik agar pemrosesan semantik kognitif Gemini memiliki waktu yang cukup
        const timeoutId = setTimeout(() => controller.abort(), 35000);

        const backendRes = await fetch(`${target}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (backendRes.ok) {
          const data: ChatResponse = await backendRes.json();
          return NextResponse.json(data);
        } else {
          console.error(
            `[Resilio Chat Proxy] Backend pada ${target} merespons status ${backendRes.status}`,
          );
          try {
            const errData = await backendRes.json();
            if (errData && errData.detail) {
              const noticeResponse: ChatResponse = {
                session_id: payload.session_id,
                reply: `⚠️ **Pemberitahuan Sistem Backend:** ${errData.detail}`,
                intent: "GENERAL_INQUIRY",
                action_required: "NONE",
              };
              return NextResponse.json(noticeResponse);
            }
          } catch {
            // Biarkan lanjut ke candidate berikutnya atau notice
          }
        }
      } catch (err: any) {
        console.warn(
          `[Resilio Chat Proxy] Gagal terhubung ke ${target}: ${err?.message || err}`,
        );
      }
    }

    // 2. Jika seluruh target backend Python di port 8000 offline / unreachable
    const offlineNotice: ChatResponse = {
      session_id: payload.session_id,
      reply: `⚠️ **Server Backend ResilioAI (Port 8000) Belum Aktif atau Sedang Mengalami Kendala Koneksi**\n\nSeluruh keputusan dan penalaran bahasa alami (termasuk deteksi niat penghapusan rekanan, analisis inventaris, dan kepatuhan regulasi gizi SPPG) diproses murni oleh model LLM Gemini dan basis data SQLite di backend Python.\n\nSilakan periksa terminal backend Anda dan pastikan server berjalan:\n\`\`\`powershell\n.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000 --reload\n\`\`\`\nSetelah server aktif, silakan kirimkan kembali instruksi Anda.`,
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
