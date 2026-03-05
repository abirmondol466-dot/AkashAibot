import pandas as pd
import requests
import time
import os
import json
import asyncio
from datetime import datetime
from telegram import Bot
from flask import Flask
from threading import Thread

# --- [১. সার্ভার সচল রাখার ওয়েব ইঞ্জিন] ---
app = Flask('')

@app.route('/')
def home():
    return "Gemini AI Master V57 is Active and Analyzing All Assets..."

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- [২. আপনার ব্যক্তিগত তথ্য] ---
TELEGRAM_TOKEN = "8783920040:AAHA088qE8eS4fPFfHaH9rxWgZmNK8GOsmo"
CHAT_ID = "8568914588"
bot = Bot(token=TELEGRAM_TOKEN)

# --- [৩. রেজাল্ট চেকার ফাংশন] ---
async def check_and_send_result(name, sym, entry_price, signal_type, delay_seconds, label):
    await asyncio.sleep(delay_seconds)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()['chart']['result'][0]['indicators']['quote'][0]
        current_price = data['close'][-1]
        
        result_icon = ""
        if signal_type == "CALL":
            result_icon = "✅ WIN" if current_price > entry_price else "❌ LOSS"
        else:
            result_icon = "✅ WIN" if current_price < entry_price else "❌ LOSS"
        
        if current_price == entry_price: result_icon = "➖ DRAW"

        result_msg = (f"📊 *SIGNAL RESULT ({label})*\n"
                      f"Asset: {name}\n"
                      f"Entry: {entry_price:.5f} -> Now: {current_price:.5f}\n"
                      f"Result: *{result_icon}*")
        
        await bot.send_message(chat_id=CHAT_ID, text=result_msg, parse_mode='Markdown')
    except:
        pass

# --- [৪. ডেল্টা রিভার এনালাইসিস ইঞ্জিন] ---
def analyze_market_v57(df):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    l_wick = min(last['open'], last['close']) - last['low']
    u_wick = last['high'] - max(last['open'], last['close'])
    c_range = last['high'] - last['low']
    
    if c_range == 0: return None
    
    delta = ((last['close'] - last['low']) - (last['high'] - last['close'])) / c_range * 100
    avg_vol = df['volume'].tail(20).mean()
    is_big_money = last['volume'] > (avg_vol * 1.5) # কনফিডেন্স ঠিক রেখে সেন্সিটিভিটি সামান্য বাড়ানো হয়েছে
    
    ema20 = df['close'].ewm(span=20).mean().iloc[-1]
    trend = "UP" if last['close'] > ema20 else "DOWN"
    poc = (last['high'] + last['low'] + last['close']) / 3
    
    stars = 0
    confs = []
    
    if (delta > 50 and trend == "UP") or (delta < -50 and trend == "DOWN"):
        stars += 1; confs.append("Trend Sync 🌊")
    if is_big_money:
        stars += 1; confs.append("Whale Entry 🔥")
    if l_wick > (body * 1.2) or u_wick > (body * 1.2):
        stars += 1; confs.append("Liquidity Grab ✅")
    if abs(delta) > 75:
        stars += 1; confs.append("Extreme Delta ⚡")
    if (delta > 0 and poc < last['close']) or (delta < 0 and poc > last['close']):
        stars += 1; confs.append("POC Cluster 🎯")

    return {"stars": stars, "delta": delta, "confs": confs, "price": last['close'], "type": "CALL" if delta > 0 else "PUT"}

# --- [৫. একক অ্যাসেট স্ক্যানার] ---
async def scan_asset(name, sym, notified_trades):
    while True:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            df = pd.DataFrame(r.json()['chart']['result'][0]['indicators']['quote'][0]).dropna()
            
            if not df.empty and len(df) > 30:
                res = analyze_market_v57(df)
                if res and res['stars'] >= 3:
                    # প্রতিটি অ্যাসেটের জন্য আলাদা টাইম গ্যাপ মেনটেইন হবে
                    if name not in notified_trades or (time.time() - notified_trades[name]) > 120:
                        star_str = "⭐" * res['stars']
                        sig_icon = "🟢" if res['type'] == "CALL" else "🔴"
                        conf_text = "\n".join([f"- {c}" for c in res['confs']])
                        
                        msg = (f"💎 *INSTITUTIONAL SIGNAL*\n"
                               f"Asset: {name} | {res['type']} {sig_icon}\n"
                               f"Strength: {star_str} ({res['stars']}/5)\n\n"
                               f"📈 *Confirmations:*\n{conf_text}\n\n"
                               f"Price: {res['price']:.5f} | Time: 1m")
                        
                        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                        notified_trades[name] = time.time()

                        asyncio.create_task(check_and_send_result(name, sym, res['price'], res['type'], 60, "1m Expiry"))
                        asyncio.create_task(check_and_send_result(name, sym, res['price'], res['type'], 180, "3m Expiry"))
        except:
            pass
        await asyncio.sleep(10) # প্রতি ১০ সেকেন্ড পর পর একটি নির্দিষ্ট অ্যাসেট রিফ্রেশ হবে

# --- [৬. মেইন ইঞ্জিন] ---
async def start_bot_engine():
    print("🚀 Gemini AI Core V57 is scanning all assets...")
    assets = {
        "EUR/USD": "EURUSD=X", 
        "GBP/USD": "GBPUSD=X", 
        "USD/JPY": "USDJPY=X", 
        "AUD/USD": "AUDUSD=X",
        "USD/CHF": "USDCHF=X",
        "USD/CAD": "USDCAD=X"
    }
    notified_trades = {}
    
    # সব অ্যাসেটকে একসাথে স্ক্যান করার জন্য টাস্ক তৈরি
    tasks = [scan_asset(name, sym, notified_trades) for name, sym in assets.items()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(start_bot_engine())        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()['chart']['result'][0]['indicators']['quote'][0]
        current_price = data['close'][-1]
        
        result_icon = ""
        if signal_type == "CALL":
            result_icon = "✅ WIN" if current_price > entry_price else "❌ LOSS"
        else:
            result_icon = "✅ WIN" if current_price < entry_price else "❌ LOSS"
        
        if current_price == entry_price: result_icon = "➖ DRAW"

        result_msg = (f"📊 *SIGNAL RESULT ({label})*\n"
                      f"Asset: {name}\n"
                      f"Entry: {entry_price:.5f} -> Now: {current_price:.5f}\n"
                      f"Result: *{result_icon}*")
        
        await bot.send_message(chat_id=CHAT_ID, text=result_msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Error checking result: {e}")

# --- [৪. ডেল্টা রিভার ও স্মার্ট মানি এনালাইসিস ইঞ্জিন] ---
def analyze_market_v57(df):
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    l_wick = min(last['open'], last['close']) - last['low']
    u_wick = last['high'] - max(last['open'], last['close'])
    c_range = last['high'] - last['low']
    
    if c_range == 0: return None
    
    delta = ((last['close'] - last['low']) - (last['high'] - last['close'])) / c_range * 100
    avg_vol = df['volume'].tail(20).mean()
    is_big_money = last['volume'] > (avg_vol * 1.8)
    
    ema20 = df['close'].ewm(span=20).mean().iloc[-1]
    trend = "UP" if last['close'] > ema20 else "DOWN"
    poc = (last['high'] + last['low'] + last['close']) / 3
    
    stars = 0
    confs = []
    
    if (delta > 55 and trend == "UP") or (delta < -55 and trend == "DOWN"):
        stars += 1; confs.append("Trend Sync 🌊")
    if is_big_money:
        stars += 1; confs.append("Whale Entry 🔥")
    if l_wick > (body * 1.6) or u_wick > (body * 1.6):
        stars += 1; confs.append("Liquidity Grab ✅")
    if abs(delta) > 80:
        stars += 1; confs.append("Extreme Delta ⚡")
    if (delta > 0 and poc < last['close']) or (delta < 0 and poc > last['close']):
        stars += 1; confs.append("POC Cluster 🎯")

    return {"stars": stars, "delta": delta, "confs": confs, "price": last['close'], "type": "CALL" if delta > 0 else "PUT"}

# --- [৫. মেইন লুপ এবং টেলিগ্রাম অ্যালার্ট] ---
async def start_bot_engine():
    print("🚀 Gemini AI Core V57 is running...")
    assets = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X", "AUD/USD": "AUDUSD=X"}
    notified_trades = {}

    while True:
        for name, sym in assets.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                df = pd.DataFrame(r.json()['chart']['result'][0]['indicators']['quote'][0]).dropna()
                
                if not df.empty and len(df) > 30:
                    res = analyze_market_v57(df)
                    if res and res['stars'] >= 3:
                        # ১৮০ সেকেন্ড (৩ মিনিট) পর পর একই অ্যাসেটে সিগন্যাল দিবে
                        if name not in notified_trades or (time.time() - notified_trades[name]) > 180:
                            star_str = "⭐" * res['stars']
                            sig_icon = "🟢" if res['type'] == "CALL" else "🔴"
                            conf_text = "\n".join([f"- {c}" for c in res['confs']])
                            
                            msg = (f"💎 *INSTITUTIONAL SIGNAL*\n"
                                   f"Asset: {name} | {res['type']} {sig_icon}\n"
                                   f"Strength: {star_str} ({res['stars']}/5)\n\n"
                                   f"📈 *Confirmations:*\n{conf_text}\n\n"
                                   f"Price: {res['price']:.5f} | Time: 1m")
                            
                            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                            notified_trades[name] = time.time()

                            # --- রেজাল্ট চেকার শিডিউল ---
                            # ১ মিনিট পর রেজাল্ট চেক
                            asyncio.create_task(check_and_send_result(name, sym, res['price'], res['type'], 60, "1m Expiry"))
                            # ৩ মিনিট পর রেজাল্ট চেক
                            asyncio.create_task(check_and_send_result(name, sym, res['price'], res['type'], 180, "3m Expiry"))
                            
            except Exception as e:
                print(f"Error in loop: {e}")
                continue
        await asyncio.sleep(15)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(start_bot_engine())
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                df = pd.DataFrame(r.json()['chart']['result'][0]['indicators']['quote'][0]).dropna()
                
                if not df.empty and len(df) > 30:
                    res = analyze_market_v57(df)
                    # ৩ বা তার বেশি স্টার থাকলে সিগন্যাল যাবে
                    if res and res['stars'] >= 3:
                        if name not in notified_trades or (time.time() - notified_trades[name]) > 180:
                            star_str = "⭐" * res['stars']
                            sig_icon = "🟢" if res['type'] == "CALL" else "🔴"
                            conf_text = "\n".join([f"- {c}" for c in res['confs']])
                            
                            msg = (f"💎 *INSTITUTIONAL SIGNAL*\n"
                                   f"Asset: {name} | {res['type']} {sig_icon}\n"
                                   f"Strength: {star_str} ({res['stars']}/5)\n\n"
                                   f"📈 *Confirmations:*\n{conf_text}\n\n"
                                   f"Price: {res['price']:.5f} | Time: 1m")
                            
                            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                            notified_trades[name] = time.time()
            except: continue
        await asyncio.sleep(15)

if __name__ == "__main__":
    keep_alive() # রেন্ডার সার্ভারকে সচল রাখবে
    asyncio.run(start_bot_engine())
