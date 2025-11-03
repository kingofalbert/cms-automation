import React, { useState } from 'react';
import { Card, Tag, Button, Space, Checkbox, Tooltip, Collapse } from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  CodeOutlined
} from '@ant-design/icons';
import { DraftRule, ReviewStatus, ReviewAction } from '../../../types/proofreading';
import './RuleCard.css';

const { Panel } = Collapse;

interface RuleCardProps {
  rule: DraftRule;
  selected: boolean;
  onSelect: (selected: boolean) => void;
  onReview: (ruleId: string, action: ReviewAction, comment?: string) => void;
  onEdit: () => void;
  onTest: () => void;
}

const RuleCard: React.FC<RuleCardProps> = ({
  rule,
  selected,
  onSelect,
  onReview,
  onEdit,
  onTest
}) => {
  const [expanded, setExpanded] = useState(false);

  // 獲取審查狀態顏色
  const getStatusColor = (status: ReviewStatus) => {
    switch (status) {
      case ReviewStatus.APPROVED:
        return 'green';
      case ReviewStatus.MODIFIED:
        return 'blue';
      case ReviewStatus.REJECTED:
        return 'red';
      case ReviewStatus.PENDING:
      default:
        return 'orange';
    }
  };

  // 獲取審查狀態文字
  const getStatusText = (status: ReviewStatus) => {
    switch (status) {
      case ReviewStatus.APPROVED:
        return '已批准';
      case ReviewStatus.MODIFIED:
        return '已修改';
      case ReviewStatus.REJECTED:
        return '已拒絕';
      case ReviewStatus.PENDING:
      default:
        return '待審查';
    }
  };

  // 格式化條件顯示
  const formatConditions = (conditions?: Record<string, any>) => {
    if (!conditions || Object.keys(conditions).length === 0) {
      return '無特殊條件';
    }

    return Object.entries(conditions)
      .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
      .join(', ');
  };

  return (
    <Card
      className={`rule-card ${selected ? 'selected' : ''}`}
      hoverable
    >
      <div className="rule-header">
        <div className="rule-header-left">
          <Checkbox
            checked={selected}
            onChange={(e) => onSelect(e.target.checked)}
          />
          <span className="rule-id">#{rule.rule_id}</span>
          <Tag color={getStatusColor(rule.review_status)}>
            {getStatusText(rule.review_status)}
          </Tag>
          <Tag color="purple">{rule.rule_type}</Tag>
          <Tag color="cyan">
            置信度: {Math.round(rule.confidence * 100)}%
          </Tag>
        </div>
        <Space>
          <Tooltip title="詳細信息">
            <Button
              type="text"
              icon={<InfoCircleOutlined />}
              onClick={() => setExpanded(!expanded)}
            />
          </Tooltip>
        </Space>
      </div>

      <div className="rule-content">
        {/* 自然語言描述 */}
        <div className="natural-language-section">
          <h4>自然語言描述:</h4>
          <p className="natural-language-text">{rule.natural_language}</p>
        </div>

        {/* 規則代碼 */}
        <div className="rule-code-section">
          <h4><CodeOutlined /> 規則代碼:</h4>
          <div className="code-display">
            {rule.pattern && (
              <div>
                <span className="code-label">Pattern:</span>
                <code>{rule.pattern}</code>
              </div>
            )}
            {rule.replacement && (
              <div>
                <span className="code-label">Replace:</span>
                <code>{rule.replacement}</code>
              </div>
            )}
            <div>
              <span className="code-label">Conditions:</span>
              <code>{formatConditions(rule.conditions)}</code>
            </div>
          </div>
        </div>

        {/* 示例 */}
        {rule.examples && rule.examples.length > 0 && (
          <div className="examples-section">
            <h4>示例:</h4>
            {rule.examples.slice(0, 2).map((example, index) => (
              <div key={index} className="example-item">
                <div className="example-before">
                  <span className="example-label">修改前:</span>
                  <span className="example-text">{example.before}</span>
                </div>
                <div className="example-after">
                  <span className="example-label">修改後:</span>
                  <span className="example-text">{example.after}</span>
                </div>
              </div>
            ))}
            {rule.examples.length > 2 && (
              <div className="more-examples">
                還有 {rule.examples.length - 2} 個示例...
              </div>
            )}
          </div>
        )}

        {/* 展開的詳細信息 */}
        {expanded && (
          <Collapse ghost activeKey={expanded ? ['1'] : []}>
            <Panel header="詳細信息" key="1">
              {rule.user_feedback && (
                <div className="feedback-section">
                  <strong>用戶反饋:</strong> {rule.user_feedback}
                </div>
              )}
              {rule.modified_at && (
                <div className="metadata">
                  <strong>最後修改:</strong> {new Date(rule.modified_at).toLocaleString('zh-TW')}
                  {rule.modified_by && ` by ${rule.modified_by}`}
                </div>
              )}
              {rule.examples && rule.examples.length > 2 && (
                <div className="all-examples">
                  <strong>所有示例:</strong>
                  {rule.examples.map((example, index) => (
                    <div key={index} className="example-item-detailed">
                      <div>{index + 1}. {example.before} → {example.after}</div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </Collapse>
        )}
      </div>

      {/* 操作按鈕 */}
      <div className="rule-actions">
        <Space>
          {rule.review_status === ReviewStatus.PENDING && (
            <>
              <Button
                type="primary"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => onReview(rule.rule_id, ReviewAction.APPROVE)}
              >
                批准
              </Button>
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={onEdit}
              >
                修改
              </Button>
              <Button
                danger
                size="small"
                icon={<CloseOutlined />}
                onClick={() => onReview(rule.rule_id, ReviewAction.REJECT)}
              >
                拒絕
              </Button>
            </>
          )}
          <Button
            size="small"
            icon={<ExperimentOutlined />}
            onClick={onTest}
          >
            測試
          </Button>
        </Space>
      </div>
    </Card>
  );
};

export default RuleCard;