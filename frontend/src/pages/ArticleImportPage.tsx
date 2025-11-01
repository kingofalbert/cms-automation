/**
 * Article Import Page
 * Supports CSV, JSON, and manual article import.
 */

import { Tabs, TabsList, TabsTrigger, TabsContent, Card } from '@/components/ui';
import { CSVUploadForm } from '@/components/ArticleImport/CSVUploadForm';
import { JSONUploadForm } from '@/components/ArticleImport/JSONUploadForm';
import { ManualArticleForm } from '@/components/ArticleImport/ManualArticleForm';
import { ImportHistoryTable } from '@/components/ArticleImport/ImportHistoryTable';

export default function ArticleImportPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">导入文章</h1>
        <p className="mt-2 text-gray-600">
          支持 CSV 批量导入、JSON 导入和手动输入
        </p>
      </div>

      {/* Import Tabs */}
      <Card className="mb-8">
        <Tabs defaultValue="csv">
          <div className="border-b px-6 py-4">
            <TabsList>
              <TabsTrigger value="csv">CSV 导入</TabsTrigger>
              <TabsTrigger value="json">JSON 导入</TabsTrigger>
              <TabsTrigger value="manual">手动输入</TabsTrigger>
            </TabsList>
          </div>

          <div className="p-6">
            <TabsContent value="csv">
              <CSVUploadForm />
            </TabsContent>

            <TabsContent value="json">
              <JSONUploadForm />
            </TabsContent>

            <TabsContent value="manual">
              <ManualArticleForm />
            </TabsContent>
          </div>
        </Tabs>
      </Card>

      {/* Import History */}
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">导入历史</h2>
        <Card>
          <ImportHistoryTable />
        </Card>
      </div>
    </div>
  );
}
