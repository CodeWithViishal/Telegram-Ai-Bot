import os
import asyncio
import nest_asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Fix async issues for Railway
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hello! I’m your *Free AI Bot*.\n\n"
        "💬 Send me a message to chat.\n🖼 Use /image <prompt> to generate an image.",
        parse_mode="Markdown"
    )

# --- Chat Command ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("💭 Thinking...")

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": user_text}
        )

        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            reply = data[0]["generated_text"]
        else:
            reply = "⚠️ Sorry, I couldn’t generate a reply."
    except Exception as e:
        reply = f"⚠️ Error: {e}"

    await update.message.reply_text(reply)

# --- Image Generator ---
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /image <prompt>")
        return

    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 Generating image... please wait ⏳")

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": prompt}
        )

        if response.status_code == 200:
            with open("output.png", "wb") as f:
                f.write(response.content)
            await update.message.reply_photo(photo=open("output.png", "rb"))
        else:
            await update.message.reply_text(f"⚠️ Failed: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# --- Main Bot ---
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", generate_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot started!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
