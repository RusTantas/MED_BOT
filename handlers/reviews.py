from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import REVIEWS_LINKS

async def reviews_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "⭐ Отзывы пациентов:\n\n"
    for i, link in enumerate(REVIEWS_LINKS, 1):
        text += f"{i}. {link}\n"
    
    text += "\nВы можете оставить свой отзыв по этим ссылкам!❤️"
    
    keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )