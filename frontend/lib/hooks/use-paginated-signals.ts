"use client";

import { useEffect, useRef, useState } from "react";
import { api, type BatchSignalItem } from "@/lib/api";

const CHUNK_SIZE = 10;  // هر صفحه 10 تا

interface UsePaginatedSignalsOptions {
  symbols: string[];
  tf: string;
  filterFn: (s: BatchSignalItem) => boolean;
  filterKey: string;    // برای reset — مثلاً "buy-strong"
  pageSize?: number;
  currentPage: number;
}

export function usePaginatedSignals({
  symbols,
  tf,
  filterFn,
  filterKey,
  pageSize = 10,
  currentPage,
}: UsePaginatedSignalsOptions) {
  const [matches, setMatches] = useState<BatchSignalItem[]>([]);
  const [loadedUpTo, setLoadedUpTo] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [isDone, setIsDone] = useState(false);

  // Keep filterFn in ref (avoid dependency churn)
  const filterRef = useRef(filterFn);
  filterRef.current = filterFn;

  // ---------- Reset when filter or symbols change ----------
  useEffect(() => {
    setMatches([]);
    setLoadedUpTo(0);
    setIsFetching(false);
    setIsDone(false);
  }, [filterKey, tf, symbols.length]);

  // ---------- Auto-fetch more when needed ----------
  useEffect(() => {
    const needed = currentPage * pageSize;

    if (matches.length >= needed) return;   // already enough
    if (isDone) return;                     // no more symbols
    if (isFetching) return;                 // already fetching
    if (symbols.length === 0) return;

    const start = loadedUpTo;
    const end = Math.min(start + CHUNK_SIZE, symbols.length);
    const chunk = symbols.slice(start, end);

    if (chunk.length === 0) {
      setIsDone(true);
      return;
    }

    setIsFetching(true);
    api
      .getBatchSignals({ symbols: chunk, tf, limit: 200 })
      .then((result) => {
        const newMatches = result.signals.filter(filterRef.current);
        setMatches((prev) => [...prev, ...newMatches]);
        setLoadedUpTo(end);
        if (end >= symbols.length) setIsDone(true);
      })
      .catch(() => {
        setLoadedUpTo(end);
        if (end >= symbols.length) setIsDone(true);
      })
      .finally(() => setIsFetching(false));
  }, [
    currentPage,
    pageSize,
    matches.length,
    loadedUpTo,
    isFetching,
    isDone,
    symbols,
    tf,
  ]);

  return {
    matches,
    isFetching,
    isDone,
    loadedCount: loadedUpTo,
    totalCount: symbols.length,
  };
}
