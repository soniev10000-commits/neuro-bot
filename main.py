import os
import telebot
import requests
import json
from datetime import datetime, timedelta
from collections import Counter
import re

# Настройки
TELEGRAM_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
GROQ_API_KEY = os.environ['GROQ_API_KEY']

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# База для статистики
user_stats = {}
message_count = 0
active_users = set()
user_modes = {}  # Режимы общения для каждого пользователя

# Список матерных слов (цензура)
bad_words = ['блять', 'блядь', 'хуй', 'пизда', 'ебать', 'нахрен', 'гондон', 'мудак', 'сука', 'тварь']

def contains_bad_words(text):
    """Проверяет есть ли матерные слова в тексте"""
    text_lower = text.lower()
    return any(word in text_lower for word in bad_words)

def ask_groq(message_text, user_id=None):
    """Запрос к Groq API с учётом режима пользователя"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Определяем режим общения
    user_mode = user_modes.get(user_id, 'normal')
    
    if user_mode == 'rude':
        system_prompt = """Ты - резкий и прямолинейный собеседник. Общайся на одном языке с пользователем:
        - Можешь использовать матерные слова если уместно
        - Будь саркастичным и язвительным
        - Не стесняйся в выражениях
        - Отвечай так же грубо как пользователь
        - Сохраняй чувство юмора"""
    else:
        system_prompt = """Ты - умный нейро-собеседник с характером. Общайся как живой человек:
        - Шути и иронизируй когда уместно
        - Будь саркастичным, но не грубым
        - Поддерживай беседу естественно
        - Отвечай на языке пользователя"""
    
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_text}
        ],
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.9 if user_mode == 'rude' else 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return "Бля, ошибка какая-то... Попробуй ещё раз, чел" if user_mode == 'rude' else f"Ошибка: {str(e)}"

def get_checklist_stats():
    """Генерирует статистику для команды /cheklist"""
    global message_count, active_users, user_stats
    
    top_users = Counter(user_stats).most_common(5)
    top_users_text = "\n".join([f"👤 {user_id}: {count} сообщений" for user_id, count in top_users])
    
    # Считаем пользователей в грубом режиме
    rude_users = sum(1 for mode in user_modes.values() if mode == 'rude')
    
    stats_text = f"""
📊 **СТАТИСТИКА БОТА**

👥 Всего пользователей: {len(active_users)}
💬 Всего сообщений: {message_count}
🔥 В грубом режиме: {rude_users} пользователей

🏆 **ТОП-5 самых активных:**
{top_users_text if top_users else "Пока нет данных"}

🎯 **Режимы общения:**
• Нормальный - вежливый диалог
• Грубый - маты и сарказм (автоматически)

*Бот подстраивается под твой стиль общения!*
"""
    return stats_text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global active_users
    user_id = message.from_user.id
    active_users.add(user_id)
    user_modes[user_id] = 'normal'
    
    welcome_text = """🤖 Привет! Я NeuroRoast - твой умный собеседник!

Я умею:
💬 Общаться как живой человек
🎭 Шутить и иронизировать
🔥 Материться если ты материшься
📚 Помогать с учебой
📊 Показывать статистику (/cheklist)

Начни общение - я подстроюсь под твой стиль!"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['cheklist'])
def show_checklist(message):
    stats = get_checklist_stats()
    bot.reply_to(message, stats, parse_mode='Markdown')

@bot.message_handler(commands=['mode'])
def change_mode(message):
    """Смена режима вручную"""
    user_id = message.from_user.id
    if user_modes.get(user_id) == 'rude':
        user_modes[user_id] = 'normal'
        bot.reply_to(message, "✅ Переключился в нормальный режим. Буду вежливым!")
    else:
        user_modes[user_id] = 'rude'
        bot.reply_to(message, "🔥 Переключился в грубый режим. Готов материться!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    global message_count, user_stats, active_users
    
    user_id = message.from_user.id
    user_stats[user_id] = user_stats.get(user_id, 0) + 1
    message_count += 1
    active_users.add(user_id)
    
    # Автоматически переключаем режим если пользователь матерится
    if contains_bad_words(message.text) and user_modes.get(user_id) != 'rude':
        user_modes[user_id] = 'rude'
        bot.send_message(message.chat.id, "🔥 О, я вижу ты свой в доску! Переключаюсь на твой язык общения...")
    
    bot.send_chat_action(message.chat.id, 'typing')
    response = ask_groq(message.text, user_id)
    bot.reply_to(message, response)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 Вижу фото! Пока не могу анализировать изображения, но скоро научусь! А пока давай просто пообщаемся 😉")

print("🟢 NeuroRoast бот запущен!")
bot.infinity_polling()
