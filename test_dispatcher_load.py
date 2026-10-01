from pathlib import Path
import json

# مسیر فایل رو دقیق چک کنیم
config_path = Path("backend/data/strategy_config.json")
print(f"Checking path: {config_path.absolute()}")
print(f"File exists: {config_path.exists()}")

if config_path.exists():
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            print(f"File loaded successfully. Number of symbols: {len(data)}")
    except Exception as e:
        print(f"Error loading JSON: {e}")
