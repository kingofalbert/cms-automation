/**
 * CSV Upload Form component for batch article import.
 */

import { useState } from 'react';
import { DragDropZone } from './DragDropZone';
import { Button, Spinner } from '@/components/ui';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface CSVPreviewData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

export const CSVUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<CSVPreviewData | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const parseCSVPreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter((line) => line.trim());

      if (lines.length === 0) {
        alert('CSV 文件为空');
        return;
      }

      const headers = lines[0].split(',').map((h) => h.trim());
      const rows = lines
        .slice(1, 6) // Preview first 5 rows
        .map((line) => line.split(',').map((cell) => cell.trim()));

      setPreviewData({
        headers,
        rows,
        totalRows: lines.length - 1,
      });
    };

    reader.readAsText(file);
  };

  const handleFileAccepted = (files: File[]) => {
    const file = files[0];
    setSelectedFile(file);
    parseCSVPreview(file);
  };

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/v1/articles/import/batch', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(percentCompleted);
        },
      });

      return response.data;
    },
    onSuccess: (data) => {
      alert(
        `导入成功！\n总计: ${data.total}\n成功: ${data.success}\n失败: ${data.failed}`
      );
      setSelectedFile(null);
      setPreviewData(null);
      setUploadProgress(0);
    },
    onError: (error: any) => {
      alert(`导入失败: ${error.response?.data?.message || error.message}`);
      setUploadProgress(0);
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
    setUploadProgress(0);
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">CSV 格式要求</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>必填列：title（标题）、content（内容）</li>
          <li>可选列：excerpt（摘要）、tags（标签，用分号分隔）、categories（分类，用分号分隔）</li>
          <li>编码：UTF-8</li>
          <li>最大文件大小：10MB</li>
        </ul>
      </div>

      {/* File Upload */}
      {!selectedFile ? (
        <DragDropZone
          onFilesAccepted={handleFileAccepted}
          acceptedFileTypes={{ 'text/csv': ['.csv'] }}
          maxFiles={1}
          maxSize={10 * 1024 * 1024}
        />
      ) : (
        <>
          {/* File Info */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-green-900">{selectedFile.name}</p>
                <p className="text-sm text-green-700">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                移除
              </Button>
            </div>
          </div>

          {/* Preview */}
          {previewData && (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b">
                <p className="text-sm font-medium text-gray-700">
                  数据预览（前 5 行，共 {previewData.totalRows} 行）
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      {previewData.headers.map((header, idx) => (
                        <th
                          key={idx}
                          className="px-4 py-2 text-left font-semibold text-gray-700"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, rowIdx) => (
                      <tr key={rowIdx} className="border-t">
                        {row.map((cell, cellIdx) => (
                          <td key={cellIdx} className="px-4 py-2 text-gray-600">
                            {cell.length > 50
                              ? `${cell.substring(0, 50)}...`
                              : cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {uploadMutation.isPending && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700">上传中...</span>
                <span className="text-gray-700">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3">
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <>
                  <Spinner size="sm" variant="white" className="mr-2" />
                  上传中...
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
        </>
      )}
    </div>
  );
};
