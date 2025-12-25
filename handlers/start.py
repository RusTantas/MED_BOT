# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import AUTHOR_NAME

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"Добро пожаловать! Это чат-бот доктора {AUTHOR_NAME}. "
        "Здесь вы найдёте информацию об инфопродуктах, отзывы.\n"
        "Нажимая кнопку «Старт», вы активируете бота и даёте согласие на получение сообщений в этом чат-боте. \n"
        "Если вы еще не подписаны на мой блог обязательно подпешитесь \n"
        "@dr_halimova_gulnaz"

    )
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Об авторе", callback_data="about")],
        [InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")],
        [InlineKeyboardButton("🌿 Здорове тело", callback_data="product")],
        [InlineKeyboardButton("📅 Запись на консультацию", callback_data="booking")],
        [InlineKeyboardButton("Согласие на обработку ПД", callback_data="consent")],
        [InlineKeyboardButton("📥 Скачать гайд", callback_data="guide")]
        # остальные кнопки добавим позже — по ТЗ сначала только start + consent
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.data == "back":
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_handler(update, context)

