# handlers/admin.py
import csv
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes, ConversationHandler

# --- Вспомогательная функция проверки админа ---
def is_admin(user_id: int) -> bool:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str.strip():
        return False
    try:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        return user_id in admin_ids
    except (ValueError, AttributeError):
        return False

# --- Константы ---
CSV_PATH = "./storage/leads.csv"
DATA_DIR = "./data"  # папка для гайдов (на уровне main.py)

# Убедимся, что папка data существует
os.makedirs(DATA_DIR, exist_ok=True)

# Состояния
ASK_LEADS_COUNT = 1
AWAIT_GUIDE_FILE = 2


# --- Хендлер: /albina — админ-меню ---
async def albina_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🔒 Неизвестная команда.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Последние лиды", callback_data="admin_ask_leads")],
        [InlineKeyboardButton("🔢 Общее количество", callback_data="admin_count_now")],
        [InlineKeyboardButton("📤 Скачать CSV", callback_data="admin_export_csv")],
        [InlineKeyboardButton("📘 Загрузить гайд", callback_data="admin_upload_guide")]
    ])
    await update.message.reply_text("🔐 Админ-панель «Альбина»", reply_markup=keyboard)


# --- Хендлер: нажали "Последние лиды" → бот просит ввести число ---
async def admin_ask_leads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await query.message.reply_text("🔒 Доступ запрещён.")
        return

    await query.message.reply_text(
        "🔢 Сколько последних лидов вывести? (от 1 до 100)"
    )
    return ASK_LEADS_COUNT


async def process_leads_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🔒 Доступ запрещён.")
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        n = int(text)
        if n < 1:
            await update.message.reply_text("❌ Число должно быть ≥ 1. Попробуйте снова:")
            return ASK_LEADS_COUNT
        if n > 100:
            await update.message.reply_text("⚠️ Максимум — 100 записей. Использую 100.")
            n = 100
    except ValueError:
        await update.message.reply_text("❌ Введите целое число. Например: `20`")
        return ASK_LEADS_COUNT

    if not os.path.exists(CSV_PATH):
        await update.message.reply_text("📭 Файл leads.csv не найден.")
        return ConversationHandler.END

    leads = []
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                await update.message.reply_text("📭 Нет зарегистрированных пользователей.")
                return ConversationHandler.END

            last_n = rows[-n:]
            for i, row in enumerate(reversed(last_n), 1):
                name = row.get("full_name", "").strip() or "—"
                phone = row.get("phone", "").strip() or "—"
                email = row.get("email", "").strip() or "—"
                ts_full = row.get("timestamp", "")
                ts = ts_full.split()[0] if ts_full.strip() else "—"
                user_name = row.get("telegram_username", "").strip() or "—"
                if user_name != "—":
                    user_name = "@" + user_name
                leads.append(f"{i}. {name} | 📱 {phone} | ✉️ {email} | 📅 {ts} | {user_name}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка чтения CSV: {e}")
        return ConversationHandler.END

    if not leads:
        await update.message.reply_text("📭 Нет данных.")
    else:
        header = f"📋 Последние {len(leads)} лидов:\n\n"
        text = header + "\n".join(leads)
        max_len = 4000
        for i in range(0, len(text), max_len):
            await update.message.reply_text(text[i:i + max_len])

    return ConversationHandler.END


# --- Хендлер: общее количество ---
async def count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("🔒 Доступ запрещён.")
        elif update.callback_query:
            await update.callback_query.answer("🔒 Доступ запрещён.", show_alert=True)
        return

    if not os.path.exists(CSV_PATH):
        reply_text = "📭 Нет зарегистрированных пользователей."
    else:
        try:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                total = sum(1 for _ in f) - 1
                if total < 0:
                    total = 0
            reply_text = f"🔢 Всего зарегистрировано: **{total}** человек."
        except Exception as e:
            reply_text = f"⚠️ Ошибка подсчёта: {e}"

    target = update.message or update.callback_query.message
    await target.reply_text(reply_text, parse_mode="Markdown")


async def admin_count_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await count_handler(update, context)


# --- Скачать CSV ---
async def admin_export_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await query.message.reply_text("🔒 Доступ запрещён.")
        return

    if not os.path.exists(CSV_PATH):
        await query.message.reply_text("📭 Файл leads.csv не найден.")
        return

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"leads_{today}.csv"
        with open(CSV_PATH, "rb") as f:
            await query.message.reply_document(
                document=InputFile(f, filename=filename),
                caption=f"📄 Выгрузка от {today}"
            )
    except Exception as e:
        await query.message.reply_text(f"❌ Ошибка отправки файла: {e}")


# --- НОВОЕ: Загрузка гайда ---
async def admin_upload_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await query.message.reply_text("🔒 Доступ запрещён.")
        return

    await query.message.reply_text(
        "📘 Пришлите файл гайда.\n\n"
        "✅ Требования:\n"
        "— Формат: `.pdf` \n"
        "— Имя файла должно начинаться с **«Гайд о»**, например:\n"
        "`Гайд о здоровом питании.pdf`\n\n"
        "Отмена: отправьте /cancel"
    )
    return AWAIT_GUIDE_FILE


async def receive_guide_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🔒 Доступ запрещён.")
        return ConversationHandler.END

    # Проверяем, есть ли документ
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ Пожалуйста, пришлите файл (не фото/текст).")
        return AWAIT_GUIDE_FILE

    # Проверяем расширение
    filename = document.file_name or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.doc', '.docx']:
        await update.message.reply_text(
            "❌ Неподдерживаемый формат.\n"
            "Разрешены: `.pdf`"
        )
        return AWAIT_GUIDE_FILE

    # Проверяем имя: должно содержать "Гайд о"
    if not re.search(r'Гайд\s+о\s', filename, re.IGNORECASE):
        await update.message.reply_text(
            "❌ Неверное имя файла.\n"
            "Файл должен содержать **«Гайд о»**, например:\n"
            "`Гайд о физических упражнениях.docx`"
        )
        return AWAIT_GUIDE_FILE

    # Скачиваем и сохраняем
    try:
        file = await document.get_file()
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        save_path = os.path.join(DATA_DIR, safe_filename)

        # Сохраняем
        await file.download_to_drive(save_path)

        await update.message.reply_text(
            f"✅ Гайд сохранён:\n`{safe_filename}`\n\n"
            f"Путь: `./data/{safe_filename}`"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        return AWAIT_GUIDE_FILE

    return ConversationHandler.END


# Для отмены в любой момент
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END