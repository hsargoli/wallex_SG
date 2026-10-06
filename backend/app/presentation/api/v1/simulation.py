"""Simulation endpoints — شبیه‌سازی تاریخی."""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, date, timedelta
import jdatetime

from app.services.simulator_engine import Simulator
from app.services.bot_simulator import BotSimulator, list_simulatable_bots
from app.services.bots import bot_registry
from app.domain.strategy import SimpleTrendStrategy
from app.infrastructure.wallex_repo import WallexMarketData

router = APIRouter(prefix="/simulation", tags=["Simulation"])


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------
class DateItem(BaseModel):
    gregorian: str
    jalali: str
    jalali_pretty: str


class AvailableDatesResponse(BaseModel):
    dates: List[DateItem]


class BotOption(BaseModel):
    slug: str
    name: str
    name_en: str
    description: str
    tags: List[str]
    capabilities: List[str]
    experimental: bool = False
    warning: str = ""


class BotsResponse(BaseModel):
    count: int
    bots: List[BotOption]


class SymbolOption(BaseModel):
    symbol: str           # BTCUSDT
    base: str             # BTC
    name_fa: str          # بیت‌کوین
    name_en: str          # Bitcoin


class SymbolsResponse(BaseModel):
    count: int
    symbols: List[SymbolOption]


class CompareResultItem(BaseModel):
    bot_slug: str
    bot_name: str
    name_en: str
    experimental: bool = False
    warning: str = ""
    status: str
    total_trades: int = 0
    win_rate: float = 0.0
    pnl_pct: float = 0.0
    final_balance: float = 0.0
    total_pnl: float = 0.0
    error: str = ""


class CompareResponse(BaseModel):
    symbol: str
    dates: dict
    results: List[CompareResultItem]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def gregorian_to_jalali(g_str: str) -> str:
    g = datetime.strptime(g_str, "%Y-%m-%d").date()
    j = jdatetime.date.fromgregorian(date=g)
    return j.strftime("%Y/%m/%d")


def gregorian_to_jalali_pretty(g_str: str) -> str:
    g = datetime.strptime(g_str, "%Y-%m-%d").date()
    j = jdatetime.date.fromgregorian(date=g)
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    return f"{j.day} {months[j.month - 1]} {j.year}"


def parse_any_date(date_str: str) -> str:
    """پشتیبانی از ورودی شمسی و میلادی."""
    date_str = date_str.strip().replace("-", "/")
    parts = date_str.split("/")
    if len(parts) != 3:
        raise ValueError(f"فرمت تاریخ نامعتبر: {date_str}")

    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

    if year < 1700:
        try:
            j = jdatetime.date(year, month, day)
            return j.togregorian().strftime("%Y-%m-%d")
        except Exception as e:
            raise ValueError(f"تاریخ شمسی نامعتبر: {date_str} ({e})")
    else:
        try:
            return date(year, month, day).strftime("%Y-%m-%d")
        except Exception as e:
            raise ValueError(f"تاریخ میلادی نامعتبر: {date_str} ({e})")


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------
@router.get("/available-dates", response_model=AvailableDatesResponse)
async def get_available_dates(days: int = Query(90, ge=1, le=365)):
    today = date.today()
    items = []
    for i in range(days):
        d = today - timedelta(days=i)
        g_str = d.strftime("%Y-%m-%d")
        items.append(DateItem(
            gregorian=g_str,
            jalali=gregorian_to_jalali(g_str),
            jalali_pretty=gregorian_to_jalali_pretty(g_str),
        ))
    return {"dates": items}


# هشدارها و وضعیت experimental برای ربات‌ها
BOT_WARNINGS = {
    "mean_revert": {
        "experimental": True,
        "warning": (
            "این ربات برای تایم‌فریم 15m طراحی شده، ولی والکس این تایم‌فریم را "
            "پشتیبانی نمی‌کند و ما مجبوریم روی 1h اجرا کنیم. "
            "نتایج ممکن است دقیق نباشند. توصیه می‌شود فعلاً از این ربات برای تحلیل استفاده نکنید."
        ),
    },
}


@router.get("/bots", response_model=BotsResponse)
async def get_simulation_bots():
    """لیست ربات‌های قابل شبیه‌سازی."""
    available_slugs = set(list_simulatable_bots())
    bots = []
    for slug in available_slugs:
        bot = bot_registry.get(slug)
        if bot is None:
            continue
        info = bot.info
        warn = BOT_WARNINGS.get(slug, {})
        bots.append(BotOption(
            slug=info.slug,
            name=info.name,
            name_en=info.name_en,
            description=info.description,
            tags=info.tags,
            capabilities=info.capabilities,
            experimental=warn.get("experimental", False),
            warning=warn.get("warning", ""),
        ))
    # مرتب‌سازی بر اساس نام
    bots.sort(key=lambda b: b.name)
    return {"count": len(bots), "bots": bots}


# نمادهای پیشنهادی برای شبیه‌سازی (نقدشونده و پرحجم والکس)
SIMULATION_SYMBOLS = [
    {"symbol": "BTCUSDT",  "base": "BTC",  "name_fa": "بیت‌کوین",       "name_en": "Bitcoin"},
    {"symbol": "ETHUSDT",  "base": "ETH",  "name_fa": "اتریوم",         "name_en": "Ethereum"},
    {"symbol": "BNBUSDT",  "base": "BNB",  "name_fa": "بایننس‌کوین",    "name_en": "BNB"},
    {"symbol": "SOLUSDT",  "base": "SOL",  "name_fa": "سولانا",         "name_en": "Solana"},
    {"symbol": "XRPUSDT",  "base": "XRP",  "name_fa": "ریپل",           "name_en": "XRP"},
    {"symbol": "ADAUSDT",  "base": "ADA",  "name_fa": "کاردانو",        "name_en": "Cardano"},
    {"symbol": "DOGEUSDT", "base": "DOGE", "name_fa": "دوج‌کوین",       "name_en": "Dogecoin"},
]


@router.get("/symbols", response_model=SymbolsResponse)
async def get_simulation_symbols():
    """لیست نمادهای پیشنهادی برای شبیه‌سازی."""
    return {
        "count": len(SIMULATION_SYMBOLS),
        "symbols": SIMULATION_SYMBOLS,
    }


@router.post("/compare", response_model=CompareResponse)
async def compare_simulations(
    start_date: str = Query(..., description="YYYY-MM-DD یا 1405/06/10"),
    end_date: str = Query(..., description="YYYY-MM-DD یا 1405/06/10"),
    symbol: str = Query("BTCUSDT", description="نماد معاملاتی"),
    initial_balance: float = Query(1000.0, ge=10.0, le=10_000_000.0,
                                   description="سرمایه اولیه (USDT)"),
    timeframe: str = Query("1h", description="تایم‌فریم: 1h | 4h | 1D"),
):
    """
    اجرای همه ربات‌های قابل شبیه‌سازی روی یک رمزارز و بازه‌ی مشخص.
    نتایج بر اساس PnL نزولی مرتب می‌شوند.
    """
    try:
        start_g = parse_any_date(start_date)
        end_g = parse_any_date(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if start_g > end_g:
        raise HTTPException(
            status_code=400,
            detail="تاریخ شروع باید قبل از تاریخ پایان باشه",
        )

    repo = WallexMarketData()
    results: List[CompareResultItem] = []

    # اجرای همه ربات‌ها
    for slug in list_simulatable_bots():
        # اطلاعات ربات برای نمایش
        bot = bot_registry.get(slug)
        if bot is None:
            continue
        info = bot.info
        warn = BOT_WARNINGS.get(slug, {})

        base_item = {
            "bot_slug": slug,
            "bot_name": info.name,
            "name_en": info.name_en,
            "experimental": warn.get("experimental", False),
            "warning": warn.get("warning", ""),
        }

        try:
            simulator = BotSimulator(repo, slug, initial_balance=initial_balance)
            r = await simulator.run(start_g, end_g, symbol, timeframe)
            p = r.get("pnl_report", {})

            results.append(CompareResultItem(
                **base_item,
                status=r.get("status", "error"),
                total_trades=p.get("total_trades", 0),
                win_rate=p.get("win_rate", 0.0),
                pnl_pct=p.get("pnl_pct", 0.0),
                final_balance=p.get("final_balance", 0.0),
                total_pnl=p.get("total_pnl", 0.0),
                error=r.get("message", ""),
            ))
        except Exception as e:
            results.append(CompareResultItem(
                **base_item,
                status="error",
                error=str(e)[:200],
            ))

    # مرتب‌سازی نزولی بر اساس pnl_pct
    results.sort(key=lambda x: x.pnl_pct, reverse=True)

    return {
        "symbol": symbol,
        "dates": {
            "start": {
                "gregorian": start_g,
                "jalali": gregorian_to_jalali(start_g),
                "jalali_pretty": gregorian_to_jalali_pretty(start_g),
            },
            "end": {
                "gregorian": end_g,
                "jalali": gregorian_to_jalali(end_g),
                "jalali_pretty": gregorian_to_jalali_pretty(end_g),
            },
        },
        "results": results,
    }


@router.post("/run")
async def run_simulation(
    start_date: str = Query(..., description="YYYY-MM-DD یا 1405/06/10"),
    end_date: str = Query(..., description="YYYY-MM-DD یا 1405/06/10"),
    symbol: str = Query("BTCUSDT", description="نماد معاملاتی"),
    bot_slug: str = Query(
        "",
        description="slug ربات. اگه خالی باشه، استراتژی پیش‌فرض (EMA cross) استفاده می‌شه.",
    ),
    initial_balance: float = Query(1000.0, ge=10.0, le=10_000_000.0,
                                   description="سرمایه اولیه (USDT)"),
    timeframe: str = Query("1h", description="تایم‌فریم: 1h | 4h | 1D"),
):
    try:
        start_g = parse_any_date(start_date)
        end_g = parse_any_date(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if start_g > end_g:
        raise HTTPException(
            status_code=400,
            detail="تاریخ شروع باید قبل از تاریخ پایان باشه",
        )

    repo = WallexMarketData()

    if bot_slug:
        try:
            simulator = BotSimulator(repo, bot_slug, initial_balance=initial_balance)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        result = await simulator.run(start_g, end_g, symbol, timeframe)
    else:
        strategy = SimpleTrendStrategy()
        simulator = Simulator(repo, strategy)
        # توجه: Simulator فعلاً initial_balance رو پارامتر نمی‌گیره
        result = await simulator.run(start_g, end_g, symbol, timeframe)

    result["dates"] = {
        "start": {
            "gregorian": start_g,
            "jalali": gregorian_to_jalali(start_g),
            "jalali_pretty": gregorian_to_jalali_pretty(start_g),
        },
        "end": {
            "gregorian": end_g,
            "jalali": gregorian_to_jalali(end_g),
            "jalali_pretty": gregorian_to_jalali_pretty(end_g),
        },
    }
    return result
