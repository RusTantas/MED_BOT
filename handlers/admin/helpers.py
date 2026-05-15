import os
import telegram
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger

def is_admin(user_id: int) -> bool:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str.strip():
        return False
    try:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        return user_id in admin_ids
    except (ValueError, AttributeError):
        return False

async def reply_to_update(update: Update, text: str, reply_markup=None, parse_mode=None):
    try:
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            try:
                await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except:
                if update.effective_chat:
                    try:
                        await update._bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode
                        )
                    except:
                        pass
    except telegram.error.BadRequest as e:
        logger.warning(f"Markdown parsing error, sending without formatting: {e}")
        text_without_markdown = text.replace('*', '').replace('_', '').replace('`', '')
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text_without_markdown,
                reply_markup=reply_markup,
                parse_mode=None
            )
        elif update.message:
            await update.message.reply_text(
                text_without_markdown,
                reply_markup=reply_markup,
                parse_mode=None
            )
    except Exception as e:
        logger.error(f"Error in reply_to_update: {e}")

def validate_markdown(text: str):
    if text.count('*') % 2 != 0:
        return False, "Нечётное количество символов *"
    if text.count('`') % 2 != 0:
        return False, "Нечётное количество символов `"
    if text.count('_') % 2 != 0:
        return False, "Нечётное количество символов _"
    return True, "OK"

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to_update(update, "❌ Действие отменено.")
    return ConversationHandler.END
