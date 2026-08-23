import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from openai import OpenAI

# Kalitlarni Render sozlamalaridan (Environment Variables) olish
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

async def handle_message(update: Update, context):
    user_text = update.message.text
    try:
        # OpenAI dan javob olish
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

def main():
    # Botni ishga tushirish
    if not TELEGRAM_TOKEN:
        print("XATO: TELEGRAM_TOKEN topilmadi!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Matnli xabarlarni qayta ishlash
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
