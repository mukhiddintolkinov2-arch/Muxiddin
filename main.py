import os
import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

GROQ_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
if not GROQ_KEY or not TELEGRAM_TOKEN:
    raise RuntimeError("GROQ_API_KEY yoki BOT_TOKEN topilmadi")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Muxiddin AI Online")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def ask_groq(messages, model="llama3-70b-8192", temperature=0.6):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": temperature}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

chat_histories: dict[int, list] = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    cid = update.effective_chat.id
    text = update.message.text

    if cid not in chat_histories:
        chat_histories[cid] = [{
            "role": "system",
            "content": (
                "Sizning ismingiz Muxiddin AI. Siz har doim faqat o‘zbek tilida, "
                "xushmuomala va aniq javob berasiz."
            ),
        }]

    chat_histories[cid].append({"role": "user", "content": text})
    while len(chat_histories[cid]) > 12:
        chat_histories[cid].pop(1)

    try:
        reply = await ask_groq(chat_histories[cid])
    except Exception:
        reply = await ask_groq(
            [
                {"role": "system", "content": "Faqat o‘zbek tilida javob ber."},
                {"role": "user", "content": text},
            ],
            model="llama3-8b-8192",
        )

    chat_histories[cid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def start_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
