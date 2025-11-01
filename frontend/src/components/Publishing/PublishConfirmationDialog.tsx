/**
 * Publish Confirmation Dialog component.
 * Shows confirmation before publishing an article.
 */

import { Modal, ModalFooter, Button } from '@/components/ui';
import { ProviderType, PublishOptions } from '@/types/publishing';
import { Article } from '@/types/article';

export interface PublishConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  article: Article;
  provider: ProviderType;
  options?: PublishOptions;
  isPublishing?: boolean;
}

export const PublishConfirmationDialog: React.FC<
  PublishConfirmationDialogProps
> = ({
  isOpen,
  onClose,
  onConfirm,
  article,
  provider,
  options,
  isPublishing = false,
}) => {
  const getProviderName = (type: ProviderType): string => {
    const names: Record<ProviderType, string> = {
      playwright: 'Playwright',
      computer_use: 'Computer Use',
      hybrid: 'Hybrid (智能降级)',
    };
    return names[type];
  };

  const estimatedTime = provider === 'playwright' ? '45 秒' : provider === 'computer_use' ? '2 分钟' : '50 秒';
  const estimatedCost = provider === 'playwright' ? '$0.02' : provider === 'computer_use' ? '$0.20' : '$0.04';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="确认发布" size="md">
      <div className="space-y-4">
        {/* Article Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-2">文章信息</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">标题:</span>
              <span className="text-gray-900 font-medium max-w-xs truncate">
                {article.title}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">字数:</span>
              <span className="text-gray-900">
                ~{Math.floor(article.content.length / 2)} 字
              </span>
            </div>
            {article.seo_metadata?.meta_title && (
              <div className="flex justify-between">
                <span className="text-gray-600">Meta Title:</span>
                <span className="text-gray-900 text-xs max-w-xs truncate">
                  {article.seo_metadata.meta_title}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Provider Info */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-2">发布设置</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Provider:</span>
              <span className="text-gray-900 font-medium">
                {getProviderName(provider)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">预计时长:</span>
              <span className="text-gray-900">{estimatedTime}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">预计成本:</span>
              <span className="text-gray-900">{estimatedCost}</span>
            </div>
            {options?.publish_immediately !== false && (
              <div className="flex justify-between">
                <span className="text-gray-600">发布方式:</span>
                <span className="text-green-600 font-medium">立即发布</span>
              </div>
            )}
          </div>
        </div>

        {/* Options */}
        {options && (
          <div className="space-y-2">
            {options.categories && options.categories.length > 0 && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                <span className="text-sm text-gray-600">
                  分类: {options.categories.join(', ')}
                </span>
              </div>
            )}
            {options.tags && options.tags.length > 0 && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
                <span className="text-sm text-gray-600">
                  标签: {options.tags.join(', ')}
                </span>
              </div>
            )}
            {options.seo_optimization && (
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-sm text-green-600 font-medium">
                  已启用 SEO 优化
                </span>
              </div>
            )}
          </div>
        )}

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex gap-2">
            <svg
              className="w-5 h-5 text-yellow-600 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-sm text-yellow-800">
              发布后文章将直接上线到 WordPress 网站。请确认内容无误后再继续。
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <ModalFooter>
        <Button variant="outline" onClick={onClose} disabled={isPublishing}>
          取消
        </Button>
        <Button
          variant="primary"
          onClick={onConfirm}
          disabled={isPublishing}
          isLoading={isPublishing}
        >
          {isPublishing ? '发布中...' : '确认发布'}
        </Button>
      </ModalFooter>
    </Modal>
  );
};
