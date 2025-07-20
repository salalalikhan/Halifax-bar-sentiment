// TypeScript types for API responses

export interface BarSummary {
  name: string;
  total_mentions: number;
  avg_sentiment: number;
  avg_confidence: number;
  positive_mentions: number;
  negative_mentions: number;
  neutral_mentions: number;
  first_mention?: string;
  last_mention?: string;
  top_emotions?: Record<string, number>;
  specialties: string[];
}

export interface MentionDetail {
  id: number;
  bar_name: string;
  post_id: string;
  post_title: string;
  post_text: string;
  created_at: string;
  sentiment_score: number;
  sentiment_confidence: number;
  sentiment_label: string;
  model_scores: Record<string, number>;
  emotion_scores?: Record<string, number>;
  food_mentions: string[];
  url: string;
  is_comment: boolean;
}

export interface SentimentTrend {
  date: string;
  bar_name: string;
  mention_count: number;
  avg_sentiment: number;
  avg_confidence: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

export interface AnalyticsSummary {
  total_mentions: number;
  unique_bars: number;
  avg_sentiment_score: number;
  sentiment_distribution: Record<string, number>;
  top_bars: Array<{
    name: string;
    mentions: number;
    sentiment: number;
  }>;
  trending_foods: Array<{
    food: string;
    count: number;
  }>;
  data_quality_score?: number;
  analysis_date: string;
}

export interface QualityMetrics {
  processing_date: string;
  total_posts_processed: number;
  valid_posts: number;
  invalid_posts: number;
  spam_filtered: number;
  mentions_found: number;
  unique_bars_mentioned: number;
  average_confidence: number;
  data_quality_score: number;
}

export interface SearchRequest {
  query: string;
  bars?: string[];
  sentiment?: 'positive' | 'negative' | 'neutral';
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: MentionDetail[];
  filters_applied: Record<string, any>;
}

export interface TrendRequest {
  bars?: string[];
  days?: number;
  granularity?: 'daily' | 'weekly' | 'monthly';
}

export interface TrendResponse {
  period_start: string;
  period_end: string;
  granularity: string;
  trends: SentimentTrend[];
  summary_stats: Record<string, any>;
}

export interface ComparisonRequest {
  bars: string[];
  metrics?: string[];
  days?: number;
}

export interface ComparisonResponse {
  bars: string[];
  metrics: string[];
  analysis_period: number;
  comparison_data: Record<string, Record<string, any>>;
  rankings: Record<string, string[]>;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database_connected: boolean;
  last_data_update?: string;
  total_mentions: number;
}