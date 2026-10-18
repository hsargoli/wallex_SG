import pandas as pd
import numpy as np
import sys
from pathlib import Path

def generate_synthetic_bear():
    np.random.seed(42)
    n = 1000
    
    price = 21_500_000_000
    closes = []
    
    # Simulate a bear market with pullbacks (drops 2%, rallies 0.8%, drops 2%...)
    for i in range(n):
        cycle = (i // 30) % 2 # 30 hours of drop, 30 hours of rally
        if cycle == 0:
            price *= (1 - 0.002) # Drop 0.2% per hour
        else:
            price *= (1 + 0.001) # Rally 0.1% per hour
            
        # Add small hourly noise (0.2%)
        noise = np.random.normal(0, 0.002)
        close = price * (1 + noise)
        closes.append(close)
        
    close_arr = np.array(closes)
    open_price = close_arr * (1 + np.random.normal(0, 0.001, n))
    high = np.maximum(open_price, close_arr) * (1 + np.abs(np.random.normal(0, 0.001, n)))
    low = np.minimum(open_price, close_arr) * (1 - np.abs(np.random.normal(0, 0.001, n)))
    volume = np.random.uniform(0.1, 2.0, n)
    
    start_ts = 1672531200
    open_time = [start_ts + i * 3600 for i in range(n)]
    
    df = pd.DataFrame({
        "open_time": open_time, "open": open_price,
        "high": high, "low": low, "close": close_arr, "volume": volume
    })
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    out_path = BASE_DIR / "data" / "candles" / "SYNTHETIC_BEAR_1h.csv"
    df.to_csv(out_path, index=False)
    
    print(f"✅ Realistic bear market generated.")
    print(f"Start: {close_arr[0]:,.0f} -> End: {close_arr[-1]:,.0f}")

if __name__ == "__main__":
    generate_synthetic_bear()
