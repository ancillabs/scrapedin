"""Employee scraping module for LinkedIn company pages."""

import time
from typing import List, Optional, Set
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from pydantic import HttpUrl
import urllib.parse

from ...models.company import Employee
from .. import selectors


def scrape_employees(page: Page, keyword: Optional[str] = None) -> List[Employee]:
    """
    Scrapes employee information from a company's 'People' page and returns a list.
    If keyword are provided, it performs a search before scraping.

    Args:
        page (Page): An authenticated Playwright page instance.
        keyword (Optional[str]): Optional search query for employees.

    Returns:
        List[Employee]: A list of scraped Employee objects.
    """
    scraped_employees: List[Employee] = []
    # Use a set for O(1) average time complexity checks for duplicates.
    scraped_employee_urls: Set[str] = set()

    # LinkedIn keyword filter for employees takes a commma-seperated list, but seems to only care about the first keyword.
    if keyword:
        try:
            search_input = page.locator(selectors.COMPANY_EMPLOYEE_SEARCH_INPUT)
            search_input.wait_for(state="visible", timeout=7000)
            search_input.fill(keyword)
            search_input.press("Enter")

            # Wait for the URL to reflect the search query to confirm search has executed
            encoded_keyword = urllib.parse.quote(keyword)

            page.wait_for_url(f"**/*keywords={encoded_keyword}*", timeout=10000)

        except PlaywrightTimeoutError:
            print(f"Could not perform search for keyword: {keyword}")
            return scraped_employees  # Return empty list if search fails

    try:
        page.wait_for_selector(
            selectors.COMPANY_EMPLOYEE_LIST_CONTAINER, state="visible", timeout=15000
        )
    except PlaywrightTimeoutError:
        print("Could not find the employee list container.")
        return scraped_employees

    while True:
        # Keep track of the employee count before scraping the current view
        
        last_count = len(scraped_employees)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # A brief, simple pause works best after scrolling

        employee_data_list = page.evaluate(f"""
            Array.from(document.querySelectorAll('{selectors.COMPANY_EMPLOYEE_CARD}')).map(card => {{
                const linkElement = card.querySelector('{selectors.COMPANY_EMPLOYEE_LINK_AND_NAME}');
                const positionElement = card.querySelector('{selectors.COMPANY_EMPLOYEE_POSITION}');
                if (!linkElement) return null;
                const url = linkElement.getAttribute('href').split('?')[0];
                const name = linkElement.innerText.trim();
                const position = positionElement ? positionElement.innerText.trim() : null;
                return {{ name, position, url }};
            }}).filter(item => item !== null);
        """)

        for data in employee_data_list:
            if (
                data["url"] not in scraped_employee_urls
                and "LinkedIn Member" not in data["name"]
            ):
                try:
                    employee = Employee(
                        name=data["name"],
                        position=data["position"],
                        profile_url=HttpUrl(data["url"]),
                    )
                    scraped_employees.append(employee)
                    scraped_employee_urls.add(data["url"])
                except Exception:
                    continue

        # If no new employees were added after scraping, we are done.
        if len(scraped_employees) == last_count:
            break

        # Now, try to click the button to load more.
        try:
            show_more_button = page.locator(selectors.COMPANY_EMPLOYEE_SHOW_MORE_BUTTON)
            if show_more_button.is_visible(timeout=1000):
                show_more_button.click()
                time.sleep(1.5)
            else:
                break
        except Exception:
            break

    return scraped_employees
