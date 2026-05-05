import certstream
import telebot
import threading
import os
from flask import Flask

# --- НАСТРОЙКИ ---
TOKEN = "8759513828:AAH647wLGDflE7ks5iWOBrCxYnWNBzKEwbE"
KEYWORDS = ['sber', 'vtb', 'tinkoff', 'binance', 'steam', 'wallet', 'roblox', 'ozon', 'avito']

# Список официальных сайтов, чтобы бот не ругался на настоящие ресурсы
OFFICIAL_DOMAINS = ['sberbank.ru', 'sber.ru', 'tinkoff.ru', 'vtb.ru', 'binance.com', 'roblox.com', 'ozon.ru', 'avito.ru', 'steamcommunity.com']

bot = telebot.TeleBot(TOKEN)
active_users = set()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Monitoring is Live!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА ПРИВЕТСТВИЯ ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🛡️ **ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ КИБЕРКОНТРОЛЯ!**\n\n"
        "Я — твой персональный консультант. Запомни эти правила:\n\n"
        "1️⃣ **ПРОВЕРЬ ССЫЛКУ:** Если домен похож на бренд, но в нем лишние буквы — это **100% мошенничество**.\n"
        "2️⃣ **НИКОГДА НЕ ОТПРАВЛЯЙ КОД:** Ни один банк не попросит код из SMS. Если просят — это воры!\n"
        "3️⃣ **НЕ НАЖИМАЙ:** Даже если обещают призы. Просто закрой вкладку.\n\n"
        "✅ **МОНИТОРИНГ ЗАПУЩЕН!**\n"
        "Ты можешь прислать мне любую ссылку, и я проверю её прямо сейчас!"
    )
    active_users.add(message.chat.id)
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- РУЧНАЯ ПРОВЕРКА ССЫЛОК (КОТОРЫЕ ТЫ ПРИСЫЛАЕШЬ) ---
@bot.message_handler(func=lambda message: True)
def manual_check(message):
    user_text = message.text.lower()
    
    # 1. Сначала ищем ключевое слово (например, sber)
    found_key = None
    for key in KEYWORDS:
        if key in user_text:
            found_key = key
            break
    
    if found_key:
        # 2. Если нашли слово, проверяем, не официальный ли это сайт
        is_official = any(official in user_text for official in OFFICIAL_DOMAINS)
        
        if is_official:
            bot.reply_to(message, f"✅ **ВСЕ ОК!**\n\nАдрес `{user_text}` похож на официальный ресурс. Здесь безопасно.")
        else:
            bot.reply_to(message, f"⚠️ **ПОДОЗРИТЕЛЬНО!**\n\nВ ссылке есть слово `{found_key}`, но это НЕ официальный сайт банка. \n\n🛑 **ВНИМАНИЕ:** Это может быть ловушка! Ничего не нажимай и не вводи свои данные.")
    else:
        # 3. Если опасных слов вообще нет
        bot.reply_to(message, "🔍 Я не нашел известных мне угроз в этой ссылке. Но всегда будь осторожна!")

# --- АВТО-МОНИТОРИНГ (CERTSTREAM) ---
def certstream_callback(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']
        for domain in all_domains:
            domain = domain.lower()
            for key in KEYWORDS:
                if key in domain:
                    alert_text = (
                        f"🚨 **ОБНАРУЖЕН ПОДОЗРИТЕЛЬНЫЙ ДОМЕН:**\n\n"
                        f"`{domain}`\n\n"
                        f"🛑 **МОШЕННИЧЕСТВО!** Не переходи по ссылке и не вводи данные.\n\n"
                        f"#фишинг #{key}"
                    )
                    for user_id in active_users:
                        try:
                            bot.send_message(user_id, alert_text, parse_mode='Markdown')
                        except:
                            pass

# --- ЗАПУСК ---
if __name__ == "__main__":
    # Веб-сервер
    threading.Thread(target=run_web, daemon=True).start()
    # Бот
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20), daemon=True).start()
    # Сканер
    print("Система запущена...")
    certstream.listen_for_events(certstream_callback, url='wss://certstream.calidog.io/') 
