# ADR-0004: NEXT_PUBLIC_API_URL mismatch (pre-existing, defer)

**تاریخ:** 2026-10-30
**وضعیت:** Proposed (defer)
**نویسنده:** دی رود

## Context
در frontend/lib/api.ts خطوط 1133-1198، چند تابع fallback به 127.0.0.1:8000 دارند (backend noosharp، نه wallex).
client اصلی (خط 64) درست است: baseURL: "/api/backend" → nginx proxy → 8020 ✅

## Decision
Defer — fix در sprint بعد. صفحات جدید تحت تأثیر نیستند (از client اصلی استفاده می‌کنند).

## Fix Plan (future)
1. همه‌ی process.env.NEXT_PUBLIC_API_URL || 127.0.0.1:8000 → /api/backend
2. NEXT_PUBLIC_API_URL=/api/backend در .env.local سرور
3. تست integration برای ۶ تابع
