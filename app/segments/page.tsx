"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, type Segment } from "@/lib/utils";

export default function SegmentsPage() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Segment[]>("/api/segments")
      .then(setSegments)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-tight">User Segments</h1>
        <p className="mt-2 text-blinkit-slate">
          Shopping-behavior cohorts: who experiments, who stays routine, who hunts deals.
        </p>
      </header>

      {error && <p className="text-sm text-blinkit-coral">{error}</p>}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {segments.map((seg, i) => (
          <Card
            key={seg.segment}
            className="opacity-0 animate-fade-up"
            style={{ animationDelay: `${i * 0.06}s` }}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-xl">{seg.segment}</CardTitle>
                <Badge className="bg-blinkit-yellow text-blinkit-ink">{seg.count}</Badge>
              </div>
              <CardDescription>{seg.insights}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-blinkit-slate">
                Behaviors
              </p>
              <div className="flex flex-wrap gap-2">
                {(seg.shopping_behaviors || []).length ? (
                  seg.shopping_behaviors.map((b) => (
                    <Badge key={b} className="bg-blinkit-mint text-blinkit-forest">
                      {b}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-blinkit-slate">No behaviors yet</span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
