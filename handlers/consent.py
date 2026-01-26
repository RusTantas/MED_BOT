# handlers/consent.py
import csv
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger

from config import CONSENT_TEXT

# Состояния
FULL_NAME, PHONE, EMAIL, CONFIRM = range(4)

CSV_PATH = "./storage/leads.csv"
os.makedirs("./storage", exist_ok=True)

if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", 
            "full_name", 
            "phone", 
            "email", 
            "telegram_username", 
            "tariff"
        ])


def get_back_button():
    return [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]


# --- СТАРТ: показываем текст + кнопку "Начать" ---
async def consent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_tariff = context.user_data.get("selected_tariff", "не указан")
    consent_text = CONSENT_TEXT.format(tariff=selected_tariff)

    keyboard = [
        [InlineKeyboardButton("✅ Начать заполнение", callback_data="consent_start")],
        [InlineKeyboardButton("← Назад", callback_data="product")]
    ]
    await query.edit_message_text(
        text=consent_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return FULL_NAME


# --- После нажатия "Начать" — задаём вопрос ФИО ---
async def consent_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Отправляем НОВОЕ сообщение с вопросом (или редактируем текущее)
    # Но лучше — редактируем текущее (оно и так есть)
    keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
    await query.edit_message_text(
        text="🔤 Укажите, пожалуйста, ваше ФИО:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # Сохраняем ID этого сообщения для последующих шагов
    context.user_data["form_message_id"] = query.message.message_id
    context.user_data["form_chat_id"] = query.message.chat_id
    return FULL_NAME


# --- Получено ФИО → переходим к телефону, редактируя ТО ЖЕ сообщение ---
async def full_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 📝 Сохраняем данные
    user = update.effective_user
    context.user_data["telegram_username"] = f"@{user.username}" if user.username else ""
    context.user_data["full_name"] = update.message.text.strip()

    # ✅ Удаляем сообщение с вводом пользователя (например, "Иванов И.И.")
    try:
        await update.message.delete()
    except:
        pass  # если не получилось — не критично

    # ✅ Редактируем сообщение с вопросом (сохранённое ранее)
    chat_id = context.user_data.get("form_chat_id")
    msg_id = context.user_data.get("form_message_id")

    if chat_id and msg_id:
        try:
            keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text="📱 Введите номер телефона (лучше с +7):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            # Если сообщение уже удалено — создаём новое
            sent = await update.message.reply_text(
                "📱 Введите номер телефона (лучше с +7):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data["form_message_id"] = sent.message_id
            context.user_data["form_chat_id"] = sent.chat_id
    else:
        # На всякий — fallback
        sent = await update.message.reply_text(
            "📱 Введите номер телефона (лучше с +7):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back")]])
        )
        context.user_data["form_message_id"] = sent.message_id
        context.user_data["form_chat_id"] = sent.chat_id

    return PHONE

# --- После продолжения — задаём вопрос почты ---
async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    try:
        await update.message.delete()
    except:
        pass

    chat_id = context.user_data.get("form_chat_id")
    msg_id = context.user_data.get("form_message_id")

    if chat_id and msg_id:
        try:
            keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text="📧 Укажите email (необязательно, но желательно):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            sent = await update.message.reply_text(
                "📧 Укажите email (необязательно, но желательно):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data["form_message_id"] = sent.message_id
            context.user_data["form_chat_id"] = sent.chat_id
    else:
        sent = await update.message.reply_text(
            "📧 Укажите email (необязательно, но желательно):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back")]])
        )
        context.user_data["form_message_id"] = sent.message_id
        context.user_data["form_chat_id"] = sent.chat_id

    return EMAIL


# --- Получен email → показываем подтверждение ---
async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text.strip() or ""
    try:
        await update.message.delete()
    except:
        pass

    tariff = context.user_data.get("selected_tariff", "не указан")
    text = (
        f"📌 Программа: *{tariff}*\n\n"
        "Проверьте введённые данные:\n\n"
        f"ФИО: {context.user_data['full_name']}\n"
        f"Телефон: {context.user_data['phone']}\n"
        f"Email: {context.user_data['email'] or '—'}\n\n"
        "✅ Всё верно?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Да, всё верно", callback_data="consent_confirm")],
        [InlineKeyboardButton("✏️ Заполнить заново", callback_data="consent_restart")]
    ]

    chat_id = context.user_data.get("form_chat_id")
    msg_id = context.user_data.get("form_message_id")

    if chat_id and msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"  # ← важно!
            )
        except:
            sent = await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data["form_message_id"] = sent.message_id
            context.user_data["form_chat_id"] = sent.chat_id
    else:
        sent = await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data["form_message_id"] = sent.message_id
        context.user_data["form_chat_id"] = sent.chat_id

    return CONFIRM


async def consent_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
        data = context.user_data

        full_name = data.get("full_name", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()
        telegram_username = data.get("telegram_username", "").strip()
        tariff = data.get("selected_tariff", "не указан")

        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, full_name, phone, email, telegram_username, tariff])

        logger.info(f"✅ Новый лид сохранён: {full_name} | {phone} | {tariff}")

        await query.edit_message_text(
            text=(
                "✅ Спасибо! Ваши данные сохранены.\n"
                f"Выбранная программа: *{tariff}*.\n"
                "С Вами скоро свяжутся."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Назад в меню", callback_data="back")]
            ]),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    except Exception as e:
        logger.exception("❌ Ошибка при сохранении лида в CSV")
        try:
            await query.edit_message_text(
                text="⚠️ Ошибка при сохранении. Попробуйте позже или свяжитесь с поддержкой."
            )
        except Exception:
            await query.message.reply_text("⚠️ Ошибка при сохранении. Попробуйте позже.")
        return ConversationHandler.END


# --- Перезапуск формы ---
async def consent_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await consent_full_name(update, context)


# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если отмена через команду — нужно найти и отредактировать или удалить
    if update.message:
        # Попробуем удалить/отредактировать предыдущее сообщение
        msg_id = context.user_data.get("start_message_id")
        if msg_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=msg_id,
                    text="❌ Форма отменена. Вы можете начать снова через меню.",
                    reply_markup=InlineKeyboardMarkup(get_back_button())
                )
            except:
                await update.message.reply_text(
                    "❌ Форма отменена. Вы можете начать снова через меню.",
                    reply_markup=InlineKeyboardMarkup(get_back_button())
                )
        else:
            await update.message.reply_text(
                "❌ Форма отменена. Вы можете начать снова через меню.",
                reply_markup=InlineKeyboardMarkup(get_back_button())
            )
    return ConversationHandler.END