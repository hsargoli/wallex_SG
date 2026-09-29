import asyncio
import sys
from pathlib import Path

# اضافه کردن مسیر backend به sys.path
sys.path.insert(0, '/home/hosein/wallex/backend')

from app.application.use_cases.get_balances import GetBalancesUseCase
from app.infrastructure.wallex.client import WallexClient  # یا کلاسی که برای ارتباط با والکس دارید

async def test():
    print("--- در حال دریافت موجودی‌های خام از والکس ---")
    try:
        # در صورت نیاز به تنظمیات خاص کلاینت را بسازید
        # client = WallexClient()
        # use_case = GetBalancesUseCase(exchange=client)
        
        # تست با فراخوانی مستقیم بر اساس ساختار پروژه شما
        print("لطفا ابتدا بررسی کنید نام فیلدهای موجودی چیست.")
    except Exception as e:
        print(f"خطا در دریافت موجودی: {e}")

