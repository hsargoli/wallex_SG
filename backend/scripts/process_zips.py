import zipfile
import csv
import glob
from pathlib import Path

def process_symbol_zips(symbol):
    zip_dir = Path(__file__).resolve().parent.parent / "data" / "candles" / "zips" / symbol
    out_csv = Path(__file__).resolve().parent.parent / "data" / "candles" / f"{symbol}_1h_all.csv"
    
    if not zip_dir.exists():
        print(f"⚠️ Skipping {symbol}: Folder {zip_dir} does not exist.")
        return

    zip_files = sorted(glob.glob(str(zip_dir / f"{symbol}-1h-*.zip")))
    if not zip_files:
        print(f"⚠️ Skipping {symbol}: No ZIP files found.")
        return

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    total_candles = 0
    
    print(f"Processing {symbol} ({len(zip_files)} files)...")
    
    with open(out_csv, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['open_time', 'open', 'high', 'low', 'close', 'volume'])

        for zf in zip_files:
            with zipfile.ZipFile(zf, 'r') as z:
                csv_name = z.namelist()[0] 
                with z.open(csv_name) as f_in:
                    for line in f_in:
                        parts = line.decode('utf-8').strip().split(',')
                        if not parts or len(parts) < 6: continue
                        if parts[0] == 'open_time': continue
                        
                        open_time_s = int(parts[0]) // 1000
                        writer.writerow([open_time_s, parts[1], parts[2], parts[3], parts[4], parts[5]])
                        total_candles += 1
                        
    print(f"✅ {symbol}: Processed {total_candles} candles -> {out_csv.name}")

if __name__ == "__main__":
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    for sym in symbols:
        process_symbol_zips(sym)
