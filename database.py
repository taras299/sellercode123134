import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            balance REAL DEFAULT 0,
            is_banned BOOLEAN DEFAULT 0,
            registration_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promos (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            uses INTEGER,
            amount REAL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(telegram_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, registration_date)
        VALUES (?, datetime('now'))
    ''', (telegram_id,))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users WHERE telegram_id=?
    ''', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_balance(telegram_id, amount):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET balance = balance + ?
        WHERE telegram_id = ?
    ''', (amount, telegram_id))
    conn.commit()
    conn.close()

def ban_user(telegram_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET is_banned = 1
        WHERE telegram_id = ?
    ''', (telegram_id,))
    conn.commit()
    conn.close()

def unban_user(telegram_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET is_banned = 0
        WHERE telegram_id = ?
    ''', (telegram_id,))
    conn.commit()
    conn.close()

def create_promo(code, uses, amount):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO promos (code, uses, amount)
        VALUES (?, ?, ?)
    ''', (code, uses, amount))
    conn.commit()
    conn.close()
