import { useState, type FC } from 'react';
import {
  Card,
  Button,
  Input,
  Space,
  Divider,
  Alert,
  Spin,
  Empty,
  message,
  Tabs,
  Select,
  Checkbox
} from 'antd';
import {
  PlayCircleOutlined,
  ClearOutlined,
  DownloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { DraftRule, TestResult } from '../../../types/proofreading';
import ruleManagementAPI from '../../../services/ruleManagementAPI';
import TestResults from './TestResults';
import DiffViewer from './DiffViewer';
import './TestPanel.css';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Option } = Select;

interface TestPanelProps {
  rules: DraftRule[];
  draftId: string;
}

const TestPanel: FC<TestPanelProps> = ({ rules, draftId }) => {
  const [testContent, setTestContent] = useState('');
  const [testResults, setTestResults] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedRules, setSelectedRules] = useState<string[]>([]);
  const [testOptions, setTestOptions] = useState({
    show_step_by_step: true,
    apply_conditions: true,
    highlight_changes: true
  });

  // 預設測試文本
  const sampleTexts = [
    {
      label: '一般文章',
      content: '這篇文章包含一些錯別字，因此需要校對。另外，文中有許多不規範的標點符號使用，例如：中英文混合時的標點。'
    },
    {
      label: '正式文件',
      content: '根據本公司之規定，所有員工應遵守以下條款。因此，違反規定者將受到相應處罰。'
    },
    {
      label: '技術文檔',
      content: 'API 介面返回 JSON 格式的數據，包含 status 和 data 兩個欄位。錯誤時會返回 error 訊息。'
    }
  ];

  // 執行測試
  const handleTest = async () => {
    if (!testContent.trim()) {
      message.warning('請輸入測試文本');
      return;
    }

    setLoading(true);
    try {
      // 確定要測試的規則
      const rulesToTest = selectedRules.length > 0
        ? rules.filter(r => selectedRules.includes(r.rule_id))
        : rules;

      const response = await ruleManagementAPI.testRules(
        rulesToTest,
        testContent
      );

      if (response.success) {
        setTestResults(response.data);
        message.success('測試完成');
      }
    } catch (error) {
      message.error('測試失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 清空測試
  const handleClear = () => {
    setTestContent('');
    setTestResults(null);
    setSelectedRules([]);
  };

  // 導出測試結果
  const handleExport = () => {
    if (!testResults) {
      message.warning('暫無測試結果可導出');
      return;
    }

    const exportData = {
      timestamp: new Date().toISOString(),
      draft_id: draftId,
      test_content: testContent,
      results: testResults,
      rules_tested: selectedRules.length || rules.length
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-results-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    message.success('測試結果已導出');
  };

  // 載入範例文本
  const loadSampleText = (content: string) => {
    setTestContent(content);
    setTestResults(null);
  };

  return (
    <div className="test-panel">
      <Card
        title="規則測試面板"
        extra={
          <Space>
            <Button
              icon={<SettingOutlined />}
              onClick={() => {
                // 可以打開設定對話框
              }}
            >
              測試設定
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={!testResults}
            >
              導出結果
            </Button>
          </Space>
        }
      >
        <div className="test-content">
          {/* 規則選擇 */}
          <div className="rule-selection">
            <h4>選擇要測試的規則</h4>
            <Alert
              message={
                selectedRules.length === 0
                  ? '未選擇規則時將測試所有規則'
                  : `已選擇 ${selectedRules.length} 個規則`
              }
              type="info"
              showIcon
            />
            <div className="rule-checkboxes">
              <Checkbox.Group
                value={selectedRules}
                onChange={setSelectedRules}
                style={{ width: '100%', marginTop: 10 }}
              >
                <Space direction="vertical">
                  {rules.map(rule => (
                    <Checkbox key={rule.rule_id} value={rule.rule_id}>
                      規則 #{rule.rule_id}: {rule.natural_language}
                    </Checkbox>
                  ))}
                </Space>
              </Checkbox.Group>
            </div>
          </div>

          <Divider />

          {/* 測試文本輸入 */}
          <div className="test-input">
            <div className="input-header">
              <h4>輸入測試文本</h4>
              <Select
                placeholder="載入範例文本"
                style={{ width: 200 }}
                onChange={(value) => {
                  const sample = sampleTexts.find(s => s.label === value);
                  if (sample) loadSampleText(sample.content);
                }}
              >
                {sampleTexts.map(sample => (
                  <Option key={sample.label} value={sample.label}>
                    {sample.label}
                  </Option>
                ))}
              </Select>
            </div>
            <TextArea
              rows={8}
              value={testContent}
              onChange={(e) => setTestContent(e.target.value)}
              placeholder="輸入或貼上要測試的文本..."
            />
          </div>

          {/* 測試選項 */}
          <div className="test-options">
            <Space>
              <Checkbox
                checked={testOptions.show_step_by_step}
                onChange={(e) => setTestOptions({
                  ...testOptions,
                  show_step_by_step: e.target.checked
                })}
              >
                顯示逐步處理過程
              </Checkbox>
              <Checkbox
                checked={testOptions.apply_conditions}
                onChange={(e) => setTestOptions({
                  ...testOptions,
                  apply_conditions: e.target.checked
                })}
              >
                應用條件限制
              </Checkbox>
              <Checkbox
                checked={testOptions.highlight_changes}
                onChange={(e) => setTestOptions({
                  ...testOptions,
                  highlight_changes: e.target.checked
                })}
              >
                高亮顯示變更
              </Checkbox>
            </Space>
          </div>

          {/* 操作按鈕 */}
          <div className="test-actions">
            <Space>
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleTest}
                loading={loading}
              >
                執行測試
              </Button>
              <Button
                size="large"
                icon={<ClearOutlined />}
                onClick={handleClear}
                disabled={loading}
              >
                清空
              </Button>
            </Space>
          </div>
        </div>
      </Card>

      {/* 測試結果 */}
      {loading && (
        <Card style={{ marginTop: 20, textAlign: 'center' }}>
          <Spin size="large" tip="正在執行測試..." />
        </Card>
      )}

      {!loading && testResults && (
        <Card style={{ marginTop: 20 }} title="測試結果">
          <Tabs defaultActiveKey="1">
            <TabPane tab="結果概覽" key="1">
              <TestResults results={testResults} />
            </TabPane>
            <TabPane tab="差異對比" key="2">
              <DiffViewer
                original={testResults.original}
                modified={testResults.result}
                changes={testResults.changes}
              />
            </TabPane>
            <TabPane tab="詳細報告" key="3">
              <div className="detailed-report">
                <h4>執行統計</h4>
                <ul>
                  <li>執行時間: {testResults.execution_time_ms}ms</li>
                  <li>變更數量: {testResults.changes.length}</li>
                  <li>測試規則數: {selectedRules.length || rules.length}</li>
                </ul>

                <h4>變更詳情</h4>
                {testResults.changes.length === 0 ? (
                  <Empty description="沒有發現需要修改的內容" />
                ) : (
                  <div className="changes-list">
                    {testResults.changes.map((change, index) => (
                      <Card key={index} size="small" style={{ marginBottom: 10 }}>
                        <div>
                          <strong>規則 #{change.rule_id}</strong>
                        </div>
                        <div>類型: {change.type}</div>
                        <div>
                          位置: [{change.position[0]}-{change.position[1]}]
                        </div>
                        <div>
                          原文: <code>{change.original}</code>
                        </div>
                        <div>
                          替換: <code>{change.replacement}</code>
                        </div>
                        <div>
                          置信度: {Math.round(change.confidence * 100)}%
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </TabPane>
          </Tabs>
        </Card>
      )}
    </div>
  );
};

export default TestPanel;
