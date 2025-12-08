/**
 * ContentComparisonCard - Side-by-side comparison for Before/After content
 *
 * Phase 8.3: Improved UX for parsing review
 * - Clear side-by-side comparison layout
 * - "Document Extracted" vs "AI Optimized" terminology
 * - Visual diff highlighting
 * - Action buttons for applying changes
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────────┐
 * │  📝 元描述 (Meta Description)                                    │
 * ├────────────────────────────┬────────────────────────────────────┤
 * │  📄 文档提取 (79字)         │  🤖 AI 优化建议 (78字)              │
 * │  ─────────────────────────  │  ──────────────────────────────    │
 * │  萊姆病每年影響約47.6萬名   │  萊姆病每年影響近50萬美國人，      │
 * │  美國人，常因症狀多變而延   │  症狀從皮疹到神經問題變化多端...   │
 * │  誤治療。本文詳細介紹...    │                                    │
 * │                            │                                    │
 * │  ✓ 长度合适                │  ✓ 更生动的表述                    │
 * ├────────────────────────────┴────────────────────────────────────┤
 * │  ○ 使用文档提取  ● 使用AI建议  ○ 自定义编辑                      │
 * └─────────────────────────────────────────────────────────────────┘
 */

import React, { useState } from 'react';
import { Card } from '../ui';
import { Badge } from '../ui';
import { Button } from '../ui';
import {
  FileText,
  Sparkles,
  Check,
  AlertCircle,
  Copy,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export type ContentSource = 'extracted' | 'ai' | 'custom';

export interface ContentComparisonCardProps {
  /** Card title */
  title: string;
  /** Icon to display */
  icon?: React.ReactNode;
  /** Content extracted from document */
  extractedContent: string;
  /** AI suggested content */
  aiSuggestedContent?: string;
  /** Currently selected source */
  selectedSource: ContentSource;
  /** Custom edited content (when source is 'custom') */
  customContent?: string;
  /** Callback when source changes */
  onSourceChange: (source: ContentSource, content: string) => void;
  /** Callback when custom content is edited */
  onCustomContentChange?: (content: string) => void;
  /** Optimal length range [min, max] */
  optimalLength?: [number, number];
  /** Quality indicators for extracted content */
  extractedQuality?: Array<{ label: string; status: 'good' | 'warning' | 'error' }>;
  /** Quality indicators for AI content */
  aiQuality?: Array<{ label: string; status: 'good' | 'warning' | 'error' }>;
  /** AI reasoning explanation */
  aiReasoning?: string;
  /** Whether to show expanded view by default */
  defaultExpanded?: boolean;
  /** Test ID for testing */
  testId?: string;
}

/**
 * Get length status based on optimal range
 */
const getLengthStatus = (
  length: number,
  optimalRange?: [number, number]
): 'good' | 'warning' | 'error' => {
  if (!optimalRange) return 'good';
  const [min, max] = optimalRange;
  if (length >= min && length <= max) return 'good';
  if (length > 0 && (length >= min * 0.7 || length <= max * 1.3)) return 'warning';
  return 'error';
};

/**
 * Status indicator component
 */
const StatusIndicator: React.FC<{
  status: 'good' | 'warning' | 'error';
  label: string;
}> = ({ status, label }) => {
  const config = {
    good: { icon: Check, color: 'text-green-600', bg: 'bg-green-50' },
    warning: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-50' },
    error: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50' },
  };
  const { icon: Icon, color, bg } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${color} ${bg}`}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
};

/**
 * ContentComparisonCard Component
 */
export const ContentComparisonCard: React.FC<ContentComparisonCardProps> = ({
  title,
  icon,
  extractedContent,
  aiSuggestedContent,
  selectedSource,
  customContent,
  onSourceChange,
  onCustomContentChange,
  optimalLength,
  extractedQuality,
  aiQuality,
  aiReasoning,
  defaultExpanded = true,
  testId,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(customContent || '');

  const extractedLength = extractedContent?.length || 0;
  const aiLength = aiSuggestedContent?.length || 0;
  const hasExtracted = extractedLength > 0;
  const hasAi = aiSuggestedContent && aiLength > 0;

  // If no content at all, don't render
  if (!hasExtracted && !hasAi) {
    return null;
  }

  const handleSelectSource = (source: ContentSource) => {
    let content = '';
    if (source === 'extracted') {
      content = extractedContent;
    } else if (source === 'ai') {
      content = aiSuggestedContent || '';
    } else {
      content = customContent || extractedContent || aiSuggestedContent || '';
    }
    onSourceChange(source, content);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    // TODO: Show toast notification
  };

  const handleSaveCustom = () => {
    onCustomContentChange?.(editValue);
    onSourceChange('custom', editValue);
    setIsEditing(false);
  };

  return (
    <Card
      className="overflow-hidden border-2 transition-all duration-200"
      data-testid={testId}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100 border-b cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {icon || <FileText className="w-5 h-5 text-slate-600" />}
          <h3 className="font-semibold text-slate-900">{title}</h3>
          {selectedSource !== 'extracted' && (
            <Badge variant="info" className="text-xs">
              {selectedSource === 'ai' ? 'AI优化' : '自定义'}
            </Badge>
          )}
        </div>
        <button className="p-1 hover:bg-slate-200 rounded transition-colors">
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-500" />
          )}
        </button>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-4">
          {/* Side-by-side comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Left: Document Extracted */}
            <div
              className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                selectedSource === 'extracted'
                  ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-200'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
              onClick={() => handleSelectSource('extracted')}
            >
              {/* Label */}
              <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50/80">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-slate-700">文档提取</span>
                  <span className="text-xs text-slate-500">({extractedLength} 字)</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy(extractedContent);
                  }}
                  className="p-1 hover:bg-slate-200 rounded"
                  title="复制"
                >
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                </button>
              </div>

              {/* Content */}
              <div className="p-3 min-h-[100px]">
                {hasExtracted ? (
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">
                    {extractedContent}
                  </p>
                ) : (
                  <p className="text-sm text-slate-400 italic">未提取到内容</p>
                )}
              </div>

              {/* Quality indicators */}
              <div className="px-3 py-2 border-t bg-slate-50/50 flex flex-wrap gap-1.5">
                <StatusIndicator
                  status={getLengthStatus(extractedLength, optimalLength)}
                  label={
                    optimalLength
                      ? `${extractedLength}/${optimalLength[0]}-${optimalLength[1]}字`
                      : `${extractedLength}字`
                  }
                />
                {extractedQuality?.map((q, i) => (
                  <StatusIndicator key={i} status={q.status} label={q.label} />
                ))}
              </div>

              {/* Selection indicator */}
              {selectedSource === 'extracted' && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>

            {/* Right: AI Optimized */}
            {hasAi && (
              <div
                className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                  selectedSource === 'ai'
                    ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-200'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
                onClick={() => handleSelectSource('ai')}
              >
                {/* Label */}
                <div className="flex items-center justify-between px-3 py-2 border-b bg-gradient-to-r from-emerald-50 to-teal-50">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <span className="text-sm font-medium text-emerald-700">AI 优化建议</span>
                    <span className="text-xs text-emerald-600">({aiLength} 字)</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(aiSuggestedContent || '');
                    }}
                    className="p-1 hover:bg-emerald-100 rounded"
                    title="复制"
                  >
                    <Copy className="w-3.5 h-3.5 text-emerald-500" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-3 min-h-[100px]">
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">
                    {aiSuggestedContent}
                  </p>
                </div>

                {/* Quality indicators */}
                <div className="px-3 py-2 border-t bg-emerald-50/50 flex flex-wrap gap-1.5">
                  <StatusIndicator
                    status={getLengthStatus(aiLength, optimalLength)}
                    label={
                      optimalLength
                        ? `${aiLength}/${optimalLength[0]}-${optimalLength[1]}字`
                        : `${aiLength}字`
                    }
                  />
                  {aiQuality?.map((q, i) => (
                    <StatusIndicator key={i} status={q.status} label={q.label} />
                  ))}
                </div>

                {/* Selection indicator */}
                {selectedSource === 'ai' && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* AI Reasoning (if available) */}
          {aiReasoning && (
            <div className="mb-4 p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-200">
              <div className="flex items-start gap-2">
                <span className="text-lg">💡</span>
                <div>
                  <p className="text-xs font-medium text-amber-800 mb-1">AI 优化理由</p>
                  <p className="text-sm text-amber-700">{aiReasoning}</p>
                </div>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-3 border-t">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">当前选择:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleSelectSource('extracted')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'extracted'
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  文档提取
                </button>
                {hasAi && (
                  <button
                    onClick={() => handleSelectSource('ai')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                      selectedSource === 'ai'
                        ? 'bg-emerald-500 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    AI优化
                  </button>
                )}
                <button
                  onClick={() => {
                    setEditValue(
                      selectedSource === 'extracted'
                        ? extractedContent
                        : selectedSource === 'ai'
                        ? aiSuggestedContent || ''
                        : customContent || ''
                    );
                    setIsEditing(true);
                  }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'custom'
                      ? 'bg-purple-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  自定义
                </button>
              </div>
            </div>
          </div>

          {/* Custom editing modal */}
          {isEditing && (
            <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-purple-800">自定义编辑</span>
                <span className="text-xs text-purple-600">{editValue.length} 字</span>
              </div>
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full h-32 p-3 text-sm border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-purple-400"
                placeholder="输入自定义内容..."
              />
              <div className="flex justify-end gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(false)}
                >
                  取消
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveCustom}
                  className="bg-purple-500 hover:bg-purple-600"
                >
                  应用
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

ContentComparisonCard.displayName = 'ContentComparisonCard';
