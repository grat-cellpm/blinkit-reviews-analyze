"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { apiPost, type ChatResponse } from "@/lib/utils";

const SUGGESTIONS = [
  "Why aren't users exploring new categories?",
  "What are the biggest complaints?",
  "What role do habits play in shopping behavior?",
  "Show reviews mentioning recommendations",
  "Which product improvements should Blinkit prioritize?",
];

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(q?: string) {
    const text = (q ?? question).trim();
    if (!text) return;
    setQuestion(text);
    setLoading(true);
    setError(null);
    try {
      const res = await apiPost<ChatResponse>("/api/chat", { question: text });
      setAnswer(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl tracking-tight">AI Chat</h1>
      </header>

      <Card>
        <CardContent className="space-y-4 pt-5">
          <Textarea
            placeholder="e.g. What prevents users from exploring new categories?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
          />
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => ask(s)}
                className="rounded-md border border-blinkit-ink/10 bg-white px-3 py-1.5 text-left text-xs text-blinkit-slate transition hover:border-blinkit-forest hover:text-blinkit-forest"
              >
                {s}
              </button>
            ))}
          </div>
          <Button onClick={() => ask()} disabled={loading}>
            {loading ? "Retrieving evidence…" : "Ask"}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-blinkit-coral">{error}</p>}

      {answer && (
        <div className="space-y-4 opacity-0 animate-fade-up">
          <Card className="border-blinkit-forest/20 bg-blinkit-mint/40">
            <CardHeader>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-xl">Answer</CardTitle>
                <Badge className="bg-blinkit-yellow text-blinkit-ink">
                  {(answer.confidence * 100).toFixed(0)}% confidence
                </Badge>
                <Badge>{answer.matching_reviews} matching reviews</Badge>
              </div>
              <CardDescription>{answer.question}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="leading-relaxed text-blinkit-ink">{answer.explanation}</p>
              {!!answer.related_themes?.length && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {answer.related_themes.map((t) => (
                    <Badge key={t}>{t}</Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <h2 className="font-display text-2xl">Supporting reviews</h2>
          <div className="space-y-3">
            {answer.supporting_reviews.map((r) => (
              <Card key={r.review_id}>
                <CardContent className="pt-5">
                  <div className="mb-2 flex flex-wrap gap-2">
                    <Badge className="bg-blinkit-yellow text-blinkit-ink">★ {r.rating}</Badge>
                    {r.main_theme && <Badge>{r.main_theme}</Badge>}
                    {r.relevance_score != null && (
                      <Badge className="bg-white border border-blinkit-ink/10">
                        relevance {(r.relevance_score * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed">“{r.content}”</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
