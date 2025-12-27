/**
 * PublishReadinessChecklist - Visual checklist for publish readiness
 *
 * Phase 11.5: Enhanced Publish Preview
 * - Shows completion status for all required publishing items
 * - Visual checkmarks with color coding
 * - Helps editors verify all content is ready
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────────────────────┐
 * │ ✓ 标题  ✓ 正文  ✓ SEO  ✓ 分类  ○ 图片  │  4/5 完成                         │
 * └─────────────────────────────────────────────────────────────────────────────┘
 */

import React from 'react';
import {
  Check,
  Circle,
  Type,
  FileText,
  Search,
  FolderTree,
  Image as ImageIcon,
  Tag,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

export interface ChecklistItem {
  id: string;
  label: string;
  completed: boolean;
  required: boolean;
  icon: React.ReactNode;
}

export interface PublishReadinessChecklistProps {
  /** Checklist items to display */
  items: ChecklistItem[];
  /** Overall readiness status */
  isReady: boolean;
}

/**
 * PublishReadinessChecklist Component
 */
export const PublishReadinessChecklist: React.FC<PublishReadinessChecklistProps> = ({
  items,
  isReady,
}) => {
  const completedCount = items.filter((item) => item.completed).length;
  const requiredItems = items.filter((item) => item.required);
  const requiredCompleted = requiredItems.filter((item) => item.completed).length;
  const allRequiredComplete = requiredCompleted === requiredItems.length;

  return (
    <div
      className={`p-4 rounded-lg border ${
        isReady
          ? 'bg-green-50 border-green-200'
          : allRequiredComplete
          ? 'bg-blue-50 border-blue-200'
          : 'bg-amber-50 border-amber-200'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Checklist items */}
        <div className="flex items-center gap-4 flex-wrap">
          {items.map((item) => (
            <div
              key={item.id}
              className={`flex items-center gap-1.5 text-sm ${
                item.completed
                  ? 'text-green-700'
                  : item.required
                  ? 'text-amber-700'
                  : 'text-gray-500'
              }`}
              title={item.required ? '必填项' : '可选项'}
            >
              {item.completed ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Circle
                  className={`w-4 h-4 ${
                    item.required ? 'text-amber-500' : 'text-gray-400'
                  }`}
                />
              )}
              <span className="flex items-center gap-1">
                {item.icon}
                {item.label}
              </span>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="flex items-center gap-3">
          <span
            className={`text-sm font-medium ${
              isReady ? 'text-green-700' : allRequiredComplete ? 'text-blue-700' : 'text-amber-700'
            }`}
          >
            {completedCount}/{items.length} 完成
          </span>
          {isReady ? (
            <span className="flex items-center gap-1 text-sm font-semibold text-green-700 bg-green-100 px-2 py-1 rounded-full">
              <Check className="w-4 h-4" />
              准备就绪
            </span>
          ) : allRequiredComplete ? (
            <span className="flex items-center gap-1 text-sm font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded-full">
              <Check className="w-4 h-4" />
              必填完成
            </span>
          ) : (
            <span className="flex items-center gap-1 text-sm font-medium text-amber-700 bg-amber-100 px-2 py-1 rounded-full">
              <AlertCircle className="w-4 h-4" />
              需完善
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Helper function to create default checklist items from article data
 */
export const createChecklistItems = (data: {
  hasTitle: boolean;
  hasContent: boolean;
  hasSeoKeywords: boolean;
  hasSeoDescription: boolean;
  hasCategory: boolean;
  hasTags: boolean;
  hasFeaturedImage: boolean;
  hasFaqs?: boolean;
  faqApplicable?: boolean; // Whether FAQ is applicable for this article type
}): ChecklistItem[] => {
  const items: ChecklistItem[] = [
    {
      id: 'title',
      label: '标题',
      completed: data.hasTitle,
      required: true,
      icon: <Type className="w-3 h-3" />,
    },
    {
      id: 'content',
      label: '正文',
      completed: data.hasContent,
      required: true,
      icon: <FileText className="w-3 h-3" />,
    },
    {
      id: 'seo',
      label: 'SEO',
      completed: data.hasSeoKeywords || data.hasSeoDescription,
      required: true,
      icon: <Search className="w-3 h-3" />,
    },
    {
      id: 'category',
      label: '分类',
      completed: data.hasCategory,
      required: true,
      icon: <FolderTree className="w-3 h-3" />,
    },
    {
      id: 'tags',
      label: '标签',
      completed: data.hasTags,
      required: false,
      icon: <Tag className="w-3 h-3" />,
    },
    {
      id: 'image',
      label: '图片',
      completed: data.hasFeaturedImage,
      required: false,
      icon: <ImageIcon className="w-3 h-3" />,
    },
  ];

  // Only show FAQ check if FAQ is applicable for this article type
  if (data.faqApplicable !== false) {
    items.push({
      id: 'faq',
      label: 'FAQ',
      completed: data.hasFaqs ?? false,
      required: false, // FAQ is optional but recommended
      icon: <HelpCircle className="w-3 h-3" />,
    });
  }

  return items;
};

PublishReadinessChecklist.displayName = 'PublishReadinessChecklist';
