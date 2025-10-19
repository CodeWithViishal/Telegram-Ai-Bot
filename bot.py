import os
import requests
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Fix for async loop issue
nest_asyncio.apply()

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# --- Chat Function (Text AI) ---
async def chat_with_ai(prompt):
    url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        else:
            return "⚠️ Sorry, I couldn’t understand the response."
    else:
        return f"⚠️ API Error {response.status_code}: {response.text}"

# --- Image Generator ---
async def generate_image(prompt):
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        filename = "generated_image.png"
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    else:
        return None

# --- Telegram Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hello! I'm your free AI bot.\n"
        "💬 Send me any message to chat.\n"
        "🖼️ Use /image <prompt> to generate an image!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("⏳ Thinking...")
    reply = await chat_with_ai(user_text)
    await update.message.reply_text(reply)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Please type like this:\n/image a cat riding a skateboard")
        return
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 Generating image, please wait...")
    image_file = await generate_image(prompt)
    if image_file:
        await update.message.reply_photo(photo=open(image_file, "rb"))
    else:
        await update.message.reply_text("⚠️ Error generating image. Try again later.")

# --- Main Function ---
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
