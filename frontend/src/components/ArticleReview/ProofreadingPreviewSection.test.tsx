/**
 * ProofreadingPreviewSection Component Tests
 *
 * Phase 8.4: Tests for the real-time preview component in proofreading review.
 * Tests cover rendering, highlight toggling, stats display, and edge cases.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProofreadingPreviewSection, type WordChange } from './ProofreadingPreviewSection';

describe('ProofreadingPreviewSection', () => {
  // Sample test data
  const mockOriginalContent = `健康飲食對身體很重要。
每天應該喝八杯水。
多吃蔬菜和水果。`;

  const mockProofreadContent = `健康均衡飲食對身體非常重要。
每天應該喝八杯水。
多吃新鮮蔬菜和有機水果。
適量運動有助於健康。`;

  const mockWordChanges: WordChange[] = [
    {
      type: 'replace',
      original: '很',
      suggested: '非常',
      original_pos: [4, 5],
      suggested_pos: [5, 6],
    },
    {
      type: 'insert',
      suggested: '新鮮',
      suggested_pos: [15, 16],
    },
  ];

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should render proofread content', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Check that content is displayed
      expect(screen.getByText(/健康均衡飲食/)).toBeInTheDocument();
    });

    it('should show no changes message when content is identical', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockOriginalContent}
        />
      );
      expect(screen.getByText('内容无需修改')).toBeInTheDocument();
      expect(
        screen.getByText('AI 校对认为原文已经很好，无需调整')
      ).toBeInTheDocument();
    });

    it('should display statistics section', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('字数')).toBeInTheDocument();
      expect(screen.getByText('新增')).toBeInTheDocument();
      expect(screen.getByText('修改')).toBeInTheDocument();
      expect(screen.getByText('删除')).toBeInTheDocument();
    });
  });

  describe('Highlight Toggle', () => {
    it('should have highlight toggle button in text mode', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Switch to text mode first (default is rendered mode)
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      // Now highlight button should be visible
      const highlightButton = screen.getByTitle('隐藏高亮');
      expect(highlightButton).toBeInTheDocument();
    });

    it('should toggle highlight when button is clicked', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Switch to text mode first
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      // Now find and click highlight button
      const highlightButton = screen.getByTitle('隐藏高亮');
      fireEvent.click(highlightButton);
      // Button should now say show highlights
      expect(screen.getByTitle('显示高亮')).toBeInTheDocument();
    });

    it('should show legend when highlights are enabled in text mode', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          wordChanges={mockWordChanges}
        />
      );
      // Switch to text mode first
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      expect(screen.getByText('图例:')).toBeInTheDocument();
    });
  });

  describe('Original Inline Toggle', () => {
    it('should show original inline toggle when in text mode with highlights enabled', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Switch to text mode first
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      expect(screen.getByTitle('显示原文')).toBeInTheDocument();
    });

    it('should hide original inline toggle when highlights are disabled', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Switch to text mode first
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      // Disable highlights
      fireEvent.click(screen.getByTitle('隐藏高亮'));
      // Original inline toggle should not be visible
      expect(screen.queryByTitle('显示原文')).not.toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('should display character count', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(
        screen.getByText(`${mockProofreadContent.length.toLocaleString('zh-CN')}`)
      ).toBeInTheDocument();
    });

    it('should display line count', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      const lineCount = mockProofreadContent.split('\n').length;
      expect(screen.getByText(`${lineCount} 行`)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty original content', () => {
      render(
        <ProofreadingPreviewSection
          originalContent=""
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle empty proofread content', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent=""
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle both contents being empty', () => {
      render(<ProofreadingPreviewSection originalContent="" proofreadContent="" />);
      expect(screen.getByText('内容无需修改')).toBeInTheDocument();
    });

    it('should handle very long content', () => {
      const longContent = '這是一段很長的文字。'.repeat(1000);
      const modifiedLongContent = '這是一段經過修改的很長的文字。'.repeat(1000);

      render(
        <ProofreadingPreviewSection
          originalContent={longContent}
          proofreadContent={modifiedLongContent}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle special characters', () => {
      const specialContent = '特殊字符：@#$%^&*()，。！？《》';
      const modifiedSpecialContent = '特殊字符：@#$%^&*()，。！？「」';

      render(
        <ProofreadingPreviewSection
          originalContent={specialContent}
          proofreadContent={modifiedSpecialContent}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle undefined originalContent', () => {
      render(
        <ProofreadingPreviewSection
          // @ts-expect-error - Testing undefined content
          originalContent={undefined}
          proofreadContent="有內容"
        />
      );
      // Should render without crashing
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle undefined proofreadContent', () => {
      render(
        <ProofreadingPreviewSection
          originalContent="有內容"
          // @ts-expect-error - Testing undefined content
          proofreadContent={undefined}
        />
      );
      // Should render without crashing
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle both contents being undefined', () => {
      render(
        <ProofreadingPreviewSection
          // @ts-expect-error - Testing undefined content
          originalContent={undefined}
          // @ts-expect-error - Testing undefined content
          proofreadContent={undefined}
        />
      );
      // Should render without crashing
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle null originalContent', () => {
      render(
        <ProofreadingPreviewSection
          // @ts-expect-error - Testing null content
          originalContent={null}
          proofreadContent="有內容"
        />
      );
      // Should render without crashing
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle null proofreadContent', () => {
      render(
        <ProofreadingPreviewSection
          originalContent="有內容"
          // @ts-expect-error - Testing null content
          proofreadContent={null}
        />
      );
      // Should render without crashing
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle content with HTML tags (for rendered mode)', () => {
      const htmlContent = '<p>這是<strong>粗體</strong>文字</p>';
      const modifiedHtml = '<p>這是<strong>加粗</strong>文字</p>';

      render(
        <ProofreadingPreviewSection
          originalContent={htmlContent}
          proofreadContent={modifiedHtml}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle content with emoji', () => {
      const emojiContent = '健康飲食 🥗 很重要';
      const modifiedEmoji = '健康飲食 🥗🍎 非常重要';

      render(
        <ProofreadingPreviewSection
          originalContent={emojiContent}
          proofreadContent={modifiedEmoji}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle content with only whitespace changes', () => {
      const original = '這是 一段 文字';
      const modified = '這是  一段  文字';

      render(
        <ProofreadingPreviewSection
          originalContent={original}
          proofreadContent={modified}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });
  });

  describe('Word Changes Integration', () => {
    it('should handle provided word changes', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          wordChanges={mockWordChanges}
        />
      );
      // Should render without errors
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle empty word changes array', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          wordChanges={[]}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });

    it('should handle undefined word changes', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          wordChanges={undefined}
        />
      );
      expect(screen.getByText('预览模式')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button titles in text mode', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Switch to text mode first
      const textModeButton = screen.getByTitle('文本模式：显示修改高亮');
      fireEvent.click(textModeButton);
      expect(screen.getByTitle('隐藏高亮')).toBeInTheDocument();
      expect(screen.getByTitle('显示原文')).toBeInTheDocument();
    });

    it('should have view mode toggle buttons', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByTitle('渲染模式：显示最终排版效果')).toBeInTheDocument();
      expect(screen.getByTitle('文本模式：显示修改高亮')).toBeInTheDocument();
    });

    it('should have semantic headings', () => {
      render(
        <ProofreadingPreviewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      const heading = screen.getByText('预览模式');
      expect(heading.tagName).toBe('H3');
    });
  });
});
