"""ConversationEngine — Rule-based explanation for Copilot decisions (ADR-0042 MVP)."""


class ConversationEngine:
    """Rule-based engine: last_decision -> Persian answer."""

    @staticmethod
    def explain(decision: dict) -> str:
        action = decision.get("action", "unknown")
        evidence = decision.get("evidence", {}) or {}
        regime_fa = {
            "uptrend": "صعودی",
            "downtrend": "نزولی",
            "range": "رنج",
            "unknown": "نامشخص",
        }.get(evidence.get("regime", "unknown"), "نامشخص")

        if action == "pending":
            reason = decision.get("why", "")
            if reason == "regime_changed":
                return f"منتظر تثبیت روند {regime_fa} هستم. رژیم تازه تغییر کرده است."
            stable = evidence.get("stable_candles", 0)
            needed = evidence.get("needed", 0)
            return (
                f"منتظر تثبیت روند {regime_fa} هستم. "
                f"تا الان {stable} کندل از {needed} کندل لازم پایدار بوده‌ام."
            )

        if action == "switched":
            bots = evidence.get("active_bots", [])
            bots_fa = "، ".join(bots) if bots else "هیچ رباتی"
            return (
                f"روند به {regime_fa} تغییر کرد و پایدار ماند. "
                f"ربات‌های زیر فعال شدند: {bots_fa}."
            )

        if action == "no_change":
            return f"وضعیت روند {regime_fa} بدون تغییر است. استراتژی فعلی ادامه دارد."

        if action == "cooldown":
            since = evidence.get("since_switch", 0)
            needed = evidence.get("needed", 0)
            return (
                f"پس از آخرین تغییر، دوره خنک‌سازی فعال است. "
                f"{since} از {needed} کندل گذشته است."
            )

        if action == "kill_switch_active":
            reason = evidence.get("reason", "auto")
            if reason == "manual":
                return "دستور توقف دستی فعال شده است. ورودهای جدید مسدود است."
            return "دستور توقف خودکار فعال شده است. ورودهای جدید مسدود است."

        if action == "daily_loss_kill":
            pnl = evidence.get("daily_pnl_pct", 0)
            return (
                f"حد ضرر روزانه فعال شد (PnL روزانه: {pnl:.1f}٪). "
                f"سیستم برای محافظت از سرمایه متوقف شد."
            )

        return f"نمی‌دانم چرا این تصمیم ({action}) گرفته شده. اطلاعات کافی موجود نیست."
