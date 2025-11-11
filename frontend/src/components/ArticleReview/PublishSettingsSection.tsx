/**
 * PublishSettingsSection - Publish settings configuration
 *
 * Phase 8.4: Publish Preview Panel
 * - Status: draft/publish/schedule
 * - Visibility: public/private/password
 * - Publish date/time (for scheduled)
 * - Categories and tags selection
 * - Featured image URL
 * - Excerpt
 */

import React, { useState } from 'react';
import { Button } from '../ui';
import { Settings, Calendar, Eye, Lock, Hash, Tag as TagIcon, Image as ImageIcon, FileText } from 'lucide-react';

export interface PublishSettingsSectionProps {
  publishStatus: 'draft' | 'publish' | 'schedule';
  visibility: 'public' | 'private' | 'password';
  password: string;
  publishDate: string;
  categories: string[];
  tags: string[];
  featuredImage: string;
  excerpt: string;
  onPublishStatusChange: (status: 'draft' | 'publish' | 'schedule') => void;
  onVisibilityChange: (visibility: 'public' | 'private' | 'password') => void;
  onPasswordChange: (password: string) => void;
  onPublishDateChange: (date: string) => void;
  onCategoriesChange: (categories: string[]) => void;
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
  categories,
  tags,
  featuredImage,
  excerpt,
  onPublishStatusChange,
  onVisibilityChange,
  onPasswordChange,
  onPublishDateChange,
  onCategoriesChange,
  onTagsChange,
  onFeaturedImageChange,
  onExcerptChange,
}) => {
  const [categoryInput, setCategoryInput] = useState('');
  const [tagInput, setTagInput] = useState('');

  const handleAddCategory = () => {
    const trimmed = categoryInput.trim();
    if (trimmed && !categories.includes(trimmed)) {
      onCategoriesChange([...categories, trimmed]);
      setCategoryInput('');
    }
  };

  const handleRemoveCategory = (category: string) => {
    onCategoriesChange(categories.filter((c) => c !== category));
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
        <h3 className="text-lg font-semibold text-gray-900">发布设置</h3>
      </div>

      {/* Publish Status */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          发布状态
        </label>
        <div className="flex gap-2">
          {(['publish', 'draft', 'schedule'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => onPublishStatusChange(status)}
              className={`px-4 py-2 text-sm rounded ${
                publishStatus === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status === 'publish' && '立即发布'}
              {status === 'draft' && '保存草稿'}
              {status === 'schedule' && '定时发布'}
            </button>
          ))}
        </div>
      </div>

      {/* Publish Date (only for schedule) */}
      {publishStatus === 'schedule' && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            发布时间 <span className="text-red-500">*</span>
          </label>
          <input
            type="datetime-local"
            value={publishDate}
            onChange={(e) => onPublishDateChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

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
            placeholder="设置访问密码"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

      {/* Categories */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Hash className="w-4 h-4" />
          分类
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={categoryInput}
            onChange={(e) => setCategoryInput(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, handleAddCategory)}
            placeholder="输入分类名称"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <Button size="sm" onClick={handleAddCategory}>
            添加
          </Button>
        </div>
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {categories.map((category, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
              >
                {category}
                <button
                  type="button"
                  onClick={() => handleRemoveCategory(category)}
                  className="ml-1 text-gray-500 hover:text-gray-700"
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
          标签
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, handleAddTag)}
            placeholder="输入标签名称"
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
              alt="特色图片预览"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23f3f4f6" width="200" height="150"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%236b7280" font-family="sans-serif" font-size="12"%3E加载失败%3C/text%3E%3C/svg%3E';
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
