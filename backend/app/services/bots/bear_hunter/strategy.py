"""Short strategy: RSI crosses down from 70 (reversal) + ADX > 25 (trend was strong)."""
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
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha=1/period).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    return dx.rolling(window=period).mean()

def check_short_signal(df: pd.DataFrame, idx: int) -> bool:
    if idx < 20: 
        return False
    
    rsi = df['rsi'].iloc[idx]
    prev_rsi = df['rsi'].iloc[idx-1]
    adx = df['adx'].iloc[idx]
    close = df['close'].iloc[idx]
    ema = df['ema'].iloc[idx]
    
    if pd.isna(rsi) or pd.isna(adx) or pd.isna(ema) or pd.isna(prev_rsi): 
        return False
        
    # استراتژی جدید: RSI از بالای 70 به زیر 70 بشکنه (شکار برگشت) + ADX بالای 25 باشه
    rsi_reversal = (prev_rsi > 70) and (rsi < 70)
    strong_trend = adx > 25
    
    return rsi_reversal and strong_trend
