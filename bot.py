import os
import asyncio
import logging
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv

import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---- Voice/audio imports removed ----
# from pydub import AudioSegment
# from gtts import gTTS

# ---- Load env ----
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Set TELEGRAM_TOKEN and OPENAI_API_KEY in .env or Railway Variables")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Helpers ----
async def ask_openai(prompt: str):
    def call_openai():
        return openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            max_tokens=400,
        )
    resp = await asyncio.to_thread(call_openai)
    return resp["choices"][0]["message"]["content"]

async def generate_image(prompt: str):
    def call_images():
        return openai.Image.create(prompt=prompt, n=1, size="512x512")
    resp = await asyncio.to_thread(call_images)
    return resp["data"][0]["url"]

# ---- Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your AI bot. Send me text, /image <prompt>!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/image "):
        prompt = text[len("/image "):]
        await update.message.reply_text("Generating image, please wait...")
        try:
            url = await generate_image(prompt)
            await update.message.reply_photo(photo=url, caption=f"Prompt: {prompt}")
        except Exception as e:
            await update.message.reply_text(f"Image generation failed: {e}")
    else:
        await update.message.chat.do_action("typing")
        try:
            reply = await ask_openai(text)
            await update.message.reply_text(reply)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

# ---- Run ----
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    # Voice handler removed to prevent crash
    # app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    logger.info("Bot started.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
