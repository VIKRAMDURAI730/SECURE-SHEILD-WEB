"""SQLite database setup and helpers."""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'purchase.db')


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    """Context manager for database operations."""
    conn = get_db()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables and seed products."""
    with db_cursor() as cur:
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                image TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                shipping_name TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                attacker_name TEXT,
                ip_address TEXT,
                location TEXT,
                fixed INTEGER NOT NULL DEFAULT 1,
                message TEXT,
                details TEXT,
                user_agent TEXT
            );
        ''')

        # Seed / expand products safely (insert by name if missing)
        products = [
            ('Wireless Headphones', 89.99, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop'),
            ('Mechanical Keyboard', 129.99, 'https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=400&h=400&fit=crop'),
            ('Portable SSD 1TB', 119.99, 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&h=400&fit=crop'),
            ('Smart Watch', 199.99, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop'),
            ('Desk Lamp', 49.99, 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop'),
            ('USB-C Hub', 45.99, 'https://images.unsplash.com/photo-1625723044792-44de16ccb4e9?w=400&h=400&fit=crop'),
            ('Bluetooth Speaker', 59.99, 'https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=400&h=400&fit=crop'),
            ('Gaming Mouse', 39.99, 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=400&h=400&fit=crop'),
            ('4K Monitor 27\"', 289.99, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&h=400&fit=crop'),
            ('Laptop Stand', 24.99, 'https://images.unsplash.com/photo-1581345334162-fce5d1c6b7d6?w=400&h=400&fit=crop'),
            ('Noise Cancelling Earbuds', 79.99, 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&h=400&fit=crop'),
            ('Webcam HD', 34.99, 'https://images.unsplash.com/photo-1612810436541-336d9f9b99f1?w=400&h=400&fit=crop'),
            ('Office Chair', 149.99, 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=400&fit=crop'),
            ('Notebook (A5)', 9.99, 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=400&h=400&fit=crop'),
            ('Water Bottle', 14.99, 'https://images.unsplash.com/photo-1526401485004-2aa7b82b7b1b?w=400&h=400&fit=crop'),
            ('Backpack', 54.99, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop'),
        ]

        for name, price, image in products:
            cur.execute('SELECT 1 FROM products WHERE name = ? LIMIT 1', (name,))
            exists = cur.fetchone()
            if not exists:
                cur.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', (name, price, image))
