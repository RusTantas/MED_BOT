import asyncio
import telegram
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from logger import logger
import database
from .helpers import is_admin, reply_to_update

SEND_BROADCAST = 5
BROADCAST_TEXT = 6
BROADCAST_PHOTO = 7
BROADCAST_DOCUMENT = 8

async def admin_broadcast_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    history = database.get_broadcast_history(10)

    if not history:
        text = "📋 *История рассылок*\n\nРассылок еще не было."
    else:
        text = "📋 *История рассылок (последние 10)*\n\n"
        for broadcast in history:
            success_rate = (broadcast['successful'] / broadcast['total_users'] * 100) if broadcast['total_users'] > 0 else 0
            text += f"📅 *{broadcast['sent_at']}*\n"
            text += f"Тип: {broadcast['type'].upper()}\n"
            text += f"Пользователей: {broadcast['total_users']}\n"
            text += f"Успешно: {broadcast['successful']} ({success_rate:.1f}%)\n"
            text += f"Не удалось: {broadcast['failed']}\n"
            text += f"Текст: {broadcast['content']}\n"
            text += "─" * 30 + "\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Новая рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return

    total_users = database.get_user_count()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Рассылка ТЕКСТОМ", callback_data="broadcast_text")],
        [InlineKeyboardButton("🖼 Рассылка с ФОТО", callback_data="broadcast_photo")],
        [InlineKeyboardButton("📎 Рассылка с ДОКУМЕНТОМ", callback_data="broadcast_document")],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    await query.edit_message_text(
        text=f"📢 *РАССЫЛКА СООБЩЕНИЙ*\n\n"
             f"Всего пользователей в базе: *{total_users}*\n\n"
             "Выберите тип рассылки:\n"
             "• *ТЕКСТ* — обычное текстовое сообщение\n"
             "• *ФОТО* — картинка с подписью\n"
             "• *ДОКУМЕНТ* — файл с подписью\n\n"
             "ℹ️ Подпись к фото/документу можно оставить пустой.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def broadcast_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast_type"] = "text"
    await query.edit_message_text(
        text="📝 *РАССЫЛКА ТЕКСТОМ*\n\n"
             "Введите текст для рассылки:\n\n"
             "ℹ️ Поддерживается Markdown разметка:\n"
             "• *жирный* — *текст*\n"
             "• _курсив_ — _текст_\n"
             "• [ссылка](https://...) — [текст](ссылка)\n\n"
             "❌ Отмена: /cancel",
        parse_mode="Markdown"
    )
    return BROADCAST_TEXT

async def broadcast_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast_type"] = "photo"
    await query.edit_message_text(
        text="🖼 *РАССЫЛКА С ФОТО*\n\n"
             "Отправьте фотографию (не файлом, а как фото):\n\n"
             "❌ Отмена: /cancel",
        parse_mode="Markdown"
    )
    return BROADCAST_PHOTO

async def broadcast_document_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["broadcast_type"] = "document"
    await query.edit_message_text(
        text="📎 *РАССЫЛКА С ДОКУМЕНТОМ*\n\n"
             "Отправьте документ (PDF, Word, Excel и т.д.):\n\n"
             "❌ Отмена: /cancel",
        parse_mode="Markdown"
    )
    return BROADCAST_DOCUMENT

async def process_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    message_text = update.message.text.strip()
    if not message_text:
        await update.message.reply_text("❌ Текст не может быть пустым. Попробуйте снова:")
        return BROADCAST_TEXT

    context.user_data["broadcast_content"] = message_text
    total_users = database.get_user_count()
    preview = message_text[:200] + "..." if len(message_text) > 200 else message_text

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, отправить всем", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_broadcast")]
    ])

    await update.message.reply_text(
        f"📨 *ПРЕДПРОСМОТР РАССЫЛКИ*\n\n"
        f"Тип: Текст\n"
        f"Получателей: {total_users}\n"
        f"Длина: {len(message_text)} символов\n\n"
        f"*Текст:*\n{preview}\n\n"
        f"Отправить это сообщение всем пользователям?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    return SEND_BROADCAST

async def process_broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    if update.message.photo:
        photo = update.message.photo[-1]
        context.user_data["broadcast_photo_id"] = photo.file_id
        await update.message.reply_text(
            "✅ Фото получено. Теперь отправьте подпись к фото "
            "(или /skip чтобы оставить без подписки):"
        )
        return BROADCAST_TEXT

    await update.message.reply_text("❌ Пожалуйста, отправьте фото.")
    return BROADCAST_PHOTO

async def process_broadcast_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    if update.message.document:
        document = update.message.document
        context.user_data["broadcast_document_id"] = document.file_id
        context.user_data["broadcast_document_name"] = document.file_name
        await update.message.reply_text(
            "✅ Документ получен. Теперь отправьте подпись к документу "
            "(или /skip чтобы оставить без подписки):"
        )
        return BROADCAST_TEXT

    await update.message.reply_text("❌ Пожалуйста, отправьте документ.")
    return BROADCAST_DOCUMENT

async def process_broadcast_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await reply_to_update(update, "🔒 Доступ запрещён.")
        return ConversationHandler.END

    broadcast_type = context.user_data.get("broadcast_type")
    total_users = database.get_user_count()

    if update.message.text and update.message.text.strip() == "/skip":
        caption = ""
    else:
        caption = update.message.text.strip() if update.message.text else ""

    context.user_data["broadcast_caption"] = caption

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, отправить всем", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_broadcast")]
    ])

    if broadcast_type == "photo":
        caption_info = f"Длина подписи: {len(caption)} символов" if caption else "Подпись: без подписи"
        text = (f"📸 *ПРЕДПРОСМОТР РАССЫЛКИ*\n\n"
                f"Тип: Фото с подписью\n"
                f"Получателей: {total_users}\n"
                f"{caption_info}\n\n"
                f"Отправить фото всем пользователям?")
    elif broadcast_type == "document":
        doc_name = context.user_data.get("broadcast_document_name", "документ")
        caption_info = f"Длина подписи: {len(caption)} символов" if caption else "Подпись: без подписи"
        text = (f"📎 *ПРЕДПРОСМОТР РАССЫЛКИ*\n\n"
                f"Тип: Документ с подписью\n"
                f"Файл: {doc_name}\n"
                f"Получателей: {total_users}\n"
                f"{caption_info}\n\n"
                f"Отправить документ всем пользователям?")

    await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
    return SEND_BROADCAST

async def confirm_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    broadcast_type = context.user_data.get("broadcast_type", "text")
    all_users = database.get_all_active_users()
    total = len(all_users)

    if total == 0:
        await query.edit_message_text(
            "❌ Нет пользователей для рассылки.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
            ])
        )
        return ConversationHandler.END

    if broadcast_type == "text":
        content = context.user_data.get("broadcast_content", "")
        content_preview = content[:100] + "..." if len(content) > 100 else content
    elif broadcast_type == "photo":
        content = context.user_data.get("broadcast_caption", "")
        content_preview = "Фото" + (f": {content[:100]}..." if content else "")
    elif broadcast_type == "document":
        doc_name = context.user_data.get("broadcast_document_name", "документ")
        content = context.user_data.get("broadcast_caption", "")
        content_preview = f"Документ: {doc_name}" + (f" - {content[:100]}..." if content else "")

    broadcast_id = database.add_broadcast_record(user_id, broadcast_type, content_preview)

    await query.edit_message_text(f"🔄 Начинаю рассылку...\nПолучателей: {total}\nОтправка...")

    successful = 0
    failed = 0

    for user in all_users:
        try:
            if broadcast_type == "text":
                content = context.user_data.get("broadcast_content", "")
                await context.bot.send_message(
                    chat_id=user['chat_id'], text=content, parse_mode="Markdown"
                )
            elif broadcast_type == "photo":
                photo_id = context.user_data.get("broadcast_photo_id")
                caption = context.user_data.get("broadcast_caption", "")
                await context.bot.send_photo(
                    chat_id=user['chat_id'], photo=photo_id,
                    caption=caption if caption else None, parse_mode="Markdown"
                )
            elif broadcast_type == "document":
                document_id = context.user_data.get("broadcast_document_id")
                caption = context.user_data.get("broadcast_caption", "")
                await context.bot.send_document(
                    chat_id=user['chat_id'], document=document_id,
                    caption=caption if caption else None, parse_mode="Markdown"
                )

            successful += 1
            database.add_broadcast_log(broadcast_id, user['user_id'], user['chat_id'], "success")
            await asyncio.sleep(0.05)

        except telegram.error.Unauthorized as e:
            failed += 1
            database.add_broadcast_log(broadcast_id, user['user_id'], user['chat_id'], "failed", "Пользователь заблокировал бота")
            logger.warning(f"Пользователь {user['user_id']} заблокировал бота")
        except Exception as e:
            failed += 1
            error_msg = str(e)[:200]
            database.add_broadcast_log(broadcast_id, user['user_id'], user['chat_id'], "failed", error_msg)
            logger.error(f"Ошибка отправки сообщения {user['chat_id']}: {e}")

    database.update_broadcast_stats(broadcast_id, total, successful, failed)

    success_rate = (successful / total * 100) if total > 0 else 0
    report = (
        f"📊 *ОТЧЕТ О РАССЫЛКЕ*\n\n"
        f"Тип: {broadcast_type.upper()}\n"
        f"Всего получателей: {total}\n"
        f"✅ Успешно: {successful} ({success_rate:.1f}%)\n"
        f"❌ Не удалось: {failed}\n"
        f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"ID рассылки: #{broadcast_id}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 История рассылок", callback_data="admin_broadcast_history")],
        [InlineKeyboardButton("📢 Новая рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
    ])

    await query.edit_message_text(text=report, reply_markup=keyboard, parse_mode="Markdown")

    for key in ["broadcast_type", "broadcast_content", "broadcast_photo_id",
                "broadcast_document_id", "broadcast_caption", "broadcast_document_name"]:
        context.user_data.pop(key, None)

    return ConversationHandler.END

async def cancel_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    for key in ["broadcast_type", "broadcast_content", "broadcast_photo_id",
                "broadcast_document_id", "broadcast_caption", "broadcast_document_name"]:
        context.user_data.pop(key, None)

    await query.edit_message_text(
        "❌ Рассылка отменена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад в админ-панель", callback_data="back_to_admin")]
        ])
    )

    return ConversationHandler.END
