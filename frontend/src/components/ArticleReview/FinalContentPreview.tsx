/**
 * FinalContentPreview - Final content preview before publish
 *
 * Phase 8.4: Publish Preview Panel
 * - Shows final article as it will appear
 * - Title, author, content, images
 * - SEO metadata preview
 * - Categories and tags
 */

import React from 'react';
import { FileText, User, Hash, Tag as TagIcon, Image as ImageIcon } from 'lucide-react';
import { Badge } from '../ui';

export interface FinalContentPreviewProps {
  /** Content data to preview */
  data: {
    title: string;
    content: string;
    author: string;
    featuredImage?: string;
    seoMetadata: {
      metaDescription: string;
      keywords: string[];
    };
    categories: string[];
    tags: string[];
  };
}

/**
 * FinalContentPreview Component
 */
export const FinalContentPreview: React.FC<FinalContentPreviewProps> = ({ data }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">内容预览</h3>
      </div>

      {/* Title */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-gray-900 leading-tight">
          {data.title || '(无标题)'}
        </h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <User className="w-4 h-4" />
          <span>{data.author || '(无作者)'}</span>
        </div>
      </div>

      {/* Featured Image */}
      {data.featuredImage && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <ImageIcon className="w-4 h-4" />
            <span className="font-medium">特色图片</span>
          </div>
          <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={data.featuredImage}
              alt="特色图片"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23f3f4f6" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%236b7280" font-family="sans-serif" font-size="16"%3E图片加载失败%3C/text%3E%3C/svg%3E';
              }}
            />
          </div>
        </div>
      )}

      {/* Content Preview (truncated) */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-gray-700">正文内容</div>
        <div className="p-3 bg-gray-50 border border-gray-200 rounded max-h-64 overflow-auto">
          <div
            className="prose prose-sm max-w-none text-gray-800"
            dangerouslySetInnerHTML={{
              __html: data.content.substring(0, 800) + (data.content.length > 800 ? '...' : ''),
            }}
          />
        </div>
        <div className="text-xs text-gray-500">
          共 {data.content.length} 字符
        </div>
      </div>

      {/* Categories */}
      {data.categories.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Hash className="w-4 h-4" />
            <span className="font-medium">分类</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.categories.map((category, idx) => (
              <Badge key={idx} variant="secondary">
                {category}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Tags */}
      {data.tags.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <TagIcon className="w-4 h-4" />
            <span className="font-medium">标签</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.tags.map((tag, idx) => (
              <Badge key={idx} variant="info">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* SEO Metadata */}
      <div className="space-y-2 pt-4 border-t">
        <div className="text-sm font-medium text-gray-700">SEO 元数据</div>
        <div className="space-y-2">
          <div className="text-xs">
            <span className="text-gray-600">描述: </span>
            <span className="text-gray-800">
              {data.seoMetadata.metaDescription || '(无描述)'}
            </span>
          </div>
          {data.seoMetadata.keywords.length > 0 && (
            <div className="text-xs">
              <span className="text-gray-600">关键词: </span>
              <span className="text-gray-800">
                {data.seoMetadata.keywords.join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Info box */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
        <strong>提示：</strong>这是文章的最终预览。请仔细检查所有内容，确认无误后再发布。
      </div>
    </div>
  );
};

FinalContentPreview.displayName = 'FinalContentPreview';
