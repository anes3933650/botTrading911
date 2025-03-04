import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd

# 🔹 استبدل هذه القيم بمعلوماتك
BINANCE_API_KEY = "kzrOKJK6QSd5CYOqUhzdicScUtYOGLyaG7phuHEa5YzWqSebNp04Pxu7Tg8a4eWU"
BINANCE_API_SECRET = "vDQzTQKisF2OfX8f2NXUMe96lwj70HUzUsh12V48hr31o5JSqOJ5gW8v9So6edbt"
TELEGRAM_BOT_TOKEN = "7941278728:AAG-NJyw7gnCEywZSzWx1Q03TttBrMp8cHI"
CHAT_ID = "7474513301"

def send_telegram_message(message):
    """إرسال رسالة إلى تليغرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=data)
        response_json = response.json()

        if response_json.get("ok"):
            print(f"✅ تم إرسال الرسالة: {message}")
        else:
            print(f"❌ خطأ أثناء إرسال الرسالة: {response_json}")

    except Exception as e:
        print(f"❌ استثناء أثناء إرسال رسالة تليغرام: {e}")

def get_price(client, symbol="BTCUSDT"):
    """جلب السعر الحالي للعملة المحددة"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except BinanceAPIException as e:
        print(f"⚠️ خطأ عند جلب السعر: {e}")
        return None

def get_candlestick_data(client, symbol="BTCUSDT", interval="1h", limit=50):
    """جلب بيانات الشموع لعملة معينة"""
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(candles, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "close_time", 
            "quote_asset_volume", "number_of_trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except BinanceAPIException as e:
        print(f"⚠️ خطأ عند جلب بيانات الشموع: {e}")
        return None

import threading
import time
from price_alerts import set_price_alerts
from technical_indicators import analyze_market, format_trading_alert

def send_market_analysis(client, symbol="BTCUSDT", interval="1h", recommendation_number=None):
    """إرسال تحليل السوق عبر تيليغرام"""
    analysis, _ = analyze_market(client, symbol, interval)
    if analysis:
        # إذا لم يتم تحديد رقم التوصية، استخدم رقمًا عشوائيًا بين 1 و 100
        if recommendation_number is None:
            import random
            recommendation_number = random.randint(1, 100)
        
        # استخدام التنسيق الجديد للتنبيه
        message = format_trading_alert(analysis, recommendation_number)
        
        send_telegram_message(message)
        return analysis
    return None

def scheduled_analysis(client, symbols=None, interval="4h"):
    """تنفيذ تحليل سوق مجدول"""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "LPTUSDT"]
    
    import random
    recommendation_counter = random.randint(50, 100)  # بدء من رقم عشوائي
    
    try:
        while True:
            for symbol in symbols:
                recommendation_counter += 1
                send_market_analysis(client, symbol, interval, recommendation_counter)
                time.sleep(5)  # انتظار بين كل تحليل
            
            # انتظار 4 ساعات قبل التحليل التالي
            time.sleep(4 * 60 * 60)
    except Exception as e:
        send_telegram_message(f"❌ خطأ في التحليل المجدول: {e}")

def main():
    print("🚀 بدء تشغيل البوت...")
    send_telegram_message("🚀 البوت بدأ العمل!")

    try:
        # 🔹 تهيئة عميل Binance
        client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)

        # 🔹 الحصول على وقت الخادم
        server_time = client.get_server_time()
        print(f"🕒 وقت الخادم: {server_time}")

        # 🔹 جلب السعر الحالي لعدة عملات
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for symbol in symbols:
            price = get_price(client, symbol)
            if price:
                print(f"📊 السعر الحالي لـ {symbol}: {price}")
                send_telegram_message(f"📊 السعر الحالي لـ {symbol}: {price} USDT")

        # 🔹 إرسال تحليل فني أولي
        for symbol in symbols:
            send_market_analysis(client, symbol)

        # 🔹 بدء مراقبة الأسعار في ثريد منفصل
        price_alert_symbols = {
            "BTCUSDT": {"upper": 70000, "lower": 60000, "percent_change": 2.5},
            "ETHUSDT": {"upper": 4000, "lower": 3000, "percent_change": 3.0},
            "BNBUSDT": {"upper": 600, "lower": 500, "percent_change": 4.0}
        }
        
        price_alert_thread = threading.Thread(
            target=set_price_alerts,
            args=(client, send_telegram_message, price_alert_symbols),
            daemon=True
        )
        price_alert_thread.start()
        
        # 🔹 بدء تحليل السوق المجدول في ثريد منفصل
        analysis_thread = threading.Thread(
            target=scheduled_analysis,
            args=(client, symbols),
            daemon=True
        )
        analysis_thread.start()
        
        # 🔹 إرسال إشعار عند النجاح
        send_telegram_message("✅ البوت يعمل بشكل سليم! 🚀\n"
                             "- تم تفعيل مراقبة الأسعار ✓\n"
                             "- تم تفعيل التحليل الفني المجدول ✓")
        
        # 🔹 إبقاء الثريد الرئيسي نشطًا
        while True:
            time.sleep(60)
            
    except BinanceAPIException as e:
        print(f"❌ خطأ من Binance API: {e}")
        send_telegram_message(f"⚠️ خطأ في API: {e}")
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت يدويًا")
        send_telegram_message("🛑 تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        send_telegram_message(f"⚠️ خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()
