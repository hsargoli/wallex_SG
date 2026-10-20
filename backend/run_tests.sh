#!/bin/bash
# اسکریپت اجرای دستی تست‌ها (برای مواقعی که Hook غیرفعال است)
echo "⏳ در حال اجرای تست‌های بک‌اند..."
cd "$(dirname "$0")"
uv run pytest -q --tb=short
