import sqlite3
import random
import time
from pathlib import Path

DB_PATH = Path("game_local.db")

LOOT_META = {
    "none": {"display_name": "Dneska nic", "price": 0},
    "rare": {"display_name": "Sleva 5%", "price": 5},
    "epic": {"display_name": "Sleva 20%", "price": 20},
    "mythic": {"display_name": "AirForce1 zdarma", "price": 75},
    "legendary": {"display_name": "200$ kredit", "price": 200},
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_loot_meta(key_name: str):
    return LOOT_META.get(key_name, {"display_name": key_name, "price": 0})


def get_case_price(case_id=1):
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT price FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    return int(row["price"]) if row else 20


def _ensure_schema(conn):
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        credits INTEGER DEFAULT 200,
        created_at INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS loot_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        key_name TEXT,
        weight INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS case_openings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        outcome TEXT,
        created_at INTEGER
    )
    """)

    conn.commit()


def init_db():
    conn = get_conn()
    c = conn.cursor()
    _ensure_schema(conn)

    case = c.execute("SELECT id FROM cases LIMIT 1").fetchone()
    if not case:
        c.execute(
            "INSERT INTO cases (name, price) VALUES (?, ?)",
            ("Hyper Bedna", 20)
        )
        case_id = c.lastrowid

        loots = [
            ("none", 80),
            ("rare", 10),
            ("epic", 5),
            ("mythic", 4),
            ("legendary", 1),
        ]

        for key_name, weight in loots:
            c.execute(
                "INSERT INTO loot_items (case_id, key_name, weight) VALUES (?, ?, ?)",
                (case_id, key_name, weight)
            )

    conn.commit()
    conn.close()


def get_or_create_user(username):
    conn = get_conn()
    c = conn.cursor()

    user = c.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if not user:
        c.execute(
            "INSERT INTO users (username, credits, created_at) VALUES (?, ?, ?)",
            (username, 200, int(time.time()))
        )
        conn.commit()
        user = c.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    conn.close()
    return dict(user)


def open_case(username, case_id=1):
    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("BEGIN")

        user = c.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        case = c.execute(
            "SELECT * FROM cases WHERE id = ?",
            (case_id,)
        ).fetchone()

        if not user or not case:
            conn.rollback()
            return {"success": False, "error": "missing_user_or_case"}

        if user["credits"] < case["price"]:
            conn.rollback()
            return {"success": False, "error": "not_enough_credits"}

        loots = c.execute(
            "SELECT * FROM loot_items WHERE case_id = ?",
            (case_id,)
        ).fetchall()

        if not loots:
            conn.rollback()
            return {"success": False, "error": "no_loot_items"}

        total_weight = sum(l["weight"] for l in loots)
        roll = random.randint(1, total_weight)

        picked = loots[0]
        current = 0
        for loot in loots:
            current += loot["weight"]
            if roll <= current:
                picked = loot
                break

        new_credits = user["credits"] - case["price"]

        c.execute(
            "UPDATE users SET credits = ? WHERE username = ?",
            (new_credits, username)
        )

        c.execute("""
            INSERT INTO case_openings (username, outcome, created_at)
            VALUES (?, ?, ?)
        """, (username, picked["key_name"], int(time.time())))

        conn.commit()

        return {
            "success": True,
            "loot": {"key": picked["key_name"]},
            "user_credits": new_credits,
            "case_price": case["price"]
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_history_rows(limit=10):
    conn = get_conn()
    c = conn.cursor()

    rows = c.execute("""
        SELECT username, outcome, created_at
        FROM case_openings
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    result = []
    for r in rows:
        meta = get_loot_meta(r["outcome"])
        result.append({
            "username": r["username"],
            "outcome": r["outcome"],
            "loot_name": meta["display_name"],
            "loot_price": meta["price"],
            "time": time.strftime("%H:%M:%S", time.localtime(r["created_at"])),
        })
    return result


def get_history(limit=10):
    rows = get_history_rows(limit)
    return [
        f"{r['username']}  |  {r['loot_name']}  |  ${r['loot_price']}  |  {r['time']}"
        for r in rows
    ]


def get_leaderboard(limit=20):
    conn = get_conn()
    c = conn.cursor()

    rows = c.execute("""
        SELECT username, credits
        FROM users
        ORDER BY credits DESC, username ASC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_top_wins(limit=10):
    conn = get_conn()
    c = conn.cursor()

    rows = c.execute("""
        SELECT username, outcome, created_at
        FROM case_openings
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    result = []
    for r in rows:
        meta = get_loot_meta(r["outcome"])
        result.append({
            "username": r["username"],
            "outcome": r["outcome"],
            "loot_name": meta["display_name"],
            "loot_price": meta["price"],
            "time": time.strftime("%H:%M:%S", time.localtime(r["created_at"])),
        })

    result.sort(key=lambda x: (x["loot_price"], x["time"]), reverse=True)
    return result[:limit]