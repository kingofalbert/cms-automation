/**
 * SEOComparisonCard - Display SEO comparison with AI suggestions
 *
 * Shows side-by-side comparison of original vs suggested SEO metadata
 * with AI reasoning and quality scores
 */

import React from 'react';
import { Card } from '../ui';
import { Badge } from '../ui';
import { TrendingUp, Lightbulb, ArrowRight } from 'lucide-react';
import type { MetaComparison, SEOComparison } from '../../types/api';

export interface SEOComparisonCardProps {
  /** Meta description comparison */
  meta?: MetaComparison;
  /** SEO keywords comparison */
  seo?: SEOComparison;
  /** Whether to show in compact mode */
  compact?: boolean;
}

/**
 * SEOComparisonCard Component
 */
export const SEOComparisonCard: React.FC<SEOComparisonCardProps> = ({
  meta,
  seo,
  compact = false,
}) => {
  if (!meta && !seo) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Meta Description Comparison */}
      {meta && meta.suggested && (
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <Lightbulb className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">
                AI 建议：元描述优化
                {meta.score !== null && meta.score !== undefined && (
                  <Badge variant="info" className="ml-2">
                    评分: {Math.round(meta.score * 100)}
                  </Badge>
                )}
              </h4>

              {/* Original */}
              <div className="mb-3">
                <p className="text-xs text-gray-600 mb-1">
                  原始 ({meta.length_original} 字符)
                </p>
                <div className="p-2 bg-white rounded border border-gray-200">
                  <p className="text-sm text-gray-700">
                    {meta.original || '未设置'}
                  </p>
                </div>
              </div>

              {/* Arrow */}
              <div className="flex justify-center my-2">
                <ArrowRight className="w-4 h-4 text-blue-500" />
              </div>

              {/* Suggested */}
              <div className="mb-3">
                <p className="text-xs text-blue-700 font-medium mb-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  AI 建议 ({meta.length_suggested} 字符)
                </p>
                <div className="p-2 bg-blue-100 rounded border border-blue-300">
                  <p className="text-sm text-gray-900 font-medium">
                    {meta.suggested}
                  </p>
                </div>
              </div>

              {/* Reasoning */}
              {meta.reasoning && (
                <div className="p-2 bg-white/50 rounded border border-blue-100">
                  <p className="text-xs text-gray-600 font-medium mb-1">💡 优化理由：</p>
                  <p className="text-xs text-gray-700">{meta.reasoning}</p>
                </div>
              )}

              {/* Character count validation */}
              {meta.length_suggested && (
                <div className="mt-2">
                  <p className={`text-xs ${
                    meta.length_suggested >= 120 && meta.length_suggested <= 160
                      ? 'text-green-600'
                      : 'text-amber-600'
                  }`}>
                    {meta.length_suggested >= 120 && meta.length_suggested <= 160
                      ? '✓ 长度符合 SEO 最佳实践 (120-160)'
                      : '⚠ 建议长度为 120-160 字符'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* SEO Keywords Comparison */}
      {seo && seo.suggested_keywords && seo.suggested_keywords.length > 0 && (
        <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <Lightbulb className="w-5 h-5 text-green-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">
                AI 建议：SEO 关键词优化
                {seo.score !== null && seo.score !== undefined && (
                  <Badge variant="success" className="ml-2">
                    评分: {Math.round(seo.score * 100)}
                  </Badge>
                )}
              </h4>

              {/* Original Keywords */}
              {seo.original_keywords.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs text-gray-600 mb-1">
                    原始关键词 ({seo.original_keywords.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {seo.original_keywords.map((keyword, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Arrow */}
              <div className="flex justify-center my-2">
                <ArrowRight className="w-4 h-4 text-green-500" />
              </div>

              {/* Suggested Keywords */}
              <div className="mb-3">
                <p className="text-xs text-green-700 font-medium mb-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  AI 建议关键词 ({seo.suggested_keywords.length})
                </p>
                <div className="flex flex-wrap gap-1 p-2 bg-green-100 rounded border border-green-300">
                  {seo.suggested_keywords.map((keyword, idx) => (
                    <Badge key={idx} variant="success" className="text-xs font-medium">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Reasoning */}
              {seo.reasoning && (
                <div className="p-2 bg-white/50 rounded border border-green-100">
                  <p className="text-xs text-gray-600 font-medium mb-1">💡 优化理由：</p>
                  <p className="text-xs text-gray-700">{seo.reasoning}</p>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
