/**
 * MetadataSummaryPanel - Comprehensive metadata overview for publish preview
 *
 * Phase 11.5: Enhanced Publish Preview
 * - SEO metadata (title, description, keywords)
 * - Categories (primary + secondary)
 * - Tags
 * - Article statistics
 * - Proofreading summary
 *
 * Layout:
 * ┌─────────────────────────────────┐
 * │ 📊 SEO 优化                     │
 * │ ──────────────────────────────  │
 * │ 标题: xxx                       │
 * │ 描述: xxx                       │
 * │ 关键词: tag1, tag2, tag3        │
 * ├─────────────────────────────────┤
 * │ 📁 分类与标签                   │
 * │ ──────────────────────────────  │
 * │ 主分类: xxx                     │
 * │ 副分类: xxx, xxx                │
 * │ 标签: tag1, tag2                │
 * ├─────────────────────────────────┤
 * │ 📈 文章统计                     │
 * │ ──────────────────────────────  │
 * │ 字数: 2,345                     │
 * │ 阅读时间: ~5分钟                │
 * │ 校对修改: 12处                  │
 * └─────────────────────────────────┘
 */

import React from 'react';
import {
  Search,
  FolderTree,
  Tag,
  BarChart3,
  Clock,
  FileText,
  Edit3,
  Check,
  X,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { Badge } from '../ui';

export interface MetadataSummaryPanelProps {
  /** SEO data */
  seo: {
    title?: string;
    description?: string;
    keywords: string[];
    score?: number;
  };
  /** Category data */
  categories: {
    primary?: string | null;
    secondary: string[];
  };
  /** Tags */
  tags: string[];
  /** Article statistics */
  stats: {
    wordCount: number;
    charCount: number;
    readingTimeMinutes?: number;
    paragraphCount?: number;
  };
  /** Proofreading summary */
  proofreading?: {
    totalChanges: number;
    additions: number;
    deletions: number;
    modifications: number;
  };
  /** Featured image URL */
  featuredImage?: string;
}

/**
 * MetadataSummaryPanel Component
 */
export const MetadataSummaryPanel: React.FC<MetadataSummaryPanelProps> = ({
  seo,
  categories,
  tags,
  stats,
  proofreading,
  featuredImage,
}) => {
  // Calculate reading time if not provided
  const readingTime = stats.readingTimeMinutes ?? Math.ceil(stats.wordCount / 200);

  return (
    <div className="space-y-4">
      {/* SEO Section */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <Search className="w-4 h-4 text-blue-600" />
          SEO 优化
          {seo.score != null && (
            <span
              className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                seo.score >= 0.7
                  ? 'bg-green-100 text-green-700'
                  : seo.score >= 0.5
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {Math.round(seo.score * 100)}分
            </span>
          )}
        </h4>
        <div className="space-y-2.5">
          {/* SEO Title */}
          <div>
            <div className="text-xs text-gray-500 mb-0.5">SEO 标题</div>
            <div className="text-sm text-gray-900">
              {seo.title || <span className="text-gray-400 italic">使用文章标题</span>}
            </div>
          </div>
          {/* Meta Description */}
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Meta 描述</div>
            <div className="text-sm text-gray-900 line-clamp-2">
              {seo.description || <span className="text-gray-400 italic">未设置</span>}
            </div>
          </div>
          {/* Keywords */}
          <div>
            <div className="text-xs text-gray-500 mb-1">关键词 ({seo.keywords.length})</div>
            {seo.keywords.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {seo.keywords.map((keyword, idx) => (
                  <Badge
                    key={idx}
                    variant="secondary"
                    className="text-xs bg-blue-50 text-blue-700 border-blue-200"
                  >
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-400 italic">未设置</span>
            )}
          </div>
        </div>
      </div>

      {/* Categories & Tags Section */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <FolderTree className="w-4 h-4 text-purple-600" />
          分类与标签
        </h4>
        <div className="space-y-2.5">
          {/* Primary Category */}
          <div>
            <div className="text-xs text-gray-500 mb-1">主分类</div>
            {categories.primary ? (
              <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                {categories.primary}
              </Badge>
            ) : (
              <span className="text-sm text-amber-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                未设置
              </span>
            )}
          </div>
          {/* Secondary Categories */}
          {categories.secondary.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-1">
                副分类 ({categories.secondary.length})
              </div>
              <div className="flex flex-wrap gap-1.5">
                {categories.secondary.map((cat, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {cat}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {/* Tags */}
          <div>
            <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
              <Tag className="w-3 h-3" />
              标签 ({tags.length})
            </div>
            {tags.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag, idx) => (
                  <Badge
                    key={idx}
                    variant="info"
                    className="text-xs bg-cyan-50 text-cyan-700 border-cyan-200"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-400 italic">无标签</span>
            )}
          </div>
        </div>
      </div>

      {/* Statistics Section */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <BarChart3 className="w-4 h-4 text-green-600" />
          文章统计
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-lg font-semibold text-gray-900">
              {stats.charCount.toLocaleString('zh-CN')}
            </div>
            <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
              <FileText className="w-3 h-3" />
              字符
            </div>
          </div>
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-lg font-semibold text-gray-900">~{readingTime}分钟</div>
            <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
              <Clock className="w-3 h-3" />
              阅读时间
            </div>
          </div>
        </div>
      </div>

      {/* Proofreading Summary */}
      {proofreading && proofreading.totalChanges > 0 && (
        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
            <Sparkles className="w-4 h-4 text-amber-600" />
            校对摘要
          </h4>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 bg-green-50 rounded">
              <div className="text-base font-semibold text-green-700">{proofreading.additions}</div>
              <div className="text-xs text-green-600 flex items-center justify-center gap-0.5">
                <Check className="w-3 h-3" />
                新增
              </div>
            </div>
            <div className="p-2 bg-amber-50 rounded">
              <div className="text-base font-semibold text-amber-700">
                {proofreading.modifications}
              </div>
              <div className="text-xs text-amber-600 flex items-center justify-center gap-0.5">
                <Edit3 className="w-3 h-3" />
                修改
              </div>
            </div>
            <div className="p-2 bg-red-50 rounded">
              <div className="text-base font-semibold text-red-700">{proofreading.deletions}</div>
              <div className="text-xs text-red-600 flex items-center justify-center gap-0.5">
                <X className="w-3 h-3" />
                删除
              </div>
            </div>
          </div>
          <div className="mt-2 text-center text-xs text-gray-500">
            共 {proofreading.totalChanges} 处修改
          </div>
        </div>
      )}

      {/* Featured Image Preview */}
      {featuredImage && (
        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
            <Check className="w-4 h-4 text-green-600" />
            特色图片
          </h4>
          <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={featuredImage}
              alt="特色图片"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

MetadataSummaryPanel.displayName = 'MetadataSummaryPanel';
