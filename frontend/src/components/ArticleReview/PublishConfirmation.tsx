/**
 * PublishConfirmation - Confirmation dialog before uploading to WordPress
 *
 * Phase 12: Clarified "上稿" workflow
 * - Articles are ALWAYS uploaded as DRAFT to WordPress
 * - Final publishing is done by editors in WordPress admin
 * - "上稿" = Upload to WP as draft, NOT publish
 */

import React from 'react';
import { Button } from '../ui';
import { CheckCircle, Upload, Info } from 'lucide-react';
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
  const getVisibilityText = () => {
    switch (settings.visibility) {
      case 'public':
        return '公開';
      case 'private':
        return '私密';
      case 'password':
        return '密碼保護';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-start gap-3">
          <Upload className="w-6 h-6 text-blue-500 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              確認上稿
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              文章將上傳到 WordPress 作為草稿
            </p>
          </div>
        </div>

        {/* Article Title */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600 mb-1">文章標題</div>
          <div className="font-medium text-gray-900">{articleTitle}</div>
        </div>

        {/* Settings Summary */}
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">上稿模式</span>
            <span className="text-sm font-medium text-green-600">草稿（不發布）</span>
          </div>

          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">可見性設置</span>
            <span className="text-sm font-medium text-gray-900">{getVisibilityText()}</span>
          </div>

          {settings.visibility === 'password' && settings.password && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">訪問密碼</span>
              <span className="text-sm font-medium text-gray-900 font-mono">
                {settings.password}
              </span>
            </div>
          )}

          {settings.primary_category && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">主分類</span>
              <span className="text-sm font-medium text-gray-900">
                {settings.primary_category}
              </span>
            </div>
          )}

          {settings.secondary_categories && settings.secondary_categories.length > 0 && (
            <div className="flex items-start justify-between py-2 border-b">
              <span className="text-sm text-gray-600">副分類</span>
              <span className="text-sm font-medium text-gray-900 text-right">
                {settings.secondary_categories.join(', ')}
              </span>
            </div>
          )}

          {settings.tags && settings.tags.length > 0 && (
            <div className="flex items-start justify-between py-2 border-b">
              <span className="text-sm text-gray-600">標籤</span>
              <span className="text-sm font-medium text-gray-900 text-right">
                {settings.tags.join(', ')}
              </span>
            </div>
          )}

          {settings.featured_image && (
            <div className="flex items-center justify-between py-2 border-b">
              <span className="text-sm text-gray-600">特色圖片</span>
              <span className="text-sm font-medium text-green-600">✓ 已設置</span>
            </div>
          )}
        </div>

        {/* Info Banner - Explains what will happen */}
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-green-800">
              <p className="font-medium mb-1">上稿後會發生什麼？</p>
              <ul className="list-disc list-inside space-y-1 text-green-700">
                <li>文章將上傳到 WordPress 並保存為<strong>草稿</strong></li>
                <li>文章<strong>不會</strong>直接發布到網站</li>
                <li>最終審稿編輯可在 WordPress 後台審核後再發布</li>
              </ul>
            </div>
          </div>
        </div>

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
