/**
 * Topic submission form component for article generation.
 */

import { useForm } from 'react-hook-form';
import { Button, Card, CardContent, CardHeader } from '../ui';

interface TopicFormData {
  topic_description: string;
  style_tone: string;
  target_word_count: number;
  outline?: string;
}

interface TopicSubmissionFormProps {
  onSubmit: (data: TopicFormData) => void;
  isLoading?: boolean;
}

export function TopicSubmissionForm({ onSubmit, isLoading = false }: TopicSubmissionFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<TopicFormData>({
    defaultValues: {
      topic_description: '',
      style_tone: 'professional',
      target_word_count: 1000,
      outline: '',
    },
  });

  const handleFormSubmit = (data: TopicFormData) => {
    onSubmit(data);
    reset();
  };

  return (
    <Card>
      <CardHeader title="Generate New Article" description="Submit a topic for AI-powered article generation" />
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Topic Description <span className="text-error-500">*</span>
            </label>
            <textarea
              {...register('topic_description', {
                required: 'Topic description is required',
                minLength: { value: 10, message: 'Minimum 10 characters required' },
                maxLength: { value: 5000, message: 'Maximum 5000 characters allowed' },
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 min-h-[100px]"
              placeholder="Describe the article topic you want to generate..."
              disabled={isLoading}
            />
            {errors.topic_description && (
              <p className="text-sm text-error-600 mt-1">{errors.topic_description.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Writing Style</label>
              <select
                {...register('style_tone')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isLoading}
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="technical">Technical</option>
                <option value="academic">Academic</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Word Count</label>
              <input
                type="number"
                {...register('target_word_count', {
                  min: { value: 100, message: 'Minimum 100 words' },
                  max: { value: 10000, message: 'Maximum 10,000 words' },
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isLoading}
              />
              {errors.target_word_count && (
                <p className="text-sm text-error-600 mt-1">{errors.target_word_count.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Outline (Optional)
            </label>
            <textarea
              {...register('outline')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 min-h-[80px]"
              placeholder="Optional: Provide a structured outline for the article..."
              disabled={isLoading}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => reset()}
              disabled={isLoading}
            >
              Clear
            </Button>
            <Button type="submit" isLoading={isLoading}>
              Generate Article
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
