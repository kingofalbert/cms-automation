/**
 * Title Optimization Card (Phase 7)
 *
 * Displays AI-generated title optimization suggestions with:
 * - Original 3-part title structure
 * - 2-3 optimization options with scores
 * - Character count indicators
 * - Selection and editing capability
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/alert';
import type { TitleOption } from '../../services/parsing';

export interface TitleOptimizationCardProps {
  /** Original title components */
  original: {
    prefix?: string | null;
    main: string;
    suffix?: string | null;
    full: string;
  };
  /** AI-generated optimization options (2-3) */
  suggestions: TitleOption[];
  /** Optimization notes from AI */
  notes?: string[];
  /** Loading state during AI generation */
  isGenerating?: boolean;
  /** Selected option ID */
  selectedId?: string | null;
  /** Callback when user selects an option */
  onSelect?: (optionId: string) => void;
  /** Callback when user edits a title component */
  onEdit?: (optionId: string, field: 'prefix' | 'main' | 'suffix', value: string) => void;
}

/**
 * Get color for title score (0-100).
 */
function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600 bg-green-50';
  if (score >= 75) return 'text-blue-600 bg-blue-50';
  if (score >= 60) return 'text-yellow-600 bg-yellow-50';
  return 'text-gray-600 bg-gray-50';
}

/**
 * Get badge variant for title type.
 */
function getTypeVariant(type: string): 'default' | 'secondary' | 'info' {
  const typeMap: Record<string, 'default' | 'secondary' | 'info'> = {
    data_driven: 'default',
    authority_backed: 'secondary',
    how_to: 'default',
    comprehensive_guide: 'secondary',
    question_based: 'info',
  };
  return typeMap[type] || 'info';
}

/**
 * Format character count with color coding.
 */
function CharacterCount({ count, min, max }: { count: number; min: number; max: number }) {
  const isGood = count >= min && count <= max;
  const color = isGood ? 'text-green-600' : count < min ? 'text-yellow-600' : 'text-red-600';

  return (
    <span className={`text-xs font-mono ${color}`}>
      {count} 字符
      {!isGood && ` (建议: ${min}-${max})`}
    </span>
  );
}

export default function TitleOptimizationCard({
  original,
  suggestions,
  notes = [],
  isGenerating = false,
  selectedId,
  onSelect,
  onEdit,
}: TitleOptimizationCardProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{
    prefix: string;
    main: string;
    suffix: string;
  }>({ prefix: '', main: '', suffix: '' });

  const handleEditClick = (option: TitleOption) => {
    setEditingId(option.id);
    setEditValues({
      prefix: option.title_prefix || '',
      main: option.title_main,
      suffix: option.title_suffix || '',
    });
  };

  const handleSaveEdit = (optionId: string) => {
    // Call parent callback for each edited field
    if (onEdit) {
      onEdit(optionId, 'prefix', editValues.prefix);
      onEdit(optionId, 'main', editValues.main);
      onEdit(optionId, 'suffix', editValues.suffix);
    }
    setEditingId(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>标题优化建议</CardTitle>
        <CardDescription>
          AI 生成了 {suggestions.length} 个优化方案，选择最适合的标题或手动编辑
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Original Title */}
        <div className="border-l-4 border-gray-300 pl-4 py-2 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">原始标题</span>
            <Badge variant="default">当前使用</Badge>
          </div>
          <p className="text-lg font-semibold text-gray-900">{original.full}</p>
          {(original.prefix || original.suffix) && (
            <div className="mt-2 text-xs text-gray-600 space-y-1">
              {original.prefix && (
                <div>
                  <span className="font-medium">前缀:</span> {original.prefix}
                </div>
              )}
              <div>
                <span className="font-medium">主标题:</span> {original.main}
              </div>
              {original.suffix && (
                <div>
                  <span className="font-medium">副标题:</span> {original.suffix}
                </div>
              )}
            </div>
          )}
        </div>

        {/* AI Generation Loading */}
        {isGenerating && (
          <Alert>
            <AlertDescription className="flex items-center gap-2">
              <span className="animate-spin">⏳</span>
              正在生成 AI 优化建议... (预计 20-30 秒)
            </AlertDescription>
          </Alert>
        )}

        {/* Optimization Options */}
        {!isGenerating && suggestions.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900">
              优化方案 ({suggestions.length})
            </h4>

            {suggestions.map((option, index) => {
              const isSelected = option.id === selectedId;
              const isEditing = option.id === editingId;

              return (
                <div
                  key={option.id}
                  className={`border rounded-lg p-4 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {/* Option Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-gray-700">
                        方案 {index + 1}
                      </span>
                      <Badge variant={getTypeVariant(option.type)}>
                        {option.type.replace('_', ' ')}
                      </Badge>
                      <div className={`px-2 py-1 rounded text-sm font-semibold ${getScoreColor(option.score)}`}>
                        得分: {option.score}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!isEditing && (
                        <>
                          <Button
                            size="sm"
                            variant={isSelected ? 'primary' : 'outline'}
                            onClick={() => onSelect?.(option.id)}
                          >
                            {isSelected ? '✓ 已选择' : '选择'}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditClick(option)}
                          >
                            编辑
                          </Button>
                        </>
                      )}
                      {isEditing && (
                        <>
                          <Button
                            size="sm"
                            onClick={() => handleSaveEdit(option.id)}
                          >
                            保存
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setEditingId(null)}
                          >
                            取消
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Title Display or Edit */}
                  {!isEditing ? (
                    <div className="space-y-2">
                      <p className="text-xl font-bold text-gray-900">
                        {option.full_title}
                      </p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        {option.title_prefix && (
                          <div>
                            <span className="font-medium text-gray-600">前缀:</span>
                            <p className="mt-1 text-gray-800">{option.title_prefix}</p>
                            <CharacterCount
                              count={option.character_count.prefix}
                              min={2}
                              max={6}
                            />
                          </div>
                        )}
                        <div className={option.title_prefix ? '' : 'col-span-2'}>
                          <span className="font-medium text-gray-600">主标题:</span>
                          <p className="mt-1 text-gray-800">{option.title_main}</p>
                          <CharacterCount
                            count={option.character_count.main}
                            min={15}
                            max={30}
                          />
                        </div>
                        {option.title_suffix && (
                          <div>
                            <span className="font-medium text-gray-600">副标题:</span>
                            <p className="mt-1 text-gray-800">{option.title_suffix}</p>
                            <CharacterCount
                              count={option.character_count.suffix}
                              min={4}
                              max={12}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          前缀 (可选, 2-6字符)
                        </label>
                        <input
                          type="text"
                          value={editValues.prefix}
                          onChange={(e) =>
                            setEditValues({ ...editValues, prefix: e.target.value })
                          }
                          className="w-full px-3 py-2 border rounded-md text-sm"
                          placeholder="例: 【最新】"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          主标题 * (15-30字符)
                        </label>
                        <input
                          type="text"
                          value={editValues.main}
                          onChange={(e) =>
                            setEditValues({ ...editValues, main: e.target.value })
                          }
                          className="w-full px-3 py-2 border rounded-md text-sm"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          副标题 (可选, 4-12字符)
                        </label>
                        <input
                          type="text"
                          value={editValues.suffix}
                          onChange={(e) =>
                            setEditValues({ ...editValues, suffix: e.target.value })
                          }
                          className="w-full px-3 py-2 border rounded-md text-sm"
                          placeholder="例: 完整指南"
                        />
                      </div>
                    </div>
                  )}

                  {/* Strengths & Recommendation */}
                  {!isEditing && (
                    <div className="mt-3 pt-3 border-t space-y-2">
                      <div>
                        <span className="text-xs font-semibold text-gray-700">优势:</span>
                        <ul className="mt-1 space-y-1">
                          {option.strengths.map((strength, idx) => (
                            <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                              <span className="text-green-600 mt-0.5">✓</span>
                              {strength}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="text-xs text-gray-600">
                        <span className="font-semibold">推荐理由:</span> {option.recommendation}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Optimization Notes */}
        {!isGenerating && notes.length > 0 && (
          <Alert>
            <AlertDescription>
              <p className="font-semibold mb-2">📝 优化建议</p>
              <ul className="space-y-1 text-sm">
                {notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
