/**
 * Worklist Detail Drawer component.
 * Shows detailed information about a worklist item, timeline, and CTAs.
 */

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import {
  AlertTriangle,
  Clock,
  ExternalLink,
  FileText,
  Folder,
  Send,
  Tag,
  User,
  CheckCircle,
  ClipboardCheck,
} from 'lucide-react';

import { Drawer, DrawerFooter, Button, Textarea } from '@/components/ui';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import type {
  WorklistItem,
  WorklistItemDetail,
  WorklistStatus,
} from '@/types/worklist';

export interface WorklistDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  item: WorklistItem | null;
  detail?: WorklistItemDetail | null;
  isLoading?: boolean;
  onStatusChange?: (
    itemId: number,
    newStatus: WorklistStatus,
    note?: string
  ) => void;
  onPublish?: (itemId: number) => void;
}

const STATUS_ORDER: WorklistStatus[] = [
  'pending',
  'proofreading',
  'under_review',
  'ready_to_publish',
  'publishing',
  'published',
  'failed',
];

const STATUS_LABELS: Record<WorklistStatus, string> = {
  pending: '待处理',
  proofreading: '校对中',
  under_review: '审核中',
  ready_to_publish: '待发布',
  publishing: '发布中',
  published: '已发布',
  failed: '失败',
};

const STATUS_TRANSITIONS: Record<WorklistStatus, WorklistStatus[]> = {
  pending: ['proofreading', 'failed'],
  proofreading: ['under_review', 'failed'],
  under_review: ['ready_to_publish', 'failed'],
  ready_to_publish: ['publishing', 'failed'],
  publishing: ['published', 'failed'],
  published: [],
  failed: ['pending'],
};

export const WorklistDetailDrawer: React.FC<WorklistDetailDrawerProps> = ({
  isOpen,
  onClose,
  item,
  detail,
  isLoading,
  onStatusChange,
  onPublish,
}) => {
  const [note, setNote] = useState('');
  const [changingStatus, setChangingStatus] = useState(false);

  const data = detail ?? item;

  const metadata = useMemo(
    () => detail?.metadata ?? item?.metadata ?? {},
    [detail, item]
  );

  const formatDate = (value: string | null | undefined) => {
    if (!value) return '—';
    try {
      return format(new Date(value), 'yyyy-MM-dd HH:mm:ss');
    } catch {
      return value;
    }
  };

  const resolveStatus = (status: WorklistStatus | string): WorklistStatus => {
    return STATUS_ORDER.includes(status as WorklistStatus)
      ? (status as WorklistStatus)
      : 'pending';
  };

  const handleStatusChange = async (newStatus: WorklistStatus) => {
    if (!onStatusChange || !data) return;
    setChangingStatus(true);
    try {
      await onStatusChange(data.id, newStatus, note);
      setNote('');
    } finally {
      setChangingStatus(false);
    }
  };

  const handlePublish = async () => {
    if (!onPublish || !data) return;
    await onPublish(data.id);
  };

  if (!data) {
    if (!isLoading) {
      return null;
    }
    return (
      <Drawer isOpen={isOpen} onClose={onClose} title="工作清单详情" size="lg" position="right">
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="inline-flex flex-col items-center gap-2">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-primary-600" />
            加载详情中...
          </div>
        </div>
        <DrawerFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DrawerFooter>
      </Drawer>
    );
  }

  const resolvedStatus = resolveStatus(data.status);
  const nextStatuses = STATUS_TRANSITIONS[resolvedStatus] || [];
  const statusHistory = detail?.article_status_history ?? [];
  const driveMetadata = detail?.drive_metadata ?? {};
  const wordCount =
    typeof metadata?.word_count === 'number' ? metadata.word_count : undefined;
  const readingTime =
    typeof metadata?.estimated_reading_time === 'number'
      ? metadata.estimated_reading_time
      : undefined;
  const qualityScore =
    typeof metadata?.quality_score === 'number' ? metadata.quality_score : undefined;
  const description =
    (typeof metadata?.description === 'string' && metadata.description) ||
    (typeof metadata?.summary === 'string' && metadata.summary) ||
    undefined;
  const contentPreview = (detail?.content || data.content || '').slice(0, 800);
  const lastSyncedAt =
    (typeof metadata?.last_synced_at === 'string' && metadata.last_synced_at) ||
    data.synced_at;
  const isFailed = resolvedStatus === 'failed';
  const latestErrorNote = [...(data.notes || [])]
    .reverse()
    .find((noteEntry) =>
      (noteEntry.level || noteEntry.status || '').toString().toLowerCase().includes('error')
    );

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="工作清单详情"
      size="lg"
      position="right"
    >
      <div className="space-y-6">
        <div>
          <div className="flex items-start justify-between mb-2">
            <h2 className="text-xl font-semibold text-gray-900">{data.title}</h2>
            <WorklistStatusBadge status={resolvedStatus} size="md" />
          </div>
          {description && (
            <p className="text-sm text-gray-600 line-clamp-3">{description}</p>
          )}
        </div>

        {isFailed && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">自动流程失败</p>
              <p className="text-sm text-red-700">
                请检查错误详情后重新尝试同步或触发校对。
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center text-sm text-gray-600">
            <User className="w-4 h-4 mr-2" />
            <span>作者: {data.author || '未知作者'}</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <FileText className="w-4 h-4 mr-2" />
            <span>{wordCount ? `${wordCount.toLocaleString()} 字` : '字数未知'}</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="w-4 h-4 mr-2" />
            <span>{readingTime ? `${readingTime} 分钟阅读` : '阅读时间未知'}</span>
          </div>
          {qualityScore !== undefined && (
            <div className="flex items-center text-sm text-gray-600">
              <CheckCircle className="w-4 h-4 mr-2" />
              <span>质量分数: {qualityScore.toFixed(0)}/100</span>
            </div>
          )}
        </div>

        {(detail?.tags?.length || data.tags?.length || 0) > 0 && (
          <div className="space-y-2">
            <div className="flex items-start">
              <Tag className="w-4 h-4 text-gray-400 mr-2 mt-0.5" />
              <div className="flex flex-wrap gap-2">
                {(detail?.tags ?? data.tags ?? []).map((tag, index) => (
                  <span
                    key={`${tag}-${index}`}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {(detail?.categories?.length || data.categories?.length || 0) > 0 && (
          <div className="space-y-2">
            <div className="flex items-start">
              <Folder className="w-4 h-4 text-gray-400 mr-2 mt-0.5" />
              <div className="flex flex-wrap gap-2">
                {(detail?.categories ?? data.categories ?? []).map(
                  (category, index) => (
                    <span
                      key={`${category}-${index}`}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      {category}
                    </span>
                  )
                )}
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3">时间线</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">创建时间:</span>
              <span className="text-gray-900">{formatDate(data.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">更新时间:</span>
              <span className="text-gray-900">{formatDate(data.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">最后同步:</span>
              <span className="text-gray-900">{formatDate(lastSyncedAt)}</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3">状态历史</h3>
          {statusHistory.length === 0 ? (
            <p className="text-sm text-gray-500">暂无状态变化记录</p>
          ) : (
            <div className="space-y-3 text-sm">
              {statusHistory.map((entry, idx) => (
                <div
                  key={`${entry.created_at}-${idx}`}
                  className="flex items-start justify-between"
                >
                  <div>
                    <p className="text-gray-900 font-medium">{entry.new_status}</p>
                    {entry.change_reason && (
                      <p className="text-xs text-gray-600 mt-1">{entry.change_reason}</p>
                    )}
                  </div>
                  <div className="text-right text-gray-500">
                    <p>{formatDate(entry.created_at)}</p>
                    {entry.changed_by && (
                      <p className="text-xs mt-1">由 {entry.changed_by}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="font-medium text-gray-900 mb-2">内容预览</h3>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-800 whitespace-pre-line max-h-64 overflow-y-auto">
            {contentPreview
              ? `${contentPreview}${
                  detail?.content && detail.content.length > contentPreview.length
                    ? '…'
                    : ''
                }`
              : '暂无内容'}
          </div>
        </div>

        <div className="flex items-center justify-between">
          {driveMetadata?.webViewLink ? (
            <a
              href={driveMetadata.webViewLink as string}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              在 Google Drive 中打开
            </a>
          ) : (
            <span className="text-sm text-gray-500">
              文件 ID: {data.drive_file_id}
            </span>
          )}
          {data.article_id && resolvedStatus === 'under_review' && (
            <Link
              to={`/worklist/${data.id}/review`}
              className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              <ClipboardCheck className="w-4 h-4 mr-1" />
              开始审核 →
            </Link>
          )}
        </div>

        {data.notes && data.notes.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">备注历史</h3>
            <div className="space-y-3 max-h-60 overflow-y-auto">
              {data.notes.map((entry, index) => {
                const noteId = (entry.id ?? `${data.id}-note-${index}`) as string;
                const message = (entry.message ?? entry.content ?? '') as string;
                const author = (entry.author ?? '未知作者') as string;
                const resolved = Boolean(entry.resolved);
                const timestamp =
                  (typeof entry.created_at === 'string' ? entry.created_at : undefined) ??
                  null;
                return (
                  <div
                    key={noteId}
                    className={`p-3 rounded-lg ${
                      resolved ? 'bg-gray-50' : 'bg-yellow-50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">{author}</span>
                      <span className="text-xs text-gray-500">{formatDate(timestamp)}</span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-line">
                      {message || '（无备注内容）'}
                    </p>
                    {resolved && (
                      <span className="inline-flex items-center text-xs text-green-600 mt-1">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        已解决
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {nextStatuses.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h3 className="font-medium text-gray-900 mb-3">状态变更</h3>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="添加备注 (可选)"
              rows={3}
              className="mb-3"
            />
            <div className="flex flex-wrap gap-2">
              {nextStatuses.map((status) => (
                <Button
                  key={status}
                  variant="outline"
                  onClick={() => handleStatusChange(status)}
                  disabled={changingStatus}
                >
                  <Send className="w-4 h-4 mr-2" />
                  变更为: {STATUS_LABELS[status]}
                </Button>
              ))}
            </div>
          </div>
        )}

        {resolvedStatus === 'ready_to_publish' && onPublish && (
          <div className="border-t border-gray-200 pt-4">
            <Button variant="primary" onClick={handlePublish} fullWidth>
              <Send className="w-4 h-4 mr-2" />
              发布到 WordPress
            </Button>
          </div>
        )}
      </div>

      <DrawerFooter>
        <div className="flex items-center justify-between w-full">
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
          {data.article_id && resolvedStatus === 'under_review' && (
            <Link to={`/worklist/${data.id}/review`}>
              <Button variant="primary">
                <ClipboardCheck className="w-4 h-4 mr-2" />
                开始审核
              </Button>
            </Link>
          )}
        </div>
      </DrawerFooter>
    </Drawer>
  );
};
