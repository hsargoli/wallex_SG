"use client";

import { useEffect, useRef, useState } from "react";

export type LiveTickerState = {
  price: string;
  change24h: number;
  lastUpdate: number | null;
  connected: boolean;
};

const STALE_MS = 5000;
const RECONNECT_MS = 3000;

function getWsUrl(symbol: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
  return `${base}/ws/ticker/${symbol}`;
}

/**
 * hook اتصال زنده به /ws/ticker/{symbol}.
 *
 * - reconnect خودکار هر ۳ ثانیه اگه قطع شد
 * - stale = اگه آخرین پیام بیش از ۵ ثانیه پیش بود
 * - cleanup کامل موقع unmount
 */
export function useLiveTicker(symbol: string): LiveTickerState & { stale: boolean } {
  const [state, setState] = useState<LiveTickerState>({
    price: "",
    change24h: 0,
    lastUpdate: null,
    connected: false,
  });
  const [now, setNow] = useState(() => Date.now());
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(getWsUrl(symbol));
      wsRef.current = ws;

      ws.onopen = () => {
        setState((s) => ({ ...s, connected: true }));
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as Record<string, unknown>;
          setState({
            price: String(data.price ?? ""),
            change24h: Number(data["24h_ch"] ?? 0),
            lastUpdate: Date.now(),
            connected: true,
          });
        } catch {
          /* ignore malformed */
        }
      };

      ws.onclose = () => {
        setState((s) => ({ ...s, connected: false }));
        if (!cancelled) {
          reconnectTimer.current = setTimeout(connect, RECONNECT_MS);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [symbol]);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const stale = state.lastUpdate === null || now - state.lastUpdate > STALE_MS;
  return { ...state, stale };
}
