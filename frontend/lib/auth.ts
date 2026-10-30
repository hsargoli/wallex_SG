/**
 * Auth — مدیریت user_token + اطلاعات کاربر در localStorage.
 *
 * کاربر لاگین‌شده، اولویت داره نسبت به guest-token.
 * اگه user_token وجود داشت، guest_token نادیده گرفته می‌شه.
 */

import { getGuestToken } from "./guest";

const TOKEN_KEY = "sarvbots_user_token";
const INFO_KEY = "sarvbots_user_info";

export interface StoredUser {
  user_id: string;
  email: string;
  capital_total: number;
}

// ═══ Token ═══

export function getUserToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setUserToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearUserToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function hasUserToken(): boolean {
  return getUserToken() !== null;
}

// ═══ Info (cache برای UI سریع) ═══

export function getUserInfo(): StoredUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(INFO_KEY);
    return raw ? (JSON.parse(raw) as StoredUser) : null;
  } catch {
    return null;
  }
}

export function setUserInfo(info: StoredUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(INFO_KEY, JSON.stringify(info));
}

export function clearUserInfo(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(INFO_KEY);
}

// ═══ Full logout ═══

export function fullLogout(): void {
  clearUserToken();
  clearUserInfo();
  // guest_token هم پاک کن — کاربر دیگه مهمان نیست
  localStorage.removeItem("sarvbots_guest_token");
}

// ═══ Access control (per Hosein 2026-10-30: guest allowed for /bots) ═══

/**
 * مسیرهای app که مهمان می‌تواند ببیند (بدون login).
 * /learn در (public) است — نیازی به اینجا نیست.
 * /sarvrouter, /dashboard, /orders, ... هنوز نیاز به login دارند.
 */
export const GUEST_ALLOWED_APP_PATHS = ["/bots"] as const;

export function isGuestAllowedPath(pathname: string): boolean {
  return GUEST_ALLOWED_APP_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
}

/**
 * آیا کاربر می‌تواند به این مسیر app دسترسی داشته باشد؟
 *   - user token دارد → همه‌جا ✅
 *   - guest token دارد → فقط /bots, /bots/[slug] ✅
 *   - هیچ‌کدام → ❌ (باید به /login برود)
 */
export function canAccessAppPath(pathname: string): boolean {
  if (hasUserToken()) return true;
  if (!getGuestToken()) return false;
  return isGuestAllowedPath(pathname);
}

