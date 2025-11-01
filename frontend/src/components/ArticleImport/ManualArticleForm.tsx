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
import axios from 'axios';
import { ArticleImportRequest } from '@/types/article';

const articleSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(200, '标题最多 200 字符'),
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

  const importMutation = useMutation({
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

      const response = await axios.post('/api/v1/articles/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      return response.data;
    },
    onSuccess: (data) => {
      alert(`文章创建成功！ID: ${data.id}`);
      handleReset();
    },
    onError: (error: any) => {
      alert(`创建失败: ${error.response?.data?.message || error.message}`);
    },
  });

  const onSubmit = (data: ArticleFormData) => {
    if (!content || content.trim() === '') {
      alert('文章内容不能为空');
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
        label="文章标题"
        placeholder="输入文章标题"
        error={errors.title?.message}
        fullWidth
        required
        {...register('title')}
      />

      {/* Excerpt */}
      <Textarea
        label="摘要"
        placeholder="输入文章摘要（可选）"
        error={errors.excerpt?.message}
        helperText="用于 SEO 和文章列表展示"
        fullWidth
        rows={3}
        maxCharacters={500}
        characterCount={excerptValue?.length || 0}
        {...register('excerpt')}
      />

      {/* Content */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          文章内容 <span className="text-error-500">*</span>
        </label>
        <RichTextEditor
          content={content}
          onChange={setContent}
          placeholder="开始撰写您的文章..."
          minHeight="400px"
        />
      </div>

      {/* Tags */}
      <Input
        label="标签"
        placeholder="输入标签，用逗号分隔（例如：技术, AI, 自动化）"
        error={errors.tags?.message}
        helperText="用逗号分隔多个标签"
        fullWidth
        {...register('tags')}
      />

      {/* Categories */}
      <Input
        label="分类"
        placeholder="输入分类，用逗号分隔（例如：技术, 教程）"
        error={errors.categories?.message}
        helperText="用逗号分隔多个分类"
        fullWidth
        {...register('categories')}
      />

      {/* Images */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          图片上传
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
              创建中...
            </>
          ) : (
            '创建文章'
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
