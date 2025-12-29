import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from logger import logger

CHANNEL_ID = "@dr_halimova_gulnaz"  # 
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
    logger.info(f"show_guides_list called")
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()  
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        edit_message = True
        current_message = query.message
    else:
        chat_id = update.message.chat_id
        message_id = None
        edit_message = False
        current_message = None
    
    guides = get_available_guides()
    
    if not guides:
        text = "📭 Гайды временно отсутствуют. Загляните позже!"
        keyboard = [[InlineKeyboardButton("← Назад в меню", callback_data="back")]]
    else:
        text = "📚 *Доступные гайды:*\n\n"
        keyboard = []
        
        # Сохраняем guides в context для доступа в download_guide_handler
        context.user_data['guides'] = guides
        
        for i, guide in enumerate(guides, 1):
            text += f"{i}. {guide['name']}\n"
            callback_data = f"dl:{i-1}"
            keyboard.append([InlineKeyboardButton(f"📥 {guide['name']}", callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("← Назад в меню", callback_data="back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # ИСПРАВЛЕНО: Проверяем, нужно ли редактировать сообщение
    should_edit = False
    if edit_message and message_id and current_message:
        current_text = current_message.text or ""
        # Если контент отличается, редактируем
        if current_text[:100] != text[:100]:
            should_edit = True
    
    if edit_message and message_id and should_edit:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка редактирования: {e}")
            # Отправляем новое сообщение вместо редактирования
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    else:
        # Либо отправляем новое сообщение, либо ничего не делаем
        if not edit_message or not should_edit:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def download_guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("=== download_guide_handler CALLED ===")
    query = update.callback_query
    if not query:
        logger.error("No callback query found!")
        return
    
    await query.answer()
    
    logger.info(f"=== START DOWNLOAD GUIDE ===")
    logger.info(f"User ID: {query.from_user.id}")
    logger.info(f"Callback data: {query.data}")
    logger.info(f"Context user_data: {context.user_data}")
    
    # Получаем индекс из callback_data
    data = query.data
    
    if data.startswith("dl:"):
        try:
            guide_idx = int(data.split(":")[1])
            logger.info(f"Parsed guide index: {guide_idx}")
            
            guides = context.user_data.get('guides', [])
            logger.info(f"Guides in context: {len(guides)} items")
            
            if guides:
                for i, g in enumerate(guides):
                    logger.info(f"  Guide {i}: {g.get('name')} -> {g.get('filename')}")
            
            if 0 <= guide_idx < len(guides):
                guide = guides[guide_idx]
                filename = guide.get('filename')
                filepath = DATA_DIR / filename
                
                logger.info(f"Selected guide: {guide}")
                logger.info(f"Filename: {filename}")
                logger.info(f"DATA_DIR: {DATA_DIR}")
                logger.info(f"Full filepath: {filepath}")
                logger.info(f"Filepath exists: {filepath.exists()}")
                logger.info(f"Filepath is absolute: {filepath.is_absolute()}")
                
                if filepath.exists():
                    logger.info(f"File size: {filepath.stat().st_size} bytes")
                else:
                    logger.error(f"FILE NOT FOUND! Checking alternatives...")
                    # Проверяем другие возможные пути
                    alt_paths = [
                        Path("./data") / filename,
                        Path("data") / filename,
                        Path("/home/MED_BOT/MED_BOT/data") / filename,
                    ]
                    for alt in alt_paths:
                        logger.info(f"  Alternative: {alt} -> exists: {alt.exists()}")
                    
            else:
                logger.error(f"Guide index {guide_idx} out of range (0-{len(guides)-1})")
                await query.answer("❌ Гайд не найден по индексу!", show_alert=True)
                return
                
        except Exception as e:
            logger.error(f"Error in parsing: {e}", exc_info=True)
            await query.answer(f"❌ Ошибка обработки: {str(e)[:50]}", show_alert=True)
            return
    else:
        logger.info(f"Old format callback: {data}")
        filename = data.replace("download_", "")
        filepath = DATA_DIR / filename
    
    if not filepath.exists():
        logger.error(f"FINAL: File not found at {filepath}")
        await query.answer("❌ Файл не найден!", show_alert=True)
        return
    
    logger.info(f"Attempting to send file: {filepath}")
    
    try:
        with open(filepath, 'rb') as file:
            logger.info(f"File opened successfully")
            file_size = len(file.read())
            logger.info(f"File size in bytes: {file_size}")
            file.seek(0)  # Возвращаемся в начало файла
            
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                filename=filename,
                caption="Гайд готов к скачиванию ✅ Приятного прочтения и активного долголетия ❤️"
            )
        
        logger.info("✅ File sent successfully")
        await query.answer("✅ Гайд отправлен! Проверьте сообщения.", show_alert=False)
        
    except Exception as e:
        logger.error(f"❌ Error sending file: {e}", exc_info=True)
        await query.answer(f"❌ Ошибка отправки: {str(e)[:100]}", show_alert=True)
    
    logger.info(f"=== END DOWNLOAD GUIDE ===")

async def check_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    user_id = query.from_user.id
    is_subscribed = await check_subscription(context.bot, user_id)
    
    if not is_subscribed:
        
        await query.answer(
            "❌ Вы не подписаны на канал!\n\n"
            "Пожалуйста, подпишитесь на канал"
            "и попробуйте ещё раз.",
            show_alert=True  
        )
        return
    
    await query.answer("✅ Вы подписаны! Загружаю гайды...", show_alert=False)
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
        logger.warning(f"⚠️ Не удалось проверить подписку user_id={user_id}: {e}")
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