/**
 * FAQReviewSection - AI-Powered FAQ Review and Generation
 *
 * Phase 9.2: AI FAQ Generation for Search Engine Optimization
 * Phase 13: FAQ v2.2 - Applicability Assessment & YMYL Compliance
 * - AI-generated FAQs optimized for AI search engines (Google SGE, Perplexity, etc.)
 * - Deep semantic analysis of article content
 * - Applicability assessment (some articles don't need FAQ)
 * - YMYL safety warnings for health content
 * - Questions based on user search intent and common queries
 * - Rich structured data for FAQ schema markup
 */

import React, { useState } from 'react';
import { Button } from '../ui';
import { Textarea } from '../ui/Textarea';
import { Input } from '../ui/Input';
import { Badge } from '../ui/badge';
import {
  HelpCircle,
  Plus,
  Trash2,
  Sparkles,
  Check,
  Copy,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Loader2,
  Brain,
  Search,
  Target,
  XCircle,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';

export interface FAQ {
  question: string;
  answer: string;
}

export interface AIFAQSuggestion {
  question: string;
  answer: string;
  question_type?: string;
  search_intent?: string;
  keywords_covered?: string[];
  confidence?: number;
  safety_warning?: boolean;  // YMYL safety warning flag (v2.2)
}

/**
 * FAQ v2.2 Assessment result
 */
export interface FAQAssessment {
  is_applicable: boolean;
  reason: string;
  target_pain_points?: string[];
}

export interface FAQReviewSectionProps {
  /** Article ID for API calls */
  articleId?: number | null;
  /** Current FAQ items (user accepted) */
  faqs: FAQ[];
  /** AI-generated FAQ suggestions */
  aiSuggestions?: AIFAQSuggestion[];
  /** Whether AI generation is in progress */
  isGenerating?: boolean;
  /** Callback when FAQs change */
  onFaqsChange: (faqs: FAQ[]) => void;
  /** Callback to trigger AI FAQ generation */
  onGenerateFaqs?: () => Promise<void>;
  /** Error message */
  error?: string | null;
  /** FAQ v2.2: Whether FAQ is applicable for this article */
  faqApplicable?: boolean | null;
  /** FAQ v2.2: Assessment details */
  faqAssessment?: FAQAssessment | null;
}

/**
 * Get question type label in Chinese
 */
const getQuestionTypeLabel = (type?: string): string => {
  const types: Record<string, string> = {
    factual: '事實型',
    how_to: '操作型',
    comparison: '比較型',
    definition: '定義型',
    why: '原因型',
    what_if: '假設型',
  };
  return types[type || ''] || type || '';
};

/**
 * Get search intent label in Chinese
 */
const getSearchIntentLabel = (intent?: string): string => {
  const intents: Record<string, string> = {
    informational: '資訊查詢',
    navigational: '導航型',
    transactional: '交易型',
    commercial: '商業調查',
  };
  return intents[intent || ''] || intent || '';
};

/**
 * FAQReviewSection Component
 */
export const FAQReviewSection: React.FC<FAQReviewSectionProps> = ({
  articleId,
  faqs,
  aiSuggestions = [],
  isGenerating = false,
  onFaqsChange,
  onGenerateFaqs,
  error,
  faqApplicable,
  faqAssessment,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [acceptedIndices, setAcceptedIndices] = useState<Set<number>>(new Set());
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editQuestion, setEditQuestion] = useState('');
  const [editAnswer, setEditAnswer] = useState('');

  // Handle add empty FAQ
  const handleAddFaq = () => {
    onFaqsChange([...faqs, { question: '', answer: '' }]);
  };

  // Handle remove FAQ
  const handleRemoveFaq = (index: number) => {
    const newFaqs = [...faqs];
    newFaqs.splice(index, 1);
    onFaqsChange(newFaqs);
  };

  // Handle update FAQ field
  const handleUpdateFaq = (index: number, field: 'question' | 'answer', value: string) => {
    const newFaqs = [...faqs];
    newFaqs[index] = { ...newFaqs[index], [field]: value };
    onFaqsChange(newFaqs);
  };

  // Accept AI suggestion
  const handleAcceptSuggestion = (suggestion: AIFAQSuggestion, index: number) => {
    onFaqsChange([...faqs, { question: suggestion.question, answer: suggestion.answer }]);
    setAcceptedIndices(new Set([...acceptedIndices, index]));
  };

  // Accept all AI suggestions
  const handleAcceptAll = () => {
    const newFaqs = [
      ...faqs,
      ...aiSuggestions
        .filter((_, i) => !acceptedIndices.has(i))
        .map(s => ({ question: s.question, answer: s.answer })),
    ];
    onFaqsChange(newFaqs);
    setAcceptedIndices(new Set(aiSuggestions.map((_, i) => i)));
  };

  // Copy to clipboard
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // Start editing a suggestion
  const handleStartEdit = (index: number, suggestion: AIFAQSuggestion) => {
    setEditingIndex(index);
    setEditQuestion(suggestion.question);
    setEditAnswer(suggestion.answer);
  };

  // Save edited suggestion
  const handleSaveEdit = (index: number) => {
    onFaqsChange([...faqs, { question: editQuestion, answer: editAnswer }]);
    setAcceptedIndices(new Set([...acceptedIndices, index]));
    setEditingIndex(null);
    setEditQuestion('');
    setEditAnswer('');
  };

  const hasAiSuggestions = aiSuggestions.length > 0;
  const unacceptedSuggestions = aiSuggestions.filter((_, i) => !acceptedIndices.has(i));

  // FAQ v2.2: Check applicability
  const isApplicable = faqApplicable !== false; // null or true means applicable
  const hasSafetyWarnings = aiSuggestions.some(s => s.safety_warning);

  return (
    <div className="space-y-4" data-testid="faq-review-section">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-slate-600" />
          <h3 className="text-lg font-semibold text-gray-900">FAQ 建議</h3>
          {/* FAQ v2.2: Applicability Status */}
          {faqApplicable === false && (
            <Badge variant="outline" className="text-xs bg-gray-100 text-gray-600">
              <XCircle className="w-3 h-3 mr-1" />
              不適用
            </Badge>
          )}
          {faqApplicable === true && (
            <Badge variant="success" className="text-xs">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              適用
            </Badge>
          )}
          {hasSafetyWarnings && (
            <Badge variant="warning" className="text-xs bg-amber-100 text-amber-700">
              <ShieldAlert className="w-3 h-3 mr-1" />
              健康安全
            </Badge>
          )}
          {faqs.length > 0 && (
            <Badge variant="success" className="text-xs">
              {faqs.length} 個
            </Badge>
          )}
          {hasAiSuggestions && unacceptedSuggestions.length > 0 && (
            <Badge variant="default" className="text-xs bg-purple-100 text-purple-700">
              <Sparkles className="w-3 h-3 mr-1" />
              {unacceptedSuggestions.length} AI 建議
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleAddFaq(); }}>
            <Plus className="w-4 h-4 mr-1" />
            添加
          </Button>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-500" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          {/* FAQ v2.2: Not Applicable Banner */}
          {faqApplicable === false && faqAssessment && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <XCircle className="w-5 h-5 text-gray-500" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-700">此文章不適用 FAQ</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {faqAssessment.reason}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    新聞報導、時事評論等類型文章通常不需要 FAQ 區塊。
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AI FAQ Info Banner - Show only when FAQs are loaded */}
          {isApplicable && hasAiSuggestions && (
            <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-purple-900">AI 智能 FAQ 已生成</h4>
                  <p className="text-sm text-purple-700 mt-1">
                    以下 FAQ 已基於文章內容自動生成，優化 AI 搜索引擎曝光。
                    請審核並選擇要使用的 FAQ。
                  </p>
                  {unacceptedSuggestions.length > 0 && (
                    <div className="flex items-center gap-2 mt-3">
                      <Button
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAcceptAll();
                        }}
                        className="border-purple-300 text-purple-700 hover:bg-purple-100"
                      >
                        <Check className="w-4 h-4 mr-1" />
                        接受全部 ({unacceptedSuggestions.length})
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* AI Suggestions */}
          {hasAiSuggestions && unacceptedSuggestions.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-purple-700">
                <Sparkles className="w-4 h-4" />
                AI 生成的 FAQ 建議
              </div>
              {aiSuggestions.map((suggestion, index) => {
                if (acceptedIndices.has(index)) return null;

                const isEditing = editingIndex === index;

                return (
                  <div
                    key={`ai-${index}`}
                    className="p-4 border-2 border-purple-200 bg-purple-50/50 rounded-lg space-y-3 hover:border-purple-300 transition-colors"
                  >
                    {isEditing ? (
                      // Editing mode
                      <>
                        <div className="space-y-2">
                          <label className="block text-xs font-medium text-gray-600">問題</label>
                          <Input
                            type="text"
                            value={editQuestion}
                            onChange={(e) => setEditQuestion(e.target.value)}
                            className="w-full"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="block text-xs font-medium text-gray-600">回答</label>
                          <Textarea
                            value={editAnswer}
                            onChange={(e) => setEditAnswer(e.target.value)}
                            rows={3}
                            className="w-full"
                          />
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingIndex(null)}
                          >
                            取消
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleSaveEdit(index)}
                            className="bg-purple-500 hover:bg-purple-600"
                          >
                            保存並使用
                          </Button>
                        </div>
                      </>
                    ) : (
                      // View mode
                      <>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-purple-700">
                              Q{index + 1}
                            </span>
                            {suggestion.question_type && (
                              <Badge variant="outline" className="text-xs bg-white">
                                <Target className="w-3 h-3 mr-1" />
                                {getQuestionTypeLabel(suggestion.question_type)}
                              </Badge>
                            )}
                            {suggestion.search_intent && (
                              <Badge variant="outline" className="text-xs bg-white">
                                <Search className="w-3 h-3 mr-1" />
                                {getSearchIntentLabel(suggestion.search_intent)}
                              </Badge>
                            )}
                            {suggestion.confidence && suggestion.confidence > 0.8 && (
                              <Badge variant="success" className="text-xs">
                                高相關
                              </Badge>
                            )}
                            {suggestion.safety_warning && (
                              <Badge variant="warning" className="text-xs bg-amber-100 text-amber-700 border-amber-300">
                                <ShieldAlert className="w-3 h-3 mr-1" />
                                健康安全提示
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleCopy(`${suggestion.question}\n${suggestion.answer}`)}
                              className="p-1.5 hover:bg-purple-100 rounded"
                              title="複製"
                            >
                              <Copy className="w-3.5 h-3.5 text-purple-500" />
                            </button>
                          </div>
                        </div>

                        <div className="pl-6">
                          <p className="text-sm font-medium text-gray-900 mb-2">
                            {suggestion.question}
                          </p>
                          <p className="text-sm text-gray-600 bg-white p-2 rounded border border-purple-100">
                            {suggestion.answer}
                          </p>
                        </div>

                        {suggestion.keywords_covered && suggestion.keywords_covered.length > 0 && (
                          <div className="pl-6 flex flex-wrap gap-1">
                            <span className="text-xs text-gray-500">關鍵詞:</span>
                            {suggestion.keywords_covered.slice(0, 5).map((kw, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs bg-white">
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        )}

                        <div className="flex justify-end gap-2 pt-2 border-t border-purple-100">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStartEdit(index, suggestion)}
                            className="text-purple-600 border-purple-300"
                          >
                            編輯後使用
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleAcceptSuggestion(suggestion, index)}
                            className="bg-purple-500 hover:bg-purple-600 text-white"
                          >
                            <Check className="w-4 h-4 mr-1" />
                            使用此 FAQ
                          </Button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Accepted/User FAQs */}
          {faqs.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Check className="w-4 h-4 text-green-500" />
                已選定的 FAQ ({faqs.length})
              </div>
              {faqs.map((faq, index) => (
                <div
                  key={index}
                  className="p-4 border border-gray-200 rounded-lg space-y-3 bg-white"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      FAQ #{index + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFaq(index)}
                      className="text-red-600 hover:text-red-700 p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-xs font-medium text-gray-600">問題</label>
                    <Input
                      type="text"
                      value={faq.question}
                      onChange={(e) => handleUpdateFaq(index, 'question', e.target.value)}
                      placeholder="輸入問題"
                      className="w-full"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-xs font-medium text-gray-600">回答</label>
                    <Textarea
                      value={faq.answer}
                      onChange={(e) => handleUpdateFaq(index, 'answer', e.target.value)}
                      placeholder="輸入回答"
                      rows={3}
                      className="w-full"
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : !hasAiSuggestions ? (
            <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
              <HelpCircle className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500 mb-3">
                {isGenerating ? '正在載入 FAQ...' : 'FAQ 將在文章解析時自動生成'}
              </p>
              {isGenerating && (
                <Loader2 className="w-6 h-6 mx-auto text-purple-500 animate-spin" />
              )}
              {!isGenerating && (
                <Button variant="outline" size="sm" onClick={handleAddFaq}>
                  <Plus className="w-4 h-4 mr-1" />
                  手動添加 FAQ
                </Button>
              )}
            </div>
          ) : null}

          {/* FAQ guidelines - v2.2 */}
          {(faqs.length > 0 || hasAiSuggestions) && isApplicable && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
              <strong>FAQ v2.2 優化建議：</strong>
              <ul className="mt-1 ml-4 list-disc space-y-1">
                <li>建議 3-5 個精準的專業 FAQ，針對讀者真實痛點</li>
                <li>問題應簡潔明了，模擬用戶真實搜索意圖</li>
                <li>回答應詳細專業，建議 50-150 字</li>
                <li>健康類文章請注意標註「健康安全提示」標籤</li>
                <li>FAQ 將自動加入文章內容，優化 AI 搜索曝光</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

FAQReviewSection.displayName = 'FAQReviewSection';
