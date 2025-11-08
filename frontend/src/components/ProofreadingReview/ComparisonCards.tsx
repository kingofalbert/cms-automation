/**
 * Comparison Cards
 * Display Meta, SEO, and FAQ comparison data for proofreading review.
 *
 * Performance optimizations:
 * - Individual cards memoized to prevent unnecessary re-renders
 * - ScoreBadge memoized for efficient badge rendering
 */

import { useState, memo } from 'react';
import { ChevronDown, ChevronUp, Sparkles, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type {
  MetaComparison,
  SEOComparison,
  FAQProposal,
} from '@/types/api';

interface ComparisonCardsProps {
  meta: MetaComparison;
  seo: SEOComparison;
  faqProposals: FAQProposal[];
}

export function ComparisonCards({ meta, seo, faqProposals }: ComparisonCardsProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-4 p-6">
      <h2 className="text-lg font-semibold text-gray-900">
        {t('proofreading.comparison.title')}
      </h2>
      <MetaDescriptionCard meta={meta} />
      <SEOKeywordsCard seo={seo} />
      {faqProposals.length > 0 && <FAQProposalsCard proposals={faqProposals} />}
    </div>
  );
}

/**
 * Meta Description Comparison Card
 * Memoized to prevent re-renders when meta data doesn't change
 */
const MetaDescriptionCard = memo(({ meta }: { meta: MetaComparison }) => {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);

  const hasContent = meta.suggested || meta.original;

  if (!hasContent) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          <span className="font-medium text-gray-900">
            {t('proofreading.comparison.meta.title')}
          </span>
          {meta.score !== null && meta.score !== undefined && (
            <ScoreBadge score={meta.score} />
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          {/* Original */}
          <div>
            <div className="mb-1 text-xs font-medium text-gray-500 uppercase">
              {t('proofreading.comparison.meta.original', {
                count: meta.length_original ?? 0,
              })}
            </div>
            <div className="rounded bg-gray-50 p-3 text-sm text-gray-700">
              {meta.original || (
                <span className="text-gray-400 italic">
                  {t('proofreading.comparison.meta.notSet')}
                </span>
              )}
            </div>
          </div>

          {/* Suggested */}
          {meta.suggested && (
            <div>
              <div className="mb-1 text-xs font-medium text-purple-600 uppercase">
                {t('proofreading.comparison.meta.suggested', {
                  count: meta.length_suggested ?? 0,
                })}
              </div>
              <div className="rounded bg-purple-50 p-3 text-sm text-gray-900">
                {meta.suggested}
              </div>
            </div>
          )}

          {/* Reasoning */}
          {meta.reasoning && (
            <div>
              <div className="mb-1 text-xs font-medium text-gray-500 uppercase">
                {t('proofreading.comparison.meta.reasoning')}
              </div>
              <div className="text-sm text-gray-600">{meta.reasoning}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

MetaDescriptionCard.displayName = 'MetaDescriptionCard';

/**
 * SEO Keywords Comparison Card
 * Memoized to prevent re-renders when seo data doesn't change
 */
const SEOKeywordsCard = memo(({ seo }: { seo: SEOComparison }) => {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);

  const hasContent = seo.suggested_keywords || seo.original_keywords.length > 0;

  if (!hasContent) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-500" />
          <span className="font-medium text-gray-900">
            {t('proofreading.comparison.seo.title')}
          </span>
          {seo.score !== null && seo.score !== undefined && (
            <ScoreBadge score={seo.score} />
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          {/* Original Keywords */}
          <div>
            <div className="mb-2 text-xs font-medium text-gray-500 uppercase">
              {t('proofreading.comparison.seo.original', {
                count: seo.original_keywords.length,
              })}
            </div>
            <div className="flex flex-wrap gap-2">
              {seo.original_keywords.length > 0 ? (
                seo.original_keywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="inline-block rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700"
                  >
                    {keyword}
                  </span>
                ))
              ) : (
                <span className="text-sm text-gray-400 italic">
                  {t('proofreading.comparison.seo.notSet')}
                </span>
              )}
            </div>
          </div>

          {/* Suggested Keywords */}
          {seo.suggested_keywords && (
            <div>
              <div className="mb-2 text-xs font-medium text-blue-600 uppercase">
                {t('proofreading.comparison.seo.suggested')}
              </div>
              <div className="rounded bg-blue-50 p-3">
                <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                  {JSON.stringify(seo.suggested_keywords, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Reasoning */}
          {seo.reasoning && (
            <div>
              <div className="mb-1 text-xs font-medium text-gray-500 uppercase">
                {t('proofreading.comparison.seo.reasoning')}
              </div>
              <div className="text-sm text-gray-600">{seo.reasoning}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

SEOKeywordsCard.displayName = 'SEOKeywordsCard';

/**
 * FAQ Schema Proposals Card
 * Memoized to prevent re-renders when proposals don't change
 */
const FAQProposalsCard = memo(({ proposals }: { proposals: FAQProposal[] }) => {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState(0);

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-green-100 text-xs font-bold text-green-700">
            ?
          </div>
          <span className="font-medium text-gray-900">
            {t('proofreading.comparison.faq.title')}
          </span>
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
            {t('proofreading.comparison.faq.count', { count: proposals.length })}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          {/* Proposal Selector */}
          {proposals.length > 1 && (
            <div className="flex gap-2">
              {proposals.map((proposal, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedProposal(idx)}
                  className={cn(
                    'rounded px-3 py-1.5 text-sm font-medium transition-colors',
                    selectedProposal === idx
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {t('proofreading.comparison.faq.proposal', { index: idx + 1 })}
                  {proposal.score !== null && proposal.score !== undefined && (
                    <span className="ml-1 opacity-75">
                      ({Math.round(proposal.score * 100)}%)
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Selected Proposal */}
          <div>
            <div className="mb-2 text-xs font-medium text-gray-500 uppercase">
              {t('proofreading.comparison.faq.schemaType', {
                type: proposals[selectedProposal].schema_type,
              })}
            </div>
            <div className="space-y-3">
              {proposals[selectedProposal].questions.map((qa, idx) => (
                <div key={idx} className="rounded-lg bg-green-50 p-3">
                  <div className="mb-1 text-sm font-medium text-gray-900">
                    {t('proofreading.comparison.faq.question', {
                      index: idx + 1,
                      question: (qa as any).question || JSON.stringify(qa),
                    })}
                  </div>
                  {(qa as any).answer && (
                    <div className="text-sm text-gray-600">
                      {t('proofreading.comparison.faq.answer', {
                        answer: (qa as any).answer,
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

FAQProposalsCard.displayName = 'FAQProposalsCard';

/**
 * Score Badge Component
 * Memoized to prevent re-renders when score doesn't change
 */
const ScoreBadge = memo(({ score }: { score: number }) => {
  const percentage = Math.round(score * 100);
  const color =
    percentage >= 80
      ? 'bg-green-100 text-green-700'
      : percentage >= 60
      ? 'bg-yellow-100 text-yellow-700'
      : 'bg-red-100 text-red-700';

  return (
    <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', color)}>
      {percentage}%
    </span>
  );
});

ScoreBadge.displayName = 'ScoreBadge';
