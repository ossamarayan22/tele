import requests
import time

TOKEN = "7502253350:AAGTxj1mCOdWHm7fTZm3_RgzTxpvgq7bmSw"
CHAT_ID = "5820030195"
BLM_ID = "blombard"

# حفظ آخر update_id
last_update_id = None

# إرسال إشعار عبر تيليجرام
def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    response = requests.get(url)
    return response.json()

# الحصول على جميع بيانات العملة من CoinGecko
def get_blm_details():
    url = f"https://api.coingecko.com/api/v3/coins/{BLM_ID}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

# إرسال تفاصيل العملة
def send_blm_details():
    data = get_blm_details()
    if isinstance(data, str):  # إذا كانت البيانات عبارة عن رسالة خطأ
        send_telegram_notification(data)
    elif 'market_data' in data:
        current_price = data['market_data']['current_price'].get('usd', 'N/A')
        market_cap = data['market_data']['market_cap'].get('usd', 'N/A')
        volume = data['market_data']['total_volume'].get('usd', 'N/A')
        price_change = data['market_data'].get('price_change_percentage_24h', 'N/A')
        circulating_supply = data['market_data'].get('circulating_supply', 'N/A')

        message = f"""
        Here are the current details for Blombard:
        - Price: ${current_price}
        - Market Cap: ${market_cap}
        - 24h Price Change: {price_change}%
        - Trading Volume: ${volume}
        - Circulating Supply: {circulating_supply}
        """
        send_telegram_notification(message)
    else:
        send_telegram_notification("Unable to fetch Blombard details.")

# التحقق من الأوامر الواردة
def check_for_updates():
    global last_update_id

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url)
    updates = response.json()

    if "result" in updates:
        for update in updates['result']:
            update_id = update['update_id']
            if last_update_id is None or update_id > last_update_id:
                last_update_id = update_id  # تحديث آخر update_id

                if 'message' in update and 'text' in update['message']:
                    text = update['message']['text']
                    print(f"Received command: {text}")  # رسالة تصحيحية
                    if text.lower() == "/blm":
                        send_blm_details()

# المراقبة اليومية
def monitor_daily():
    while True:
        check_for_updates()
        time.sleep(5)  # تحقق كل 5 ثوانٍ

# بدء المراقبة
monitor_daily()
