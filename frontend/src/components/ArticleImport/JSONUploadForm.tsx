/**
 * JSON Upload Form component for batch article import.
 */

import { useState } from 'react';
import { DragDropZone } from './DragDropZone';
import { Button, Spinner } from '@/components/ui';
import { useMutation } from '@tanstack/react-query';
import axios, { type AxiosError } from 'axios';
import type { ImportResult } from '@/types/api';
import type { ArticleImportRequest } from '@/types/article';

interface JSONPreviewData {
  articles: ArticleImportRequest[];
  totalCount: number;
}

export const JSONUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<JSONPreviewData | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const isArticleImportRequest = (value: unknown): value is ArticleImportRequest => {
    if (!value || typeof value !== 'object') {
      return false;
    }
    const article = value as Partial<ArticleImportRequest>;
    return typeof article.title === 'string' && typeof article.content === 'string';
  };

  const parseJSONPreview = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text) as { articles?: unknown };

      if (!Array.isArray(data.articles)) {
        setParseError('JSON 格式错误：缺少 articles 数组');
        return;
      }

      const validArticles = data.articles.filter(isArticleImportRequest);

      if (validArticles.length === 0) {
        setParseError('没有有效的文章数据（必须包含 title 和 content）');
        return;
      }

      setPreviewData({
        articles: validArticles.slice(0, 5),
        totalCount: validArticles.length,
      });
      setParseError(null);
    } catch (error) {
      setParseError('JSON 解析失败：' + (error as Error).message);
    }
  };

  const handleFileAccepted = (files: File[]) => {
    const file = files[0];
    setSelectedFile(file);
    void parseJSONPreview(file);
  };

  const uploadMutation = useMutation<ImportResult, AxiosError<{ message?: string }>, File>({
    mutationFn: async (file: File) => {
      const text = await file.text();
      const payload = JSON.parse(text) as { articles?: unknown };

      if (!Array.isArray(payload.articles)) {
        throw new Error('JSON 格式错误：缺少 articles 数组');
      }

      const articles = payload.articles.filter(isArticleImportRequest);
      if (articles.length === 0) {
        throw new Error('没有有效的文章数据（必须包含 title 和 content）');
      }

      const response = await axios.post<ImportResult>(
        '/v1/articles/import/batch',
        { articles }
      );
      return response.data;
    },
    onSuccess: (data) => {
      alert(
        `导入成功！\n总计: ${data.total}\n成功: ${data.success}\n失败: ${data.failed}`
      );
      handleReset();
    },
    onError: (error) => {
      const message = error.response?.data?.message ?? error.message;
      alert(`导入失败: ${message}`);
    },
  });

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setParseError(null);
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">JSON 格式要求</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p>JSON 文件应包含一个 articles 数组，每个文章对象应包含：</p>
          <pre className="bg-blue-100 p-3 rounded font-mono text-xs overflow-x-auto">
{`{
  "articles": [
    {
      "title": "文章标题",
      "content": "文章内容",
      "excerpt": "摘要（可选）",
      "tags": ["标签1", "标签2"],
      "categories": ["分类1"]
    }
  ]
}`}
          </pre>
          <p>最大文件大小：10MB</p>
        </div>
      </div>

      {/* File Upload */}
      {!selectedFile ? (
        <DragDropZone
          onFilesAccepted={handleFileAccepted}
          acceptedFileTypes={{ 'application/json': ['.json'] }}
          maxFiles={1}
          maxSize={10 * 1024 * 1024}
        />
      ) : (
        <>
          {/* File Info */}
          <div className={`border rounded-lg p-4 ${parseError ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`font-medium ${parseError ? 'text-red-900' : 'text-green-900'}`}>
                  {selectedFile.name}
                </p>
                <p className={`text-sm ${parseError ? 'text-red-700' : 'text-green-700'}`}>
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                移除
              </Button>
            </div>
          </div>

          {/* Parse Error */}
          {parseError && (
            <div className="bg-red-100 border border-red-300 rounded-lg p-4">
              <p className="text-red-900 font-medium">解析错误</p>
              <p className="text-red-700 text-sm mt-1">{parseError}</p>
            </div>
          )}

          {/* Preview */}
          {previewData && !parseError && (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b">
                <p className="text-sm font-medium text-gray-700">
                  数据预览（前 5 篇，共 {previewData.totalCount} 篇）
                </p>
              </div>
              <div className="divide-y">
                {previewData.articles.map((article, idx) => (
                  <div key={idx} className="p-4 hover:bg-gray-50">
                    <h4 className="font-semibold text-gray-900">{article.title}</h4>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {article.content.substring(0, 150)}
                      {article.content.length > 150 && '...'}
                    </p>
                    {article.tags && article.tags.length > 0 && (
                      <div className="flex gap-2 mt-2">
                        {article.tags.map((tag, tagIdx) => (
                          <span
                            key={tagIdx}
                            className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          {!parseError && (
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? (
                  <>
                    <Spinner size="sm" variant="white" className="mr-2" />
                    导入中...
                  </>
                ) : (
                  '开始导入'
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={uploadMutation.isPending}
              >
                取消
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
