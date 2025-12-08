# main.py
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from handlers import (
    start_handler,
    about_handler, reviews_handler, product_handler,
    booking_handler, consent_handler, guide_handler
)

load_dotenv()

def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Команды
    app.add_handler(CommandHandler("start", start_handler))

    # Callback-кнопки (Inline)
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(reviews_handler, pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(product_handler, pattern="^product$"))
    app.add_handler(CallbackQueryHandler(booking_handler, pattern="^booking$"))
    app.add_handler(CallbackQueryHandler(consent_handler, pattern="^consent$"))
    app.add_handler(CallbackQueryHandler(guide_handler, pattern="^guide$"))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()