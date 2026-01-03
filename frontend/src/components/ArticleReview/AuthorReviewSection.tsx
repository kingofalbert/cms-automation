/**
 * AuthorReviewSection - Author information review
 *
 * Phase 8.2: Parsing Review Panel
 * - Display extracted author
 * - Allow manual editing
 * - Author suggestions
 */

import React from 'react';
import { Input } from '../ui/Input';
import { User } from 'lucide-react';

export interface AuthorReviewSectionProps {
  /** Current author */
  author: string;
  /** Original extracted author */
  originalAuthor: string;
  /** Callback when author changes */
  onAuthorChange: (author: string) => void;
}

/**
 * AuthorReviewSection Component
 */
export const AuthorReviewSection: React.FC<AuthorReviewSectionProps> = ({
  author,
  originalAuthor,
  onAuthorChange,
}) => {
  const isModified = author !== originalAuthor;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <User className="w-5 h-5" />
          作者審核
        </h3>
        {isModified && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            已修改
          </span>
        )}
      </div>

      {/* Original author (if modified) */}
      {isModified && originalAuthor && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-xs text-gray-500 mb-1">原始作者</div>
          <div className="text-sm text-gray-700">{originalAuthor}</div>
        </div>
      )}

      {/* Current author input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          當前作者
        </label>
        <Input
          type="text"
          value={author}
          onChange={(e) => onAuthorChange(e.target.value)}
          placeholder="輸入作者名稱"
          className="w-full"
        />
        {!author && (
          <p className="text-xs text-amber-600">
            ⚠️ 建議填寫作者信息以增強文章可信度
          </p>
        )}
      </div>

      {/* Common authors quick select */}
      <div className="space-y-2">
        <div className="text-xs text-gray-500">常用作者</div>
        <div className="flex flex-wrap gap-2">
          {['編輯部', '管理員', '匿名'].map((commonAuthor) => (
            <button
              key={commonAuthor}
              type="button"
              onClick={() => onAuthorChange(commonAuthor)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
            >
              {commonAuthor}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

AuthorReviewSection.displayName = 'AuthorReviewSection';
