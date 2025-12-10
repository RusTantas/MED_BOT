import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

CHANNEL_ID = "@dr_halimova_gulnaz"
DATA_DIR = Path("data")

async def guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_subscribed = await check_subscription(context.bot, user_id)
    
    if not is_subscribed:
        text = "📢 Чтобы получить доступ к гайдам, подпишитесь на канал!"
        
        keyboard = [
            [InlineKeyboardButton("✅ Подписаться на канал", url=f"https://t.me/dr_halimova_gulnaz")],
            [InlineKeyboardButton("🔍 Проверить подписку", callback_data="check_subscription")],
            [InlineKeyboardButton("← Назад в меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception:
            pass
        return
    
    await show_guides_list(update, context)

async def show_guides_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        edit_message = True
    else:
        chat_id = update.message.chat_id
        message_id = None
        edit_message = False
    
    guides = get_available_guides()
    
    if not guides:
        text = "📭 Гайды временно отсутствуют. Загляните позже!"
        keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
    else:
        text = "📚 *Доступные гайды:*\n\n"
        keyboard = []
        
        for i, guide in enumerate(guides, 1):
            text += f"{i}. {guide['name']}\n"
            callback_data = f"download_{guide['filename']}"
            keyboard.append([InlineKeyboardButton(f"📥 {guide['name']}", callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("← Назад в меню", callback_data="back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message and message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def download_guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    filename = query.data.replace("download_", "")
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        await query.answer("❌ Файл не найден!", show_alert=True)
        return
    
    try:
        with open(filepath, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                filename=filename,
                caption="✅ Вот ваш гайд! Приятного изучения."
            )
        
        await query.answer("✅ Гайд отправлен! Проверьте сообщения.", show_alert=False)
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)[:50]}...", show_alert=True)

async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_subscribed = await check_subscription(context.bot, user_id)
    
    if not is_subscribed:
        await query.answer(
            "❌ Вы не подписаны на канал! Подпишитесь и попробуйте снова.",
            show_alert=True
        )
        return
    
    await show_guides_list(update, context)

async def check_subscription(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        
        subscribed_statuses = ['member', 'administrator', 'creator']
        return member.status in subscribed_statuses
        
    except Exception:
        return False

def get_available_guides():
    guides = []
    
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return guides
    
    allowed_extensions = ['.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    
    for file in DATA_DIR.iterdir():
        if file.is_file() and file.suffix.lower() in allowed_extensions:
            guides.append({
                'filename': file.name,
                'name': file.stem,
                'path': file,
                'size': file.stat().st_size
            })
    
    return sorted(guides, key=lambda x: x['name'])