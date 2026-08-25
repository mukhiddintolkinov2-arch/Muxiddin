import os
import telebot
from groq import Groq

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

user_context = {}

def get_groq_response(user_id, user_name, text):
    if user_id not in user_context:
        user_context[user_id] = [
            {"role": "system", "content": f"Sen Telegram guruhdagi do'stona va aqlli yordamchisan. Foydalanuvchining ismi: {user_name}. Faqat O'zbek tilida yoz. Suhbatdoshni tanib, uning oldingi gaplarini eslab qol."}
        ]
    
    user_context[user_id].append({"role": "user", "content": text})

    if len(user_context[user_id]) > 11:
        user_context[user_id] = [user_context[user_id][0]] + user_context[user_id][-10:]

    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=user_context[user_id],
            temperature=0.7,
            max_tokens=500
        )
        
        bot_reply = completion.choices[0].message.content
        user_context[user_id].append({"role": "assistant", "content": bot_reply})
        
        return bot_reply
    except Exception as e:
        print(f"Groq xatosi: {e}")
        return "Kechirasiz, hozir biroz bandman. Keyinroq yana yozib ko'ring!"

@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    text = message.text

    bot.send_chat_action(message.chat.id, 'typing')
    reply_text = get_groq_response(user_id, user_name, text)
    bot.reply_to(message, reply_text)

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
