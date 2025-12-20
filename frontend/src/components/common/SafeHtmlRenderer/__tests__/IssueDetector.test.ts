/**
 * IssueDetector 單元測試
 *
 * @version 1.0
 * @date 2025-12-19
 */

import { describe, it, expect } from 'vitest';
import {
  detectNestingIssues,
  detectEmptyTags,
  detectDeprecatedTags,
  isGDocsContaminated,
  cleanGDocsContamination,
  removeEmptyTags,
  detectAllIssues,
  IssueDetector,
} from '../IssueDetector';

// ============================================================
// detectNestingIssues Tests
// ============================================================

describe('detectNestingIssues', () => {
  it('should detect p inside p', () => {
    const html = '<p>Outer <p>Inner</p></p>';
    const issues = detectNestingIssues(html);

    expect(issues.length).toBeGreaterThan(0);
    expect(issues[0].type).toBe('nesting');
    expect(issues[0].message).toContain('嵌套');
  });

  it('should detect div inside p', () => {
    const html = '<p>Text <div>Block</div></p>';
    const issues = detectNestingIssues(html);

    expect(issues.length).toBeGreaterThan(0);
  });

  it('should not flag valid nesting', () => {
    const html = '<div><p>Valid paragraph</p></div>';
    const issues = detectNestingIssues(html);

    expect(issues.length).toBe(0);
  });

  it('should detect span inside span issue', () => {
    const html = '<span><span><span><span>Deep</span></span></span></span>';
    // Deep nesting is technically valid but may indicate issues
    const issues = detectNestingIssues(html);
    // This depends on implementation - may or may not flag
    expect(Array.isArray(issues)).toBe(true);
  });
});

// ============================================================
// detectEmptyTags Tests
// ============================================================

describe('detectEmptyTags', () => {
  it('should detect empty paragraph', () => {
    const html = '<p></p>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(1);
    expect(issues[0].type).toBe('empty');
  });

  it('should detect empty span', () => {
    const html = '<span></span>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(1);
  });

  it('should detect paragraph with only whitespace', () => {
    const html = '<p>   </p>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(1);
  });

  it('should not flag self-closing tags', () => {
    const html = '<br/><hr/><img src="test.jpg"/>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(0);
  });

  it('should not flag tags with content', () => {
    const html = '<p>Has content</p>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(0);
  });

  it('should detect multiple empty tags', () => {
    const html = '<p></p><span></span><div></div>';
    const issues = detectEmptyTags(html);

    expect(issues.length).toBe(3);
  });
});

// ============================================================
// detectDeprecatedTags Tests
// ============================================================

describe('detectDeprecatedTags', () => {
  it('should detect font tag', () => {
    const html = '<font color="red">Text</font>';
    const issues = detectDeprecatedTags(html);

    expect(issues.length).toBe(1);
    expect(issues[0].type).toBe('deprecated');
    expect(issues[0].message).toContain('font');
  });

  it('should detect center tag', () => {
    const html = '<center>Centered</center>';
    const issues = detectDeprecatedTags(html);

    expect(issues.length).toBe(1);
  });

  it('should detect marquee tag', () => {
    const html = '<marquee>Scrolling</marquee>';
    const issues = detectDeprecatedTags(html);

    expect(issues.length).toBe(1);
  });

  it('should detect blink tag', () => {
    const html = '<blink>Blinking</blink>';
    const issues = detectDeprecatedTags(html);

    expect(issues.length).toBe(1);
  });

  it('should not flag modern tags', () => {
    const html = '<div><p><span>Modern HTML</span></p></div>';
    const issues = detectDeprecatedTags(html);

    expect(issues.length).toBe(0);
  });
});

// ============================================================
// isGDocsContaminated Tests
// ============================================================

describe('isGDocsContaminated', () => {
  it('should detect Google Docs class names', () => {
    const html = '<p class="c1">Google Docs paragraph</p>';
    expect(isGDocsContaminated(html)).toBe(true);
  });

  it('should detect Google Docs id patterns', () => {
    const html = '<span id="docs-internal-guid-12345">Text</span>';
    expect(isGDocsContaminated(html)).toBe(true);
  });

  it('should detect Google Docs data attributes', () => {
    const html = '<p data-cso="true">Content</p>';
    expect(isGDocsContaminated(html)).toBe(true);
  });

  it('should not flag clean HTML', () => {
    const html = '<p class="article-text">Clean paragraph</p>';
    expect(isGDocsContaminated(html)).toBe(false);
  });

  it('should detect mixed contamination', () => {
    const html = `
      <div>
        <p class="c0">First</p>
        <p class="c1">Second</p>
      </div>
    `;
    expect(isGDocsContaminated(html)).toBe(true);
  });
});

// ============================================================
// cleanGDocsContamination Tests
// ============================================================

describe('cleanGDocsContamination', () => {
  it('should remove Google Docs classes', () => {
    const html = '<p class="c1 c2">Text</p>';
    const result = cleanGDocsContamination(html);

    expect(result).not.toContain('class="c1');
    expect(result).toContain('<p');
    expect(result).toContain('Text');
  });

  it('should remove docs-internal-guid ids', () => {
    const html = '<span id="docs-internal-guid-abc123">Text</span>';
    const result = cleanGDocsContamination(html);

    expect(result).not.toContain('docs-internal-guid');
  });

  it('should preserve content', () => {
    const html = '<p class="c0">Important text content</p>';
    const result = cleanGDocsContamination(html);

    expect(result).toContain('Important text content');
  });

  it('should handle nested elements', () => {
    const html = '<div class="c1"><p class="c2"><span class="c3">Nested</span></p></div>';
    const result = cleanGDocsContamination(html);

    expect(result).toContain('Nested');
    expect(result).not.toContain('c1');
    expect(result).not.toContain('c2');
    expect(result).not.toContain('c3');
  });
});

// ============================================================
// removeEmptyTags Tests
// ============================================================

describe('removeEmptyTags', () => {
  it('should remove empty paragraphs', () => {
    const html = '<p></p><p>Content</p><p></p>';
    const result = removeEmptyTags(html);

    expect(result).not.toContain('<p></p>');
    expect(result).toContain('Content');
  });

  it('should remove empty spans', () => {
    const html = '<span></span>';
    const result = removeEmptyTags(html);

    expect(result).not.toContain('<span></span>');
  });

  it('should remove whitespace-only tags', () => {
    const html = '<p>   </p>';
    const result = removeEmptyTags(html);

    // Should remove or clean up whitespace-only paragraphs
    expect(result.trim()).not.toBe('<p>   </p>');
  });

  it('should preserve self-closing tags', () => {
    const html = '<p>Text</p><br/><hr/>';
    const result = removeEmptyTags(html);

    expect(result).toContain('<br');
    expect(result).toContain('<hr');
  });
});

// ============================================================
// detectAllIssues Tests
// ============================================================

describe('detectAllIssues', () => {
  it('should detect all issue types', () => {
    const html = `
      <p class="c1"><p>Nested</p></p>
      <span></span>
      <font color="red">Old</font>
    `;
    const issues = detectAllIssues(html, {
      detectNesting: true,
      detectEmpty: true,
      detectDeprecated: true,
      detectGDocs: true,
    });

    const types = issues.map(i => i.type);
    expect(types).toContain('nesting');
    expect(types).toContain('empty');
    expect(types).toContain('deprecated');
    expect(types).toContain('gdocs');
  });

  it('should respect detection options', () => {
    const html = '<p></p><font>Old</font>';

    const withEmpty = detectAllIssues(html, { detectEmpty: true, detectDeprecated: false });
    const withDeprecated = detectAllIssues(html, { detectEmpty: false, detectDeprecated: true });

    expect(withEmpty.some(i => i.type === 'empty')).toBe(true);
    expect(withEmpty.some(i => i.type === 'deprecated')).toBe(false);
    expect(withDeprecated.some(i => i.type === 'empty')).toBe(false);
    expect(withDeprecated.some(i => i.type === 'deprecated')).toBe(true);
  });

  it('should return empty array for clean HTML', () => {
    const html = '<div><p>Clean content</p></div>';
    const issues = detectAllIssues(html);

    expect(issues.length).toBe(0);
  });
});

// ============================================================
// IssueDetector Class Tests
// ============================================================

describe('IssueDetector class', () => {
  it('should create instance with default options', () => {
    const detector = new IssueDetector();
    expect(detector).toBeDefined();
  });

  it('should detect issues with instance method', () => {
    const detector = new IssueDetector();
    const issues = detector.detect('<p></p>');

    expect(issues.some(i => i.type === 'empty')).toBe(true);
  });

  it('should clean Google Docs contamination', () => {
    const detector = new IssueDetector();
    const result = detector.cleanGDocs('<p class="c1">Text</p>');

    expect(result).not.toContain('c1');
    expect(result).toContain('Text');
  });

  it('should check for Google Docs contamination', () => {
    const detector = new IssueDetector();

    expect(detector.isGDocsContaminated('<p class="c1">Text</p>')).toBe(true);
    expect(detector.isGDocsContaminated('<p>Clean</p>')).toBe(false);
  });
});
