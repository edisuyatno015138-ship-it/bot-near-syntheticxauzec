import time
import ccxt
import pandas as pd
import pandas_ta as ta

# Inisialisasi API Binance untuk data harga publik
exchange = ccxt.binance()

def get_synthetic_d1_df(symbol1='XAUT/USDT', symbol2='ZEC/USDT', limit=100):
    """
    Mengambil data Daily (D1) dari XAUT dan ZEC, 
    menghitung candle sintetis (XAUT / ZEC) & Stochastic (5, 3, 7).
    """
    ohlcv1 = exchange.fetch_ohlcv(symbol1, timeframe='1d', limit=limit)
    ohlcv2 = exchange.fetch_ohlcv(symbol2, timeframe='1d', limit=limit)

    df1 = pd.DataFrame(ohlcv1, columns=['timestamp', 'open1', 'high1', 'low1', 'close1', 'vol1'])
    df2 = pd.DataFrame(ohlcv2, columns=['timestamp', 'open2', 'high2', 'low2', 'close2', 'vol2'])

    df = pd.merge(df1, df2, on='timestamp')

    # Perhitungan Rasio Sintetis XAUT / ZEC
    df['high']  = df['high1'] / df['low2']
    df['low']   = df['low1'] / df['high2']
    df['close'] = df['close1'] / df['close2']

    # Parameter Stochastic (5, 3, 7)
    stoch = ta.stoch(high=df['high'], low=df['low'], close=df['close'], k=5, d=3, smooth_k=7)
    df = pd.concat([df, stoch], axis=1)

    return df

def check_signals():
    print("\n--------------------------------------------------")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Memeriksa Stochastic D1 (5,3,7)...")
    try:
        df = get_synthetic_d1_df(limit=100)
        
        latest_bar = df.iloc[-1]
        prev_bar   = df.iloc[-2]

        stoch_k_now = latest_bar['STOCHk_5_3_7']
        stoch_d_now = latest_bar['STOCHd_5_3_7']
        
        stoch_k_prev = prev_bar['STOCHk_5_3_7']
        stoch_d_prev = prev_bar['STOCHd_5_3_7']

        print(f"-> Candle Lalu   | %K: {stoch_k_prev:.2f} | %D: {stoch_d_prev:.2f}")
        print(f"-> Candle Terbaru| %K: {stoch_k_now:.2f} | %D: {stoch_d_now:.2f}")

        # DETEKSI PERSILANGAN (CROSS) D1
        d1_golden_cross = (stoch_k_prev <= stoch_d_prev) and (stoch_k_now > stoch_d_now)
        d1_dead_cross   = (stoch_k_prev >= stoch_d_prev) and (stoch_k_now < stoch_d_now)

        if d1_golden_cross:
            print("🚀 [SINYAL GOLDEN CROSS D1] ROTASI 100% MODAL KE XAUT!")
            execute_near_swap(from_coin="ZEC", to_coin="XAUT")

        elif d1_dead_cross:
            print("🚀 [SINYAL DEAD CROSS D1] ROTASI 100% MODAL KE ZEC!")
            execute_near_swap(from_coin="XAUT", to_coin="ZEC")

        else:
            print("-> Belum ada persilangan (%K dan %D masih bergerak searah).")

    except Exception as e:
        print(f"⚠️ Error membaca data: {e}")

def execute_near_swap(from_coin, to_coin):
    """
    Tempat eksekusi Swap NEAR Protocol / Ref Finance / NEAR Intents
    """
    print(f"[EKSEKUSI] Menukar 100% saldo {from_coin} menjadi {to_coin} di Jaringan NEAR...")

if __name__ == '__main__':
    while True:
        check_signals()
        time.sleep(3600)  # Cek otomatis setiap 1 jam
