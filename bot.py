import os
import asyncio
import nest_asyncio
import time
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from dotenv import load_dotenv

# Apply nest_asyncio to prevent "event loop already running" crash
nest_asyncio.apply()

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Logging
logger = logging.getLogger(__name__)

# Globals for cooldown & retry
USER_LAST_CALL = {}
USER_COOLDOWN_SECONDS = 2
MAX_RETRIES = 3
MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 300


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your bot. Send me a message.")


async def safe_chat_completion(user_text: str, model: str = MODEL, max_retries: int = MAX_RETRIES):
    messages = [{"role": "user", "content": user_text}]
    for attempt in range(max_retries):
        try:
            # run OpenAI call in thread
            resp = await asyncio.to_thread(
                lambda: openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                )
            )
            return resp.choices[0].message.content
        except Exception as e:
            msg_lower = str(e).lower()
            if "quota" in msg_lower or "rate limit" in msg_lower or "429" in msg_lower:
                wait = 2 ** attempt
                logger.warning(f"Rate/quota error, retry {attempt+1} after {wait}s: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                    continue
                else:
                    return None
            else:
                logger.exception(f"Unexpected OpenAI error: {e}")
                raise
    return None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    last = USER_LAST_CALL.get(user_id, 0)

    # Cooldown check
    if now - last < USER_COOLDOWN_SECONDS:
        await update.message.reply_text("Please wait a second before sending another message.")
        return
    USER_LAST_CALL[user_id] = now

    user_text = update.message.text.strip()
    if not user_text:
        await update.message.reply_text("Please send some text.")
        return

    status_msg = await update.message.reply_text("Processing your message...")

    try:
        reply = await safe_chat_completion(user_text)
    except Exception:
        await status_msg.edit_text("Sorry, an internal error occurred. Please try again later.")
        return

    if reply is None:
        await status_msg.edit_text(
            "⚠️ Sorry — OpenAI API is currently unavailable (quota or rate limit). Please try again in a few minutes."
        )
        return

    await status_msg.edit_text(reply)


async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started.")
    await app.run_polling()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
