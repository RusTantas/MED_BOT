import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger
from config import PRODUCT_CONTENT_FILE, PRICES_FILE, BASE_PRODUCT_TEXT, BASE_PRICES
from .helpers import is_admin, reply_to_update, validate_markdown

EDIT_PRODUCT_TEXT = 3
EDIT_PRICES = 4

async def admin_edit_product_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.", parse_mode=None)
        return

    current_text = BASE_PRODUCT_TEXT
    if os.path.exists(PRODUCT_CONTENT_FILE):
        try:
            with open(PRODUCT_CONTENT_FILE, 'r', encoding='utf-8') as f:
                saved_text = f.read().strip()
                if saved_text:
                    current_text = saved_text
        except:
            pass

    preview_text = current_text[:500] + "..." if len(current_text) > 500 else current_text

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Редактировать текст", callback_data="edit_text_confirm")],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    await reply_to_update(update,
        "✏️ РЕДАКТИРОВАНИЕ ТЕКСТА ПРОГРАММЫ «Здоровое Тело»\n\n"
        "Текущий текст (первые 500 символов):\n\n"
        f"{preview_text}\n\n"
        "ФОРМАТИРОВАНИЕ:\n"
        "• Используйте *жирный текст* с *\n"
        "• Используйте `код` с `\n"
        "• Разделяйте абзацы пустой строкой\n\n"
        "ВАЖНО: Убедитесь, что все markdown-теги закрыты!\n\n"
        "Нажмите кнопку ниже, чтобы начать редактирование:",
        reply_markup=keyboard,
        parse_mode=None
    )
    return EDIT_PRODUCT_TEXT

async def edit_text_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_text = BASE_PRODUCT_TEXT
    if os.path.exists(PRODUCT_CONTENT_FILE):
        try:
            with open(PRODUCT_CONTENT_FILE, 'r', encoding='utf-8') as f:
                saved_text = f.read().strip()
                if saved_text:
                    current_text = saved_text
        except:
            pass

    await query.edit_message_text(
        f"📝 Отправьте новый текст программы:\n\n"
        f"Текущий текст (первые 1000 символов):\n\n"
        f"`{current_text[:1000]}...`\n\n"
        "Отправьте новый текст или /cancel для отмены",
        parse_mode=None
    )
    return EDIT_PRODUCT_TEXT

async def process_product_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    new_text = update.message.text.strip()

    if not new_text:
        await update.message.reply_text("❌ Текст не может быть пустым.")
        return EDIT_PRODUCT_TEXT

    is_valid, message = validate_markdown(new_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ Ошибка в markdown-разметке: {message}\n"
            f"Исправьте ошибку и отправьте текст снова."
        )
        return EDIT_PRODUCT_TEXT

    try:
        with open(PRODUCT_CONTENT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_text)

        logger.info(f"✅ Текст программы обновлён администратором {user_id}")

        preview = new_text[:200].replace('*', '').replace('`', '').replace('_', '')
        preview = preview + "..." if len(new_text) > 200 else preview

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
        ])

        await update.message.reply_text(
            f"✅ Текст программы успешно обновлён!\n\n"
            f"*Превью:*\n"
            f"{preview}\n\n"
            f"Файл сохранён: `{PRODUCT_CONTENT_FILE}`\n"
            f"Размер: {len(new_text)} символов",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        return ConversationHandler.END

    except Exception as e:
        logger.exception(f"❌ Ошибка при сохранении текста программы: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении. Попробуйте снова.")
        return EDIT_PRODUCT_TEXT

def format_current_prices_for_admin(prices):
    text = ""

    new = prices.get("new", BASE_PRICES["new"])
    text += "*Новички:*\n"
    text += f"4 недели: {new['4_weeks']:,} ₽\n"
    text += f"2 недели: {new['2_weeks']:,} ₽\n"
    text += f"1 неделя: {new['1_week']:,} ₽\n\n"

    month2 = prices.get("month2", BASE_PRICES["month2"])
    text += "*2-й месяц:*\n"
    text += f"4 недели: {month2['4_weeks']:,} ₽\n"
    text += f"2 недели: {month2['2_weeks']:,} ₽\n"
    text += f"1 неделя: {month2['1_week']:,} ₽\n\n"

    long = prices.get("long", BASE_PRICES["long"])
    text += "*2+ месяца (вариант 1):*\n"
    text += f"4 недели: {long['option1']['4_weeks']:,} ₽\n"
    text += f"2 недели: {long['option1']['2_weeks']:,} ₽\n"
    text += f"1 неделя: {long['option1']['1_week']:,} ₽\n\n"

    text += "*2+ месяца (вариант 2):*\n"
    text += f"4 недели: {long['option2']['4_weeks']:,} ₽\n"
    text += f"2 недели: {long['option2']['2_weeks']:,} ₽\n"
    text += f"1 неделя: {long['option2']['1_week']:,} ₽\n"

    return text

async def admin_edit_prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                saved_prices = json.load(f)
                current_prices = saved_prices
        except:
            pass

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Новички", callback_data="edit_price_new"),
            InlineKeyboardButton("2-й месяц", callback_data="edit_price_month2")
        ],
        [
            InlineKeyboardButton("2+ месяца (вариант 1)", callback_data="edit_price_long1"),
            InlineKeyboardButton("2+ месяца (вариант 2)", callback_data="edit_price_long2")
        ],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    text = "💰 *Редактирование цен*\n\nВыберите категорию для редактирования:\n\n"
    text += format_current_prices_for_admin(current_prices)

    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")

async def edit_price_new_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _edit_price_category(update, context, "new", "Новички")

async def edit_price_month2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _edit_price_category(update, context, "month2", "2-й месяц")

async def edit_price_long1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _edit_price_category(update, context, "long_option1", "2+ месяца (вариант 1)")

async def edit_price_long2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _edit_price_category(update, context, "long_option2", "2+ месяца (вариант 2)")

async def _edit_price_category(update, context, category_key, category_name):
    query = update.callback_query
    await query.answer()
    context.user_data["editing_price_category"] = category_key

    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                current_prices = json.load(f)
        except:
            pass

    if category_key == "new":
        prices = current_prices.get("new", BASE_PRICES["new"])
    elif category_key == "month2":
        prices = current_prices.get("month2", BASE_PRICES["month2"])
    elif category_key == "long_option1":
        prices = current_prices.get("long", BASE_PRICES["long"])["option1"]
    elif category_key == "long_option2":
        prices = current_prices.get("long", BASE_PRICES["long"])["option2"]

    await query.edit_message_text(
        f"💰 *Редактирование цен для «{category_name}»*\n\n"
        f"Текущие цены:\n"
        f"• 4 недели: {prices['4_weeks']:,} ₽\n"
        f"• 2 недели: {prices['2_weeks']:,} ₽\n"
        f"• 1 неделя: {prices['1_week']:,} ₽\n\n"
        "📝 Отправьте новые цены в формате:\n"
        "`4_недели=7000 2_недели=4000 1_неделя=2000`\n\n"
        "Отмена: /cancel",
        parse_mode="Markdown"
    )
    return EDIT_PRICES

async def process_price_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    price_text = update.message.text.strip()
    category = context.user_data.get("editing_price_category")

    if not category:
        await update.message.reply_text("❌ Ошибка: категория не определена.")
        return ConversationHandler.END

    try:
        prices = {}
        for item in price_text.split():
            if '=' in item:
                key, value = item.split('=')
                if key == "4_недели":
                    json_key = "4_weeks"
                elif key == "2_недели":
                    json_key = "2_weeks"
                elif key == "1_неделя":
                    json_key = "1_week"
                else:
                    await update.message.reply_text(f"❌ Неизвестный ключ: {key}")
                    return EDIT_PRICES

                try:
                    prices[json_key] = int(value)
                except ValueError:
                    await update.message.reply_text(f"❌ Некорректное значение для {key}: {value}")
                    return EDIT_PRICES

        if not all(k in prices for k in ["4_weeks", "2_weeks", "1_week"]):
            await update.message.reply_text("❌ Необходимо указать все три цены: 4_недели, 2_недели, 1_неделя")
            return EDIT_PRICES

        current_prices = BASE_PRICES
        if os.path.exists(PRICES_FILE):
            try:
                with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                    current_prices = json.load(f)
            except:
                pass

        if category == "new":
            current_prices["new"] = prices
        elif category == "month2":
            current_prices["month2"] = prices
        elif category == "long_option1":
            if "long" not in current_prices:
                current_prices["long"] = {"option1": {}, "option2": {}}
            current_prices["long"]["option1"] = prices
        elif category == "long_option2":
            if "long" not in current_prices:
                current_prices["long"] = {"option1": {}, "option2": {}}
            current_prices["long"]["option2"] = prices

        with open(PRICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_prices, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Цены обновлены администратором {user_id}, категория: {category}")

        await update.message.reply_text(
            f"✅ Цены успешно обновлены!\n\n"
            f"Новые значения:\n"
            f"• 4 недели: {prices['4_weeks']:,} ₽\n"
            f"• 2 недели: {prices['2_weeks']:,} ₽\n"
            f"• 1 неделя: {prices['1_week']:,} ₽\n\n"
            "Изменения вступят в силу сразу.",
            parse_mode="Markdown"
        )

        return ConversationHandler.END

    except Exception as e:
        logger.exception(f"❌ Ошибка при обновлении цен: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке цен. Проверьте формат и попробуйте снова.\n"
            "Правильный формат: `4_недели=7000 2_недели=4000 1_неделя=2000`"
        )
        return EDIT_PRICES
