import os
import asyncio
import logging
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv

import openai
from gtts import gTTS
from pydub import AudioSegment
audio = AudioSegment.from_file(ogg_path, format="ogg")
audio.export(wav_path, format="wav")
from pydub import AudioSegment
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

async def transcribe_audio(file_path: str):
    def call_transcribe():
        with open(file_path, "rb") as f:
            return openai.Audio.transcribe("whisper-1", f)
    resp = await asyncio.to_thread(call_transcribe)
    return resp.get("text", "")

def text_to_speech(text: str, out_path: str):
    tts = gTTS(text=text, lang="en")
    tts.save(out_path)
    return out_path

# ---- Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your AI bot. Send me text, /image <prompt>, or voice message!")

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
        # Typing indicator fix for PTB v20
        await update.message.chat.send_action(action=ChatAction.TYPING)
        try:
            reply = await ask_openai(text)
            await update.message.reply_text(reply)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    if not voice:
        await update.message.reply_text("No voice found.")
        return

    file = await context.bot.get_file(voice.file_id)
    tmp = Path("tmp")
    tmp.mkdir(exist_ok=True)
    ogg_path = tmp / f"{uuid4()}.ogg"
    await file.download_to_drive(str(ogg_path))

    wav_path = tmp / f"{uuid4()}.wav"
    audio = AudioSegment.from_file(ogg_path)
    audio.export(wav_path, format="wav")

    try:
        text = await transcribe_audio(str(wav_path))
        await update.message.reply_text(f"You said: {text}\nProcessing...")
        reply = await ask_openai(text)
        await update.message.reply_text(reply)
        tts_file = tmp / f"{uuid4()}.mp3"
        text_to_speech(reply, str(tts_file))
        with open(tts_file, "rb") as f:
            await update.message.reply_voice(voice=f)
    except Exception as e:
        await update.message.reply_text(f"Voice processing failed: {e}")

# ---- Run ----
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    logger.info("Bot started.")
    await app.run_polling()

if __name__ == "__main__":
    # Fix for "event loop already running" in Railway / Jupyter / other async environments
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
