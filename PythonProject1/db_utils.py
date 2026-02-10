# db_utils.py
import sqlite3, json, random, time
from pathlib import Path

DB_PATH = Path("game_local.db")

def init_db():
    first = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        credits INTEGER DEFAULT 0,
        created_at INTEGER
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price_cents INTEGER
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS loot_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        key_name TEXT,
        display_name TEXT,
        weight INTEGER,
        payload TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS case_openings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        case_id INTEGER,
        loot_item_id INTEGER,
        outcome TEXT,
        created_at INTEGER
    )""")

    conn.commit()

    if first:
        c.execute("INSERT INTO users (username, credits, created_at) VALUES (?,?,?)",
                  ("demo", 20000000000, int(time.time())))

        c.execute("INSERT INTO cases (name, price_cents) VALUES (?,?)",
                  ("Hyper Bedna", 20))
        case_id = c.lastrowid

        loots = [
            ("none", "Dneska nic", 90, "{}"),
            ("rare", "Sleva 5%", 4, "{}"),
            ("epic", "Sleva 20%", 3, "{}"),
            ("mythic", "AirForce1 zdarma", 2, "{}"),
            ("legendary", "200$ kredit", 1, '{"type":"credits","amount":20000}')
        ]

        for k, n, w, p in loots:
            c.execute(
                "INSERT INTO loot_items (case_id, key_name, display_name, weight, payload) VALUES (?,?,?,?,?)",
                (case_id, k, n, w, p)
            )
        conn.commit()

    conn.close()

def get_user(user_id=1):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    u = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(u) if u else None

def open_case_local(user_id, case_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("BEGIN")

        user = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        case = c.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()

        if user["credits"] < case["price_cents"]:
            conn.rollback()
            return {"success": False}

        credits = user["credits"] - case["price_cents"]
        c.execute("UPDATE users SET credits=? WHERE id=?", (credits, user_id))

        loots = c.execute("SELECT * FROM loot_items WHERE case_id=?", (case_id,)).fetchall()
        total = sum(l["weight"] for l in loots)
        roll = random.randint(1, total)

        s = 0
        picked = loots[0]
        for l in loots:
            s += l["weight"]
            if roll <= s:
                picked = l
                break

        payload = json.loads(picked["payload"])
        if payload.get("type") == "credits":
            credits += payload["amount"]
            c.execute("UPDATE users SET credits=? WHERE id=?", (credits, user_id))

        c.execute(
            "INSERT INTO case_openings (user_id, case_id, loot_item_id, outcome, created_at) VALUES (?,?,?,?,?)",
            (user_id, case_id, picked["id"], picked["key_name"], int(time.time()))
        )

        conn.commit()
        return {
            "success": True,
            "loot": {"key": picked["key_name"]},
            "user_credits": credits
        }

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        conn.close()