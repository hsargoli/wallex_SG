"use client";

import { useEffect, useRef } from "react";

const N_PARTICLES = 32;
const CONNECT_DIST = 130;       // فاصله‌ی اتصال بین ذرات
const MOUSE_DIST   = 180;       // فاصله‌ی اتصال از موس
const SPEED        = 0.25;

const PARTICLE_COLORS = [
  "#9ca3af", "#6b7280", "#d1d5db",   // خاکستری
  "#60a5fa", "#3b82f6", "#2563eb",   // آبی
  "#f87171", "#ef4444", "#dc2626",   // قرمز
];

type P = { x: number; y: number; vx: number; vy: number; r: number; c: string };

export function BackgroundFX() {
  const svgRef = useRef<SVGSVGElement>(null);
  const particlesRef = useRef<P[]>([]);
  const mouseRef = useRef({ x: -9999, y: -9999, active: false });
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const resize = () => {
      const { innerWidth: w, innerHeight: h } = window;
      svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
      // ذرات رو دوباره بساز
      particlesRef.current = Array.from({ length: N_PARTICLES }).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * SPEED * 2,
        vy: (Math.random() - 0.5) * SPEED * 2,
        r: 1.5 + Math.random() * 2.5,
        c: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
      }));
    };
    resize();
    window.addEventListener("resize", resize);

    const onMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY, active: true };
    };
    const onLeave = () => {
      mouseRef.current.active = false;
      mouseRef.current.x = -9999;
      mouseRef.current.y = -9999;
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseleave", onLeave);

    const tick = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const ps = particlesRef.current;

      // حرکت
      for (const p of ps) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        p.x = Math.max(0, Math.min(w, p.x));
        p.y = Math.max(0, Math.min(h, p.y));
      }

      // رندر
      const parts: string[] = [];

      // اتصال ذره-ذره
      for (let i = 0; i < ps.length; i++) {
        for (let j = i + 1; j < ps.length; j++) {
          const dx = ps[i].x - ps[j].x;
          const dy = ps[i].y - ps[j].y;
          const d = Math.hypot(dx, dy);
          if (d < CONNECT_DIST) {
            const op = (1 - d / CONNECT_DIST) * 0.18;
            parts.push(
              `<line x1="${ps[i].x.toFixed(1)}" y1="${ps[i].y.toFixed(1)}" x2="${ps[j].x.toFixed(1)}" y2="${ps[j].y.toFixed(1)}" stroke="#a78bfa" stroke-opacity="${op.toFixed(3)}" stroke-width="1"/>`,
            );
          }
        }
      }

      // اتصال موس-ذره
      const m = mouseRef.current;
      if (m.active) {
        for (const p of ps) {
          const dx = p.x - m.x;
          const dy = p.y - m.y;
          const d = Math.hypot(dx, dy);
          if (d < MOUSE_DIST) {
            const op = (1 - d / MOUSE_DIST) * 0.55;
            parts.push(
              `<line x1="${m.x}" y1="${m.y}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" stroke="#c4b5fd" stroke-opacity="${op.toFixed(3)}" stroke-width="1.2"/>`,
            );
          }
        }
      }

      // ذرات
      for (const p of ps) {
        const nearMouse =
          m.active && Math.hypot(p.x - m.x, p.y - m.y) < MOUSE_DIST;
        const r = nearMouse ? p.r * 1.6 : p.r;
        const op = nearMouse ? 0.95 : 0.55;
        parts.push(
          `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r.toFixed(2)}" fill="${p.c}" fill-opacity="${op}"/>`,
        );
      }

      svg.innerHTML = parts.join("");
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* grid overlay */}
      <div className="grid-bg text-violet-400" />

      {/* orbs — بنفش خیلی تیره */}
      <div className="orb" style={{ width: 520, height: 520, top: "4%", right: "0%", background: "#4c1d95", opacity: 0.55 }} />
      <div className="orb" style={{ width: 420, height: 420, top: "48%", left: "2%", background: "#5b21b6", opacity: 0.48, animationDelay: "3s" }} />
      <div className="orb" style={{ width: 380, height: 380, bottom: "2%", right: "18%", background: "#6d28d9", opacity: 0.42, animationDelay: "6s" }} />
      <div className="orb" style={{ width: 320, height: 320, top: "26%", left: "36%", background: "#7c3aed", opacity: 0.28, animationDelay: "9s" }} />

      {/* شبکه‌ی ذرات (SVG + موس) */}
      <svg
        ref={svgRef}
        className="absolute inset-0 h-full w-full"
        preserveAspectRatio="none"
        aria-hidden="true"
      />
    </div>
  );
}
