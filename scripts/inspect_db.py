"""
Skrip Inspeksi Basis Data SQLite SPPG (Verifikasi Zero-Hallucination)

Digunakan untuk memeriksa dan memverifikasi data fisik aktual yang tersimpan di dalam
basis data SQLite (app/data/resilio.db), membuktikan bahwa asisten AI membaca data riil
dan bukan hasil halusinasi LLM.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "resilio.db"


def inspect_database(target_table: str = "all") -> None:
    """Membaca dan menampilkan isi tabel SQLite dalam format tabel rapi."""
    if not DB_PATH.exists():
        print(f"Berkas basis data tidak ditemukan di: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Dapatkan daftar seluruh tabel di SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    print("\n" + "=" * 70)
    print(f"LOKASI BASIS DATA: {DB_PATH}")
    print(f"TABEL TERDAFTAR  : {', '.join(tables)}")
    print("=" * 70)

    tables_to_show = [target_table] if target_table in tables else tables

    for table in tables_to_show:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\n[TABEL: {table.upper()}] - Total: {count} Rekord")
        print("-" * 70)

        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table} LIMIT 10")
        rows = cursor.fetchall()

        if not rows:
            print("  (Tabel kosong)")
            continue

        # Format tampilan ringkas
        if table == "suppliers":
            print(f"{'ID':<14} | {'NAMA REKANAN':<30} | {'KOMODITAS':<12} | {'HARGA (RP)':<10} | {'HALAL':<6}")
            print("-" * 70)
            for r in rows:
                sid, sname, _, comm, _, halal, _, price, _, _, _, _, _, _ = r
                halal_str = "Ya" if halal else "Tidak"
                print(f"{sid:<14} | {sname[:30]:<30} | {comm:<12} | {price:>10,.0f} | {halal_str:<6}")

        elif table == "inventory":
            print(f"{'ID ITEM':<15} | {'NAMA BAHAN':<28} | {'STOK (KG)':<10} | {'FREEZER (KG)':<12}")
            print("-" * 70)
            for r in rows:
                iid, iname, _, cstock, _, fcap, focc, _, _ = r
                f_str = f"{focc}/{fcap}"
                print(f"{iid:<15} | {iname[:28]:<28} | {cstock:>10.1f} | {f_str:>12}")

        elif table == "circular_letters":
            print(f"{'ID':<16} | {'NOMOR SURAT':<24} | {'TANGGAL':<10} | {'STATUS':<8}")
            print("-" * 70)
            for r in rows:
                lid, lnum, title, _, _, _, _, _, idate, _, _, _, status, _ = r
                print(f"{lid:<16} | {lnum[:24]:<24} | {idate:<10} | {status:<8}")

        elif table == "purchase_orders":
            print(f"{'NO PO':<18} | {'REKANAN':<26} | {'QTY (KG)':<8} | {'TOTAL (RP)':<12}")
            print("-" * 70)
            for r in rows:
                pno, _, _, sname, _, qty, _, tot, _, _, status, _, _ = r
                print(f"{pno:<18} | {sname[:26]:<26} | {qty:>8.1f} | {tot:>12,.0f}")

        else:
            print("Kolom:", ", ".join(columns[:5]))
            for r in rows[:3]:
                print(" ", r[:5])

    print("\n" + "=" * 70)
    conn.close()


if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    inspect_database(arg)

