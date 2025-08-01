"""LinkedIn Scraper Playwright - Playwright-based LinkedIn scraping library."""

from .session import LinkedInSession
from .auth import PasswordAuth, CookieAuth
from .browser import BrowserContextManager

__version__ = "2.11.5"

__all__ = [
    "LinkedInSession",
    "PasswordAuth",
    "CookieAuth",
    "BrowserContextManager",
]
