import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, message, Spin } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { DraftRule } from '../types/proofreading';
import ruleManagementAPI from '../services/ruleManagementAPI';
import TestPanel from '../components/proofreading/RuleTester/TestPanel';
import './RuleTestPage.css';

const RuleTestPage: React.FC = () => {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();
  const [rules, setRules] = useState<DraftRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [draftDescription, setDraftDescription] = useState('');

  useEffect(() => {
    loadDraftRules();
  }, [draftId]);

  const loadDraftRules = async () => {
    if (!draftId) return;

    setLoading(true);
    try {
      const response = await ruleManagementAPI.getDraftDetail(draftId);
      if (response.success) {
        setRules(response.data.rules);
        setDraftDescription(response.data.description || draftId);
      }
    } catch (error) {
      message.error('載入規則失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="載入規則中..." />
      </div>
    );
  }

  return (
    <div className="rule-test-page">
      <div className="test-page-header">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/proofreading/draft/${draftId}`)}
        >
          返回規則詳情
        </Button>
        <h2>測試規則集: {draftDescription}</h2>
      </div>

      {rules.length > 0 ? (
        <TestPanel rules={rules} draftId={draftId || ''} />
      ) : (
        <div className="no-rules-message">
          沒有可測試的規則
        </div>
      )}
    </div>
  );
};

export default RuleTestPage;