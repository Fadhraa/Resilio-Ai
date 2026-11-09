import { NextRequest, NextResponse } from "next/server";
import { mockPoSuccess } from "@/data/mockData";
import { ApprovalRequest } from "@/types/incident";

export async function POST(req: NextRequest) {
  try {
    const body: ApprovalRequest = await req.json();

    if (body.action === "REJECT") {
      return NextResponse.json({
        status: "REJECTED",
        message: "Pengadaan alternatif ditolak oleh Kepala SPPG.",
        incident_id: body.incident_id,
      });
    }

    return NextResponse.json({
      ...mockPoSuccess,
      incident_id: body.incident_id,
      approver_name: body.approver_name,
      approved_qty_kg: body.approved_qty_kg,
    });
  } catch {
    return NextResponse.json(
      { error: "Invalid approval payload format" },
      { status: 400 }
    );
  }
}

