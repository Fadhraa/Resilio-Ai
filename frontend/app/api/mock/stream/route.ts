export const dynamic = "force-dynamic";

/**
 * Mock Server-Sent Events (SSE) Route
 * Menyederhanakan pengetesan Real-Time Agent Pipeline Visualizer di sisi frontend
 * tanpa perlu menunggu backend Python LangGraph siap sepenuhnya.
 */
export async function GET() {
  const encoder = new TextEncoder();

  // Daftar sekuensial event yang dikirimkan oleh LangGraph pipeline
  const streamSteps = [
    {
      event: "node_started",
      data: {
        node: "deterministic_data_layer",
        message: "Mengambil data inventaris gudang dan kueri kapasitas chiller...",
        timestamp: new Date().toISOString(),
      },
      delay: 500,
    },
    {
      event: "node_completed",
      data: {
        node: "deterministic_data_layer",
        deficit_kg: 64.0,
        current_stock_kg: 80.0,
        freezer_remaining_kg: 20.0,
        message: "Defisit 64 kg terhitung secara deterministik (Stok 80 kg vs Kebutuhan 144 kg)",
      },
      delay: 800,
    },
    {
      event: "node_started",
      data: {
        node: "compliance_filter",
        message: "Memfilter supplier non-halal dan memeriksa batas radius logistik...",
        timestamp: new Date().toISOString(),
      },
      delay: 700,
    },
    {
      event: "node_completed",
      data: {
        node: "compliance_filter",
        message: "Lolos filter mutlak: 3 supplier berstatus halal aktif dalam radius aman.",
      },
      delay: 700,
    },
    {
      event: "node_started",
      data: {
        node: "strategic_procurement_agent",
        model: "gemini-2.5-flash",
        message: "Agen Kognitif (LLM) menimbang kendala freezer & merancang skema Split-Delivery...",
        timestamp: new Date().toISOString(),
      },
      delay: 1000,
    },
    {
      event: "node_completed",
      data: {
        node: "strategic_procurement_agent",
        message: "Strategi alokasi pengadaan selesai: Rekomendasi PT Berkah Unggas Jaya.",
      },
      delay: 900,
    },
    {
      event: "node_started",
      data: {
        node: "feasibility_scoring_engine",
        message: "Menghitung formula skor kelayakan 7 parameter berbobot...",
        timestamp: new Date().toISOString(),
      },
      delay: 600,
    },
    {
      event: "node_completed",
      data: {
        node: "feasibility_scoring_engine",
        score: 78.5,
        status: "FEASIBLE_WITH_CONDITIONS",
        message: "Skor Kelayakan 78.5/100 (FEASIBLE WITH CONDITIONS - Wajib Split Delivery)",
      },
      delay: 600,
    },
    {
      event: "workflow_waiting_approval",
      data: {
        incident_id: "INC-2026-001",
        decision_ready: true,
        message: "Eksekusi ditahan di Checkpoint LangGraph (Interrupt). Menunggu otorisasi Kepala SPPG.",
      },
      delay: 500,
    },
  ];

  const stream = new ReadableStream({
    async start(controller) {
      for (const step of streamSteps) {
        await new Promise((resolve) => setTimeout(resolve, step.delay));

        const payload = `event: ${step.event}\ndata: ${JSON.stringify(step.data)}\n\n`;
        controller.enqueue(encoder.encode(payload));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
