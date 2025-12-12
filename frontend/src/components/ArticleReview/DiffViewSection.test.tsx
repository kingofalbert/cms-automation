/**
 * DiffViewSection Component Tests
 *
 * Phase 8.4: Tests for the diff visualization component used in proofreading review.
 * Tests cover rendering, view mode switching, stats display, and edge cases.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DiffViewSection, type DiffStats } from './DiffViewSection';

describe('DiffViewSection', () => {
  // Sample test data
  const mockOriginalContent = `健康飲食對身體很重要。
每天應該喝八杯水。
多吃蔬菜和水果。`;

  const mockProofreadContent = `健康均衡飲食對身體非常重要。
每天應該喝八杯水。
多吃新鮮蔬菜和有機水果。
適量運動有助於健康。`;

  const mockDiffStats: DiffStats = {
    additions: 2,
    deletions: 1,
    total_changes: 3,
    original_lines: 3,
    suggested_lines: 4,
  };

  describe('Rendering', () => {
    it('should render without crashing', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
    });

    it('should render diff viewer when content has changes', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Check that the diff viewer is rendered (by looking for titles)
      expect(screen.getByText('原始内容')).toBeInTheDocument();
      expect(screen.getByText('校对后内容')).toBeInTheDocument();
    });

    it('should show no changes message when content is identical', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockOriginalContent}
        />
      );
      expect(screen.getByText('内容未修改')).toBeInTheDocument();
      expect(
        screen.getByText('AI 校对后内容与原始内容完全一致')
      ).toBeInTheDocument();
    });

    it('should display statistics section', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          diffStats={mockDiffStats}
        />
      );
      expect(screen.getByText('原始')).toBeInTheDocument();
      expect(screen.getByText('校对后')).toBeInTheDocument();
      expect(screen.getByText('新增')).toBeInTheDocument();
      expect(screen.getByText('删除')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
    });

    it('should show pre-generated diff indicator when hasDiffData is true', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          hasDiffData={true}
        />
      );
      expect(
        screen.getByText('使用后端预生成的词级差异数据')
      ).toBeInTheDocument();
    });

    it('should not show pre-generated diff indicator when hasDiffData is false', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          hasDiffData={false}
        />
      );
      expect(
        screen.queryByText('使用后端预生成的词级差异数据')
      ).not.toBeInTheDocument();
    });
  });

  describe('View Mode Switching', () => {
    it('should start with split view mode by default', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      const splitButton = screen.getByTitle('分栏视图');
      expect(splitButton).toHaveClass('bg-primary-600');
    });

    it('should switch to unified view when unified button is clicked', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      const unifiedButton = screen.getByTitle('统一视图');
      fireEvent.click(unifiedButton);
      expect(unifiedButton).toHaveClass('bg-primary-600');
    });

    it('should switch back to split view when split button is clicked', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Click unified first
      fireEvent.click(screen.getByTitle('统一视图'));
      // Then click split
      const splitButton = screen.getByTitle('分栏视图');
      fireEvent.click(splitButton);
      expect(splitButton).toHaveClass('bg-primary-600');
    });
  });

  describe('Line Numbers Toggle', () => {
    it('should toggle line numbers when button is clicked', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Find the line number toggle button (it has # as text)
      const lineNumberButton = screen.getByText('#');
      expect(lineNumberButton).toHaveClass('bg-gray-100'); // Initially shown

      fireEvent.click(lineNumberButton);
      expect(lineNumberButton).not.toHaveClass('bg-gray-100'); // Now hidden
    });
  });

  describe('Statistics Display', () => {
    it('should display provided diff stats', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          diffStats={mockDiffStats}
        />
      );
      // Check that stats are rendered - use container queries for specificity
      // Additions are in green, deletions in red
      const additionsElement = screen.getByText('2', {
        selector: '.font-medium.text-green-700',
      });
      const deletionsElement = screen.getByText('1', {
        selector: '.font-medium.text-red-700',
      });
      expect(additionsElement).toBeInTheDocument();
      expect(deletionsElement).toBeInTheDocument();
    });

    it('should calculate stats when not provided', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Should calculate and display stats based on content
      expect(screen.getByText('原始')).toBeInTheDocument();
      expect(screen.getByText('校对后')).toBeInTheDocument();
    });

    it('should display character counts', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Check for character count display
      expect(
        screen.getByText(`${mockOriginalContent.length} 字符`)
      ).toBeInTheDocument();
      expect(
        screen.getByText(`${mockProofreadContent.length} 字符`)
      ).toBeInTheDocument();
    });

    it('should show status as "有修改" when content has changes', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('有修改')).toBeInTheDocument();
    });

    it('should show status as "无修改" when content is identical', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockOriginalContent}
        />
      );
      expect(screen.getByText('无修改')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty original content', () => {
      render(
        <DiffViewSection
          originalContent=""
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
      expect(screen.getByText('有修改')).toBeInTheDocument();
    });

    it('should handle empty proofread content', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent=""
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
      expect(screen.getByText('有修改')).toBeInTheDocument();
    });

    it('should handle both contents being empty', () => {
      render(<DiffViewSection originalContent="" proofreadContent="" />);
      expect(screen.getByText('内容未修改')).toBeInTheDocument();
    });

    it('should handle very long content', () => {
      const longContent = '這是一段很長的文字。'.repeat(1000);
      const modifiedLongContent = '這是一段經過修改的很長的文字。'.repeat(1000);

      render(
        <DiffViewSection
          originalContent={longContent}
          proofreadContent={modifiedLongContent}
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
    });

    it('should handle special characters and punctuation', () => {
      const specialContent = '特殊字符：@#$%^&*()，。！？「」';
      const modifiedSpecialContent = '特殊字符：@#$%^&*()，。！？《》';

      render(
        <DiffViewSection
          originalContent={specialContent}
          proofreadContent={modifiedSpecialContent}
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
    });

    it('should handle mixed Chinese and English content', () => {
      const mixedContent = '使用Python進行數據分析，Hello World！';
      const modifiedMixedContent = '使用Python3進行大數據分析，Hello World!';

      render(
        <DiffViewSection
          originalContent={mixedContent}
          proofreadContent={modifiedMixedContent}
        />
      );
      expect(screen.getByText('对比视图')).toBeInTheDocument();
    });

    it('should handle whitespace-only differences', () => {
      const original = '這是一段文字';
      const withWhitespace = '這是 一段 文字';

      render(
        <DiffViewSection
          originalContent={original}
          proofreadContent={withWhitespace}
        />
      );
      expect(screen.getByText('有修改')).toBeInTheDocument();
    });

    it('should handle newline differences', () => {
      const original = '第一行\n第二行\n第三行';
      const withExtraNewlines = '第一行\n\n第二行\n\n第三行';

      render(
        <DiffViewSection
          originalContent={original}
          proofreadContent={withExtraNewlines}
        />
      );
      expect(screen.getByText('有修改')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button titles', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      expect(screen.getByTitle('分栏视图')).toBeInTheDocument();
      expect(screen.getByTitle('统一视图')).toBeInTheDocument();
    });

    it('should have semantic headings', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
        />
      );
      // Check for heading
      const heading = screen.getByText('对比视图');
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Integration with Backend Diff Data', () => {
    it('should properly use backend-provided stats', () => {
      const backendStats: DiffStats = {
        additions: 5,
        deletions: 3,
        total_changes: 8,
        original_lines: 10,
        suggested_lines: 12,
      };

      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          diffStats={backendStats}
          hasDiffData={true}
        />
      );

      // Check that backend stats are displayed - use specific selectors
      const additionsElement = screen.getByText('5', {
        selector: '.font-medium.text-green-700',
      });
      const deletionsElement = screen.getByText('3', {
        selector: '.font-medium.text-red-700',
      });
      expect(additionsElement).toBeInTheDocument();
      expect(deletionsElement).toBeInTheDocument();
    });

    it('should handle undefined diffStats gracefully', () => {
      render(
        <DiffViewSection
          originalContent={mockOriginalContent}
          proofreadContent={mockProofreadContent}
          diffStats={undefined}
        />
      );
      // Should calculate stats automatically
      expect(screen.getByText('原始')).toBeInTheDocument();
    });
  });
});
