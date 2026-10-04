"use client";

import { useEffect, useState } from "react";
import { Moon, Sun, Monitor, Palette, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

type Theme = "light" | "dark" | "system";
type ColorTheme = "default" | "blue" | "purple" | "orange" | "rose";

const COLOR_THEMES: { id: ColorTheme; label: string; color: string }[] = [
  { id: "default", label: "پیش‌فرض", color: "oklch(0.72 0.17 162)" },
  { id: "blue", label: "آبی", color: "oklch(0.68 0.17 240)" },
  { id: "purple", label: "بنفش", color: "oklch(0.65 0.20 300)" },
  { id: "orange", label: "نارنجی", color: "oklch(0.72 0.18 60)" },
  { id: "rose", label: "رز", color: "oklch(0.65 0.20 15)" },
];

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(theme: Theme, color: ColorTheme) {
  const root = document.documentElement;
  const resolved = theme === "system" ? getSystemTheme() : theme;

  root.classList.remove("light", "dark");
  root.classList.add(resolved);
  root.setAttribute("data-color", color);
  root.style.colorScheme = resolved;
}

export function ThemeSwitcher() {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [colorTheme, setColorThemeState] = useState<ColorTheme>("default");
  const [mounted, setMounted] = useState(false);

  // Init
  useEffect(() => {
    setMounted(true);
    try {
      const saved = (localStorage.getItem("wallex-theme") as Theme) || "dark";
      const savedColor =
        (localStorage.getItem("wallex-color-theme") as ColorTheme) || "default";
      setThemeState(saved);
      setColorThemeState(savedColor);
      applyTheme(saved, savedColor);
    } catch {
      // ignore
    }
  }, []);

  const handleSetTheme = (t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem("wallex-theme", t);
    } catch {
      // ignore
    }
    applyTheme(t, colorTheme);
  };

  const handleSetColor = (c: ColorTheme) => {
    setColorThemeState(c);
    try {
      localStorage.setItem("wallex-color-theme", c);
    } catch {
      // ignore
    }
    applyTheme(theme, c);
  };

  const resolved = theme === "system" ? getSystemTheme() : theme;

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-9 w-9">
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground"
          title="تم"
        >
          {resolved === "dark" ? (
            <Moon className="h-4 w-4" />
          ) : (
            <Sun className="h-4 w-4" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="end">
        <div className="space-y-1">
          <p className="px-2 py-1 text-[10px] font-bold text-muted-foreground">
            حالت
          </p>
          {[
            { id: "light" as Theme, label: "روشن", icon: Sun },
            { id: "dark" as Theme, label: "تاریک", icon: Moon },
            { id: "system" as Theme, label: "سیستم", icon: Monitor },
          ].map(({ id, label, icon: Icon }) => (
            <Button
              key={id}
              variant="ghost"
              size="sm"
              onClick={() => handleSetTheme(id)}
              className={cn(
                "w-full justify-start gap-2",
                theme === id && "bg-accent",
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
              {theme === id && <Check className="mr-auto h-3 w-3" />}
            </Button>
          ))}

          <div className="my-2 h-px bg-border" />

          <p className="px-2 py-1 text-[10px] font-bold text-muted-foreground flex items-center gap-1">
            <Palette className="h-3 w-3" />
            رنگ تم
          </p>
          <div className="flex flex-wrap gap-1.5 px-2 py-1">
            {COLOR_THEMES.map((t) => (
              <button
                key={t.id}
                onClick={() => handleSetColor(t.id)}
                title={t.label}
                className={cn(
                  "relative h-7 w-7 rounded-full border-2 transition-all hover:scale-110",
                  colorTheme === t.id
                    ? "border-foreground"
                    : "border-transparent",
                )}
                style={{ background: t.color }}
              >
                {colorTheme === t.id && (
                  <Check className="absolute inset-0 m-auto h-3.5 w-3.5 text-white drop-shadow" />
                )}
              </button>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
