"use client";

import Link from "next/link";
import {
  Bot,
  ArrowLeft,
  Zap,
  Activity,
  Database,
  Cpu,
} from "lucide-react";
import { useBots } from "@/lib/queries";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function BotsListPage() {
  const bots = useBots();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Bot className="h-6 w-6 text-emerald-400" />
            ربات‌های معاملاتی
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {bots.data
              ? `${bots.data.count} ربات در دسترس`
              : "در حال بارگذاری..."}
          </p>
        </div>
      </div>

      {/* Bots grid */}
      {bots.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      ) : bots.data?.bots.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Bot className="mx-auto mb-3 h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">
              هنوز رباتی ثبت نشده
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {bots.data?.bots.map((bot) => (
            <BotCard key={bot.slug} bot={bot} />
          ))}
        </div>
      )}
    </div>
  );
}

function BotCard({
  bot,
}: {
  bot: {
    slug: string;
    name: string;
    name_en: string;
    version: string;
    description: string;
    tags: string[];
    capabilities: string[];
  };
}) {
  return (
    <Link href={`/bots/${bot.slug}`} className="group block">
      <Card className="h-full transition hover:border-emerald-500/40 hover:bg-emerald-500/5">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/30 to-emerald-500/0">
                <Bot className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-base">{bot.name}</CardTitle>
                <CardDescription className="text-xs">
                  {bot.name_en}
                </CardDescription>
              </div>
            </div>
            <Badge variant="outline" className="text-[10px]">
              v{bot.version}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {bot.description}
          </p>

          {/* Tags */}
          {bot.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {bot.tags.slice(0, 3).map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="border-blue-500/20 bg-blue-500/5 text-[10px] text-blue-400"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          {/* Capabilities */}
          <div className="flex items-center justify-between border-t border-white/5 pt-3">
            <div className="flex gap-1.5">
              {bot.capabilities.map((cap) => (
                <CapabilityBadge key={cap} capability={cap} />
              ))}
            </div>
            <ArrowLeft className="h-4 w-4 text-muted-foreground transition group-hover:-translate-x-1 group-hover:text-emerald-400" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function CapabilityBadge({ capability }: { capability: string }) {
  const config: Record<string, { icon: React.ElementType; color: string }> = {
    paper: { icon: Database, color: "border-blue-500/30 text-blue-400" },
    live: { icon: Zap, color: "border-emerald-500/30 text-emerald-400" },
    backtest: { icon: Activity, color: "border-purple-500/30 text-purple-400" },
  };
  const cfg = config[capability] ?? {
    icon: Cpu,
    color: "border-white/10 text-zinc-400",
  };
  const Icon = cfg.icon;
  return (
    <Badge
      variant="outline"
      className={cn("gap-1 text-[9px]", cfg.color)}
    >
      <Icon className="h-2.5 w-2.5" />
      {capability}
    </Badge>
  );
}
