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
