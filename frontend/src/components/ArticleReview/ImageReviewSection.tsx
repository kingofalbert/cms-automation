/**
 * ImageReviewSection - Enhanced Image Review for Article Parsing
 *
 * Phase 13: Enhanced Image Review
 * - Display original source URL (Google Drive, etc.)
 * - Show caption (圖說) and Alt Text
 * - Display image resolution with Epoch Times standard comparison
 * - Highlight issues when standards not met
 * - Comprehensive metadata display
 */

import React, { useState, useCallback } from 'react';
import { Button } from '../ui';
import {
  Image as ImageIcon,
  X,
  ExternalLink,
  AlertTriangle,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
  FileImage,
  Ruler,
  HardDrive,
  Type,
  Link2,
  Sparkles,
  Loader2,
  Check,
  Edit3,
} from 'lucide-react';

/**
 * API response for image alt text suggestion
 */
interface ImageAltSuggestion {
  image_id: number;
  parsed_alt_text: string | null;
  parsed_caption: string | null;
  parsed_description: string | null;
  suggested_alt_text: string;
  suggested_alt_text_confidence: number;
  suggested_description: string;
  suggested_description_confidence: number;
  generation_method: 'vision' | 'context' | 'failed';
  model_used: string;
  tokens_used: number;
  error_message: string | null;
}

/**
 * Epoch Times image standards
 */
const EPOCH_TIMES_STANDARDS = {
  featuredImage: {
    minWidth: 1200,
    minHeight: 630,
    recommendedWidth: 1200,
    recommendedHeight: 630,
    maxFileSizeKB: 0,  // 不限制文件大小，允許原圖
    supportedFormats: ['JPEG', 'PNG', 'WebP', 'JPG'],
  },
  contentImage: {
    minWidth: 800,
    minHeight: 400,
    maxFileSizeKB: 0,  // 不限制文件大小，允許原圖
    supportedFormats: ['JPEG', 'PNG', 'WebP', 'JPG', 'GIF'],
  },
};

/**
 * Image metadata structure from API
 */
interface ImageMetadata {
  _schema_version?: string;
  image_technical_specs?: {
    width?: number;
    height?: number;
    aspect_ratio?: string;
    file_size_bytes?: number;
    mime_type?: string;
    format?: string;
    color_mode?: string;
    has_transparency?: boolean;
    bit_depth?: number;
    dpi?: number;
  };
  validation?: {
    is_valid?: boolean;
    validation_errors?: string[];
    validation_warnings?: string[];
  };
  exif_data?: {
    camera_make?: string;
    camera_model?: string;
    exif_date?: string;
  };
}

/**
 * Image type classification
 */
export type ImageType = 'featured' | 'content' | 'inline';

/**
 * Detection method for featured image
 */
export type DetectionMethod =
  | 'caption_keyword'
  | 'position_before_body'
  | 'manual'
  | 'position_legacy'
  | 'none';

/**
 * Article image data structure
 */
export interface ArticleImageData {
  id: number;
  article_id: number;
  preview_path?: string;
  source_path?: string;
  source_url?: string;
  caption?: string;
  alt_text?: string;
  description?: string;
  position: number;
  /** Phase 13: Whether this is the featured/cover image (置頂圖片) */
  is_featured?: boolean;
  /** Phase 13: Image type: featured (置頂) / content (正文) / inline (行內) */
  image_type?: ImageType;
  /** Phase 13: How featured status was detected */
  detection_method?: DetectionMethod;
  image_metadata?: ImageMetadata;
  created_at?: string;
  updated_at?: string;
}

export interface ImageReviewSectionProps {
  /** Featured image URL */
  featuredImage: string;
  /** Additional image URLs */
  additionalImages: string[];
  /** Full article image data from API */
  articleImages?: ArticleImageData[];
  /** Worklist item ID for uploads */
  worklistItemId: number;
  /** Callback when featured image changes */
  onFeaturedImageChange: (url: string) => void;
  /** Callback when additional images change */
  onAdditionalImagesChange: (urls: string[]) => void;
  /** Callback when image alt text is updated */
  onImageAltUpdate?: (imageId: number, altText: string, description: string) => void;
}

/**
 * Format file size for display
 */
const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '未知';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
};

/**
 * Check if resolution meets standards
 */
const checkResolution = (
  width?: number,
  height?: number,
  isFeatured: boolean = false
): { status: 'pass' | 'warning' | 'fail'; message: string } => {
  if (!width || !height) {
    return { status: 'warning', message: '無法獲取解析度信息' };
  }

  const standards = isFeatured
    ? EPOCH_TIMES_STANDARDS.featuredImage
    : EPOCH_TIMES_STANDARDS.contentImage;

  if (width >= standards.minWidth && height >= standards.minHeight) {
    return { status: 'pass', message: `✓ 符合標準 (≥${standards.minWidth}×${standards.minHeight})` };
  }

  if (width >= standards.minWidth * 0.8 && height >= standards.minHeight * 0.8) {
    return {
      status: 'warning',
      message: `⚠ 接近標準 (建議 ≥${standards.minWidth}×${standards.minHeight})`,
    };
  }

  return {
    status: 'fail',
    message: `✗ 低於標準 (需要 ≥${standards.minWidth}×${standards.minHeight})`,
  };
};

/**
 * Check if file size meets standards
 * When maxFileSizeKB is 0, no limit is applied
 */
const checkFileSize = (
  bytes?: number,
  isFeatured: boolean = false
): { status: 'pass' | 'warning' | 'fail'; message: string } => {
  if (!bytes) {
    return { status: 'warning', message: '無法獲取文件大小' };
  }

  const maxKB = isFeatured
    ? EPOCH_TIMES_STANDARDS.featuredImage.maxFileSizeKB
    : EPOCH_TIMES_STANDARDS.contentImage.maxFileSizeKB;

  const sizeKB = bytes / 1024;
  const sizeMB = sizeKB / 1024;

  // If maxKB is 0, no limit - always pass
  if (maxKB === 0) {
    if (sizeMB >= 1) {
      return { status: 'pass', message: `✓ ${sizeMB.toFixed(1)}MB (無大小限制)` };
    }
    return { status: 'pass', message: `✓ ${sizeKB.toFixed(0)}KB (無大小限制)` };
  }

  if (sizeKB <= maxKB) {
    return { status: 'pass', message: `✓ 文件大小符合 (≤${maxKB}KB)` };
  }

  if (sizeKB <= maxKB * 1.5) {
    return { status: 'warning', message: `⚠ 文件略大 (建議 ≤${maxKB}KB)` };
  }

  return { status: 'fail', message: `✗ 文件過大 (需要 ≤${maxKB}KB)` };
};

/**
 * Check if format is supported
 */
const checkFormat = (
  format?: string,
  isFeatured: boolean = false
): { status: 'pass' | 'warning' | 'fail'; message: string } => {
  if (!format) {
    return { status: 'warning', message: '無法獲取格式信息' };
  }

  const supportedFormats = isFeatured
    ? EPOCH_TIMES_STANDARDS.featuredImage.supportedFormats
    : EPOCH_TIMES_STANDARDS.contentImage.supportedFormats;

  const normalizedFormat = format.toUpperCase();

  if (supportedFormats.includes(normalizedFormat)) {
    return { status: 'pass', message: `✓ 格式支持 (${format})` };
  }

  return { status: 'fail', message: `✗ 格式不支持 (${format})` };
};

/**
 * Status badge component
 */
const StatusBadge: React.FC<{
  status: 'pass' | 'warning' | 'fail';
  message: string;
}> = ({ status, message }) => {
  const colors = {
    pass: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-amber-100 text-amber-800 border-amber-200',
    fail: 'bg-red-100 text-red-800 border-red-200',
  };

  const icons = {
    pass: <CheckCircle className="w-3 h-3" />,
    warning: <AlertTriangle className="w-3 h-3" />,
    fail: <AlertTriangle className="w-3 h-3" />,
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${colors[status]}`}
    >
      {icons[status]}
      {message}
    </span>
  );
};

/**
 * Featured image badge component
 * Displays detection method and confidence information
 */
const FeaturedBadge: React.FC<{
  detectionMethod?: DetectionMethod;
}> = ({ detectionMethod }) => {
  const getDetectionLabel = (): { label: string; tooltip: string } => {
    switch (detectionMethod) {
      case 'caption_keyword':
        return { label: '圖說標記', tooltip: 'Caption 包含「置頂」等關鍵字' };
      case 'position_before_body':
        return { label: '位置檢測', tooltip: '圖片位於正文之前' };
      case 'manual':
        return { label: '手動設置', tooltip: '由用戶手動標記為置頂' };
      case 'position_legacy':
        return { label: '舊版遷移', tooltip: '從舊版 position=0 遷移' };
      default:
        return { label: '自動檢測', tooltip: '系統自動識別' };
    }
  };

  const { label, tooltip } = getDetectionLabel();

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800 border border-amber-200"
      title={tooltip}
    >
      ⭐ 置頂圖片
      <span className="text-[10px] text-amber-600">({label})</span>
    </span>
  );
};

/**
 * Confidence badge component
 */
const ConfidenceBadge: React.FC<{ confidence: number }> = ({ confidence }) => {
  const percentage = Math.round(confidence * 100);
  let colorClass = 'bg-green-100 text-green-700';
  if (percentage < 70) colorClass = 'bg-amber-100 text-amber-700';
  if (percentage < 50) colorClass = 'bg-red-100 text-red-700';

  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded ${colorClass}`}>
      {percentage}% 信心度
    </span>
  );
};

/**
 * Single image card with detailed information and AI suggestions
 */
const ImageInfoCard: React.FC<{
  image: ArticleImageData;
  imageUrl: string;
  isFeatured: boolean;
  onRemove?: () => void;
  onAltTextUpdate?: (imageId: number, altText: string, description: string) => void;
}> = ({ image, imageUrl, isFeatured, onRemove, onAltTextUpdate }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [suggestion, setSuggestion] = useState<ImageAltSuggestion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingAltText, setEditingAltText] = useState<string | null>(null);
  const [editingDescription, setEditingDescription] = useState<string | null>(null);

  // Generate AI suggestions
  const handleGenerateAlt = useCallback(async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/images/${image.id}/generate-alt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ use_vision: true }),
      });

      if (!response.ok) {
        throw new Error(`生成失敗: ${response.statusText}`);
      }

      const data: ImageAltSuggestion = await response.json();
      setSuggestion(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失敗');
    } finally {
      setIsGenerating(false);
    }
  }, [image.id]);

  // Apply suggested alt text
  const handleApplyAltText = useCallback(() => {
    if (suggestion && onAltTextUpdate) {
      onAltTextUpdate(
        image.id,
        suggestion.suggested_alt_text,
        editingDescription ?? suggestion.suggested_description
      );
      // Update local state to show as "adopted"
      setEditingAltText(suggestion.suggested_alt_text);
    }
  }, [suggestion, image.id, onAltTextUpdate, editingDescription]);

  // Apply suggested description
  const handleApplyDescription = useCallback(() => {
    if (suggestion && onAltTextUpdate) {
      onAltTextUpdate(
        image.id,
        editingAltText ?? suggestion.suggested_alt_text,
        suggestion.suggested_description
      );
      setEditingDescription(suggestion.suggested_description);
    }
  }, [suggestion, image.id, onAltTextUpdate, editingAltText]);

  const specs = image.image_metadata?.image_technical_specs;
  const resolutionCheck = checkResolution(specs?.width, specs?.height, isFeatured);
  const fileSizeCheck = checkFileSize(specs?.file_size_bytes, isFeatured);
  const formatCheck = checkFormat(specs?.format, isFeatured);

  // Overall status
  const hasIssues =
    resolutionCheck.status === 'fail' ||
    fileSizeCheck.status === 'fail' ||
    formatCheck.status === 'fail';
  const hasWarnings =
    resolutionCheck.status === 'warning' ||
    fileSizeCheck.status === 'warning' ||
    formatCheck.status === 'warning';

  return (
    <div
      className={`border rounded-lg overflow-hidden ${
        hasIssues
          ? 'border-red-300 bg-red-50'
          : hasWarnings
          ? 'border-amber-300 bg-amber-50'
          : 'border-gray-200 bg-white'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b">
        <div className="flex items-center gap-2">
          <FileImage className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            {isFeatured ? '置頂圖片' : `正文圖片 #${image.position + 1}`}
          </span>
          {/* Phase 13: Show FeaturedBadge for featured images */}
          {isFeatured && (
            <FeaturedBadge detectionMethod={image.detection_method} />
          )}
          {hasIssues && (
            <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded">需修正</span>
          )}
          {!hasIssues && hasWarnings && (
            <span className="text-xs bg-amber-500 text-white px-1.5 py-0.5 rounded">建議優化</span>
          )}
          {!hasIssues && !hasWarnings && (
            <span className="text-xs bg-green-500 text-white px-1.5 py-0.5 rounded">符合標準</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-200 rounded"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          {onRemove && (
            <button
              type="button"
              onClick={onRemove}
              className="p-1 text-red-600 hover:bg-red-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="p-3 space-y-3">
          {/* Image preview and metadata side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Image preview */}
            <div className="space-y-2">
              <img
                src={imageUrl}
                alt={image.alt_text || image.caption || '文章圖片'}
                className="w-full h-40 object-cover rounded border border-gray-200"
              />
              {/* Resolution display */}
              {specs?.width && specs?.height && (
                <div className="text-center text-xs text-gray-600">
                  {specs.width} × {specs.height} px
                  {specs.aspect_ratio && ` (${specs.aspect_ratio})`}
                </div>
              )}
            </div>

            {/* Metadata */}
            <div className="space-y-2 text-sm">
              {/* Original URL */}
              {image.source_url && (
                <div className="flex items-start gap-2">
                  <Link2 className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-gray-500 mb-0.5">原始鏈接</div>
                    <a
                      href={image.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 break-all text-xs flex items-center gap-1"
                    >
                      {image.source_url.length > 50
                        ? `${image.source_url.slice(0, 50)}...`
                        : image.source_url}
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                  </div>
                </div>
              )}

              {/* Caption (圖說) */}
              <div className="flex items-start gap-2">
                <Type className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="text-xs text-gray-500 mb-0.5">圖說 (Caption)</div>
                  <div className={`text-xs ${image.caption ? 'text-gray-800' : 'text-gray-400 italic'}`}>
                    {image.caption || '未設置'}
                  </div>
                </div>
              </div>

              {/* Alt Text */}
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="text-xs text-gray-500 mb-0.5">Alt Text (無障礙)</div>
                  <div className={`text-xs ${image.alt_text ? 'text-gray-800' : 'text-gray-400 italic'}`}>
                    {image.alt_text || '未設置'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Suggestions Section */}
          <div className="border-t pt-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-medium text-gray-600 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-purple-500" />
                AI 建議 (Alt Text & Description)
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerateAlt}
                disabled={isGenerating}
                className="text-xs h-7 px-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3 h-3 mr-1" />
                    {suggestion ? '重新生成' : 'AI 生成'}
                  </>
                )}
              </Button>
            </div>

            {/* Error message */}
            {error && (
              <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 mb-2">
                {error}
              </div>
            )}

            {/* Suggestions display */}
            {suggestion && (
              <div className="space-y-3">
                {/* Generation info */}
                <div className="flex items-center gap-2 text-[10px] text-gray-500">
                  <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded">
                    {suggestion.generation_method === 'vision' ? '🔍 視覺分析' : '📝 上下文推斷'}
                  </span>
                  <span>模型: {suggestion.model_used}</span>
                  <span>Token: {suggestion.tokens_used}</span>
                </div>

                {/* Alt Text Comparison */}
                <div className="p-2 bg-gray-50 rounded border">
                  <div className="text-[10px] font-medium text-gray-600 mb-1.5 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Alt Text 對比
                  </div>

                  {/* Original */}
                  <div className="mb-2">
                    <div className="text-[10px] text-gray-500 mb-0.5">原始解析：</div>
                    <div className={`text-xs p-1.5 rounded border ${
                      image.alt_text ? 'bg-white border-gray-200' : 'bg-gray-100 border-gray-200 italic text-gray-400'
                    }`}>
                      {image.alt_text || '(未設置)'}
                    </div>
                  </div>

                  {/* AI Suggestion */}
                  <div>
                    <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-2">
                      <span>💡 AI 建議：</span>
                      <ConfidenceBadge confidence={suggestion.suggested_alt_text_confidence} />
                    </div>
                    <div className="flex gap-2">
                      <div className="flex-1 text-xs p-1.5 rounded border bg-purple-50 border-purple-200 text-purple-900">
                        {suggestion.suggested_alt_text}
                      </div>
                      <button
                        type="button"
                        onClick={handleApplyAltText}
                        className="px-2 py-1 bg-purple-600 text-white text-[10px] rounded hover:bg-purple-700 flex items-center gap-1 flex-shrink-0"
                        title="採用此建議"
                      >
                        <Check className="w-3 h-3" />
                        採用
                      </button>
                    </div>
                  </div>
                </div>

                {/* Description Comparison */}
                <div className="p-2 bg-gray-50 rounded border">
                  <div className="text-[10px] font-medium text-gray-600 mb-1.5 flex items-center gap-1">
                    <Edit3 className="w-3 h-3" />
                    Description 對比
                  </div>

                  {/* Original */}
                  <div className="mb-2">
                    <div className="text-[10px] text-gray-500 mb-0.5">原始解析：</div>
                    <div className={`text-xs p-1.5 rounded border ${
                      image.description ? 'bg-white border-gray-200' : 'bg-gray-100 border-gray-200 italic text-gray-400'
                    }`}>
                      {image.description || '(未設置)'}
                    </div>
                  </div>

                  {/* AI Suggestion */}
                  <div>
                    <div className="text-[10px] text-gray-500 mb-0.5 flex items-center gap-2">
                      <span>💡 AI 建議：</span>
                      <ConfidenceBadge confidence={suggestion.suggested_description_confidence} />
                    </div>
                    <div className="flex gap-2">
                      <div className="flex-1 text-xs p-1.5 rounded border bg-purple-50 border-purple-200 text-purple-900">
                        {suggestion.suggested_description}
                      </div>
                      <button
                        type="button"
                        onClick={handleApplyDescription}
                        className="px-2 py-1 bg-purple-600 text-white text-[10px] rounded hover:bg-purple-700 flex items-center gap-1 flex-shrink-0"
                        title="採用此建議"
                      >
                        <Check className="w-3 h-3" />
                        採用
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Placeholder when no suggestion yet */}
            {!suggestion && !isGenerating && !error && (
              <div className="p-3 bg-gray-50 border border-dashed border-gray-300 rounded text-center">
                <Sparkles className="w-6 h-6 mx-auto text-gray-400 mb-1" />
                <p className="text-xs text-gray-500">
                  點擊「AI 生成」按鈕，使用 GPT-4o 分析圖片並生成 Alt Text 和 Description 建議
                </p>
              </div>
            )}
          </div>

          {/* Standards comparison */}
          <div className="border-t pt-3">
            <div className="text-xs font-medium text-gray-600 mb-2 flex items-center gap-1">
              <Ruler className="w-3 h-3" />
              大紀元標準對比
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {/* Resolution */}
              <div className="p-2 bg-white rounded border">
                <div className="text-[10px] text-gray-500 mb-1">解析度</div>
                <div className="text-xs font-mono">
                  {specs?.width && specs?.height
                    ? `${specs.width}×${specs.height}`
                    : '未知'}
                </div>
                <StatusBadge status={resolutionCheck.status} message={resolutionCheck.message} />
              </div>

              {/* File size */}
              <div className="p-2 bg-white rounded border">
                <div className="text-[10px] text-gray-500 mb-1 flex items-center gap-1">
                  <HardDrive className="w-3 h-3" />
                  文件大小
                </div>
                <div className="text-xs font-mono">{formatFileSize(specs?.file_size_bytes)}</div>
                <StatusBadge status={fileSizeCheck.status} message={fileSizeCheck.message} />
              </div>

              {/* Format */}
              <div className="p-2 bg-white rounded border">
                <div className="text-[10px] text-gray-500 mb-1">格式</div>
                <div className="text-xs font-mono">{specs?.format || '未知'}</div>
                <StatusBadge status={formatCheck.status} message={formatCheck.message} />
              </div>
            </div>
          </div>

          {/* Issues summary if any */}
          {(hasIssues || hasWarnings) && (
            <div
              className={`p-2 rounded text-xs ${
                hasIssues ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
              }`}
            >
              <strong>分析結果：</strong>
              <ul className="mt-1 ml-4 list-disc space-y-0.5">
                {resolutionCheck.status !== 'pass' && <li>{resolutionCheck.message}</li>}
                {fileSizeCheck.status !== 'pass' && <li>{fileSizeCheck.message}</li>}
                {formatCheck.status !== 'pass' && <li>{formatCheck.message}</li>}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ImageReviewSection Component
 */
export const ImageReviewSection: React.FC<ImageReviewSectionProps> = ({
  featuredImage,
  additionalImages,
  articleImages = [],
  worklistItemId,
  onFeaturedImageChange,
  onAdditionalImagesChange,
  onImageAltUpdate,
}) => {
  const handleRemoveAdditionalImage = (index: number) => {
    const newImages = [...additionalImages];
    newImages.splice(index, 1);
    onAdditionalImagesChange(newImages);
  };

  // Phase 13: Use is_featured field for separation (fallback to position for legacy data)
  // Get featured image data - using is_featured field or fallback to position === 0
  const featuredImageData = articleImages.find(
    (img) => img.is_featured === true || (img.is_featured === undefined && img.position === 0)
  );

  // Get content images (non-featured), sorted by position
  const contentImagesData = articleImages
    .filter((img) => !img.is_featured && (img.is_featured !== undefined || img.position > 0))
    .sort((a, b) => a.position - b.position);

  // Count issues
  const totalIssues = articleImages.reduce((count, img) => {
    const specs = img.image_metadata?.image_technical_specs;
    // Use is_featured field for standards check (fallback to position for legacy)
    const isFeatured = img.is_featured === true || (img.is_featured === undefined && img.position === 0);
    if (checkResolution(specs?.width, specs?.height, isFeatured).status === 'fail') count++;
    if (checkFileSize(specs?.file_size_bytes, isFeatured).status === 'fail') count++;
    if (checkFormat(specs?.format, isFeatured).status === 'fail') count++;
    return count;
  }, 0);

  // Count featured vs content images for display
  const featuredCount = articleImages.filter(
    (img) => img.is_featured === true || (img.is_featured === undefined && img.position === 0)
  ).length;
  const contentCount = articleImages.length - featuredCount;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <ImageIcon className="w-5 h-5" />
        圖片審核
        <span className="text-sm font-normal text-gray-500">
          ({articleImages.length} 張圖片：{featuredCount} 置頂 + {contentCount} 正文)
        </span>
        {totalIssues > 0 && (
          <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
            {totalIssues} 個問題
          </span>
        )}
      </h3>

      {/* Featured Image (置頂圖片) */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          置頂圖片 (Featured Image)
        </label>
        {featuredImage && featuredImageData ? (
          <ImageInfoCard
            image={featuredImageData}
            imageUrl={featuredImage}
            isFeatured={true}
            onRemove={() => onFeaturedImageChange('')}
            onAltTextUpdate={onImageAltUpdate}
          />
        ) : featuredImage ? (
          // Legacy display if no article image data
          <div className="relative inline-block">
            <img
              src={featuredImage}
              alt="Featured"
              className="w-full max-w-md h-48 object-cover rounded-lg border border-gray-200"
            />
            <button
              type="button"
              onClick={() => onFeaturedImageChange('')}
              className="absolute top-2 right-2 p-1 bg-red-600 text-white rounded-full hover:bg-red-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="w-full max-w-md h-48 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ImageIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">暫無特色圖片</p>
              {/* Note: Image upload button removed - manual upload is a future feature */}
            </div>
          </div>
        )}
      </div>

      {/* Content Images (正文圖片) */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          正文圖片 (Content Images) ({contentCount})
        </label>
        {contentImagesData.length > 0 ? (
          <div className="space-y-3">
            {contentImagesData.map((imgData, index) => (
              <ImageInfoCard
                key={imgData.id}
                image={imgData}
                imageUrl={additionalImages[index] || imgData.source_url || ''}
                isFeatured={false}
                onRemove={() => handleRemoveAdditionalImage(index)}
                onAltTextUpdate={onImageAltUpdate}
              />
            ))}
          </div>
        ) : additionalImages.length > 0 ? (
          // Legacy grid display
          <div className="grid grid-cols-3 gap-2">
            {additionalImages.map((url, index) => (
              <div key={index} className="relative">
                <img
                  src={url}
                  alt={`Additional ${index + 1}`}
                  className="w-full h-24 object-cover rounded border border-gray-200"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveAdditionalImage(index)}
                  className="absolute top-1 right-1 p-0.5 bg-red-600 text-white rounded-full hover:bg-red-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">暫無附加圖片</p>
        )}
        {/* Note: "添加圖片" button removed - manual image upload is a future feature */}
      </div>

      {/* Image guidelines */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
        <strong>大紀元圖片標準：</strong>
        <ul className="mt-1 ml-4 list-disc space-y-1">
          <li>特色圖片建議尺寸：1200×630 像素 (最低)</li>
          <li>內文圖片建議尺寸：800×400 像素 (最低)</li>
          <li>支持格式：JPG, PNG, WebP</li>
          <li>每張圖片需設置圖說 (Caption) 和 Alt Text</li>
        </ul>
      </div>
    </div>
  );
};

ImageReviewSection.displayName = 'ImageReviewSection';
