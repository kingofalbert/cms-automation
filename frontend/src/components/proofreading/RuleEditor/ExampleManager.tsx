import React from 'react';
import { Form, Input, Button, Space, Card, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { Example } from '../../../types/proofreading';
import './ExampleManager.css';

interface ExampleManagerProps {
  examples: Example[];
  onChange: (examples: Example[]) => void;
}

const ExampleManager: React.FC<ExampleManagerProps> = ({ examples, onChange }) => {
  // 添加新示例
  const addExample = () => {
    onChange([
      ...examples,
      { before: '', after: '' }
    ]);
  };

  // 更新示例
  const updateExample = (index: number, field: 'before' | 'after', value: string) => {
    const newExamples = [...examples];
    newExamples[index] = {
      ...newExamples[index],
      [field]: value
    };
    onChange(newExamples);
  };

  // 刪除示例
  const removeExample = (index: number) => {
    onChange(examples.filter((_, i) => i !== index));
  };

  return (
    <div className="example-manager">
      <div className="manager-header">
        <h4>示例管理</h4>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={addExample}
          size="small"
        >
          添加示例
        </Button>
      </div>

      {examples.length === 0 ? (
        <Empty
          description="暫無示例"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button onClick={addExample}>添加第一個示例</Button>
        </Empty>
      ) : (
        <div className="examples-list">
          {examples.map((example, index) => (
            <Card
              key={index}
              size="small"
              title={`示例 ${index + 1}`}
              extra={
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeExample(index)}
                  size="small"
                />
              }
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Form.Item label="修改前">
                  <Input
                    value={example.before}
                    onChange={(e) => updateExample(index, 'before', e.target.value)}
                    placeholder="輸入原始文本..."
                  />
                </Form.Item>
                <Form.Item label="修改後">
                  <Input
                    value={example.after}
                    onChange={(e) => updateExample(index, 'after', e.target.value)}
                    placeholder="輸入修改後的文本..."
                  />
                </Form.Item>
              </Space>
            </Card>
          ))}
        </div>
      )}

      <div className="example-tips">
        <p>提示：提供多個示例可以幫助系統更好地理解規則意圖</p>
      </div>
    </div>
  );
};

export default ExampleManager;