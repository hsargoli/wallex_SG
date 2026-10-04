"use client";

import { useEffect, useRef, useState } from "react";
import { api, type TrendResult } from "@/lib/api";

const CHUNK_SIZE = 10;

interface UsePaginatedScannerOptions {
  symbols: string[];
  tf: string;
  filterFn: (it: TrendResult) => boolean;
  filterKey: string;
  pageSize?: number;
  currentPage: number;
}

export function usePaginatedScanner({
  symbols,
  tf,
  filterFn,
  filterKey,
  pageSize = 15,
  currentPage,
}: UsePaginatedScannerOptions) {
  const [matches, setMatches] = useState<TrendResult[]>([]);
  const [loadedUpTo, setLoadedUpTo] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [isDone, setIsDone] = useState(false);

  const filterRef = useRef(filterFn);
  filterRef.current = filterFn;

  // Reset when filter or symbols change
  useEffect(() => {
    setMatches([]);
    setLoadedUpTo(0);
    setIsFetching(false);
    setIsDone(false);
  }, [filterKey, tf, symbols.length]);

  // Auto-fetch more when needed
  useEffect(() => {
    const needed = currentPage * pageSize;

    if (matches.length >= needed) return; // already enough
    if (isDone) return;                   // no more symbols
    if (isFetching) return;               // already fetching
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
      .scanSymbols(chunk, tf)
      .then((res) => {
        const filtered = res.items.filter((it) => filterRef.current(it));
        setMatches((prev) => [...prev, ...filtered]);
        setLoadedUpTo(end);
        if (end >= symbols.length) setIsDone(true);
      })
      .catch(() => {
        setLoadedUpTo(end);
        if (end >= symbols.length) setIsDone(true);
      })
      .finally(() => {
        setIsFetching(false);
      });
  }, [currentPage, pageSize, symbols, tf, matches.length, isDone, isFetching, loadedUpTo]);

  const pageItems = matches.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  const hasMoreToLoad = loadedUpTo < symbols.length && !isDone;

  return {
    items: pageItems,
    totalMatches: matches.length,
    totalSymbols: symbols.length,
    totalScanned: loadedUpTo,
    isComplete: isDone && loadedUpTo >= symbols.length,
    isLoading: isFetching || (matches.length < currentPage * pageSize && !isDone),
    hasMoreToLoad,
  };
}
