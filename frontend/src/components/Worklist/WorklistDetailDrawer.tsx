/**
 * Worklist Detail Drawer component.
 * Shows detailed information about a worklist item and allows status transitions.
 */

import { useState } from 'react';
import { WorklistItem, WorklistStatus } from '@/types/worklist';
import { Drawer, DrawerFooter, Button, Textarea } from '@/components/ui';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import { format } from 'date-fns';
import {
  FileText,
  User,
  Tag,
  Folder,
  Clock,
  CheckCircle,
  Send,
  ExternalLink,
} from 'lucide-react';

export interface WorklistDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  item: WorklistItem | null;
  onStatusChange?: (
    itemId: string,
    newStatus: WorklistStatus,
    note?: string
  ) => void;
  onPublish?: (itemId: string) => void;
}

export const WorklistDetailDrawer: React.FC<WorklistDetailDrawerProps> = ({
  isOpen,
  onClose,
  item,
  onStatusChange,
  onPublish,
}) => {
  const [note, setNote] = useState('');
  const [changingStatus, setChangingStatus] = useState(false);

  if (!item) {
    return null;
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss');
    } catch {
      return dateStr;
    }
  };

  // Get possible next statuses
  const getNextStatuses = (currentStatus: WorklistStatus): WorklistStatus[] => {
    const transitions: Record<WorklistStatus, WorklistStatus[]> = {
      to_evaluate: ['to_confirm', 'to_revise'],
      to_confirm: ['to_review', 'to_revise'],
      to_review: ['ready_to_publish', 'to_revise'],
      to_revise: ['to_rereview'],
      to_rereview: ['ready_to_publish', 'to_revise'],
      ready_to_publish: ['published'],
      published: [],
    };
    return transitions[currentStatus] || [];
  };

  const getStatusLabel = (status: WorklistStatus): string => {
    const labels: Record<WorklistStatus, string> = {
      to_evaluate: '待评估',
      to_confirm: '待确认',
      to_review: '待审稿',
      to_revise: '待修改',
      to_rereview: '待复审',
      ready_to_publish: '待发布',
      published: '已发布',
    };
    return labels[status];
  };

  const handleStatusChange = async (newStatus: WorklistStatus) => {
    if (!onStatusChange) return;

    setChangingStatus(true);
    try {
      await onStatusChange(item.id, newStatus, note);
      setNote('');
    } finally {
      setChangingStatus(false);
    }
  };

  const handlePublish = async () => {
    if (!onPublish) return;
    await onPublish(item.id);
  };

  const nextStatuses = getNextStatuses(item.status);

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="工作清单详情"
      size="lg"
      position="right"
    >
      <div className="space-y-6">
        {/* Title and Status */}
        <div>
          <div className="flex items-start justify-between mb-2">
            <h2 className="text-xl font-semibold text-gray-900">{item.title}</h2>
            <WorklistStatusBadge status={item.status} size="md" />
          </div>
          {item.excerpt && (
            <p className="text-sm text-gray-600">{item.excerpt}</p>
          )}
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center text-sm text-gray-600">
            <User className="w-4 h-4 mr-2" />
            <span>作者: {item.author}</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <FileText className="w-4 h-4 mr-2" />
            <span>{item.metadata.word_count.toLocaleString()} 字</span>
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="w-4 h-4 mr-2" />
            <span>{item.metadata.estimated_reading_time} 分钟阅读</span>
          </div>
          {item.metadata.quality_score !== undefined && (
            <div className="flex items-center text-sm text-gray-600">
              <CheckCircle className="w-4 h-4 mr-2" />
              <span>质量分数: {item.metadata.quality_score.toFixed(0)}/100</span>
            </div>
          )}
        </div>

        {/* Tags and Categories */}
        {(item.tags && item.tags.length > 0) ||
        (item.categories && item.categories.length > 0) ? (
          <div className="space-y-2">
            {item.tags && item.tags.length > 0 && (
              <div className="flex items-start">
                <Tag className="w-4 h-4 text-gray-400 mr-2 mt-0.5" />
                <div className="flex flex-wrap gap-2">
                  {item.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {item.categories && item.categories.length > 0 && (
              <div className="flex items-start">
                <Folder className="w-4 h-4 text-gray-400 mr-2 mt-0.5" />
                <div className="flex flex-wrap gap-2">
                  {item.categories.map((category, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      {category}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}

        {/* Timeline */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3">时间线</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">创建时间:</span>
              <span className="text-gray-900">{formatDate(item.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">更新时间:</span>
              <span className="text-gray-900">{formatDate(item.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">状态变更:</span>
              <span className="text-gray-900">
                {formatDate(item.status_changed_at)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">最后同步:</span>
              <span className="text-gray-900">
                {formatDate(item.metadata.last_synced_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Google Drive Link */}
        <div>
          <a
            href={`https://docs.google.com/document/d/${item.drive_file_id}/edit`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            在 Google Drive 中打开
          </a>
        </div>

        {/* Notes */}
        {item.notes && item.notes.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3">备注历史</h3>
            <div className="space-y-3 max-h-60 overflow-y-auto">
              {item.notes.map((note) => (
                <div
                  key={note.id}
                  className={`p-3 rounded-lg ${
                    note.resolved ? 'bg-gray-50' : 'bg-yellow-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {note.author}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatDate(note.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{note.content}</p>
                  {note.resolved && (
                    <span className="inline-flex items-center text-xs text-green-600 mt-1">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      已解决
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Status Transition */}
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
                  变更为: {getStatusLabel(status)}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Publish Button */}
        {item.status === 'ready_to_publish' && onPublish && (
          <div className="border-t border-gray-200 pt-4">
            <Button variant="primary" onClick={handlePublish} fullWidth>
              <Send className="w-4 h-4 mr-2" />
              发布到 WordPress
            </Button>
          </div>
        )}
      </div>

      {/* Footer */}
      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>
          关闭
        </Button>
      </DrawerFooter>
    </Drawer>
  );
};
