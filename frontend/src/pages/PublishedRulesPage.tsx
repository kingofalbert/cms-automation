import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message, Tooltip, Modal, Descriptions, Typography, Divider } from 'antd';
import {
  DownloadOutlined,
  EyeOutlined,
  CodeOutlined,
  FileTextOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import ruleManagementAPI from '../services/ruleManagementAPI';
import { formatDate, DATE_FORMATS } from '../lib/utils';
import './PublishedRulesPage.css';

const { Title, Text } = Typography;

interface PublishedRuleset {
  ruleset_id: string;
  name: string;
  total_rules: number;
  created_at: string;
  status: string;
  download_urls: {
    python: string;
    typescript: string;
    json: string;
  };
}

const PublishedRulesPage: React.FC = () => {
  const [rulesets, setRulesets] = useState<PublishedRuleset[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedRuleset, setSelectedRuleset] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // 載入已發布的規則集
  const loadPublishedRulesets = async () => {
    setLoading(true);
    try {
      const response = await ruleManagementAPI.getPublishedRulesets();
      if (response.success) {
        setRulesets(response.data.rulesets || []);
      }
    } catch (error) {
      message.error('載入規則集失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPublishedRulesets();
  }, []);

  // 下載規則文件
  const handleDownload = async (rulesetId: string, format: 'python' | 'typescript' | 'json') => {
    try {
      message.loading({ content: `正在下載 ${format.toUpperCase()} 文件...`, key: 'download' });

      const blob = await ruleManagementAPI.downloadRules(rulesetId, format);

      // 創建下載連結
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // 設置文件名
      const extension = format === 'typescript' ? 'ts' : format === 'python' ? 'py' : 'json';
      link.download = `${rulesetId}.${extension}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success({ content: '下載成功', key: 'download' });
    } catch (error) {
      message.error({ content: '下載失敗', key: 'download' });
      console.error(error);
    }
  };

  // 查看規則集詳情
  const handleViewDetail = async (rulesetId: string) => {
    setDetailLoading(true);
    setDetailModalVisible(true);

    try {
      const response = await ruleManagementAPI.getPublishedRulesetDetail(rulesetId);
      if (response.success) {
        setSelectedRuleset(response.data);
      }
    } catch (error) {
      message.error('載入詳情失敗');
      console.error(error);
    } finally {
      setDetailLoading(false);
    }
  };

  const columns = [
    {
      title: '規則集ID',
      dataIndex: 'ruleset_id',
      key: 'ruleset_id',
      width: 200,
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '規則集名稱',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '規則數量',
      dataIndex: 'total_rules',
      key: 'total_rules',
      width: 100,
      align: 'center' as const,
      render: (count: number) => <Tag color="blue">{count} 條</Tag>
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
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
      width: 180,
      render: (date: string) => formatDate(date, DATE_FORMATS.FULL)
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      render: (_: any, record: PublishedRuleset) => (
        <Space>
          <Tooltip title="查看詳情">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record.ruleset_id)}
            >
              詳情
            </Button>
          </Tooltip>

          <Tooltip title="下載 Python 模組">
            <Button
              size="small"
              icon={<CodeOutlined />}
              onClick={() => handleDownload(record.ruleset_id, 'python')}
            >
              Python
            </Button>
          </Tooltip>

          <Tooltip title="下載 TypeScript 模組">
            <Button
              size="small"
              icon={<CodeOutlined />}
              onClick={() => handleDownload(record.ruleset_id, 'typescript')}
            >
              TS
            </Button>
          </Tooltip>

          <Tooltip title="下載 JSON 配置">
            <Button
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => handleDownload(record.ruleset_id, 'json')}
            >
              JSON
            </Button>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div className="published-rules-page">
      <Card>
        <div className="page-header">
          <Title level={2}>
            <DownloadOutlined /> 已發布規則集
          </Title>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadPublishedRulesets}
            loading={loading}
          >
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={rulesets}
          rowKey="ruleset_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 個規則集`,
            showSizeChanger: true
          }}
        />
      </Card>

      {/* 詳情彈窗 */}
      <Modal
        title="規則集詳情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            關閉
          </Button>
        ]}
        width={800}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>載入中...</div>
        ) : selectedRuleset ? (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="規則集ID" span={2}>
                <Text code>{selectedRuleset.ruleset_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="名稱" span={2}>
                {selectedRuleset.metadata?.name || selectedRuleset.ruleset_id}
              </Descriptions.Item>
              <Descriptions.Item label="狀態">
                <Tag color={selectedRuleset.status === 'active' ? 'success' : 'default'}>
                  {selectedRuleset.status === 'active' ? '啟用中' : '測試模式'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="規則數量">
                <Tag color="blue">{selectedRuleset.rules?.length || 0} 條</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="創建時間" span={2}>
                {formatDate(selectedRuleset.created_at, DATE_FORMATS.FULL)}
              </Descriptions.Item>
              <Descriptions.Item label="版本">
                {selectedRuleset.version || '1.0.0'}
              </Descriptions.Item>
              <Descriptions.Item label="模組名稱">
                <Text code>{selectedRuleset.module_name}</Text>
              </Descriptions.Item>
            </Descriptions>

            <Divider>規則列表</Divider>

            <div style={{ maxHeight: '400px', overflow: 'auto' }}>
              {selectedRuleset.rules?.map((rule: any, index: number) => (
                <Card key={index} size="small" style={{ marginBottom: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <strong>規則 {index + 1}:</strong> {rule.natural_language}
                    </div>
                    <div>
                      <Tag color="purple">類型: {rule.rule_type}</Tag>
                      <Tag color="cyan">置信度: {(rule.confidence * 100).toFixed(0)}%</Tag>
                    </div>
                    {rule.pattern && (
                      <div>
                        <Text code style={{ fontSize: '12px' }}>{rule.pattern}</Text>
                      </div>
                    )}
                  </Space>
                </Card>
              ))}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

export default PublishedRulesPage;
