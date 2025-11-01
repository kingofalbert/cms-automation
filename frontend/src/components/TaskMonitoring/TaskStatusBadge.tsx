/**
 * Task Status Badge component.
 * Displays the status of a publishing task with appropriate styling.
 */

import { Badge } from '@/components/ui';
import { PublishStatus } from '@/types/publishing';

export interface TaskStatusBadgeProps {
  status: PublishStatus;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

const STATUS_CONFIG: Record<
  PublishStatus,
  { variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary'; label: string }
> = {
  idle: { variant: 'default', label: '待发布' },
  pending: { variant: 'secondary', label: '等待中' },
  initializing: { variant: 'info', label: '初始化' },
  logging_in: { variant: 'info', label: '登录中' },
  creating_post: { variant: 'info', label: '创建文章' },
  uploading_images: { variant: 'info', label: '上传图片' },
  configuring_seo: { variant: 'info', label: '配置 SEO' },
  publishing: { variant: 'info', label: '发布中' },
  completed: { variant: 'success', label: '已完成' },
  failed: { variant: 'error', label: '失败' },
};

export const TaskStatusBadge: React.FC<TaskStatusBadgeProps> = ({
  status,
  size = 'md',
  dot = true,
}) => {
  const config = STATUS_CONFIG[status];

  return (
    <Badge variant={config.variant} size={size} dot={dot}>
      {config.label}
    </Badge>
  );
};
