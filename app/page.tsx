"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  MessageSquareText,
  Sparkles,
  Star,
  Smile,
  Layers
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, type DashboardMetrics } from "@/lib/utils";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#15904E", // blinkit-brand
  neutral: "#FACC15",  // blinkit-yellow
  negative: "#F87171", // blinkit-coral
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DashboardMetrics>("/api/dashboard/metrics")
      .then(setMetrics)
      .catch((e) => setError(e.message));
  }, []);

  const positivePercent = metrics
    ? Math.round(
        ((metrics.sentiment_distribution.positive || 0) /
          Math.max(metrics.analyzed_reviews, 1)) *
          100
      )
    : 0;

  const themesCount = Object.keys(metrics?.theme_distribution || {}).length || 0;

  const sentimentData = Object.entries(metrics?.sentiment_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );
  const themeData = Object.entries(metrics?.theme_distribution || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="space-y-6 animate-fade-up">
      {error && (
        <Card className="border-blinkit-coral/40 bg-red-50">
          <CardContent className="pt-5 text-sm text-blinkit-coral">
            Cannot reach API ({error}). Check if the backend is running on port 8000.
          </CardContent>
        </Card>
      )}
      
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blinkit-ink">Platform Overview</h1>
          <p className="text-sm text-blinkit-slate mt-1">Real-time feedback intelligence and sentiment analysis.</p>
        </div>
        <Link href="/chat" className="flex items-center gap-2 rounded-md bg-blinkit-yellow px-4 py-2.5 text-sm font-semibold text-blinkit-ink hover:bg-yellow-500 transition-colors shadow-sm">
          <Sparkles className="h-4 w-4" />
          Ask AI Assistant
        </Link>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Reviews */}
        <Card className="border border-blinkit-border shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <div className="flex items-start justify-between">
              <div className="rounded-md bg-green-50 p-2 text-blinkit-brand">
                <MessageSquareText className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-blinkit-slate">Reviews Analyzed</p>
              <div className="flex items-end gap-3 mt-1">
                <h3 className="text-3xl font-bold text-blinkit-ink">{metrics?.analyzed_reviews ?? "—"}</h3>
                <p className="text-sm font-medium text-blinkit-slate mb-1">/ {metrics?.total_reviews ?? 0} total</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Avg Rating */}
        <Card className="border border-blinkit-border shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <div className="flex items-start justify-between">
              <div className="rounded-md bg-yellow-50 p-2 text-yellow-600">
                <Star className="h-4 w-4 fill-current" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-blinkit-slate">Avg Rating</p>
              <div className="flex items-end gap-1 mt-1">
                <h3 className="text-3xl font-bold text-blinkit-ink">{metrics ? metrics.average_rating.toFixed(1) : "—"}</h3>
                <p className="text-sm font-medium text-blinkit-slate mb-1">/ 5.0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sentiment Score */}
        <Card className="border border-blinkit-border shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <div className="flex items-start justify-between">
              <div className="rounded-md bg-green-50 p-2 text-blinkit-brand">
                <Smile className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-blinkit-slate">Sentiment Score</p>
              <div className="flex items-end gap-2 mt-1">
                <h3 className="text-3xl font-bold text-blinkit-ink">{metrics ? positivePercent + "%" : "—"}</h3>
                <p className="text-sm font-medium text-blinkit-brand mb-1">Positive</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Themes Detected */}
        <Card className="border border-blinkit-border shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full">
            <div className="flex items-start justify-between">
              <div className="rounded-md bg-blue-50 p-2 text-blue-600">
                <Layers className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-blinkit-slate">Themes Detected</p>
              <h3 className="text-3xl font-bold text-blinkit-ink mt-1">
                {metrics ? themesCount : "—"}
              </h3>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border border-blinkit-border shadow-sm opacity-0 animate-fade-up" style={{ animationDelay: '0.1s' }}>
          <CardHeader>
            <CardTitle>Sentiment distribution</CardTitle>
            <CardDescription>LLM-labeled review polarity</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {sentimentData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                  >
                    {sentimentData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SENTIMENT_COLORS[entry.name] || "#4B5563"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart />
            )}
          </CardContent>
        </Card>

        <Card className="border border-blinkit-border shadow-sm opacity-0 animate-fade-up" style={{ animationDelay: '0.15s' }}>
          <CardHeader>
            <CardTitle>Theme distribution</CardTitle>
            <CardDescription>Frequency of recurring themes</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {themeData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={themeData} layout="vertical" margin={{ left: 24 }}>
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={130}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip />
                  <Bar dataKey="value" fill="#15904E" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-blinkit-slate">
      No data yet — run seed or ingestion pipeline.
    </div>
  );
}
