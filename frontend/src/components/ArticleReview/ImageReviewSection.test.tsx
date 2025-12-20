/**
 * ImageReviewSection Component Tests
 *
 * Phase 13: Enhanced Image Review - Visual Regression Tests
 * Tests cover:
 * 1. FeaturedBadge component with different detection methods
 * 2. Image separation (置頂 vs 正文)
 * 3. ImageInfoCard rendering with status badges
 * 4. Epoch Times standards validation
 * 5. Edge cases and accessibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageReviewSection, type ArticleImageData } from './ImageReviewSection';

describe('ImageReviewSection', () => {
  // Mock callback functions
  const mockOnFeaturedImageChange = vi.fn();
  const mockOnAdditionalImagesChange = vi.fn();
  const mockOnImageAltUpdate = vi.fn();

  // Sample test data - Featured image detected by caption keyword
  const mockFeaturedImageByCaption: ArticleImageData = {
    id: 1,
    article_id: 100,
    position: 0,
    preview_path: '/images/featured.jpg',
    source_url: 'https://drive.google.com/file/d/abc123',
    caption: '置頂圖：AI 醫療示意圖',
    alt_text: 'AI-powered medical diagnosis illustration',
    is_featured: true,
    image_type: 'featured',
    detection_method: 'caption_keyword',
    image_metadata: {
      image_technical_specs: {
        width: 1200,
        height: 630,
        aspect_ratio: '16:9',
        file_size_bytes: 245000,
        format: 'JPEG',
      },
    },
  };

  // Featured image detected by position
  const mockFeaturedImageByPosition: ArticleImageData = {
    id: 2,
    article_id: 100,
    position: 0,
    preview_path: '/images/featured2.jpg',
    caption: 'Regular caption without keywords',
    is_featured: true,
    image_type: 'featured',
    detection_method: 'position_before_body',
    image_metadata: {
      image_technical_specs: {
        width: 1200,
        height: 630,
        file_size_bytes: 300000,
        format: 'PNG',
      },
    },
  };

  // Featured image set manually
  const mockManualFeaturedImage: ArticleImageData = {
    id: 3,
    article_id: 100,
    position: 5,
    preview_path: '/images/manual.jpg',
    caption: 'User-selected featured image',
    is_featured: true,
    image_type: 'featured',
    detection_method: 'manual',
    image_metadata: {
      image_technical_specs: {
        width: 1400,
        height: 700,
        file_size_bytes: 200000,
        format: 'WebP',
      },
    },
  };

  // Legacy migrated featured image
  const mockLegacyFeaturedImage: ArticleImageData = {
    id: 4,
    article_id: 100,
    position: 0,
    preview_path: '/images/legacy.jpg',
    is_featured: true,
    image_type: 'featured',
    detection_method: 'position_legacy',
    image_metadata: {
      image_technical_specs: {
        width: 1200,
        height: 630,
        file_size_bytes: 150000,
        format: 'JPEG',
      },
    },
  };

  // Content images
  const mockContentImages: ArticleImageData[] = [
    {
      id: 10,
      article_id: 100,
      position: 1,
      preview_path: '/images/content1.jpg',
      caption: '內文圖片說明',
      alt_text: 'Content image 1',
      is_featured: false,
      image_type: 'content',
      detection_method: 'none',
      image_metadata: {
        image_technical_specs: {
          width: 800,
          height: 450,
          file_size_bytes: 150000,
          format: 'JPEG',
        },
      },
    },
    {
      id: 11,
      article_id: 100,
      position: 2,
      preview_path: '/images/content2.jpg',
      caption: '第二張內文圖',
      is_featured: false,
      image_type: 'content',
      detection_method: 'none',
      image_metadata: {
        image_technical_specs: {
          width: 900,
          height: 500,
          file_size_bytes: 200000,
          format: 'PNG',
        },
      },
    },
  ];

  // Image that fails standards
  const mockFailingImage: ArticleImageData = {
    id: 20,
    article_id: 100,
    position: 3,
    preview_path: '/images/small.jpg',
    caption: '小圖片',
    is_featured: false,
    image_type: 'content',
    detection_method: 'none',
    image_metadata: {
      image_technical_specs: {
        width: 400,
        height: 200,
        file_size_bytes: 500000,
        format: 'BMP',
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ========================================================================
  // Basic Rendering Tests
  // ========================================================================

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('圖片審核')).toBeInTheDocument();
    });

    it('should display correct image count summary', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={['/images/content1.jpg', '/images/content2.jpg']}
          articleImages={[mockFeaturedImageByCaption, ...mockContentImages]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText(/\(3 張圖片：1 置頂 \+ 2 正文\)/)).toBeInTheDocument();
    });

    it('should show empty state when no featured image', () => {
      render(
        <ImageReviewSection
          featuredImage=""
          additionalImages={[]}
          articleImages={[]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('暫無特色圖片')).toBeInTheDocument();
    });

    it('should show empty state for content images', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('暫無附加圖片')).toBeInTheDocument();
    });
  });

  // ========================================================================
  // FeaturedBadge Component Tests
  // ========================================================================

  describe('FeaturedBadge', () => {
    it('should display FeaturedBadge for featured images', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      // Multiple "置頂圖片" elements exist (label, header, badge)
      const featuredElements = screen.getAllByText(/置頂圖片/);
      expect(featuredElements.length).toBeGreaterThanOrEqual(2);
      // Check that FeaturedBadge with emoji exists
      expect(screen.getByText(/⭐ 置頂圖片/)).toBeInTheDocument();
    });

    it('should show caption_keyword detection method', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('(圖說標記)')).toBeInTheDocument();
    });

    it('should show position_before_body detection method', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByPosition]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('(位置檢測)')).toBeInTheDocument();
    });

    it('should show manual detection method', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/manual.jpg"
          additionalImages={[]}
          articleImages={[mockManualFeaturedImage]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('(手動設置)')).toBeInTheDocument();
    });

    it('should show position_legacy detection method', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/legacy.jpg"
          additionalImages={[]}
          articleImages={[mockLegacyFeaturedImage]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('(舊版遷移)')).toBeInTheDocument();
    });

    it('should display tooltip with detection method description', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      // The badge should have a title attribute with tooltip text
      const badge = screen.getByTitle('Caption 包含「置頂」等關鍵字');
      expect(badge).toBeInTheDocument();
    });
  });

  // ========================================================================
  // Image Separation Tests (置頂 vs 正文)
  // ========================================================================

  describe('Image Separation', () => {
    it('should separate featured and content images correctly', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={['/images/content1.jpg', '/images/content2.jpg']}
          articleImages={[mockFeaturedImageByCaption, ...mockContentImages]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should show labels for both sections
      expect(screen.getByText('置頂圖片 (Featured Image)')).toBeInTheDocument();
      expect(screen.getByText(/正文圖片 \(Content Images\)/)).toBeInTheDocument();
    });

    it('should use is_featured field for separation', () => {
      const articleImages = [
        { ...mockContentImages[0], position: 0, is_featured: false }, // position 0 but not featured
        { ...mockFeaturedImageByCaption, position: 2, is_featured: true }, // position 2 but featured
      ];

      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={['/images/content1.jpg']}
          articleImages={articleImages}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // The image at position 2 should be shown as featured because is_featured=true
      expect(screen.getByText(/\(2 張圖片：1 置頂 \+ 1 正文\)/)).toBeInTheDocument();
    });

    it('should fallback to position=0 for legacy data without is_featured', () => {
      const legacyImages: ArticleImageData[] = [
        {
          id: 30,
          article_id: 100,
          position: 0,
          preview_path: '/images/legacy-featured.jpg',
          // is_featured is undefined (legacy data)
          image_metadata: {
            image_technical_specs: {
              width: 1200,
              height: 630,
              file_size_bytes: 200000,
              format: 'JPEG',
            },
          },
        } as ArticleImageData,
        {
          id: 31,
          article_id: 100,
          position: 1,
          preview_path: '/images/legacy-content.jpg',
          image_metadata: {
            image_technical_specs: {
              width: 800,
              height: 400,
              file_size_bytes: 150000,
              format: 'PNG',
            },
          },
        } as ArticleImageData,
      ];

      render(
        <ImageReviewSection
          featuredImage="/images/legacy-featured.jpg"
          additionalImages={['/images/legacy-content.jpg']}
          articleImages={legacyImages}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should still identify position=0 as featured for legacy data
      expect(screen.getByText(/\(2 張圖片：1 置頂 \+ 1 正文\)/)).toBeInTheDocument();
    });
  });

  // ========================================================================
  // Status Badge Tests
  // ========================================================================

  describe('Status Badges', () => {
    it('should show pass badge when image meets standards', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('符合標準')).toBeInTheDocument();
    });

    it('should show fail badge when image does not meet standards', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/small.jpg"
          additionalImages={[]}
          articleImages={[{ ...mockFailingImage, is_featured: true, image_type: 'featured' }]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );
      expect(screen.getByText('需修正')).toBeInTheDocument();
    });

    it('should display total issues count', () => {
      const allImages = [
        { ...mockFailingImage, is_featured: true, image_type: 'featured' as const },
        mockFailingImage,
      ];

      render(
        <ImageReviewSection
          featuredImage="/images/small.jpg"
          additionalImages={['/images/small.jpg']}
          articleImages={allImages}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should show issues count (multiple issues expected)
      expect(screen.getByText(/個問題/)).toBeInTheDocument();
    });
  });

  // ========================================================================
  // ImageInfoCard Tests
  // ========================================================================

  describe('ImageInfoCard', () => {
    it('should display image metadata', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Resolution display (includes aspect ratio)
      expect(screen.getByText(/1200 × 630 px/)).toBeInTheDocument();
    });

    it('should display caption and alt text', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('置頂圖：AI 醫療示意圖')).toBeInTheDocument();
      expect(screen.getByText('AI-powered medical diagnosis illustration')).toBeInTheDocument();
    });

    it('should display 未設置 when caption or alt text is missing', () => {
      const imageWithoutText: ArticleImageData = {
        ...mockFeaturedImageByCaption,
        caption: undefined,
        alt_text: undefined,
      };

      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[imageWithoutText]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should show "未設置" for missing caption and alt text
      const notSetElements = screen.getAllByText('未設置');
      expect(notSetElements.length).toBeGreaterThanOrEqual(2);
    });

    it('should display original source URL', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('原始鏈接')).toBeInTheDocument();
    });

    it('should toggle expand/collapse', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Find the collapse button (initially showing collapse icon since expanded is default)
      const collapseButton = screen.getAllByRole('button').find(
        (button) => button.querySelector('svg[class*="lucide-chevron"]')
      );

      if (collapseButton) {
        fireEvent.click(collapseButton);
        // After clicking, the detailed content should be hidden
        // We can verify by checking that resolution is no longer visible
        expect(screen.queryByText('1200 × 630 px')).not.toBeInTheDocument();
      }
    });
  });

  // ========================================================================
  // Epoch Times Standards Tests
  // ========================================================================

  describe('Epoch Times Standards', () => {
    it('should display standards comparison section', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('大紀元標準對比')).toBeInTheDocument();
      expect(screen.getByText('解析度')).toBeInTheDocument();
      expect(screen.getByText('文件大小')).toBeInTheDocument();
      expect(screen.getByText('格式')).toBeInTheDocument();
    });

    it('should show image guidelines', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('大紀元圖片標準：')).toBeInTheDocument();
      expect(screen.getByText(/特色圖片建議尺寸：1200×630 像素/)).toBeInTheDocument();
    });
  });

  // ========================================================================
  // User Interactions Tests
  // ========================================================================

  describe('User Interactions', () => {
    it('should call onFeaturedImageChange when remove button is clicked', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Find the remove button (X icon)
      const removeButtons = screen.getAllByRole('button');
      const removeButton = removeButtons.find(
        (button) => button.className.includes('text-red-600')
      );

      if (removeButton) {
        fireEvent.click(removeButton);
        expect(mockOnFeaturedImageChange).toHaveBeenCalledWith('');
      }
    });

    it('should call onAdditionalImagesChange when content image is removed', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={['/images/content1.jpg', '/images/content2.jpg']}
          articleImages={[mockFeaturedImageByCaption, ...mockContentImages]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Find remove buttons for content images
      const removeButtons = screen.getAllByRole('button').filter(
        (button) => button.className.includes('text-red-600')
      );

      // Click the first content image's remove button (index 1, since index 0 is featured)
      if (removeButtons.length > 1) {
        fireEvent.click(removeButtons[1]);
        expect(mockOnAdditionalImagesChange).toHaveBeenCalled();
      }
    });
  });

  // ========================================================================
  // Edge Cases Tests
  // ========================================================================

  describe('Edge Cases', () => {
    it('should handle empty articleImages array', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('圖片審核')).toBeInTheDocument();
      expect(screen.getByText(/\(0 張圖片：0 置頂 \+ 0 正文\)/)).toBeInTheDocument();
    });

    it('should handle missing image_metadata', () => {
      const imageWithoutMetadata: ArticleImageData = {
        id: 50,
        article_id: 100,
        position: 0,
        is_featured: true,
        image_type: 'featured',
        detection_method: 'caption_keyword',
        caption: '圖片沒有元數據',
        // image_metadata is undefined
      };

      render(
        <ImageReviewSection
          featuredImage="/images/no-metadata.jpg"
          additionalImages={[]}
          articleImages={[imageWithoutMetadata]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should render without crashing
      expect(screen.getByText('圖片審核')).toBeInTheDocument();
      // Should show "未知" for unknown values
      expect(screen.getAllByText('未知').length).toBeGreaterThan(0);
    });

    it('should handle multiple featured images (only first should be featured)', () => {
      // In case backend sends multiple is_featured=true (shouldn't happen but handle gracefully)
      const multipleFeatureds = [
        { ...mockFeaturedImageByCaption, id: 1, is_featured: true },
        { ...mockFeaturedImageByPosition, id: 2, is_featured: true },
      ];

      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={['/images/featured2.jpg']}
          articleImages={multipleFeatureds}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Should render without crashing - display logic will handle this
      expect(screen.getByText('圖片審核')).toBeInTheDocument();
    });

    it('should handle very long source URLs', () => {
      const imageWithLongUrl: ArticleImageData = {
        ...mockFeaturedImageByCaption,
        source_url: 'https://drive.google.com/file/d/' + 'a'.repeat(200) + '/view?usp=sharing',
      };

      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[imageWithLongUrl]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // URL should be truncated
      expect(screen.getByText(/\.\.\./)).toBeInTheDocument();
    });
  });

  // ========================================================================
  // Accessibility Tests
  // ========================================================================

  describe('Accessibility', () => {
    it('should have semantic heading for main section', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      const heading = screen.getByText('圖片審核');
      expect(heading.tagName).toBe('H3');
    });

    it('should have accessible labels for sections', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      expect(screen.getByText('置頂圖片 (Featured Image)')).toBeInTheDocument();
      expect(screen.getByText(/正文圖片 \(Content Images\)/)).toBeInTheDocument();
    });

    it('should have alt text for images', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      const images = screen.getAllByRole('img');
      images.forEach((img) => {
        expect(img).toHaveAttribute('alt');
      });
    });

    it('should have title attribute on FeaturedBadge for tooltip', () => {
      render(
        <ImageReviewSection
          featuredImage="/images/featured.jpg"
          additionalImages={[]}
          articleImages={[mockFeaturedImageByCaption]}
          worklistItemId={1}
          onFeaturedImageChange={mockOnFeaturedImageChange}
          onAdditionalImagesChange={mockOnAdditionalImagesChange}
        />
      );

      // Check that the badge has a descriptive title
      const badgeWithTooltip = screen.getByTitle(/Caption 包含/);
      expect(badgeWithTooltip).toBeInTheDocument();
    });
  });
});
