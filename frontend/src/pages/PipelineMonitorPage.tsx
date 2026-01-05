import React, { useState, useEffect, useCallback } from 'react';

interface LocalStats {
  total_local: number;
  categories: Record<string, number>;
  last_update?: string;
}

interface PipelineStatus {
  status: 'running' | 'stopped';
  phase: string;
  phase_description: string;
  pid: number | null;
  pids: Record<string, number | null>;
  runtime: string | null;
  log_file: string | null;
  database: {
    scraped: number;
    parsed: number;
    ready: number;
    total: number;
  };
  local: LocalStats;
  completion_rate: number;
  timestamp: string;
}

interface LogsResponse {
  logs: string[];
  log_file: string | null;
  timestamp: string;
}

interface HistoryItem {
  filename: string;
  type: string;
  start_time: string;
  size_kb: number;
}

const MONITOR_API_BASE = 'http://localhost:5050/api/pipeline';

const PipelineMonitorPage: React.FC = () => {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${MONITOR_API_BASE}/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError('無法連接到監控 API。請確保 pipeline_monitor_api.py 正在運行。');
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const response = await fetch(`${MONITOR_API_BASE}/logs?lines=30`);
      if (!response.ok) throw new Error('Failed to fetch logs');
      const data: LogsResponse = await response.json();
      setLogs(data.logs);
    } catch (err) {
      // 靜默處理日誌錯誤
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(`${MONITOR_API_BASE}/history`);
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setHistory(data.history);
    } catch (err) {
      // 靜默處理歷史錯誤
    }
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchStatus(), fetchLogs(), fetchHistory()]);
    setLoading(false);
  }, [fetchStatus, fetchLogs, fetchHistory]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 5000); // 每 5 秒刷新
    return () => clearInterval(interval);
  }, [autoRefresh, fetchStatus, fetchLogs]);

  const handleStart = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(`${MONITOR_API_BASE}/start`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchAll();
      } else {
        alert(data.message);
      }
    } catch (err) {
      alert('啟動失敗');
    }
    setActionLoading(false);
  };

  const handleStop = async () => {
    if (!confirm('確定要停止 Pipeline 嗎？')) return;
    setActionLoading(true);
    try {
      const response = await fetch(`${MONITOR_API_BASE}/stop`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchAll();
      } else {
        alert(data.message);
      }
    } catch (err) {
      alert('停止失敗');
    }
    setActionLoading(false);
  };

  const formatNumber = (num: number) => num.toLocaleString();

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'scraping': return '#2196F3';
      case 'importing': return '#9C27B0';
      case 'parsing': return '#FF9800';
      case 'embedding': return '#4CAF50';
      default: return '#666';
    }
  };

  if (error) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Pipeline 監控</h1>
        <div style={styles.errorCard}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔌</div>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>監控服務暫時無法連接</h3>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            Pipeline 監控服務目前未運行。如需查看 Pipeline 狀態，請聯繫系統管理員啟動服務。
          </p>
          <button onClick={fetchAll} style={styles.retryButton}>
            重試連接
          </button>
          <details style={{ marginTop: '1.5rem', textAlign: 'left' }}>
            <summary style={{ cursor: 'pointer', color: '#666', fontSize: '0.85rem' }}>
              技術詳情 (管理員用)
            </summary>
            <pre style={{ ...styles.codeBlock, marginTop: '0.5rem', fontSize: '0.8rem' }}>
              cd backend && source venv/bin/activate && python scripts/pipeline_monitor_api.py
            </pre>
          </details>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Pipeline 監控</h1>
        <div style={styles.headerActions}>
          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自動刷新 (5秒)
          </label>
          <button onClick={fetchAll} style={styles.refreshButton} disabled={loading}>
            刷新
          </button>
        </div>
      </div>

      {/* 狀態卡片 */}
      <div style={styles.statusSection}>
        <div style={{
          ...styles.statusCard,
          borderLeft: `4px solid ${status?.status === 'running' ? getPhaseColor(status?.phase || '') : '#f44336'}`
        }}>
          <div style={styles.statusHeader}>
            <span style={{
              ...styles.statusBadge,
              backgroundColor: status?.status === 'running' ? getPhaseColor(status?.phase || '') : '#f44336'
            }}>
              {status?.status === 'running' ? status?.phase_description : '已停止'}
            </span>
            {status?.pid && <span style={styles.pidText}>PID: {status.pid}</span>}
          </div>
          {status?.runtime && (
            <p style={styles.runtime}>運行時間: {status.runtime}</p>
          )}
          <div style={styles.actionButtons}>
            {status?.status !== 'running' ? (
              <button
                onClick={handleStart}
                disabled={actionLoading}
                style={styles.startButton}
              >
                {actionLoading ? '啟動中...' : '啟動 Pipeline'}
              </button>
            ) : (
              <button
                onClick={handleStop}
                disabled={actionLoading}
                style={styles.stopButton}
              >
                {actionLoading ? '停止中...' : '停止 Pipeline'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 本地抓取進度（階段 1） */}
      {status?.local && status.local.total_local > 0 && (
        <div style={styles.localSection}>
          <h3 style={styles.sectionTitle}>
            本地抓取進度
            <span style={styles.localBadge}>階段 1</span>
          </h3>
          <div style={styles.localStats}>
            <div style={styles.localTotal}>
              <span style={styles.localNumber}>{formatNumber(status.local.total_local)}</span>
              <span style={styles.localLabel}>篇文章已抓取到本地</span>
            </div>
            <div style={styles.categoryList}>
              {Object.entries(status.local.categories || {}).map(([cat, count]) => (
                <div key={cat} style={styles.categoryItem}>
                  <span>{cat}</span>
                  <span style={styles.categoryCount}>{formatNumber(count as number)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 數據庫統計卡片 */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statIcon}>📥</div>
          <div style={styles.statContent}>
            <div style={styles.statValue}>{formatNumber(status?.database.scraped || 0)}</div>
            <div style={styles.statLabel}>已抓取 (待解析)</div>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statIcon}>🔄</div>
          <div style={styles.statContent}>
            <div style={styles.statValue}>{formatNumber(status?.database.parsed || 0)}</div>
            <div style={styles.statLabel}>已解析 (待向量化)</div>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statIcon}>✅</div>
          <div style={styles.statContent}>
            <div style={styles.statValue}>{formatNumber(status?.database.ready || 0)}</div>
            <div style={styles.statLabel}>完全處理完成</div>
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statIcon}>📚</div>
          <div style={styles.statContent}>
            <div style={styles.statValue}>{formatNumber(status?.database.total || 0)}</div>
            <div style={styles.statLabel}>數據庫總計</div>
          </div>
        </div>
      </div>

      {/* 進度條 */}
      <div style={styles.progressSection}>
        <div style={styles.progressHeader}>
          <span>處理進度（數據庫）</span>
          <span style={styles.progressPercent}>{status?.completion_rate || 0}%</span>
        </div>
        <div style={styles.progressBar}>
          <div
            style={{
              ...styles.progressFill,
              width: `${status?.completion_rate || 0}%`
            }}
          />
        </div>
        <div style={styles.progressLegend}>
          <span>已完成: {formatNumber(status?.database.ready || 0)} / {formatNumber(status?.database.total || 0)}</span>
        </div>
      </div>

      {/* 日誌區域 */}
      <div style={styles.logsSection}>
        <h3 style={styles.sectionTitle}>
          即時日誌
          {status?.log_file && <span style={styles.logFile}>{status.log_file}</span>}
        </h3>
        <div style={styles.logsContainer}>
          {logs.length > 0 ? (
            logs.map((line, index) => (
              <div
                key={index}
                style={{
                  ...styles.logLine,
                  color: line.includes('ERROR') ? '#f44336' :
                         line.includes('WARNING') ? '#ff9800' :
                         line.includes('INFO') ? '#4CAF50' :
                         line.includes('階段') ? '#2196F3' : '#ccc'
                }}
              >
                {line}
              </div>
            ))
          ) : (
            <div style={styles.noLogs}>暫無日誌</div>
          )}
        </div>
      </div>

      {/* 歷史記錄 */}
      <div style={styles.historySection}>
        <h3 style={styles.sectionTitle}>運行歷史</h3>
        <div style={styles.historyList}>
          {history.map((item, index) => (
            <div key={index} style={styles.historyItem}>
              <span style={styles.historyType}>{item.type}</span>
              <span style={styles.historyFilename}>{item.filename}</span>
              <span style={styles.historyTime}>
                {new Date(item.start_time).toLocaleString()}
              </span>
              <span style={styles.historySize}>{item.size_kb} KB</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '1.8rem',
    fontWeight: 600,
    color: '#333',
    margin: 0,
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.9rem',
    color: '#666',
  },
  refreshButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  errorCard: {
    backgroundColor: '#fff3f3',
    border: '1px solid #ffcdd2',
    borderRadius: '8px',
    padding: '2rem',
    textAlign: 'center' as const,
  },
  codeBlock: {
    backgroundColor: '#f5f5f5',
    padding: '1rem',
    borderRadius: '4px',
    overflow: 'auto',
    textAlign: 'left' as const,
    fontSize: '0.85rem',
  },
  retryButton: {
    marginTop: '1rem',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  statusSection: {
    marginBottom: '2rem',
  },
  statusCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  statusHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  statusBadge: {
    padding: '0.25rem 0.75rem',
    borderRadius: '20px',
    color: 'white',
    fontWeight: 500,
    fontSize: '0.9rem',
  },
  pidText: {
    color: '#666',
    fontSize: '0.9rem',
  },
  runtime: {
    margin: '0.5rem 0 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  actionButtons: {
    marginTop: '1rem',
  },
  startButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  stopButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  localSection: {
    backgroundColor: '#e3f2fd',
    borderRadius: '8px',
    padding: '1.5rem',
    marginBottom: '2rem',
    border: '1px solid #bbdefb',
  },
  localBadge: {
    backgroundColor: '#2196F3',
    color: 'white',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    marginLeft: '0.5rem',
  },
  localStats: {
    display: 'flex',
    alignItems: 'center',
    gap: '2rem',
    flexWrap: 'wrap' as const,
  },
  localTotal: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
  },
  localNumber: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#1976D2',
  },
  localLabel: {
    fontSize: '0.9rem',
    color: '#666',
  },
  categoryList: {
    display: 'flex',
    gap: '1rem',
    flexWrap: 'wrap' as const,
  },
  categoryItem: {
    backgroundColor: 'white',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  categoryCount: {
    fontWeight: 600,
    color: '#1976D2',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  statCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  statIcon: {
    fontSize: '2rem',
  },
  statContent: {},
  statValue: {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#333',
  },
  statLabel: {
    fontSize: '0.85rem',
    color: '#666',
  },
  progressSection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '2rem',
  },
  progressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
    fontWeight: 500,
  },
  progressPercent: {
    color: '#4CAF50',
    fontWeight: 600,
  },
  progressBar: {
    height: '20px',
    backgroundColor: '#e0e0e0',
    borderRadius: '10px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    transition: 'width 0.3s ease',
  },
  progressLegend: {
    marginTop: '0.5rem',
    fontSize: '0.85rem',
    color: '#666',
    textAlign: 'right' as const,
  },
  logsSection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: 600,
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  logFile: {
    fontSize: '0.8rem',
    color: '#666',
    fontWeight: 400,
  },
  logsContainer: {
    backgroundColor: '#1e1e1e',
    borderRadius: '4px',
    padding: '1rem',
    maxHeight: '300px',
    overflow: 'auto',
    fontFamily: 'Monaco, Consolas, monospace',
    fontSize: '0.8rem',
  },
  logLine: {
    padding: '2px 0',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-all' as const,
  },
  noLogs: {
    color: '#666',
    textAlign: 'center' as const,
    padding: '2rem',
  },
  historySection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  historyList: {},
  historyItem: {
    display: 'grid',
    gridTemplateColumns: '120px 1fr 180px 80px',
    gap: '1rem',
    padding: '0.75rem 0',
    borderBottom: '1px solid #eee',
    alignItems: 'center',
  },
  historyType: {
    backgroundColor: '#e3f2fd',
    color: '#1976D2',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    textAlign: 'center' as const,
  },
  historyFilename: {
    fontFamily: 'Monaco, Consolas, monospace',
    fontSize: '0.85rem',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  historyTime: {
    color: '#666',
    fontSize: '0.85rem',
  },
  historySize: {
    color: '#999',
    fontSize: '0.85rem',
    textAlign: 'right' as const,
  },
};

export default PipelineMonitorPage;
