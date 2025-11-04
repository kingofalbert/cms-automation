/**
 * Generation progress component for real-time article generation status tracking.
 *
 * Displays the current status of a topic request as it progresses through:
 * pending → processing → completed/failed
 */

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader } from '../ui';
import { api } from '../../services/api-client';

interface TopicRequest {
  id: number;
  topic_description: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  article_id?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

interface GenerationProgressProps {
  topicRequestId: number;
  onComplete?: (articleId: number) => void;
  onError?: (error: string) => void;
}

export function GenerationProgress({
  topicRequestId,
  onComplete,
  onError,
}: GenerationProgressProps) {
  const [startTime] = useState(Date.now());
  const [elapsedTime, setElapsedTime] = useState(0);

  // Poll for status updates every 2 seconds when processing
  const { data: topicRequest, isLoading } = useQuery<TopicRequest>({
    queryKey: ['topic-request', topicRequestId],
    queryFn: async () => api.get<TopicRequest>(`/v1/topics/${topicRequestId}`),
    refetchInterval: (query) => {
      const currentStatus = query.state.data?.status;
      // Stop polling if completed, failed, or cancelled
      if (!currentStatus || ['completed', 'failed', 'cancelled'].includes(currentStatus)) {
        return false;
      }
      // Poll every 2 seconds while pending or processing
      return 2000;
    },
    enabled: !!topicRequestId,
  });

  // Update elapsed time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Handle completion
  useEffect(() => {
    if (topicRequest?.status === 'completed' && topicRequest.article_id) {
      onComplete?.(topicRequest.article_id);
    } else if (topicRequest?.status === 'failed' && topicRequest.error_message) {
      onError?.(topicRequest.error_message);
    }
  }, [topicRequest?.status, topicRequest?.article_id, topicRequest?.error_message, onComplete, onError]);

  const formatElapsedTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return {
          label: 'Queued',
          description: 'Your request is in the queue...',
          color: 'bg-gray-100 text-gray-800',
          icon: '⏳',
          progress: 10,
        };
      case 'processing':
        return {
          label: 'Generating',
          description: 'Claude is writing your article...',
          color: 'bg-blue-100 text-blue-800',
          icon: '✍️',
          progress: 50,
        };
      case 'completed':
        return {
          label: 'Completed',
          description: 'Article generated successfully!',
          color: 'bg-green-100 text-green-800',
          icon: '✅',
          progress: 100,
        };
      case 'failed':
        return {
          label: 'Failed',
          description: 'Generation failed. Please try again.',
          color: 'bg-red-100 text-red-800',
          icon: '❌',
          progress: 0,
        };
      case 'cancelled':
        return {
          label: 'Cancelled',
          description: 'Request was cancelled.',
          color: 'bg-gray-100 text-gray-800',
          icon: '🚫',
          progress: 0,
        };
      default:
        return {
          label: 'Unknown',
          description: 'Status unknown',
          color: 'bg-gray-100 text-gray-800',
          icon: '❓',
          progress: 0,
        };
    }
  };

  if (isLoading || !topicRequest) {
    return (
      <Card>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const statusInfo = getStatusInfo(topicRequest.status);

  return (
    <Card className="border-2 border-blue-200 shadow-md">
      <CardHeader
        title={
          <div className="flex items-center gap-2">
            <span className="text-2xl">{statusInfo.icon}</span>
            <span>Article Generation Progress</span>
          </div>
        }
        description={
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}
            >
              {statusInfo.label}
            </span>
            <span className="text-sm text-gray-500">
              Elapsed: {formatElapsedTime(elapsedTime)}
            </span>
          </div>
        }
      />
      <CardContent>
        {/* Progress bar */}
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${
                topicRequest.status === 'completed'
                  ? 'bg-green-600'
                  : topicRequest.status === 'failed'
                  ? 'bg-red-600'
                  : 'bg-blue-600'
              }`}
              style={{ width: `${statusInfo.progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">{statusInfo.description}</p>
        </div>

        {/* Topic description */}
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <p className="text-sm font-medium text-gray-700">Topic:</p>
          <p className="text-sm text-gray-600 mt-1">{topicRequest.topic_description}</p>
        </div>

        {/* Error message */}
        {topicRequest.status === 'failed' && topicRequest.error_message && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm font-medium text-red-800">Error:</p>
            <p className="text-sm text-red-600 mt-1">{topicRequest.error_message}</p>
          </div>
        )}

        {/* Success message */}
        {topicRequest.status === 'completed' && topicRequest.article_id && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-medium text-green-800">
              ✓ Article #{topicRequest.article_id} generated successfully!
            </p>
            <p className="text-sm text-green-600 mt-1">
              You can now view and edit your article below.
            </p>
          </div>
        )}

        {/* Processing animation */}
        {topicRequest.status === 'processing' && (
          <div className="flex items-center justify-center py-4">
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}

        {/* SLA warning (5 minutes) */}
        {topicRequest.status === 'processing' && elapsedTime > 240 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              ⚠️ This is taking longer than usual. Please be patient...
            </p>
          </div>
        )}

        {/* Timestamps */}
        <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500 space-y-1">
          <div>
            <span className="font-medium">Created:</span>{' '}
            {new Date(topicRequest.created_at).toLocaleString()}
          </div>
          {topicRequest.updated_at !== topicRequest.created_at && (
            <div>
              <span className="font-medium">Updated:</span>{' '}
              {new Date(topicRequest.updated_at).toLocaleString()}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
