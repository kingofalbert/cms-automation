/**
 * PublishConfirmation - Confirmation dialog before publishing
 *
 * Phase 8.4: Publish Preview Panel
 * - Shows summary of publish settings
 * - Final confirmation before publish
 * - Overlay modal
 */

import React from 'react';
import { Button } from '../ui';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import type { PublishSettings } from './PublishPreviewPanel';

export interface PublishConfirmationProps {
  /** Publish settings to confirm */
  settings: PublishSettings;
  /** Article title */
  articleTitle: string;
  /** Callback when confirmed */
  onConfirm: () => void;
  /** Callback when cancelled */
  onCancel: () => void;
  /** Whether publishing is in progress */
  isPublishing?: boolean;
}

/**
 * PublishConfirmation Component
 */
export const PublishConfirmation: React.FC<PublishConfirmationProps> = ({
  settings,
  articleTitle,
  onConfirm,
  onCancel,
  isPublishing = false,
}) => {
  const getStatusText = () => {
    switch (settings.status) {
      case 'publish':
        return '上稿並發布';
      case 'draft':
        return '上稿（草稿）';
      case 'schedule':
        return '定時上稿';
    }
  };

  const getVisibilityText = () => {
    switch (settings.visibility) {
      case 'public':
        return '公开';
      case 'private':
        return '私密';
      case 'password':
        return '密码保护';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              確認上稿
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              請確認以下上稿設置是否正確
            </p>
          </div>
        </div>

        {/* Article Title */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600 mb-1">文章标题</div>
          <div className="font-medium text-gray-900">{articleTitle}</div>
        </div>

        {/* Settings Summary */}
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">上稿狀態</span>
            <span className="text-sm font-medium text-gray-900">{getStatusText()}</span>
          </div>

          {settings.status === 'schedule' && settings.publish_date && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">上稿時間</span>
              <span className="text-sm font-medium text-gray-900">
                {new Date(settings.publish_date).toLocaleString('zh-CN')}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">可见性</span>
            <span className="text-sm font-medium text-gray-900">{getVisibilityText()}</span>
          </div>

          {settings.visibility === 'password' && settings.password && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">访问密码</span>
              <span className="text-sm font-medium text-gray-900 font-mono">
                {settings.password}
              </span>
            </div>
          )}

          {settings.categories && settings.categories.length > 0 && (
            <div className="flex items-start justify-between py-2 border-b">
              <span className="text-sm text-gray-600">分类</span>
              <span className="text-sm font-medium text-gray-900 text-right">
                {settings.categories.join(', ')}
              </span>
            </div>
          )}

          {settings.tags && settings.tags.length > 0 && (
            <div className="flex items-start justify-between py-2 border-b">
              <span className="text-sm text-gray-600">标签</span>
              <span className="text-sm font-medium text-gray-900 text-right">
                {settings.tags.join(', ')}
              </span>
            </div>
          )}

          {settings.featured_image && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">特色图片</span>
              <span className="text-sm font-medium text-green-600">✓ 已设置</span>
            </div>
          )}
        </div>

        {/* Warning */}
        {settings.status === 'publish' && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-amber-800">
                <strong>注意：</strong>文章將立即發布到網站，所有用戶都可以訪問。
              </p>
            </div>
          </div>
        )}

        {settings.status === 'draft' && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">
                文章將上稿到 WordPress 並保存為草稿，不會發布。最終審稿編輯可在 WordPress 後台進行最後審核後發布。
              </p>
            </div>
          </div>
        )}

        {settings.status === 'schedule' && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800">
                文章將在指定時間自動發布。
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isPublishing}
            className="flex-1"
          >
            取消
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isPublishing}
            className="flex-1"
          >
            {isPublishing ? '上稿中...' : '確認上稿'}
          </Button>
        </div>
      </div>
    </div>
  );
};

PublishConfirmation.displayName = 'PublishConfirmation';
