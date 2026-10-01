import os
from pathlib import Path

# این اسکریپت رو از همونجایی اجرا کن که uvicorn رو اجرا می‌کنی (داخل backend)
current_path = Path("data/strategy_config.json")
print(f"--- DEBUGGING CONFIG PATH ---")
print(f"CWD (Current Working Directory): {os.getcwd()}")
print(f"Target Path (Absolute): {current_path.absolute()}")
print(f"File Exists: {current_path.exists()}")

