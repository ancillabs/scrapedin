"""Simple browser management for LinkedIn scraping."""

from typing import Any, Dict, Optional
from playwright.sync_api import BrowserContext, sync_playwright

from ..config import BrowserConfig


class BrowserContextManager:
    """Context manager for browser contexts with automatic cleanup."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright_context = None

    def __enter__(
        self,
        launch_args: Optional[Dict[str, Any]] = None,
        context_args: Optional[Dict[str, Any]] = None,
    ) -> BrowserContext:
        """Create and return browser context with standard configuration."""
        self.playwright_context = sync_playwright()
        playwright = self.playwright_context.__enter__()

        # Safely handle optional arguments
        final_launch_args = (launch_args or {}).copy()
        final_context_args = (context_args or {}).copy()

        # Pop the 'args' list to combine it with the defaults
        custom_cli_args = final_launch_args.pop("args", [])
        all_cli_args = BrowserConfig.CHROME_ARGS + custom_cli_args

        browser = playwright.chromium.launch(
            headless=self.headless,
            args=all_cli_args,
            channel="chrome",
            **final_launch_args,
        )

        context = browser.new_context(
            user_agent=BrowserConfig.USER_AGENT,
            viewport=None,
            **final_context_args,
        )
        context.set_default_timeout(BrowserConfig.TIMEOUT)

        return context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure browser and playwright are properly closed."""
        if self.playwright_context:
            self.playwright_context.__exit__(exc_type, exc_val, exc_tb)
