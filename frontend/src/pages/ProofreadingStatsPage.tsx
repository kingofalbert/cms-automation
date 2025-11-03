import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Typography,
  Space,
  Spin,
  Empty,
  Progress,
  Timeline,
  Divider
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';
import ruleManagementAPI from '../services/ruleManagementAPI';
import './ProofreadingStatsPage.css';

const { Title, Text } = Typography;

interface StatsData {
  totalRulesets: number;
  totalRules: number;
  activeRulesets: number;
  avgRulesPerRuleset: number;
  recentActivity: Array<{
    date: string;
    action: string;
    rulesetId: string;
    ruleCount: number;
  }>;
  rulesetDistribution: Array<{
    ruleCount: number;
    count: number;
  }>;
  topRulesets: Array<{
    ruleset_id: string;
    name: string;
    total_rules: number;
    status: string;
    created_at: string;
  }>;
}

const ProofreadingStatsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [drafts, setDrafts] = useState<any[]>([]);

  // 載入統計數據
  const loadStatistics = async () => {
    setLoading(true);
    try {
      // 獲取已發布的規則集
      const publishedResponse = await ruleManagementAPI.getPublishedRulesets();

      // 獲取草稿列表
      const draftsResponse = await ruleManagementAPI.fetchDrafts(undefined, 1, 100);

      if (publishedResponse.success) {
        const rulesets = publishedResponse.data.rulesets || [];

        // 計算統計數據
        const totalRulesets = rulesets.length;
        const totalRules = rulesets.reduce((sum: number, rs: any) => sum + (rs.total_rules || 0), 0);
        const activeRulesets = rulesets.filter((rs: any) => rs.status === 'active').length;
        const avgRulesPerRuleset = totalRulesets > 0 ? Math.round(totalRules / totalRulesets) : 0;

        // 計算規則集分佈
        const distribution = new Map<number, number>();
        rulesets.forEach((rs: any) => {
          const count = rs.total_rules || 0;
          const bucket = Math.floor(count / 10) * 10; // 按10分組
          distribution.set(bucket, (distribution.get(bucket) || 0) + 1);
        });

        const rulesetDistribution = Array.from(distribution.entries())
          .map(([ruleCount, count]) => ({ ruleCount, count }))
          .sort((a, b) => a.ruleCount - b.ruleCount);

        // 取前5個規則集
        const topRulesets = [...rulesets]
          .sort((a: any, b: any) => (b.total_rules || 0) - (a.total_rules || 0))
          .slice(0, 5);

        // 生成最近活動（基於創建時間）
        const recentActivity = rulesets
          .map((rs: any) => ({
            date: rs.created_at,
            action: '發布規則集',
            rulesetId: rs.ruleset_id,
            ruleCount: rs.total_rules
          }))
          .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime())
          .slice(0, 10);

        setStats({
          totalRulesets,
          totalRules,
          activeRulesets,
          avgRulesPerRuleset,
          recentActivity,
          rulesetDistribution,
          topRulesets
        });
      }

      if (draftsResponse.success) {
        setDrafts(draftsResponse.data.drafts || []);
      }
    } catch (error) {
      console.error('載入統計數據失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatistics();
  }, []);

  if (loading) {
    return (
      <div className="proofreading-stats-page loading-container">
        <Spin size="large" tip="載入統計數據中..." />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="proofreading-stats-page">
        <Empty description="無統計數據" />
      </div>
    );
  }

  // 草稿統計
  const draftStats = {
    total: drafts.length,
    pending: drafts.filter(d => d.status === 'pending').length,
    inReview: drafts.filter(d => d.status === 'in_review').length,
    published: drafts.filter(d => d.status === 'published').length
  };

  // 計算發佈率
  const publishRate = draftStats.total > 0
    ? Math.round((draftStats.published / draftStats.total) * 100)
    : 0;

  // 規則集分佈表格列
  const distributionColumns = [
    {
      title: '規則數量範圍',
      dataIndex: 'ruleCount',
      key: 'ruleCount',
      render: (count: number) => `${count}-${count + 9} 條`
    },
    {
      title: '規則集數量',
      dataIndex: 'count',
      key: 'count',
      render: (count: number) => <Tag color="blue">{count} 個</Tag>
    },
    {
      title: '百分比',
      key: 'percentage',
      render: (_: any, record: any) => {
        const percentage = ((record.count / stats.totalRulesets) * 100).toFixed(1);
        return <Progress percent={parseFloat(percentage)} size="small" />;
      }
    }
  ];

  // 頂級規則集表格列
  const topRulesetsColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: any, __: any, index: number) => (
        <Text strong style={{ fontSize: '18px' }}>#{index + 1}</Text>
      )
    },
    {
      title: '規則集ID',
      dataIndex: 'ruleset_id',
      key: 'ruleset_id',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '規則數量',
      dataIndex: 'total_rules',
      key: 'total_rules',
      align: 'center' as const,
      render: (count: number) => (
        <Tag color="purple" style={{ fontSize: '14px' }}>
          <ThunderboltOutlined /> {count} 條
        </Tag>
      )
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '啟用中' : '測試模式'}
        </Tag>
      )
    },
    {
      title: '創建時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('zh-TW')
    }
  ];

  return (
    <div className="proofreading-stats-page">
      <div className="page-header">
        <Title level={2}>
          <FileTextOutlined /> 校對規則統計
        </Title>
      </div>

      {/* 核心統計卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已發布規則集"
              value={stats.totalRulesets}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              suffix="個"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="總規則數"
              value={stats.totalRules}
              prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
              suffix="條"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="啟用中規則集"
              value={stats.activeRulesets}
              prefix={<ThunderboltOutlined style={{ color: '#faad14' }} />}
              suffix={`/ ${stats.totalRulesets}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均規則數"
              value={stats.avgRulesPerRuleset}
              prefix={<RiseOutlined style={{ color: '#722ed1' }} />}
              suffix="條/集"
            />
          </Card>
        </Col>
      </Row>

      {/* 草稿統計 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="草稿狀態分佈">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="待審核"
                  value={draftStats.pending}
                  prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                  suffix={`/ ${draftStats.total}`}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="審核中"
                  value={draftStats.inReview}
                  prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
                  suffix={`/ ${draftStats.total}`}
                />
              </Col>
            </Row>
            <Divider />
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">發布成功率</Text>
              <div style={{ marginTop: 8 }}>
                <Progress
                  type="circle"
                  percent={publishRate}
                  format={percent => `${percent}%`}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="最近活動" style={{ height: '100%' }}>
            <Timeline
              items={stats.recentActivity.slice(0, 5).map(activity => ({
                color: 'green',
                children: (
                  <div>
                    <Text strong>{activity.action}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {activity.rulesetId} · {activity.ruleCount} 條規則
                    </Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '11px' }}>
                      {new Date(activity.date).toLocaleString('zh-TW')}
                    </Text>
                  </div>
                )
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* 規則集分佈 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="規則集分佈">
            <Table
              columns={distributionColumns}
              dataSource={stats.rulesetDistribution}
              rowKey="ruleCount"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* 頂級規則集 */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="Top 5 規則集（按規則數量）">
            <Table
              columns={topRulesetsColumns}
              dataSource={stats.topRulesets}
              rowKey="ruleset_id"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ProofreadingStatsPage;
