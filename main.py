import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

GROQ_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

client = Groq(api_key=GROQ_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": update.message.text}],
            model="llama3-70b-8192",
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
