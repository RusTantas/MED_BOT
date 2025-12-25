# handlers/product_details.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# --- Тексты тарифов ---
TARIFF_NEW = (
    "🔹 *Вы впервые в программе?*\n\n"
    "*Стоимость:*\n"
    "• 4 недели — 7000 ₽\n"
    "• 2 недели — 4000 ₽\n"
    "• 1 неделя — 2000 ₽\n\n"
    "*Включено:*\n"
    "✔️ Первый информационный блок «Здоровое Тело»\n"
    "✔️ Доступ к нему сохраняется после завершения\n"
    "✔️ Сопровождение в группе\n"
    "✔️ Обратная связь по дневникам питания\n"
    "✔️ Ответы на вопросы в установленное время (будни)\n"
    "✔️ Анализ опросника и индивидуальные рекомендации"
)

TARIFF_MONTH2 = (
    "🔹 *Вы продолжаете второй месяц?*\n\n"
    "*Стоимость:*\n"
    "• 4 недели — 6500 ₽\n"
    "• 2 недели — 3500 ₽\n"
    "• 1 неделя — 1800 ₽\n\n"
    "*Включено:*\n"
    "✔️ Открыт второй информационный блок\n"
    "✔️ Доступ к нему сохраняется\n"
    "✔️ Сопровождение и формат работы — как в первый месяц"
)

TARIFF_LONG = (
    "🔹 *Вы уже были в программе 2 месяца и более*\n\n"
    "*Вариант 1. Только сопровождение в группе*\n"
    "(без инфо-блоков)\n"
    "• 4 недели — 4000 ₽\n"
    "• 2 недели — 2500 ₽\n"
    "• 1 неделя — 1500 ₽\n\n"
    "*Вариант 2. Максимальный доступ + сопровождение*\n"
    "✔️ Бессрочный доступ ко всем 3 инфо-блокам\n"
    " (питание, желчь, лимфа, кишечник, холестерин — если вы ещё не в них 😊)\n"
    "✔️ Контроль рациона и ответы на вопросы\n"
    "• 4 недели — 5500 ₽\n"
    "• 2 недели — 3500 ₽\n"
    "• 1 неделя — 2000 ₽"
)

async def show_tariff_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Впервые в программе"

    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=TARIFF_NEW,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_tariff_month2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Продолжаю 2-й месяц"

    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=TARIFF_MONTH2,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_tariff_long(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["selected_tariff"] = "Уже 2+ месяца"

    keyboard = [
        [InlineKeyboardButton("📩 Оставить заявку", callback_data="consent")],
        [InlineKeyboardButton("← Назад к выбору", callback_data="product")]
    ]
    await query.edit_message_text(
        text=TARIFF_LONG,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )