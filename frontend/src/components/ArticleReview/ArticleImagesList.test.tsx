/**
 * ArticleImagesList Component Tests
 *
 * Phase 16: Tests for the article images list component in publish preview.
 * Tests cover rendering, edge cases (especially undefined URLs), and interactions.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ArticleImagesList, type ArticleImage } from './ArticleImagesList';

describe('ArticleImagesList', () => {
  // Sample test data
  const mockImagesWithAlt: ArticleImage[] = [
    {
      id: 1,
      image_url: 'https://example.com/image1.jpg',
      alt_text: '健康食材圖片',
      position: 1,
      filename: 'image1.jpg',
    },
    {
      id: 2,
      image_url: 'https://example.com/image2.jpg',
      alt_text: '營養均衡飲食',
      position: 2,
      filename: 'image2.jpg',
    },
    {
      id: 3,
      image_url: 'https://example.com/image3.jpg',
      ai_alt_text: 'AI 生成的圖片描述',
      position: 3,
      filename: 'image3.jpg',
    },
  ];

  const mockImagesWithoutAlt: ArticleImage[] = [
    {
      id: 1,
      image_url: 'https://example.com/image1.jpg',
      position: 1,
    },
    {
      id: 2,
      image_url: 'https://example.com/image2.jpg',
      position: 2,
    },
  ];

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText(/文章圖片/)).toBeInTheDocument();
    });

    it('should display image count', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText('文章圖片 (3張)')).toBeInTheDocument();
    });

    it('should show "無內文圖片" when images array is empty', () => {
      render(<ArticleImagesList images={[]} />);
      expect(screen.getByText('無內文圖片')).toBeInTheDocument();
    });

    it('should show "無內文圖片" when images is undefined', () => {
      // @ts-expect-error - Testing undefined images prop
      render(<ArticleImagesList images={undefined} />);
      expect(screen.getByText('無內文圖片')).toBeInTheDocument();
    });

    it('should display Alt 完整 badge when all images have alt text', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText('Alt 完整')).toBeInTheDocument();
    });

    it('should display missing alt count badge when some images lack alt text', () => {
      render(<ArticleImagesList images={mockImagesWithoutAlt} />);
      expect(screen.getByText('2張缺少 Alt')).toBeInTheDocument();
    });
  });

  describe('Image Display', () => {
    it('should display image filename', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText('image1.jpg')).toBeInTheDocument();
    });

    it('should display alt text for images with alt', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText(/健康食材圖片/)).toBeInTheDocument();
    });

    it('should display AI tag for AI-generated alt text', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      expect(screen.getByText('(AI)')).toBeInTheDocument();
    });

    it('should display "Alt: 缺失" for images without alt text', () => {
      render(<ArticleImagesList images={mockImagesWithoutAlt} />);
      const missingAlts = screen.getAllByText('Alt: 缺失');
      expect(missingAlts.length).toBe(2);
    });
  });

  describe('Edge Cases - Undefined/Null URL Handling', () => {
    it('should handle image with undefined URL', () => {
      const imagesWithUndefinedUrl: ArticleImage[] = [
        {
          id: 1,
          // @ts-expect-error - Testing undefined URL
          image_url: undefined,
          alt_text: '有 alt 但沒有 URL',
        },
      ];
      render(<ArticleImagesList images={imagesWithUndefinedUrl} />);
      // Should render without crashing
      expect(screen.getByText('文章圖片 (1張)')).toBeInTheDocument();
      // Should show default filename "image"
      expect(screen.getByText('image')).toBeInTheDocument();
    });

    it('should handle image with null URL', () => {
      const imagesWithNullUrl: ArticleImage[] = [
        {
          id: 1,
          // @ts-expect-error - Testing null URL
          image_url: null,
          alt_text: '有 alt 但 URL 為 null',
        },
      ];
      render(<ArticleImagesList images={imagesWithNullUrl} />);
      // Should render without crashing
      expect(screen.getByText('文章圖片 (1張)')).toBeInTheDocument();
      expect(screen.getByText('image')).toBeInTheDocument();
    });

    it('should handle image with empty string URL', () => {
      const imagesWithEmptyUrl: ArticleImage[] = [
        {
          id: 1,
          image_url: '',
          alt_text: '有 alt 但 URL 為空',
        },
      ];
      render(<ArticleImagesList images={imagesWithEmptyUrl} />);
      // Should render without crashing
      expect(screen.getByText('文章圖片 (1張)')).toBeInTheDocument();
    });

    it('should handle mixed images - some with URL, some without', () => {
      const mixedImages: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/valid.jpg',
          alt_text: '有效圖片',
        },
        {
          id: 2,
          // @ts-expect-error - Testing undefined URL
          image_url: undefined,
          alt_text: '無 URL 圖片',
        },
        {
          id: 3,
          image_url: 'https://example.com/another.jpg',
        },
      ];
      render(<ArticleImagesList images={mixedImages} />);
      expect(screen.getByText('文章圖片 (3張)')).toBeInTheDocument();
      expect(screen.getByText('valid.jpg')).toBeInTheDocument();
      expect(screen.getByText('image')).toBeInTheDocument(); // fallback for undefined URL
    });

    it('should use fallback filename when URL is invalid but filename is provided', () => {
      const imageWithFallbackFilename: ArticleImage[] = [
        {
          id: 1,
          // @ts-expect-error - Testing undefined URL
          image_url: undefined,
          filename: 'my-custom-filename.png',
          alt_text: '有 filename 的圖片',
        },
      ];
      render(<ArticleImagesList images={imageWithFallbackFilename} />);
      expect(screen.getByText('my-custom-filename.png')).toBeInTheDocument();
    });
  });

  describe('Edge Cases - Alt Text Handling', () => {
    it('should handle undefined alt_text and undefined ai_alt_text', () => {
      const imageNoAlt: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/test.jpg',
          alt_text: undefined,
          ai_alt_text: undefined,
        },
      ];
      render(<ArticleImagesList images={imageNoAlt} />);
      expect(screen.getByText('Alt: 缺失')).toBeInTheDocument();
    });

    it('should handle null alt_text', () => {
      const imageNullAlt: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/test.jpg',
          alt_text: null,
        },
      ];
      render(<ArticleImagesList images={imageNullAlt} />);
      expect(screen.getByText('Alt: 缺失')).toBeInTheDocument();
    });

    it('should prefer alt_text over ai_alt_text when both exist', () => {
      const imageBothAlts: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/test.jpg',
          alt_text: '人工編輯的 Alt',
          ai_alt_text: 'AI 生成的 Alt',
        },
      ];
      render(<ArticleImagesList images={imageBothAlts} />);
      expect(screen.getByText(/人工編輯的 Alt/)).toBeInTheDocument();
      expect(screen.queryByText(/AI 生成的 Alt/)).not.toBeInTheDocument();
    });
  });

  describe('Show More/Less Functionality', () => {
    const manyImages: ArticleImage[] = Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      image_url: `https://example.com/image${i + 1}.jpg`,
      alt_text: `圖片 ${i + 1} 的描述`,
      position: i + 1,
      filename: `image${i + 1}.jpg`,
    }));

    it('should show only initial display count by default', () => {
      render(<ArticleImagesList images={manyImages} initialDisplayCount={3} />);
      // Should only show 3 images initially
      expect(screen.getByText('image1.jpg')).toBeInTheDocument();
      expect(screen.getByText('image2.jpg')).toBeInTheDocument();
      expect(screen.getByText('image3.jpg')).toBeInTheDocument();
      expect(screen.queryByText('image4.jpg')).not.toBeInTheDocument();
    });

    it('should show "顯示全部" button when there are more images', () => {
      render(<ArticleImagesList images={manyImages} initialDisplayCount={3} />);
      expect(screen.getByText('顯示全部 (10張)')).toBeInTheDocument();
    });

    it('should expand to show all images when "顯示全部" is clicked', () => {
      render(<ArticleImagesList images={manyImages} initialDisplayCount={3} />);
      fireEvent.click(screen.getByText('顯示全部 (10張)'));
      // Now all images should be visible
      expect(screen.getByText('image1.jpg')).toBeInTheDocument();
      expect(screen.getByText('image10.jpg')).toBeInTheDocument();
    });

    it('should show "收起" button after expanding', () => {
      render(<ArticleImagesList images={manyImages} initialDisplayCount={3} />);
      fireEvent.click(screen.getByText('顯示全部 (10張)'));
      expect(screen.getByText('收起')).toBeInTheDocument();
    });

    it('should collapse back when "收起" is clicked', () => {
      render(<ArticleImagesList images={manyImages} initialDisplayCount={3} />);
      fireEvent.click(screen.getByText('顯示全部 (10張)'));
      fireEvent.click(screen.getByText('收起'));
      // Should be back to 3 images
      expect(screen.getByText('image1.jpg')).toBeInTheDocument();
      expect(screen.queryByText('image4.jpg')).not.toBeInTheDocument();
    });

    it('should not show expand button when images count <= initialDisplayCount', () => {
      const fewImages = manyImages.slice(0, 2);
      render(<ArticleImagesList images={fewImages} initialDisplayCount={3} />);
      expect(screen.queryByText(/顯示全部/)).not.toBeInTheDocument();
    });
  });

  describe('URL Parsing', () => {
    it('should extract filename from standard URL', () => {
      const imageWithPath: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/path/to/my-image.jpg',
        },
      ];
      render(<ArticleImagesList images={imageWithPath} />);
      expect(screen.getByText('my-image.jpg')).toBeInTheDocument();
    });

    it('should handle URL with query parameters', () => {
      const imageWithQuery: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/path/image.jpg?size=large&quality=high',
        },
      ];
      render(<ArticleImagesList images={imageWithQuery} />);
      // The query parameters should be ignored in filename extraction
      expect(screen.getByText('image.jpg')).toBeInTheDocument();
    });

    it('should handle malformed URL gracefully', () => {
      const imageWithBadUrl: ArticleImage[] = [
        {
          id: 1,
          image_url: 'not-a-valid-url/image.png',
        },
      ];
      render(<ArticleImagesList images={imageWithBadUrl} />);
      // Should still extract filename
      expect(screen.getByText('image.png')).toBeInTheDocument();
    });
  });

  describe('External Link', () => {
    it('should show external link icon when source_url is provided', () => {
      const imageWithSource: ArticleImage[] = [
        {
          id: 1,
          image_url: 'https://example.com/image.jpg',
          alt_text: '測試圖片',
          source_url: 'https://original-source.com/image.jpg',
        },
      ];
      render(<ArticleImagesList images={imageWithSource} />);
      // Check for external link - there should be an <a> tag with the source URL
      const link = document.querySelector('a[href="https://original-source.com/image.jpg"]');
      expect(link).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible heading', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      const heading = screen.getByText(/文章圖片/);
      expect(heading.tagName).toBe('H4');
    });

    it('should have proper alt text on images', () => {
      render(<ArticleImagesList images={mockImagesWithAlt} />);
      // Images should have alt attribute
      const images = document.querySelectorAll('img');
      images.forEach((img) => {
        expect(img).toHaveAttribute('alt');
      });
    });
  });
});
