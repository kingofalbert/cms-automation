/**
 * Publishing related type definitions.
 */

export type ProviderType = 'playwright' | 'computer_use' | 'hybrid';

export type PublishStatus =
  | 'idle'
  | 'pending'
  | 'initializing'
  | 'logging_in'
  | 'creating_post'
  | 'uploading_images'
  | 'configuring_seo'
  | 'publishing'
  | 'completed'
  | 'failed';

export interface PublishTask {
  id: string;
  article_id: string;
  article_title: string;
  provider: ProviderType;
  status: PublishStatus;
  progress: number; // 0-100
  current_step: string;
  total_steps: number;
  completed_steps: number;
  screenshots: Screenshot[];
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration?: number; // in seconds
  cost?: number; // in USD
}

export interface Screenshot {
  id: string;
  step: string;
  url: string;
  timestamp: string;
  description?: string;
}

export interface PublishRequest {
  article_id: string;
  provider: ProviderType;
  options?: PublishOptions;
}

export interface PublishOptions {
  featured_image_url?: string;
  /** @deprecated Use primary_category and secondary_categories instead */
  categories?: string[];
  /** WordPress primary category (主分類，決定URL結構) */
  primary_category?: string;
  /** WordPress secondary categories (副分類，用於交叉列表) */
  secondary_categories?: string[];
  tags?: string[];
  publish_immediately?: boolean;
  seo_optimization?: boolean;
}

export interface PublishResult {
  task_id: string;
  status: PublishStatus;
  message: string;
  published_url?: string;
}

export interface ProviderInfo {
  type: ProviderType;
  name: string;
  description: string;
  icon: string;
  cost_per_publish: number; // in USD
  avg_duration: number; // in seconds
  success_rate: number; // 0-100
  features: string[];
  recommended?: boolean;
}
