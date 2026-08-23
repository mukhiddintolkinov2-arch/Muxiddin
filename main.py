import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Loglarni sozlash (Xatolarni kuzatish uchun)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Hosting (Render) uchun Health Check server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Muxiddin AI Online")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# API kalitlarni olish
GROQ_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

client = Groq(api_key=GROQ_KEY)

# Chat xotirasi (Kontekst)
chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Faqat matnli xabarlarni qayta ishlash
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name
    user_text = update.message.text

    # Yangi chat uchun xotira yaratish va qat'iy til qoidasini o'rnatish
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [
            {
                "role": "system", 
                "content": (
                    "Sizning ismingiz Muxiddin AI. Siz Telegram guruhlarida va shaxsiy xabarlarda "
                    "do'stona suhbatdoshsiz. SIZ FAQAT O'ZBEK TILIDA JAVOB BERISHINGIZ SHART! "
                    "Hech qachon inglizcha so'z aralashtirmang. Foydalanuvchi inglizcha yozsa ham, "
                    "siz javobni toza o'zbek tilida bering. O'zbek tilidagi terminlarni ishlating."
                )
            }
        ]

    # Foydalanuvchi xabarini xotiraga qo'shish
    chat_histories[chat_id].append({"role": "user", "content": f"{user_name}: {user_text}"})

    # Xotirani oxirgi 12 ta xabar bilan cheklash (Bot adashib ketmasligi uchun)
    if len(chat_histories[chat_id]) > 12:
        chat_histories[chat_id].pop(1)

    try:
        # AI dan javob so'rash
        completion = client.chat.completions.create(
            messages=chat_histories[chat_id],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
        )
        
        ai_response = completion.choices[0].message.content
        
        # AI javobini xotiraga saqlash
        chat_histories[chat_id].append({"role": "assistant", "content": ai_response})

        # Javobni Telegramga yuborish
        await update.message.reply_text(ai_response)
            
    except Exception as e:
        logging.error(f"Xato yuz berdi: {e}")
        # Zaxira modeli (Agar asosiy modelda muammo bo'lsa)
        try:
            fallback = client.chat.completions.create(
                messages=[{"role": "system", "content": "Faqat o'zbek tilida javob ber."}, 
                          {"role": "user", "content": user_text}],
                model="llama3-8b-8192"
            )
            await update.message.reply_text(fallback.choices[0].message.content)
        except:
            pass

def main():
    # Health check serverni ishga tushirish
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # Botni yaratish
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Barcha xabarlarga javob berish handlerini qo'shish
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Muxiddin AI (Universal) ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':
    main()
