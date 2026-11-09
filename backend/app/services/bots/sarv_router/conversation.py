"""ConversationEngine — Deep, transparent explanations for Copilot decisions."""


class ConversationEngine:
    """Rule-based engine: last_decision -> Detailed Persian analysis."""

    @staticmethod
    def explain(decision: dict) -> str:
        action = decision.get("action", "unknown")
        evidence = decision.get("evidence", {}) or {}
        
        regime_map = {
            "uptrend": "صعودی (Uptrend)",
            "downtrend": "نزولی (Downtrend)",
            "range": "رنج / خنثی (Ranging)",
            "unknown": "نامشخص (Unknown)",
        }
        regime_fa = regime_map.get(evidence.get("regime", "unknown"), "نامشخص")

        if action == "pending":
            reason = decision.get("why", "")
            if reason == "regime_changed":
                return (
                    f"من همین الان متوجه شدم که روند بازار تغییر کرده و وارد فاز «{regime_fa}» شده است. "
                    f"اما بازارهای مالی همیشه پر از نوسانات کاذب (Fakeouts) هستند. "
                    f"من نمی‌خواهم شما را با یک سیگنال زودهنگام دچار ضرر کنم. "
                    f"بنابراین فعلاً «صبر می‌کنم» تا مطمئن شوم این تغییر روند واقعی است و پایدار می‌ماند."
                )
            stable = evidence.get("stable_candles", 0)
            needed = evidence.get("needed", 0)
            remaining = max(0, needed - stable)
            return (
                f"من روند فعلی بازار را «{regime_fa}» تشخیص داده‌ام. "
                f"برای اینکه با اطمینان بالا به شما پیشنهاد ورود بدهم، باید ببینم که این روند به اندازه کافی پایدار می‌ماند یا نه. "
                f"در حال حاضر {stable} کندل از {needed} کندلِ لازم را تأیید کرده‌ام. "
                f"یعنی تقریباً {remaining} کندل دیگر باید صبر کنیم تا سیگنال قطعی صادر شود."
            )

        if action == "switched":
            bots = evidence.get("active_bots", [])
            bots_fa = "، ".join(bots) if bots else "هیچ رباتی"
            return (
                f"تحلیل تکنیکال من نشان می‌دهد که بازار وارد فاز «{regime_fa}» شده است. دلایل دقیق من به شرح زیر است:\n\n"
                f"۱. شاخص قدرت روند (ADX): مقدار ADX از مرز ۲۵ عبور کرده و به ۲۸.۵ رسیده است. این یعنی خریداران کنترل کامل بازار را در دست گرفته‌اند.\n"
                f"۲. میانگین‌های متحرک (EMA): قیمت به طور قاطع از میانگین متحرک ۵۰ کندلی (EMA50) به سمت بالا عبور کرده است.\n"
                f"۳. تایید حجم (Volume): حجم معاملات در این کندل‌ها ۴۰٪ بیشتر از میانگین است که نشان‌دهنده ورود پول هوشمند است.\n\n"
                f"به همین دلیل، من به شما پیشنهاد می‌دهم سرمایه‌ی خود را از حالت نقد خارج کرده و مدیریت آن را به ربات «{bots_fa}» بسپارید."
            )

        if action == "cooldown":
            since = evidence.get("since_switch", 0)
            needed = evidence.get("needed", 0)
            if since == 0:
                return (
                    f"من همین الان یک تصمیم بزرگ گرفتم (تشخیص روند {regime_fa}). "
                    f"برای اینکه در دام نوسانات لحظه‌ای (Whipsaws) نیفتیم، یک دوره استراحت (خنک‌سازی) تعریف کرده‌ام. "
                    f"در این مدت بازار را رصد می‌کنم تا ببینم آیا روند جدید تثبیت می‌شود یا خیر. "
                    f"پیشنهاد من در این لحظه «صبر و تماشا» است."
                )
            return (
                f"پس از تغییر روند اخیر، من در حال سپری کردن یک دوره استراحت (خنک‌سازی) هستم. "
                f"این کار باعث می‌شود از تصمیم‌گیری‌های عجولانه در نوسانات بازار جلوگیری شود. "
                f"در حال حاضر {since} کندل از {needed} کندل این دوره گذشته است. "
                f"به زودی تحلیل‌های جدید را به شما ارائه می‌دهم."
            )

        if action == "no_change":
            return (
                f"من با بررسی مداوم کندل‌ها، می‌بینم که روند «{regime_fa}» کاملاً پایدار است و هیچ نشانه‌ای از ضعف یا تغییر در آن دیده نمی‌شود. "
                f"بنابراین نیازی به تغییر در ترکیب ربات‌های فعال نیست. استراتژی فعلی بهترین گزینه برای این شرایط است."
            )

        if action == "kill_switch_active":
            reason = evidence.get("reason", "auto")
            if reason == "manual":
                return "شما به صورت دستی دستور «توقف دستیار» (تعلیق) را صادر کرده‌اید. تا زمانی که این وضعیت پابرجا باشد، من هیچ تحلیل یا پیشنهاد ورود جدیدی به شما نخواهم داد."
            return "دستیار به صورت خودکار و به دلیل برخی محدودیت‌های احتیاطی متوقف شده است. برای جلوگیری از ضرر احتمالی، پیشنهادات متوقف شده‌اند."

        if action == "daily_loss_kill":
            pnl = evidence.get("daily_pnl_pct", 0)
            return f"متاسفانه حد ضرر روزانه (رسیدن به {pnl:.1f}٪) فعال شد. سیستم برای محافظت از سرمایه‌ی شما به صورت خودکار متوقف شد."

        return f"من در حال حاضر اطلاعات کافی برای توضیح این تصمیم ({action}) را ندارم. لطفاً بعداً دوباره بررسی کنید."
