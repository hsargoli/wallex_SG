# 🔍 Investigate — SarvRouter همه‌ی tickها pending

**تاریخ:** ۲۰۲۶-۱۰-۲۹ ۱۸:۲۰ UTC
**شاهد:** ۵ tick در ۲.۵ ساعت، همه `pending`

## state
- `regime_since_idx: null`
- `last_switch_idx: null`
- audit: خالی

## دو باگ

### ۱. SarvRouter در هر tick جدید ساخته می‌شود
- `lifecycle._current_regime = None` هر بار
- همیشه `regime_changed` → `pending`

### ۲. `now_idx` همیشه ۳۰۰ (نه ساعت)
- `now_idx = len(candles) - 1` → همیشه ۳۰۰
- حتی با singleton، `stable = 0` → همیشه `pending`

## Fix پیشنهادی
1. singleton router در scheduler
2. `now_idx = int(time.time() // 3600)` (ساعت UTC)

## تصمیم
Fix فردا با ذهن تازه + تست RED→GREEN.
