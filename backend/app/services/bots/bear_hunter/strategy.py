"""Short strategy: RSI reversal + ADX trend + Volume filter + ATR-based levels."""
import pandas as pd


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_ema(series: pd.Series, period: int = 20) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    tr = pd.concat([tr1, tr2, tr3], axis=1, join='inner').max(axis=1)
    atr = tr.rolling(window=period).mean()

    plus_di = 100 * (plus_dm.ewm(alpha=1 / period).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha=1 / period).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    return dx.rolling(window=period).mean()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_volume_z(volume: pd.Series, period: int = 20) -> pd.Series:
    mean = volume.rolling(period).mean()
    std = volume.rolling(period).std()
    return (volume - mean) / std


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators to a DataFrame."""
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'])
    df['ema'] = calculate_ema(df['close'])
    df['adx'] = calculate_adx(df['high'], df['low'], df['close'])
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    df['vol_z'] = calculate_volume_z(df['volume']) if 'volume' in df.columns else 0.0
    return df


def check_short_signal(df: pd.DataFrame, idx: int, config) -> dict | None:
    """
    Returns dict with {sl, tp, atr_abs} if signal valid, else None.
    Multi-condition: RSI reversal + strong trend + volume filter.
    """
    if idx < 20:
        return None

    row = df.iloc[idx]
    prev = df.iloc[idx - 1]

    for col in ['rsi', 'adx', 'atr', 'ema', 'vol_z']:
        if pd.isna(row[col]):
            return None
    if pd.isna(prev['rsi']):
        return None

    # 1) RSI reversal: was overbought, now dropping below 70
    rsi_reversal = (prev['rsi'] > config.rsi_overbought) and (row['rsi'] < config.rsi_overbought)

    # 2) Strong trend (ADX)
    strong_trend = row['adx'] > config.adx_min

    # 3) Volume filter (avoid low-liquidity fake signals)
    volume_ok = row['vol_z'] > config.volume_z_min

    if not (rsi_reversal and strong_trend and volume_ok):
        return None

    # ATR-based levels (for SHORT: SL above, TP below)
    entry = float(row['close'])
    atr = float(row['atr'])
    sl = entry + atr * config.sl_atr_mult
    tp = entry - atr * config.tp_atr_mult

    return {"sl": sl, "tp": tp, "atr_abs": atr}
