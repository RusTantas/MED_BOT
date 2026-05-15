import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from logger import logger
from config import DB_PATH, STORAGE_DIR

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_bot INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON users(chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON users(is_active)')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                broadcast_type TEXT,
                content TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_users INTEGER DEFAULT 0,
                successful_sends INTEGER DEFAULT 0,
                failed_sends INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcast_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_id INTEGER,
                user_id INTEGER,
                chat_id INTEGER,
                status TEXT,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (broadcast_id) REFERENCES broadcasts(broadcast_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

    logger.info(f"База данных инициализирована: {DB_PATH}")

def add_or_update_user(user_data):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, chat_id, username, first_name, last_name, language_code, is_bot, last_active, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data['id'],
            user_data.get('chat_id', user_data['id']),
            user_data.get('username'),
            user_data.get('first_name'),
            user_data.get('last_name'),
            user_data.get('language_code'),
            1 if user_data.get('is_bot', False) else 0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            1
        ))

def get_all_active_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, chat_id, username, first_name, last_name 
            FROM users 
            WHERE is_active = 1
            ORDER BY joined_at DESC
        ''')
        rows = cursor.fetchall()

    return [{
        'user_id': row[0],
        'chat_id': row[1],
        'username': row[2],
        'first_name': row[3],
        'last_name': row[4]
    } for row in rows]

def get_user_count():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        count = cursor.fetchone()[0]
    return count

def add_broadcast_record(admin_id, broadcast_type, content):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcasts (admin_id, broadcast_type, content)
            VALUES (?, ?, ?)
        ''', (admin_id, broadcast_type, content))
        broadcast_id = cursor.lastrowid
    return broadcast_id

def update_broadcast_stats(broadcast_id, total_users, successful_sends, failed_sends):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE broadcasts 
            SET total_users = ?, successful_sends = ?, failed_sends = ?
            WHERE broadcast_id = ?
        ''', (total_users, successful_sends, failed_sends, broadcast_id))

def add_broadcast_log(broadcast_id, user_id, chat_id, status, error_message=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcast_logs (broadcast_id, user_id, chat_id, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (broadcast_id, user_id, chat_id, status, error_message))

def get_broadcast_history(limit=10):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                broadcast_id,
                admin_id,
                broadcast_type,
                strftime('%d.%m.%Y %H:%M', sent_at) as sent_at,
                total_users,
                successful_sends,
                failed_sends,
                content
            FROM broadcasts
            ORDER BY sent_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()

    return [{
        'broadcast_id': row[0],
        'admin_id': row[1],
        'type': row[2],
        'sent_at': row[3],
        'total_users': row[4],
        'successful': row[5],
        'failed': row[6],
        'content': row[7][:100] + '...' if row[7] and len(row[7]) > 100 else row[7]
    } for row in rows]
