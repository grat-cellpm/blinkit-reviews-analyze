import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json();
}

export type DashboardMetrics = {
  total_reviews: number;
  analyzed_reviews: number;
  average_rating: number;
  sentiment_distribution: Record<string, number>;
  theme_distribution: Record<string, number>;
  segment_distribution: Record<string, number>;
  rating_distribution: Record<string, number>;
};

export type Theme = {
  theme: string;
  frequency: number;
  ai_summary?: string;
  representative_reviews: Array<{
    review_id: string;
    content: string;
    rating: number;
    sentiment?: string;
    confidence?: number;
  }>;
};

export type Segment = {
  segment: string;
  count: number;
  shopping_behaviors: string[];
  insights?: string;
};

export type Review = {
  id: number;
  review_id: string;
  user_name?: string;
  content: string;
  rating: number;
  thumbs_up: number;
  review_date?: string;
  sentiment?: string;
  main_theme?: string;
  user_segment?: string;
  pain_point?: string;
  confidence?: number;
};

export type Opportunity = {
  id: number;
  title: string;
  description: string;
  supporting_evidence: Array<{
    review_id: string;
    content: string;
    rating: number;
    theme?: string;
  }>;
  evidence_count: number;
  estimated_impact: string;
  confidence: number;
  related_theme?: string;
  rank: number;
};

export type ChatResponse = {
  question: string;
  explanation: string;
  supporting_reviews: Array<{
    review_id: string;
    content: string;
    rating: number;
    sentiment?: string;
    main_theme?: string;
    relevance_score?: number;
  }>;
  matching_reviews: number;
  confidence: number;
  related_themes: string[];
};
