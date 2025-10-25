/**
 * Article Generator page - main interface for article generation workflow.
 */

import { useState } from 'react';
import { ArticlePreview } from '../components/ArticleGenerator/ArticlePreview';
import { TopicSubmissionForm } from '../components/ArticleGenerator/TopicSubmissionForm';
import { Button } from '../components/ui';
import { useArticles } from '../hooks/useArticles';
import { useCreateTopicRequest } from '../hooks/useTopicRequests';

interface TopicFormData {
  topic_description: string;
  style_tone: string;
  target_word_count: number;
  outline?: string;
}

export default function ArticleGeneratorPage() {
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(true);

  const { data: articles, isLoading: articlesLoading, refetch: refetchArticles } = useArticles(0, 10);
  const createTopicMutation = useCreateTopicRequest();

  const handleSubmitTopic = async (data: TopicFormData) => {
    try {
      await createTopicMutation.mutateAsync(data);
      // Poll for new articles after submission
      setTimeout(() => {
        refetchArticles();
      }, 3000);
    } catch (error) {
      console.error('Failed to submit topic:', error);
    }
  };

  const handleViewArticle = (articleId: number) => {
    setSelectedArticleId(articleId);
    setShowForm(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Article Generator</h1>
        <p className="mt-2 text-gray-600">
          Generate AI-powered articles using Claude. Submit a topic and let AI create comprehensive content.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Topic submission form */}
        <div className="lg:col-span-1">
          {showForm && (
            <TopicSubmissionForm
              onSubmit={handleSubmitTopic}
              isLoading={createTopicMutation.isPending}
            />
          )}

          {createTopicMutation.isSuccess && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                Topic submitted successfully! Article generation started in the background.
              </p>
            </div>
          )}

          {createTopicMutation.isError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                Failed to submit topic. Please try again.
              </p>
            </div>
          )}
        </div>

        {/* Right column - Generated articles */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">Generated Articles</h2>
            <Button
              variant="outline"
              onClick={() => refetchArticles()}
              disabled={articlesLoading}
            >
              Refresh
            </Button>
          </div>

          {articlesLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading articles...</p>
            </div>
          ) : articles && articles.length > 0 ? (
            <div className="space-y-4">
              {articles.map((article) => (
                <ArticlePreview
                  key={article.id}
                  article={article}
                  onView={handleViewArticle}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No articles yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by submitting a topic for article generation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
