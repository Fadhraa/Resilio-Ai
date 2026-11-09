import { NextResponse } from "next/server";
import { mockCircularLetters } from "@/data/mockData";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_API_URL ||
  "http://127.0.0.1:8000/api/v1";

export async function GET() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const backendRes = await fetch(`${BACKEND_URL}/circular-letters`, {
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

  return NextResponse.json(mockCircularLetters);
}

