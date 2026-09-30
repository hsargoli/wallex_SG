import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  sub?: string;
  icon?: LucideIcon;
  accent?: string;
  loading?: boolean;
}

export function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  accent = 'text-foreground',
  loading = false,
}: StatCardProps) {
  if (loading) {
    return (
      <div className="rounded-xl border bg-card p-4 shadow-sm animate-pulse space-y-2">
        <div className="h-4 bg-muted rounded w-1/3"></div>
        <div className="h-8 bg-muted rounded w-2/3"></div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground font-medium">
        <span>{title}</span>
        {Icon && <Icon className="h-4 w-4 opacity-70" />}
      </div>
      <div className={`text-xl font-bold font-mono ${accent}`}>{value}</div>
      {sub && <div className="text-[11px] text-muted-foreground">{sub}</div>}
    </div>
  );
}
