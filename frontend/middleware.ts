import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const token = req.cookies.get("user_token")?.value || req.headers.get("authorization");

  // اگر کاربر لاگین نیست و می‌خواهد به مسیرهای تنظیمات یا داشبورد برود
  if (!token && (req.nextUrl.pathname.startsWith("/settings") || req.nextUrl.pathname === "/dashboard")) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/settings/:path*", "/dashboard"],
};
