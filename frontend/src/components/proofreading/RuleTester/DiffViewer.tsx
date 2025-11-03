import React, { useMemo } from 'react';
import { Card, Tag, Switch, Space, Alert } from 'antd';
import { DiffOutlined, EyeOutlined } from '@ant-design/icons';
import './DiffViewer.css';

interface DiffViewerProps {
  original: string;
  modified: string;
  changes: Array<{
    rule_id: string;
    type: string;
    position: [number, number];
    original: string;
    replacement: string;
    confidence: number;
  }>;
}

const DiffViewer: React.FC<DiffViewerProps> = ({ original, modified, changes }) => {
  const [showInline, setShowInline] = React.useState(true);
  const [highlightChanges, setHighlightChanges] = React.useState(true);

  // 生成帶高亮的文本
  const generateHighlightedText = useMemo(() => {
    if (!highlightChanges || changes.length === 0) {
      return { original, modified };
    }

    // 對變更按位置排序
    const sortedChanges = [...changes].sort((a, b) => a.position[0] - b.position[0]);

    // 生成原始文本的高亮版本
    let highlightedOriginal = '';
    let lastPos = 0;

    sortedChanges.forEach(change => {
      // 添加未改變的部分
      highlightedOriginal += original.substring(lastPos, change.position[0]);
      // 添加被刪除的部分（紅色高亮）
      highlightedOriginal += `<span class="diff-removed">${original.substring(change.position[0], change.position[1])}</span>`;
      lastPos = change.position[1];
    });
    // 添加剩餘部分
    highlightedOriginal += original.substring(lastPos);

    // 生成修改後文本的高亮版本
    let highlightedModified = modified;
    sortedChanges.forEach(change => {
      const regex = new RegExp(change.replacement, 'g');
      highlightedModified = highlightedModified.replace(regex,
        `<span class="diff-added">${change.replacement}</span>`
      );
    });

    return {
      original: highlightedOriginal,
      modified: highlightedModified
    };
  }, [original, modified, changes, highlightChanges]);

  // 計算文本差異統計
  const diffStats = useMemo(() => {
    const lines1 = original.split('\n');
    const lines2 = modified.split('\n');
    const changedLines = new Set<number>();

    changes.forEach(change => {
      const lineNum = original.substring(0, change.position[0]).split('\n').length - 1;
      changedLines.add(lineNum);
    });

    return {
      originalLines: lines1.length,
      modifiedLines: lines2.length,
      changedLines: changedLines.size,
      additions: Math.max(0, lines2.length - lines1.length),
      deletions: Math.max(0, lines1.length - lines2.length)
    };
  }, [original, modified, changes]);

  return (
    <div className="diff-viewer">
      {/* 控制選項 */}
      <Card className="viewer-controls">
        <Space>
          <span>顯示模式:</span>
          <Switch
            checkedChildren="內聯"
            unCheckedChildren="並排"
            checked={showInline}
            onChange={setShowInline}
          />
          <span>高亮變更:</span>
          <Switch
            checked={highlightChanges}
            onChange={setHighlightChanges}
          />
        </Space>
        <div className="diff-stats">
          <Tag color="green">+{diffStats.additions} 行</Tag>
          <Tag color="red">-{diffStats.deletions} 行</Tag>
          <Tag color="orange">~{diffStats.changedLines} 行變更</Tag>
        </div>
      </Card>

      {/* 差異顯示 */}
      {showInline ? (
        // 內聯顯示模式
        <div className="inline-diff">
          <Card title={
            <span><DiffOutlined /> 變更對比（內聯模式）</span>
          }>
            <Alert
              message="使用說明"
              description="紅色背景表示被刪除的內容，綠色背景表示新增的內容"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <div className="diff-content">
              <div
                className="diff-text"
                dangerouslySetInnerHTML={{
                  __html: generateHighlightedText.modified
                }}
              />
            </div>
          </Card>
        </div>
      ) : (
        // 並排顯示模式
        <div className="side-by-side-diff">
          <div className="diff-column">
            <Card
              title={<span><EyeOutlined /> 原始文本</span>}
              className="diff-card"
            >
              <div
                className="diff-text"
                dangerouslySetInnerHTML={{
                  __html: generateHighlightedText.original
                }}
              />
            </Card>
          </div>
          <div className="diff-column">
            <Card
              title={<span><EyeOutlined /> 修改後文本</span>}
              className="diff-card"
            >
              <div
                className="diff-text"
                dangerouslySetInnerHTML={{
                  __html: generateHighlightedText.modified
                }}
              />
            </Card>
          </div>
        </div>
      )}

      {/* 變更詳情 */}
      {changes.length > 0 && (
        <Card title="變更詳情" style={{ marginTop: 16 }}>
          <div className="change-details">
            {changes.map((change, index) => (
              <div key={index} className="change-item">
                <div className="change-header">
                  <Tag color="purple">規則 #{change.rule_id}</Tag>
                  <Tag color="blue">{change.type}</Tag>
                  <Tag color={
                    change.confidence >= 0.9 ? 'green' :
                    change.confidence >= 0.7 ? 'blue' : 'orange'
                  }>
                    置信度: {Math.round(change.confidence * 100)}%
                  </Tag>
                </div>
                <div className="change-content">
                  <span className="change-label">位置:</span>
                  <span>[{change.position[0]}-{change.position[1]}]</span>
                  <span className="change-label">原文:</span>
                  <code className="diff-removed">{change.original}</code>
                  <span className="change-arrow">→</span>
                  <code className="diff-added">{change.replacement}</code>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default DiffViewer;