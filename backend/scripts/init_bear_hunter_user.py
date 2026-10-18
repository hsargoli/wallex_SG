"""Init bear_hunter state for a user (CLI testing)."""
import sys, uuid, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.bots.bear_hunter.state import BearHunterState, StateStore
from app.services.bots.bear_hunter.paths import user_state_path

parser = argparse.ArgumentParser()
parser.add_argument("user_id")
parser.add_argument("--direction", default="bearish", choices=["bearish", "bullish", "neutral"])
parser.add_argument("--ttl-days", type=int, default=10)
parser.add_argument("--live", action="store_true", help="paper_mode=False")
parser.add_argument("--capital", type=float, default=100_000.0)
parser.add_argument("--note", default=None)
args = parser.parse_args()

uid = uuid.UUID(args.user_id)
path = user_state_path(uid)
store = StateStore(path=str(path))
if path.exists():
    state = store.load()
    print(f"⚠️  already exists: {path}")
    print(f"   paper_mode={state.paper_mode} status={state.bot_status}")
else:
    state = BearHunterState()
    state.capital_tmn = args.capital
    state.paper_mode = not args.live
    state.set_signal(args.direction, args.ttl_days, set_by="cli", note=args.note)
    store.bootstrap(state)
    print(f"✅ Created: {path}")
    print(f"   paper_mode={state.paper_mode} capital={state.capital_tmn}")
    print(f"   signal={state.human_signal.direction} status={state.bot_status}")
