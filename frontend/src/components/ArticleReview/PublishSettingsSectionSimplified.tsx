/**
 * PublishSettingsSectionSimplified - Simplified upload settings
 *
 * Phase 12: Clarified "上稿" workflow
 * - Articles are ALWAYS uploaded as DRAFT to WordPress
 * - Final publishing is done by editors in WordPress admin
 * - Only visibility settings are configurable (for when article is eventually published)
 *
 * This component now only handles:
 * - Visibility: public/private/password (applied when published in WP)
 *
 * NOTE: "上稿" means upload to WordPress as draft, NOT publish
 */

import React from 'react';
import { Eye, Lock, Upload, Info } from 'lucide-react';

export interface PublishSettingsSectionSimplifiedProps {
  publishStatus: 'draft' | 'publish' | 'schedule';
  visibility: 'public' | 'private' | 'password';
  password: string;
  publishDate: string;
  onPublishStatusChange: (status: 'draft' | 'publish' | 'schedule') => void;
  onVisibilityChange: (visibility: 'public' | 'private' | 'password') => void;
  onPasswordChange: (password: string) => void;
  onPublishDateChange: (date: string) => void;
}

/**
 * PublishSettingsSectionSimplified Component
 */
export const PublishSettingsSectionSimplified: React.FC<PublishSettingsSectionSimplifiedProps> = ({
  visibility,
  password,
  onVisibilityChange,
  onPasswordChange,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Upload className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">上稿設置</h3>
      </div>

      {/* Info Banner - Explains what "上稿" means */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">什麼是「上稿」？</p>
            <ul className="list-disc list-inside space-y-1 text-blue-700">
              <li>文章將上傳到 WordPress 並保存為<strong>草稿</strong></li>
              <li>文章<strong>不會</strong>直接發布到網站</li>
              <li>最終審稿編輯可在 WordPress 後台審核後再發布</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Visibility - For when article is eventually published */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Eye className="w-4 h-4" />
          可見性設置
          <span className="text-xs text-gray-500 font-normal">（發布時生效）</span>
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(['public', 'private', 'password'] as const).map((vis) => (
            <button
              key={vis}
              type="button"
              onClick={() => onVisibilityChange(vis)}
              className={`px-4 py-3 text-sm rounded-lg border-2 transition-all ${
                visibility === vis
                  ? 'bg-green-600 text-white border-green-600 shadow-md'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-green-300 hover:bg-green-50'
              }`}
            >
              {vis === 'public' && '公開'}
              {vis === 'private' && '私密'}
              {vis === 'password' && '密碼保護'}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500">
          此設置將在 WordPress 後台最終發布時套用
        </p>
      </div>

      {/* Password (only for password visibility) */}
      {visibility === 'password' && (
        <div className="space-y-2 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <label className="text-sm font-medium text-purple-800 flex items-center gap-2">
            <Lock className="w-4 h-4" />
            訪問密碼 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder="設置訪問密碼"
            className="w-full px-3 py-2 border border-purple-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
          />
          {!password && (
            <p className="text-xs text-purple-600">請設置訪問密碼</p>
          )}
        </div>
      )}

      {/* Summary Info */}
      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
        <h4 className="text-sm font-medium text-slate-700 mb-2">上稿摘要</h4>
        <div className="space-y-1 text-sm text-slate-600">
          <p>
            <span className="text-slate-500">上稿模式：</span>
            <span className="font-medium text-green-600">草稿（不發布）</span>
          </p>
          <p>
            <span className="text-slate-500">可見性：</span>
            <span className="font-medium">
              {visibility === 'public' && '公開'}
              {visibility === 'private' && '私密'}
              {visibility === 'password' && '密碼保護'}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

PublishSettingsSectionSimplified.displayName = 'PublishSettingsSectionSimplified';
