/**
 * Type definitions for worklist and Google Drive integration.
 */

/**
 * Worklist status - 7-state workflow.
 */
export type WorklistStatus =
  | 'to_evaluate' // 待评估
  | 'to_confirm' // 待确认
  | 'to_review' // 待审稿
  | 'to_revise' // 待修改
  | 'to_rereview' // 待复审
  | 'ready_to_publish' // 待发布
  | 'published'; // 已发布

/**
 * Worklist item from Google Drive.
 */
export interface WorklistItem {
  id: string;
  drive_file_id: string;
  title: string;
  status: WorklistStatus;
  content: string;
  excerpt?: string;
  author: string;
  created_at: string;
  updated_at: string;
  status_changed_at: string;
  tags?: string[];
  categories?: string[];
  notes?: WorklistNote[];
  metadata: WorklistMetadata;
}

/**
 * Worklist item metadata.
 */
export interface WorklistMetadata {
  word_count: number;
  estimated_reading_time: number; // minutes
  drive_folder: string;
  last_synced_at: string;
  quality_score?: number; // 0-100
  seo_score?: number; // 0-100
}

/**
 * Worklist note/comment.
 */
export interface WorklistNote {
  id: string;
  author: string;
  content: string;
  created_at: string;
  resolved: boolean;
}

/**
 * Worklist statistics.
 */
export interface WorklistStatistics {
  total: number;
  by_status: {
    [K in WorklistStatus]: number;
  };
  avg_time_per_status: {
    [K in WorklistStatus]: number; // hours
  };
  total_word_count: number;
  avg_quality_score: number;
}

/**
 * Worklist filter options.
 */
export interface WorklistFilters {
  status?: WorklistStatus | 'all';
  author?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  categories?: string[];
}

/**
 * Status transition request.
 */
export interface StatusTransitionRequest {
  item_id: string;
  from_status: WorklistStatus;
  to_status: WorklistStatus;
  note?: string;
}

/**
 * Google Drive sync status.
 */
export interface DriveSyncStatus {
  last_sync_at: string;
  is_syncing: boolean;
  total_files: number;
  synced_files: number;
  failed_files: number;
  errors: string[];
}

/**
 * Worklist item update request.
 */
export interface WorklistItemUpdate {
  title?: string;
  content?: string;
  excerpt?: string;
  tags?: string[];
  categories?: string[];
  status?: WorklistStatus;
}
