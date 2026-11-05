import { NextResponse } from "next/server";
import { mockIncidentDecision } from "@/data/mockData";

export async function GET() {
  return NextResponse.json(mockIncidentDecision);
}

