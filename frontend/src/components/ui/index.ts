/**
 * Base UI components export.
 */

// Shadcn-style UI components
export { Button } from './button';
export type { ButtonProps } from './button';

export { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription } from './card';

export { Badge } from './badge';
export type { BadgeProps } from './badge';

export { Alert, AlertTitle, AlertDescription } from './alert';

export { Input } from './Input';
export type { InputProps } from './Input';

export { Spinner } from './Spinner';
export type { SpinnerProps } from './Spinner';

export { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
export type { TabsProps, TabsListProps, TabsTriggerProps, TabsContentProps } from './Tabs';

export { Modal, ModalFooter } from './Modal';
export type { ModalProps, ModalFooterProps } from './Modal';

export { Drawer, DrawerFooter } from './Drawer';
export type { DrawerProps, DrawerFooterProps } from './Drawer';

export { Textarea } from './Textarea';
export type { TextareaProps } from './Textarea';

export { Select } from './Select';
export type { SelectProps, SelectOption } from './Select';

export { LazyImage } from './LazyImage';
export type { LazyImageProps } from './LazyImage';

export { VirtualList } from './VirtualList';
export type { VirtualListProps } from './VirtualList';

export { ArticleCard } from './ArticleCard';
export type { ArticleCardProps } from './ArticleCard';

export { ArticleList } from './ArticleList';
export type { ArticleListProps } from './ArticleList';

export { Accordion, AccordionItem } from './Accordion';
export type { AccordionProps, AccordionItemProps } from './Accordion';

export { Toast, ToastContainer } from './Toast';
export type { ToastProps, ToastContainerProps, ToastType } from './Toast';

export {
  Skeleton,
  SkeletonCard,
  SkeletonTableRow,
  SkeletonStatsCard,
  SkeletonIssueList,
  SkeletonArticleContent,
  SkeletonIssueDetail,
  SkeletonProofreadingPage,
} from './skeleton';
export type { SkeletonProps } from './skeleton';

export { EmptyState } from './EmptyState';
export type { EmptyStateProps } from './EmptyState';

export { StatusBadge, getStatusColor, getStatusConfig } from './StatusBadge';
export type { StatusBadgeProps, WorkflowStatus } from './StatusBadge';

export {
  KeyboardShortcutsHint,
  Kbd,
  PROOFREADING_SHORTCUTS,
  PROOFREADING_SHORTCUTS_COMPACT,
} from './KeyboardShortcutsHint';
export type { KeyboardShortcutsHintProps, KeyboardShortcut } from './KeyboardShortcutsHint';
