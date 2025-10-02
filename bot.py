import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# For Chat + Image generation
import openai

# Apply nest_asyncio to prevent event loop crashes
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

openai.api_key = OPENAI_API_KEY

# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 🤖 I am your AI bot.\n"
        "Send me a message to chat or type /image <prompt> to generate an image."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/image <prompt> - Generate an image"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}],
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        reply_text = f"⚠️ Error: {e}"

    await update.message.reply_text(reply_text)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a prompt. Example:\n/image a cat riding a skateboard")
        return

    prompt = " ".join(context.args)

    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024"
        )
        image_url = response.data[0].url
        await update.message.reply_text(f"Here is your image:\n{image_url}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generating image: {e}")

# --- Main Bot Runner ---

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("image", generate_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started ✅")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
