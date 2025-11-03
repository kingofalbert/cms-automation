import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Space,
  Progress,
  message,
  Spin,
  Empty,
  Tag,
  Divider,
  Modal,
  Tooltip
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  ExperimentOutlined,
  SaveOutlined,
  RocketOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { RuleDraft, DraftRule, ReviewStatus, ReviewAction } from '../../../types/proofreading';
import ruleManagementAPI from '../../../services/ruleManagementAPI';
import RuleCard from './RuleCard';
import BatchReviewPanel from './BatchReviewPanel';
import './RuleDetailPage.css';

const RuleDetailPage: React.FC = () => {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<RuleDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [showBatchReview, setShowBatchReview] = useState(false);
  const [editingRule, setEditingRule] = useState<string | null>(null);
  const [testingRule, setTestingRule] = useState<string | null>(null);

  // 載入草稿詳情
  const loadDraftDetail = async () => {
    if (!draftId) return;

    setLoading(true);
    try {
      const response = await ruleManagementAPI.getDraftDetail(draftId);
      if (response.success) {
        setDraft(response.data);
      }
    } catch (error) {
      message.error('載入草稿詳情失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDraftDetail();
  }, [draftId]);

  // 處理單個規則審查
  const handleRuleReview = async (ruleId: string, action: ReviewAction, comment?: string) => {
    if (!draft) return;

    try {
      const response = await ruleManagementAPI.batchReview(draft.draft_id, [{
        rule_id: ruleId,
        action,
        comment
      }]);

      if (response.success) {
        message.success('審查成功');
        loadDraftDetail(); // 重新載入
      }
    } catch (error) {
      message.error('審查失敗');
      console.error(error);
    }
  };

  // 處理批量審查
  const handleBatchReview = async (action: ReviewAction, reviews?: Array<{
    rule_id: string;
    action: ReviewAction;
    comment?: string;
  }>) => {
    if (!draft) return;

    try {
      const reviewItems = reviews || selectedRules.map(ruleId => ({
        rule_id: ruleId,
        action,
        comment: undefined
      }));

      const response = await ruleManagementAPI.batchReview(draft.draft_id, reviewItems);

      if (response.success) {
        message.success('批量審查成功');
        setSelectedRules([]);
        setShowBatchReview(false);
        loadDraftDetail();
      }
    } catch (error) {
      message.error('批量審查失敗');
      console.error(error);
    }
  };

  // 處理規則發布
  const handlePublish = () => {
    Modal.confirm({
      title: '確認發布規則',
      content: '發布後規則將立即生效，是否繼續？',
      onOk: async () => {
        if (!draft) return;

        try {
          const response = await ruleManagementAPI.publishRules(draft.draft_id, {
            name: `規則集 ${new Date().toISOString()}`,
            description: draft.description || '自動發布的規則集',
            include_rejected: false,
            test_mode: false
          });

          if (response.success) {
            message.success('規則發布成功');
            navigate('/proofreading/rules');
          }
        } catch (error) {
          message.error('發布失敗');
          console.error(error);
        }
      }
    });
  };

  // 計算進度統計
  const getProgressStats = () => {
    if (!draft) return { percent: 0, approved: 0, modified: 0, rejected: 0, pending: 0 };

    const stats = draft.review_progress;
    const percent = stats.total > 0 ? Math.round((stats.reviewed / stats.total) * 100) : 0;
    const pending = stats.total - stats.reviewed;

    return {
      percent,
      approved: stats.approved,
      modified: stats.modified,
      rejected: stats.rejected,
      pending
    };
  };

  const stats = getProgressStats();

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="載入中..." />
      </div>
    );
  }

  if (!draft) {
    return (
      <Empty
        description="草稿不存在"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button onClick={() => navigate('/proofreading/rules')}>
          返回規則列表
        </Button>
      </Empty>
    );
  }

  return (
    <div className="rule-detail-page">
      {/* 頁面標題 */}
      <Card className="page-header">
        <div className="header-content">
          <div className="header-left">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/proofreading/rules')}
            >
              返回
            </Button>
            <Divider type="vertical" />
            <h2>{draft.description || draft.draft_id}</h2>
          </div>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadDraftDetail}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={handlePublish}
              disabled={stats.pending > 0}
            >
              發布規則
            </Button>
          </Space>
        </div>
      </Card>

      {/* 進度統計 */}
      <Card className="progress-card">
        <div className="progress-header">
          <span>審查進度: {stats.percent}%</span>
          <div className="progress-stats">
            <Tag color="green">
              <CheckOutlined /> 已批准: {stats.approved}
            </Tag>
            <Tag color="blue">
              <EditOutlined /> 已修改: {stats.modified}
            </Tag>
            <Tag color="red">
              <CloseOutlined /> 已拒絕: {stats.rejected}
            </Tag>
            <Tag color="orange">
              待審查: {stats.pending}
            </Tag>
          </div>
        </div>
        <Progress
          percent={stats.percent}
          status={stats.percent === 100 ? 'success' : 'active'}
          strokeColor={{
            '0%': '#1890ff',
            '100%': '#52c41a'
          }}
        />
      </Card>

      {/* 操作欄 */}
      <Card className="action-bar">
        <Space>
          <Button
            onClick={() => setShowBatchReview(true)}
            disabled={selectedRules.length === 0}
          >
            批量操作 ({selectedRules.length})
          </Button>
          <Button
            icon={<ExperimentOutlined />}
            onClick={() => navigate(`/proofreading/test/${draft.draft_id}`)}
          >
            測試所有規則
          </Button>
        </Space>
      </Card>

      {/* 規則列表 */}
      <div className="rules-container">
        {draft.rules.map((rule) => (
          <RuleCard
            key={rule.rule_id}
            rule={rule}
            selected={selectedRules.includes(rule.rule_id)}
            onSelect={(selected) => {
              if (selected) {
                setSelectedRules([...selectedRules, rule.rule_id]);
              } else {
                setSelectedRules(selectedRules.filter(id => id !== rule.rule_id));
              }
            }}
            onReview={handleRuleReview}
            onEdit={() => setEditingRule(rule.rule_id)}
            onTest={() => setTestingRule(rule.rule_id)}
          />
        ))}
      </div>

      {/* 批量審查面板 */}
      <Modal
        title="批量審查"
        visible={showBatchReview}
        onCancel={() => setShowBatchReview(false)}
        footer={null}
        width={600}
      >
        <BatchReviewPanel
          selectedRules={selectedRules}
          rules={draft.rules.filter(r => selectedRules.includes(r.rule_id))}
          onReview={handleBatchReview}
          onCancel={() => setShowBatchReview(false)}
        />
      </Modal>
    </div>
  );
};

export default RuleDetailPage;