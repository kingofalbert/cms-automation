/**
 * ArticleImagesList - Displays article images with alt text status
 *
 * Phase 16: Enhanced Publish Preview
 * - Shows all images from article_images
 * - Displays alt text status for each image
 * - Warning for missing alt text
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ 🖼️ 文章圖片 (3張)                                           │
 * ├─────────────────────────────────────────────────────────────┤
 * │ [縮圖1] food-1.jpg  ✅ Alt: 補血食材紅棗枸杞                │
 * │ [縮圖2] food-2.jpg  ⚠️ Alt: 缺失                           │
 * │ [縮圖3] recipe.jpg  ✅ Alt: 番茄牛肉湯                      │
 * └─────────────────────────────────────────────────────────────┘
 */

import React, { useState } from 'react';
import { Image as ImageIcon, Check, AlertCircle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

export interface ArticleImage {
  /** Image ID */
  id?: number;
  /** Image URL */
  image_url: string;
  /** Alt text */
  alt_text?: string | null;
  /** AI generated alt text */
  ai_alt_text?: string | null;
  /** Position in article */
  position?: number;
  /** Image filename */
  filename?: string;
  /** Original source URL */
  source_url?: string;
}

export interface ArticleImagesListProps {
  /** List of article images */
  images: ArticleImage[];
  /** Maximum images to show initially */
  initialDisplayCount?: number;
}

/**
 * ArticleImagesList Component
 *
 * Displays article images with their alt text status.
 */
export const ArticleImagesList: React.FC<ArticleImagesListProps> = ({
  images,
  initialDisplayCount = 3,
}) => {
  const [showAll, setShowAll] = useState(false);

  // If no images
  if (!images || images.length === 0) {
    return (
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <ImageIcon className="w-4 h-4 text-teal-600" />
          文章圖片
        </h4>
        <div className="text-sm text-gray-500 italic">
          無內文圖片
        </div>
      </div>
    );
  }

  // Count images with/without alt text
  const imagesWithAlt = images.filter(img => img.alt_text || img.ai_alt_text).length;
  const imagesMissingAlt = images.length - imagesWithAlt;

  // Images to display
  const displayImages = showAll ? images : images.slice(0, initialDisplayCount);
  const hasMore = images.length > initialDisplayCount;

  // Get filename from URL
  const getFilename = (url: string | undefined | null, fallbackFilename?: string): string => {
    if (fallbackFilename) return fallbackFilename;
    if (!url) return 'image'; // Handle undefined/null URL
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      return pathname.split('/').pop() || 'image';
    } catch {
      return url.split('/').pop() || 'image';
    }
  };

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
        <ImageIcon className="w-4 h-4 text-teal-600" />
        文章圖片 ({images.length}張)
        {imagesMissingAlt > 0 && (
          <span className="ml-auto text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {imagesMissingAlt}張缺少 Alt
          </span>
        )}
        {imagesMissingAlt === 0 && (
          <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Check className="w-3 h-3" />
            Alt 完整
          </span>
        )}
      </h4>

      {/* Image list */}
      <div className="space-y-2">
        {displayImages.map((image, index) => {
          const hasAlt = Boolean(image.alt_text || image.ai_alt_text);
          const displayAlt = image.alt_text || image.ai_alt_text;
          const filename = getFilename(image.image_url, image.filename);

          return (
            <div
              key={image.id || index}
              className="flex items-start gap-3 p-2 bg-gray-50 rounded-lg"
            >
              {/* Thumbnail */}
              <div className="w-12 h-12 bg-gray-200 rounded overflow-hidden shrink-0">
                <img
                  src={image.image_url}
                  alt={displayAlt || filename}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-700 font-medium truncate">
                    {filename}
                  </span>
                  {image.source_url && (
                    <a
                      href={image.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-blue-600"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                <div className="flex items-start gap-1 mt-1">
                  {hasAlt ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-600 shrink-0 mt-0.5" />
                      <span className="text-xs text-gray-600 line-clamp-2">
                        Alt: {displayAlt}
                        {image.ai_alt_text && !image.alt_text && (
                          <span className="text-blue-600 ml-1">(AI)</span>
                        )}
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                      <span className="text-xs text-amber-600">Alt: 缺失</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Show more/less toggle */}
      {hasMore && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="w-full mt-3 py-2 text-xs text-gray-600 hover:text-gray-800 flex items-center justify-center gap-1 border-t border-gray-100"
        >
          {showAll ? (
            <>
              <ChevronUp className="w-3 h-3" />
              收起
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" />
              顯示全部 ({images.length}張)
            </>
          )}
        </button>
      )}
    </div>
  );
};

ArticleImagesList.displayName = 'ArticleImagesList';
