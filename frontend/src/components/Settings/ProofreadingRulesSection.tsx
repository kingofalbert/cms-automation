/**
 * Proofreading Rules Section component.
 * Manage proofreading rules and rulesets from Settings page.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Badge, Spinner } from '@/components/ui';
import { useTranslation } from 'react-i18next';
import {
  CheckCircle,
  FileText,
  ArrowRight,
  AlertCircle,
  Plus,
  BarChart3,
} from 'lucide-react';
import ruleManagementAPI from '@/services/ruleManagementAPI';
import type { PublishedRuleset, ProofreadingStats } from '@/types/api';

export const ProofreadingRulesSection: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch published rulesets
  const { data: rulesetsData, isLoading: rulesetsLoading } = useQuery({
    queryKey: ['published-rulesets'],
    queryFn: async () => {
      const response = await ruleManagementAPI.getPublishedRulesets();
      return response.data;
    },
  });

  // Fetch statistics
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['proofreading-stats'],
    queryFn: async () => {
      const response = await ruleManagementAPI.getStatistics();
      return response.data as ProofreadingStats;
    },
  });

  const handleGenerateRules = async () => {
    setIsGenerating(true);
    try {
      await ruleManagementAPI.generateRules(0.8);
      // Navigate to rule drafts page after generation
      navigate('/proofreading/rules');
    } catch (error) {
      console.error('Failed to generate rules:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const isLoading = rulesetsLoading || statsLoading;

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

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
          </div>
        )}

        {/* Statistics Cards */}
        {!isLoading && statsData && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary-600" />
                <span className="text-sm font-medium text-gray-600">
                  {t('settings.proofreading.totalRules')}
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-gray-900">
                {statsData.total_rules || 0}
              </p>
            </div>

            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-success-600" />
                <span className="text-sm font-medium text-gray-600">
                  {t('settings.proofreading.publishedRulesets')}
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-gray-900">
                {rulesetsData?.rulesets?.length || 0}
              </p>
            </div>

            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-info-600" />
                <span className="text-sm font-medium text-gray-600">
                  {t('settings.proofreading.appliedCount')}
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-gray-900">
                {statsData.active_rulesets || 0}
              </p>
            </div>
          </div>
        )}

        {/* Published Rulesets */}
        {!isLoading && rulesetsData && (
          <div>
            <h3 className="mb-3 text-sm font-medium text-gray-700">
              {t('settings.proofreading.recentRulesets')}
            </h3>
            {rulesetsData.rulesets && rulesetsData.rulesets.length > 0 ? (
              <div className="space-y-2">
                {rulesetsData.rulesets.slice(0, 3).map((ruleset: PublishedRuleset) => (
                  <div
                    key={ruleset.ruleset_id}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-success-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {ruleset.name || 'Unnamed Ruleset'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {ruleset.total_rules || 0} {t('settings.proofreading.rules')} •{' '}
                          {new Date(ruleset.created_at).toLocaleDateString('zh-CN')}
                        </p>
                      </div>
                    </div>
                    <Badge variant={ruleset.status === 'active' ? 'success' : 'secondary'}>
                      {ruleset.status === 'active'
                        ? t('settings.proofreading.active')
                        : t('settings.proofreading.inactive')}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 py-8">
                <AlertCircle className="mb-2 h-8 w-8 text-gray-400" />
                <p className="mb-1 text-sm font-medium text-gray-600">
                  {t('settings.proofreading.noRulesets')}
                </p>
                <p className="mb-4 text-xs text-gray-500">
                  {t('settings.proofreading.noRulesetsHint')}
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleGenerateRules}
                  isLoading={isGenerating}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  {t('settings.proofreading.generateRules')}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex gap-3 border-t border-gray-200 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/proofreading/test/:new')}
          >
            {t('settings.proofreading.testRules')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/proofreading/stats')}
          >
            {t('settings.proofreading.viewStats')}
          </Button>
        </div>
      </div>
    </Card>
  );
};
