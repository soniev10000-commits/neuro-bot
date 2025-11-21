import os
import telebot
import requests

TELEGRAM_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
GROQ_API_KEY = os.environ['GROQ_API_KEY']

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_groq(message_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """Ты - умный нейро-собеседник. Отвечай на языке пользователя. 
    Будь добрым на личные темы, серьезным на важные, и саркастичным когда уместно."""
    
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_text}
        ],
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Ошибка: {str(e)}"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = ask_groq(message.text)
    bot.reply_to(message, response)

print("🟢 Умный нейро-бот запущен!")
bot.infinity_polling()
