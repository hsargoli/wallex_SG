from app.services.smart_dispatcher import dispatcher
from app.domain.entities.candle import Candle
# فرض بر این است که ریپازیتوری کندل‌ها را داری؛ مسیرش را چک کن
from app.repositories.candle_repo import get_candles_by_date 

def run_simulation(target_date: str):
    # دریافت کندل‌های یک روز خاص
    candles = get_candles_by_date(target_date)
    
    results = []
    equity = 300000.0  # سرمایه اولیه
    
    # اجرای حلقه زمانی
    for i in range(len(candles)):
        current_chunk = candles[:i+1]
        symbol = candles[i].symbol
        
        # گرفتن تصمیم از دیسپچر
        decision = dispatcher.make_decision(symbol, current_chunk)
        
        if decision and decision.get("should_trade"):
            results.append({
                "time": candles[i].timestamp,
                "symbol": symbol,
                "action": decision
            })
            
    return {"final_equity": equity, "trades_count": len(results), "trades": results}
