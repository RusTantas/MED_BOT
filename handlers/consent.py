from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def consent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "Форма согласия на обработку персональных данных.\n\n*Здесь будет форма с полями:*\n- ФИО\n- Телефон\n- Email\n- Согласие (галочка)"
    
    keyboard = [
        [InlineKeyboardButton("Заполнить форму", callback_data="start_form")],
        [InlineKeyboardButton("← Назад в меню", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )

async def start_form_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="Начало формы... (будет реализовано позже)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="consent")]])
    )