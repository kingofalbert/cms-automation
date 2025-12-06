/**
 * PublishSettingsSectionSimplified - Simplified publish settings (actions only)
 *
 * Phase 11: Moved content-related settings to ParsingReviewPanel
 * This component now only handles:
 * - Publish status: draft/publish/schedule
 * - Publish date (for scheduled)
 * - Visibility: public/private/password
 *
 * Removed (now in ParsingReviewPanel):
 * - Primary/Secondary categories
 * - Tags
 * - Featured image
 * - Excerpt
 */

import React from 'react';
import { Calendar, Eye, Lock, Send } from 'lucide-react';

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
  publishStatus,
  visibility,
  password,
  publishDate,
  onPublishStatusChange,
  onVisibilityChange,
  onPasswordChange,
  onPublishDateChange,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Send className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">发布设置</h3>
      </div>

      {/* Publish Status */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          发布状态
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(['publish', 'draft', 'schedule'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => onPublishStatusChange(status)}
              className={`px-4 py-3 text-sm rounded-lg border-2 transition-all ${
                publishStatus === status
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:bg-blue-50'
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
        <div className="space-y-2 p-4 bg-amber-50 rounded-lg border border-amber-200">
          <label className="text-sm font-medium text-amber-800 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            定时发布时间 <span className="text-red-500">*</span>
          </label>
          <input
            type="datetime-local"
            value={publishDate}
            onChange={(e) => onPublishDateChange(e.target.value)}
            className="w-full px-3 py-2 border border-amber-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
          />
          {!publishDate && (
            <p className="text-xs text-amber-600">请选择发布时间</p>
          )}
        </div>
      )}

      {/* Visibility */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <Eye className="w-4 h-4" />
          可见性
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
              {vis === 'public' && '公开'}
              {vis === 'private' && '私密'}
              {vis === 'password' && '密码保护'}
            </button>
          ))}
        </div>
      </div>

      {/* Password (only for password visibility) */}
      {visibility === 'password' && (
        <div className="space-y-2 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <label className="text-sm font-medium text-purple-800 flex items-center gap-2">
            <Lock className="w-4 h-4" />
            访问密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            placeholder="设置访问密码"
            className="w-full px-3 py-2 border border-purple-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
          />
          {!password && (
            <p className="text-xs text-purple-600">请设置访问密码</p>
          )}
        </div>
      )}

      {/* Summary Info */}
      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
        <h4 className="text-sm font-medium text-slate-700 mb-2">发布摘要</h4>
        <div className="space-y-1 text-sm text-slate-600">
          <p>
            <span className="text-slate-500">状态：</span>
            <span className="font-medium">
              {publishStatus === 'publish' && '立即发布'}
              {publishStatus === 'draft' && '保存为草稿'}
              {publishStatus === 'schedule' && `定时发布 ${publishDate || '(未设置)'}`}
            </span>
          </p>
          <p>
            <span className="text-slate-500">可见性：</span>
            <span className="font-medium">
              {visibility === 'public' && '公开'}
              {visibility === 'private' && '私密'}
              {visibility === 'password' && '密码保护'}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

PublishSettingsSectionSimplified.displayName = 'PublishSettingsSectionSimplified';
