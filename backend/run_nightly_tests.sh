#!/bin/bash
# اسکریپت اجرای خودکار تست‌ها
# این اسکریپت توسط Cron اجرا می‌شود

cd /home/hosein/wallex/backend || exit 1

# گرفتن مسیر uv (چون کران ممکنه PATH رو نداشته باشه)
UV_BIN=$(which uv)
LOG_DIR="/home/hosein/wallex/backend/logs"
DATE=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/nightly_test_$DATE.log"

echo "=== شروع تست‌ها در $(date) ===" > "$LOG_FILE"

# اجرای تست‌ها و ذخیره خروجی
$UV_BIN run pytest -q --tb=short >> "$LOG_FILE" 2>&1

STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "✅ نتیجه: تمام تست‌ها با موفقیت پاس شدند." >> "$LOG_FILE"
else
    echo "❌ نتیجه: برخی از تست‌ها با خطا مواجه شدند. (کد خطا: $STATUS)" >> "$LOG_FILE"
fi

# نگه داشتن فقط ۷ لاگ آخر (برای جلوگیری از پر شدن هارد)
ls -1t "$LOG_DIR"/nightly_test_*.log | tail -n +8 | xargs -r rm
