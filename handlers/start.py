# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import AUTHOR_NAME
import database  # Импортируем нашу базу данных

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем пользователя в базу данных
    user = update.effective_user
    
    user_data = {
        'id': user.id,
        'chat_id': update.effective_chat.id,  # Важно! Сохраняем chat_id
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'language_code': user.language_code,
        'is_bot': user.is_bot
    }
    
    database.add_or_update_user(user_data)
    
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
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.data == "back":
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Также сохраняем пользователя при взаимодействии с меню
    if update.effective_user:
        user = update.effective_user
        user_data = {
            'id': user.id,
            'chat_id': update.effective_chat.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language_code': user.language_code,
            'is_bot': user.is_bot
        }
        
        database.add_or_update_user(user_data)
    
    await start_handler(update, context)