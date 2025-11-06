/**
 * Phase 1 Header Component
 *
 * Unified header for Phase 1 with:
 * - App name and logo
 * - Language switcher
 * - Settings button
 */

import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from '../common/LanguageSwitcher';
import { Settings, FileText } from 'lucide-react';

export const Phase1Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const isSettingsPage = location.pathname === '/settings';
  const isWorklistPage = location.pathname === '/' || location.pathname === '/worklist';

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Left: App Name and Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-md">
            <FileText className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {t('common.appName')}
            </h1>
          </div>
        </div>

        {/* Right: Language Switcher and Settings */}
        <div className="flex items-center gap-3">
          <LanguageSwitcher />

          {!isSettingsPage && (
            <button
              onClick={() => navigate('/settings')}
              className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={t('common.settings')}
            >
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">{t('common.settings')}</span>
            </button>
          )}

          {isSettingsPage && !isWorklistPage && (
            <button
              onClick={() => navigate('/worklist')}
              className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={t('worklist.title')}
            >
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">{t('worklist.title')}</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Phase1Header;
