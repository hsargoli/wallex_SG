"use client";

import { useMemo, useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, ChevronsUpDown, X } from "lucide-react";
import { useMarkets } from "@/lib/queries";
import { cn } from "@/lib/utils";

interface SymbolSwitcherProps {
  current: string;
  basePath?: string;
  suffix?: string;
}

export function SymbolSwitcher({
  current,
  basePath = "/markets",
  suffix = "",
}: SymbolSwitcherProps) {
  const router = useRouter();
  const markets = useMarkets();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const items = markets.data?.items ?? [];
    const q = query.trim().toUpperCase();
    if (!q) return items.slice(0, 100);
    return items
      .filter(
        (m) =>
          m.symbol.toUpperCase().includes(q) ||
          (m.base_asset ?? "").toUpperCase().includes(q) ||
          (m.fa_name ?? "").includes(query),
      )
      .slice(0, 100);
  }, [markets.data, query]);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", onClick);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const handleSelect = (symbol: string) => {
    setOpen(false);
    setQuery("");
    router.push(`${basePath}/${symbol}${suffix}`);
  };

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <style>{`
        .ss-trigger,
        .ss-trigger * {
          color: #f4f4f5 !important;
        }
        .ss-trigger svg {
          color: #a1a1aa !important;
        }
        .ss-item,
        .ss-item .ss-symbol {
          color: #f4f4f5 !important;
        }
        .ss-item[data-active="true"],
        .ss-item[data-active="true"] .ss-symbol {
          color: #10b981 !important;
        }
        .ss-item .ss-name {
          color: #a1a1aa !important;
        }
        .ss-item .ss-badge {
          color: #10b981 !important;
        }
        .ss-input,
        .ss-input::placeholder {
          color: #f4f4f5 !important;
        }
        .ss-input::placeholder {
          color: #71717a !important;
        }
        .ss-footer {
          color: #a1a1aa !important;
        }
        .ss-empty {
          color: #a1a1aa !important;
        }
      `}</style>
      {/* Trigger */}
      <button
        className="ss-trigger"
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.5rem 0.75rem",
          borderRadius: "0.5rem",
          border: "1px solid rgba(255,255,255,0.1)",
          background: "#16161f",
          color: "#f4f4f5",
          cursor: "pointer",
          fontSize: "0.875rem",
        }}
      >
        <Search size={16} style={{ color: "#a1a1aa" }} />
        <span style={{ fontFamily: "monospace" }}>{current}</span>
        <ChevronsUpDown size={14} style={{ color: "#a1a1aa" }} />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            right: 0,
            marginTop: "0.5rem",
            width: "20rem",
            background: "#18181b",
            border: "1px solid rgba(255,255,255,0.15)",
            borderRadius: "0.75rem",
            boxShadow: "0 20px 25px -5px rgba(0,0,0,0.6)",
            zIndex: 100,
            overflow: "hidden",
          }}
        >
          {/* Search input */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.5rem 0.75rem",
              borderBottom: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            <Search size={16} style={{ color: "#a1a1aa" }} />
            <input
              className="ss-input"
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="جستجوی نماد..."
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "#f4f4f5",
                fontSize: "0.875rem",
                textAlign: "right",
                direction: "rtl",
              }}
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#a1a1aa",
                  cursor: "pointer",
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Results */}
          <div style={{ maxHeight: "20rem", overflowY: "auto", padding: "0.25rem 0" }}>
            {markets.isLoading && (
              <div
                className="ss-empty"
                style={{
                  padding: "1.5rem 0.75rem",
                  textAlign: "center",
                  fontSize: "0.75rem",
                }}
              >
                در حال بارگذاری...
              </div>
            )}
            {!markets.isLoading && filtered.length === 0 && (
              <div
                className="ss-empty"
                style={{
                  padding: "1.5rem 0.75rem",
                  textAlign: "center",
                  fontSize: "0.75rem",
                }}
              >
                نتیجه‌ای یافت نشد
              </div>
            )}
            {filtered.map((m) => {
              const active = m.symbol === current;
              return (
                <button
                  key={m.symbol}
                  className="ss-item"
                  data-active={active}
                  onClick={() => handleSelect(m.symbol)}
                  style={{
                    display: "flex",
                    width: "100%",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.5rem 0.75rem",
                    textAlign: "right",
                    fontSize: "0.875rem",
                    background: active ? "rgba(16,185,129,0.1)" : "transparent",
                    color: active ? "#10b981" : "#f4f4f5",
                    border: "none",
                    cursor: "pointer",
                  }}
                  onMouseEnter={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                    <span
                      className="ss-symbol"
                      style={{ fontFamily: "monospace", fontWeight: 500 }}
                    >
                      {m.symbol}
                    </span>
                    {m.fa_name && (
                      <span className="ss-name" style={{ fontSize: "10px" }}>
                        {m.fa_name}
                      </span>
                    )}
                  </div>
                  {active && (
                    <span className="ss-badge" style={{ fontSize: "10px" }}>
                      فعلی
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Footer */}
          {markets.data && (
            <div
              className="ss-footer"
              style={{
                borderTop: "1px solid rgba(255,255,255,0.1)",
                padding: "0.375rem 0.75rem",
                fontSize: "10px",
              }}
            >
              {filtered.length} از {markets.data.count} نماد
            </div>
          )}
        </div>
      )}
    </div>
  );
}
