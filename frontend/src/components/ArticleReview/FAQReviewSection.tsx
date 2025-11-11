/**
 * FAQReviewSection - FAQ suggestions review
 *
 * Phase 8.2: Parsing Review Panel
 * - Display AI-generated FAQ suggestions
 * - Allow editing FAQ items
 * - Add/remove FAQ items
 */

import React from 'react';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Textarea';
import { Input } from '../ui/Input';
import { HelpCircle, Plus, Trash2 } from 'lucide-react';

export interface FAQ {
  question: string;
  answer: string;
}

export interface FAQReviewSectionProps {
  /** FAQ items */
  faqs: FAQ[];
  /** Callback when FAQs change */
  onFaqsChange: (faqs: FAQ[]) => void;
}

/**
 * FAQReviewSection Component
 */
export const FAQReviewSection: React.FC<FAQReviewSectionProps> = ({
  faqs,
  onFaqsChange,
}) => {
  const handleAddFaq = () => {
    onFaqsChange([...faqs, { question: '', answer: '' }]);
  };

  const handleRemoveFaq = (index: number) => {
    const newFaqs = [...faqs];
    newFaqs.splice(index, 1);
    onFaqsChange(newFaqs);
  };

  const handleUpdateFaq = (index: number, field: 'question' | 'answer', value: string) => {
    const newFaqs = [...faqs];
    newFaqs[index] = { ...newFaqs[index], [field]: value };
    onFaqsChange(newFaqs);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <HelpCircle className="w-5 h-5" />
          FAQ 建议
        </h3>
        <Button variant="outline" size="sm" onClick={handleAddFaq}>
          <Plus className="w-4 h-4 mr-1" />
          添加
        </Button>
      </div>

      {/* FAQ Items */}
      {faqs.length > 0 ? (
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="p-4 border border-gray-200 rounded-lg space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  FAQ #{index + 1}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveFaq(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-medium text-gray-600">
                  问题
                </label>
                <Input
                  type="text"
                  value={faq.question}
                  onChange={(e) => handleUpdateFaq(index, 'question', e.target.value)}
                  placeholder="输入问题"
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-medium text-gray-600">
                  回答
                </label>
                <Textarea
                  value={faq.answer}
                  onChange={(e) => handleUpdateFaq(index, 'answer', e.target.value)}
                  placeholder="输入回答"
                  rows={3}
                  className="w-full"
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
          <HelpCircle className="w-12 h-12 mx-auto text-gray-400 mb-2" />
          <p className="text-sm text-gray-500 mb-3">暂无 FAQ 建议</p>
          <Button variant="outline" size="sm" onClick={handleAddFaq}>
            <Plus className="w-4 h-4 mr-1" />
            添加第一个 FAQ
          </Button>
        </div>
      )}

      {/* FAQ guidelines */}
      {faqs.length > 0 && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
          <strong>FAQ 建议：</strong>
          <ul className="mt-1 ml-4 list-disc space-y-1">
            <li>问题应简洁明了，直击用户痛点</li>
            <li>回答应详细且实用，提供具体解决方案</li>
            <li>建议添加 3-5 个高质量 FAQ</li>
          </ul>
        </div>
      )}
    </div>
  );
};

FAQReviewSection.displayName = 'FAQReviewSection';
