"""Wrapper: override TP_ATR_MULT at runtime."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.services.bots.sarv_tiger.analyzer.backtest_analyzer_only as bt

if len(sys.argv) < 2:
    print("usage: run_analyzer_backtest_tp.py <tp_atr> [args...]")
    sys.exit(1)

bt.TP_ATR_MULT = float(sys.argv[1])
sys.argv = ["run_analyzer_backtest.py"] + sys.argv[2:]

from scripts.run_analyzer_backtest import main
sys.exit(main())
