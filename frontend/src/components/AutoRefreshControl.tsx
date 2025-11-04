/**
 * AutoRefreshControl Component
 *
 * Toggle control for enabling/disabling automatic data refreshing with polling.
 * Provides visual feedback of refresh status and interval configuration.
 */

import { useEffect, useState } from 'react';
import { Switch, Select, Space, Typography, Badge } from 'antd';
import { ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useQueryPolling } from '../hooks/usePolling';

const { Text } = Typography;

interface AutoRefreshControlProps {
  /**
   * Refetch function from React Query
   */
  onRefresh: () => Promise<unknown>;

  /**
   * Polling interval in milliseconds
   * @default 5000
   */
  interval?: number;

  /**
   * Whether auto-refresh is enabled by default
   * @default true
   */
  defaultEnabled?: boolean;

  /**
   * Label text
   * @default "自動刷新"
   */
  label?: string;

  /**
   * Show interval selector
   * @default true
   */
  showIntervalSelector?: boolean;

  /**
   * Available interval options in milliseconds
   * @default [3000, 5000, 10000, 30000, 60000]
   */
  intervalOptions?: number[];

  /**
   * Callback when polling state changes
   */
  onPollingChange?: (isPolling: boolean) => void;
}

/**
 * Format milliseconds to human-readable text
 */
function formatInterval(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${ms / 1000}秒`;
  return `${ms / 60000}分鐘`;
}

/**
 * Control component for toggling automatic data refresh.
 *
 * @example
 * ```tsx
 * function MyPage() {
 *   const { refetch } = useQuery(['data'], fetchData);
 *
 *   return (
 *     <div>
 *       <AutoRefreshControl
 *         onRefresh={refetch}
 *         interval={5000}
 *         label="自動更新任務"
 *       />
 *       <DataTable />
 *     </div>
 *   );
 * }
 * ```
 */
export function AutoRefreshControl({
  onRefresh,
  interval: initialInterval = 5000,
  defaultEnabled = true,
  label = '自動刷新',
  showIntervalSelector = true,
  intervalOptions = [3000, 5000, 10000, 30000, 60000],
  onPollingChange,
}: AutoRefreshControlProps) {
  const [interval, setInterval] = useState(initialInterval);

  const { isPolling, toggle, errorCount, resetErrors } = useQueryPolling(onRefresh, {
    interval,
    enabled: defaultEnabled,
    pollWhenHidden: false,
    maxErrors: 3,
    onMaxErrors: (count) => {
      console.error(`Auto-refresh stopped after ${count} consecutive errors`);
    },
  });

  useEffect(() => {
    onPollingChange?.(isPolling);
  }, [isPolling, onPollingChange]);

  return (
    <Space align="center" size="middle">
      {/* Status Badge */}
      <Badge status={isPolling ? 'processing' : 'default'} />

      {/* Toggle Switch */}
      <Space size="small">
        <ReloadOutlined spin={isPolling} style={{ color: isPolling ? '#1890ff' : '#8c8c8c' }} />
        <Text strong={isPolling}>{label}</Text>
        <Switch
          checked={isPolling}
          onChange={() => {
            toggle();
            if (errorCount > 0) resetErrors();
          }}
          size="small"
        />
      </Space>

      {/* Interval Selector */}
      {showIntervalSelector && (
        <Space size="small">
          <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
          <Select
            value={interval}
            onChange={setInterval}
            size="small"
            style={{ width: 100 }}
            disabled={!isPolling}
          >
            {intervalOptions.map((ms) => (
              <Select.Option key={ms} value={ms}>
                {formatInterval(ms)}
              </Select.Option>
            ))}
          </Select>
        </Space>
      )}

      {/* Error Indicator */}
      {errorCount > 0 && (
        <Text type="warning" style={{ fontSize: '12px' }}>
          ({errorCount} 次錯誤)
        </Text>
      )}
    </Space>
  );
}

/**
 * Compact version of AutoRefreshControl for toolbars.
 */
export function AutoRefreshToggle({
  onRefresh,
  interval = 5000,
  defaultEnabled = true,
}: Pick<AutoRefreshControlProps, 'onRefresh' | 'interval' | 'defaultEnabled'>) {
  const { isPolling, toggle } = useQueryPolling(onRefresh, {
    interval,
    enabled: defaultEnabled,
    pollWhenHidden: false,
  });

  return (
    <Space size="small">
      <ReloadOutlined spin={isPolling} style={{ color: isPolling ? '#1890ff' : '#8c8c8c' }} />
      <Switch checked={isPolling} onChange={toggle} size="small" />
    </Space>
  );
}

export default AutoRefreshControl;
