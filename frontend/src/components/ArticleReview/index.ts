/**
 * ArticleReview Components - Phase 8 Workflow Simplification
 *
 * Exports:
 * - ArticleReviewModal: Main modal component
 * - ReviewProgressStepper: Progress indicator
 *
 * Phase 8.1: Modal Framework ✅
 * Phase 8.2: Parsing Review Panel ✅
 * Phase 8.3: Proofreading Review Panel ✅
 * Phase 8.4: Publish Preview Panel ✅
 */

export { ArticleReviewModal } from './ArticleReviewModal';
export type { ArticleReviewModalProps } from './ArticleReviewModal';

export { ReviewProgressStepper } from './ReviewProgressStepper';
export type { ReviewProgressStepperProps } from './ReviewProgressStepper';

export { ParsingReviewPanel } from './ParsingReviewPanel';
export type { ParsingReviewPanelProps, ParsingData } from './ParsingReviewPanel';

export { TitleReviewSection } from './TitleReviewSection';
export type { TitleReviewSectionProps } from './TitleReviewSection';

export { SEOTitleSelectionCard } from './SEOTitleSelectionCard';
export type { SEOTitleSelectionCardProps } from './SEOTitleSelectionCard';

export { AuthorReviewSection } from './AuthorReviewSection';
export type { AuthorReviewSectionProps } from './AuthorReviewSection';

export { ImageReviewSection } from './ImageReviewSection';
export type { ImageReviewSectionProps } from './ImageReviewSection';

export { SEOReviewSection } from './SEOReviewSection';
export type { SEOReviewSectionProps } from './SEOReviewSection';

export { FAQReviewSection } from './FAQReviewSection';
export type { FAQReviewSectionProps, FAQ } from './FAQReviewSection';

export { ProofreadingReviewPanel } from './ProofreadingReviewPanel';
export type { ProofreadingReviewPanelProps } from './ProofreadingReviewPanel';

export { DiffViewSection } from './DiffViewSection';
export type { DiffViewSectionProps } from './DiffViewSection';

// Phase 8.4: Real-time Preview Mode
export { ProofreadingPreviewSection } from './ProofreadingPreviewSection';
export type { ProofreadingPreviewSectionProps, WordChange } from './ProofreadingPreviewSection';

export { ProofreadingIssuesSection } from './ProofreadingIssuesSection';
export type { ProofreadingIssuesSectionProps } from './ProofreadingIssuesSection';

export { BatchApprovalControls } from './BatchApprovalControls';
export type { BatchApprovalControlsProps } from './BatchApprovalControls';

// Phase 8.7: WYSIWYG Final Effect Preview
export { FinalPreviewSection } from './FinalPreviewSection';
export type { FinalPreviewSectionProps } from './FinalPreviewSection';

export { PublishPreviewPanel } from './PublishPreviewPanel';
export type { PublishPreviewPanelProps, PublishSettings, PublishResult } from './PublishPreviewPanel';

export { FinalContentPreview } from './FinalContentPreview';
export type { FinalContentPreviewProps } from './FinalContentPreview';

export { PublishSettingsSection } from './PublishSettingsSection';
export type { PublishSettingsSectionProps } from './PublishSettingsSection';

export { PublishConfirmation } from './PublishConfirmation';
export type { PublishConfirmationProps } from './PublishConfirmation';

// Phase 17: WordPress Draft Success Confirmation
export { PublishSuccessConfirmation } from './PublishSuccessConfirmation';
export type { PublishSuccessConfirmationProps } from './PublishSuccessConfirmation';

// Phase 8.3: Content Comparison Components
export { ContentComparisonCard } from './ContentComparisonCard';
export type { ContentComparisonCardProps, ContentSource } from './ContentComparisonCard';

export { KeywordsComparisonCard } from './KeywordsComparisonCard';
export type { KeywordsComparisonCardProps, KeywordSource } from './KeywordsComparisonCard';

export { TagsComparisonCard } from './TagsComparisonCard';
export type { TagsComparisonCardProps, TagSource } from './TagsComparisonCard';

export { SEOComparisonCard } from './SEOComparisonCard';
export type { SEOComparisonCardProps } from './SEOComparisonCard';

// Phase 11: Category Selection with AI Recommendation
export { CategorySelectionCard } from './CategorySelectionCard';
export type { CategorySelectionCardProps, AICategoryRecommendation } from './CategorySelectionCard';

// Phase 11: Excerpt Review (moved from PublishPreviewPanel)
export { ExcerptReviewSection } from './ExcerptReviewSection';
export type { ExcerptReviewSectionProps } from './ExcerptReviewSection';

// Phase 11.5: Enhanced Publish Preview
export { PublishReadinessChecklist, createChecklistItems } from './PublishReadinessChecklist';
export type { PublishReadinessChecklistProps, ChecklistItem } from './PublishReadinessChecklist';

export { MetadataSummaryPanel } from './MetadataSummaryPanel';
export type { MetadataSummaryPanelProps } from './MetadataSummaryPanel';

// Phase 16: Enhanced Publish Preview Components - Re-enabling one by one for testing
export { GoogleSearchPreview } from './GoogleSearchPreview';
export type { GoogleSearchPreviewProps } from './GoogleSearchPreview';

export { ParsingConfirmationSection } from './ParsingConfirmationSection';
export type { ParsingConfirmationSectionProps } from './ParsingConfirmationSection';

export { ProofreadingSummarySection } from './ProofreadingSummarySection';
export type { ProofreadingSummarySectionProps, ProofreadingSummaryStats } from './ProofreadingSummarySection';

export { ArticleImagesList } from './ArticleImagesList';
export type { ArticleImagesListProps, ArticleImage } from './ArticleImagesList';
