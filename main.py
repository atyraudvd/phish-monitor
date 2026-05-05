import certstream
import telebot
import threading
import os
from flask import Flask

# --- НАСТРОЙКИ ---
# Токен из твоего BotFather (Снимок экрана 2026-05-05 111215.jpg)
TOKEN = "8759513828:AAH647wLGDflE7ks5iWOBrCxYnWNBzKEwbE"

# Ключевые слова для поиска мошенников
KEYWORDS = ['sber', 'vtb', 'tinkoff', 'binance', 'steam', 'wallet', 'roblox', 'ozon', 'avito']

bot = telebot.TeleBot(TOKEN)
active_users = set()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы сервис не засыпал) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Monitoring is Live!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА КОНСУЛЬТАЦИИ И ПРИВЕТСТВИЯ ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🛡️ **ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ КИБЕРКОНТРОЛЯ!**\n\n"
        "Я — твой персональный консультант по безопасности. Пока я мониторю сеть, "
        "запомни эти правила, чтобы не стать жертвой мошенников:\n\n"
        "1️⃣ **ПРОВЕРЬ ССЫЛКУ:** Если домен похож на известный бренд, но в нем лишние буквы "
        "(например, `sbeerr` вместо `sber`), это **100% мошенничество**.\n\n"
        "2️⃣ **НИКОГДА НЕ ОТПРАВЛЯЙ КОД:** Никакой официальный банк или сервис не попросит "
        "тебя прислать код из SMS. Если просят — это воры!\n\n"
        "3️⃣ **НЕ НАЖИМАЙ:** Даже если на сайте обещают подарки или выплаты. Просто закрой вкладку.\n\n"
        "4️⃣ **НЕ ВВОДИ ДАННЫЕ:** Пароли и номера карт вводятся только в официальных приложениях.\n\n"
        "✅ **Мониторинг запущен!** Как только я найду реальную угрозу, я пришлю тебе алерт."
    )
    # Добавляем пользователя в список рассылки
    active_users.add(message.chat.id)
    # Отправляем инструкцию
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# --- ЛОГИКА МОНИТОРИНГА ДОМЕНОВ ---
def certstream_callback(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']
        for domain in all_domains:
            domain = domain.lower()
            for key in KEYWORDS:
                if key in domain:
                    # Если нашли совпадение, рассылаем уведомление с предупреждением
                    alert_text = (
                        f"🚨 **ОБНАРУЖЕН ПОДОЗРИТЕЛЬНЫЙ ДОМЕН:**\n\n"
                        f"`{domain}`\n\n"
                        f"🛑 **ПРЕДУПРЕЖДЕНИЕ:** Это может быть мошенничество! "
                        f"Не переходи по ссылке и не вводи свои данные.\n\n"
                        f"#фишинг #{key}"
                    )
                    for user_id in active_users:
                        try:
                            bot.send_message(user_id, alert_text, parse_mode='Markdown')
                        except Exception as e:
                            print(f"Ошибка отправки: {e}")

# --- ЗАПУСК ВСЕХ ПРОЦЕССОВ ---
if __name__ == "__main__":
    # 1. Запуск веб-сервера (для Render)
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # 2. Запуск Telegram бота
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(timeout=10, long_polling_timeout=5))
    bot_thread.daemon = True
    bot_thread.start()

    # 3. Запуск сканера Certstream
    print("Система киберконтроля запущена...")
    certstream.listen_for_events(certstream_callback, url='wss://certstream.calidog.io/')
