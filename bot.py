import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from groq import Groq  # Make sure correct import for Groq

# Apply nest_asyncio to prevent event loop crashes
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 🤖 I am your Gen z Ai bot.\n"
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
        # Groq Chat request
        response = client.chat(
            model="llama-3.1-8b-instant",  # Update to a supported Groq model
            inputs=[{"role": "user", "content": user_text}]
        )
        reply_text = response["outputs"][0]["content"]
    except Exception as e:
        reply_text = f"⚠️ Error: {e}"

    await update.message.reply_text(reply_text)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a prompt. Example:\n/image a cat riding a skateboard")
        return

    prompt = " ".join(context.args)

    try:
        # Groq Image generation
        response = client.image(
            model="groq-image-1",  # Example model, replace if needed
            prompt=prompt,
            size="1024x1024"
        )
        image_url = response["outputs"][0]["url"]
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

    print("Gen Z ai Bot started ✅")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
