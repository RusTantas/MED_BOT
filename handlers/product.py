from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import PRODUCT_TEXT

async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ Впервые в программе", callback_data="product_new")],
        [InlineKeyboardButton("2️⃣ Продолжаю 2‑й месяц", callback_data="product_month2")],
        [InlineKeyboardButton("3️⃣ Уже 2+ месяца", callback_data="product_long")],
        [InlineKeyboardButton("← Назад в меню", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=PRODUCT_TEXT,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )