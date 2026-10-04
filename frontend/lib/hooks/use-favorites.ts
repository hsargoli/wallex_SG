"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "wallex-favorite-markets";

/**
 * هوک مدیریت علاقه‌مندی‌های بازار (localStorage).
 *
 * الگو:
 *   const { favorites, toggle, isFavorite } = useFavorites();
 */
export function useFavorites() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [mounted, setMounted] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setFavorites(parsed.filter((x) => typeof x === "string"));
        }
      }
    } catch {
      // ignore
    }
  }, []);

  const persist = useCallback((list: string[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    } catch {
      // ignore
    }
  }, []);

  const toggle = useCallback(
    (symbol: string) => {
      setFavorites((prev) => {
        const next = prev.includes(symbol)
          ? prev.filter((s) => s !== symbol)
          : [...prev, symbol];
        persist(next);
        return next;
      });
    },
    [persist],
  );

  const isFavorite = useCallback(
    (symbol: string) => favorites.includes(symbol),
    [favorites],
  );

  return { favorites, toggle, isFavorite, mounted };
}
