import os, logging
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

PORT   = int(os.getenv("PORT", "8080"))
PUBLIC = os.getenv("RENDER_EXTERNAL_URL", "")   # render injects this
PATH   = "webhook"

def main():
    if not PUBLIC:
        raise SystemExit("RENDER_EXTERNAL_URL missing — set it or use polling mode.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_cb, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(menu_cb,   pattern="^menu_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, token_input))

    print(f"🚀 KING VOID BIND MANAGER ᴡᴇʙʜᴏᴏᴋ ᴏɴ :{PORT}/{PATH}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=PATH,
        webhook_url=f"{PUBLIC}/{PATH}",
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
