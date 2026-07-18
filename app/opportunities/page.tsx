"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet, type Opportunity } from "@/lib/utils";

const IMPACT_STYLE: Record<string, string> = {
  High: "bg-blinkit-coral text-white",
  Medium: "bg-blinkit-yellow text-blinkit-ink",
  Low: "bg-blinkit-mint text-blinkit-forest",
};

export default function OpportunitiesPage() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Opportunity[]>("/api/opportunities")
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-tight">Product Opportunities</h1>
        <p className="mt-2 text-blinkit-slate">
          Ranked AI recommendations from recurring pain points, with evidence and impact.
        </p>
      </header>

      {error && <p className="text-sm text-blinkit-coral">{error}</p>}

      <div className="space-y-4">
        {items.map((opp, i) => (
          <Card
            key={opp.id}
            className="opacity-0 animate-fade-up"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-blinkit-slate">
                    Rank #{opp.rank}
                  </p>
                  <CardTitle className="mt-1">{opp.title}</CardTitle>
                  <CardDescription className="mt-2">{opp.description}</CardDescription>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className={IMPACT_STYLE[opp.estimated_impact] || IMPACT_STYLE.Medium}>
                    {opp.estimated_impact} impact
                  </Badge>
                  <Badge>
                    {(opp.confidence * 100).toFixed(0)}% confidence
                  </Badge>
                  <Badge className="bg-blinkit-forest text-white">
                    {opp.evidence_count} evidence
                  </Badge>
                </div>
              </div>
              {opp.related_theme && (
                <Badge className="w-fit mt-2">{opp.related_theme}</Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-blinkit-slate">
                Supporting evidence
              </p>
              {(opp.supporting_evidence || []).slice(0, 3).map((e) => (
                <blockquote
                  key={e.review_id}
                  className="border-l-2 border-blinkit-yellow pl-3 text-sm"
                >
                  “{e.content}”
                </blockquote>
              ))}
            </CardContent>
          </Card>
        ))}
        {!items.length && !error && (
          <p className="text-sm text-blinkit-slate">No opportunities generated yet.</p>
        )}
      </div>
    </div>
  );
}
