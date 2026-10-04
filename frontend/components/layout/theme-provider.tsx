"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

type Theme = "light" | "dark" | "system";
type ColorTheme = "default" | "blue" | "purple" | "orange" | "rose";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  resolvedTheme: "light" | "dark";
  colorTheme: ColorTheme;
  setColorTheme: (c: ColorTheme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const THEME_KEY = "wallex-theme";
const COLOR_KEY = "wallex-color-theme";

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(resolved: "light" | "dark", color: ColorTheme) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;

  // Apply dark/light class
  root.classList.remove("light", "dark");
  root.classList.add(resolved);

  // Apply color theme
  root.setAttribute("data-color", color);

  // Update color-scheme for native elements (scrollbars, etc.)
  root.style.colorScheme = resolved;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [colorTheme, setColorThemeState] = useState<ColorTheme>("default");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("dark");
  const [mounted, setMounted] = useState(false);

  // ---------- Initialize from localStorage ----------
  useEffect(() => {
    setMounted(true);

    try {
      const savedTheme = (localStorage.getItem(THEME_KEY) as Theme) || "dark";
      const savedColor =
        (localStorage.getItem(COLOR_KEY) as ColorTheme) || "default";

      setThemeState(savedTheme);
      setColorThemeState(savedColor);

      const resolved = savedTheme === "system" ? getSystemTheme() : savedTheme;
      setResolvedTheme(resolved);
      applyTheme(resolved, savedColor);
    } catch {
      // ignore
    }
  }, []);

  // ---------- React to theme changes ----------
  useEffect(() => {
    if (!mounted) return;
    const resolved = theme === "system" ? getSystemTheme() : theme;
    setResolvedTheme(resolved);
    applyTheme(resolved, colorTheme);
  }, [theme, colorTheme, mounted]);

  // ---------- Listen to system theme changes ----------
  useEffect(() => {
    if (!mounted || theme !== "system") return;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const resolved = media.matches ? "dark" : "light";
      setResolvedTheme(resolved);
      applyTheme(resolved, colorTheme);
    };

    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, [theme, colorTheme, mounted]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem(THEME_KEY, t);
    } catch {
      // ignore
    }
  }, []);

  const setColorTheme = useCallback((c: ColorTheme) => {
    setColorThemeState(c);
    try {
      localStorage.setItem(COLOR_KEY, c);
    } catch {
      // ignore
    }
  }, []);

  // Until mounted, pass through children without provider (SSR-safe)
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        resolvedTheme,
        colorTheme,
        setColorTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Fallback برای کامپوننت‌هایی که قبل از mount رندر میشن
    return {
      theme: "dark" as Theme,
      setTheme: () => {},
      resolvedTheme: "dark" as const,
      colorTheme: "default" as ColorTheme,
      setColorTheme: () => {},
    };
  }
  return ctx;
}
