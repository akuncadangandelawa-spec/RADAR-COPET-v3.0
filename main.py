import time
from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

app = Flask(__name__)

# Daftar simbol kustom Akun Cent HFM Anda
SYMBOL_LIST = ["XAUUSDc", "EURUSDc", "GBPUSDc", "USDJPYc", "AUDUSDc"]

def get_ma_signal(df, period):
    ma = df['close'].rolling(window=period).mean().iloc[-1]
    last_close = df['close'].iloc[-1]
    return "BUY" if last_close > ma else "SELL", round(ma, 5)

def get_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def get_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return round(true_range.rolling(window=period).mean().iloc[-1], 5)

def calculate_tf_power(symbol, timeframe):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 20)
    if rates is None or len(rates) < 20:
        return 50, 50
    df = pd.DataFrame(rates)
    close = df['close'].iloc[-1]
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    rsi = get_rsi(df)
    
    buy_score = 0
    sell_score = 0
    if close > ma10: buy_score += 30
    else: sell_score += 30
    if close > ma20: buy_score += 30
    else: sell_score += 30
    if rsi > 55: buy_score += 40
    elif rsi < 45: sell_score += 40
    else: buy_score += 20; sell_score += 20
    return buy_score, sell_score

def process_tf_data(symbol, tf_code, digits):
    # Mengambil data 160 bar untuk kalkulasi BB150
    rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, 160)
    if rates is None or len(rates) < 155:
        return None
        
    df = pd.DataFrame(rates)
    df['ma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    bb1_up = df['ma20'] + (1.3 * df['std20'])
    bb1_mid = df['ma20']
    bb1_low = df['ma20'] - (1.3 * df['std20'])

    df['ma150'] = df['close'].rolling(150).mean()
    df['std150'] = df['close'].rolling(150).std()
    bb2_up = df['ma150'] + (1.3 * df['std150'])
    bb2_mid = df['ma150']
    bb2_low = df['ma150'] - (1.3 * df['std150'])

    cls1, cls2 = df['close'].iloc[-1], df['close'].iloc[-2]
    
    trigger = "WAIT"
    status_cross = "Flat / No Cross"
    
    if (bb1_mid.iloc[-2] <= bb2_mid.iloc[-2] and bb1_mid.iloc[-1] > bb2_mid.iloc[-1]):
        trigger, status_cross = "BUY", "Mid Crossover (BB1 > BB2 Mid)"
    elif (bb1_mid.iloc[-2] <= bb2_low.iloc[-2] and bb1_mid.iloc[-1] > bb2_low.iloc[-1]):
        trigger, status_cross = "BUY", "Reversal (BB1 Mid > BB2 Low)"
    elif (bb1_up.iloc[-2] <= bb2_mid.iloc[-2] and bb1_up.iloc[-1] > bb2_mid.iloc[-1]):
        trigger, status_cross = "BUY", "Upper Break (BB1 Up > BB2 Mid)"
    elif (bb1_mid.iloc[-2] >= bb2_mid.iloc[-2] and bb1_mid.iloc[-1] < bb2_mid.iloc[-1]):
        trigger, status_cross = "SELL", "Mid Crossover (BB1 < BB2 Mid)"
    elif (bb1_mid.iloc[-2] >= bb2_low.iloc[-2] and bb1_mid.iloc[-1] < bb2_low.iloc[-1]):
        trigger, status_cross = "SELL", "Reversal (BB1 Mid < BB2 Low)"
    elif (bb1_low.iloc[-2] >= bb2_mid.iloc[-2] and bb1_low.iloc[-1] < bb2_mid.iloc[-1]):
        trigger, status_cross = "SELL", "Lower Break (BB1 Low < BB2 Mid)"
    elif cls1 > bb1_up.iloc[-1]:
        trigger, status_cross = "BUY", "Breakout: Close > BB1 Upper"
    elif cls1 < bb1_low.iloc[-1]:
        trigger, status_cross = "SELL", "Breakout: Close < BB1 Lower"

    _, ma_fast_val = get_ma_signal(df, 10)
    _, ma_slow_val = get_ma_signal(df, 20)
    rsi_val = get_rsi(df)
    atr_val = get_atr(df)

    return {
        "trigger": trigger, "status_cross": status_cross,
        "bb1": f"U:{round(bb1_up.iloc[-1], digits)} | M:{round(bb1_mid.iloc[-1], digits)} | L:{round(bb1_low.iloc[-1], digits)}",
        "bb2": f"U:{round(bb2_up.iloc[-1], digits)} | M:{round(bb2_mid.iloc[-1], digits)} | L:{round(bb2_low.iloc[-1], digits)}",
        "ma_fast": ma_fast_val, "ma_slow": ma_slow_val, "rsi": rsi_val, "atr": atr_val
    }

@app.route('/')
def index():
    return render_template('index.html', symbols=SYMBOL_LIST)

@app.route('/api/radar_data')
def radar_data():
    symbol = request.args.get('symbol', 'XAUUSDc')
    if not mt5.initialize():
        return jsonify({"error": "Gagal koneksi ke MT5"}), 500
        
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    if tick is None or info is None:
        return jsonify({"error": "Simbol Tidak Ditemukan"}), 400

    digits = info.digits
    pip_size = info.point * 10 if (digits == 3 or digits == 5) else info.point

    # Ambil info multi-timeframe m1 dan m5
    data_m1 = process_tf_data(symbol, mt5.TIMEFRAME_M1, digits)
    data_m5 = process_tf_data(symbol, mt5.TIMEFRAME_M5, digits)
    
    if data_m1 is None or data_m5 is None:
        return jsonify({"error": "Gagal memproses indikator"}), 400

    # Hitung sisa detik lilin berjalan
    curr_time = int(time.time())
    time_left_m1 = 60 - (curr_time % 60)
    time_left_m5 = 300 - (curr_time % 300)

    # Info Open Harian
    daily_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1)
    d_open = daily_rates[0]['open'] if daily_rates is not None else tick.bid
    open_pips = round((tick.bid - d_open) / pip_size, 1)

    # Kalkulasi Matrix Power Kekuatan Tren
    tf_list = {"m1": mt5.TIMEFRAME_M1, "m5": mt5.TIMEFRAME_M5, "m15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1}
    power_data = {}
    for name, tf_val in tf_list.items():
        b_pow, s_pow = calculate_tf_power(symbol, tf_val)
        power_data[f"buy_{name}"] = f"{b_pow}%"
        power_data[f"sell_{name}"] = f"{s_pow}%"

    return jsonify({
        "symbol": symbol, "spread": info.spread, "daily_open": round(d_open, digits), "open_pips": f"{open_pips} pips",
        "m1": {**data_m1, "time_left": time_left_m1},
        "m5": {**data_m5, "time_left": time_left_m5},
        **power_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050) # host 0.0.0.0 agar bisa ditembak ip lokal via HP