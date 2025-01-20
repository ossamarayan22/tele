import requests
import time

# إعداد التوكن ومعرفات الحساسة
TOKEN = "7502253350:AAGTxj1mCOdWHm7fTZm3_RgzTxpvgq7bmSw"
CHAT_ID = "5820030195"
BLM_ID = "blombard"
alerts = {}  # تخزين التنبيهات حسب معرف الدردشة

last_update_id = None

# إرسال إشعار عبر تيليجرام
def send_telegram_notification(message, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Telegram notification error: {e}")

# الحصول على بيانات العملة
def get_coin_details(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

# إرسال التفاصيل المختصرة للعملة BLM
def send_coin_details(coin_id):
    data = get_coin_details(coin_id)
    if not data:
        send_telegram_notification(f"⚠️ Unable to fetch details for `{coin_id}`.")
        return

    if 'market_data' in data:
        # بيانات عامة
        name = data.get("name", "Unknown")
        symbol = data.get("symbol", "N/A").upper()
        current_price = data['market_data']['current_price'].get('usd', 'N/A')
        market_cap = data['market_data']['market_cap'].get('usd', 'N/A')
        volume = data['market_data']['total_volume'].get('usd', 'N/A')

        # بيانات موسعة
        all_time_high = data['market_data']['ath'].get('usd', 'N/A')
        ath_date = data['market_data']['ath_date'].get('usd', 'N/A')
        all_time_low = data['market_data']['atl'].get('usd', 'N/A')
        atl_date = data['market_data']['atl_date'].get('usd', 'N/A')
        volatility = data['market_data'].get('price_change_percentage_24h', 'N/A')
        max_supply = data.get("max_supply", 'N/A')
        total_supply = data.get("total_supply", 'N/A')
        circulating_supply = data['market_data'].get('circulating_supply', 'N/A')
        liquidity_score = data.get("liquidity_score", 'N/A')
        market_dominance = data['market_data'].get('market_cap_percentage', {}).get('usd', 'N/A')
        roi = data.get('roi', {}).get('percentage', 'N/A')

        # تحليل مبدأي لتوصيات البيع
        if volatility > 5:
            recommendation = "⚠️ High volatility! Consider monitoring closely."
        elif current_price > all_time_high * 0.9:
            recommendation = "✅ Good time to sell (near ATH)."
        else:
            recommendation = "📈 Hold for better market conditions."

        # بناء الرسالة
        message = f"""
*Details for {name} ({symbol}):*
- 💵 *Current Price*: ${current_price}
- 📈 *Market Cap*: ${market_cap}
- 🔄 *24h Volatility*: {volatility}%
- 🔝 *All-Time High*: ${all_time_high} (Date: {ath_date})
- 📉 *All-Time Low*: ${all_time_low} (Date: {atl_date})
- 📊 *Trading Volume*: ${volume}
- 🪙 *Circulating Supply*: {circulating_supply}
- 🏦 *Max Supply*: {max_supply}
- 🔢 *Total Supply*: {total_supply}
- 💧 *Liquidity Score*: {liquidity_score}
- 🌍 *Market Dominance*: {market_dominance}%
- 📊 *ROI*: {roi}%

💡 *Recommendation*: {recommendation}
"""
        send_telegram_notification(message)
    else:
        send_telegram_notification(f"⚠️ No market data available for `{coin_id}`.")

# التحقق من إدراج العملة في منصات التداول
def send_market_availability(coin_id):
    data = get_coin_details(coin_id)
    if not data or 'tickers' not in data:
        send_telegram_notification(f"⚠️ Unable to fetch market data for `{coin_id}`.")
        return

    markets = data['tickers']
    if not markets:
        send_telegram_notification(f"⚠️ `{coin_id}` is not listed on any exchanges.")
        return

    exchanges = {market['market']['name'] for market in markets}
    exchange_list = "\n".join(f"- {exchange}" for exchange in exchanges)
    message = f"""
*{coin_id.capitalize()} is listed on the following exchanges:*
{exchange_list}
"""
    send_telegram_notification(message)

# تعيين تنبيه للأسعار
def set_price_alert(chat_id, target_price):
    alerts[chat_id] = target_price
    send_telegram_notification(f"✅ Alert set for price: ${target_price}")

# التحقق من التنبيهات
def check_alerts():
    data = get_coin_details(BLM_ID)
    if not data or 'market_data' not in data:
        return

    current_price = data['market_data']['current_price'].get('usd', None)
    if not current_price:
        return

    for chat_id, target_price in alerts.items():
        if current_price >= target_price:
            send_telegram_notification(
                f"🚨 Alert: Blombard price reached ${current_price} (Target: ${target_price})!"
            )
            del alerts[chat_id]

# التحقق من تغير السعر بشكل كبير
def check_price_fluctuations(coin_id, threshold=10):
    data = get_coin_details(coin_id)
    if not data or 'market_data' not in data:
        return

    price_change = data['market_data'].get('price_change_percentage_24h', 0)
    if abs(price_change) >= threshold:
        send_telegram_notification(
            f"🚨 *Significant Price Change Alert for {coin_id.capitalize()}!*\n"
            f"- 24h Price Change: {price_change}%\n"
            f"Threshold: {threshold}%"
        )

# معالجة الأوامر
def handle_command(command, chat_id):
    args = command.split()
    if args[0] == "/details":
        send_coin_details(BLM_ID)
    elif args[0] == "/markets":
        send_market_availability(BLM_ID)
    elif args[0] == "/setalert" and len(args) > 1:
        try:
            target_price = float(args[1])
            set_price_alert(chat_id, target_price)
        except ValueError:
            send_telegram_notification("⚠️ Invalid price value.")
    elif args[0] == "/alerts":
        send_telegram_notification(f"Active alerts: {alerts}")
    elif args[0] == "/help":
        send_telegram_notification("""
*Available Commands:*
- `/details` : Get details for Blombard.
- `/markets` : Check which exchanges list Blombard.
- `/setalert <price>` : Set a price alert.
- `/alerts` : View active alerts.
- `/help` : Display this help message.
""")
    else:
        send_telegram_notification("❓ Unknown command. Use `/help` for available commands.")

# التحقق من الأوامر
def check_for_updates():
    global last_update_id

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        updates = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching updates: {e}")
        return

    if "result" in updates:
        for update in updates['result']:
            update_id = update['update_id']
            if last_update_id is None or update_id > last_update_id:
                last_update_id = update_id

                if 'message' in update and 'text' in update['message']:
                    command = update['message']['text'].lower()
                    chat_id = update['message']['chat']['id']
                    handle_command(command, chat_id)

# بدء المراقبة
def monitor_daily():
    print("Bot is running...")
    while True:
        check_for_updates()
        check_alerts()
        check_price_fluctuations(BLM_ID, threshold=10)  # فحص تغيرات السعر
        time.sleep(120)  # تحقق كل 5 ثوانٍ

if __name__ == "__main__":
    monitor_daily()
