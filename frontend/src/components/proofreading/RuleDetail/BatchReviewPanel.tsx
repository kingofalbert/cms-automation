import React, { useState } from 'react';
import { Radio, Button, Space, Input, Table, Tag } from 'antd';
import { DraftRule, ReviewAction } from '../../../types/proofreading';
import './BatchReviewPanel.css';

const { TextArea } = Input;

interface BatchReviewPanelProps {
  selectedRules: string[];
  rules: DraftRule[];
  onReview: (
    action: ReviewAction,
    reviews?: Array<{
      rule_id: string;
      action: ReviewAction;
      comment?: string;
    }>
  ) => void;
  onCancel: () => void;
}

const BatchReviewPanel: React.FC<BatchReviewPanelProps> = ({
  selectedRules,
  rules,
  onReview,
  onCancel
}) => {
  const [mode, setMode] = useState<'batch' | 'individual'>('batch');
  const [batchAction, setBatchAction] = useState<ReviewAction>(ReviewAction.APPROVE);
  const [batchComment, setBatchComment] = useState('');
  const [individualReviews, setIndividualReviews] = useState<
    Record<string, { action: ReviewAction; comment?: string }>
  >({});

  // 處理批量審查
  const handleBatchSubmit = () => {
    const reviews = selectedRules.map(ruleId => ({
      rule_id: ruleId,
      action: batchAction,
      comment: batchComment || undefined
    }));
    onReview(batchAction, reviews);
  };

  // 處理逐個審查
  const handleIndividualSubmit = () => {
    const reviews = selectedRules.map(ruleId => ({
      rule_id: ruleId,
      action: individualReviews[ruleId]?.action || ReviewAction.APPROVE,
      comment: individualReviews[ruleId]?.comment
    }));
    onReview(ReviewAction.APPROVE, reviews); // 這裡的第一個參數不重要
  };

  // 更新個別規則的審查
  const updateIndividualReview = (
    ruleId: string,
    action: ReviewAction,
    comment?: string
  ) => {
    setIndividualReviews({
      ...individualReviews,
      [ruleId]: { action, comment }
    });
  };

  const columns = [
    {
      title: '規則ID',
      dataIndex: 'rule_id',
      key: 'rule_id',
      width: 100,
    },
    {
      title: '描述',
      dataIndex: 'natural_language',
      key: 'natural_language',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, rule: DraftRule) => (
        <Radio.Group
          value={individualReviews[rule.rule_id]?.action || ReviewAction.APPROVE}
          onChange={(e) => updateIndividualReview(
            rule.rule_id,
            e.target.value,
            individualReviews[rule.rule_id]?.comment
          )}
          size="small"
        >
          <Radio.Button value={ReviewAction.APPROVE}>
            <Tag color="green">批准</Tag>
          </Radio.Button>
          <Radio.Button value={ReviewAction.MODIFY}>
            <Tag color="blue">修改</Tag>
          </Radio.Button>
          <Radio.Button value={ReviewAction.REJECT}>
            <Tag color="red">拒絕</Tag>
          </Radio.Button>
        </Radio.Group>
      ),
    },
    {
      title: '備註',
      key: 'comment',
      width: 200,
      render: (_, rule: DraftRule) => (
        <Input
          placeholder="選填"
          value={individualReviews[rule.rule_id]?.comment || ''}
          onChange={(e) => updateIndividualReview(
            rule.rule_id,
            individualReviews[rule.rule_id]?.action || ReviewAction.APPROVE,
            e.target.value
          )}
          size="small"
        />
      ),
    },
  ];

  return (
    <div className="batch-review-panel">
      <div className="review-summary">
        已選擇 <strong>{selectedRules.length}</strong> 個規則進行批量審查
      </div>

      <Radio.Group
        value={mode}
        onChange={(e) => setMode(e.target.value)}
        style={{ marginBottom: 20 }}
      >
        <Radio value="batch">統一操作</Radio>
        <Radio value="individual">逐個審查</Radio>
      </Radio.Group>

      {mode === 'batch' ? (
        <div className="batch-mode">
          <div className="batch-action">
            <span>批量操作:</span>
            <Radio.Group
              value={batchAction}
              onChange={(e) => setBatchAction(e.target.value)}
            >
              <Radio.Button value={ReviewAction.APPROVE}>
                全部批准
              </Radio.Button>
              <Radio.Button value={ReviewAction.REJECT}>
                全部拒絕
              </Radio.Button>
            </Radio.Group>
          </div>

          <div className="batch-comment">
            <span>備註 (選填):</span>
            <TextArea
              rows={3}
              value={batchComment}
              onChange={(e) => setBatchComment(e.target.value)}
              placeholder="輸入批量審查備註..."
            />
          </div>

          <div className="action-buttons">
            <Space>
              <Button onClick={onCancel}>取消</Button>
              <Button type="primary" onClick={handleBatchSubmit}>
                確認批量{batchAction === ReviewAction.APPROVE ? '批准' : '拒絕'}
              </Button>
            </Space>
          </div>
        </div>
      ) : (
        <div className="individual-mode">
          <Table
            dataSource={rules}
            columns={columns}
            rowKey="rule_id"
            pagination={false}
            size="small"
            scroll={{ y: 400 }}
          />

          <div className="action-buttons">
            <Space>
              <Button onClick={onCancel}>取消</Button>
              <Button type="primary" onClick={handleIndividualSubmit}>
                提交審查結果
              </Button>
            </Space>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchReviewPanel;