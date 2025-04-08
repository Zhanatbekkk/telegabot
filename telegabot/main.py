import logging
import requests
import pytz
import httpx
from datetime import datetime, time, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import os

# Создаём HTTPX клиент (без использования HTTPXRequest)
client = httpx.AsyncClient(verify=False)

# ТВОИ ДАННЫЕ
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Логируем значения переменных для отладки
print(f"BOT_TOKEN: {BOT_TOKEN}, CHAT_ID: {CHAT_ID}")

# Проверка на None
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")

if CHAT_ID is None:
    raise ValueError("CHAT_ID не задан в переменных окружения")

CHAT_ID = int(CHAT_ID)  # Преобразуем в int только если переменная есть

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём приложение с переданным HTTPX клиентом
app = ApplicationBuilder().token(BOT_TOKEN).build()

def get_currency():
    today = datetime.now(pytz.timezone("Asia/Almaty")).strftime('%d.%m.%Y')
    url = "https://nationalbank.kz/rss/rates_all.xml"
    try:
        response = requests.get(url, timeout=5)
        xml = response.text
    except Exception as e:
        return f"Ошибка при подключении к Нацбанку:\n{e}"

    def extract(tag):
        try:
            start = xml.index(f"<title>{tag}</title>")
            desc_start = xml.index("<description>", start) + 13
            desc_end = xml.index("</description>", desc_start)
            return xml[desc_start:desc_end]
        except ValueError:
            return "нет данных"

    usd = extract("USD")
    eur = extract("EUR")
    rub = extract("RUB")

    return f"📅 Курс на {today} (Астана):\n🇺🇸 USD: {usd} ₸\n🇪🇺 EUR: {eur} ₸\n🇷🇺 RUB: {rub} ₸"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📊 Получить курс", callback_data="get_rate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я бот курса валют.", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_currency()
    await query.edit_message_text(text=text)

async def send_morning_rate(context: ContextTypes.DEFAULT_TYPE):
    text = get_currency()
    await context.bot.send_message(chat_id=CHAT_ID, text=text)

def get_seconds_until_8_astana():
    tz = pytz.timezone("Asia/Almaty")
    now = datetime.now(tz)
    target = tz.localize(datetime.combine(now.date(), time(8, 0)))
    if now > target:
        target += timedelta(days=1)
    return (target - now).total_seconds()

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    seconds = get_seconds_until_8_astana()
    app.job_queue.run_repeating(send_morning_rate, interval=86400, first=seconds)

    await app.initialize()
    await app.start()
    print("✅ Бот запущен")
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
