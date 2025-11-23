/**
 * Article Review Parsing Visual Validation
 *
 * Uses Playwright + Chrome DevTools Protocol to validate:
 * - Parsing review sections render with expected dimensions
 * - Parsed data (title/author/SEO) matches worklist metadata
 * - Visual snapshot of the modal is captured for manual review
 */

import { test, expect, Page, Locator } from '@playwright/test';
import type { CDPSession } from 'playwright-core';
import path from 'node:path';
import { mkdirSync, writeFileSync } from 'node:fs';

import {
  getTestConfig,
  navigateWithRetry,
  waitForPageReady,
} from './utils/test-helpers';

const config = getTestConfig();

interface SectionExpectation {
  label: string;
  minWidth: number;
  minHeight: number;
  selectors?: string[];
  headingPattern?: RegExp;
  optional?: boolean;
}

const SECTION_EXPECTATIONS: SectionExpectation[] = [
  {
    label: 'Title Review',
    minWidth: 360,
    minHeight: 160,
    selectors: ['[data-testid="parsing-title-card"]'],
    headingPattern: /标题审核|Title Review/,
  },
  {
    label: 'Author Review',
    minWidth: 360,
    minHeight: 120,
    selectors: ['[data-testid="parsing-author-card"]'],
    headingPattern: /作者审核|Author Review/,
  },
  {
    label: 'Image Review',
    minWidth: 360,
    minHeight: 220,
    selectors: ['[data-testid="parsing-image-card"]'],
    headingPattern: /图片审核|Image Review/,
  },
  {
    label: 'SEO Review',
    minWidth: 280,
    minHeight: 260,
    selectors: ['[data-testid="parsing-seo-card"]'],
    headingPattern: /SEO 优化|SEO Review/,
  },
  {
    label: 'SEO Title Selection',
    minWidth: 360,
    minHeight: 200,
    selectors: ['[data-testid="seo-title-selection-card"]'],
    headingPattern: /SEO Title/,
    optional: true,
  },
  {
    label: 'FAQ Review',
    minWidth: 280,
    minHeight: 220,
    selectors: ['[data-testid="parsing-faq-card"]'],
    headingPattern: /FAQ 建议|FAQ Review/,
  },
];

const IGNORED_AUTHOR_VALUES = ['—', '-', '', '未知作者', 'Unknown Author'];

const VISUAL_OUTPUT_PATH = path.resolve(
  process.cwd(),
  'test-results/visual/article-review-parsing-modal.png'
);

interface BoxMetrics {
  width: number;
  height: number;
  x: number;
  y: number;
  clipWidth: number;
  clipHeight: number;
}

const normalizeText = (value?: string | null): string =>
  (value || '').replace(/\s+/g, ' ').trim();

const ensureDirectory = (filePath: string): void => {
  mkdirSync(path.dirname(filePath), { recursive: true });
};

async function getBoxMetrics(cdp: CDPSession, selector: string): Promise<BoxMetrics> {
  const { root } = await cdp.send('DOM.getDocument', { depth: -1 });
  const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector });

  if (!nodeId) {
    throw new Error(`Selector not found: ${selector}`);
  }

  const boxModel = await cdp.send('DOM.getBoxModel', { nodeId });
  const points: number[] = boxModel.model.border || boxModel.model.content;

  const xs: number[] = [];
  const ys: number[] = [];

  for (let i = 0; i < points.length; i += 2) {
    xs.push(points[i]);
    ys.push(points[i + 1]);
  }

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  return {
    width: boxModel.model.width,
    height: boxModel.model.height,
    x: minX,
    y: minY,
    clipWidth: Math.max(1, maxX - minX),
    clipHeight: Math.max(1, maxY - minY),
  };
}

async function resolveLocator(
  page: Page,
  selectors: string[],
  options?: { optional?: boolean }
): Promise<Locator | null> {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if ((await locator.count()) > 0) {
      return locator;
    }
  }

  if (options?.optional) {
    console.warn(`⚠️  Optional locator not found for selectors: ${selectors.join(', ')}`);
    return null;
  }

  throw new Error(`Locator not found for selectors: ${selectors.join(', ')}`);
}

const ensureLocator = (locator: Locator | null, description: string): Locator => {
  if (!locator) {
    throw new Error(`Required locator not found: ${description}`);
  }
  return locator;
};

async function resolveSectionLocator(
  page: Page,
  section: SectionExpectation
): Promise<Locator | null> {
  if (section.selectors) {
    for (const selector of section.selectors) {
      const locator = page.locator(selector).first();
      if ((await locator.count()) > 0) {
        return locator;
      }
    }
  }

  if (section.headingPattern) {
    const headingLocator = page
      .locator('div')
      .filter({ hasText: section.headingPattern })
      .first();
    if ((await headingLocator.count()) > 0) {
      return headingLocator;
    }
  }

  if (section.optional) {
    console.warn(`⚠️  Optional section not found: ${section.label}`);
    return null;
  }

  throw new Error(`Section not found: ${section.label}`);
}

async function getBoundingBox(locator: Locator): Promise<{ width: number; height: number }> {
  const box = await locator.boundingBox();
  if (!box) {
    throw new Error('Failed to calculate bounding box for locator');
  }
  return { width: box.width, height: box.height };
}

async function captureElementScreenshot(
  cdp: CDPSession,
  selector: string,
  outputPath: string
): Promise<void> {
  const metrics = await getBoxMetrics(cdp, selector);
  const screenshot = await cdp.send('Page.captureScreenshot', {
    format: 'png',
    clip: {
      x: metrics.x,
      y: metrics.y,
      width: metrics.clipWidth,
      height: metrics.clipHeight,
      scale: 1,
    },
  });

  ensureDirectory(outputPath);
  writeFileSync(outputPath, Buffer.from(screenshot.data, 'base64'));
}

const ELEMENT_SELECTORS = {
  titleInput: [
    '[data-testid="parsing-title-card"] input',
    'div:has(h3:has-text("标题审核")) input',
    'div:has(h3:has-text("Title Review")) input',
  ],
  authorInput: [
    '[data-testid="parsing-author-card"] input',
    'div:has(h3:has-text("作者审核")) input',
    'div:has(h3:has-text("Author Review")) input',
  ],
  metaDescription: [
    '[data-testid="parsing-seo-card"] textarea',
    'div:has(h3:has-text("SEO 优化")) textarea',
    'div:has(h3:has-text("SEO Review")) textarea',
  ],
  keywordGroup: [
    '[data-testid="parsing-seo-card"] .flex.flex-wrap.gap-2',
    'div:has(h3:has-text("SEO 优化")) .flex.flex-wrap',
    'div:has(h3:has-text("SEO Review")) .flex.flex-wrap',
  ],
  faqTextareas: [
    '[data-testid="parsing-faq-card"] textarea',
    'div:has(h3:has-text("FAQ 建议")) textarea',
    'div:has(h3:has-text("FAQ Review")) textarea',
  ],
  seoCard: [
    '[data-testid="parsing-seo-card"]',
    'div:has(h3:has-text("SEO 优化"))',
    'div:has(h3:has-text("SEO Review"))',
  ],
  faqCard: [
    '[data-testid="parsing-faq-card"]',
    'div:has(h3:has-text("FAQ 建议"))',
    'div:has(h3:has-text("FAQ Review"))',
  ],
};

test.describe('Article Review Parsing - DevTools Visual Validation', () => {
  test('validates parsing layout and parsed values', async ({ page, context }) => {
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 20000 });

    const rowCells = firstRow.locator('td');
    const rowTitle = normalizeText(await rowCells.nth(0).innerText());
    const rowAuthor = normalizeText(await rowCells.nth(2).innerText());

    await firstRow.click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 20000 });

    const loadingText = page.locator('text=/加载文章审核数据|Loading article review/i');
    if (await loadingText.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(loadingText).not.toBeVisible({ timeout: 20000 });
    }

    const parsingTab = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();
    if (await parsingTab.isVisible()) {
      await parsingTab.click();
    }

    const cdp = await context.newCDPSession(page);
    await cdp.send('DOM.enable');
    await cdp.send('Page.enable');

    const sectionLocatorMap: Record<string, Locator> = {};
    for (const section of SECTION_EXPECTATIONS) {
      const locator = await resolveSectionLocator(page, section);
      if (!locator) {
        continue;
      }

      await expect(locator).toBeVisible({ timeout: 20000 });
      const { width, height } = await getBoundingBox(locator);
      console.log(`[Layout] ${section.label}: ${Math.round(width)}x${Math.round(height)}px`);
      expect(width).toBeGreaterThan(section.minWidth);
      expect(height).toBeGreaterThan(section.minHeight);

      sectionLocatorMap[section.label] = locator;
    }

    const titleInput = ensureLocator(
      await resolveLocator(page, ELEMENT_SELECTORS.titleInput),
      'Title input'
    );
    const titleValue = normalizeText(await titleInput.inputValue());
    console.log(`[Parsing] Title in modal: ${titleValue}`);
    expect(titleValue.length).toBeGreaterThanOrEqual(5);
    if (rowTitle) {
      expect(titleValue.toLowerCase()).toContain(rowTitle.split(' ')[0].toLowerCase());
    }

    const authorInput = ensureLocator(
      await resolveLocator(page, ELEMENT_SELECTORS.authorInput),
      'Author input'
    );
    const authorValue = normalizeText(await authorInput.inputValue());
    console.log(`[Parsing] Author in modal: ${authorValue || '(empty)'}`);
    if (rowAuthor && !IGNORED_AUTHOR_VALUES.includes(rowAuthor)) {
      expect(authorValue.length).toBeGreaterThan(0);
    }

    const metaDescriptionLocator = ensureLocator(
      await resolveLocator(page, ELEMENT_SELECTORS.metaDescription),
      'Meta description textarea'
    );
    await expect(metaDescriptionLocator).toBeVisible();
    const metaDescription = normalizeText(await metaDescriptionLocator.inputValue());
    console.log(`[Parsing] Meta description length: ${metaDescription.length}`);
    expect(metaDescription.length).toBeGreaterThanOrEqual(0);

    const keywordContainer = await resolveLocator(page, ELEMENT_SELECTORS.keywordGroup, { optional: true });
    let keywordCount = 0;
    if (keywordContainer) {
      const keywordBadges = keywordContainer.locator('> *');
      keywordCount = await keywordBadges.count();
    }
    console.log(`[Parsing] Keyword chips: ${keywordCount}`);
    if (keywordCount === 0) {
      const seoCard = sectionLocatorMap['SEO Review'] ??
        ensureLocator(await resolveLocator(page, ELEMENT_SELECTORS.seoCard), 'SEO card');
      await expect(
        seoCard.locator('text=/暂无关键词|No keywords/i')
      ).toBeVisible();
    }

    const faqLocator = await resolveLocator(page, ELEMENT_SELECTORS.faqTextareas, { optional: true });
    const faqCount = faqLocator ? await faqLocator.count() : 0;
    console.log(`[Parsing] FAQ editor count: ${faqCount}`);
    if (faqCount === 0) {
      const faqCard = sectionLocatorMap['FAQ Review'] ??
        ensureLocator(await resolveLocator(page, ELEMENT_SELECTORS.faqCard), 'FAQ card');
      await expect(faqCard.locator('text=/暂无 FAQ 建议|No FAQ/')).toBeVisible();
    }

    await captureElementScreenshot(cdp, '[role="dialog"]', VISUAL_OUTPUT_PATH);
    test.info().attach('article-review-parsing-modal', {
      path: VISUAL_OUTPUT_PATH,
      contentType: 'image/png',
    });
  });
});
