import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Render va boshqa platformalar uchun Health Check server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Muxiddin AI ishlamoqda...")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# API kalitlar (Environment Variables orqali)
GROQ_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

client = Groq(api_key=GROQ_KEY)

# Guruh xotirasi (Har bir chat uchun alohida kontekst)
chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name
    user_text = update.message.text

    # Kontekstni boshqarish va Qat'iy O'zbek tili qoidasi
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [
            {
                "role": "system", 
                "content": (
                    "Sizning ismingiz Muxiddin AI. Siz guruhdagi aqlli va samimiy suhbatdoshsiz. "
                    "SIZ FAQAT O'ZBEK TILIDA JAVOB BERISHINGIZ SHART! Inglizcha so'zlarni mutlaqo aralashtirmang. "
                    "Agar foydalanuvchi inglizcha yozsa ham, siz javobni toza o'zbek tilida qaytaring. "
                    "Guruh a'zolari bilan do'stona muloqot qiling."
                )
            }
        ]

    # Foydalanuvchi xabarini xotiraga qo'shish
    chat_histories[chat_id].append({"role": "user", "content": f"{user_name}: {user_text}"})

    # Xotirani cheklash (oxirgi 12 ta xabar saqlanadi)
    if len(chat_histories[chat_id]) > 12:
        chat_histories[chat_id].pop(1)

    try:
        # Groq AI dan javob olish
        completion = client.chat.completions.create(
            messages=chat_histories[chat_id],
            model="llama-3.3-70b-versatile",
            temperature=0.6, # Til aniqligini ta'minlash uchun pasaytirildi
        )
        
        ai_response = completion.choices[0].message.content
        
        # AI javobini xotiraga saqlash
        chat_histories[chat_id].append({"role": "assistant", "content": ai_response})

        await update.message.reply_text(ai_response)
            
    except Exception as e:
        # Zaxira (Fallback) model agar asosiy modelda xato bo'lsa
        try:
            fallback = client.chat.completions.create(
                messages=[{"role": "system", "content": "Faqat o'zbek tilida javob bering."}, 
                          {"role": "user", "content": user_text}],
                model="llama3-8b-8192"
            )
            await update.message.reply_text(fallback.choices[0].message.content)
        except:
            print(f"Tizimda xatolik: {e}")

def main():
    # Health check serverni alohida oqimda boshlash
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # Telegram botni sozlash
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Guruhdagi barcha matnlarni o'qish (Privacy Mode OFF bo'lishi kerak)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Muxiddin AI guruhlarda suhbatlashishga tayyor...")
    application.run_polling()

if __name__ == '__main__':
    main()
