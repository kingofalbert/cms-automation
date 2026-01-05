/**
 * 404 Not Found Page
 * Displays a user-friendly message when a route is not found.
 */

import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function NotFoundPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50">
      <div className="text-center px-4">
        {/* 404 Illustration */}
        <div className="mb-8">
          <div className="text-9xl font-bold text-gray-200 select-none">404</div>
        </div>

        {/* Message */}
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">
          {t('errors.pageNotFound', '找不到頁面')}
        </h1>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          {t(
            'errors.pageNotFoundDesc',
            '您訪問的頁面不存在或已被移動。請檢查網址是否正確，或返回工作列表。'
          )}
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {t('common.goBack', '返回上一頁')}
          </button>
          <button
            onClick={() => navigate('/worklist')}
            className="px-6 py-2.5 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            {t('common.goToWorklist', '前往工作列表')}
          </button>
        </div>

        {/* Help Text */}
        <p className="mt-8 text-sm text-gray-400">
          {t('errors.needHelp', '如果問題持續，請聯繫系統管理員。')}
        </p>
      </div>
    </div>
  );
}
