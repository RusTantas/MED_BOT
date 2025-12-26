# handlers/admin.py
import csv
import os
import re
import json
import telegram  # Добавлен импорт
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger
from config import PRODUCT_CONTENT_FILE, PRICES_FILE, BASE_PRODUCT_TEXT, BASE_PRICES

# --- Вспомогательная функция проверки админа ---
def is_admin(user_id: int) -> bool:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str.strip():
        return False
    try:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        return user_id in admin_ids
    except (ValueError, AttributeError):
        return False

# --- Вспомогательная функция отправки сообщений ---
async def reply_to_update(update: Update, text: str, reply_markup=None, parse_mode=None):
    """Универсальная функция отправки сообщений для любого типа апдейта"""
    try:
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            # Резервный вариант
            try:
                await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except:
                # Если ничего не работает
                if update.effective_chat:
                    try:
                        await update._bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode
                        )
                    except:
                        pass
    except telegram.error.BadRequest as e:
        # Если ошибка парсинга markdown, отправляем без разметки
        logger.warning(f"Markdown parsing error, sending without formatting: {e}")
        text_without_markdown = text.replace('*', '').replace('_', '').replace('`', '')
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text_without_markdown, 
                reply_markup=reply_markup,
                parse_mode=None
            )
        elif update.message:
            await update.message.reply_text(
                text_without_markdown,
                reply_markup=reply_markup,
                parse_mode=None
            )
    except Exception as e:
        logger.error(f"Error in reply_to_update: {e}")

# --- Константы ---
CSV_PATH = "./storage/leads.csv"
DATA_DIR = "./data"  # папка для гайдов (на уровне main.py)

# Убедимся, что папка data существует
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("./storage", exist_ok=True)

# Состояния
ASK_LEADS_COUNT = 1
AWAIT_GUIDE_FILE = 2
EDIT_PRODUCT_TEXT = 3
EDIT_PRICES = 4

# --- Хендлер: /albina — админ-меню ---
async def albina_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Неизвестная команда.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Последние лиды", callback_data="admin_ask_leads")],
        [InlineKeyboardButton("🔢 Общее количество", callback_data="admin_count_now")],
        [InlineKeyboardButton("📤 Скачать CSV", callback_data="admin_export_csv")],
        [InlineKeyboardButton("📘 Загрузить гайд", callback_data="admin_upload_guide")],
        [InlineKeyboardButton("✏️ Редактировать текст программы", callback_data="admin_edit_product_text")],
        [InlineKeyboardButton("💰 Изменить цены", callback_data="admin_edit_prices")]
    ])
    await reply_to_update(update, "🔐 Админ-панель «Альбина»", reply_markup=keyboard)

# --- Редактирование текста программы ---
async def admin_edit_product_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.", parse_mode=None)
        return
    
    # Загружаем текущий текст или базовый
    current_text = BASE_PRODUCT_TEXT
    if os.path.exists(PRODUCT_CONTENT_FILE):
        try:
            with open(PRODUCT_CONTENT_FILE, 'r', encoding='utf-8') as f:
                saved_text = f.read().strip()
                if saved_text:
                    current_text = saved_text
        except:
            pass
    
    # Безопасное превью
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
        parse_mode=None  # Отключаем markdown для админ-сообщений
    )
    return EDIT_PRODUCT_TEXT

async def edit_text_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Загружаем текущий текст или базовый
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
        f"*Текущий текст (полный):*\n"
        f"`{current_text[:1000]}...`\n\n"
        "Отправьте новый текст или /cancel для отмены",
        parse_mode="Markdown"
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
    
    try:
        # Сохраняем новый текст
        with open(PRODUCT_CONTENT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_text)
        
        logger.info(f"✅ Текст программы обновлён администратором {user_id}")
        
        # Предпросмотр без markdown
        preview = new_text[:200].replace('*', '').replace('`', '').replace('_', '')
        preview = preview + "..." if len(new_text) > 200 else preview
        
        await update.message.reply_text(
            f"✅ Текст программы успешно обновлён!\n\n"
            f"*Предпросмотр:*\n"
            f"{preview}\n\n"
            f"Файл сохранён: `{PRODUCT_CONTENT_FILE}`",
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.exception(f"❌ Ошибка при сохранении текста программы: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении. Попробуйте снова.")
        return EDIT_PRODUCT_TEXT

# --- Редактирование цен ---
async def admin_edit_prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return
    
    # Загружаем текущие цены
    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                saved_prices = json.load(f)
                current_prices = saved_prices
        except:
            pass
    
    # Создаем удобное отображение для редактирования
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
    
    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def format_current_prices_for_admin(prices):
    """Форматирует цены для отображения в админке"""
    text = ""
    
    # Новые
    new = prices.get("new", BASE_PRICES["new"])
    text += "*Новички:*\n"
    text += f"4 недели: {new['4_weeks']:,} ₽\n"
    text += f"2 недели: {new['2_weeks']:,} ₽\n"
    text += f"1 неделя: {new['1_week']:,} ₽\n\n"
    
    # 2-й месяц
    month2 = prices.get("month2", BASE_PRICES["month2"])
    text += "*2-й месяц:*\n"
    text += f"4 недели: {month2['4_weeks']:,} ₽\n"
    text += f"2 недели: {month2['2_weeks']:,} ₽\n"
    text += f"1 неделя: {month2['1_week']:,} ₽\n\n"
    
    # 2+ месяца
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

async def edit_price_new_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data["editing_price_category"] = "new"
    
    # Загружаем текущие цены
    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                current_prices = json.load(f)
        except:
            pass
    
    new_prices = current_prices.get("new", BASE_PRICES["new"])
    
    await query.edit_message_text(
        "💰 *Редактирование цен для «Новички»*\n\n"
        f"Текущие цены:\n"
        f"• 4 недели: {new_prices['4_weeks']:,} ₽\n"
        f"• 2 недели: {new_prices['2_weeks']:,} ₽\n"
        f"• 1 неделя: {new_prices['1_week']:,} ₽\n\n"
        "📝 Отправьте новые цены в формате:\n"
        "`4_недели=7000 2_недели=4000 1_неделя=2000`\n\n"
        "Пример: `4_недели=7500 2_недели=4200 1_неделя=2100`\n"
        "Отмена: /cancel",
        parse_mode="Markdown"
    )
    return EDIT_PRICES

async def edit_price_month2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data["editing_price_category"] = "month2"
    
    # Загружаем текущие цены
    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                current_prices = json.load(f)
        except:
            pass
    
    month2_prices = current_prices.get("month2", BASE_PRICES["month2"])
    
    await query.edit_message_text(
        "💰 *Редактирование цен для «2-й месяц»*\n\n"
        f"Текущие цены:\n"
        f"• 4 недели: {month2_prices['4_weeks']:,} ₽\n"
        f"• 2 недели: {month2_prices['2_weeks']:,} ₽\n"
        f"• 1 неделя: {month2_prices['1_week']:,} ₽\n\n"
        "📝 Отправьте новые цены в формате:\n"
        "`4_недели=6500 2_недели=3500 1_неделя=1800`\n\n"
        "Пример: `4_недели=6800 2_недели=3700 1_неделя=1900`\n"
        "Отмена: /cancel",
        parse_mode="Markdown"
    )
    return EDIT_PRICES

async def edit_price_long1_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data["editing_price_category"] = "long_option1"
    
    # Загружаем текущие цены
    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                current_prices = json.load(f)
        except:
            pass
    
    long_prices = current_prices.get("long", BASE_PRICES["long"])
    
    await query.edit_message_text(
        "💰 *Редактирование цен для «2+ месяца (вариант 1)»*\n\n"
        f"Текущие цены:\n"
        f"• 4 недели: {long_prices['option1']['4_weeks']:,} ₽\n"
        f"• 2 недели: {long_prices['option1']['2_weeks']:,} ₽\n"
        f"• 1 неделя: {long_prices['option1']['1_week']:,} ₽\n\n"
        "📝 Отправьте новые цены в формате:\n"
        "`4_недели=4000 2_недели=2500 1_неделя=1500`\n\n"
        "Пример: `4_недели=4200 2_недели=2600 1_неделя=1600`\n"
        "Отмена: /cancel",
        parse_mode="Markdown"
    )
    return EDIT_PRICES

async def edit_price_long2_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data["editing_price_category"] = "long_option2"
    
    # Загружаем текущие цены
    current_prices = BASE_PRICES
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                current_prices = json.load(f)
        except:
            pass
    
    long_prices = current_prices.get("long", BASE_PRICES["long"])
    
    await query.edit_message_text(
        "💰 *Редактирование цен для «2+ месяца (вариант 2)»*\n\n"
        f"Текущие цены:\n"
        f"• 4 недели: {long_prices['option2']['4_weeks']:,} ₽\n"
        f"• 2 недели: {long_prices['option2']['2_weeks']:,} ₽\n"
        f"• 1 неделя: {long_prices['option2']['1_week']:,} ₽\n\n"
        "📝 Отправьте новые цены в формате:\n"
        "`4_недели=5500 2_недели=3500 1_неделя=2000`\n\n"
        "Пример: `4_недели=5800 2_недели=3700 1_неделя=2100`\n"
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
    
    # Парсим цены
    try:
        prices = {}
        for item in price_text.split():
            if '=' in item:
                key, value = item.split('=')
                # Преобразуем ключ к формату JSON
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
        
        # Проверяем, что все три цены заданы
        if not all(k in prices for k in ["4_weeks", "2_weeks", "1_week"]):
            await update.message.reply_text("❌ Необходимо указать все три цены: 4_недели, 2_недели, 1_неделя")
            return EDIT_PRICES
        
        # Загружаем текущие цены
        current_prices = BASE_PRICES
        if os.path.exists(PRICES_FILE):
            try:
                with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                    current_prices = json.load(f)
            except:
                pass
        
        # Обновляем нужную категорию
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
        
        # Сохраняем обновленные цены
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

def validate_markdown(text: str):
    """Проверяет корректность markdown разметки"""
    if text.count('*') % 2 != 0:
        return False, "Нечётное количество символов *"
    if text.count('`') % 2 != 0:
        return False, "Нечётное количество символов `"
    if text.count('_') % 2 != 0:
        return False, "Нечётное количество символов _"
    return True, "OK"

async def process_product_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    new_text = update.message.text.strip()
    
    if not new_text:
        await update.message.reply_text("❌ Текст не может быть пустым.")
        return EDIT_PRODUCT_TEXT
    
    # Проверяем markdown
    is_valid, message = validate_markdown(new_text)
    if not is_valid:
        await update.message.reply_text(
            f"❌ Ошибка в markdown-разметке: {message}\n"
            f"Исправьте ошибку и отправьте текст снова."
        )
        return EDIT_PRODUCT_TEXT
    
    try:
        # Сохраняем новый текст
        with open(PRODUCT_CONTENT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_text)
        
        logger.info(f"✅ Текст программы обновлён администратором {user_id}")
        
        # Создаем безопасное превью без markdown
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


async def edit_text_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Загружаем текущий текст или базовый
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

async def back_to_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await albina_handler(update, context)

# --- Хендлер: нажали "Последние лиды" → бот просит ввести число ---
async def admin_ask_leads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    await reply_to_update(update, "🔢 Сколько последних лидов вывести? (от 1 до 100)")
    return ASK_LEADS_COUNT


async def process_leads_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        n = int(text)
        if n < 1:
            await reply_to_update(update, "❌ Число должно быть ≥ 1. Попробуйте снова:")
            return ASK_LEADS_COUNT
        if n > 100:
            await reply_to_update(update, "⚠️ Максимум — 100 записей. Использую 100.")
            n = 100
    except ValueError:
        await reply_to_update(update, "❌ Введите целое число. Например: `20`")
        return ASK_LEADS_COUNT

    if not os.path.exists(CSV_PATH):
        await reply_to_update(update, "📭 Файл leads.csv не найден.")
        return ConversationHandler.END

    leads = []
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                await reply_to_update(update, "📭 Нет зарегистрированных пользователей.")
                return ConversationHandler.END

            last_n = rows[-n:]
            for i, row in enumerate(reversed(last_n), 1):
                name = row.get("full_name", "").strip() or "—"
                phone = row.get("phone", "").strip() or "—"
                email = row.get("email", "").strip() or "—"
                tarif = row.get("tariff", "").strip() or "—"
                ts_full = row.get("timestamp", "")
                ts = ts_full.split()[0] if ts_full.strip() else "—"
                user_name = row.get("telegram_username", "").strip() or "—"
                if user_name != "—":
                    user_name = "@" + user_name
                leads.append(f"{i}. {name} | 📱 {phone} | ✉️ {email} |  📋 {tarif} | 📅 {ts} | {user_name}")

    except Exception as e:
        await reply_to_update(update, f"⚠️ Ошибка чтения CSV: {e}")
        return ConversationHandler.END

    if not leads:
        await reply_to_update(update, "📭 Нет данных.")
    else:
        header = f"📋 Последние {len(leads)} лидов:\n\n"
        text = header + "\n".join(leads)
        max_len = 4000
        for i in range(0, len(text), max_len):
            await reply_to_update(update, text[i:i + max_len])

    return ConversationHandler.END


# --- Хендлер: общее количество ---
async def count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("🔒 Доступ запрещён.")
        elif update.callback_query:
            await update.callback_query.answer("🔒 Доступ запрещён.", show_alert=True)
        return

    if not os.path.exists(CSV_PATH):
        reply_text = "📭 Нет зарегистрированных пользователей."
    else:
        try:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                total = sum(1 for _ in f) - 1
                if total < 0:
                    total = 0
            reply_text = f"🔢 Всего зарегистрировано: **{total}** человек."
        except Exception as e:
            reply_text = f"⚠️ Ошибка подсчёта: {e}"

    # Используем универсальную функцию
    await reply_to_update(update, reply_text, parse_mode="Markdown")


async def admin_count_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await count_handler(update, context)


# --- Скачать CSV ---
async def admin_export_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    if not os.path.exists(CSV_PATH):
        await reply_to_update(update, "📭 Файл leads.csv не найден.")
        return

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"leads_{today}.csv"
        with open(CSV_PATH, "rb") as f:
            # Для документов нужно использовать оригинальный message
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_document(
                    document=InputFile(f, filename=filename),
                    caption=f"📄 Выгрузка от {today}"
                )
            elif update.message:
                await update.message.reply_document(
                    document=InputFile(f, filename=filename),
                    caption=f"📄 Выгрузка от {today}"
                )
    except Exception as e:
        await reply_to_update(update, f"❌ Ошибка отправки файла: {e}")


# --- НОВОЕ: Загрузка гайда ---
async def admin_upload_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    await reply_to_update(update,
        "📘 Пришлите файл гайда.\n\n"
        "✅ Требования:\n"
        "— Формат: `.pdf` \n"
        "— Имя файла должно начинаться с **«Гайд о»**, например:\n"
        "`Гайд о здоровом питании.pdf`\n\n"
        "Отмена: отправьте /cancel"
    )
    return AWAIT_GUIDE_FILE


async def receive_guide_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    try:
        document = update.message.document
        if not document:
            await update.message.reply_text("❌ Пожалуйста, пришлите файл (не фото/текст).")
            return AWAIT_GUIDE_FILE

        # Получаем имя и расширение
        filename = document.file_name or "unnamed"
        base_name = os.path.basename(filename)
        ext = Path(base_name).suffix.lower()

        # Поддерживаемые форматы (как в config.ALLOWED_EXTENSIONS, но без изображений)
        if ext not in ['.pdf', '.doc', '.docx']:
            await update.message.reply_text(
                "❌ Неподдерживаемый формат.\n"
                "Разрешены: `.pdf`, `.doc`, `.docx`"
            )
            return AWAIT_GUIDE_FILE

        # Проверка: имя файла должно начинаться с «Гайд о» (регистронезависимо)
        if not base_name.lower().startswith('гайд о'):
            await update.message.reply_text(
                "❌ Неверное имя файла.\n"
                "Файл должен начинаться с **«Гайд о»**, например:\n"
                "`Гайд о физических упражнениях.pdf`"
            )
            return AWAIT_GUIDE_FILE

        # Безопасное имя (убираем потенциально опасные символы)
        safe_name = re.sub(r'[<>:"|?*]', '_', base_name)
        save_path = Path(DATA_DIR) / safe_name

        # Скачивание
        file = await document.get_file()
        await file.download_to_drive(save_path)

        logger.info(f"✅ Гайд загружен: {safe_name} от user_id={user_id}")
        await update.message.reply_text(
            f"✅ Гайд сохранён:\n`{safe_name}`\n\n"
            f"Путь: `./data/{safe_name}`"
        )

        return ConversationHandler.END

    except Exception as e:
        logger.exception(f"❌ Ошибка при загрузке гайда от user_id={user_id}: {e}")
        await update.message.reply_text("❌ Не удалось сохранить файл. Администратор уведомлён.")
        return ConversationHandler.END



# Для отмены в любой момент
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to_update(update, "❌ Действие отменено.")
    return ConversationHandler.END