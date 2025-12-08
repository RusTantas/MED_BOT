from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "Чтобы получить гайд, необходимо подписаться на наш Telegram-канал.\n\nПосле подписки вы сможете скачать полезный материал."
    
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url="https://t.me/your_channel")],
        [InlineKeyboardButton("Проверить подписку", callback_data="check_subscription")],
        [InlineKeyboardButton("← Назад в меню", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )

async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="Проверка подписки... (будет реализовано позже)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="guide")]])
    )