"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, type Theme } from "@/lib/utils";

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Theme[]>("/api/themes")
      .then(setThemes)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-tight">Theme Explorer</h1>
        <p className="mt-2 text-blinkit-slate">
          Recurring feedback clusters with AI summaries and representative reviews.
        </p>
      </header>

      {error && <p className="text-sm text-blinkit-coral">{error}</p>}

      <div className="grid gap-5 md:grid-cols-2">
        {themes.map((theme, i) => (
          <Card
            key={theme.theme}
            className="opacity-0 animate-fade-up"
            style={{ animationDelay: `${i * 0.06}s` }}
          >
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <CardTitle>{theme.theme}</CardTitle>
                <Badge>{theme.frequency} reviews</Badge>
              </div>
              <CardDescription>{theme.ai_summary}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs font-medium uppercase tracking-wide text-blinkit-slate">
                Representative reviews
              </p>
              {(theme.representative_reviews || []).slice(0, 3).map((r) => (
                <blockquote
                  key={r.review_id}
                  className="border-l-2 border-blinkit-yellow pl-3 text-sm text-blinkit-ink/90"
                >
                  “{r.content}”
                  <span className="mt-1 block text-xs text-blinkit-slate">
                    ★ {r.rating} · {r.sentiment || "n/a"}
                  </span>
                </blockquote>
              ))}
            </CardContent>
          </Card>
        ))}
        {!themes.length && !error && (
          <p className="text-sm text-blinkit-slate">No themes yet.</p>
        )}
      </div>
    </div>
  );
}
