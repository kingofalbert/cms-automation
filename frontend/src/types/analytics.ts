/**
 * Type definitions for analytics and provider comparison.
 */

import { ProviderType } from './publishing';

/**
 * Provider performance metrics.
 */
export interface ProviderMetrics {
  provider: ProviderType;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  success_rate: number; // Percentage (0-100)
  avg_duration: number; // Seconds
  avg_cost: number; // USD
  total_cost: number; // USD
  last_30_days: DailyMetrics[];
}

/**
 * Daily metrics for trend analysis.
 */
export interface DailyMetrics {
  date: string; // YYYY-MM-DD
  tasks: number;
  success_rate: number; // Percentage (0-100)
  avg_cost: number; // USD
}

/**
 * Task distribution by status.
 */
export interface TaskDistribution {
  status: string;
  count: number;
  percentage: number;
}

/**
 * Provider comparison data.
 */
export interface ProviderComparison {
  metrics: ProviderMetrics[];
  task_distribution: {
    [provider: string]: TaskDistribution[];
  };
  recommendations: Recommendation[];
  summary: ComparisonSummary;
}

/**
 * Recommendation for provider selection.
 */
export interface Recommendation {
  provider: ProviderType;
  score: number; // 0-100
  reason: string;
  use_cases: string[];
  pros: string[];
  cons: string[];
}

/**
 * Summary statistics.
 */
export interface ComparisonSummary {
  best_success_rate: {
    provider: ProviderType;
    value: number;
  };
  best_cost_efficiency: {
    provider: ProviderType;
    value: number;
  };
  best_speed: {
    provider: ProviderType;
    value: number;
  };
  recommended_provider: ProviderType;
}

/**
 * Time range for analytics.
 */
export type TimeRange = '7d' | '30d' | '90d' | 'all';

/**
 * Chart data point for line charts.
 */
export interface ChartDataPoint {
  date: string;
  [provider: string]: string | number;
}
