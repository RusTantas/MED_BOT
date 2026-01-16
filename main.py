import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

from handlers.start import start_handler
from handlers.consent import (
    consent_start, consent_full_name, full_name_received,
    phone_received, email_received, consent_confirm,
    consent_restart, cancel,
    FULL_NAME, PHONE, EMAIL, CONFIRM
)

from handlers.admin import (
    albina_handler,
    admin_ask_leads_callback,
    admin_count_now_callback,
    admin_export_csv_callback,
    admin_upload_guide_callback,
    admin_user_stats_callback,
    admin_broadcast_history_callback,
    admin_broadcast_callback,
    broadcast_text_callback,
    broadcast_photo_callback,
    broadcast_document_callback,
    process_broadcast_text,
    process_broadcast_photo,
    process_broadcast_document,
    process_broadcast_caption,
    confirm_broadcast_callback,
    cancel_broadcast_callback,
    process_leads_count,
    receive_guide_file,
    count_handler,
    cancel as admin_cancel,
    ASK_LEADS_COUNT,
    AWAIT_GUIDE_FILE,
    SEND_BROADCAST,
    BROADCAST_TEXT,
    BROADCAST_PHOTO,
    BROADCAST_DOCUMENT
)

from handlers import (
    handle_main_menu,
    about_handler,
    reviews_handler,
    product_handler,
    booking_handler,
    guide_handler,
    check_subscription_handler,
    download_guide_handler,
    show_guides_list,
    product_handler,
    show_tariff_new,
    show_tariff_month2,
    show_tariff_long,
    show_tariff_detox
)

import warnings
from telegram.warnings import PTBUserWarning
from logger import logger
import asyncio
import time
from telegram.error import NetworkError, RetryAfter, TimedOut
import database  # Импортируем базу данных

warnings.filterwarnings(
    "ignore",
    message=r".*per_message=False.*CallbackQueryHandler",
    category=PTBUserWarning
)

load_dotenv()

# Настройка глобального exception handler'а
def global_exception_handler(update, context):
    logger.error(
        "Unhandled exception occurred",
        exc_info=context.error,
        extra={"update": update.to_dict() if update else None}
    )
    
    # Опционально: отправить админам сообщение об ошибке
    try:
        import os
        admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        error_msg = (
            f"🚨 *Критическая ошибка в боте*\n"
            f"```\n{str(context.error)[:1000]}\n```"
        )
        for admin_id in admin_ids:
            context.bot.send_message(chat_id=admin_id, text=error_msg, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Failed to notify admins: {e}")

def main():
    # Инициализация базы данных
    database.init_database()
    
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    consent_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(consent_start, pattern="^consent$")],
        states={
            FULL_NAME: [
                CallbackQueryHandler(consent_full_name, pattern="^consent_start$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, full_name_received)
            ],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_received)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_received)],
            CONFIRM: [
                CallbackQueryHandler(consent_confirm, pattern="^consent_confirm$"),
                CallbackQueryHandler(consent_restart, pattern="^consent_restart$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    leads_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_ask_leads_callback, pattern="^admin_ask_leads$")],
        states={
            ASK_LEADS_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_leads_count)
            ]
        },
        fallbacks=[],
        allow_reentry=True
    )

    upload_guide_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_upload_guide_callback, pattern="^admin_upload_guide$")],
        states={
            AWAIT_GUIDE_FILE: [
                MessageHandler(filters.Document.ALL & ~filters.COMMAND, receive_guide_file)
            ]
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True
    )

    # ConversationHandler для текстовой рассылки
    broadcast_text_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_text_callback, pattern="^broadcast_text$")],
        states={
            BROADCAST_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast_text)
            ],
            SEND_BROADCAST: []  # Для подтверждения
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True
    )
    
    # ConversationHandler для рассылки с фото
    broadcast_photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_photo_callback, pattern="^broadcast_photo$")],
        states={
            BROADCAST_PHOTO: [
                MessageHandler(filters.PHOTO & ~filters.COMMAND, process_broadcast_photo)
            ],
            BROADCAST_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast_caption)
            ],
            SEND_BROADCAST: []  # Для подтверждения
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True
    )
    
    # ConversationHandler для рассылки с документом
    broadcast_document_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_document_callback, pattern="^broadcast_document$")],
        states={
            BROADCAST_DOCUMENT: [
                MessageHandler(filters.Document.ALL & ~filters.COMMAND, process_broadcast_document)
            ],
            BROADCAST_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast_caption)
            ],
            SEND_BROADCAST: []  # Для подтверждения
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", start_handler))
    app.add_handler(CommandHandler("albina", albina_handler))
    app.add_handler(CommandHandler("count", count_handler))
    app.add_handler(CommandHandler("guides", show_guides_list))

    app.add_handler(consent_conv)
    app.add_handler(leads_conversation)
    app.add_handler(upload_guide_conv)
    app.add_handler(broadcast_text_conv)
    app.add_handler(broadcast_photo_conv)
    app.add_handler(broadcast_document_conv)

    app.add_handler(CallbackQueryHandler(start_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews_handler, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(product_handler, pattern="^product$"))
    app.add_handler(CallbackQueryHandler(show_tariff_new, pattern="^product_new$"))
    app.add_handler(CallbackQueryHandler(show_tariff_month2, pattern="^product_month2$"))
    app.add_handler(CallbackQueryHandler(show_tariff_long, pattern="^product_long$"))
    app.add_handler(CallbackQueryHandler(show_tariff_detox, pattern="^tariff_detox$"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^booking$"))
    app.add_handler(CallbackQueryHandler(guide_handler, pattern="^guide$"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(download_guide_handler, pattern="^dl:.*$"))
    app.add_handler(CallbackQueryHandler(admin_count_now_callback, pattern="^admin_count_now$"))
    app.add_handler(CallbackQueryHandler(admin_export_csv_callback, pattern="^admin_export_csv$"))
    app.add_handler(CallbackQueryHandler(admin_user_stats_callback, pattern="^admin_user_stats$"))
    app.add_handler(CallbackQueryHandler(admin_broadcast_history_callback, pattern="^admin_broadcast_history$"))
    app.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"))
    app.add_handler(CallbackQueryHandler(confirm_broadcast_callback, pattern="^confirm_broadcast$"))
    app.add_handler(CallbackQueryHandler(cancel_broadcast_callback, pattern="^cancel_broadcast$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
    
    # Регистрируем глобальный обработчик ошибок
    app.add_error_handler(global_exception_handler)

    logger.info("✅ Бот запущен. Логирование активно.")

    while True:
        try:
            app.run_polling(
                drop_pending_updates=True,
                close_loop=False,
                allowed_updates=Update.ALL_TYPES
            )
        except (NetworkError, TimedOut, RetryAfter) as e:
            logger.warning(f"⚠️ Сетевая ошибка: {e}. Переподключение через 5 сек...")
            time.sleep(5)
        except Exception as e:
            logger.exception(f"🚨 Критическая ошибка. Перезапуск через 10 сек...")
            time.sleep(10)
        finally:
            # Очистим pending updates при перезапуске
            try:
                asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))
            except:
                pass

if __name__ == "__main__":
    main()