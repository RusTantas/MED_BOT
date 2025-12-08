from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BACK_BUTTON_TEXT

def get_main_keyboard():
    """Клавиатура мейн меню"""
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Об авторе", callback_data="about")],
        [InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")],
        [InlineKeyboardButton("📦 О продукте", callback_data="product")],
        [InlineKeyboardButton("📅 Запись на консультацию", callback_data="booking")],
        [InlineKeyboardButton("📝 Согласие на обработку данных", callback_data="consent")],
        [InlineKeyboardButton("📥 Скачать гайд", callback_data="guide")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """с кнопкой 'назад' """
    keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)