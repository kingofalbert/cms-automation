/**
 * Proofreading Rules Section component.
 * Manage proofreading rules and rulesets from Settings page.
 *
 * Updated: 2025-12-25 - Added proper "API unavailable" state
 * The statistics/published rulesets APIs are not yet implemented in the backend.
 */

import { useNavigate } from 'react-router-dom';
import { Card, Button } from '@/components/ui';
import { useTranslation } from 'react-i18next';
import {
  ArrowRight,
  AlertCircle,
  Clock,
} from 'lucide-react';

// Feature flag: Set to true when backend API is implemented
const API_AVAILABLE = false;

export const ProofreadingRulesSection: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {t('settings.proofreading.title')}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              {t('settings.proofreading.description')}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/proofreading/rules')}
          >
            {t('settings.proofreading.manageRules')}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        {/* API Not Available Notice */}
        {!API_AVAILABLE && (
          <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-amber-300 bg-amber-50 py-8">
            <Clock className="mb-2 h-8 w-8 text-amber-500" />
            <p className="mb-1 text-sm font-medium text-amber-800">
              統計功能開發中
            </p>
            <p className="mb-4 text-xs text-amber-600 text-center max-w-md">
              校對規則統計和已發布規則集 API 尚在開發中。
              您仍然可以使用規則管理和測試功能。
            </p>
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex gap-3 border-t border-gray-200 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/proofreading/rules')}
          >
            {t('settings.proofreading.manageRules')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/proofreading/test/:new')}
          >
            {t('settings.proofreading.testRules')}
          </Button>
        </div>
      </div>
    </Card>
  );
};
