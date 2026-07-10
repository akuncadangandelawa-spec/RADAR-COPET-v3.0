"""
RADAR COPET v3.1 - Production Ready (Bugfix Numpy Truth Value)
Architecture: Background Worker + Cache + Flask API
"""
import time
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "SYMBOL_LIST": ["XAUUSDc", "EURUSDc", "GBPUSDc", "USDJPYc", "AUDUSDc"],
    "DEFAULT_SYMBOL": "XAUUSDc",
    "PORT": 5000,
    "HOST": "0.0.0.0",
    "CACHE_TTL_SECONDS": 0.5,
    "HISTORY_BARS": 160,
}

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("RadarCopet")

# ============================================================
# FLASK APP & CACHE
# ============================================================
app = Flask(__name__)
SYMBOL_LIST = CONFIG["SYMBOL_LIST"]

class RadarCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}
        self._last_update = {}

    def set(self, symbol, data):
        with self._lock:
            self._data[symbol] = data
            self._last_update[symbol] = time.time()

    def get(self, symbol):
        with self._lock:
            return self._data.get(symbol)

cache = RadarCache()

# ============================================================
# INDICATOR FUNCTIONS
# ============================================================
def get_ma_signal(df, period):
    ma = df['close'].rolling(window=period).mean().iloc[-1]
    last_close = df['close'].iloc[-1]
    return ("BUY" if last_close > ma else "SELL"), round(ma, 5)

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

def calculate_tf_power(df):
    # Fix: Gunakan .empty untuk cek DataFrame pandas
    if df is None or df.empty or len(df) < 20:
        return 50, 50
    close = df['close'].iloc[-1]
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    rsi = get_rsi(df)

    buy_score = sell_score = 0
    if close > ma10: buy_score += 30
    else: sell_score += 30
    if close > ma20: buy_score += 30
    else: sell_score += 30
    if rsi > 55: buy_score += 40
    elif rsi < 45: sell_score += 40
    else: buy_score += 20; sell_score += 20
    return buy_score, sell_score

def process_tf_data(df, digits):
    if df is None or df.empty or len(df) < 155:
        return None

    df = df.copy()
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

    if bb1_mid.iloc[-2] <= bb2_mid.iloc[-2] and bb1_mid.iloc[-1] > bb2_mid.iloc[-1]:
        trigger, status_cross = "BUY", "Mid Crossover (BB1 > BB2 Mid)"
    elif bb1_mid.iloc[-2] <= bb2_low.iloc[-2] and bb1_mid.iloc[-1] > bb2_low.iloc[-1]:
        trigger, status_cross = "BUY", "Reversal (BB1 Mid > BB2 Low)"
    elif bb1_up.iloc[-2] <= bb2_mid.iloc[-2] and bb1_up.iloc[-1] > bb2_mid.iloc[-1]:
        trigger, status_cross = "BUY", "Upper Break (BB1 Up > BB2 Mid)"
    elif bb1_mid.iloc[-2] >= bb2_mid.iloc[-2] and bb1_mid.iloc[-1] < bb2_mid.iloc[-1]:
        trigger, status_cross = "SELL", "Mid Crossover (BB1 < BB2 Mid)"
    elif bb1_mid.iloc[-2] >= bb2_low.iloc[-2] and bb1_mid.iloc[-1] < bb2_low.iloc[-1]:
        trigger, status_cross = "SELL", "Reversal (BB1 Mid < BB2 Low)"
    elif bb1_low.iloc[-2] >= bb2_mid.iloc[-2] and bb1_low.iloc[-1] < bb2_mid.iloc[-1]:
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

# ============================================================
# BACKGROUND WORKER (FIXED NUMPY BUG)
# ============================================================
def fetch_symbol_data(symbol):
    try:
        mt5.symbol_select(symbol, True)
        tick = mt5.symbol_info_tick(symbol)
        info = mt5.symbol_info(symbol)
        if tick is None or info is None:
            return {"error": f"Simbol {symbol} tidak ditemukan"}

        digits = info.digits
        pip_size = info.point * 10 if digits in (3, 5) else info.point

        rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, CONFIG["HISTORY_BARS"])
        rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, CONFIG["HISTORY_BARS"])

        df_m1 = pd.DataFrame(rates_m1) if rates_m1 is not None else None
        df_m5 = pd.DataFrame(rates_m5) if rates_m5 is not None else None

        data_m1 = process_tf_data(df_m1, digits) if df_m1 is not None else None
        data_m5 = process_tf_data(df_m5, digits) if df_m5 is not None else None

        server_time = datetime.fromtimestamp(tick.time)
        time_left_m1 = 60 - server_time.second
        time_left_m5 = 300 - (server_time.minute % 5) * 60 - server_time.second

        daily_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1)
        d_open = daily_rates[0]['open'] if daily_rates is not None and len(daily_rates) > 0 else tick.bid
        open_pips = round((tick.bid - d_open) / pip_size, 1)

        # 🔥 FIX: Ambil data TF lain secara eksplisit, JANGAN gunakan `or []` pada Numpy Array!
        rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 20)
        rates_h1  = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
        rates_d1  = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 20)
        rates_w1  = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_W1, 0, 20)

        tf_map = {
            "m1": df_m1, 
            "m5": df_m5,
            "m15": pd.DataFrame(rates_m15) if rates_m15 is not None else pd.DataFrame(),
            "H1":  pd.DataFrame(rates_h1)  if rates_h1 is not None else pd.DataFrame(),
            "D1":  pd.DataFrame(rates_d1)  if rates_d1 is not None else pd.DataFrame(),
            "W1":  pd.DataFrame(rates_w1)  if rates_w1 is not None else pd.DataFrame(),
        }
        
        power_data = {}
        for name, df in tf_map.items():
            b_pow, s_pow = calculate_tf_power(df)
            power_data[f"buy_{name}"] = f"{b_pow}%"
            power_data[f"sell_{name}"] = f"{s_pow}%"

        if data_m1 is None:
            data_m1 = {"trigger": "NO DATA", "status_cross": "History < 155 bars", "bb1": "-", "bb2": "-", "ma_fast": "-", "ma_slow": "-", "rsi": "-", "atr": "-"}
        if data_m5 is None:
            data_m5 = {"trigger": "NO DATA", "status_cross": "History < 155 bars", "bb1": "-", "bb2": "-", "ma_fast": "-", "ma_slow": "-", "rsi": "-", "atr": "-"}

        return {
            "symbol": symbol, "spread": info.spread, "bid": tick.bid, "ask": tick.ask,
            "daily_open": round(d_open, digits), "open_pips": f"{open_pips} pips",
            "server_time": server_time.strftime("%H:%M:%S"),
            "m1": {**data_m1, "time_left": time_left_m1},
            "m5": {**data_m5, "time_left": time_left_m5},
            **power_data
        }
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return {"error": str(e)}

def background_worker():
    logger.info("🚀 Background worker started")
    while True:
        for symbol in SYMBOL_LIST:
            try:
                data = fetch_symbol_data(symbol)
                if "error" not in data:
                    cache.set(symbol, data)
            except Exception as e:
                logger.error(f"Worker error on {symbol}: {e}")
        time.sleep(CONFIG["CACHE_TTL_SECONDS"])

# ============================================================
# MT5 INIT & ROUTES
# ============================================================
def init_mt5():
    if not mt5.initialize():
        logger.error(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    logger.info("✅ MT5 connected successfully")
    for sym in SYMBOL_LIST:
        mt5.symbol_select(sym, True)
    return True

def shutdown_mt5():
    logger.info("🛑 Shutting down MT5 connection...")
    mt5.shutdown()

@app.route('/')
def index():
    return render_template('index.html', symbols=SYMBOL_LIST, default_symbol=CONFIG["DEFAULT_SYMBOL"])

@app.route('/api/radar_data')
def radar_data():
    symbol = request.args.get('symbol', CONFIG["DEFAULT_SYMBOL"])
    data = cache.get(symbol)
    if data is None:
        return jsonify({"error": "Data belum siap, coba lagi dalam 1 detik", "status": "LOADING"}), 202
    return jsonify(data)

if __name__ == '__main__':
    if not init_mt5():
        exit(1)

    worker_thread = threading.Thread(target=background_worker, daemon=True)
    worker_thread.start()

    try:
        logger.info(f"🌐 Server running on http://{CONFIG['HOST']}:{CONFIG['PORT']}")
        app.run(debug=False, host=CONFIG["HOST"], port=CONFIG["PORT"], threaded=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        shutdown_mt5()