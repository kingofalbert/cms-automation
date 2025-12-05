/**
 * Article related type definitions.
 */

export interface Article {
  id: string;
  title: string;
  content: string;
  excerpt?: string;
  status: ArticleStatus;
  seo_metadata?: SEOMetadata;
  images?: ArticleImage[];
  tags?: string[];
  categories?: string[];
  /** WordPress primary category (主分類，決定URL結構和麵包屑導航) */
  primary_category?: string;
  /** WordPress secondary categories (副分類，可多選，用於交叉列表) */
  secondary_categories?: string[];
  created_at: string;
  updated_at: string;
}

export type ArticleStatus =
  | 'draft'
  | 'pending'
  | 'proofreading'
  | 'under_review'
  | 'ready_to_publish'
  | 'publishing'
  | 'published'
  | 'failed';

export interface SEOMetadata {
  meta_title?: string;
  meta_description?: string;
  focus_keyword?: string;
  additional_keywords?: string[];
  readability_score?: number;
  keyword_density?: Record<string, number>;
  optimization_score?: number;
  recommendations?: string[];
}

export interface ArticleImage {
  id: string;
  url: string;
  alt_text?: string;
  caption?: string;
  is_featured: boolean;
}

export interface ArticleImportRequest {
  title: string;
  content: string;
  excerpt?: string;
  tags?: string[];
  categories?: string[];
  images?: File[];
}

export interface BatchImportRequest {
  articles: ArticleImportRequest[];
}

export interface ImportHistoryItem {
  id: string;
  filename: string;
  import_type: 'csv' | 'json' | 'manual';
  total_count: number;
  success_count: number;
  failed_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  error_message?: string;
}
