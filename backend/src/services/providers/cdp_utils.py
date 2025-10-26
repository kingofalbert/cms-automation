"""Chrome DevTools Protocol (CDP) utility modules.

Provides utilities for:
- Performance monitoring
- Network optimization
- Visual regression testing
- DOM inspection

Research: See specs/001-cms-automation/research.md Section 4.1
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.async_api import CDPSession, Page, expect

from src.config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Performance Monitoring
# =============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics from CDP."""
    first_contentful_paint: float  # FCP in seconds
    dom_content_loaded: float  # DCL in seconds
    layout_duration: float  # Layout time in milliseconds
    script_duration: float  # Script execution time in milliseconds
    task_duration: float  # Total task duration in milliseconds
    js_heap_used_size: float  # JS heap size in MB
    js_heap_total_size: float  # Total heap size in MB
    network_request_count: int  # Number of network requests


class CDPPerformanceMonitor:
    """Monitor page performance using CDP Performance domain."""

    def __init__(self, cdp_session: CDPSession):
        """Initialize performance monitor.

        Args:
            cdp_session: Active CDP session from Playwright
        """
        self.cdp = cdp_session
        self.metrics_log: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []

    async def start(self) -> None:
        """Enable performance monitoring domains."""
        # Enable Performance domain
        await self.cdp.send('Performance.enable')

        # Enable Network domain for request tracking
        await self.cdp.send('Network.enable')

        # Set up network request listener
        self.cdp.on('Network.requestWillBeSent', self._on_request)
        self.cdp.on('Network.responseReceived', self._on_response)

        logger.info("cdp_performance_monitor_started")

    async def stop(self) -> None:
        """Disable performance monitoring domains."""
        await self.cdp.send('Performance.disable')
        await self.cdp.send('Network.disable')

        logger.info(
            "cdp_performance_monitor_stopped",
            total_requests=len(self.network_requests)
        )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics.

        Returns:
            Dict with performance metrics:
            - first_contentful_paint: float
            - dom_content_loaded: float
            - layout_duration: float
            - script_duration: float
            - network_request_count: int
            - js_heap_used_mb: float
        """
        # Get performance metrics
        response = await self.cdp.send('Performance.getMetrics')
        metrics = response['metrics']

        # Extract specific metrics
        performance_data = {
            'first_contentful_paint': self._get_metric_value(metrics, 'FirstContentfulPaint'),
            'dom_content_loaded': self._get_metric_value(metrics, 'DomContentLoaded'),
            'layout_duration': self._get_metric_value(metrics, 'LayoutDuration'),
            'script_duration': self._get_metric_value(metrics, 'ScriptDuration'),
            'task_duration': self._get_metric_value(metrics, 'TaskDuration'),
            'js_heap_used_size': self._get_metric_value(metrics, 'JSHeapUsedSize') / (1024 * 1024),  # Convert to MB
            'js_heap_total_size': self._get_metric_value(metrics, 'JSHeapTotalSize') / (1024 * 1024),
            'network_request_count': len(self.network_requests)
        }

        logger.info(
            "cdp_performance_metrics_collected",
            fcp=performance_data['first_contentful_paint'],
            dcl=performance_data['dom_content_loaded'],
            requests=performance_data['network_request_count']
        )

        return performance_data

    def _get_metric_value(self, metrics: List[Dict], name: str) -> float:
        """Extract metric value by name."""
        for metric in metrics:
            if metric['name'] == name:
                return metric['value']
        return 0.0

    def _on_request(self, params: Dict[str, Any]) -> None:
        """Handle network request event."""
        self.network_requests.append({
            'url': params['request']['url'],
            'method': params['request']['method'],
            'timestamp': params['timestamp']
        })

    def _on_response(self, params: Dict[str, Any]) -> None:
        """Handle network response event."""
        # Track response timing
        response = params.get('response', {})
        logger.debug(
            "network_response",
            url=response.get('url'),
            status=response.get('status'),
            mime_type=response.get('mimeType')
        )


# =============================================================================
# Network Optimization
# =============================================================================

@dataclass
class NetworkStats:
    """Network statistics."""
    total_requests: int
    blocked_requests: int
    total_bytes_downloaded: int
    requests_by_type: Dict[str, int]


class CDPNetworkOptimizer:
    """Optimize network requests using CDP Network domain."""

    def __init__(self, cdp_session: CDPSession):
        """Initialize network optimizer.

        Args:
            cdp_session: Active CDP session
        """
        self.cdp = cdp_session
        self.blocked_patterns = [
            '*google-analytics.com*',
            '*facebook.com/tr*',
            '*doubleclick.net*',
            '*googlesyndication.com*',
            '*google-adsense*'
        ]
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'total_bytes': 0,
            'requests_by_type': {}
        }

    async def start(self) -> None:
        """Enable network optimization."""
        # Enable Network domain
        await self.cdp.send('Network.enable')

        # Enable request interception
        await self.cdp.send('Network.setRequestInterception', {
            'patterns': [{'urlPattern': '*', 'interceptionStage': 'HeadersReceived'}]
        })

        # Set up interception handler
        self.cdp.on('Network.requestIntercepted', self._on_request_intercepted)

        logger.info(
            "cdp_network_optimizer_started",
            blocked_patterns=self.blocked_patterns
        )

    async def stop(self) -> None:
        """Disable network optimization."""
        await self.cdp.send('Network.disable')

        logger.info(
            "cdp_network_optimizer_stopped",
            total_requests=self.stats['total_requests'],
            blocked_requests=self.stats['blocked_requests']
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Get network optimization statistics."""
        return {
            'total_requests': self.stats['total_requests'],
            'blocked_requests': self.stats['blocked_requests'],
            'block_rate': (
                self.stats['blocked_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'requests_by_type': self.stats['requests_by_type']
        }

    async def _on_request_intercepted(self, params: Dict[str, Any]) -> None:
        """Handle intercepted request."""
        interception_id = params['interceptionId']
        request = params.get('request', {})
        url = request.get('url', '')

        self.stats['total_requests'] += 1

        # Check if request should be blocked
        should_block = any(
            self._match_pattern(url, pattern)
            for pattern in self.blocked_patterns
        )

        if should_block:
            # Block request
            await self.cdp.send('Network.continueInterceptedRequest', {
                'interceptionId': interception_id,
                'errorReason': 'Aborted'
            })

            self.stats['blocked_requests'] += 1

            logger.debug(
                "network_request_blocked",
                url=url,
                reason="matched_blocked_pattern"
            )
        else:
            # Allow request
            await self.cdp.send('Network.continueInterceptedRequest', {
                'interceptionId': interception_id
            })

    def _match_pattern(self, url: str, pattern: str) -> bool:
        """Simple wildcard pattern matching."""
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(regex_pattern, url))


# =============================================================================
# Visual Regression Testing
# =============================================================================

@dataclass
class VisualDiff:
    """Visual difference report."""
    baseline_path: str
    current_path: str
    diff_path: Optional[str]
    diff_pixels: int
    diff_percentage: float
    passed: bool


class VisualRegressionTester:
    """Visual regression testing using Playwright's built-in capabilities."""

    def __init__(self, page: Page):
        """Initialize visual tester.

        Args:
            page: Playwright Page object
        """
        self.page = page
        self.baseline_dir = "screenshots/baselines"
        self.current_dir = "screenshots/current"
        self.diff_dir = "screenshots/diffs"

    async def verify_screenshot(
        self,
        name: str,
        max_diff_pixels: int = 100,
        threshold: float = 0.2
    ) -> VisualDiff:
        """Verify screenshot against baseline.

        Args:
            name: Screenshot name (without extension)
            max_diff_pixels: Maximum allowed pixel differences
            threshold: Color difference threshold (0-1)

        Returns:
            VisualDiff report
        """
        try:
            # Take screenshot and compare
            await expect(self.page).to_have_screenshot(
                f"{name}.png",
                max_diff_pixels=max_diff_pixels,
                threshold=threshold
            )

            logger.info(
                "visual_regression_passed",
                name=name,
                max_diff_pixels=max_diff_pixels
            )

            return VisualDiff(
                baseline_path=f"{self.baseline_dir}/{name}.png",
                current_path=f"{self.current_dir}/{name}.png",
                diff_path=None,
                diff_pixels=0,
                diff_percentage=0.0,
                passed=True
            )

        except AssertionError as e:
            # Visual regression detected
            logger.warning(
                "visual_regression_detected",
                name=name,
                error=str(e)
            )

            return VisualDiff(
                baseline_path=f"{self.baseline_dir}/{name}.png",
                current_path=f"{self.current_dir}/{name}.png",
                diff_path=f"{self.diff_dir}/{name}-diff.png",
                diff_pixels=max_diff_pixels + 1,  # Exceeded threshold
                diff_percentage=0.0,  # Would need Pixelmatch for exact %
                passed=False
            )

    async def verify_element_screenshot(
        self,
        selector: str,
        name: str,
        max_diff_pixels: int = 50
    ) -> VisualDiff:
        """Verify element screenshot against baseline.

        Args:
            selector: CSS selector for element
            name: Screenshot name
            max_diff_pixels: Maximum allowed pixel differences

        Returns:
            VisualDiff report
        """
        element = self.page.locator(selector)

        try:
            await expect(element).to_have_screenshot(
                f"{name}.png",
                max_diff_pixels=max_diff_pixels
            )

            logger.info(
                "element_visual_regression_passed",
                selector=selector,
                name=name
            )

            return VisualDiff(
                baseline_path=f"{self.baseline_dir}/{name}.png",
                current_path=f"{self.current_dir}/{name}.png",
                diff_path=None,
                diff_pixels=0,
                diff_percentage=0.0,
                passed=True
            )

        except AssertionError as e:
            logger.warning(
                "element_visual_regression_detected",
                selector=selector,
                name=name,
                error=str(e)
            )

            return VisualDiff(
                baseline_path=f"{self.baseline_dir}/{name}.png",
                current_path=f"{self.current_dir}/{name}.png",
                diff_path=f"{self.diff_dir}/{name}-diff.png",
                diff_pixels=max_diff_pixels + 1,
                diff_percentage=0.0,
                passed=False
            )

    async def verify_element_visible(
        self,
        locator,
        description: str
    ) -> None:
        """Verify element is visible.

        Args:
            locator: Playwright Locator
            description: Test description for logging

        Raises:
            AssertionError: If element is not visible
        """
        await expect(locator).to_be_visible()

        logger.info(
            "element_visibility_verified",
            description=description
        )


# =============================================================================
# DOM Inspection Utilities
# =============================================================================

class CDPDOMInspector:
    """Inspect DOM using CDP DOM domain."""

    def __init__(self, cdp_session: CDPSession):
        """Initialize DOM inspector.

        Args:
            cdp_session: Active CDP session
        """
        self.cdp = cdp_session

    async def get_element_box_model(self, selector: str) -> Dict[str, Any]:
        """Get element bounding box via CDP.

        Args:
            selector: CSS selector

        Returns:
            Box model data with content, padding, border, margin
        """
        # Get document root
        doc = await self.cdp.send('DOM.getDocument')
        root_node_id = doc['root']['nodeId']

        # Query selector
        result = await self.cdp.send('DOM.querySelector', {
            'nodeId': root_node_id,
            'selector': selector
        })

        node_id = result['nodeId']

        # Get box model
        box_model = await self.cdp.send('DOM.getBoxModel', {
            'nodeId': node_id
        })

        return {
            'content': box_model['model']['content'],
            'padding': box_model['model']['padding'],
            'border': box_model['model']['border'],
            'margin': box_model['model']['margin'],
            'width': box_model['model']['width'],
            'height': box_model['model']['height']
        }

    async def is_element_visible(self, selector: str) -> bool:
        """Check if element is visible.

        Args:
            selector: CSS selector

        Returns:
            True if element is visible, False otherwise
        """
        try:
            box_model = await self.get_element_box_model(selector)
            return box_model['height'] > 0 and box_model['width'] > 0
        except Exception as e:
            logger.debug(
                "element_visibility_check_failed",
                selector=selector,
                error=str(e)
            )
            return False

    async def get_element_attributes(self, selector: str) -> Dict[str, str]:
        """Get element attributes via CDP.

        Args:
            selector: CSS selector

        Returns:
            Dict of attribute name -> value
        """
        # Get document root
        doc = await self.cdp.send('DOM.getDocument')
        root_node_id = doc['root']['nodeId']

        # Query selector
        result = await self.cdp.send('DOM.querySelector', {
            'nodeId': root_node_id,
            'selector': selector
        })

        node_id = result['nodeId']

        # Get attributes
        attrs_result = await self.cdp.send('DOM.getAttributes', {
            'nodeId': node_id
        })

        # Convert flat array to dict
        attributes = {}
        attrs = attrs_result['attributes']
        for i in range(0, len(attrs), 2):
            if i + 1 < len(attrs):
                attributes[attrs[i]] = attrs[i + 1]

        return attributes
