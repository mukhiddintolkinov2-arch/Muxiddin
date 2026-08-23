import os
import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not GROQ_KEY or not BOT_TOKEN:
    raise RuntimeError("GROQ_API_KEY yoki BOT_TOKEN topilmadi")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_server() -> None:
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

async def ask_groq(
    messages: list[dict], model: str = "llama3-70b-8192", temperature: float = 0.6
) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as s:
        async with s.post(url, headers=headers, json=payload) as r:
            r.raise_for_status()
            data = await r.json()
            return data["choices"][0]["message"]["content"]

history: dict[int, list] = {}

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    cid = update.effective_chat.id
    text = update.message.text

    if cid not in history:
        history[cid] = [
            {
                "role": "system",
                "content": (
                    "Sizning ismingiz Muxiddin AI. Siz faqat o‘zbek tilida, "
                    "xushmuomala va aniq javob berasiz."
                ),
            }
        ]

    history[cid].append({"role": "user", "content": text})
    history[cid] = history[cid][-12:]

    try:
        reply = await ask_groq(history[cid])
    except Exception:
        reply = await ask_groq(
            [
                {"role": "system", "content": "Faqat o‘zbek tilida javob ber."},
                {"role": "user", "content": text},
            ],
            model="llama3-8b-8192",
        )

    history[cid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def main() -> None:
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    await app.initialize()
    await app.start()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=start_health_server, daemon=True).start()
    asyncio.run(main())
