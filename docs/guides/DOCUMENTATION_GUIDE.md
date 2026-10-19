# 📝 راهنمای مستندسازی

> چطور markdown سالم در ترمینال بسازیم
> نسخه ۱.۰ — مهر ۱۴۰۵
> شرکت: SGPR (سرو پایا رشد سبز)

---

## 🎯 چرا این سند؟

**مشکل:** markdown در ترمینال backtick را گم می‌کند.
**دلیل:** backtick = command substitution در shell.
**نتیجه:** `code inline` خالی می‌شود.

**راه‌حل:** سه مرحله‌ای — AI + nano + Python.

**مخاطب:** دی، نووآ، هر AI جدید، حسین.

---

## 🐛 مشکل چیست؟

وقتی markdown را مستقیم در ترمینال paste می‌کنی:

| کاراکتر | shell چه می‌کند |
|---|---|
| ` (backtick) | command substitution — اجرا می‌کند |
| `#` | comment — نادیده می‌گیرد |
| `$` | variable — تفسیر می‌کند |
| `**` | glob — گاهی |

**نتیجه:** markdown ناقص.

---

## ✅ راه‌حل — سه مرحله

### مرحله ۱ — AI با placeholder می‌فرستد

AI (دی یا نووآ) محتوا را با این placeholderها می‌فرستد:

| Placeholder | تبدیل به | برای |
|---|---|---|
| ` | backtick | inline code |
| ``` | سه backtick | بلوک کد |
| BEGIN_X | (حذف) | شروع محتوا |
| END_X | (حذف) | پایان محتوا |

**مثال:**

AI می‌فرستد:

```
# عنوان

این `bold` است.

```
code block
```

متن دیگر.
```

نکته: placeholderها (` و ```) در چت RTL گم نمی‌شوند — چون کاراکتر خاص نیستند.

---

### مرحله ۲ — کاربر در nano paste می‌کند

**دستور:**

```
LANG=C nano ~/PATH/FILE.md
```

**در nano:**

| کلید | کار |
|---|---|
| Ctrl+Shift+V | paste |
| Ctrl+O | ذخیره |
| Enter | تأیید نام فایل |
| Ctrl+X | خروج |

**چرا LANG=C؟**

- LANG=C = انگلیسی، بدون RTL
- markdown سالم می‌ماند
- فارسی چپ‌چین می‌شود (ولی سالم)

⚠️ **نکته:** placeholderها (` و ```) دست‌نخورده می‌مانند.

---

### مرحله ۳ — Python تبدیل می‌کند

**دستور:**

```
cd ~ && python3 << 'PYEOF'
from pathlib import Path

p = Path("FILE.md")
src = p.read_text(encoding="utf-8")

# ═══ حذف delimiter ═══
src = src.replace("BEGIN_FILE\n", "").replace("\nEND_FILE", "")

# ═══ تبدیل بلوک کد ═══
src = src.replace("```", "```")

# ═══ تبدیل inline code ═══
src = src.replace("`", "`")

# ═══ حذف خطوط خالی آخر ═══
src = src.rstrip() + "\n"

p.write_text(src, encoding="utf-8")
print(f"✅ {len(src.splitlines())} خط")
PYEOF
```

**نتیجه:** markdown کامل، backtick سالم.

---

## 📊 شاهد بعد از ساخت

**دستور:**

```
cd ~ && \
echo "خطوط:" && wc -l FILE.md && \
echo "backtick:" && python3 -c "print(open('FILE.md').read().count(chr(96)))" && \
echo "heading ##:" && grep -c '^## ' FILE.md && \
echo "heading ###:" && grep -c '^### ' FILE.md && \
echo "بلوک کد:" && grep -c '^```' FILE.md && \
echo "" && \
echo "BEGIN/END:" && grep -c "BEGIN_FILE\|END_FILE" FILE.md
```

**انتظار:**

| مورد | انتظار |
|---|---|
| خطوط | مطابق محتوا |
| backtick | حداقل ۱۰-۲۰ |
| heading `##` | ۵-۱۰ |
| بلوک کد | ۵-۲۰ |
| BEGIN/END | ۰ |

---

## 🔧 عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| backtick گم شد | به‌جای backtick، ` بفرست |
| فایل عجیب در git status | `rm -f '**text**' 'فایل'` |
| heading `##` گم شد | `grep -n '^#' FILE.md` ببین کدام هست |
| BEGIN/END ماند | Python را دوباره اجرا کن |
| Python در ترمینال خطا | اسکریپت را در nano بنویس، بعد `python3 file.py` |

---

## 🐍 الگوهای Python

### ۱. ساخت فایل جدید

```
from pathlib import Path

content = r'''# عنوان

محتوا با `backtick` و ```code block```
'''

Path("file.md").write_text(content, encoding="utf-8")
print("✅ ساخته شد")
```

**نکته:** `r'''...'''` = raw string (بدون escape).

### ۲. تغییر دقیق

```
from pathlib import Path

p = Path("file.md")
src = p.read_text(encoding="utf-8")

old = "متن قدیمی"
new = "متن جدید"

if old not in src:
    raise SystemExit("❌ پیدا نشد")
if src.count(old) != 1:
    raise SystemExit(f"❌ {src.count(old)} match")

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("✅ OK")
```

### ۳. شمارش backtick

```
python3 -c "print(open('file.md').read().count(chr(96)))"
```

**⚠️ چرا `chr(96)`؟**
چون backtick در shell تفسیر می‌شود.

---

## 💡 چرا این روش کار می‌کند؟

| مرحله | محافظت |
|---|---|
| AI با placeholder | backtick در چت گم نمی‌شود |
| nano (LANG=C) | ترمینال markdown را نمی‌خورد |
| Python | exact match، بدون shell |

**سه لایه محافظت.**

---

## 🎯 قاعده طلایی

> **backtick را هرگز مستقیم paste نکن.**
> **همیشه ` بفرست. Python تبدیل می‌کند.**

---

## 📌 خلاصه

| مرحله | ابزار | کار |
|---|---|---|
| ۱ | AI | محتوا با ` و ``` |
| ۲ | nano (LANG=C) | paste + ذخیره |
| ۳ | Python | تبدیل به markdown |

**شاهد:** بعد از Python بگیر.

**قاعده:** backtick مستقیم paste نکن.

---

## 📚 مراجع

- **قواعد پروژه:** `docs/CONVENTIONS.md`
- **اصول AI:** `AI_PRIMER.md`
- **شروع کار:** `docs/GETTING_STARTED.md`

---

**«آهسته، مطمئن، با شاهد، با بازبینی.»** — SGPR (سرو پایا رشد سبز)

**موفق باشی، همراه.** 🌿
