"""High-level LinkedIn scraping session API."""

import os
from typing import Any, Dict, Optional
from playwright.sync_api import Page, BrowserContext

from .auth import CookieAuth, LinkedInAuth, PasswordAuth
from .browser import BrowserContextManager
from .models.person import Person
from .models.company import Company
from .models.job import Job, JobSearch


class LinkedInSession:
    """
    High-level LinkedIn scraping session that manages authentication and browser state.

    This class is the main entry point for using the scraper. It should be
    instantiated using one of the class methods (`from_password`, `from_cookie`,
    or `from_storage_state`) and used as a context manager.
    """

    def __init__(
        self,
        auth: Optional[LinkedInAuth] = None,
        storage_state_path: Optional[str] = None,
        headless: bool = True,
        launch_args: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the LinkedIn session. It's recommended to use the class methods
        for instantiation rather than calling this constructor directly.

        Args:
            auth (Optional[LinkedInAuth]): An authentication instance (e.g., PasswordAuth).
            storage_state_path (Optional[str]): Path to a saved Playwright storage state file.
            headless (bool): Whether to run the browser in headless mode.
        """
        if not auth and not storage_state_path:
            raise ValueError("Either 'auth' or 'storage_state_path' must be provided.")

        self._auth = auth
        self._storage_state_path = storage_state_path
        self._headless = headless
        self._launch_args = launch_args or {}
        self._browser_session: Optional[BrowserContextManager] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._authenticated = False

    @classmethod
    def from_password(
        cls,
        email: str,
        password: str,
        interactive: bool = False,
        headless: bool = True,
        launch_args: Optional[Dict[str, Any]] = None,
    ) -> "LinkedInSession":
        auth = PasswordAuth(email, password, interactive=interactive)
        return cls(auth=auth, headless=headless, launch_args=launch_args)

    @classmethod
    def from_cookie(
        cls,
        cookie: str,
        headless: bool = True,
        launch_args: Optional[Dict[str, Any]] = None,
    ) -> "LinkedInSession":
        auth = CookieAuth(cookie)
        return cls(auth=auth, headless=headless, launch_args=launch_args)

    @classmethod
    def from_storage_state(
        cls,
        storage_state_path: str,
        headless: bool = True,
        launch_args: Optional[Dict[str, Any]] = None,
    ) -> "LinkedInSession":
        return cls(
            storage_state_path=storage_state_path,
            headless=headless,
            launch_args=launch_args,
        )

    def get_profile(self, url: str) -> Person:
        """
        Scrapes a LinkedIn person profile.

        Args:
            url (str): The full URL of the LinkedIn profile to scrape.

        Returns:
            Person: A Pydantic object containing the scraped profile data.

        Raises:
            RuntimeError: If the session is not authenticated.
        """
        from .scrapers.person import PersonScraper

        page: Page = self._ensure_authenticated()
        scraper = PersonScraper(page)
        return scraper.scrape_profile(url)

    def get_company(
        self,
        url: str,
        get_employees: bool = False,
        employee_keyword: Optional[str] = None,
        employees_only: bool = False,
    ) -> Company:
        """
        Scrapes a LinkedIn company profile.

        Args:
            url (str): The URL of the company page to scrape.
            get_employees (bool): If True, scrapes all company employees.
            employee_keyword (Optional[str]): If set, searches for and scrapes employees
                                                matching these keywords. This can be much
                                                faster than getting all employees.
        Returns:
            Company: A Pydantic object with the scraped company data.
        """
        from .scrapers.company import CompanyScraper

        page: Page = self._ensure_authenticated()
        scraper = CompanyScraper(page)
        return scraper.scrape_profile(
            url,
            get_employees=get_employees,
            employee_keyword=employee_keyword,
            employees_only=employees_only,
        )

    def save_storage_state(self, path: str) -> None:
        """
        Saves the current session's storage state (cookies, local storage) to a file.
        This is useful for persisting a login session.

        Args:
            path (str): The file path where the JSON state will be saved.

        Raises:
            RuntimeError: If the session is not authenticated.
        """
        if not self._context:
            raise RuntimeError(
                "Browser context is not available. Ensure the session is active."
            )
        self._ensure_authenticated()
        self._context.storage_state(path=path)

    def get_job(self, job: Job) -> Optional[Job]:
        """
        Enriches a Job object with its full details from the job's page.

        Args:
            job (Job): A partial Job object from a search result.

        Returns:
            Job: The same Job object, now populated with detailed information.
        """
        from .scrapers.job import JobScraper

        page: Page = self._ensure_authenticated()
        scraper = JobScraper(page)
        result_job = scraper.scrape_job_details(job_to_enrich=job)
        if result_job:
            return result_job

    def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = "Worldwide",
        date_posted_filter: Optional[str] = None,
    ) -> JobSearch:
        """
        Performs a job search on LinkedIn for remote jobs and scrapes the results.

        Args:
            keywords (str): The search terms for the job.
            location (str): The location to search in. Defaults to "Worldwide".
            date_posted_filter (Optional[str]): Filter by date. Accepts "day", "week", or "month".

        Returns:
            JobSearch: A Pydantic object containing the search query and a list of found jobs.
        """
        from .scrapers.job import JobScraper

        page: Page = self._ensure_authenticated()
        scraper = JobScraper(page)
        jobs_list = scraper.search(
            keywords=keywords, location=location, date_posted_filter=date_posted_filter
        )

        return JobSearch(
            search_query=keywords,
            location=location,
            jobs=jobs_list,
            total_results=len(jobs_list),
        )

    def is_authenticated(self) -> bool:
        """Check if session is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated and self._page is not None

    def _ensure_authenticated(self) -> Page:
        """Ensure session is authenticated and return page.

        Returns:
            Authenticated page instance

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.is_authenticated():
            raise RuntimeError(
                "Not authenticated. Call login() or login_with_cookie() first."
            )
        if self._page is None:
            raise RuntimeError(
                "No page found. Call login() or login_with_cookie() first."
            )
        return self._page

    def close(self) -> None:
        """Close LinkedIn session and clean up browser resources."""
        self._authenticated = False
        if self._browser_session:
            self._browser_session.close()
            self._browser_session = None
        self._context = None
        self._page = None

    def __enter__(self):
        """Context manager entry - initialize browser and authenticate."""
        try:
            self._browser_session = BrowserContextManager(headless=self._headless)

            context_args = {}
            if self._storage_state_path and os.path.exists(self._storage_state_path):
                context_args["storage_state"] = self._storage_state_path

            self._context = self._browser_session.__enter__(
                launch_args=self._launch_args, context_args=context_args
            )

            if self._auth:
                assert self._auth is not None
                self._page = self._auth.login(context=self._context)
            else:
                self._page = self._context.new_page()

            self._authenticated = True
            return self
        except Exception:
            self.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
