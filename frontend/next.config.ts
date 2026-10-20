import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  // خاموش کردن strict mode — رفع مشکل next-themes + React 19
  reactStrictMode: false,

  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8020/:path*",
      },
    ];
  },
};

export default nextConfig;
