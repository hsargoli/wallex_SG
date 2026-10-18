import httpx
import time
import csv
from pathlib import Path
from datetime import datetime

def download_binance_data(symbol="BTCUSDT", interval="1h", start_str="2022-01-01", end_str="2024-12-31"):
    start_ts = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_ts = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000)

    # Using Binance Public Data domain
    url = "https://data-api.binance.vision/api/v3/klines"
    all_data = []

    current_ts = start_ts
    print(f"Downloading {symbol} {interval} from {start_str} to {end_str}...")
    
    while current_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_ts,
            "limit": 1000
        }
        try:
            r = httpx.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            
            all_data.extend(data)
            # Update current_ts to the last candle's close time + 1
            current_ts = data[-1][6] + 1
            
            # Print progress every 10,000 candles
            if len(all_data) % 10000 < 1000:
                print(f"  Fetched {len(all_data)} candles... (up to {datetime.fromtimestamp(current_ts/1000).strftime('%Y-%m-%d')})")
            
            time.sleep(0.1) # Rate limit
        except Exception as e:
            print(f"Error: {e}")
            break

    # Save to CSV in the backend's candles folder
    out_path = Path("backend/data/candles") / f"{symbol}_{interval}_historical.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['open_time', 'open', 'high', 'low', 'close', 'volume'])
        for row in all_data:
            # Binance returns: [open_time(ms), open, high, low, close, volume, ...]
            writer.writerow([row[0]//1000, row[1], row[2], row[3], row[4], row[5]])
            
    print(f"✅ Saved {len(all_data)} candles to {out_path}")

if __name__ == "__main__":
    # دانلود داده‌های ۲۰۲۲ (نزولی) تا ۲۰۲۴ (صعودی/رنج)
    download_binance_data("BTCUSDT", "1h", "2022-01-01", "2024-12-31")
