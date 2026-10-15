/**
 * Guest Mode — مدیریت guest-token در localStorage.
 *
 * Guest-token یه UUID v4 هست که از /v1/guest/anonymous می‌گیریم
 * و توی localStorage ذخیره می‌کنیم.
 *
 * اگه localStorage پاک شه، پول مجازی مهمان از دست می‌ره (طبق طراحی).
 */

const STORAGE_KEY = "sarvbots_guest_token";

export function getGuestToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setGuestToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearGuestToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

export function hasGuestToken(): boolean {
  return getGuestToken() !== null;
}
