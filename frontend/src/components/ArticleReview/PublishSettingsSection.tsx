/**
 * PublishSettingsSection - Publish settings configuration
 *
 * Phase 8.4: Publish Preview Panel
 * Phase 11: Primary + Secondary category system
 * - Status: draft/publish/schedule
 * - Visibility: public/private/password
 * - Publish date/time (for scheduled)
 * - Primary category (single selection, determines URL)
 * - Secondary categories (multiple selection, for cross-listing)
 * - Tags selection
 * - Featured image URL
 * - Excerpt
 */

import React, { useState, useMemo } from 'react';
import { Button } from '../ui';
import { Settings, Calendar, Eye, Lock, Hash, Tag as TagIcon, Image as ImageIcon, FileText, Star, Folder, ChevronDown, ChevronRight } from 'lucide-react';
import {
  PRIMARY_CATEGORIES,
  CATEGORY_HIERARCHY,
  getSecondaryCategories,
} from '../../config/wordpressTaxonomy';

export interface PublishSettingsSectionProps {
  publishStatus: 'draft' | 'publish' | 'schedule';
  visibility: 'public' | 'private' | 'password';
  password: string;
  publishDate: string;
  /** @deprecated Use primaryCategory and secondaryCategories instead */
  categories?: string[];
  /** Primary category (主分類) - determines URL structure */
  primaryCategory: string | null;
  /** Secondary categories (副分類) - for cross-listing */
  secondaryCategories: string[];
  tags: string[];
  featuredImage: string;
  excerpt: string;
  onPublishStatusChange: (status: 'draft' | 'publish' | 'schedule') => void;
  onVisibilityChange: (visibility: 'public' | 'private' | 'password') => void;
  onPasswordChange: (password: string) => void;
  onPublishDateChange: (date: string) => void;
  /** @deprecated Use onPrimaryCategoryChange and onSecondaryCategoriesChange instead */
  onCategoriesChange?: (categories: string[]) => void;
  onPrimaryCategoryChange: (category: string | null) => void;
  onSecondaryCategoriesChange: (categories: string[]) => void;
  onTagsChange: (tags: string[]) => void;
  onFeaturedImageChange: (url: string) => void;
  onExcerptChange: (excerpt: string) => void;
}

/**
 * PublishSettingsSection Component
 */
export const PublishSettingsSection: React.FC<PublishSettingsSectionProps> = ({
  publishStatus,
  visibility,
  password,
  publishDate,
  primaryCategory,
  secondaryCategories,
  tags,
  featuredImage,
  excerpt,
  onPublishStatusChange,
  onVisibilityChange,
  onPasswordChange,
  onPublishDateChange,
  onPrimaryCategoryChange,
  onSecondaryCategoriesChange,
  onTagsChange,
  onFeaturedImageChange,
  onExcerptChange,
}) => {
  const [tagInput, setTagInput] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Get available secondary categories based on selected primary
  const availableSecondaryCategories = useMemo(() => {
    if (!primaryCategory) return [];
    return getSecondaryCategories(primaryCategory);
  }, [primaryCategory]);

  const handlePrimaryCategoryChange = (category: string) => {
    onPrimaryCategoryChange(category);
    // Clear secondary categories when primary changes (since they might not be valid anymore)
    onSecondaryCategoriesChange([]);
  };

  const handleSecondaryToggle = (category: string) => {
    if (secondaryCategories.includes(category)) {
      onSecondaryCategoriesChange(secondaryCategories.filter((c) => c !== category));
    } else {
      onSecondaryCategoriesChange([...secondaryCategories, category]);
    }
  };

  const toggleCategoryExpand = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const handleAddTag = () => {
    const trimmed = tagInput.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onTagsChange([...tags, trimmed]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    onTagsChange(tags.filter((t) => t !== tag));
  };

  const handleKeyPress = (e: React.KeyboardEvent, handler: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handler();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">上稿設置</h3>
      </div>

      {/* Upload Mode - Always draft */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          上稿模式
        </label>
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            <strong>草稿模式</strong> - 文章將上傳到 WordPress 作為草稿，由最終審稿編輯在 WordPress 後台審核後再發布。
          </p>
        </div>
      </div>


      {/* Visibility */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Eye className="w-4 h-4" />
          可见性
        </label>
        <div className="flex gap-2">
          {(['public', 'private', 'password'] as const).map((vis) => (
            <button
              key={vis}
              type="button"
              onClick={() => onVisibilityChange(vis)}
              className={`px-4 py-2 text-sm rounded ${
                visibility === vis
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {vis === 'public' && '公开'}
              {vis === 'private' && '私密'}
              {vis === 'password' && '密码保护'}
            </button>
          ))}
        </div>
      </div>

      {/* Password (only for password visibility) */}
      {visibility === 'password' && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Lock className="w-4 h-4" />
            密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder="設置訪問密碼"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

      {/* Primary Category (主分類) */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Star className="w-4 h-4 text-yellow-500" />
          主分類 (Primary Category) <span className="text-red-500">*</span>
        </label>
        <p className="text-xs text-gray-500 mb-2">
          決定文章URL結構和麵包屑導航
        </p>
        <select
          value={primaryCategory || ''}
          onChange={(e) => handlePrimaryCategoryChange(e.target.value || '')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">-- 請選擇主分類 --</option>
          {PRIMARY_CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        {primaryCategory && (
          <div className="mt-2 inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
            <Star className="w-3 h-3" />
            {primaryCategory}
            <span className="text-xs text-yellow-600 ml-1">(主分類)</span>
          </div>
        )}
      </div>

      {/* Secondary Categories (副分類) */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Folder className="w-4 h-4" />
          副分類 (Secondary Categories)
        </label>
        <p className="text-xs text-gray-500 mb-2">
          讓文章同時出現在其他分類列表頁面 (可多選)
        </p>

        {/* Show subcategories of selected primary category */}
        {primaryCategory && availableSecondaryCategories.length > 0 && (
          <div className="border border-gray-200 rounded-md p-3 bg-gray-50">
            <div
              className="flex items-center gap-2 cursor-pointer mb-2"
              onClick={() => toggleCategoryExpand(primaryCategory)}
            >
              {expandedCategories.has(primaryCategory) ? (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500" />
              )}
              <span className="text-sm font-medium text-gray-700">
                {primaryCategory} 的子分類
              </span>
            </div>
            {expandedCategories.has(primaryCategory) && (
              <div className="grid grid-cols-2 gap-2 ml-6">
                {availableSecondaryCategories.map((subCategory) => (
                  <label
                    key={subCategory}
                    className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-900"
                  >
                    <input
                      type="checkbox"
                      checked={secondaryCategories.includes(subCategory)}
                      onChange={() => handleSecondaryToggle(subCategory)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    {subCategory}
                  </label>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Show other primary categories as cross-listing options */}
        <div className="border border-gray-200 rounded-md p-3">
          <div className="text-sm font-medium text-gray-700 mb-2">
            其他主分類 (交叉列表)
          </div>
          <div className="grid grid-cols-2 gap-2">
            {PRIMARY_CATEGORIES.filter((cat) => cat !== primaryCategory).map((category) => (
              <label
                key={category}
                className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-900"
              >
                <input
                  type="checkbox"
                  checked={secondaryCategories.includes(category)}
                  onChange={() => handleSecondaryToggle(category)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                {category}
              </label>
            ))}
          </div>
        </div>

        {/* Display selected secondary categories */}
        {secondaryCategories.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {secondaryCategories.map((category) => (
              <span
                key={category}
                className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
              >
                {category}
                <button
                  type="button"
                  onClick={() => handleSecondaryToggle(category)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <TagIcon className="w-4 h-4" />
          標籤
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, handleAddTag)}
            placeholder="輸入標籤名稱"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <Button size="sm" onClick={handleAddTag}>
            添加
          </Button>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {tags.map((tag, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 text-blue-500 hover:text-blue-700"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Featured Image */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <ImageIcon className="w-4 h-4" />
          特色图片 URL
        </label>
        <input
          type="text"
          value={featuredImage}
          onChange={(e) => onFeaturedImageChange(e.target.value)}
          placeholder="https://example.com/image.jpg"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        {featuredImage && (
          <div className="mt-2 aspect-video bg-gray-100 rounded overflow-hidden max-w-xs">
            <img
              src={featuredImage}
              alt="特色圖片預覽"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23f3f4f6" width="200" height="150"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%236b7280" font-family="sans-serif" font-size="12"%3E載入失敗%3C/text%3E%3C/svg%3E';
              }}
            />
          </div>
        )}
      </div>

      {/* Excerpt */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <FileText className="w-4 h-4" />
          摘要
        </label>
        <textarea
          value={excerpt}
          onChange={(e) => onExcerptChange(e.target.value)}
          placeholder="简短描述文章内容..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <div className="text-xs text-gray-500">
          {excerpt.length} 字符 (推荐 100-200 字符)
        </div>
      </div>
    </div>
  );
};

PublishSettingsSection.displayName = 'PublishSettingsSection';
