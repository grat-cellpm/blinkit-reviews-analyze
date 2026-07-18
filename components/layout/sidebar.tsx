"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Layers,
  Users,
  MessageSquareText,
  Search,
  Lightbulb,
  Sparkles,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/reviews", label: "Review Explorer", icon: Search },
  { href: "/themes", label: "Theme Clustering", icon: Layers },
  { href: "/segments", label: "User Segments", icon: Users },
  { href: "/opportunities", label: "Product Opportunities", icon: Lightbulb },
  { href: "/chat", label: "AI Assistant", icon: MessageSquareText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-blinkit-border bg-white text-blinkit-ink">
      <div className="px-6 py-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blinkit-yellow text-blinkit-ink">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-display text-xl font-bold leading-tight text-blinkit-ink">
              Blink<span className="text-blinkit-brand">it</span> Feedback AI
            </p>
          </div>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-4">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-blinkit-brand text-white"
                  : "text-blinkit-slate hover:bg-blinkit-light hover:text-blinkit-ink"
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
