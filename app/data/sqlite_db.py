"""
Modul Basis Data SQLite SPPG (Deterministic Persistent Storage)

Menyediakan penyimpanan relasional lokal terstruktur berbasis SQLite standar Python
tanpa dependensi eksternal, mendukung transaksi ACID untuk:
1. Inventaris bahan pangan
2. Rekanan supplier halal
3. Riwayat Surat Edaran (Circular Letters) mitigasi
4. Riwayat Purchase Order (PO)
5. Rekam riwayat sesi obrolan AI
"""

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Lokasi berkas database SQLite
DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "resilio.db"


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Membuka koneksi thread-safe ke basis data SQLite dan menutupnya secara otomatis."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_sqlite_db() -> None:
    """Inisialisasi skema tabel relasional dan penyemaian data awal (seed)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Tabel Inventaris
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                item_id TEXT PRIMARY KEY,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                current_stock_kg REAL NOT NULL,
                safety_stock_kg REAL NOT NULL,
                freezer_capacity_kg REAL NOT NULL,
                freezer_occupied_kg REAL NOT NULL,
                sop_max_price_per_kg REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # 2. Tabel Rekanan Supplier
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id TEXT PRIMARY KEY,
                supplier_name TEXT NOT NULL,
                category TEXT NOT NULL,
                commodity TEXT NOT NULL,
                supported_items TEXT NOT NULL,
                halal_certified INTEGER NOT NULL,
                halal_cert_number TEXT,
                unit_price_idr REAL NOT NULL,
                daily_capacity_kg REAL NOT NULL,
                lead_time_hours REAL NOT NULL,
                distance_km REAL NOT NULL,
                reliability_rating REAL NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )

        # 3. Tabel Surat Edaran (Circular Letters)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS circular_letters (
                letter_id TEXT PRIMARY KEY,
                letter_number TEXT NOT NULL,
                title TEXT NOT NULL,
                incident_id TEXT,
                item_id TEXT,
                deficit_kg REAL,
                supplier_id TEXT,
                supplier_name TEXT,
                issued_date TEXT NOT NULL,
                signer_name TEXT NOT NULL,
                signer_role TEXT NOT NULL,
                content_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ISSUED',
                created_at TEXT NOT NULL
            )
            """
        )

        # 4. Tabel Purchase Order (PO)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS purchase_orders (
                po_number TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                supplier_id TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                item_id TEXT NOT NULL,
                approved_qty_kg REAL NOT NULL,
                unit_price_idr REAL NOT NULL,
                total_amount_idr REAL NOT NULL,
                logistics_strategy TEXT NOT NULL,
                approver_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'APPROVED',
                po_download_url TEXT,
                generated_at TEXT NOT NULL
            )
            """
        )

        # 5. Tabel Riwayat Sesi Obrolan
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                intent TEXT,
                action_required TEXT,
                preview_data TEXT,
                execution_trace TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Migrasi kolom execution_trace jika belum ada pada tabel lama
        try:
            cursor.execute("ALTER TABLE chat_history ADD COLUMN execution_trace TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        conn.commit()

        # Seed data awal hanya jika database benar-benar baru
        _seed_initial_data(conn)

        # Otomatis bersihkan duplikasi rekanan jika ada di database SQLite
        cleanup_duplicate_suppliers(conn)


def cleanup_duplicate_suppliers(conn: sqlite3.Connection) -> None:
    """Membersihkan duplikasi baris rekanan di SQLite berdasarkan nama yang identik."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM suppliers
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM suppliers
                GROUP BY LOWER(TRIM(supplier_name))
            )
            """
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass


def _seed_initial_data(conn: sqlite3.Connection) -> None:
    """Penyemaian dataset awal inventaris dan supplier SPPG jika tabel belum terisi."""
    cursor = conn.cursor()

    # Cek apakah inventory kosong
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now(timezone.utc).isoformat()
        seed_inventory = [
            ("ITEM-AYAM-01", "Daging Ayam Broiler Segar", "PROTEIN", 80.0, 30.0, 100.0, 80.0, 42000.0, now_str),
            ("ITEM-BERAS-01", "Beras Premium Ramos", "STAPLE", 500.0, 150.0, 0.0, 0.0, 16500.0, now_str),
            ("ITEM-TELUR-01", "Telur Ayam Ras Segar", "PROTEIN", 120.0, 50.0, 60.0, 40.0, 31000.0, now_str),
            ("ITEM-WORTEL-01", "Wortel Segar Brastagi", "VEGETABLE", 45.0, 20.0, 40.0, 25.0, 18000.0, now_str),
            ("ITEM-SAPI-01", "Daging Sapi Segar (Has Luar)", "PROTEIN", 50.0, 25.0, 80.0, 40.0, 135000.0, now_str),
            ("ITEM-TAHU-01", "Tahu Putih Segar", "PROTEIN", 50.0, 20.0, 40.0, 10.0, 25000.0, now_str),
            ("ITEM-TEMPE-01", "Tempe Kedelai Segar", "PROTEIN", 40.0, 15.0, 30.0, 10.0, 22000.0, now_str),
        ]
        cursor.executemany(
            """
            INSERT INTO inventory (
                item_id, item_name, category, current_stock_kg, safety_stock_kg,
                freezer_capacity_kg, freezer_occupied_kg, sop_max_price_per_kg, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_inventory,
        )

    # Cek apakah suppliers kosong
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now(timezone.utc).isoformat()
        seed_suppliers = [
            (
                "SUP-UTAMA-01", "PT Unggas Sejahtera Nusantara", "PROTEIN", "DAGING_AYAM",
                json.dumps(["ITEM-AYAM-01"]), 1, "ID32110000123450124", 37500.0, 300.0, 2.5, 12.0, 96.0, 1, now_str
            ),
            (
                "SUP-ALT-02", "PT Berkah Unggas Jaya", "PROTEIN", "DAGING_AYAM",
                json.dumps(["ITEM-AYAM-01"]), 1, "ID32110000897650324", 36500.0, 140.0, 4.0, 22.0, 95.0, 1, now_str
            ),
            (
                "SUP-REG-04", "CV Berkah Barokah Tahu", "PROTEIN", "TAHU",
                json.dumps(["ITEM-TAHU-01"]), 1, "ID32110000789010124", 18000.0, 200.0, 2.5, 14.0, 95.0, 1, now_str
            ),
            (
                "SUP-REG-05", "CV Berkah Tempe Alami", "PROTEIN", "TEMPE",
                json.dumps(["ITEM-TEMPE-01"]), 1, "ID32110000789010224", 16000.0, 180.0, 2.5, 15.0, 94.0, 1, now_str
            ),
            (
                "SUP-TELUR-01", "CV Sumber Telur Mandiri", "PROTEIN", "TELUR_AYAM",
                json.dumps(["ITEM-TELUR-01"]), 1, "ID32110000445560624", 28500.0, 500.0, 2.0, 12.0, 93.0, 1, now_str
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO suppliers (
                supplier_id, supplier_name, category, commodity, supported_items,
                halal_certified, halal_cert_number, unit_price_idr, daily_capacity_kg,
                lead_time_hours, distance_km, reliability_rating, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            seed_suppliers,
        )

    conn.commit()


# =========================================================================
# OPERASI SURAT EDARAN & PURCHASE ORDER
# =========================================================================

def clear_all_circular_letters() -> int:
    """Mengosongkan seluruh arsip surat edaran dari basis data SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM circular_letters")
        count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM circular_letters")
        conn.commit()
        return count


def clear_all_purchase_orders() -> int:
    """Mengosongkan seluruh arsip Purchase Order dari basis data SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM purchase_orders")
        count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM purchase_orders")
        conn.commit()
        return count


def clear_all_documents() -> Dict[str, int]:
    """Mengosongkan seluruh surat edaran dan purchase order secara simultan."""
    se_count = clear_all_circular_letters()
    po_count = clear_all_purchase_orders()
    return {"circular_letters_cleared": se_count, "purchase_orders_cleared": po_count}


def delete_circular_letter_by_id(identifier: str) -> bool:
    """Menghapus satu berkas surat edaran berdasarkan ID atau nomor surat."""
    init_sqlite_db()
    ident = identifier.strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM circular_letters WHERE letter_id = ? OR letter_number = ?",
            (ident, ident),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_purchase_order_by_number(po_number: str) -> bool:
    """Menghapus satu berkas Purchase Order berdasarkan nomor PO."""
    init_sqlite_db()
    pno = po_number.strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM purchase_orders WHERE po_number = ?",
            (pno,),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_purchase_order_by_number(po_number: str) -> Optional[Dict[str, Any]]:
    """Mengambil rincian satu berkas Purchase Order berdasarkan nomor PO."""
    init_sqlite_db()
    pno = po_number.strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (pno,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["logistics_strategy"] = json.loads(d["logistics_strategy"])
        except Exception:
            pass
        return d


# =========================================================================
# OPERASI SURAT EDARAN & PURCHASE ORDER
# =========================================================================

def get_all_circular_letters() -> List[Dict[str, Any]]:
    """Mengambil seluruh daftar surat edaran mitigasi SPPG."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM circular_letters ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_circular_letter_by_id(letter_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil satu surat edaran berdasarkan letter_id."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM circular_letters WHERE letter_id = ?", (letter_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_circular_letter(letter_data: Dict[str, Any]) -> Dict[str, Any]:
    """Menyimpan surat edaran baru ke dalam SQLite."""
    init_sqlite_db()
    now_str = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO circular_letters (
                letter_id, letter_number, title, incident_id, item_id, deficit_kg,
                supplier_id, supplier_name, issued_date, signer_name, signer_role,
                content_text, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                letter_data["letter_id"],
                letter_data["letter_number"],
                letter_data["title"],
                letter_data.get("incident_id"),
                letter_data.get("item_id"),
                letter_data.get("deficit_kg", 0.0),
                letter_data.get("supplier_id"),
                letter_data.get("supplier_name"),
                letter_data.get("issued_date", datetime.now().strftime("%Y-%m-%d")),
                letter_data.get("signer_name", "Kepala SPPG"),
                letter_data.get("signer_role", "Kepala Satuan Pelayanan Pemenuhan Gizi"),
                letter_data["content_text"],
                letter_data.get("status", "ISSUED"),
                now_str,
            ),
        )
        conn.commit()
    return get_circular_letter_by_id(letter_data["letter_id"]) or letter_data


def get_all_purchase_orders() -> List[Dict[str, Any]]:
    """Mengambil seluruh daftar Purchase Order (PO) yang diterbitkan."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase_orders ORDER BY generated_at DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["logistics_strategy"] = json.loads(d["logistics_strategy"])
            except Exception:
                pass
            result.append(d)
        return result


def save_purchase_order(po_data: Dict[str, Any]) -> Dict[str, Any]:
    """Menyimpan Purchase Order resmi ke dalam SQLite."""
    init_sqlite_db()
    logistics_str = (
        json.dumps(po_data["logistics_strategy"])
        if isinstance(po_data.get("logistics_strategy"), (dict, list))
        else str(po_data.get("logistics_strategy", "{}"))
    )
    gen_at = po_data.get("generated_at")
    if hasattr(gen_at, "isoformat"):
        gen_at_str = gen_at.isoformat()
    elif isinstance(gen_at, str):
        gen_at_str = gen_at
    else:
        gen_at_str = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO purchase_orders (
                po_number, incident_id, supplier_id, supplier_name, item_id,
                approved_qty_kg, unit_price_idr, total_amount_idr, logistics_strategy,
                approver_name, status, po_download_url, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                po_data["po_number"],
                po_data["incident_id"],
                po_data["supplier_id"],
                po_data["supplier_name"],
                po_data["item_id"],
                po_data["approved_qty_kg"],
                po_data["unit_price_idr"],
                po_data["total_amount_idr"],
                logistics_str,
                po_data.get("approver_name", "Kepala SPPG"),
                po_data.get("status", "APPROVED"),
                po_data.get("po_download_url", f"/api/v1/orders/{po_data['po_number']}/pdf"),
                gen_at_str,
            ),
        )
        conn.commit()
    return po_data


# =========================================================================
# OPERASI INVENTARIS & SUPPLIER DI SQLITE
# =========================================================================

def get_all_inventory_items() -> List[Dict[str, Any]]:
    """Mengambil seluruh data inventaris bahan pangan dari SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory ORDER BY category, item_name")
        return [dict(row) for row in cursor.fetchall()]


def get_inventory_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil rincian data satu bahan pangan dari SQLite berdasarkan ID atau nama bahan."""
    init_sqlite_db()
    ident = item_id.strip()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM inventory WHERE UPPER(item_id) = UPPER(?) OR LOWER(item_name) = LOWER(?)",
            (ident, ident),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def upsert_inventory_item(item_data: Dict[str, Any]) -> None:
    """Menyimpan atau memperbarui data bahan pangan inventaris ke basis data SQLite."""
    init_sqlite_db()
    now_str = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO inventory (
                item_id, item_name, category, current_stock_kg, safety_stock_kg,
                freezer_capacity_kg, freezer_occupied_kg, sop_max_price_per_kg, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_data["item_id"],
                item_data["item_name"],
                item_data["category"],
                float(item_data["current_stock_kg"]),
                float(item_data["safety_stock_kg"]),
                float(item_data["freezer_capacity_kg"]),
                float(item_data["freezer_occupied_kg"]),
                float(item_data["sop_max_price_per_kg"]),
                item_data.get("updated_at", now_str),
            ),
        )
        conn.commit()


def reset_sqlite_to_default() -> None:
    """Mereset tabel inventaris dan supplier kembali ke seed bawaan langsung di SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory")
        cursor.execute("DELETE FROM suppliers")
        conn.commit()
        _seed_initial_data(conn)


def get_all_suppliers(include_inactive: bool = False, commodity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Mengambil katalog rekanan supplier dari SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM suppliers WHERE 1=1"
        params: List[Any] = []
        if not include_inactive:
            query += " AND is_active = 1"
        if commodity:
            query += " AND UPPER(commodity) = ?"
            params.append(commodity.strip().upper())
        query += " ORDER BY reliability_rating DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["halal_certified"] = bool(d["halal_certified"])
            d["is_active"] = bool(d["is_active"])
            try:
                d["supported_items"] = json.loads(d["supported_items"])
            except Exception:
                d["supported_items"] = []
            result.append(d)
        return result


def upsert_supplier(record: Dict[str, Any]) -> None:
    """Menyimpan atau memperbarui data rekanan supplier ke SQLite."""
    init_sqlite_db()
    now_str = datetime.now(timezone.utc).isoformat()
    supported_str = (
        json.dumps(record["supported_items"])
        if isinstance(record.get("supported_items"), list)
        else str(record.get("supported_items", "[]"))
    )
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO suppliers (
                supplier_id, supplier_name, category, commodity, supported_items,
                halal_certified, halal_cert_number, unit_price_idr, daily_capacity_kg,
                lead_time_hours, distance_km, reliability_rating, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["supplier_id"],
                record["supplier_name"],
                record["category"],
                record["commodity"],
                supported_str,
                1 if record["halal_certified"] else 0,
                record.get("halal_cert_number"),
                record["unit_price_idr"],
                record["daily_capacity_kg"],
                record["lead_time_hours"],
                record["distance_km"],
                record["reliability_rating"],
                1 if record.get("is_active", True) else 0,
                record.get("created_at", now_str),
            ),
        )
        conn.commit()


def deactivate_supplier_in_db(supplier_id: str) -> bool:
    """Menonaktifkan rekanan di SQLite (is_active = 0 / Soft Delete)."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE suppliers SET is_active = 0 WHERE UPPER(supplier_id) = UPPER(?) OR LOWER(supplier_name) = LOWER(?)",
            (supplier_id.strip(), supplier_id.strip()),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_supplier_permanently_from_db(supplier_id: str) -> bool:
    """Menghapus baris rekanan secara permanen (Hard Delete) dari SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM suppliers WHERE UPPER(supplier_id) = UPPER(?) OR LOWER(supplier_name) = LOWER(?)",
            (supplier_id.strip(), supplier_id.strip()),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_supplier_by_id_from_db(supplier_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil rincian data rekanan supplier dari basis data SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM suppliers WHERE UPPER(supplier_id) = UPPER(?) OR LOWER(supplier_name) = LOWER(?)",
            (supplier_id.strip(), supplier_id.strip()),
        )
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["halal_certified"] = bool(d["halal_certified"])
        d["is_active"] = bool(d["is_active"])
        try:
            d["supported_items"] = json.loads(d["supported_items"])
        except Exception:
            d["supported_items"] = []
        return d


# =========================================================================
# OPERASI RIWAYAT CHAT
# =========================================================================

def record_chat_message(
    session_id: str,
    role: str,
    message: str,
    intent: Optional[str] = None,
    action_required: Optional[str] = None,
    preview_data: Optional[Dict[str, Any]] = None,
    execution_trace: Optional[List[Any]] = None,
) -> None:
    """Merekam satu putaran pesan obrolan ke SQLite."""
    init_sqlite_db()
    now_str = datetime.now(timezone.utc).isoformat()
    preview_str = json.dumps(preview_data) if preview_data else None
    trace_str = None
    if execution_trace:
        try:
            raw_traces = [t.model_dump() if hasattr(t, "model_dump") else (t.dict() if hasattr(t, "dict") else t) for t in execution_trace]
            trace_str = json.dumps(raw_traces)
        except Exception:
            trace_str = None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_history (
                session_id, role, message, intent, action_required, preview_data, execution_trace, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, role, message, intent, action_required, preview_str, trace_str, now_str),
        )
        conn.commit()


def get_chat_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Mengambil riwayat obrolan untuk sesi tertentu dari SQLite."""
    init_sqlite_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_history WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("preview_data"):
                try:
                    d["preview_data"] = json.loads(d["preview_data"])
                except Exception:
                    pass
            if d.get("execution_trace"):
                try:
                    d["execution_trace"] = json.loads(d["execution_trace"])
                except Exception:
                    pass
            result.append(d)
        return result
