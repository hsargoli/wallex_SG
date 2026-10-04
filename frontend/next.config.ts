import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // خاموش کردن indicator شناور Next.js در پایین صفحه
  // (با sidebar و RTL تداخل داشت)
  devIndicators: false,

  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
