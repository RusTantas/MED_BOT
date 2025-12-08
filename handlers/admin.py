# handlers/admin.py
import csv
import os
from telegram import Update
from telegram.ext import ContextTypes

CSV_PATH = "./storage/leads.csv"

async def leads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

    if user_id not in admin_ids:
        await update.message.reply_text("🔒 Доступ запрещён.")
        return

    if not os.path.exists(CSV_PATH):
        await update.message.reply_text("📭 Нет зарегистрированных пользователей.")
        return

    leads = []
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                if i > 20:  # лимит 20
                    break
                name = row.get("full_name", "").strip() or "—"
                phone = row.get("phone", "").strip() or "—"
                email = row.get("email", "").strip() or "—"
                ts = row.get("timestamp", "").split()[0] 
                user_name = row.get("telegram_username", "").strip() or "—"
                leads.append(f"{i}. {name} | 📱 {phone} | ✉️ {email} | 📅 {ts} | ⚠️{user_name}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка чтения: {e}")
        return

    if not leads:
        await update.message.reply_text("📭 Нет зарегистрированных пользователей.")
    else:
        text = "📋 Последние регистрации (до 20):\n\n" + "\n".join(leads)
        # Telegram ограничивает ~4096 символов — если много, можно разделить на части
        if len(text) > 4000:
            text = text[:4000] + "\n… (обрезано)"
        await update.message.reply_text(text)

async def count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

    if user_id not in admin_ids:
        await update.message.reply_text("🔒 Доступ запрещён.")
        return

    if not os.path.exists(CSV_PATH):
        await update.message.reply_text("📭 Нет зарегистрированных пользователей.")
        return

    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            # Пропускаем заголовок
            lines = sum(1 for line in f) - 1
            if lines < 0:
                lines = 0
        await update.message.reply_text(f"🔢 Всего зарегистрировано: **{lines}** человек.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка подсчёта: {e}")