/**
 * Tag Management Section component.
 * Manage commonly used tags and tag suggestions.
 */

import { useState } from 'react';
import { Card, Button, Input, Badge } from '@/components/ui';
import { useTranslation } from 'react-i18next';
import { Plus, Tag, Trash2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface TagItem {
  id: string;
  name: string;
  count: number;
  color?: string;
}

export const TagManagementSection: React.FC = () => {
  const { t } = useTranslation();

  // Mock data - 实际应该从后端 API 获取
  const [tags, setTags] = useState<TagItem[]>([
    { id: '1', name: 'SEO优化', count: 15, color: 'blue' },
    { id: '2', name: '技术教程', count: 23, color: 'green' },
    { id: '3', name: '产品评测', count: 8, color: 'purple' },
    { id: '4', name: '行业动态', count: 12, color: 'orange' },
    { id: '5', name: '用户体验', count: 6, color: 'pink' },
  ]);

  const [newTagName, setNewTagName] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddTag = () => {
    if (!newTagName.trim()) {
      toast.error(t('settings.tags.emptyTagError'));
      return;
    }

    // Check if tag already exists
    const exists = tags.some(
      (tag) => tag.name.toLowerCase() === newTagName.toLowerCase()
    );

    if (exists) {
      toast.error(t('settings.tags.duplicateTagError'));
      return;
    }

    const newTag: TagItem = {
      id: Date.now().toString(),
      name: newTagName.trim(),
      count: 0,
      color: 'gray',
    };

    setTags([...tags, newTag]);
    setNewTagName('');
    setIsAdding(false);
    toast.success(t('settings.tags.addSuccess', { name: newTag.name }));
  };

  const handleDeleteTag = (tagId: string) => {
    const tag = tags.find((t) => t.id === tagId);
    if (!tag) return;

    if (tag.count > 0) {
      toast.error(
        t('settings.tags.deleteError', { count: tag.count })
      );
      return;
    }

    setTags(tags.filter((t) => t.id !== tagId));
    toast.success(t('settings.tags.deleteSuccess', { name: tag.name }));
  };

  const sortedTags = [...tags].sort((a, b) => b.count - a.count);

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {t('settings.tags.title')}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              {t('settings.tags.description')}
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAdding(!isAdding)}
          >
            <Plus className="mr-2 h-4 w-4" />
            {t('settings.tags.addTag')}
          </Button>
        </div>

        {/* Add Tag Form */}
        {isAdding && (
          <div className="rounded-lg border border-primary-200 bg-primary-50 p-4">
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <Input
                  label={t('settings.tags.newTagLabel')}
                  placeholder={t('settings.tags.newTagPlaceholder')}
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAddTag();
                    } else if (e.key === 'Escape') {
                      setIsAdding(false);
                      setNewTagName('');
                    }
                  }}
                  autoFocus
                />
              </div>
              <Button variant="primary" size="md" onClick={handleAddTag}>
                {t('common.save')}
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={() => {
                  setIsAdding(false);
                  setNewTagName('');
                }}
              >
                {t('common.cancel')}
              </Button>
            </div>
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-primary-600" />
              <span className="text-sm font-medium text-gray-600">
                {t('settings.tags.totalTags')}
              </span>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">{tags.length}</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-warning-600" />
              <span className="text-sm font-medium text-gray-600">
                {t('settings.tags.unusedTags')}
              </span>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {tags.filter((t) => t.count === 0).length}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-success-600" />
              <span className="text-sm font-medium text-gray-600">
                {t('settings.tags.mostUsed')}
              </span>
            </div>
            <p className="mt-2 text-lg font-bold text-gray-900">
              {sortedTags[0]?.name || '-'}
            </p>
          </div>
        </div>

        {/* Tags List */}
        <div>
          <h3 className="mb-3 text-sm font-medium text-gray-700">
            {t('settings.tags.allTags')}
          </h3>
          {tags.length > 0 ? (
            <div className="space-y-2">
              {sortedTags.map((tag) => (
                <div
                  key={tag.id}
                  className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <Tag className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{tag.name}</p>
                      <p className="text-xs text-gray-500">
                        {t('settings.tags.usedInArticles', { count: tag.count })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={tag.count > 0 ? 'default' : 'secondary'}
                    >
                      {tag.count}
                    </Badge>
                    {tag.count === 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteTag(tag.id)}
                        className="text-error-600 hover:bg-error-50 hover:text-error-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 py-8">
              <Tag className="mb-2 h-8 w-8 text-gray-400" />
              <p className="mb-1 text-sm font-medium text-gray-600">
                {t('settings.tags.noTags')}
              </p>
              <p className="text-xs text-gray-500">
                {t('settings.tags.noTagsHint')}
              </p>
            </div>
          )}
        </div>

        {/* Info Note */}
        <div className="rounded-lg border border-info-200 bg-info-50 p-4">
          <div className="flex gap-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-info-600" />
            <div className="text-sm text-info-800">
              <p className="font-medium">{t('settings.tags.noteTitle')}</p>
              <p className="mt-1 text-info-700">{t('settings.tags.noteDescription')}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
