import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import PRICES_FILE, BASE_PRICES
from logger import logger

def load_prices():
    try:
        if os.path.exists(PRICES_FILE):
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Ошибка загрузки цен: {e}")
    
    return BASE_PRICES

def format_price(price):
    """Форматирует цену с разделителем тысяч"""
    return f"{price:,}".replace(",", " ")

async def show_tariff_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Впервые в программе"
    
    # Загружаем актуальные цены
    prices = load_prices()
    new_prices = prices.get("new", BASE_PRICES["new"])
    
    text = (
        "🔹 *Вы впервые в программе?*\n\n"
        "*Стоимость:*\n"
        f"• 4 недели — {format_price(new_prices['4_weeks'])} ₽\n"
        f"• 2 недели — {format_price(new_prices['2_weeks'])} ₽\n"
        f"• 1 неделя — {format_price(new_prices['1_week'])} ₽\n\n"
        "*Включено:*\n"
        "✔️ Первый информационный блок «Здоровое Тело» - доступ к группе 1 год\n"
        "✔️ Доступ к нему сохраняется после завершения\n"
        "✔️ Сопровождение в группе\n"
        "✔️ Обратная связь по дневникам питания\n"
        "✔️ Ответы на вопросы в установленное время (будни)\n"
        "✔️ Анализ опросника и индивидуальные рекомендации\n\n"
        "Ознакомиться с документами можно "
        " [здесь ❗️](https://taplink.cc/dr_gulnaz_halimova)"
    )
    
    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_tariff_month2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Продолжаю 2-й месяц"
    
    # Загружаем актуальные цены
    prices = load_prices()
    month2_prices = prices.get("month2", BASE_PRICES["month2"])
    
    text = (
        "🔹 *Вы продолжаете второй месяц?*\n\n"
        "*Стоимость:*\n"
        f"• 4 недели — {format_price(month2_prices['4_weeks'])} ₽\n"
        f"• 2 недели — {format_price(month2_prices['2_weeks'])} ₽\n"
        f"• 1 неделя — {format_price(month2_prices['1_week'])} ₽\n\n"
        "Ознакомиться с документами можно "
        " [здесь ❗️](https://taplink.cc/dr_gulnaz_halimova)"
    )
    
    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_tariff_long(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Уже 2+ месяца"
    
    # Загружаем актуальные цены
    prices = load_prices()
    long_prices = prices.get("long", BASE_PRICES["long"])
    
    text = (
        "🔹 *Вы уже были в программе 2 месяца и более*\n\n"
        "*Вариант 1. Только сопровождение в группе*\n"
        "(без инфо-блоков)\n"
        f"• 4 недели — {format_price(long_prices['option1']['4_weeks'])} ₽\n"
        f"• 2 недели — {format_price(long_prices['option1']['2_weeks'])} ₽\n"
        f"• 1 неделя — {format_price(long_prices['option1']['1_week'])} ₽\n\n"
        "*Вариант 2. Максимальный доступ + сопровождение*\n"
        "✔️ Контроль рациона и ответы на вопросы\n"
        f"• 4 недели — {format_price(long_prices['option2']['4_weeks'])} ₽\n"
        f"• 2 недели — {format_price(long_prices['option2']['2_weeks'])} ₽\n"
        f"• 1 неделя — {format_price(long_prices['option2']['1_week'])} ₽\n\n"
        "Ознакомиться с документами можно "
        " [здесь ❗️](https://taplink.cc/dr_gulnaz_halimova)"
    )
    
    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_tariff_detox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Детокс неделя"
    # prices = load_prices()
    # detox_prices = prices.get("detox", BASE_PRICES["1_week"])

    text = (
        "🔹 *Детокс неделя*\n\n"
        f"• Стоимость 2000₽\n\n"
        "✔️ Длительность — 5 дней\n"
        "✔️ Бонусом на 2 недели — доступ к легкой теории по нашим органам детокса\n\n"
        "❗️ Только для моих пациентов или/и участников «Здорового тела».\n"
        "❗️ Только для женщин.\n\n"
        "Запись осуществляется с момента анонса в основной группе "
        "[Доктор Гульназ Халимова ❤️](https://t.me/dr_halimova_gulnaz)\n\n"
        "Ознакомиться с документами можно "
        " [здесь ❗️](https://taplink.cc/dr_gulnaz_halimova)"
    )

    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
