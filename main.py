import certstream
import telebot
import threading
import os
from flask import Flask

# --- НАСТРОЙКИ ---
# Вставь свой токен внутри кавычек
TOKEN = "8759513828:AAH647wLGDflE7ks5iWOBrCxYnWNBzKEwbE"
# Ключевые слова для поиска (можно дополнять)
KEYWORDS = ['sber', 'vtb', 'tinkoff', 'binance', 'steam', 'wallet', 'roblox', 'ozon', 'avito']

bot = telebot.TeleBot(TOKEN)
active_users = set()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы не было ошибки Status 2) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Monitoring is Live!", 200

def run_web():
    # Render сам назначит порт через переменную окружения
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ЛОГИКА МОНИТОРИНГА ---
@bot.message_handler(commands=['start'])
def start_command(message):
    active_users.add(message.chat.id)
    bot.send_message(message.chat.id, "✅ **Мониторинг запущен!**\n\nЯ сканирую новые домены в реальном времени. Если найду совпадение с твоими ключевыми словами — сразу пришлю уведомление.")

def certstream_callback(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']
        for domain in all_domains:
            domain = domain.lower()
            for key in KEYWORDS:
                if key in domain:
                    # Если нашли совпадение, рассылаем всем пользователям бота
                    for user_id in active_users:
                        try:
                            bot.send_message(user_id, f"🚨 **ОБНАРУЖЕН ПОДОЗРИТЕЛЬНЫЙ ДОМЕН:**\n\n`{domain}`\n\n#фишинг #{key}")
                        except Exception as e:
                            print(f"Ошибка отправки: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запускаем веб-заглушку в отдельном потоке
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # 2. Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=bot.infinity_polling)
    bot_thread.daemon = True
    bot_thread.start()

    # 3. Запускаем сканер (основной процесс)
    print("Сканирование запущено...")
    certstream.listen_for_events(certstream_callback, url='wss://certstream.calidog.io/')
