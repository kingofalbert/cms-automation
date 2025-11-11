/**
 * DiffViewSection - Side-by-side diff view
 *
 * Phase 8.3: Proofreading Review Panel
 * - Shows original vs proofread content
 * - Highlights differences
 * - Scrollable comparison
 */

import React, { useState } from 'react';
import { FileText, Eye } from 'lucide-react';

export interface DiffViewSectionProps {
  /** Original content */
  originalContent: string;
  /** Proofread content */
  proofreadContent: string;
}

/**
 * DiffViewSection Component
 */
export const DiffViewSection: React.FC<DiffViewSectionProps> = ({
  originalContent,
  proofreadContent,
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  // Simple diff highlighting (for demo - in production use a proper diff library)
  const hasChanges = originalContent !== proofreadContent;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          对比视图
        </h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setViewMode('split')}
            className={`px-3 py-1 text-xs rounded ${
              viewMode === 'split'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            分栏
          </button>
          <button
            type="button"
            onClick={() => setViewMode('unified')}
            className={`px-3 py-1 text-xs rounded ${
              viewMode === 'unified'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            统一
          </button>
        </div>
      </div>

      {!hasChanges && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
          <Eye className="w-12 h-12 mx-auto text-green-600 mb-2" />
          <p className="text-sm text-green-800">内容未修改</p>
        </div>
      )}

      {hasChanges && viewMode === 'split' && (
        <div className="grid grid-cols-2 gap-4">
          {/* Original */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-500 bg-red-50 px-2 py-1 rounded">
              原始内容
            </div>
            <div className="p-3 bg-red-50 border border-red-200 rounded max-h-96 overflow-auto">
              <pre className="text-xs text-gray-800 whitespace-pre-wrap break-words">
                {originalContent.substring(0, 500)}
                {originalContent.length > 500 && '...'}
              </pre>
            </div>
          </div>

          {/* Proofread */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-500 bg-green-50 px-2 py-1 rounded">
              校对后内容
            </div>
            <div className="p-3 bg-green-50 border border-green-200 rounded max-h-96 overflow-auto">
              <pre className="text-xs text-gray-800 whitespace-pre-wrap break-words">
                {proofreadContent.substring(0, 500)}
                {proofreadContent.length > 500 && '...'}
              </pre>
            </div>
          </div>
        </div>
      )}

      {hasChanges && viewMode === 'unified' && (
        <div className="space-y-2">
          <div className="p-3 bg-gray-50 border border-gray-200 rounded max-h-96 overflow-auto">
            <div className="space-y-2 text-xs">
              <div className="bg-red-50 px-2 py-1 rounded">
                <span className="text-red-600 font-mono">- </span>
                <span className="text-gray-800">
                  {originalContent.substring(0, 200)}...
                </span>
              </div>
              <div className="bg-green-50 px-2 py-1 rounded">
                <span className="text-green-600 font-mono">+ </span>
                <span className="text-gray-800">
                  {proofreadContent.substring(0, 200)}...
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="p-2 bg-gray-50 rounded text-center">
          <div className="text-gray-500">原始</div>
          <div className="font-medium text-gray-900">
            {originalContent.length} 字符
          </div>
        </div>
        <div className="p-2 bg-gray-50 rounded text-center">
          <div className="text-gray-500">校对后</div>
          <div className="font-medium text-gray-900">
            {proofreadContent.length} 字符
          </div>
        </div>
        <div className="p-2 bg-gray-50 rounded text-center">
          <div className="text-gray-500">差异</div>
          <div className={`font-medium ${hasChanges ? 'text-amber-600' : 'text-green-600'}`}>
            {hasChanges ? '有修改' : '无修改'}
          </div>
        </div>
      </div>
    </div>
  );
};

DiffViewSection.displayName = 'DiffViewSection';
