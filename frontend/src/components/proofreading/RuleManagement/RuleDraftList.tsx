import { useState, useEffect, type FC } from 'react';
import { Card, Button, Select, Input, Space, message, Spin, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined, ReloadOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ruleManagementAPI from '../../../services/ruleManagementAPI';
import { DraftStatus } from '../../../types/proofreading';
import RuleDraftCard from './RuleDraftCard';
import './RuleDraftList.css';

const { Option } = Select;
const { Search } = Input;

const RuleDraftList: FC = () => {
  const navigate = useNavigate();
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchText, setSearchText] = useState('');

  // 載入草稿列表
  const loadDrafts = async () => {
    setLoading(true);
    try {
      const response = await ruleManagementAPI.fetchDrafts(statusFilter || undefined, 1);
      if (response.success) {
        setDrafts(response.data.items || []);
      }
    } catch (error) {
      message.error('載入草稿列表失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, [statusFilter]);

  // 生成新規則
  const handleGenerateRules = async () => {
    setLoading(true);
    try {
      const response = await ruleManagementAPI.generateRules(0.8);
      if (response.success) {
        message.success('規則生成成功');
        await loadDrafts(); // 重新載入列表
      }
    } catch (error) {
      message.error('生成規則失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 處理搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
    // TODO: 實現搜索功能
  };

  // 篩選顯示的草稿
  const filteredDrafts = drafts.filter(draft => {
    if (searchText) {
      return draft.description?.toLowerCase().includes(searchText.toLowerCase()) ||
             draft.draft_id.toLowerCase().includes(searchText.toLowerCase());
    }
    return true;
  });

  return (
    <div className="rule-draft-list">
      <Card className="list-header">
        <div className="header-content">
          <h2>
            <FileTextOutlined /> 規則管理中心
          </h2>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleGenerateRules}
              loading={loading}
            >
              生成新規則
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadDrafts}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </div>

        <div className="filter-bar">
          <Space>
            <Select
              style={{ width: 150 }}
              placeholder="篩選狀態"
              allowClear
              onChange={(value) => setStatusFilter(value || '')}
            >
              <Option value="">全部</Option>
              <Option value={DraftStatus.PENDING_REVIEW}>待審查</Option>
              <Option value={DraftStatus.IN_REVIEW}>審查中</Option>
              <Option value={DraftStatus.APPROVED}>已批准</Option>
              <Option value={DraftStatus.REJECTED}>已拒絕</Option>
            </Select>

            <Search
              placeholder="搜索規則集..."
              onSearch={handleSearch}
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
          </Space>
        </div>
      </Card>

      <div className="draft-list-content">
        {loading ? (
          <div className="loading-container">
            <Spin size="large" tip="載入中..." />
          </div>
        ) : filteredDrafts.length === 0 ? (
          <Empty
            description="暫無規則草稿"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={handleGenerateRules}>
              生成第一個規則集
            </Button>
          </Empty>
        ) : (
          <div className="draft-grid">
            {filteredDrafts.map(draft => (
              <RuleDraftCard
                key={draft.draft_id}
                draft={draft}
                onView={() => navigate(`/proofreading/draft/${draft.draft_id}`)}
                onRefresh={loadDrafts}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RuleDraftList;
