/**
 * FontAnalyzer 單元測試
 *
 * @version 1.0
 * @date 2025-12-19
 */

import { describe, it, expect } from 'vitest';
import {
  parseFontFamily,
  checkFont,
  analyzeHtmlFonts,
  removeProblematicFonts,
  replaceFont,
  FontAnalyzer,
} from '../FontAnalyzer';

// ============================================================
// parseFontFamily Tests
// ============================================================

describe('parseFontFamily', () => {
  it('should parse single font', () => {
    expect(parseFontFamily('Arial')).toEqual(['Arial']);
  });

  it('should parse font with quotes', () => {
    expect(parseFontFamily('"Times New Roman"')).toEqual(['Times New Roman']);
    expect(parseFontFamily("'Noto Sans SC'")).toEqual(['Noto Sans SC']);
  });

  it('should parse font stack', () => {
    expect(parseFontFamily('"Segoe UI", Arial, sans-serif')).toEqual([
      'Segoe UI',
      'Arial',
      'sans-serif',
    ]);
  });

  it('should handle mixed quotes', () => {
    expect(parseFontFamily('"Times New Roman", \'Arial\', sans-serif')).toEqual([
      'Times New Roman',
      'Arial',
      'sans-serif',
    ]);
  });

  it('should handle empty string', () => {
    expect(parseFontFamily('')).toEqual([]);
  });

  it('should handle whitespace', () => {
    expect(parseFontFamily('  Arial  ,  Helvetica  ')).toEqual(['Arial', 'Helvetica']);
  });
});

// ============================================================
// checkFont Tests
// ============================================================

describe('checkFont', () => {
  describe('system fonts', () => {
    it('should accept -apple-system', () => {
      const result = checkFont('-apple-system');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('system');
      expect(result.severity).toBe('ok');
    });

    it('should accept Segoe UI', () => {
      const result = checkFont('Segoe UI');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('system');
    });

    it('should accept sans-serif', () => {
      const result = checkFont('sans-serif');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('system');
    });
  });

  describe('Chinese fonts', () => {
    it('should accept Noto Sans SC', () => {
      const result = checkFont('Noto Sans SC');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('chinese');
    });

    it('should accept Microsoft YaHei', () => {
      const result = checkFont('Microsoft YaHei');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('chinese');
    });

    it('should accept PingFang SC', () => {
      const result = checkFont('PingFang SC');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('chinese');
    });
  });

  describe('web-safe fonts', () => {
    it('should accept Arial', () => {
      const result = checkFont('Arial');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('web-safe');
    });

    it('should accept Helvetica', () => {
      const result = checkFont('Helvetica');
      expect(result.isValid).toBe(true);
      expect(result.category).toBe('web-safe');
    });
  });

  describe('problematic fonts', () => {
    it('should warn about Times New Roman', () => {
      const result = checkFont('Times New Roman');
      expect(result.isValid).toBe(false);
      expect(result.category).toBe('problematic');
      expect(result.severity).toBe('warning');
      expect(result.message).toContain('Times New Roman');
    });

    it('should warn about Calibri', () => {
      const result = checkFont('Calibri');
      expect(result.isValid).toBe(false);
      expect(result.category).toBe('problematic');
      expect(result.severity).toBe('warning');
    });

    it('should warn about Comic Sans MS', () => {
      const result = checkFont('Comic Sans MS');
      expect(result.isValid).toBe(false);
      expect(result.category).toBe('problematic');
    });

    it('should warn about SimSun as print font', () => {
      const result = checkFont('SimSun');
      expect(result.isValid).toBe(false);
      expect(result.category).toBe('problematic');
      expect(result.message).toContain('印刷');
    });

    it('should warn about 宋体 as print font', () => {
      const result = checkFont('宋体');
      expect(result.isValid).toBe(false);
      expect(result.message).toContain('印刷');
    });
  });

  describe('unknown fonts', () => {
    it('should mark unknown fonts as info', () => {
      const result = checkFont('SomeRandomFont');
      expect(result.isValid).toBe(false);
      expect(result.category).toBe('unknown');
      expect(result.severity).toBe('info');
      expect(result.message).toContain('未識別');
    });
  });

  describe('font stacks', () => {
    it('should check primary font in stack', () => {
      const result = checkFont('"Times New Roman", Arial, sans-serif');
      expect(result.isValid).toBe(false);
      expect(result.primaryFont).toBe('Times New Roman');
      expect(result.fallbackFonts).toEqual(['Arial', 'sans-serif']);
    });

    it('should pass if primary font is valid', () => {
      const result = checkFont('Arial, "Times New Roman", sans-serif');
      expect(result.isValid).toBe(true);
      expect(result.primaryFont).toBe('Arial');
    });
  });
});

// ============================================================
// analyzeHtmlFonts Tests
// ============================================================

describe('analyzeHtmlFonts', () => {
  it('should detect font-family in style attribute', () => {
    const html = '<p style="font-family: Times New Roman">Test</p>';
    const result = analyzeHtmlFonts(html);

    expect(result.hasProblematicFonts).toBe(true);
    expect(result.issues.length).toBe(1);
    expect(result.issues[0].type).toBe('font');
  });

  it('should detect multiple font declarations', () => {
    const html = `
      <p style="font-family: Calibri">First</p>
      <p style="font-family: Times New Roman">Second</p>
    `;
    const result = analyzeHtmlFonts(html);

    expect(result.issues.length).toBe(2);
    expect(result.uniqueFonts).toContain('Calibri');
    expect(result.uniqueFonts).toContain('Times New Roman');
  });

  it('should not create issues for valid fonts', () => {
    const html = '<p style="font-family: Arial">Test</p>';
    const result = analyzeHtmlFonts(html);

    expect(result.hasProblematicFonts).toBe(false);
    expect(result.issues.length).toBe(0);
  });

  it('should handle quoted font names', () => {
    const html = `<p style="font-family: 'Times New Roman'">Test</p>`;
    const result = analyzeHtmlFonts(html);

    expect(result.hasProblematicFonts).toBe(true);
  });

  it('should record issue position', () => {
    const html = '<p style="font-family: Calibri">Test</p>';
    const result = analyzeHtmlFonts(html);

    expect(result.issues[0].position.start).toBeGreaterThanOrEqual(0);
    expect(result.issues[0].position.end).toBeGreaterThan(result.issues[0].position.start);
  });
});

// ============================================================
// removeProblematicFonts Tests
// ============================================================

describe('removeProblematicFonts', () => {
  it('should remove font-family from style', () => {
    const html = '<p style="font-family: Times New Roman; color: red;">Test</p>';
    const result = removeProblematicFonts(html);

    expect(result).not.toContain('font-family');
    expect(result).toContain('color: red');
  });

  it('should remove empty style attributes', () => {
    const html = '<p style="font-family: Times New Roman;">Test</p>';
    const result = removeProblematicFonts(html);

    expect(result).not.toContain('style=""');
  });

  it('should handle multiple elements', () => {
    const html = `
      <p style="font-family: Calibri">First</p>
      <span style="font-family: Arial">Second</span>
    `;
    const result = removeProblematicFonts(html);

    expect(result).not.toContain('Calibri');
    expect(result).not.toContain('Arial');
  });
});

// ============================================================
// replaceFont Tests
// ============================================================

describe('replaceFont', () => {
  it('should replace specific font', () => {
    const html = '<p style="font-family: Times New Roman">Test</p>';
    const result = replaceFont(html, 'Times New Roman', 'Arial');

    expect(result).toContain('font-family: Arial');
    expect(result).not.toContain('Times New Roman');
  });

  it('should replace with inherit by default', () => {
    const html = '<p style="font-family: Calibri">Test</p>';
    const result = replaceFont(html, 'Calibri');

    expect(result).toContain('font-family: inherit');
  });
});

// ============================================================
// FontAnalyzer Class Tests
// ============================================================

describe('FontAnalyzer class', () => {
  it('should create instance with default fonts', () => {
    const analyzer = new FontAnalyzer();
    const fonts = analyzer.getAllowedFonts();

    expect(fonts.length).toBeGreaterThan(0);
    expect(fonts).toContain('Arial');
  });

  it('should create instance with custom fonts', () => {
    const analyzer = new FontAnalyzer(['CustomFont']);
    const result = analyzer.checkFont('CustomFont');

    expect(result.isValid).toBe(true);
  });

  it('should add allowed font', () => {
    const analyzer = new FontAnalyzer([]);
    analyzer.addAllowedFont('NewFont');

    const fonts = analyzer.getAllowedFonts();
    expect(fonts).toContain('NewFont');
  });

  it('should analyze HTML', () => {
    const analyzer = new FontAnalyzer();
    const result = analyzer.analyze('<p style="font-family: Calibri">Test</p>');

    expect(result.hasProblematicFonts).toBe(true);
  });
});
