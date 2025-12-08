import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers import (
    start_handler,
    handle_main_menu,
    about_handler,
    reviews_handler,
    product_handler,
    booking_handler,
    consent_handler,
    start_form_handler,
    guide_handler,
    check_subscription_handler
)

load_dotenv()

def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("menu", start_handler))

    app.add_handler(CallbackQueryHandler(start_handler, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews_handler, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(product_handler, pattern="^product$"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^booking$"))
    app.add_handler(CallbackQueryHandler(consent_handler, pattern="^consent$"))
    app.add_handler(CallbackQueryHandler(start_form_handler, pattern="^start_form$"))
    app.add_handler(CallbackQueryHandler(guide_handler, pattern="^guide$"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_subscription$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))


    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()