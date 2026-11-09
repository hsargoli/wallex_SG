"""ConversationEngine — Human-readable explanations for Copilot decisions (ADR-0042)."""


class ConversationEngine:
    """Rule-based engine: last_decision -> Persian answer."""

    @staticmethod
    def explain(decision: dict) -> str:
        action = decision.get("action", "unknown")
        evidence = decision.get("evidence", {}) or {}
        regime_fa = {
            "uptrend": "صعودی",
            "downtrend": "نزولی",
            "range": "رنج (خنثی)",
            "unknown": "نامشخص",
        }.get(evidence.get("regime", "unknown"), "نامشخص")

        if action == "pending":
            reason = decision.get("why", "")
            if reason == "regime_changed":
                return f"من روند بازار را تغییر یافته به {regime_fa} تشخیص دادم، اما برای اطمینان از اینکه این یک نوسان کاذب نیست، فعلاً منتظر می‌مانم تا روند تثبیت شود."
            stable = evidence.get("stable_candles", 0)
            needed = evidence.get("needed", 0)
            return f"روند {regime_fa} را تشخیص داده‌ام، اما فعلاً پیشنهاد ورود نمی‌دهم. باید {needed} کندل بگذرد تا مطمئن شوم این روند پایدار است (تا الان {stable} کندل گذشته است)."

        if action == "switched":
            bots = evidence.get("active_bots", [])
            bots_fa = "، ".join(bots) if bots else "هیچ رباتی"
            return f"روند بازار به {regime_fa} تغییر کرد و در بازه‌ی زمانی تعیین‌شده پایدار ماند. بنابراین، پیشنهاد من فعال‌سازی {bots_fa} برای استفاده از این فرصت است."

        if action == "cooldown":
            since = evidence.get("since_switch", 0)
            needed = evidence.get("needed", 0)
            if since == 0:
                return "من همین الان یک تصمیم جدید گرفتم (تغییر روند). برای اینکه در دام نوسانات لحظه‌ای بازار نیفتیم، یک دوره انتظار (خنک‌سازی) تنظیم کرده‌ام. پیشنهاد من در حال حاضر صبر کردن است."
            return f"پس از تغییر اخیر، برای جلوگیری از تصمیم‌گیری‌های عجولانه در نوسانات بازار، یک دوره انتظار (خنک‌سازی) در نظر گرفته‌ام. {since} کندل از {needed} کندل این دوره گذشته است."

        if action == "no_change":
            return f"روند {regime_fa} کاملاً پایدار است. نیازی به تغییر در ترکیب ربات‌های فعال نیست و استراتژی فعلی را ادامه می‌دهم."

        if action == "kill_switch_active":
            reason = evidence.get("reason", "auto")
            if reason == "manual":
                return "شما دستور توقف اضطراری را صادر کرده‌اید. تا زمانی که این وضعیت فعال باشد، من هیچ پیشنهاد ورود جدیدی نخواهم داد."
            return "دستور توقف خودکار (احتمالاً به دلیل حد ضرر) فعال شده است. برای محافظت از سرمایه، ورودهای جدید مسدود شده‌اند."

        if action == "daily_loss_kill":
            pnl = evidence.get("daily_pnl_pct", 0)
            return f"متاسفانه حد ضرر روزانه (رسیدن به {pnl:.1f}٪) فعال شد. سیستم برای محافظت از سرمایه‌ی شما به صورت خودکار متوقف شد."

        return f"من در حال حاضر اطلاعات کافی برای توضیح این تصمیم ({action}) را ندارم. لطفاً بعداً دوباره تلاش کنید."
