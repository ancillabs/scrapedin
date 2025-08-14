"""Job scraping module for LinkedIn."""

import random
import re
import time
from typing import List, Optional, Set
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from pydantic import HttpUrl

from ...models.job import Job
from .. import selectors
from ..utils import robust_navigate, scroll_to_bottom


class JobScraper:
    """
    Scraper for LinkedIn jobs, handling both search and individual job pages.
    """

    def __init__(self, page: Page):
        """
        Initialize the scraper with a Playwright page.

        Args:
            page (Page): An authenticated Playwright page instance.
        """
        self.page = page

    def search(
        self,
        keywords: str,
        location: Optional[str],
        date_posted_filter: Optional[str] = None,
    ) -> List[Job]:
        """
        Scrapes job listings from LinkedIn, with filters for remote and date posted.

        Args:
            keywords (str): The search terms for the job.
            location (str): The location to search in.
            date_posted_filter (Optional[str]): Can be 'day', 'week', or 'month'.
        """
        scraped_jobs: List[Job] = []
        scraped_job_ids: Set[str] = set()

        # Navigate to the main jobs page first for a more human-like approach
        self.page.goto("https://www.linkedin.com/jobs/")
        self.page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        try:
            # --- Step 1: Perform the initial search ---
            keywords_input = self.page.locator(
                selectors.JOB_SEARCH_KEYWORDS_INPUT
            ).first
            keywords_input.wait_for(state="visible", timeout=5000)
            keywords_input.fill(keywords)

            location_input = self.page.locator(
                selectors.JOB_SEARCH_LOCATION_INPUT
            ).first
            location_input.wait_for(state="visible", timeout=5000)
            location_input.clear()
            if location:
                location_input.fill(location)

            self.page.wait_for_selector(
                selectors.JOB_SEARCH_LOCATION_SUGGESTION_LIST,
                state="visible",
                timeout=5000,
            )
            location_input.press("Enter")

            # Wait for the initial search results to load
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)

            # --- Step 2: Apply the "Remote" filter on the results page ---
            remote_filter_button = self.page.locator(
                selectors.JOB_SEARCH_ONSITE_REMOTE_FILTER_BUTTON
            ).first
            remote_filter_button.wait_for(state="visible", timeout=5000)
            remote_filter_button.click()

            remote_checkbox = self.page.locator(
                selectors.JOB_SEARCH_REMOTE_FILTER_CHECKBOX
            ).first
            remote_checkbox.wait_for(state="visible", timeout=3000)
            remote_checkbox.click()

            apply_button = self.page.locator(
                selectors.JOB_SEARCH_APPLY_FILTER_BUTTON
            ).first
            apply_button.wait_for(state="visible", timeout=3000)

            apply_button.click(timeout=2000)
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            time.sleep(1.5)  # I'm tired boss // TODO: fix race condition

            # with self.page.expect_response(
            #     "**/voyagerJobsDashJobCards**", timeout=15000
            # ):
            #     apply_button.click()
            if date_posted_filter:
                date_filter_button = self.page.locator(
                    selectors.JOB_SEARCH_DATE_POSTED_FILTER_BUTTON
                ).first
                date_filter_button.wait_for(state="visible", timeout=3000)
                expect(date_filter_button).to_be_enabled(timeout=10000)

                date_filter_button.click(timeout=2000)

                date_checkbox_selector = ""
                if date_posted_filter == "month":
                    date_checkbox_selector = (
                        selectors.JOB_SEARCH_PAST_MONTH_FILTER_CHECKBOX
                    )
                elif date_posted_filter == "week":
                    date_checkbox_selector = (
                        selectors.JOB_SEARCH_PAST_WEEK_FILTER_CHECKBOX
                    )
                elif date_posted_filter == "day":
                    date_checkbox_selector = (
                        selectors.JOB_SEARCH_PAST_DAY_FILTER_CHECKBOX
                    )

                if date_checkbox_selector:
                    date_checkbox = self.page.locator(date_checkbox_selector).first
                    date_checkbox.wait_for(state="visible", timeout=3000)
                    date_checkbox.click(timeout=2000)

                    date_apply_button = self.page.locator(
                        selectors.JOB_SEARCH_DATE_APPLY_FILTER_BUTTON
                    ).first
                    date_apply_button.wait_for(state="visible", timeout=3000)
                    date_apply_button.click(timeout=2000)

                    self.page.wait_for_load_state("domcontentloaded", timeout=10000)

        except Exception as e:
            print(f"Failed during the search and filtering process: {e}")
            return scraped_jobs

        try:
            self.page.wait_for_selector(
                selectors.JOB_SEARCH_LIST, state="visible", timeout=10000
            )
        except PlaywrightTimeoutError:
            print("Could not find job search results list after applying filters.")
            return scraped_jobs

        while True:
            time.sleep(random.uniform(1.0, 7.0))
            scroll_to_bottom(self.page)
            self.page.wait_for_timeout(1000)  # Short wait for lazy-loading

            # High-performance data extraction
            job_data_list = self.page.evaluate(f"""
                Array.from(document.querySelectorAll('{selectors.JOB_SEARCH_ITEM}')).map(item => {{
                    const linkElement = item.querySelector('{selectors.JOB_SEARCH_ITEM_LINK}');
                    const titleElement = item.querySelector('{selectors.JOB_SEARCH_ITEM_TITLE}');
                    const companyElement = item.querySelector('{selectors.JOB_SEARCH_ITEM_COMPANY}');
                    const locationElement = item.querySelector('{selectors.JOB_SEARCH_ITEM_LOCATION}');
                    const dateElement = item.querySelector('{selectors.JOB_SEARCH_ITEM_POSTED_DATE}');
                    
                    if (!linkElement || !titleElement) return null;

                    const url = linkElement.getAttribute('href');
                    const title = titleElement.innerText.trim();
                    const company = companyElement ? companyElement.innerText.trim() : null;
                    const location = locationElement ? locationElement.innerText.trim() : null;
                    const posted_date = dateElement ? dateElement.innerText.trim() : null;
                    
                    return {{ url, title, company, location, posted_date }};
                }}).filter(item => item !== null);
            """)

            for data in job_data_list:
                try:
                    job_id_match = re.search(r"/jobs/view/(\d+)/", data["url"])
                    job_id = job_id_match.group(1) if job_id_match else None

                    if not job_id or job_id in scraped_job_ids:
                        continue

                    job = Job(
                        job_id=job_id,
                        linkedin_url=HttpUrl(
                            f"https://www.linkedin.com{data['url'].split('?')[0]}"
                        ),
                        title=data["title"],
                        company=data["company"],
                        location=data["location"],
                        posted_date=data["posted_date"],
                        num_applicants=None,  # Explicitly set to None
                    )
                    scraped_jobs.append(job)
                    scraped_job_ids.add(job_id)
                except Exception:
                    continue

            try:
                next_button = self.page.locator(selectors.JOB_SEARCH_PAGINATION_NEXT)
                if next_button.is_visible(timeout=1000) and next_button.is_enabled(
                    timeout=1000
                ):
                    next_button.click()
                    self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                else:
                    break
            except Exception:
                break

        return scraped_jobs

    def scrape_job_details(self, job_to_enrich: Job) -> Optional[Job]:
        """
        Enriches a Job object with its full details from the job's page.
        """
        robust_navigate(
            self.page, str(job_to_enrich.linkedin_url), selectors.JOB_DETAILS_TITLE
        )

        try:
            show_more_button = self.page.locator(
                selectors.JOB_DETAILS_SHOW_MORE_BUTTON
            ).first
            if show_more_button.is_visible(timeout=2000):
                show_more_button.click()
        except Exception:
            pass

        # Scrape core details
        title = (
            self.page.locator(selectors.JOB_DETAILS_TITLE).first.inner_text().strip()
        )

        company_link_loc = self.page.locator(selectors.JOB_DETAILS_COMPANY_LINK).first
        company_name = company_link_loc.inner_text().strip()
        company_url = company_link_loc.get_attribute("href")

        description_loc = self.page.locator(selectors.JOB_DETAILS_DESCRIPTION).first
        description = (
            description_loc.inner_text() if description_loc.is_visible() else ""
        )

        # Extract location and applicant count from the metadata container
        location = None
        num_applicants = None
        if not job_to_enrich.posted_date:
            try:
                metadata_text = self.page.locator(
                    selectors.JOB_DETAILS_METADATA_CONTAINER
                ).first.inner_text()
                # The date is usually the second item, after the location.
                parts = [part.strip() for part in metadata_text.split("·")]
                if len(parts) > 1:
                    # A simple check to see if it looks like a date string
                    if "ago" in parts[1].lower() or "day" in parts[1].lower():
                        job_to_enrich.posted_date = parts[1]
            except Exception:
                pass

        job_to_enrich.title = title
        job_to_enrich.company = company_name
        job_to_enrich.company_url = HttpUrl(company_url) if company_url else None
        job_to_enrich.location = location
        job_to_enrich.description = description
        job_to_enrich.num_applicants = num_applicants

        return job_to_enrich
