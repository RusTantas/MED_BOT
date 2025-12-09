# handlers/consent.py
import csv
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

from config import CONSENT_TEXT

# Состояния диалога
FULL_NAME, PHONE, EMAIL, CONFIRM = range(4)

# Путь к CSV
CSV_PATH = "./storage/leads.csv"
os.makedirs("./storage", exist_ok=True)

# Создаём CSV с заголовком, если не существует
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "full_name", "phone", "email", "telegram_username"])

async def consent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало формы: показываем текст согласия и кнопку «Начать»"""
    keyboard = [[InlineKeyboardButton("✅ Начать заполнение", callback_data="consent_start")],
                [InlineKeyboardButton("← Назад в меню", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        CONSENT_TEXT,
        reply_markup=reply_markup
    )
    return FULL_NAME

async def consent_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔤 Укажите, пожалуйста, ваше ФИО:")
    return FULL_NAME

async def full_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔹 Сохраняем Telegram-логин пользователя (если есть)
    user = update.effective_user
    username = user.username or ""
    display_username = f"@{username}" if username else ""
    context.user_data["telegram_username"] = display_username
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📱 Введите номер телефона (лучше с +7):")
    return PHONE

async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("📧 Укажите email (необязательно, но желательно):")
    return EMAIL

async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text.strip()
    
    # Подтверждение
    text = (
        "Проверьте введённые данные:\n\n"
        f"ФИО: {context.user_data['full_name']}\n"
        f"Телефон: {context.user_data['phone']}\n"
        f"Email: {context.user_data['email'] or '—'}\n\n"
        "Всё верно?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Да, всё верно", callback_data="consent_confirm")],
        [InlineKeyboardButton("✏️ Заполнить заново", callback_data="consent_restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)
    return CONFIRM

async def consent_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    # Сохраняем в CSV
    data = context.user_data
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            data.get("full_name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("telegram_username", "")
        ])
    
    await update.callback_query.message.reply_text(
        "✅ Спасибо! Ваши данные сохранены. С вами скоро свяжутся для уточнения деталей."
    )
    return ConversationHandler.END

async def consent_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔁 Заполняем заново:")
    return await consent_full_name(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Форма отменена. Вы можете начать снова через меню.")
    return ConversationHandler.END



# Влада вариант
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import ContextTypes

# async def consent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     text = "Форма согласия на обработку персональных данных.\n\n*Здесь будет форма с полями:*\n- ФИО\n- Телефон\n- Email\n- Согласие (галочка)"
    
#     keyboard = [
#         [InlineKeyboardButton("Заполнить форму", callback_data="start_form")],
#         [InlineKeyboardButton("← Назад в меню", callback_data="back")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await query.edit_message_text(
#         text=text,
#         reply_markup=reply_markup
#     )

# async def start_form_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     await query.edit_message_text(
#         text="Начало формы... (будет реализовано позже)",
#         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="consent")]])
#     )