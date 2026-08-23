import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Render yoki boshqa platformalar uchun Health Check
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# API kalitlar
GROQ_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

client = Groq(api_key=GROQ_KEY)

def get_active_model():
    """Akkauntingizda mavjud bo'lgan birinchi ishlaydigan modelni oladi"""
    try:
        models = client.models.list()
        # Birinchi navbatda Llama 3.3 yoki 3.2 ni qidiradi
        for m in models.data:
            if "llama-3.3" in m.id or "llama-3.2" in m.id:
                return m.id
        # Bo'lmasa, ro'yxatdagi birinchi modelni oladi
        return models.data[0].id
    except:
        return "llama-3.3-70b-versatile"

# Dinamik model tanlash
CURRENT_MODEL = get_active_model()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_MODEL
    if not update.message or not update.message.text:
        return
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model=CURRENT_MODEL,
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        # Agar model o'chgan bo'lsa (400/404), yangisini qidirib qayta urinadi
        try:
            CURRENT_MODEL = get_active_model()
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": update.message.text}],
                model=CURRENT_MODEL,
            )
            await update.message.reply_text(chat_completion.choices[0].message.content)
        except Exception as last_error:
            await update.message.reply_text(f"Xatolik yuz berdi: {str(last_error)}")

def main():
    # Serverni alohida oqimda ishga tushirish
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # Botni ishga tushirish
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"Bot ishga tushdi. Tanlangan model: {CURRENT_MODEL}")
    application.run_polling()

if __name__ == '__main__':
    main()
