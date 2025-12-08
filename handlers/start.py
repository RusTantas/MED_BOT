# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import AUTHOR_NAME

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Добро пожаловать! Это бот {AUTHOR_NAME}. Здесь вы можете узнать обо мне, моих услугах, записаться на консультацию и получить полезные материалы."
    
    keyboard = [
        [InlineKeyboardButton("Об авторе", callback_data="about")],
        [InlineKeyboardButton("Отзывы", callback_data="reviews")],
        [InlineKeyboardButton("О продукте", callback_data="product")],
        [InlineKeyboardButton("Запись на консультацию", callback_data="booking")],
        [InlineKeyboardButton("Согласие на обработку ПД", callback_data="consent")],
        [InlineKeyboardButton("Скачать гайд", callback_data="guide")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)