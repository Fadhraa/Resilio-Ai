"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, ArrowRight, Lock, Mail, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("budi.santoso@sppg.go.id");
  const [password, setPassword] = useState("password123");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Simulasi autentikasi sederhana
    setTimeout(() => {
      if (!email || !password) {
        setError("Email dan kata sandi wajib diisi");
        setIsLoading(false);
        return;
      }
      setIsLoading(false);
      router.push("/dashboard");
    }, 600);
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo & Judul */}
        <div className="flex justify-center">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-white font-bold text-sm shadow-xs">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="text-left">
              <div className="font-bold text-lg text-zinc-900 tracking-tight">
                ResilioAI
              </div>
              <p className="text-[11px] text-zinc-500 font-medium">
                Dapur Gizi SPPG
              </p>
            </div>
          </Link>
        </div>

        <h2 className="mt-6 text-center text-xl font-bold tracking-tight text-zinc-900">
          Masuk ke Akun Petugas SPPG
        </h2>
        <p className="mt-1 text-center text-xs text-zinc-500">
          Masukkan email atau NIP terdaftar untuk mengelola pasokan makanan
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-zinc-200 rounded-2xl sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-zinc-100 border border-zinc-300 text-xs text-zinc-800 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold text-zinc-700 mb-1"
              >
                Email Petugas / NIP
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="budi.santoso@sppg.go.id"
                  className="block w-full pl-9 pr-3 py-2 text-xs border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900 focus:border-zinc-900 text-zinc-900"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold text-zinc-700"
                >
                  Kata Sandi
                </label>
                <a
                  href="#"
                  className="text-[11px] text-zinc-500 hover:text-zinc-900"
                >
                  Lupa sandi?
                </a>
              </div>
              <div className="relative rounded-lg shadow-2xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-xs border border-zinc-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-900 focus:border-zinc-900 text-zinc-900"
                />
              </div>
            </div>

            <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200 text-[11px] text-zinc-500">
              <span className="font-semibold text-zinc-700">Akun Pengujian Demo:</span>{" "}
              budi.santoso@sppg.go.id (Kepala SPPG)
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg text-xs font-semibold text-white bg-zinc-900 hover:bg-zinc-800 transition active:scale-[0.98] shadow-xs"
            >
              <span>{isLoading ? "Memeriksa..." : "Masuk ke Sistem"}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-zinc-500">
            Belum punya akun petugas?{" "}
            <Link
              href="/register"
              className="font-semibold text-zinc-900 hover:underline"
            >
              Daftar Petugas Baru
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-xs text-zinc-500 hover:text-zinc-900 font-medium"
          >
            ← Kembali ke Halaman Depan
          </Link>
        </div>
      </div>
    </div>
  );
}

