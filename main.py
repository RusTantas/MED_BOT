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

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()