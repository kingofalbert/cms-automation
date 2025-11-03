/**
 * ErrorFallback Component
 *
 * Lightweight fallback UI for displaying error states in specific components or sections.
 * Use this for more granular error handling within pages or features.
 */

import React from 'react';
import { Alert, Button, Space } from 'antd';
import { ReloadOutlined, CloseCircleOutlined } from '@ant-design/icons';

interface ErrorFallbackProps {
  error?: Error | string;
  title?: string;
  message?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  type?: 'error' | 'warning' | 'info';
}

/**
 * Lightweight error fallback component for section-level errors.
 */
export function ErrorFallback({
  error,
  title = '發生錯誤',
  message,
  onRetry,
  onDismiss,
  showDetails = import.meta.env.DEV,
  type = 'error',
}: ErrorFallbackProps) {
  const errorMessage = typeof error === 'string' ? error : error?.message;
  const errorStack = typeof error !== 'string' ? error?.stack : undefined;

  return (
    <Alert
      type={type}
      message={title}
      description={
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>{message || errorMessage || '發生未知錯誤，請稍後重試。'}</div>

          {showDetails && errorStack && (
            <details style={{ marginTop: '8px' }}>
              <summary style={{ cursor: 'pointer', color: '#1890ff' }}>顯示詳細信息</summary>
              <pre
                style={{
                  marginTop: '8px',
                  padding: '8px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px',
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '200px',
                }}
              >
                {errorStack}
              </pre>
            </details>
          )}

          <Space style={{ marginTop: '8px' }}>
            {onRetry && (
              <Button size="small" type="primary" icon={<ReloadOutlined />} onClick={onRetry}>
                重試
              </Button>
            )}
            {onDismiss && (
              <Button size="small" icon={<CloseCircleOutlined />} onClick={onDismiss}>
                關閉
              </Button>
            )}
          </Space>
        </Space>
      }
      closable={!!onDismiss}
      onClose={onDismiss}
      showIcon
    />
  );
}

/**
 * Compact error display for inline errors.
 */
export function InlineError({ error, onRetry }: { error: Error | string; onRetry?: () => void }) {
  const errorMessage = typeof error === 'string' ? error : error?.message;

  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: '#fff2f0',
        border: '1px solid #ffccc7',
        borderRadius: '4px',
        color: '#cf1322',
      }}
    >
      <Space>
        <CloseCircleOutlined />
        <span>{errorMessage || '發生錯誤'}</span>
        {onRetry && (
          <Button size="small" type="link" onClick={onRetry}>
            重試
          </Button>
        )}
      </Space>
    </div>
  );
}

/**
 * Empty state with error message.
 */
export function EmptyError({
  title = '加載失敗',
  description = '無法加載內容，請重試。',
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        color: '#8c8c8c',
      }}
    >
      <CloseCircleOutlined style={{ fontSize: '48px', color: '#ff4d4f', marginBottom: '16px' }} />
      <h3 style={{ marginBottom: '8px', color: '#262626' }}>{title}</h3>
      <p style={{ marginBottom: '16px' }}>{description}</p>
      {onRetry && (
        <Button type="primary" icon={<ReloadOutlined />} onClick={onRetry}>
          重試
        </Button>
      )}
    </div>
  );
}

export default ErrorFallback;
