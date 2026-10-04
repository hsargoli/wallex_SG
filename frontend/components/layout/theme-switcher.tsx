"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun, Monitor, Palette, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

// ---------- Themes ----------
// "light" و "dark" و "system" (توسط next-themes)
// + تم‌های رنگی (با data-theme)

const COLOR_THEMES = [
  {
    id: "default",
    label: "پیش‌فرض",
    color: "oklch(0.72 0.17 162)",  // سبز
  },
  {
    id: "blue",
    label: "آبی",
    color: "oklch(0.65 0.18 240)",
  },
  {
    id: "purple",
    label: "بنفش",
    color: "oklch(0.65 0.20 300)",
  },
  {
    id: "orange",
    label: "نارنجی",
    color: "oklch(0.72 0.18 60)",
  },
  {
    id: "rose",
    label: "رز",
    color: "oklch(0.65 0.20 15)",
  },
];

// ---------- Component ----------

export function ThemeSwitcher() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [colorTheme, setColorTheme] = useState<string>("default");

  // خواندن color theme از localStorage
  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("wallex-color-theme") || "default";
      setColorTheme(saved);
      document.documentElement.setAttribute("data-color", saved);
    }
  }, []);

  const handleColorChange = (id: string) => {
    setColorTheme(id);
    if (typeof window !== "undefined") {
      localStorage.setItem("wallex-color-theme", id);
      document.documentElement.setAttribute("data-color", id);
    }
  };

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
          {resolvedTheme === "dark" ? (
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
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme("light")}
            className={cn(
              "w-full justify-start gap-2",
              theme === "light" && "bg-accent",
            )}
          >
            <Sun className="h-3.5 w-3.5" />
            روشن
            {theme === "light" && <Check className="mr-auto h-3 w-3" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme("dark")}
            className={cn(
              "w-full justify-start gap-2",
              theme === "dark" && "bg-accent",
            )}
          >
            <Moon className="h-3.5 w-3.5" />
            تاریک
            {theme === "dark" && <Check className="mr-auto h-3 w-3" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme("system")}
            className={cn(
              "w-full justify-start gap-2",
              theme === "system" && "bg-accent",
            )}
          >
            <Monitor className="h-3.5 w-3.5" />
            سیستم
            {theme === "system" && <Check className="mr-auto h-3 w-3" />}
          </Button>

          <div className="my-2 h-px bg-border" />

          <p className="px-2 py-1 text-[10px] font-bold text-muted-foreground flex items-center gap-1">
            <Palette className="h-3 w-3" />
            رنگ تم
          </p>
          <div className="flex flex-wrap gap-1.5 px-2 py-1">
            {COLOR_THEMES.map((t) => (
              <button
                key={t.id}
                onClick={() => handleColorChange(t.id)}
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
