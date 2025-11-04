import type { FC } from 'react';
import { Card, Statistic, Row, Col, Tag, Progress, Alert } from 'antd';
import {
  CheckCircleOutlined,
  EditOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { TestResult } from '../../../types/proofreading';
import './TestResults.css';

interface TestResultsProps {
  results: TestResult;
}

const TestResults: FC<TestResultsProps> = ({ results }) => {
  // 計算文字變更統計
  const calculateStats = () => {
    const originalLength = results.original.length;
    const modifiedLength = results.result.length;
    const changeCount = results.changes.length;
    const changePercent = originalLength > 0
      ? Math.round((Math.abs(modifiedLength - originalLength) / originalLength) * 100)
      : 0;

    return {
      originalLength,
      modifiedLength,
      changeCount,
      changePercent,
      addedChars: Math.max(0, modifiedLength - originalLength),
      removedChars: Math.max(0, originalLength - modifiedLength)
    };
  };

  const stats = calculateStats();

  // 根據置信度獲取顏色
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'green';
    if (confidence >= 0.7) return 'blue';
    if (confidence >= 0.5) return 'orange';
    return 'red';
  };

  // 計算平均置信度
  const averageConfidence = results.changes.length > 0
    ? results.changes.reduce((sum, change) => sum + change.confidence, 0) / results.changes.length
    : 0;

  return (
    <div className="test-results">
      {/* 統計卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="變更數量"
              value={stats.changeCount}
              prefix={<EditOutlined />}
              suffix="處"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="執行時間"
              value={results.execution_time_ms}
              prefix={<ClockCircleOutlined />}
              suffix="ms"
              valueStyle={{ color: results.execution_time_ms < 100 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文字長度變化"
              value={stats.changePercent}
              suffix="%"
              valueStyle={{ color: stats.changePercent === 0 ? '#3f8600' : '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均置信度"
              value={Math.round(averageConfidence * 100)}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: getConfidenceColor(averageConfidence) }}
            />
          </Card>
        </Col>
      </Row>

      {/* 詳細統計 */}
      <Card title="詳細分析" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <div className="stat-item">
              <span className="stat-label">原始文本長度:</span>
              <span className="stat-value">{stats.originalLength} 字符</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">修改後長度:</span>
              <span className="stat-value">{stats.modifiedLength} 字符</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">新增字符:</span>
              <Tag color="green">+{stats.addedChars}</Tag>
            </div>
            <div className="stat-item">
              <span className="stat-label">刪除字符:</span>
              <Tag color="red">-{stats.removedChars}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="confidence-distribution">
              <h4>置信度分布</h4>
              {results.changes.length > 0 ? (
                <>
                  <div className="confidence-item">
                    <span>高置信度 (≥90%):</span>
                    <Progress
                      percent={
                        (results.changes.filter(c => c.confidence >= 0.9).length / results.changes.length) * 100
                      }
                      strokeColor="#52c41a"
                      format={(percent) => `${Math.round(percent || 0)}%`}
                    />
                  </div>
                  <div className="confidence-item">
                    <span>中置信度 (70-89%):</span>
                    <Progress
                      percent={
                        (results.changes.filter(c => c.confidence >= 0.7 && c.confidence < 0.9).length / results.changes.length) * 100
                      }
                      strokeColor="#1890ff"
                      format={(percent) => `${Math.round(percent || 0)}%`}
                    />
                  </div>
                  <div className="confidence-item">
                    <span>低置信度 (&lt;70%):</span>
                    <Progress
                      percent={
                        (results.changes.filter(c => c.confidence < 0.7).length / results.changes.length) * 100
                      }
                      strokeColor="#faad14"
                      format={(percent) => `${Math.round(percent || 0)}%`}
                    />
                  </div>
                </>
              ) : (
                <Alert
                  message="無變更"
                  description="測試未發現需要修改的內容"
                  type="info"
                  showIcon
                />
              )}
            </div>
          </Col>
        </Row>
      </Card>

      {/* 變更類型統計 */}
      <Card title="變更類型分析" style={{ marginTop: 16 }}>
        {results.changes.length > 0 ? (
          <div className="change-type-stats">
            {Object.entries(
              results.changes.reduce((acc, change) => {
                acc[change.type] = (acc[change.type] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).map(([type, count]) => (
              <div key={type} className="type-stat">
                <Tag color="purple">{type}</Tag>
                <span className="type-count">{count} 處</span>
                <Progress
                  percent={(count / results.changes.length) * 100}
                  size="small"
                  format={(percent) => `${Math.round(percent || 0)}%`}
                />
              </div>
            ))}
          </div>
        ) : (
          <Alert
            message="無變更類型"
            description="測試未發現需要修改的內容"
            type="info"
            showIcon
          />
        )}
      </Card>
    </div>
  );
};

export default TestResults;
