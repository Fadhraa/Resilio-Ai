import { NextRequest, NextResponse } from "next/server";
import { mockSuppliersList } from "@/data/mockData";
import { SupplierCreateRequest, SupplierRecord } from "@/types/incident";

let localSuppliers = [...mockSuppliersList];

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const commodity = searchParams.get("commodity");
  const includeInactive = searchParams.get("include_inactive") === "true";

  let results = [...localSuppliers];
  if (!includeInactive) {
    results = results.filter((s) => s.is_active);
  }
  if (commodity) {
    results = results.filter((s) => s.commodity.toLowerCase() === commodity.toLowerCase());
  }

  return NextResponse.json(results);
}

export async function POST(req: NextRequest) {
  try {
    const body: SupplierCreateRequest = await req.json();
    const newId = `SUP-REG-${(localSuppliers.length + 1).toString().padStart(2, "0")}`;

    const newSupplier: SupplierRecord = {
      supplier_id: newId,
      supplier_name: body.supplier_name,
      category: body.category || "PROTEIN",
      commodity: body.commodity || "DAGING_AYAM",
      supported_items: body.supported_items || ["ITEM-AYAM-01"],
      halal_certified: body.halal_certified,
      halal_cert_number: body.halal_cert_number || null,
      unit_price_idr: body.unit_price_idr,
      daily_capacity_kg: body.daily_capacity_kg,
      lead_time_hours: body.lead_time_hours || 3.0,
      distance_km: body.distance_km || 15.0,
      reliability_rating: body.reliability_rating || 85.0,
      is_active: true,
    };

    localSuppliers = [newSupplier, ...localSuppliers];

    return NextResponse.json(
      {
        status: "SUCCESS",
        message: `Pemasok ${newSupplier.supplier_name} berhasil didaftarkan.`,
        supplier: newSupplier,
      },
      { status: 201 }
    );
  } catch {
    return NextResponse.json(
      { error: "Format pendaftaran pemasok tidak valid" },
      { status: 400 }
    );
  }
}

