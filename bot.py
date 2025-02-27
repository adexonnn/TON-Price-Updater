import asyncio
import requests
from telegram import Bot
from configparser import ConfigParser
from utils import read_previous_price, save_current_price, format_market_cap
import logging

config = ConfigParser()
config.read('config.ini')

DYOR_API_URL = config.get('settings', 'DYOR_API_URL')
CONTRACT_ADDRESS = DYOR_API_URL.split("YOUR-CONTRACT-HERE")[0]
TELEGRAM_TOKEN = config.get('settings', 'TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = config.get('settings', 'TELEGRAM_CHAT_ID')
DELAY = config.getint('settings', 'DELAY')
RUB_EXCHANGE_RATE = config.getfloat('settings', 'RUB_EXCHANGE_RATE')
TON_EXCHANGE_RATE = config.getfloat('settings', 'TON_EXCHANGE_RATE')
PRICE_FILE = config.get('settings', 'PRICE_FILE')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_token_data():
    try:
        api_url = DYOR_API_URL.replace("YOUR-CONTRACT-HERE", CONTRACT_ADDRESS)
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            price_usd_value = data.get("details", {}).get("priceUsd", {}).get("value")
            fdv_value = data.get("details", {}).get("fdmc", {}).get("value")

            if price_usd_value and fdv_value:
                price = round(float(price_usd_value) / 1_000_000, 5)
                fdv = format_market_cap(float(fdv_value) / 1_000_000)
                price_native = round(price / TON_EXCHANGE_RATE, 5)
                return price, fdv, price_native

        logging.error(f"Ошибка API: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"Ошибка соединения: {e}")
    return None, None, None

async def send_to_telegram(bot, price, fdv, price_native):
    if price is None:
        logging.error("Ошибка: не удалось получить данные о цене.")
        return
    
    previous_price = read_previous_price(PRICE_FILE)
    price_rub = round(price * RUB_EXCHANGE_RATE, 4)
    price_change = ""
    
    if previous_price is not None and previous_price != price:
        change_percent = round(((price - previous_price) / previous_price) * 100, 2)
        change_icon = "🟢" if change_percent > 0 else "🔴"
        alert_icon = "❗️" if abs(change_percent) > 5 else ""
        price_change = f"\n\n⚙️ Изменение: {alert_icon}{change_percent}% {change_icon}"

    save_current_price(PRICE_FILE, price)

    message = (f"💰 Цена токена: {price} USD₮ ≈ {price_rub} RUB\n"
               f"💎 Цена в TON: {price_native} TON\n"
               f"⛽️ Капитализация: {fdv} USD₮"
               f"{price_change}\n\n"
               f"[График](https://yourlink.here) | "
               f"[Купить](https://yourlink.here) | "
               f"[Чат](https://yourlink.here)")

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    
    while True:
        try:
            price, fdv, price_native = get_token_data()
            if price is not None:
                await send_to_telegram(bot, price, fdv, price_native)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
        
        await asyncio.sleep(DELAY)

if __name__ == "__main__":
    asyncio.run(main())
