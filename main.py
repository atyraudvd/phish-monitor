import certstream
import telebot
import threading

# --- ВСТАВЬ СВОЙ ТОКЕН НИЖЕ ---
TOKEN = 8759513828:AAH647wLGDflE7ks5iWOBrCxYnWNBzKEwbE
# Слова, на которые бот будет реагировать
KEYWORDS = ['sber', 'vtb', 'tinkoff', 'binance', 'steam', 'wallet', 'roblox']

bot = telebot.TeleBot(TOKEN)
active_users = set()

@bot.message_handler(commands=['start'])
def start(message):
    active_users.add(message.chat.id)
    bot.send_message(message.chat.id, "🔍 Мониторинг запущен! Как только я увижу подозрительный сайт в мировом потоке, я пришлю ссылку.")

def callback(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']
        for domain in all_domains:
            domain = domain.lower()
            for key in KEYWORDS:
                if key in domain:
                    for user_id in active_users:
                        try:
                            bot.send_message(user_id, f"🚨 ОБНАРУЖЕН ПОДОЗРИТЕЛЬНЫЙ САЙТ:\n`{domain}`")
                        except: pass

# Запуск бота в отдельном потоке
threading.Thread(target=bot.infinity_polling).start()
# Запуск сканера интернета
certstream.listen_for_events(callback, url='wss://certstream.calidog.io/')
