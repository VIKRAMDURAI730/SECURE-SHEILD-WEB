"""View database contents in the terminal. Run: python view_db.py"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'purchase.db')

W = 72  # table width


def _row(*cells, widths=None):
    """Format a table row with aligned columns."""
    if widths:
        parts = [str(c)[:w].ljust(w) for c, w in zip(cells, widths)]
        return "| " + " | ".join(parts) + " |"
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _sep(widths):
    return "+-" + "-+-".join("-" * w for w in widths) + "-+"


def run():
    if not os.path.exists(DB_PATH):
        print("No database found. Run the app first (python app.py) and register or place an order.")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Error opening database: {e}")
        return
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def section(title):
        print()
        print("=" * W)
        print(f"  {title}")
        print("=" * W)

    # --- USERS ---
    section("USERS")
    try:
        cur.execute("SELECT id, email, name, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  Error: {e}")
    else:
        if not rows:
            print("  (none)")
        else:
            w = (6, 28, 18, 20)
            print(_sep(w))
            print(_row("id", "email", "name", "created_at", widths=w))
            print(_sep(w))
            for r in rows:
                print(_row(r[0], r[1] or "", r[2] or "", r[3] or "", widths=w))
            print(_sep(w))

    # --- PRODUCTS ---
    section("PRODUCTS")
    try:
        cur.execute("SELECT id, name, price, image FROM products ORDER BY id")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  Error: {e}")
    else:
        if not rows:
            print("  (none)")
        else:
            w = (6, 24, 10, 30)
            print(_sep(w))
            print(_row("id", "name", "price", "image", widths=w))
            print(_sep(w))
            for r in rows:
                img = (str(r[3])[:28] + "..") if r[3] and len(str(r[3])) > 30 else (r[3] or "")
                print(_row(r[0], r[1] or "", f"${r[2]:.2f}", img, widths=w))
            print(_sep(w))

    # --- ORDERS ---
    section("ORDERS")
    try:
        cur.execute("""
            SELECT o.id, o.user_id, u.email, o.total, o.shipping_name, o.shipping_address, o.created_at
            FROM orders o
            JOIN users u ON u.id = o.user_id
            ORDER BY o.id
        """)
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  Error: {e}")
    else:
        if not rows:
            print("  (none)")
        else:
            w = (10, 8, 22, 10, 22)
            print(_sep(w))
            print(_row("order_id", "user_id", "email", "total", "created_at", widths=w))
            print(_sep(w))
            for r in rows:
                print(_row(r[0], r[1], r[2] or "", f"${r[3]:.2f}", r[6] or "", widths=w))
            print(_sep(w))
            for r in rows:
                print(f"  Order #{r[0]}: ship to {r[4] or ''}, {r[5] or ''}")

    # --- ORDER ITEMS ---
    section("ORDER ITEMS")
    try:
        cur.execute("""
            SELECT oi.order_id, p.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            ORDER BY oi.order_id, oi.id
        """)
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  Error: {e}")
    else:
        if not rows:
            print("  (none)")
        else:
            w = (10, 28, 10, 10)
            print(_sep(w))
            print(_row("order_id", "product", "qty", "price", widths=w))
            print(_sep(w))
            for r in rows:
                print(_row(r[0], r[1] or "", r[2], f"${r[3]:.2f}", widths=w))
            print(_sep(w))

    # --- SECURITY EVENTS ---
    section("SECURITY EVENTS (Owner Dashboard)")
    try:
        cur.execute("""
            SELECT id, created_at, event_type, attacker_name, ip_address, location, fixed, message
            FROM security_events
            ORDER BY id DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  Error: {e}")
    else:
        if not rows:
            print("  (none)")
        else:
            w = (6, 22, 12, 22, 12, 12, 8, 40)
            print(_sep(w))
            print(_row("id", "created_at", "type", "attacker", "ip", "location", "fixed", "message", widths=w))
            print(_sep(w))
            for r in rows:
                print(_row(r[0], r[1] or "", r[2] or "", r[3] or "", r[4] or "", r[5] or "", "Yes" if r[6] else "No", (r[7] or "")[:38], widths=w))
            print(_sep(w))

    conn.close()
    print()

if __name__ == "__main__":
    run()
