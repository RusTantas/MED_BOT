# main.py
import os
from dotenv import load_dotenv
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
from handlers.admin import leads_handler, count_handler

from handlers import (
    start_handler,
    handle_main_menu,
    about_handler,
    reviews_handler,
    product_handler,
    booking_handler,
   # consent_handler,
   # start_form_handler,
    guide_handler,
    check_subscription_handler
)

import warnings
from telegram.warnings import PTBUserWarning

# Подавляем только это конкретное предупреждение
warnings.filterwarnings(
    "ignore",
    message=r".*per_message=False.*CallbackQueryHandler",
    category=PTBUserWarning
)

load_dotenv()

def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Диалог согласия
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

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(consent_conv)
    app.add_handler(CommandHandler("leads", leads_handler))
    app.add_handler(CommandHandler("count", count_handler))

    # Блок Влада 
    app.add_handler(CommandHandler("menu", start_handler))

    app.add_handler(CallbackQueryHandler(start_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews_handler, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(product_handler, pattern="^product$"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^booking$"))
    # app.add_handler(CallbackQueryHandler(consent_handler, pattern="^consent$"))
    # app.add_handler(CallbackQueryHandler(start_form_handler, pattern="^start_form$"))
    app.add_handler(CallbackQueryHandler(guide_handler, pattern="^guide$"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_subscription$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()