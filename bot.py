import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq.client import GroqClient
from dotenv import load_dotenv

# Prevent event loop crash
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = GroqClient(api_key=GROQ_API_KEY)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 🤖 I am your Groq-powered bot.\n"
        "Send me a message to chat or type /image <prompt> to generate an image."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.chat_completion(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": user_text}]
        )
        reply_text = response.completion
    except Exception as e:
        reply_text = f"⚠️ Error: {e}"
    await update.message.reply_text(reply_text)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide a prompt. Example:\n/image a cat riding a skateboard"
        )
        return

    prompt = " ".join(context.args)
    try:
        response = client.image_generation(
            model="groq-dalle-mini",
            prompt=prompt,
            size="1024x1024"
        )
        image_url = response.images[0].url
        await update.message.reply_text(f"Here is your image:\n{image_url}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generating image: {e}")

# --- Main ---
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", generate_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started ✅")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
