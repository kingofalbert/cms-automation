import React from 'react';
import { Card, Alert, Tag, Empty } from 'antd';
import { CodeOutlined } from '@ant-design/icons';
import './CodePreview.css';

export interface GeneratedRulePreviewCondition {
  type: string;
  value: unknown;
}

export interface GeneratedRulePreview {
  pattern?: string;
  replacement?: string;
  confidence?: number;
  conditions?: GeneratedRulePreviewCondition[];
}

interface CodePreviewProps {
  code: GeneratedRulePreview | null;
  naturalLanguage: string;
}

const CodePreview: React.FC<CodePreviewProps> = ({ code, naturalLanguage }) => {
  // 格式化代碼顯示
  const formatCode = (obj: GeneratedRulePreview | null): string => {
    if (!obj) return '{}';
    return JSON.stringify(obj, null, 2);
  };

  if (!code && !naturalLanguage) {
    return (
      <Empty
        description="請先輸入自然語言描述"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <div className="code-preview">
      <Alert
        message="自動生成的規則代碼"
        description="系統根據您的自然語言描述自動生成以下規則代碼。您可以查看並確認代碼是否符合預期。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {naturalLanguage && (
        <Card
          size="small"
          title={
            <span>
              <CodeOutlined /> 自然語言輸入
            </span>
          }
          style={{ marginBottom: 16 }}
        >
          <p className="natural-language-display">{naturalLanguage}</p>
        </Card>
      )}

      {code && (
        <>
          <Card
            size="small"
            title={
              <span>
                <CodeOutlined /> 生成的規則代碼
              </span>
            }
            extra={
              <Tag color="blue">
                置信度: {Math.round((code.confidence || 0.85) * 100)}%
              </Tag>
            }
          >
            <pre className="code-display">
              <code>{formatCode(code)}</code>
            </pre>
          </Card>

          <div className="code-explanation">
            <h4>代碼說明：</h4>
            <ul>
              {code.pattern && (
                <li>
                  <strong>匹配模式 (pattern):</strong> {code.pattern}
                  <br />
                  <small>系統會搜索符合此模式的文本</small>
                </li>
              )}
              {code.replacement && (
                <li>
                  <strong>替換文本 (replacement):</strong> {code.replacement}
                  <br />
                  <small>匹配到的文本將被替換為此內容</small>
                </li>
              )}
              {code.conditions && code.conditions.length > 0 && (
                <li>
                  <strong>應用條件 (conditions):</strong>
                  <ul>
                    {code.conditions.map((cond: GeneratedRulePreviewCondition, index: number) => (
                      <li key={index}>
                        {cond.type}: {JSON.stringify(cond.value)}
                      </li>
                    ))}
                  </ul>
                  <small>只有滿足這些條件時，規則才會被應用</small>
                </li>
              )}
            </ul>
          </div>
        </>
      )}

      <div className="preview-footer">
        <Alert
          message="注意"
          description="生成的代碼可能需要進一步調整。保存後，系統會進行驗證並優化。"
          type="warning"
          showIcon
        />
      </div>
    </div>
  );
};

export default CodePreview;
