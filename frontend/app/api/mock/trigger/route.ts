import { NextRequest, NextResponse } from "next/server";
import { IncidentTriggerRequest, IncidentTriggerResponse } from "@/types/incident";

export async function POST(req: NextRequest) {
  try {
    const body: IncidentTriggerRequest = await req.json();

    const response: IncidentTriggerResponse = {
      incident_id: body.item_id ? `INC-${Date.now().toString().slice(-4)}` : "INC-2026-001",
      status: "PROCESSING",
      stream_url: "/api/mock/stream",
    };

    return NextResponse.json(response);
  } catch {
    return NextResponse.json(
      { error: "Invalid trigger payload format" },
      { status: 400 }
    );
  }
}
