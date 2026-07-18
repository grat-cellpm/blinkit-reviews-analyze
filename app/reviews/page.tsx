"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL, type Review } from "@/lib/utils";

const SENTIMENTS = ["", "positive", "neutral", "negative"];
const THEMES = [
  "",
  "Habit Shopping",
  "Poor Product Discovery",
  "Search Issues",
  "Recommendation Quality",
  "Delivery Experience",
  "Product Availability",
  "Pricing",
  "App Experience",
  "Customer Support",
  "Other",
];

export default function ReviewsPage() {
  const [items, setItems] = useState<Review[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [rating, setRating] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [theme, setTheme] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (rating) params.set("rating", rating);
    if (sentiment) params.set("sentiment", sentiment);
    if (theme) params.set("theme", theme);
    params.set("limit", "40");
    try {
      const res = await fetch(`${API_URL}/api/reviews?${params}`);
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [q, rating, sentiment, theme]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-tight">Review Explorer</h1>
        <p className="mt-2 text-blinkit-slate">
          Search and filter reviews by rating, sentiment, and theme.
        </p>
      </header>

      <Card>
        <CardContent className="grid gap-3 pt-5 md:grid-cols-5">
          <Input
            placeholder="Search reviews…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="md:col-span-2"
          />
          <select
            className="h-10 rounded-md border border-blinkit-ink/15 bg-white px-3 text-sm"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
          >
            <option value="">All ratings</option>
            {[5, 4, 3, 2, 1].map((r) => (
              <option key={r} value={r}>
                {r} stars
              </option>
            ))}
          </select>
          <select
            className="h-10 rounded-md border border-blinkit-ink/15 bg-white px-3 text-sm"
            value={sentiment}
            onChange={(e) => setSentiment(e.target.value)}
          >
            {SENTIMENTS.map((s) => (
              <option key={s || "all"} value={s}>
                {s || "All sentiments"}
              </option>
            ))}
          </select>
          <select
            className="h-10 rounded-md border border-blinkit-ink/15 bg-white px-3 text-sm"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          >
            {THEMES.map((t) => (
              <option key={t || "all"} value={t}>
                {t || "All themes"}
              </option>
            ))}
          </select>
          <Button onClick={load} className="md:col-span-5 md:w-fit">
            {loading ? "Loading…" : `Apply filters (${total})`}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-blinkit-coral">{error}</p>}

      <div className="space-y-3">
        {items.map((r) => (
          <Card key={r.review_id}>
            <CardHeader className="pb-1">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-base font-sans font-medium">
                  {r.user_name || "Anonymous"}
                </CardTitle>
                <Badge className="bg-blinkit-yellow text-blinkit-ink">★ {r.rating}</Badge>
                {r.sentiment && <Badge>{r.sentiment}</Badge>}
                {r.main_theme && (
                  <Badge className="bg-blinkit-forest text-white">{r.main_theme}</Badge>
                )}
                {r.user_segment && (
                  <Badge className="bg-white border border-blinkit-ink/10 text-blinkit-slate">
                    {r.user_segment}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-blinkit-ink/90">{r.content}</p>
              {r.pain_point && (
                <p className="mt-2 text-xs text-blinkit-slate">
                  Pain point: {r.pain_point}
                  {r.confidence != null ? ` · confidence ${(r.confidence * 100).toFixed(0)}%` : ""}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
        {!items.length && !error && (
          <p className="text-sm text-blinkit-slate">No reviews match these filters.</p>
        )}
      </div>
    </div>
  );
}
