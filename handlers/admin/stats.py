from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from html import escape
import database
from logger import logger
from .helpers import is_admin, reply_to_update

async def admin_user_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    total_users = database.get_user_count()
    all_users = database.get_all_active_users()

    text = f"👥 *Статистика пользователей*\n\n"
    text += f"Всего активных пользователей: *{total_users}*, Гайд скачало *{total_users - 7}* \n\n"

    if total_users > 0 and all_users:
        text += "*Последние 50 пользователей:*\n"
        for i, user in enumerate(all_users[:50], 1):
            first_name = escape(str(user.get('first_name', '')))
            last_name = escape(str(user.get('last_name', '')))
            username = escape(str(user.get('username', ''))) if user.get('username') else ''
            user_id_val = str(user.get('user_id', 'N/A'))

            name = f"{first_name} {last_name}".strip()
            if not name:
                name = "Без имени"
            username_part = f" (@{username})" if username else ""

            text += f"{i}. {name}{username_part} - ID: {user_id_val}\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    parse_mode = "HTML" if total_users > 0 and all_users else "Markdown"

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode=parse_mode
    )
