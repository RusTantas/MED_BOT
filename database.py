# database.py
import sqlite3
import os
from datetime import datetime
from logger import logger

DB_PATH = "./storage/users.db"

def init_database():
    """Инициализация базы данных"""
    os.makedirs("./storage", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей
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
    
    # Индексы для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON users(chat_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON users(is_active)')
    
    # Таблица рассылок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            broadcast_type TEXT,  -- text, photo, document
            content TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_users INTEGER DEFAULT 0,
            successful_sends INTEGER DEFAULT 0,
            failed_sends INTEGER DEFAULT 0
        )
    ''')
    
    # История отправки рассылок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcast_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            broadcast_id INTEGER,
            user_id INTEGER,
            chat_id INTEGER,
            status TEXT,  -- success, failed
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (broadcast_id) REFERENCES broadcasts(broadcast_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"База данных инициализирована: {DB_PATH}")

def add_or_update_user(user_data):
    """Добавляет или обновляет пользователя в базе"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, chat_id, username, first_name, last_name, language_code, is_bot, last_active, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['id'],
        user_data.get('chat_id', user_data['id']),  # По умолчанию chat_id = user_id
        user_data.get('username'),
        user_data.get('first_name'),
        user_data.get('last_name'),
        user_data.get('language_code'),
        1 if user_data.get('is_bot', False) else 0,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        1
    ))
    
    conn.commit()
    conn.close()

def get_all_active_users():
    """Получает всех активных пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, chat_id, username, first_name, last_name 
        FROM users 
        WHERE is_active = 1
        ORDER BY joined_at DESC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': row[0],
        'chat_id': row[1],
        'username': row[2],
        'first_name': row[3],
        'last_name': row[4]
    } for row in users]

def get_user_count():
    """Возвращает количество пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def add_broadcast_record(admin_id, broadcast_type, content):
    """Добавляет запись о рассылке"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO broadcasts (admin_id, broadcast_type, content)
        VALUES (?, ?, ?)
    ''', (admin_id, broadcast_type, content))
    
    broadcast_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return broadcast_id

def update_broadcast_stats(broadcast_id, total_users, successful_sends, failed_sends):
    """Обновляет статистику рассылки"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE broadcasts 
        SET total_users = ?, successful_sends = ?, failed_sends = ?
        WHERE broadcast_id = ?
    ''', (total_users, successful_sends, failed_sends, broadcast_id))
    
    conn.commit()
    conn.close()

def add_broadcast_log(broadcast_id, user_id, chat_id, status, error_message=None):
    """Добавляет лог отправки рассылки"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO broadcast_logs (broadcast_id, user_id, chat_id, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (broadcast_id, user_id, chat_id, status, error_message))
    
    conn.commit()
    conn.close()

def get_broadcast_history(limit=10):
    """Получает историю рассылок"""
    conn = sqlite3.connect(DB_PATH)
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
    
    broadcasts = cursor.fetchall()
    conn.close()
    
    return [{
        'broadcast_id': row[0],
        'admin_id': row[1],
        'type': row[2],
        'sent_at': row[3],
        'total_users': row[4],
        'successful': row[5],
        'failed': row[6],
        'content': row[7][:100] + '...' if row[7] and len(row[7]) > 100 else row[7]
    } for row in broadcasts]

# Инициализация при импорте
init_database()