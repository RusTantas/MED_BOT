# main.py
import os
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

# --- Основные хендлеры ---
from handlers.start import start_handler
from handlers.consent import (
    consent_start, consent_full_name, full_name_received,
    phone_received, email_received, consent_confirm,
    consent_restart, cancel,
    FULL_NAME, PHONE, EMAIL, CONFIRM
)

# --- Админ-хендлеры ---
# Обрати внимание: leads_handler больше не нужен — заменён на диалог
from handlers.admin import (
    albina_handler,
    admin_ask_leads_callback,
    admin_count_now_callback,
    admin_export_csv_callback,
    admin_upload_guide_callback,   # ← новое
    process_leads_count,
    receive_guide_file,            # ← новое
    count_handler,
    cancel as admin_cancel,        # ← чтобы не конфликтовало с consent.cancel
    ASK_LEADS_COUNT,
    AWAIT_GUIDE_FILE               # ← новое
)

# --- Остальные хендлеры (меню, разделы и т.д.) ---
from handlers import (
    handle_main_menu,
    about_handler,
    reviews_handler,
    product_handler,
    booking_handler,
    guide_handler,
    check_subscription_handler,
    download_guide_handler,
    show_guides_list
)

# --- Подавление предупреждения (оставим как есть) ---
import warnings
from telegram.warnings import PTBUserWarning

warnings.filterwarnings(
    "ignore",
    message=r".*per_message=False.*CallbackQueryHandler",
    category=PTBUserWarning
)

load_dotenv()


def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # --- Диалог согласия (остаётся без изменений) ---
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

    # --- Диалог админ-запроса количества лидов ---
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

    # main.py → внутри def main():

    # --- Диалог загрузки гайда ---
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

    # --- Регистрация хендлеров ---

    # Команды
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", start_handler))  # алиас

    # Админ-команды
    app.add_handler(CommandHandler("albina", albina_handler))
    app.add_handler(CommandHandler("count", count_handler))  # можно вызывать и так
    app.add_handler(CommandHandler("guides", show_guides_list))

    # Диалоги
    app.add_handler(consent_conv)
    app.add_handler(leads_conversation)
    app.add_handler(upload_guide_conv)

    # Callback-кнопки основного меню
    app.add_handler(CallbackQueryHandler(start_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews_handler, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(product_handler, pattern="^product$"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^booking$"))
    app.add_handler(CallbackQueryHandler(guide_handler, pattern="^guide$"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(download_guide_handler, pattern="^download_.*$"))

    # Callback-кнопки админ-меню
    app.add_handler(CallbackQueryHandler(admin_count_now_callback, pattern="^admin_count_now$"))
    app.add_handler(CallbackQueryHandler(admin_export_csv_callback, pattern="^admin_export_csv$"))
    # (leads_conversation уже обрабатывает admin_ask_leads)

    # Обработка текстовых сообщений (главное меню по названию)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    # Запуск
    print("✅ Бот запущен. Ожидаю обновлений...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()