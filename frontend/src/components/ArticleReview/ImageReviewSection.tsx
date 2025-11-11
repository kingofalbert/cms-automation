/**
 * ImageReviewSection - Image management for article
 *
 * Phase 8.2: Parsing Review Panel
 * - Featured image selection
 * - Additional images management
 * - Image upload
 */

import React from 'react';
import { Button } from '../ui/Button';
import { Image as ImageIcon, Upload, X } from 'lucide-react';

export interface ImageReviewSectionProps {
  /** Featured image URL */
  featuredImage: string;
  /** Additional image URLs */
  additionalImages: string[];
  /** Worklist item ID for uploads */
  worklistItemId: number;
  /** Callback when featured image changes */
  onFeaturedImageChange: (url: string) => void;
  /** Callback when additional images change */
  onAdditionalImagesChange: (urls: string[]) => void;
}

/**
 * ImageReviewSection Component
 */
export const ImageReviewSection: React.FC<ImageReviewSectionProps> = ({
  featuredImage,
  additionalImages,
  worklistItemId,
  onFeaturedImageChange,
  onAdditionalImagesChange,
}) => {
  const handleRemoveAdditionalImage = (index: number) => {
    const newImages = [...additionalImages];
    newImages.splice(index, 1);
    onAdditionalImagesChange(newImages);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <ImageIcon className="w-5 h-5" />
        图片审核
      </h3>

      {/* Featured Image */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          特色图片
        </label>
        {featuredImage ? (
          <div className="relative inline-block">
            <img
              src={featuredImage}
              alt="Featured"
              className="w-full max-w-md h-48 object-cover rounded-lg border border-gray-200"
            />
            <button
              type="button"
              onClick={() => onFeaturedImageChange('')}
              className="absolute top-2 right-2 p-1 bg-red-600 text-white rounded-full hover:bg-red-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="w-full max-w-md h-48 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <ImageIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">暂无特色图片</p>
              <Button variant="outline" size="sm" className="mt-2">
                <Upload className="w-4 h-4 mr-2" />
                上传图片
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Additional Images */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          附加图片 ({additionalImages.length})
        </label>
        {additionalImages.length > 0 ? (
          <div className="grid grid-cols-3 gap-2">
            {additionalImages.map((url, index) => (
              <div key={index} className="relative">
                <img
                  src={url}
                  alt={`Additional ${index + 1}`}
                  className="w-full h-24 object-cover rounded border border-gray-200"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveAdditionalImage(index)}
                  className="absolute top-1 right-1 p-0.5 bg-red-600 text-white rounded-full hover:bg-red-700"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">暂无附加图片</p>
        )}
        <Button variant="outline" size="sm">
          <Upload className="w-4 h-4 mr-2" />
          添加图片
        </Button>
      </div>

      {/* Image guidelines */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
        <strong>图片建议：</strong>
        <ul className="mt-1 ml-4 list-disc space-y-1">
          <li>特色图片建议尺寸：1200×630 像素</li>
          <li>支持格式：JPG, PNG, WebP</li>
          <li>文件大小：建议 &lt; 500KB</li>
        </ul>
      </div>
    </div>
  );
};

ImageReviewSection.displayName = 'ImageReviewSection';
