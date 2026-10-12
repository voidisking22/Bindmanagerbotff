import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters,
)
from config import BOT_TOKEN
from handlers import start, verify_cb, menu_cb, token_input

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_cb, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(menu_cb,   pattern="^menu_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, token_input))

    print("🚀 KING VOID BIND MANAGER ɪꜱ ʀᴜɴɴɪɴɢ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()