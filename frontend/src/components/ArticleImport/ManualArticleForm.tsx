/**
 * Manual Article Form component.
 * Allows users to manually input article data with rich text editing.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input, Textarea, Button, Spinner } from '@/components/ui';
import { RichTextEditor } from './RichTextEditor';
import { ImageUploadWidget, UploadedImage } from './ImageUploadWidget';
import { useMutation } from '@tanstack/react-query';
import axios, { type AxiosError } from 'axios';
import type { Article } from '@/types/api';
import type { ArticleImportRequest } from '@/types/article';

const articleSchema = z.object({
  title: z.string().min(1, '標題不能為空').max(200, '標題最多 200 字符'),
  excerpt: z.string().max(500, '摘要最多 500 字符').optional(),
  tags: z.string().optional(),
  categories: z.string().optional(),
});

type ArticleFormData = z.infer<typeof articleSchema>;

export const ManualArticleForm: React.FC = () => {
  const [content, setContent] = useState('');
  const [images, setImages] = useState<UploadedImage[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ArticleFormData>({
    resolver: zodResolver(articleSchema),
  });

  const excerptValue = watch('excerpt');

  const importMutation = useMutation<Article, AxiosError<{ message?: string }>, ArticleImportRequest>({
    mutationFn: async (data: ArticleImportRequest) => {
      const formData = new FormData();
      formData.append('title', data.title);
      formData.append('content', data.content);

      if (data.excerpt) {
        formData.append('excerpt', data.excerpt);
      }

      if (data.tags && data.tags.length > 0) {
        formData.append('tags', JSON.stringify(data.tags));
      }

      if (data.categories && data.categories.length > 0) {
        formData.append('categories', JSON.stringify(data.categories));
      }

      // Add images
      if (data.images && data.images.length > 0) {
        data.images.forEach((image, index) => {
          formData.append('images', image);
          if (images[index].altText) {
            formData.append(`alt_text_${index}`, images[index].altText);
          }
          if (images[index].isFeatured) {
            formData.append('featured_image_index', index.toString());
          }
        });
      }

      const response = await axios.post<Article>('v1/articles/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      return response.data;
    },
    onSuccess: (data) => {
      alert(`文章創建成功！ID: ${data.id}`);
      handleReset();
    },
    onError: (error) => {
      const message = error.response?.data?.message ?? error.message;
      alert(`創建失敗: ${message}`);
    },
  });

  const onSubmit = (data: ArticleFormData) => {
    if (!content || content.trim() === '') {
      alert('文章內容不能為空');
      return;
    }

    const articleData: ArticleImportRequest = {
      title: data.title,
      content,
      excerpt: data.excerpt,
      tags: data.tags
        ? data.tags.split(',').map((t) => t.trim()).filter(Boolean)
        : undefined,
      categories: data.categories
        ? data.categories.split(',').map((c) => c.trim()).filter(Boolean)
        : undefined,
      images: images.map((img) => img.file),
    };

    importMutation.mutate(articleData);
  };

  const handleReset = () => {
    reset();
    setContent('');
    setImages([]);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Title */}
      <Input
        label="文章標題"
        placeholder="輸入文章標題"
        error={errors.title?.message}
        fullWidth
        required
        {...register('title')}
      />

      {/* Excerpt */}
      <Textarea
        label="摘要"
        placeholder="輸入文章摘要（可選）"
        error={errors.excerpt?.message}
        helperText="用於 SEO 和文章列表展示"
        fullWidth
        rows={3}
        maxCharacters={500}
        characterCount={excerptValue?.length || 0}
        {...register('excerpt')}
      />

      {/* Content */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          文章內容 <span className="text-error-500">*</span>
        </label>
        <RichTextEditor
          content={content}
          onChange={setContent}
          placeholder="開始撰寫您的文章..."
          minHeight="400px"
        />
      </div>

      {/* Tags */}
      <Input
        label="標籤"
        placeholder="輸入標籤，用逗號分隔（例如：技術, AI, 自動化）"
        error={errors.tags?.message}
        helperText="用逗號分隔多個標籤"
        fullWidth
        {...register('tags')}
      />

      {/* Categories */}
      <Input
        label="分類"
        placeholder="輸入分類，用逗號分隔（例如：技術, 教程）"
        error={errors.categories?.message}
        helperText="用逗號分隔多個分類"
        fullWidth
        {...register('categories')}
      />

      {/* Images */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          圖片上傳
        </label>
        <ImageUploadWidget images={images} onChange={setImages} maxImages={10} />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-4 border-t">
        <Button
          type="submit"
          variant="primary"
          disabled={importMutation.isPending}
        >
          {importMutation.isPending ? (
            <>
              <Spinner size="sm" variant="white" className="mr-2" />
              創建中...
            </>
          ) : (
            '創建文章'
          )}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={handleReset}
          disabled={importMutation.isPending}
        >
          重置
        </Button>
      </div>
    </form>
  );
};
