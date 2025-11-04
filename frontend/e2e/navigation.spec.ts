import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:3001'
  : 'https://storage.googleapis.com/cms-automation-frontend-2025';

test.describe('Navigation Component', () => {
  test.describe('Desktop Navigation', () => {
    test('should display all navigation links on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto(BASE_URL);

      // Check that desktop navigation is visible
      const desktopNav = page.locator('nav div.hidden.md\\:flex');
      await expect(desktopNav).toBeVisible();

      // Verify all expected navigation items are present in desktop nav
      const expectedNavItems = [
        '首頁',
        '生成文章',
        '導入文章',
        '文章列表',
        '發佈任務',
        '提供商對比',
        '設置',
        '工作清單',
        '排程管理',
        '標籤管理',
        '校對規則',
        '已發佈規則',
        '校對統計',
      ];

      for (const item of expectedNavItems) {
        // Target links specifically in desktop nav
        await expect(desktopNav.getByRole('link', { name: item })).toBeVisible();
      }
    });

    test('should not wrap navigation text on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto(BASE_URL);

      // Get the navigation container
      const navContainer = page.locator('nav div.hidden.md\\:flex');

      // Check that the container has flex-nowrap class
      await expect(navContainer).toHaveClass(/flex-nowrap/);

      // Check that links have whitespace-nowrap
      const firstLink = navContainer.locator('a').first();
      await expect(firstLink).toHaveClass(/whitespace-nowrap/);
    });

    test('should highlight active navigation item', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto(BASE_URL);

      // Home page should be active by default in desktop nav
      const desktopNav = page.locator('nav div.hidden.md\\:flex');
      const homeLink = desktopNav.getByRole('link', { name: '首頁' });
      await expect(homeLink).toHaveClass(/bg-blue-100/);
      await expect(homeLink).toHaveClass(/text-blue-700/);
    });

    test('should navigate to different pages when clicking links', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto(BASE_URL);

      // Click on "文章列表" link in desktop nav
      const desktopNav = page.locator('nav div.hidden.md\\:flex');
      await desktopNav.getByRole('link', { name: '文章列表' }).click();

      // Verify URL changed
      await expect(page).toHaveURL(/\/articles/);

      // Verify the link is now active in desktop nav
      const articlesLink = desktopNav.getByRole('link', { name: '文章列表' });
      await expect(articlesLink).toHaveClass(/bg-blue-100/);
    });

    test('should hide mobile menu button on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto(BASE_URL);

      // Mobile menu button should be hidden (has md:hidden class)
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await expect(mobileMenuButton).toHaveClass(/md:hidden/);

      // Check CSS computed style - button should not be displayed on desktop
      await expect(mobileMenuButton).toHaveCSS('display', 'none');
    });
  });

  test.describe('Mobile Navigation', () => {
    test('should show hamburger menu on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Hamburger button should be visible
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await expect(mobileMenuButton).toBeVisible();

      // Desktop navigation should have display: none on mobile
      const desktopNav = page.locator('nav div.hidden.md\\:flex');
      await expect(desktopNav).toHaveCSS('display', 'none');
    });

    test('should open mobile menu when clicking hamburger', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Click hamburger button
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await mobileMenuButton.click();

      // Wait for menu to be visible
      const drawer = page.locator('div.fixed.top-0.right-0').last();
      await expect(drawer).toBeVisible();

      // Verify menu title
      await expect(page.getByRole('heading', { name: '菜單' })).toBeVisible();

      // Verify navigation items are present in mobile drawer
      await expect(drawer.getByRole('link', { name: '首頁' })).toBeVisible();
      await expect(drawer.getByRole('link', { name: '生成文章' })).toBeVisible();
    });

    test('should close mobile menu when clicking close button', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Open menu
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await mobileMenuButton.click();

      // Wait for menu to open
      const drawer = page.locator('div.fixed.top-0.right-0');
      await expect(drawer).toBeVisible();

      // Click close button
      const closeButton = page.locator('button[aria-label="Close menu"]');
      await closeButton.click();

      // Menu should be hidden (check for transform class)
      await expect(drawer).toHaveClass(/translate-x-full/);
    });

    test('should close mobile menu when clicking backdrop', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Open menu
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await mobileMenuButton.click();

      // Wait for drawer to open
      const drawer = page.locator('div.fixed.top-0.right-0').last();
      await expect(drawer).not.toHaveClass(/translate-x-full/);

      // Wait for backdrop to be visible
      const backdrop = page.locator('div.fixed.inset-0.bg-black');
      await expect(backdrop).toBeVisible();

      // Click backdrop
      await backdrop.click({ force: true });

      // Menu should close
      await expect(drawer).toHaveClass(/translate-x-full/);
    });

    test('should close mobile menu when clicking a navigation link', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Open menu
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await mobileMenuButton.click();

      // Wait for menu to open
      const drawer = page.locator('div.fixed.top-0.right-0').last();
      await expect(drawer).toBeVisible();

      // Click a navigation link in the drawer
      await drawer.getByRole('link', { name: '文章列表' }).click();

      // Menu should close
      await expect(drawer).toHaveClass(/translate-x-full/);

      // URL should change
      await expect(page).toHaveURL(/\/articles/);
    });

    test('should toggle hamburger icon when menu opens/closes', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');

      // Initially should show hamburger icon (M4 6h16M4 12h16M4 18h16)
      await expect(mobileMenuButton.locator('svg path')).toHaveAttribute('d', /M4 6h16/);

      // Open menu
      await mobileMenuButton.click();

      // Should now show X icon (M6 18L18 6M6 6l12 12)
      await expect(mobileMenuButton.locator('svg path')).toHaveAttribute('d', /M6 18L18 6/);
    });

    test('should be scrollable when many menu items', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Open menu
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await mobileMenuButton.click();

      // Check that nav has overflow-y-auto
      const nav = page.locator('nav.p-4.space-y-2');
      await expect(nav).toHaveClass(/overflow-y-auto/);
    });
  });

  test.describe('Responsive Behavior', () => {
    test('should switch from desktop to mobile navigation at 768px breakpoint', async ({ page }) => {
      // Start with desktop size
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.goto(BASE_URL);

      // Desktop nav should be visible
      const desktopNav = page.locator('nav div.hidden.md\\:flex');
      await expect(desktopNav).toBeVisible();

      // Mobile menu button should have display: none
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await expect(mobileMenuButton).toHaveCSS('display', 'none');

      // Resize to mobile
      await page.setViewportSize({ width: 767, height: 768 });

      // Wait a bit for CSS to apply
      await page.waitForTimeout(100);

      // Desktop nav should have display: none
      await expect(desktopNav).toHaveCSS('display', 'none');

      // Mobile menu button should be visible now
      await expect(mobileMenuButton).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('mobile menu should have proper ARIA attributes', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');

      // Initially menu is closed
      await expect(mobileMenuButton).toHaveAttribute('aria-expanded', 'false');

      // Open menu
      await mobileMenuButton.click();

      // Should now be expanded
      await expect(mobileMenuButton).toHaveAttribute('aria-expanded', 'true');
    });

    test('should be keyboard navigable', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Tab to hamburger button
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Open with Enter
      await page.keyboard.press('Enter');

      // Menu should be open
      const drawer = page.locator('div.fixed.top-0.right-0');
      await expect(drawer).toBeVisible();

      // Should be able to navigate to close button
      await page.keyboard.press('Tab');

      // Close with Enter
      await page.keyboard.press('Enter');

      // Menu should close
      await expect(drawer).toHaveClass(/translate-x-full/);
    });
  });
});
