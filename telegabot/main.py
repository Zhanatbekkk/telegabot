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
from telegram.request import HTTPXRequest

# 🔐 Отключаем SSL-проверку (если на Render потребуется)
httpx_client = httpx.AsyncClient(verify=False)
request = HTTPXRequest(client=httpx_client)

# ✅ ТВОИ ДАННЫЕ
TOKEN = "7566959944:AAEK4jEofM1z7T5JMoK5kYmzTzX_WCY0OCI"  # ← вставь сюда токен бота
CHAT_ID = 6259223196  # ← вставь сюда свой chat_id

# Логирование
logging.basicConfig(level=logging.INFO)


# Получение курса валют с Нацбанка
def get_currency():
    today = datetime.now(pytz.timezone("Asia/Almaty")).strftime("%d.%m.%Y")
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


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📊 Получить курс", callback_data="get_rate")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я бот курса валют.", reply_markup=markup)


# Обработка кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_currency()
    await query.edit_message_text(text=text)


# Автоматическая утренняя отправка
async def send_morning_rate(context: ContextTypes.DEFAULT_TYPE):
    text = get_currency()
    await context.bot.send_message(chat_id=CHAT_ID, text=text)


# Вычисляем сколько секунд до 8:00 по Астане
def get_seconds_until_8_astana():
    tz = pytz.timezone("Asia/Almaty")
    now = datetime.now(tz)
    target = tz.localize(datetime.combine(now.date(), time(8, 0)))
    if now > target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


# Основной запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Запуск авторассылки в 8:00 по Астане
    seconds = get_seconds_until_8_astana()
    app.job_queue.run_repeating(send_morning_rate, interval=86400, first=seconds)

    await app.initialize()
    await app.start()
    print("✅ Бот запущен")
    await app.updater.start_polling()
    await asyncio.Event().wait()


# Запуск
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
