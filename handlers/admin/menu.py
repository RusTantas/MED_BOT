from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from .helpers import is_admin, reply_to_update

async def albina_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Неизвестная команда.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Последние лиды", callback_data="admin_ask_leads")],
        [InlineKeyboardButton("🔢 Общее количество", callback_data="admin_count_now")],
        [InlineKeyboardButton("👥 Пользователи бота", callback_data="admin_user_stats")],
        [InlineKeyboardButton("📤 Скачать CSV", callback_data="admin_export_csv")],
        [InlineKeyboardButton("📘 Загрузить гайд", callback_data="admin_upload_guide")],
        [InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📋 История рассылок", callback_data="admin_broadcast_history")],
        [InlineKeyboardButton("✏️ Редактировать текст программы", callback_data="admin_edit_product_text")],
        [InlineKeyboardButton("💰 Изменить цены", callback_data="admin_edit_prices")]
    ])
    await reply_to_update(update, "🔐 Админ-панель «Альбина»", reply_markup=keyboard)

async def back_to_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await albina_handler(update, context)
