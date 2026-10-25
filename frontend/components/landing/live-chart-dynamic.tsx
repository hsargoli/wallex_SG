"use client";

import dynamic from "next/dynamic";

// Client wrapper: ssr:false is only allowed inside Client Components
// (Next.js 15+ rule). Server Component pages import this wrapper.
export const LiveChartDynamic = dynamic(
  () => import("@/components/landing/live-chart").then((m) => m.LiveChart),
  {
    ssr: false,
    // CLS-safe: matches LiveChart's internal fallback height (line 156)
    loading: () => (
      <div className="h-[400px] w-full animate-pulse rounded-xl bg-muted/20" />
    ),
  },
);
