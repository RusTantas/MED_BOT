import os
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger
from config import DATA_DIR
from .helpers import is_admin, reply_to_update

AWAIT_GUIDE_FILE = 2

async def admin_upload_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    await reply_to_update(update,
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
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    try:
        document = update.message.document
        if not document:
            await update.message.reply_text("❌ Пожалуйста, пришлите файл (не фото/текст).")
            return AWAIT_GUIDE_FILE

        filename = document.file_name or "unnamed"
        base_name = os.path.basename(filename)
        ext = Path(base_name).suffix.lower()

        if ext not in ['.pdf', '.doc', '.docx']:
            await update.message.reply_text(
                "❌ Неподдерживаемый формат.\n"
                "Разрешены: `.pdf`, `.doc`, `.docx`"
            )
            return AWAIT_GUIDE_FILE

        if not base_name.lower().startswith('гайд о'):
            await update.message.reply_text(
                "❌ Неверное имя файла.\n"
                "Файл должен начинаться с **«Гайд о»**, например:\n"
                "`Гайд о физических упражнениях.pdf`"
            )
            return AWAIT_GUIDE_FILE

        safe_name = re.sub(r'[<>:"|?*]', '_', base_name)
        save_path = Path(DATA_DIR) / safe_name

        file = await document.get_file()
        await file.download_to_drive(save_path)

        logger.info(f"✅ Гайд загружен: {safe_name} от user_id={user_id}")
        await update.message.reply_text(
            f"✅ Гайд сохранён:\n`{safe_name}`\n\n"
            f"Путь: `./data/{safe_name}`"
        )

        return ConversationHandler.END

    except Exception as e:
        logger.exception(f"❌ Ошибка при загрузке гайда от user_id={user_id}: {e}")
        await update.message.reply_text("❌ Не удалось сохранить файл. Администратор уведомлён.")
        return ConversationHandler.END
