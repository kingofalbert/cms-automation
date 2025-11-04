/**
 * ErrorBoundary Component
 *
 * React Error Boundary that catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the entire app.
 */

import { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Result, Typography } from 'antd';
import { ReloadOutlined, HomeOutlined, BugOutlined } from '@ant-design/icons';
import { logError } from '../utils/errorLogger';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

/**
 * ErrorBoundary class component that catches errors in child components.
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details using centralized error logger
    logError(error, errorInfo, {
      type: 'react_error_boundary',
      errorCount: this.state.errorCount + 1,
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Update state with error details
    this.setState((prevState) => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    const { hasError, error, errorInfo, errorCount } = this.state;
    const { children, fallback, showDetails = import.meta.env.DEV } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return <>{fallback}</>;
      }

      // Default fallback UI
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            backgroundColor: '#f5f5f5',
          }}
        >
          <div style={{ maxWidth: '600px', width: '100%' }}>
            <Result
              status="error"
              title="應用程序出錯"
              subTitle={
                errorCount > 1
                  ? `應用程序遇到了 ${errorCount} 個錯誤。請嘗試重新加載頁面或返回首頁。`
                  : '抱歉，應用程序遇到了意外錯誤。請嘗試重新加載頁面。'
              }
              extra={[
                <Button type="primary" icon={<ReloadOutlined />} onClick={this.handleReload} key="reload">
                  重新加載
                </Button>,
                <Button icon={<HomeOutlined />} onClick={this.handleGoHome} key="home">
                  返回首頁
                </Button>,
                showDetails && (
                  <Button
                    icon={<BugOutlined />}
                    onClick={() => {
                      const details = document.getElementById('error-details');
                      if (details) {
                        details.style.display = details.style.display === 'none' ? 'block' : 'none';
                      }
                    }}
                    key="details"
                  >
                    顯示詳情
                  </Button>
                ),
              ]}
            >
              {showDetails && error && (
                <div
                  id="error-details"
                  style={{
                    display: 'none',
                    textAlign: 'left',
                    marginTop: '24px',
                    padding: '16px',
                    backgroundColor: '#fff',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                  }}
                >
                  <Paragraph>
                    <Text strong>錯誤信息：</Text>
                  </Paragraph>
                  <Paragraph>
                    <Text code>{error.toString()}</Text>
                  </Paragraph>

                  {error.stack && (
                    <>
                      <Paragraph style={{ marginTop: '16px' }}>
                        <Text strong>堆棧跟蹤：</Text>
                      </Paragraph>
                      <Paragraph>
                        <pre
                          style={{
                            fontSize: '12px',
                            backgroundColor: '#f5f5f5',
                            padding: '12px',
                            borderRadius: '4px',
                            overflow: 'auto',
                            maxHeight: '200px',
                          }}
                        >
                          {error.stack}
                        </pre>
                      </Paragraph>
                    </>
                  )}

                  {errorInfo && errorInfo.componentStack && (
                    <>
                      <Paragraph style={{ marginTop: '16px' }}>
                        <Text strong>組件堆棧：</Text>
                      </Paragraph>
                      <Paragraph>
                        <pre
                          style={{
                            fontSize: '12px',
                            backgroundColor: '#f5f5f5',
                            padding: '12px',
                            borderRadius: '4px',
                            overflow: 'auto',
                            maxHeight: '200px',
                          }}
                        >
                          {errorInfo.componentStack}
                        </pre>
                      </Paragraph>
                    </>
                  )}
                </div>
              )}
            </Result>
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
