import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import PRODUCT_CONTENT_FILE, BASE_PRODUCT_TEXT

def load_product_text():
    """Загружает текст продукта из файла"""
    try:
        if os.path.exists(PRODUCT_CONTENT_FILE):
            with open(PRODUCT_CONTENT_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception as e:
        print(f"Ошибка загрузки текста продукта: {e}")
    
    return BASE_PRODUCT_TEXT

async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Загружаем актуальный текст
    product_text = load_product_text()
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ Впервые в программе", callback_data="product_new")],
        [InlineKeyboardButton("2️⃣ Продолжаю 2‑й месяц", callback_data="product_month2")],
        [InlineKeyboardButton("3️⃣ Уже 2+ месяца", callback_data="product_long")],
        [InlineKeyboardButton("← Назад в меню", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=product_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )