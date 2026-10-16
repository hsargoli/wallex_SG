# 0015. User Paper State — انتقال paper trading از مهمان به کاربر

**Status:** Accepted
**Date:** 2026-10-16
**Deciders:** حسین س، دی

## Context

فاز ۱۷ (احراز هویت) تمام شد. الان کاربر لاگین‌شده در `/guest`:
- سرمایه‌ی ۳M و عنوان درست رو می‌بینه (از `/v1/auth/me`)
- ولی پوزیشن‌ها، تریدها، equity curve خالی‌ست
- start/stop/reset به `/v1/guest/paper-v3/*` می‌ره که با `X-Guest-Token` کار می‌کنه، نه JWT
- state در `data/guests/{token}/` ذخیره می‌شه، در حالی که کاربر state خودش رو در DB داره

فاز ۱۷.۷ می‌خواد paper state رو برای کاربر لاگین‌شده کار بندازه.

### محدودیت‌های فعلی کد

بررسی `PaperEngine` (`app/infrastructure/paper_trading/engine.py`):
- `self.repo: PaperRepository` (فایلـی، sync)
- ۶ جا `self.repo.save(self.state)` + ۱ جا `self.repo.load()` در `__init__`
- ۱ جا `self.repo.state_file.exists()` در `__init__` — صفت مخصوص `PaperRepository`
- `load()` و `save()` هر دو **sync**

`GuestScheduler` (`app/services/guest/scheduler.py`):
- یه loop مشترک هر ۱۸۰ ثانیه
- `set_engines_provider(callable)` → `dict[token, PaperEngine]`
- برای هر engine در حال اجرا: `await engine._check()`

`User` model (migration `291b79050370`):
- ستون‌های `capital_total`, `capital_available`, `capital_in_use`
- `open_positions` (JSONB), `closed_trades` (JSONB), `equity_curve` (JSONB)
- `total_trades`, `wins`, `losses`
- **نیازی به migration جدید نیست**

### نکته‌ی حساس

`PaperEngine.__init__` **sync**ـه. اگه `UserPaperRepository` async بشه، نمی‌تونیم داخل `__init__` صدا بزنیم. باید `PaperEngine` رو refactor کنیم — load از `__init__` بره بیرون.

## Decision

سه تصمیم کلیدی:

### تصمیم ۱: `UserPaperEngine(PaperEngine)` — subclass

**گزینه‌ها:**
- **الف) subclass** ✅ انتخاب شد
- ب) کلاس مستقل → تکرار منطق trading/exchange/bot

**دلیل:** `_check`, `_check_entries`, `_check_exits`, `execute_manual_order`, `close_position` همه یکسانن. فقط repo و load اولیه فرق می‌کنه.

### تصمیم ۲: `PaperScheduler` مشترک (rename از `GuestScheduler`)

**گزینه‌ها:**
- **الف) generalize به `PaperScheduler` با دو provider** ✅ انتخاب شد
- ب) `UserScheduler` جدا → دو loop موازی، منابع بیشتر
- پ) user engineها توی همون dict با کلید `user:{uuid}` → کلید قاطی، دیباگ سخت

**دلیل:** منطق یکیه؛ فقط منبع engineها فرق می‌کنه. یه loop = منابع کمتر.

### تصمیم ۳: async repo با protocol + `asyncio.to_thread` برای فایلـی

**گزینه‌ها:**
- **الف) async DB repo + refactor `PaperEngine`** ✅ انتخاب شد
- ب) sync facade با fire-and-forget `asyncio.create_task` → save بی‌صدا شکست می‌خوره
- پ) دو کلاس مستقل → تکرار منطق

**دلیل:** تنها راهی که واقعاً asyncـه و interface یکسان داره.

### جزئیات پیاده‌سازی

**الف) `PaperRepositoryProtocol`** — `app/infrastructure/paper_trading/protocol.py`:

~~~python
from typing import Protocol
from app.infrastructure.paper_trading.state import PaperState

class PaperRepositoryProtocol(Protocol):
    async def exists(self) -> bool: ...
    async def load(self) -> PaperState: ...
    async def save(self, state: PaperState) -> None: ...
~~~

**ب) `PaperRepository` فایلـی — async با `asyncio.to_thread`:**

~~~python
async def exists(self) -> bool:
    return await asyncio.to_thread(lambda: self.state_file.exists())

async def load(self) -> PaperState:
    return await asyncio.to_thread(self._load_sync)

async def save(self, state: PaperState) -> None:
    await asyncio.to_thread(self._save_sync, state)
~~~

متدهای `_load_sync`/`_save_sync` همون کد فعلی هستن.

**ج) `PaperEngine.__init__` — load از `__init__` می‌ره بیرون:**

`__init__` فقط تنظیمات رو نگه می‌داره. متد جدید:

~~~python
async def ensure_state(self) -> None:
    """بارگذاری یا ساخت state — idempotent."""
    if self._state_initialized:
        return
    exists = await self.repo.exists()
    self.state = await self.repo.load()
    if not exists:
        # init with initial_capital
        ...
    else:
        self.state.initial_capital = self.initial_capital
    self._state_initialized = True
~~~

`start()` خودش اول `ensure_state()` رو صدا می‌زنه — تا صدا زننده‌ها (endpointها) مجبور نشن مستقیماً صدا بزنن.

**د) تقسیم فاز:**

**۱۷.۷.۱ — refactor async بدون تغییر behavior**
- `protocol.py` جدید
- `PaperRepository` → async
- `PaperEngine` → `ensure_state()` + ۶ جا await
- `paper_v3.py` endpointها → `start()` خودش `ensure_state` رو صدا می‌زنه
- تست safety net سبز بمونه (۱۰ تست) + ۱۷۵ کل
- **هیچ تغییری در behavior**

**۱۷.۷.۲ — فیچر user paper**
- `UserPaperRepository` (async DB)
- `UserPaperEngine(PaperEngine)` — override `__init__` + repo
- `app/presentation/api/v1/user.py` جدید: `/v1/user/paper-v3/*` (۵ endpoint)
- nginx: `/api/backend/v1/user/*` → public (JWT داخلی auth می‌کنه)
- frontend: `useUserPaperV3Status` + switch در `/guest`
- تست‌های جدید

## Consequences

- **Positive:**
  - interface یکسان برای فایلـی و DB
  - آماده برای آینده (state در DB، مقیاس‌پذیر)
  - `PaperEngine` از `state_file` مخصوص فایل رها می‌شه
  - safety net (۱۰ تست) تضمین می‌کنه behavior عوض نشه
  - تقسیم ۱۷.۷.۱ / ۱۷.۷.۲ → rollback آسان

- **Negative:**
  - refactor در `PaperEngine` (۶ جا await)
  - تست safety net فعلاً sync نوشته شده — بعد از refactor باید `await` بشن (یا `asyncio.run` باقی بمونه؛ قابل قبوله)
  - `GuestScheduler` rename می‌شه → نیاز به grep سراسری قبل از rename

- **Neutral:**
  - `GuestScheduler` اسمش عوض می‌شه ولی رفتار یکسانه
  - endpointهای موجود مسیرشون عوض نمی‌شه

## References

- AI_PRIMER.md — قانون ۱۳ (نقطه‌ی برگشت)، قانون ۱۴ (ابزار اشتباه رو عوض کن)
- Handoff 2026-10-16 — بخش «کار بعدی»
- فایل‌های کلیدی:
  - `app/infrastructure/paper_trading/engine.py`
  - `app/infrastructure/paper_trading/repository.py`
  - `app/infrastructure/paper_trading/state.py`
  - `app/services/guest/scheduler.py`
  - `app/presentation/api/v1/paper_v3.py`
  - `app/infrastructure/db/models/user.py`
- تست safety net: `tests/integration/test_paper_engine_persistence.py`
- Migration: `291b79050370_create_users_and_register_attempts.py`
- Tag نقطه‌ی برگشت: `v0.9.17-pre-user-paper`

---

## Addendum 1 — ستون `paper_meta` (2026-10-16)

### داده‌ی جدید

در طراحی `UserPaperRepository`، نگاشت دقیق `PaperState` (۲۱ فیلد) → `User` (۸ فیلد مرتبط) گرفته شد. نتیجه:

**فیلدهای بی‌خونه (۱۰ تا):**

| PaperState | معنی | وضعیت |
|---|---|---|
| `initial_capital` | سرمایه‌ی اولیه | ❌ معادل `capital_total` نیست (معنای متفاوت) |
| `equity` | نقد + ارزش پوزیشن‌ها | ❌ مشتق می‌شه ولی برای UI سریع لازمه |
| `peak_capital`, `peak_equity` | سقف تاریخی | ❌ برای max DD |
| `max_drawdown_pct` | بیشترین افت | ❌ آمار زنده |
| `total_pnl`, `total_pnl_pct` | سود/زیان | ❌ آمار زنده |
| `win_rate` | نرخ برد | ❌ آمار زنده |
| `is_running` | فعال بودن | ❌ برای scheduler |
| `started_at`, `last_check_at`, `check_count` | متادیتای اجرا | ❌ برای scheduler |
| `events`, `radar` | رویدادها + اسکن زنده | ❌ برای UI زنده |

**نتیجه:** فرض ADR 0015 («migration جدید لازم نیست») با داده‌ی جدید رد می‌شه.

### تصمیم تصحیح‌شده

**۱. اضافه‌کردن ستون `paper_meta JSONB DEFAULT '{}'::jsonb NOT NULL` به `users`.**

- `paper_meta` = منبع کامل ۱۰ فیلد بی‌خونه
- ستون‌های موجود User به‌عنوان **view آماری ساده** برای کوئری سریع باقی می‌مونن
- ستون‌های JSONB موجود (`open_positions`, `closed_trades`, `equity_curve`) و اعداد (`capital_available`, `total_trades`, `wins`, `losses`) دست‌نخورده می‌مونن

**۲. `initial_capital` توی `paper_meta` نگه داشته می‌شه — نه `capital_total`.**

دلیل: `capital_total` ممکنه با سود/زیان تغییر کنه، ولی `initial_capital` ثابته (مبنای max_drawdown).

Fallback برای کاربرهای قدیمی (paper_meta خالی):

~~~python
meta = user.paper_meta or {}
state.initial_capital = meta.get("initial_capital", float(user.capital_total))
~~~

**۳. Sync دائمی فقط از طریق `repo.save()`.**

هر جا `UserPaperRepository.save(state)` صدا زده می‌شه، **هم** ستون‌های User **و هم** `paper_meta` آپدیت می‌شن — در یک transaction.

⚠️ **هرگز** مستقیم `session.execute(update(User)...)` نزن — چون ممکنه `paper_meta` desync بشه.

### چرا `paper_meta` JSONB، نه ۱۰ ستون جدید

| معیار | JSONB | ۱۰ ستون |
|---|---|---|
| Forward-compatible (فیلد جدید بدون migration) | ✅ | ❌ |
| Write-heavy (هر ۱۸۰ ثانیه) | ✅ یک `UPDATE` | ❌ |
| Migration اندازه | کوچیک | بزرگ |
| کوئری روی این فیلدها | ❌ (نیاز نداریم) | — |

**نتیجه:** JSONB برنده‌ست چون این فیلدها **فقط برای نمایش UI** هستن، نه برای query.

### چه چیزی در ADR 0015 عوض شد

| بند ADR 0015 | قبل | بعد (Addendum 1) |
|---|---|---|
| Migration | «لازم نیست» | «یک migration کوچیک لازمـه» |
| نگاشت state | «همه‌ی فیلدها توی User هستن» | «۱۰ فیلد توی paper_meta» |
| Subclass تصمیم | الف (بدون تغییر) | الف (بدون تغییر) |
| Scheduler | الف (بدون تغییر) | الف (بدون تغییر) |
| Async repo | الف (بدون تغییر) | الف (بدون تغییر) |

سه تصمیم اصلی ADR 0015 سرجاشون می‌مونن — فقط یک بند تصحیح شد.

### References (اضافه)

- `backend/alembic/versions/` — migration جدید (در همین فاز ساخته می‌شه)
- `app/infrastructure/db/models/user.py` — ستون جدید
- داده‌ی جدید: نگاشت ۲۱ فیلد PaperState → ۸ فیلد User (این سند)
