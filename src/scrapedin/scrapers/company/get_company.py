"""Main company profile scraper using Playwright."""

import re
from typing import Dict, Optional, Any
from playwright.sync_api import Page
from pydantic import HttpUrl

from ...models.company import Company
from .. import selectors
from .get_employees import scrape_employees


def _parse_company_size(size_text: str) -> Optional[int]:
    """Extracts the lower bound of the employee count from a string."""
    if not size_text:
        return None
    # Find all numbers in the string
    numbers = re.findall(r"\d+", size_text.replace(",", ""))
    if numbers:
        # Return the first number found as an integer
        return int(numbers[0])
    return None


class CompanyScraper:
    """Scraper for LinkedIn company profiles."""

    def __init__(self, page: Page):
        """
        Initialize the scraper with a Playwright page.

        Args:
            page (Page): An authenticated Playwright page instance.
        """
        self.page = page

    def scrape_profile(
        self,
        url: str,
        get_employees: bool = False,
        employee_keyword: Optional[str] = None,
    ) -> Company:
        """
        Scrapes a LinkedIn company profile.

        Args:
            url (str): The URL of the company page.
            get_employees (bool): If True, scrapes all employees.
            employee_keyword (Optional[str]): If provided, scrapes employees matching these keywords.
                                                Setting this implies get_employees=True.
        """
        linkedin_url = HttpUrl(url)
        self.page.goto(str(linkedin_url))
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

        # Find the base company URL to reliably build the about and people URLs.
        base_url_match = re.search(
            r"(https?://www\.linkedin\.com/company/[^/]+)", str(linkedin_url)
        )
        if not base_url_match:
            # If the regex fails for some reason, fall back to a simpler method
            base_url = str(linkedin_url).split("?")[0].rstrip("/")
        else:
            base_url = base_url_match.group(1)

        company_data = self._scrape_basic_info()

        # Navigate to the about page for more details
        about_url = f"{base_url}/about/"
        self.page.goto(about_url)
        self.page.wait_for_timeout(2000)

        about_data = self._scrape_about_info()

        # Scrape employees if requested
        employees_data = []
        if get_employees or employee_keyword:
            people_url = f"{base_url}/people/"
            self.page.goto(people_url)
            employees_data = scrape_employees(self.page, keyword=employee_keyword)

        # Combine and create the final Company object
        full_data = {**company_data, **about_data, "employees": employees_data}
        company = Company(linkedin_url=linkedin_url, **full_data)

        return company

    def _get_text(
        self, locator_str: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """Safely get inner text from a locator."""
        try:
            locator = self.page.locator(locator_str).first
            if locator.is_visible():
                return locator.inner_text()
        except Exception:
            pass
        return default

    def _get_attribute(
        self, locator_str: str, attr: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Safely get an attribute from a locator."""
        try:
            locator = self.page.locator(locator_str).first
            if locator.is_visible():
                return locator.get_attribute(attr)
        except Exception:
            pass
        return default

    def _scrape_basic_info(self) -> Dict[str, Optional[str]]:
        """Scrapes the main information from the company's homepage."""
        info: Dict[str, Optional[str]] = {"name": None, "about_us": None}
        info["name"] = self._get_text(selectors.COMPANY_NAME)
        return info

    def _scrape_about_info(self) -> Dict[str, Any]:
        """Scrapes the detailed information from the company's 'About' page."""
        info: Dict[str, Any] = {
            "about_us": None,
            "website": None,
            "industry": None,
            "company_size": None,
            "headquarters": None,
            "founded": None,
            "specialties": [],
        }

        # The overview text is different from the main page tagline
        info["about_us"] = self._get_text(selectors.COMPANY_ABOUT_OVERVIEW)

        # Locate details by finding the label (dt) and getting the adjacent value (dd)
        info["website"] = self._get_attribute("dt:has-text('Website') + dd a", "href")
        info["industry"] = self._get_text("dt:has-text('Industry') + dd")
        info["company_size"] = self._get_text("dt:has-text('Company size') + dd")
        info["headquarters"] = self._get_text("dt:has-text('Headquarters') + dd")

        # Founded year is not in the provided DOM, so we handle its absence
        founded_text = self._get_text("dt:has-text('Founded') + dd")
        if founded_text and founded_text.isdigit():
            info["founded"] = int(founded_text)

        specialties_text = self._get_text("dt:has-text('Specialties') + dd")
        if specialties_text:
            info["specialties"] = [s.strip() for s in specialties_text.split(",")]

        company_size_text = self._get_text("dt:has-text('Company size') + dd")
        if company_size_text:
            info["company_size"] = _parse_company_size(company_size_text)
            info["company_size_text"] = company_size_text
        return info
