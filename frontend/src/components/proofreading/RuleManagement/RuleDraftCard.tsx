import React from 'react';
import { Card, Progress, Tag, Button, Space, Tooltip } from 'antd';
import {
  FileTextOutlined,
  EyeOutlined,
  CheckOutlined,
  EditOutlined,
  ClockCircleOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { DraftStatus, ReviewProgress } from '../../../types/proofreading';
import './RuleDraftCard.css';

interface RuleDraftCardProps {
  draft: {
    draft_id: string;
    rule_count: number;
    status: string;
    description?: string;
    created_at: string;
    created_by: string;
    review_progress: ReviewProgress;
  };
  onView: () => void;
  onRefresh: () => void;
}

const RuleDraftCard: React.FC<RuleDraftCardProps> = ({ draft, onView }) => {
  // 獲取狀態標籤顏色
  const getStatusColor = (status: string) => {
    switch (status) {
      case DraftStatus.PENDING_REVIEW:
        return 'orange';
      case DraftStatus.IN_REVIEW:
        return 'blue';
      case DraftStatus.APPROVED:
        return 'green';
      case DraftStatus.REJECTED:
        return 'red';
      default:
        return 'default';
    }
  };

  // 獲取狀態文字
  const getStatusText = (status: string) => {
    switch (status) {
      case DraftStatus.PENDING_REVIEW:
        return '待審查';
      case DraftStatus.IN_REVIEW:
        return '審查中';
      case DraftStatus.APPROVED:
        return '已批准';
      case DraftStatus.REJECTED:
        return '已拒絕';
      default:
        return status;
    }
  };

  // 計算進度百分比
  const progressPercent = draft.review_progress.total > 0
    ? Math.round((draft.review_progress.reviewed / draft.review_progress.total) * 100)
    : 0;

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card
      className="rule-draft-card"
      hoverable
      actions={[
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={onView}
        >
          {draft.status === DraftStatus.IN_REVIEW ? '繼續審查' : '查看詳情'}
        </Button>
      ]}
    >
      <div className="card-header">
        <div className="card-title">
          <FileTextOutlined />
          <span>{draft.description || draft.draft_id}</span>
        </div>
        <Tag color={getStatusColor(draft.status)}>
          {getStatusText(draft.status)}
        </Tag>
      </div>

      <div className="card-meta">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div className="meta-item">
            <span className="meta-label">規則數量:</span>
            <span className="meta-value">{draft.rule_count} 條</span>
          </div>

          <div className="meta-item">
            <ClockCircleOutlined />
            <span className="meta-label">創建時間:</span>
            <span className="meta-value">{formatDate(draft.created_at)}</span>
          </div>

          <div className="meta-item">
            <TeamOutlined />
            <span className="meta-label">創建者:</span>
            <span className="meta-value">{draft.created_by}</span>
          </div>
        </Space>
      </div>

      <div className="card-progress">
        <div className="progress-header">
          <span>審查進度</span>
          <span>{draft.review_progress.reviewed}/{draft.review_progress.total}</span>
        </div>

        <Progress
          percent={progressPercent}
          status={progressPercent === 100 ? 'success' : 'active'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />

        <div className="progress-stats">
          <Tooltip title="已批准">
            <Tag color="green">
              <CheckOutlined /> {draft.review_progress.approved}
            </Tag>
          </Tooltip>
          <Tooltip title="已修改">
            <Tag color="blue">
              <EditOutlined /> {draft.review_progress.modified}
            </Tag>
          </Tooltip>
          <Tooltip title="已拒絕">
            <Tag color="red">
              ✕ {draft.review_progress.rejected}
            </Tag>
          </Tooltip>
        </div>
      </div>
    </Card>
  );
};

export default RuleDraftCard;