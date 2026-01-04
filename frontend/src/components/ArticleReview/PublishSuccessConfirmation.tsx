/**
 * PublishSuccessConfirmation - Success dialog after WordPress draft upload
 *
 * Phase 17: Shows WordPress draft URL and screenshot for visual confirmation
 * - Displays WordPress draft URL (clickable)
 * - Shows upload timestamp
 * - Displays final screenshot of WordPress draft
 * - Provides next steps guidance
 */

import React, { useState } from 'react';
import { Button } from '../ui';
import { CheckCircle, ExternalLink, Clock, FileText, Image, X, ChevronLeft, ChevronRight } from 'lucide-react';

export interface PublishSuccessConfirmationProps {
  /** Article title */
  articleTitle: string;
  /** WordPress draft URL */
  wordpressDraftUrl: string;
  /** Upload timestamp (ISO string) */
  uploadedAt: string;
  /** WordPress post ID */
  wordpressPostId: number;
  /** Screenshots from publishing process */
  screenshots?: string[];
  /** Callback when modal is closed */
  onClose: () => void;
  /** Callback to open WordPress in new tab */
  onOpenWordPress?: () => void;
}

/**
 * Format ISO date string to readable format
 */
const formatDateTime = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return isoString;
  }
};

/**
 * PublishSuccessConfirmation Component
 */
export const PublishSuccessConfirmation: React.FC<PublishSuccessConfirmationProps> = ({
  articleTitle,
  wordpressDraftUrl,
  uploadedAt,
  wordpressPostId,
  screenshots = [],
  onClose,
  onOpenWordPress,
}) => {
  const [selectedScreenshotIndex, setSelectedScreenshotIndex] = useState<number | null>(null);
  const [imageError, setImageError] = useState<Record<number, boolean>>({});

  const handleOpenWordPress = () => {
    if (onOpenWordPress) {
      onOpenWordPress();
    } else {
      window.open(wordpressDraftUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleScreenshotClick = (index: number) => {
    setSelectedScreenshotIndex(index);
  };

  const handleCloseLightbox = () => {
    setSelectedScreenshotIndex(null);
  };

  const handlePrevScreenshot = () => {
    if (selectedScreenshotIndex !== null && selectedScreenshotIndex > 0) {
      setSelectedScreenshotIndex(selectedScreenshotIndex - 1);
    }
  };

  const handleNextScreenshot = () => {
    if (selectedScreenshotIndex !== null && selectedScreenshotIndex < screenshots.length - 1) {
      setSelectedScreenshotIndex(selectedScreenshotIndex + 1);
    }
  };

  const handleImageError = (index: number) => {
    setImageError((prev) => ({ ...prev, [index]: true }));
  };

  const hasScreenshots = screenshots.length > 0;
  const lastScreenshot = hasScreenshots ? screenshots[screenshots.length - 1] : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6 space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="p-2 bg-green-100 rounded-full">
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              上稿成功
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              文章已成功上傳到 WordPress 作為草稿
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="關閉"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Screenshot Preview */}
        {lastScreenshot && !imageError[screenshots.length - 1] && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Image className="w-4 h-4" />
              <span>WordPress 草稿截圖</span>
              {screenshots.length > 1 && (
                <span className="text-xs text-gray-400">
                  (共 {screenshots.length} 張截圖)
                </span>
              )}
            </div>
            <div
              className="relative border border-gray-200 rounded-lg overflow-hidden cursor-pointer hover:border-blue-400 transition-colors group"
              onClick={() => handleScreenshotClick(screenshots.length - 1)}
            >
              <img
                src={lastScreenshot}
                alt="WordPress 草稿截圖"
                className="w-full h-auto max-h-64 object-contain bg-gray-50"
                onError={() => handleImageError(screenshots.length - 1)}
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-colors flex items-center justify-center">
                <span className="opacity-0 group-hover:opacity-100 text-white text-sm bg-black bg-opacity-60 px-3 py-1 rounded transition-opacity">
                  點擊放大
                </span>
              </div>
            </div>
          </div>
        )}

        {/* WordPress Draft Info */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <FileText className="w-4 h-4" />
            <span>WordPress 草稿資訊</span>
          </div>

          {/* Article Title */}
          <div className="p-4 bg-gray-50 rounded-lg space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">文章標題</div>
              <div className="font-medium text-gray-900">{articleTitle}</div>
            </div>

            {/* WordPress URL */}
            <div>
              <div className="text-xs text-gray-500 mb-1">WordPress 草稿連結</div>
              <a
                href={wordpressDraftUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline break-all text-sm flex items-start gap-1"
              >
                <span className="flex-1">{wordpressDraftUrl}</span>
                <ExternalLink className="w-3 h-3 flex-shrink-0 mt-1" />
              </a>
            </div>

            {/* Upload Time and Post ID */}
            <div className="flex gap-6">
              <div>
                <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  上傳時間
                </div>
                <div className="text-sm text-gray-900">{formatDateTime(uploadedAt)}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">WordPress 文章 ID</div>
                <div className="text-sm text-gray-900 font-mono">{wordpressPostId}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <div className="text-blue-600 mt-0.5">💡</div>
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">下一步</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li>點擊上方連結前往 WordPress 後台查看草稿</li>
                <li>最終審稿編輯可在 WordPress 後台進行最後審核並發布</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1"
          >
            關閉
          </Button>
          <Button
            onClick={handleOpenWordPress}
            className="flex-1 flex items-center justify-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            打開 WordPress
          </Button>
        </div>
      </div>

      {/* Lightbox for screenshot viewing */}
      {selectedScreenshotIndex !== null && screenshots[selectedScreenshotIndex] && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-[60]"
          onClick={handleCloseLightbox}
        >
          <button
            onClick={handleCloseLightbox}
            className="absolute top-4 right-4 p-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
            aria-label="關閉"
          >
            <X className="w-6 h-6 text-white" />
          </button>

          {/* Navigation arrows */}
          {selectedScreenshotIndex > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePrevScreenshot();
              }}
              className="absolute left-4 p-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
              aria-label="上一張"
            >
              <ChevronLeft className="w-6 h-6 text-white" />
            </button>
          )}
          {selectedScreenshotIndex < screenshots.length - 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleNextScreenshot();
              }}
              className="absolute right-4 p-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
              aria-label="下一張"
            >
              <ChevronRight className="w-6 h-6 text-white" />
            </button>
          )}

          <div className="max-w-[90vw] max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <img
              src={screenshots[selectedScreenshotIndex]}
              alt={`截圖 ${selectedScreenshotIndex + 1}`}
              className="max-w-full max-h-[85vh] object-contain"
            />
            <div className="text-center text-white text-sm mt-2">
              {selectedScreenshotIndex + 1} / {screenshots.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

PublishSuccessConfirmation.displayName = 'PublishSuccessConfirmation';
