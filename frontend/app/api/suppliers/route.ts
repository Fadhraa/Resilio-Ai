import { NextResponse } from "next/server";
import { mockSuppliers } from "@/data/mockData";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_API_URL ||
  "http://127.0.0.1:8000/api/v1";

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    if (!url.searchParams.has("include_inactive")) {
      url.searchParams.set("include_inactive", "true");
    }
    const search = url.search;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const backendRes = await fetch(`${BACKEND_URL}/suppliers${search}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (backendRes.ok) {
      const data = await backendRes.json();
      return NextResponse.json(data);
    }
  } catch {
    // Backend offline / unreachable, fallback ke mock data resmi
  }

  return NextResponse.json(mockSuppliers);
}

