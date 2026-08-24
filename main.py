```python
import os
import sqlite3
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from groq import Groq

logging.basicConfig(level=logging.INFO)

TELEGRAMTOKEN = os.environ.get("TELEGRAMTOKEN")
GROQAPIKEY = os.environ.get("GROQAPIKEY")
WEBHOOKURL = os.environ.get("WEBHOOKURL")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN topilmadi")
if not GROQAPIKEY:
    raise ValueError("GROQAPIKEY topilmadi")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL topilmadi")

client = Groq(apikey=GROQAPI_KEY)
app = Flask(_name_)
DB_NAME = "memory.db"

SYSTEM_PROMPT = """
Sen Telegram guruhida ishlaydigan o‘zbekcha aqlli botsan.
Doim faqat o‘zbek tilida javob ber.
Javoblaring tabiiy, samimiy, qisqa va foydali bo‘lsin.
Odamga o‘xshab yoz.
Suhbat kontekstini eslab qol.
Agar foydalanuvchi savol bersa aniq javob ber.
Agar foydalanuvchi oddiy gap yozsa samimiy suhbat qur.
"""

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

def savemessage(chatid, user_id, username, role, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (chatid, userid, username, role, content) VALUES (?, ?, ?, ?, ?)",
        (chatid, userid, username, role, content)
    )
    conn.commit()
    conn.close()

def getmemory(chatid, limit=20):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
        (chat_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    rows.reverse()
    return [{"role": role, "content": content} for role, content in rows]

async def handlemessage(update: Update, context: ContextTypes.DEFAULTTYPE):
    if not update.message or not update.message.text:
        return

    message = update.message
    text = message.text.strip()
    chatid = message.chatid
    user = message.from_user
    botusername = (await context.bot.getme()).username

    is_group = message.chat.type in ["group", "supergroup"]
    should_reply = True

    if is_group:
        should_reply = False

        if message.replytomessage and message.replytomessage.from_user:
            if message.replytomessage.fromuser.username == botusername:
                should_reply = True

        if f"@{bot_username}" in text:
            should_reply = True

    if not should_reply:
        return

    cleantext = text.replace(f"@{botusername}", "").strip()

    save_message(
        chatid=chatid,
        user_id=user.id,
        username=user.username or user.first_name or "user",
        role="user",
        content=clean_text
    )

    memory = getmemory(chatid, limit=20)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + memory

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        reply = f"Xatolik: {str(e)}"

    save_message(
        chatid=chatid,
        user_id=0,
        username="bot",
        role="assistant",
        content=reply
    )

    await message.reply_text(reply)

telegramapp = Application.builder().token(TELEGRAMTOKEN).build()
telegramapp.addhandler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/", methods=["GET"])
def home():
    return "Bot ishlayapti"  @app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.dejson(request.getjson(force=True), telegram_app.bot)
    telegramapp.updatequeue.put_nowait(update)
    return "ok"

async def startup():
    init_db()
    await telegram_app.initialize()
    await telegram_app.start()
    await telegramapp.bot.setwebhook(url=f"{WEBHOOKURL}/{TELEGRAMTOKEN}")

if _name_ == "_main_":
    loop = asyncio.geteventloop()
    loop.rununtilcomplete(startup())
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```
