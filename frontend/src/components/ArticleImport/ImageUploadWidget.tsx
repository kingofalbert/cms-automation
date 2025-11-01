/**
 * Image Upload Widget component.
 * Supports multiple image uploads with preview.
 */

import { useState } from 'react';
import { DragDropZone } from './DragDropZone';
import { Button } from '@/components/ui';
import { clsx } from 'clsx';

export interface UploadedImage {
  file: File;
  preview: string;
  altText?: string;
  isFeatured: boolean;
}

export interface ImageUploadWidgetProps {
  images: UploadedImage[];
  onChange: (images: UploadedImage[]) => void;
  maxImages?: number;
  className?: string;
}

export const ImageUploadWidget: React.FC<ImageUploadWidgetProps> = ({
  images,
  onChange,
  maxImages = 10,
  className,
}) => {
  const [previewMode, setPreviewMode] = useState<'grid' | 'list'>('grid');

  const handleFilesAccepted = (files: File[]) => {
    const newImages: UploadedImage[] = files.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      isFeatured: images.length === 0, // First image is featured by default
    }));

    onChange([...images, ...newImages].slice(0, maxImages));
  };

  const handleRemove = (index: number) => {
    const newImages = images.filter((_, i) => i !== index);
    // If removed image was featured, make first image featured
    if (images[index].isFeatured && newImages.length > 0) {
      newImages[0].isFeatured = true;
    }
    onChange(newImages);
  };

  const handleSetFeatured = (index: number) => {
    const newImages = images.map((img, i) => ({
      ...img,
      isFeatured: i === index,
    }));
    onChange(newImages);
  };

  const handleAltTextChange = (index: number, altText: string) => {
    const newImages = images.map((img, i) =>
      i === index ? { ...img, altText } : img
    );
    onChange(newImages);
  };

  const remainingSlots = maxImages - images.length;

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Upload Zone */}
      {remainingSlots > 0 && (
        <DragDropZone
          onFilesAccepted={handleFilesAccepted}
          acceptedFileTypes={{
            'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
          }}
          maxFiles={remainingSlots}
          maxSize={5 * 1024 * 1024} // 5MB per image
          multiple={true}
        />
      )}

      {/* Image Count */}
      {images.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            已上传 {images.length} / {maxImages} 张图片
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPreviewMode('grid')}
              className={clsx(
                'px-3 py-1 text-sm rounded',
                previewMode === 'grid'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              网格
            </button>
            <button
              type="button"
              onClick={() => setPreviewMode('list')}
              className={clsx(
                'px-3 py-1 text-sm rounded',
                previewMode === 'list'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              列表
            </button>
          </div>
        </div>
      )}

      {/* Image Preview */}
      {images.length > 0 && (
        <div
          className={clsx(
            previewMode === 'grid'
              ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'
              : 'space-y-3'
          )}
        >
          {images.map((image, index) => (
            <div
              key={index}
              className={clsx(
                'border rounded-lg overflow-hidden',
                image.isFeatured && 'ring-2 ring-primary-500',
                previewMode === 'list' && 'flex gap-4'
              )}
            >
              {/* Image Preview */}
              <div
                className={clsx(
                  'relative bg-gray-100',
                  previewMode === 'grid' ? 'aspect-square' : 'w-32 h-32 flex-shrink-0'
                )}
              >
                <img
                  src={image.preview}
                  alt={image.altText || `Image ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                {image.isFeatured && (
                  <div className="absolute top-2 left-2 bg-primary-600 text-white text-xs px-2 py-1 rounded">
                    特色图片
                  </div>
                )}
              </div>

              {/* Image Details */}
              <div className={clsx('p-3', previewMode === 'list' && 'flex-1')}>
                <input
                  type="text"
                  value={image.altText || ''}
                  onChange={(e) => handleAltTextChange(index, e.target.value)}
                  placeholder="Alt 文本（可选）"
                  className="w-full text-sm border border-gray-300 rounded px-2 py-1 mb-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />

                <div className="flex gap-2">
                  {!image.isFeatured && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSetFeatured(index)}
                    >
                      设为特色
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemove(index)}
                    className="text-red-600 hover:bg-red-50"
                  >
                    删除
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
