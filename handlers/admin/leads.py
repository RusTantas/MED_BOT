import csv
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger
from config import LEADS_CSV, STORAGE_DIR
from .helpers import is_admin, reply_to_update

ASK_LEADS_COUNT = 1

os.makedirs(STORAGE_DIR, exist_ok=True)

async def admin_ask_leads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    await reply_to_update(update, "🔢 Сколько последних лидов вывести? (от 1 до 100)")
    return ASK_LEADS_COUNT

async def process_leads_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        n = int(text)
        if n < 1:
            await reply_to_update(update, "❌ Число должно быть ≥ 1. Попробуйте снова:")
            return ASK_LEADS_COUNT
        if n > 100:
            await reply_to_update(update, "⚠️ Максимум — 100 записей. Использую 100.")
            n = 100
    except ValueError:
        await reply_to_update(update, "❌ Введите целое число. Например: `20`")
        return ASK_LEADS_COUNT

    if not os.path.exists(LEADS_CSV):
        await reply_to_update(update, "📭 Файл leads.csv не найден.")
        return ConversationHandler.END

    leads = []
    try:
        with open(LEADS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                await reply_to_update(update, "📭 Нет зарегистрированных пользователей.")
                return ConversationHandler.END

            last_n = rows[-n:]
            for i, row in enumerate(reversed(last_n), 1):
                name = row.get("full_name", "").strip() or "—"
                phone = row.get("phone", "").strip() or "—"
                email = row.get("email", "").strip() or "—"
                tarif = row.get("tariff", "").strip() or "—"
                ts_full = row.get("timestamp", "")
                ts = ts_full.split()[0] if ts_full.strip() else "—"
                user_name = row.get("telegram_username", "").strip() or "—"
                if user_name != "—":
                    user_name = "@" + user_name
                leads.append(f"{i}. {name} | 📱 {phone} | ✉️ {email} |  📋 {tarif} | 📅 {ts} | {user_name}")

    except Exception as e:
        await reply_to_update(update, f"⚠️ Ошибка чтения CSV: {e}")
        return ConversationHandler.END

    if not leads:
        await reply_to_update(update, "📭 Нет данных.")
    else:
        header = f"📋 Последние {len(leads)} лидов:\n\n"
        text = header + "\n".join(leads)
        max_len = 4000
        for i in range(0, len(text), max_len):
            await reply_to_update(update, text[i:i + max_len])

    return ConversationHandler.END

async def count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("🔒 Доступ запрещён.")
        elif update.callback_query:
            await update.callback_query.answer("🔒 Доступ запрещён.", show_alert=True)
        return

    if not os.path.exists(LEADS_CSV):
        reply_text = "📭 Нет зарегистрированных пользователей."
    else:
        try:
            with open(LEADS_CSV, "r", encoding="utf-8") as f:
                total = sum(1 for _ in f) - 1
                if total < 0:
                    total = 0
            reply_text = f"🔢 Всего зарегистрировано: **{total}** человек."
        except Exception as e:
            reply_text = f"⚠️ Ошибка подсчёта: {e}"

    await reply_to_update(update, reply_text, parse_mode="Markdown")

async def admin_count_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await count_handler(update, context)

async def admin_export_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    if not os.path.exists(LEADS_CSV):
        await reply_to_update(update, "📭 Файл leads.csv не найден.")
        return

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"leads_{today}.csv"
        with open(LEADS_CSV, "rb") as f:
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_document(
                    document=InputFile(f, filename=filename),
                    caption=f"📄 Выгрузка от {today}"
                )
            elif update.message:
                await update.message.reply_document(
                    document=InputFile(f, filename=filename),
                    caption=f"📄 Выгрузка от {today}"
                )
    except Exception as e:
        await reply_to_update(update, f"❌ Ошибка отправки файла: {e}")
