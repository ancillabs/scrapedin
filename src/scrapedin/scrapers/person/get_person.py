"""Main person profile scraper using Playwright."""

import random
from playwright.sync_api import Page
from pydantic import HttpUrl

from ...models.person import Person
from .education import scrape_educations
from .experience import scrape_experiences
from .. import selectors


class PersonScraper:
    """Scraper for LinkedIn person profiles."""

    def __init__(self, page: Page):
        """Initialize the scraper with a Playwright page.

        Args:
            page: Authenticated Playwright page instance
        """
        self.page = page

    def scrape_profile(self, url: str) -> Person:
        """Scrape a LinkedIn person profile.

        Args:
            url: LinkedIn profile URL as string

        Returns:
            Person model with scraped data
        """
        # Validate URL
        linkedin_url = HttpUrl(url)

        # Navigate to profile
        self.page.goto(str(linkedin_url))

        # Wait for initial content to load
        self.page.wait_for_timeout(2000)  # 2 seconds

        # Initialize Person model
        # Create lists to hold scraped data
        experiences_data = []
        educations_data = []
        self.page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        # Scrape basic information into a dictionary
        basic_info = self._scrape_basic_info()
        self.page.wait_for_timeout(1000)  # 1 second between sections

        # Scrape experiences into the list
        scrape_experiences(self.page, str(linkedin_url), experiences_data)
        self.page.wait_for_timeout(1000)  # 1 second between sections

        # Scrape educations into the list
        scrape_educations(self.page, str(linkedin_url), educations_data)
        self.page.wait_for_timeout(1000)  # 1 second between sections

        # At the end, create the Person object with all the collected data
        person = Person(
            linkedin_url=linkedin_url,
            experiences=experiences_data,
            educations=educations_data,
            **basic_info,
        )

        return person

    def _scrape_basic_info(self) -> dict:
        """Scrape basic profile information (name, location, about)."""
        info = {
            "name": None,
            "headline": None,
            "location": None,
            "about": None,
            "open_to_work": False,
        }

        # Get name and location
        try:
            top_panel = self.page.locator(selectors.TOP_CARD_CONTAINER).first
            name_element = top_panel.locator(selectors.TOP_CARD_NAME).first
            if name_element.is_visible():
                info["name"] = name_element.inner_text()
        except Exception:
            pass

        try:
            location_element = self.page.locator(selectors.TOP_CARD_LOCATION).first
            if location_element.is_visible():
                info["location"] = location_element.inner_text()
        except Exception:
            pass

        # Get headline - simplified approach based on DOM structure
        try:
            # From MCP DOM analysis, the headline appears right after the name
            # Try multiple selectors that should work universally
            headline_selectors = selectors.TOP_CARD_HEADLINE_SELECTORS

            for selector in headline_selectors:
                headline_element = self.page.locator(selector).first
                if headline_element.is_visible():
                    headline_text = headline_element.inner_text().strip()
                    # Make sure it's not the name and has substantial content
                    if (
                        headline_text
                        and headline_text != info["name"]
                        and len(headline_text) > 5
                        and headline_text not in ["", "null", "undefined"]
                    ):
                        info["headline"] = headline_text
                        break
        except Exception:
            pass

        # Get about section - following Selenium approach exactly
        try:
            about = (
                self.page.locator("#about").locator("..").locator(".display-flex").first
            )
            if about.is_visible():
                [info["about"]].append(about.inner_text())
        except Exception:
            pass

        # Check if open to work
        try:
            profile_picture = self.page.locator(selectors.OPEN_TO_WORK_IMAGE).first
            if profile_picture.is_visible():
                title_attr = profile_picture.get_attribute("title")
                info["open_to_work"] = title_attr and "#OPEN_TO_WORK" in title_attr
        except Exception:
            pass
        return info
