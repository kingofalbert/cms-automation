/**
 * React Query hooks for topic request operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface TopicRequestCreate {
  topic_description: string;
  style_tone: string;
  target_word_count: number;
  outline?: string;
}

interface TopicRequest {
  id: number;
  topic_description: string;
  outline?: string;
  style_tone: string;
  target_word_count: number;
  priority: string;
  status: string;
  submitted_by: number;
  article_id?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export function useTopicRequests(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['topic-requests', skip, limit],
    queryFn: async () => {
      const response = await api.get<TopicRequest[]>('/v1/topics', {
        params: { skip, limit },
      });
      return response;
    },
  });
}

export function useTopicRequest(topicId: number) {
  return useQuery({
    queryKey: ['topic-request', topicId],
    queryFn: async () => {
      const response = await api.get<TopicRequest>(`/v1/topics/${topicId}`);
      return response;
    },
    enabled: !!topicId,
  });
}

export function useCreateTopicRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TopicRequestCreate) => {
      const response = await api.post<TopicRequest>('/v1/topics', data);
      return response;
    },
    onSuccess: () => {
      // Invalidate and refetch topic requests list
      queryClient.invalidateQueries({ queryKey: ['topic-requests'] });
    },
  });
}
