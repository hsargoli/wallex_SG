"""Strategy: Human gives direction. Bot finds optimal entry/exit using TA."""
import pandas as pd

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(series: pd.Series, period: int = 20) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

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
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'])
    df['ema'] = calculate_ema(df['close'])
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    df['vol_z'] = calculate_volume_z(df['volume']) if 'volume' in df.columns else 0.0
    return df

def find_entry_signal(df: pd.DataFrame, idx: int, direction: str, config) -> dict | None:
    """
    Bot's job: Find a good entry point for the HUMAN-GIVEN direction.
    - If bearish: Short when RSI is overbought (wave top).
    - If bullish: Long when RSI is oversold (wave bottom).
    """
    if idx < 25:
        return None

    row = df.iloc[idx]
    prev = df.iloc[idx - 1]

    if pd.isna(row['rsi']) or pd.isna(prev['rsi']) or pd.isna(row['atr']):
        return None

    entry = float(row['close'])
    atr = float(row['atr'])
    
    # 1. Bearish Entry (Short at wave top)
    if direction == "bearish":
        if prev['rsi'] > 70 and row['rsi'] < 70:
            sl = entry + (atr * config.sl_atr_mult) # SL above entry
            tp = entry - (atr * config.tp_atr_mult) # TP below entry
            return {"direction": "short", "sl": sl, "tp": tp, "atr": atr}

    # 2. Bullish Entry (Long at wave bottom)
    elif direction == "bullish":
        if prev['rsi'] < 30 and row['rsi'] > 30:
            sl = entry - (atr * config.sl_atr_mult) # SL below entry
            tp = entry + (atr * config.tp_atr_mult) # TP above entry
            return {"direction": "long", "sl": sl, "tp": tp, "atr": atr}

    return None
