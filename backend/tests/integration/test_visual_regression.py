"""Visual regression testing for WordPress publishing workflow.

Tests visual consistency of WordPress editor and SEO plugin interfaces.

Research: See specs/001-cms-automation/research.md Section 4.1
"""

import pytest
from playwright.async_api import async_playwright, expect

from src.services.providers.cdp_utils import VisualRegressionTester


pytestmark = pytest.mark.asyncio


class TestWordPressVisualRegression:
    """Visual regression tests for WordPress editor."""

    @pytest.fixture
    async def wordpress_page(self):
        """Create Playwright page with WordPress editor loaded."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={'width': 1920, 'height': 1080}
            )

            # Login to WordPress
            await page.goto('https://test-wordpress.com/wp-login.php')
            await page.fill('#user_login', 'admin')
            await page.fill('#user_pass', 'password')
            await page.click('#wp-submit')
            await page.wait_for_selector('#wpadminbar')

            # Navigate to new post
            await page.goto('https://test-wordpress.com/wp-admin/post-new.php')
            await page.wait_for_selector('.editor-post-title__input')

            yield page

            await browser.close()

    async def test_wordpress_editor_baseline(self, wordpress_page):
        """
        Test: WordPress editor visual baseline

        Verifies:
        - Gutenberg editor loads correctly
        - UI elements are in expected positions
        - No unexpected visual changes

        Purpose: Detect WordPress updates that change UI
        """
        # Wait for editor to fully load
        await wordpress_page.wait_for_selector('.editor-post-title__input')
        await wordpress_page.wait_for_selector('.editor-styles-wrapper')

        # Visual snapshot comparison
        await expect(wordpress_page).to_have_screenshot(
            'wordpress-editor-baseline.png',
            max_diff_pixels=100,  # Allow minor rendering differences
            threshold=0.2,  # 20% color difference tolerance
            full_page=True
        )

    async def test_yoast_seo_panel_baseline(self, wordpress_page):
        """
        Test: Yoast SEO panel visual baseline

        Verifies:
        - Yoast SEO metabox displays correctly
        - All fields are visible
        - No layout changes

        Purpose: Detect Yoast SEO plugin updates
        """
        # Scroll to Yoast SEO metabox
        yoast_metabox = wordpress_page.locator('#yoast-seo-metabox')
        await yoast_metabox.scroll_into_view_if_needed()

        # Wait for metabox to be visible
        await expect(yoast_metabox).to_be_visible()

        # Element-level screenshot comparison
        await expect(yoast_metabox).to_have_screenshot(
            'yoast-seo-panel-baseline.png',
            max_diff_pixels=50
        )

    async def test_rank_math_panel_baseline(self, wordpress_page):
        """
        Test: Rank Math SEO panel visual baseline

        Verifies:
        - Rank Math metabox displays correctly
        - SEO score indicator visible
        - No unexpected UI changes

        Purpose: Detect Rank Math plugin updates
        """
        # Check if Rank Math is installed
        rank_math_panel = wordpress_page.locator('.rank-math-metabox')

        if await rank_math_panel.count() > 0:
            await rank_math_panel.scroll_into_view_if_needed()
            await expect(rank_math_panel).to_be_visible()

            # Screenshot comparison
            await expect(rank_math_panel).to_have_screenshot(
                'rank-math-panel-baseline.png',
                max_diff_pixels=50
            )
        else:
            pytest.skip("Rank Math not installed")

    async def test_publish_panel_visual(self, wordpress_page):
        """
        Test: Publish panel visual consistency

        Verifies:
        - Publish button and settings panel
        - Post visibility options
        - Schedule options

        Purpose: Detect changes to publishing workflow
        """
        # Open publish panel
        publish_panel = wordpress_page.locator('.editor-post-publish-panel')

        # Click settings button to ensure panel is visible
        settings_button = wordpress_page.locator('button[aria-label="Settings"]')
        await settings_button.click()

        # Wait for panel to be visible
        await expect(publish_panel).to_be_visible()

        # Screenshot comparison
        await expect(publish_panel).to_have_screenshot(
            'publish-panel-baseline.png',
            max_diff_pixels=50
        )

    async def test_gutenberg_block_editor_visual(self, wordpress_page):
        """
        Test: Gutenberg block editor visual consistency

        Verifies:
        - Block inserter button
        - Block toolbar
        - Block list view

        Purpose: Detect Gutenberg updates
        """
        # Click into content area to show block toolbar
        await wordpress_page.click('.editor-styles-wrapper')

        # Wait for block toolbar
        block_toolbar = wordpress_page.locator('.block-editor-block-toolbar')
        await expect(block_toolbar).to_be_visible()

        # Screenshot comparison
        await expect(block_toolbar).to_have_screenshot(
            'gutenberg-block-toolbar-baseline.png',
            max_diff_pixels=30
        )


class TestVisualRegressionWithDynamicContent:
    """Visual regression tests with dynamic content masking."""

    @pytest.fixture
    async def wordpress_page_with_post(self):
        """Create page with existing post."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Login and navigate to existing post
            await page.goto('https://test-wordpress.com/wp-login.php')
            await page.fill('#user_login', 'admin')
            await page.fill('#user_pass', 'password')
            await page.click('#wp-submit')

            # Open existing post
            await page.goto('https://test-wordpress.com/wp-admin/post.php?post=1&action=edit')
            await page.wait_for_selector('.editor-post-title__input')

            yield page

            await browser.close()

    async def test_post_with_masked_timestamps(self, wordpress_page_with_post):
        """
        Test: Visual regression with dynamic timestamp masking

        Verifies:
        - Editor layout consistent
        - Timestamps are masked from comparison

        Purpose: Ignore dynamic content like "Published 5 minutes ago"
        """
        # Mask dynamic elements (timestamps, post date, modified date)
        mask_selectors = [
            wordpress_page_with_post.locator('.post-publish-panel__postpublish-header time'),
            wordpress_page_with_post.locator('.edit-post-last-revision__info'),
            wordpress_page_with_post.locator('.components-datetime')
        ]

        # Screenshot with masked elements
        await expect(wordpress_page_with_post).to_have_screenshot(
            'post-editor-masked-timestamps.png',
            mask=mask_selectors,
            max_diff_pixels=100
        )


class TestCDPVisualTester:
    """Test CDP visual regression tester utility."""

    @pytest.fixture
    async def visual_tester(self):
        """Create VisualRegressionTester instance."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            tester = VisualRegressionTester(page)

            # Load test page
            await page.goto('https://test-wordpress.com/wp-admin/post-new.php')

            yield tester

            await browser.close()

    async def test_visual_tester_screenshot_comparison(self, visual_tester):
        """
        Test: VisualRegressionTester screenshot comparison

        Verifies:
        - Screenshot baseline creation
        - Pixel difference detection
        - Pass/fail reporting

        Purpose: Validate visual testing utility
        """
        # Take baseline screenshot
        result = await visual_tester.verify_screenshot(
            'test-baseline',
            max_diff_pixels=50
        )

        assert result.passed
        assert result.diff_pixels == 0

    async def test_visual_tester_element_screenshot(self, visual_tester):
        """
        Test: VisualRegressionTester element screenshot

        Verifies:
        - Element-specific screenshots
        - Selective comparison

        Purpose: Test focused visual regression
        """
        # Take element screenshot
        result = await visual_tester.verify_element_screenshot(
            '.editor-post-title__input',
            'title-input-baseline',
            max_diff_pixels=20
        )

        assert result.passed

    async def test_visual_tester_element_visibility(self, visual_tester):
        """
        Test: Element visibility verification

        Verifies:
        - Element visibility check
        - Assertion on expected elements

        Purpose: Ensure critical elements are visible
        """
        # Verify title input is visible
        await visual_tester.verify_element_visible(
            visual_tester.page.locator('.editor-post-title__input'),
            'Title input should be visible in editor'
        )


# =============================================================================
# Performance Testing with Visual Verification
# =============================================================================

class TestPerformanceWithVisuals:
    """Performance tests with visual verification."""

    async def test_editor_load_performance_with_screenshot(self):
        """
        Test: Editor load performance with visual verification

        Verifies:
        - Editor loads within performance budget
        - Visual snapshot confirms successful load

        Purpose: Performance + visual regression combined
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            # Create CDP session for performance monitoring
            cdp = await context.new_cdp_session(page)
            await cdp.send('Performance.enable')

            # Navigate to editor
            await page.goto('https://test-wordpress.com/wp-admin/post-new.php')
            await page.wait_for_selector('.editor-post-title__input')

            # Get performance metrics
            metrics_response = await cdp.send('Performance.getMetrics')
            metrics = metrics_response['metrics']

            # Extract FCP (First Contentful Paint)
            fcp = next(
                (m['value'] for m in metrics if m['name'] == 'FirstContentfulPaint'),
                0
            )

            # Assert performance budget
            assert fcp < 3.0, f"Editor FCP {fcp}s exceeded 3s budget"

            # Visual verification that editor loaded correctly
            await expect(page).to_have_screenshot(
                'editor-performance-load.png',
                max_diff_pixels=100
            )

            await browser.close()


# =============================================================================
# Update Baseline Screenshots (Run manually when UI changes intentionally)
# =============================================================================

@pytest.mark.skip(reason="Manual update only")
class TestUpdateBaselines:
    """Manual tests to update baseline screenshots."""

    async def test_update_all_baselines(self):
        """
        Update all baseline screenshots.

        Run this test manually when WordPress updates require new baselines:
        pytest tests/integration/test_visual_regression.py::TestUpdateBaselines -v --update-snapshots
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Login
            await page.goto('https://test-wordpress.com/wp-login.php')
            await page.fill('#user_login', 'admin')
            await page.fill('#user_pass', 'password')
            await page.click('#wp-submit')

            # New post
            await page.goto('https://test-wordpress.com/wp-admin/post-new.php')
            await page.wait_for_selector('.editor-post-title__input')

            # Update baselines
            await expect(page).to_have_screenshot('wordpress-editor-baseline.png')
            await expect(page.locator('#yoast-seo-metabox')).to_have_screenshot('yoast-seo-panel-baseline.png')

            await browser.close()
