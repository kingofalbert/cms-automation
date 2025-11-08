/**
 * Worklist Statistics component.
 * Displays statistics cards for worklist overview.
 */

import { WorklistStatistics as Stats } from '@/types/worklist';
import { Card } from '@/components/ui';
import { FileText, Clock, TrendingUp, BarChart3, Activity, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export interface WorklistStatisticsProps {
  statistics: Stats;
}

export const WorklistStatistics: React.FC<WorklistStatisticsProps> = ({
  statistics,
}) => {
  const { t } = useTranslation();
  const breakdown = statistics.breakdown || {};
  const readyToPublish = breakdown.ready_to_publish ?? 0;
  const published = breakdown.published ?? 0;
  const proofreading = breakdown.proofreading ?? 0;
  const underReview = breakdown.under_review ?? 0;
  const failed = breakdown.failed ?? 0;
  const totalWordCount =
    typeof statistics.total_word_count === 'number'
      ? statistics.total_word_count
      : null;
  const avgQuality =
    typeof statistics.avg_quality_score === 'number'
      ? statistics.avg_quality_score
      : null;

  const avgCycleTimeHours = statistics.avg_time_per_status
    ? Object.values(statistics.avg_time_per_status).reduce((acc, value) => {
        if (typeof value === 'number' && !Number.isNaN(value)) {
          return acc + value;
        }
        if (typeof value === 'string') {
          const parsed = Number(value);
          if (!Number.isNaN(parsed)) {
            return acc + parsed;
          }
        }
        return acc;
      }, 0)
    : null;

  const formatTime = (hours: number | null) => {
    if (hours === null) {
      return t('worklist.statisticsCards.noCycleData');
    }
    if (hours < 24) {
      const formattedHours = Number(hours.toFixed(1));
      return t('worklist.statisticsCards.hours', { hours: formattedHours });
    }
    const days = Math.floor(hours / 24);
    const remainingHours = Number((hours % 24).toFixed(0));
    return t('worklist.statisticsCards.daysHours', { days, hours: remainingHours });
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Items */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">{t('worklist.statistics.total')}</p>
              <p className="text-2xl font-bold text-gray-900">{statistics.total}</p>
              <p className="text-xs text-gray-600 mt-1">
                {totalWordCount !== null
                  ? t('worklist.statisticsCards.wordsLabel', {
                      count: totalWordCount,
                    })
                  : '—'}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </Card>

        {/* Ready to Publish */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.status.ready_to_publish')}
              </p>
              <p className="text-2xl font-bold text-green-600">
                {readyToPublish}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {t('worklist.statisticsCards.readyHint')}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </Card>

        {/* Average Cycle Time */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.statisticsCards.avgCycle')}
              </p>
              <p className="text-lg font-bold text-purple-600">
                {formatTime(avgCycleTimeHours)}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {t('worklist.statisticsCards.cycleHint')}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </Card>

        {/* Average Quality Score */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.statisticsCards.avgQuality')}
              </p>
              <p className="text-2xl font-bold text-yellow-600">
                {avgQuality !== null ? avgQuality.toFixed(1) : '—'}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {t('worklist.statisticsCards.qualityHint')}
              </p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </Card>
        {/* Published */}
        <Card className="p-4 md:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.status.published')}
              </p>
              <p className="text-2xl font-bold text-gray-900">{published}</p>
              <p className="text-xs text-gray-600 mt-1">
                {t('worklist.statisticsCards.publishedHint')}
              </p>
            </div>
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
              <FileText className="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.status.proofreading')}
              </p>
              <p className="text-xl font-semibold text-amber-600">{proofreading}</p>
            </div>
            <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
              <Activity className="w-5 h-5 text-amber-600" />
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.status.under_review')}
              </p>
              <p className="text-xl font-semibold text-blue-600">{underReview}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('worklist.status.failed')}
              </p>
              <p className="text-xl font-semibold text-red-600">{failed}</p>
            </div>
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
          </div>
        </Card>
      </div>
    </>
  );
};
