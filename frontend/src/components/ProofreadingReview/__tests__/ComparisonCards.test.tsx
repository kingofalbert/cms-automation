/**
 * Unit tests for ComparisonCards component
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ComparisonCards } from '../ComparisonCards';
import type { MetaComparison, SEOComparison, FAQProposal } from '@/types/api';

describe('ComparisonCards', () => {
  const mockMeta: MetaComparison = {
    original: 'Original meta description',
    suggested: 'Suggested meta description',
    reasoning: 'This is better for SEO',
    score: 0.85,
    length_original: 25,
    length_suggested: 28,
  };

  const mockSEO: SEOComparison = {
    original_keywords: ['keyword1', 'keyword2'],
    suggested_keywords: ['seo1', 'seo2'],
    reasoning: 'Better keyword targeting',
    score: 0.9,
  };

  const mockFAQ: FAQProposal[] = [
    {
      questions: [
        { question: 'What is this?', answer: 'This is a test.' },
      ],
      schema_type: 'FAQPage',
      score: 0.95,
    },
  ];

  it('should render main heading', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={mockFAQ} />
    );
    expect(screen.getByText('AI 优化建议')).toBeInTheDocument();
  });

  it('should render Meta Description card', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={[]} />
    );
    expect(screen.getByText('Meta Description')).toBeInTheDocument();
  });

  it('should expand Meta card on click', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={[]} />
    );

    const metaButton = screen.getByText('Meta Description');
    fireEvent.click(metaButton);

    // Check if original content is shown
    expect(screen.getByText('Original meta description')).toBeInTheDocument();
  });

  it('should render SEO Keywords card', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={[]} />
    );
    // Use regex to match Chinese or English
    expect(screen.getByText(/SEO 关键词|SEO Keywords/)).toBeInTheDocument();
  });

  it('should render FAQ Proposals card when proposals exist', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={mockFAQ} />
    );
    // Use regex to match Chinese or English
    expect(screen.getByText(/FAQ Schema 提案|FAQ Schema Proposals/)).toBeInTheDocument();
  });

  it('should not render FAQ card when no proposals', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={[]} />
    );
    // Use regex to match Chinese or English
    expect(screen.queryByText(/FAQ Schema 提案|FAQ Schema Proposals/)).not.toBeInTheDocument();
  });

  it('should display score badges correctly', () => {
    render(
      <ComparisonCards meta={mockMeta} seo={mockSEO} faqProposals={[]} />
    );

    // Meta score should be 85%
    expect(screen.getByText('85%')).toBeInTheDocument();
    // SEO score should be 90%
    expect(screen.getByText('90%')).toBeInTheDocument();
  });
});
