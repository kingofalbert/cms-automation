import { useState, useEffect, type FC } from 'react';
import {
  Modal,
  Input,
  Button,
  Space,
  Form,
  Checkbox,
  Tag,
  Divider,
  Alert,
  Tabs,
  Card,
  message
} from 'antd';
import {
  SaveOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { DraftRule, Example, TestResult } from '../../../types/proofreading';
import ruleManagementAPI from '../../../services/ruleManagementAPI';
import CodePreview, { type GeneratedRulePreview } from './CodePreview';
import ExampleManager from './ExampleManager';
import './NaturalLanguageEditor.css';

const { TextArea } = Input;
const { TabPane } = Tabs;

interface NaturalLanguageEditorProps {
  visible: boolean;
  rule: DraftRule | null;
  draftId: string;
  onSave: (rule: DraftRule) => void;
  onCancel: () => void;
}

const NaturalLanguageEditor: FC<NaturalLanguageEditorProps> = ({
  visible,
  rule,
  draftId,
  onSave,
  onCancel
}) => {
  const [form] = Form.useForm();
  const [naturalLanguage, setNaturalLanguage] = useState('');
  const [examples, setExamples] = useState<Example[]>([]);
  const [conditions, setConditions] = useState<Record<string, boolean>>({
    'only_informal': false,
    'paragraph_start': false,
    'ignore_quotes': false,
    'case_sensitive': false
  });
  const [generatedCode, setGeneratedCode] = useState<GeneratedRulePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [testContent, setTestContent] = useState('');
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  useEffect(() => {
    if (!rule) {
      return;
    }

    setNaturalLanguage(rule.natural_language);
    setExamples(rule.examples || []);
    if (rule.conditions) {
      setConditions((prev) => ({
        ...prev,
        ...rule.conditions,
      }));
    }
    form.setFieldsValue({
      natural_language: rule.natural_language,
    });
  }, [rule, form]);

  // 生成規則代碼預覽
  const generateCodePreview = () => {
    // 模擬從自然語言生成代碼
    // 實際應用中，這裡會調用後端 API
    const code: GeneratedRulePreview = {
      pattern: extractPattern(naturalLanguage),
      replacement: extractReplacement(naturalLanguage),
      conditions: Object.entries(conditions)
        .filter(([_, value]) => value)
        .map(([key]) => ({ type: key, value: true })),
      confidence: 0.85
    };
    setGeneratedCode(code);
  };

  // 從自然語言提取模式（簡化示例）
  const extractPattern = (text: string): string => {
    const patterns = [
      { keyword: '當看到', extract: /當看到「(.+?)」/ },
      { keyword: '當遇到', extract: /當遇到「(.+?)」/ },
      { keyword: '如果有', extract: /如果有「(.+?)」/ }
    ];

    for (const { keyword, extract } of patterns) {
      if (text.includes(keyword)) {
        const match = text.match(extract);
        if (match) return match[1];
      }
    }
    return '';
  };

  // 從自然語言提取替換文本（簡化示例）
  const extractReplacement = (text: string): string => {
    const patterns = [
      { keyword: '建議改為', extract: /建議改為「(.+?)」/ },
      { keyword: '替換為', extract: /替換為「(.+?)」/ },
      { keyword: '改成', extract: /改成「(.+?)」/ }
    ];

    for (const { keyword, extract } of patterns) {
      if (text.includes(keyword)) {
        const match = text.match(extract);
        if (match) return match[1];
      }
    }
    return '';
  };

  // 測試規則
  const handleTest = async () => {
    if (!testContent) {
      message.warning('請輸入測試文本');
      return;
    }

    setLoading(true);
    try {
      const testRule = {
        ...rule,
        natural_language: naturalLanguage,
        examples,
        conditions
      } as DraftRule;

      const response = await ruleManagementAPI.testRules([testRule], testContent);
      if (response.success) {
        setTestResult(response.data);
        message.success('測試完成');
      }
    } catch (error) {
      message.error('測試失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 保存修改
  const handleSave = async () => {
    if (!rule) return;

    try {
      await form.validateFields();

      setLoading(true);
      const response = await ruleManagementAPI.updateRule(
        draftId,
        rule.rule_id,
        {
          natural_language: naturalLanguage,
          examples,
          conditions
        }
      );

      if (response.success) {
        message.success('規則已更新');
        onSave({
          ...rule,
          natural_language: naturalLanguage,
          examples,
          conditions
        });
      }
    } catch (error) {
      message.error('保存失敗');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={`編輯規則 #${rule?.rule_id || ''}`}
      visible={visible}
      onCancel={onCancel}
      width={900}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button
          key="test"
          icon={<ExperimentOutlined />}
          onClick={handleTest}
          loading={loading}
        >
          測試規則
        </Button>,
        <Button
          key="save"
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={loading}
        >
          保存修改
        </Button>
      ]}
    >
      <Tabs defaultActiveKey="1">
        <TabPane tab="自然語言編輯" key="1">
          <Form form={form} layout="vertical">
            <Form.Item
              label="使用自然語言描述規則"
              name="natural_language"
              rules={[{ required: true, message: '請輸入規則描述' }]}
            >
              <TextArea
                rows={4}
                value={naturalLanguage}
                onChange={(e) => {
                  setNaturalLanguage(e.target.value);
                  generateCodePreview();
                }}
                placeholder="例如：當看到「因此」在段落開頭時，建議改為「所以」，但如果是正式文件則保留原樣。"
              />
            </Form.Item>

            <Alert
              message="提示"
              description="請用清晰的中文描述規則，系統會自動轉換為可執行的代碼。描述時請包含：何時應用規則、如何修改、特殊條件等。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Divider>應用條件</Divider>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Checkbox
                checked={conditions.only_informal}
                onChange={(e) => setConditions({
                  ...conditions,
                  only_informal: e.target.checked
                })}
              >
                只在非正式文檔中應用
              </Checkbox>
              <Checkbox
                checked={conditions.paragraph_start}
                onChange={(e) => setConditions({
                  ...conditions,
                  paragraph_start: e.target.checked
                })}
              >
                只在段落開頭應用
              </Checkbox>
              <Checkbox
                checked={conditions.ignore_quotes}
                onChange={(e) => setConditions({
                  ...conditions,
                  ignore_quotes: e.target.checked
                })}
              >
                忽略引用內容
              </Checkbox>
              <Checkbox
                checked={conditions.case_sensitive}
                onChange={(e) => setConditions({
                  ...conditions,
                  case_sensitive: e.target.checked
                })}
              >
                區分大小寫
              </Checkbox>
            </Space>
          </Form>
        </TabPane>

        <TabPane tab="示例管理" key="2">
          <ExampleManager
            examples={examples}
            onChange={setExamples}
          />
        </TabPane>

        <TabPane tab="代碼預覽" key="3">
          <CodePreview
            code={generatedCode}
            naturalLanguage={naturalLanguage}
          />
        </TabPane>

        <TabPane tab="規則測試" key="4">
          <div className="test-panel">
            <Form.Item label="輸入測試文本">
              <TextArea
                rows={4}
                value={testContent}
                onChange={(e) => setTestContent(e.target.value)}
                placeholder="輸入要測試的文本..."
              />
            </Form.Item>

            {testResult && (
              <Card title="測試結果" style={{ marginTop: 16 }}>
                <div className="test-result">
                  <div className="result-section">
                    <strong>原始文本:</strong>
                    <pre>{testResult.original}</pre>
                  </div>
                  <div className="result-section">
                    <strong>修改後:</strong>
                    <pre>{testResult.result}</pre>
                  </div>
                  {testResult.changes.length > 0 && (
                    <div className="changes-section">
                      <strong>變更詳情:</strong>
                      {testResult.changes.map((change, index) => (
                        <div key={index} className="change-item">
                          <Tag color="blue">{change.type}</Tag>
                          <span>
                            位置 [{change.position[0]}-{change.position[1]}]:
                            "{change.original}" → "{change.replacement}"
                          </span>
                          <Tag color="green">置信度: {Math.round(change.confidence * 100)}%</Tag>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="execution-time">
                    執行時間: {testResult.execution_time_ms}ms
                  </div>
                </div>
              </Card>
            )}
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default NaturalLanguageEditor;
