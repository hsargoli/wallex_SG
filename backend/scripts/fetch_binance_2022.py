import requests
import pandas as pd
import time
from pathlib import Path

def fetch_binance_klines(symbol="BTCUSDT", interval="1h", start_str="2022-01-01 00:00:00", end_str="2022-12-31 23:59:59"):
    start_ts = int(pd.Timestamp(start_str).timestamp() * 1000)
    end_ts = int(pd.Timestamp(end_str).timestamp() * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    
    print(f"Fetching {symbol} {interval} from {start_str} to {end_str}...")
    
    while start_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "limit": 1000
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            if not data:
                break
            
            all_data.extend(data)
            start_ts = data[-1][0] + 1
            print(f"  fetched {len(all_data)} candles...", end="\r")
            time.sleep(0.1) # rate limit
        except Exception as e:
            print(f"\nError: {e}")
            break
            
    print(f"\nTotal fetched: {len(all_data)}")
    
    if not all_data:
        return None
        
    df = pd.DataFrame(all_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"
    ])
    
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    
    # Convert to numeric
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])
        
    return df

if __name__ == "__main__":
    out_path = Path("backend/data/candles/BTCUSDT_1h_2022.csv")
    df = fetch_binance_klines()
    if df is not None:
        df.to_csv(out_path, index=False)
        print(f"✅ Saved to {out_path}")
