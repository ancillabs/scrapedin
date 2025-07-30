import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List
from dotenv import load_dotenv

from scrapedin import LinkedInSession
from scrapedin.models.job import Job

import time
import random

load_dotenv()

# --- Configuration ---
HEADLESS = False
OUTPUT_DIR = "output"
AUTH_STATE_FILE = "auth_state.json"
JOB_KEYWORDS = "Automation Expert"
JOB_LOCATION = "Worldwide"
JOBS_TO_SCRAPE = 3


def get_and_save_job_details(
    job: Job, storage_state_path: str, launch_args: Dict[str, Any]
):
    """
    Worker function: Scrapes the full details of a single job posting and saves it.
    """
    """
    Worker function: Scrapes the full details of a single job posting and saves it.
    """
    time.sleep(random.uniform(1, 5))

    with LinkedInSession.from_storage_state(
        storage_state_path=storage_state_path,
        headless=False,  # Make sure headless is False for the demo
        launch_args=launch_args,
    ) as session:
        job_details: Job = session.get_job(job=job)

        # # Create a unique filename from the job ID
        # job_id = job_url.split("/jobs/view/")[1].split("/")[0]
        # filename = os.path.join("tests", OUTPUT_DIR, f"job_{job_id}.json")
        # os.makedirs(os.path.dirname(filename), exist_ok=True)

        # with open(filename, "w", encoding="utf-8") as f:
        #     json.dump(
        #         job_details.model_dump(), f, indent=2, default=str, ensure_ascii=False
        #     )

        return json.dumps(
            job_details.model_dump(),
            indent=2,
            default=str,
            ensure_ascii=False,
        )


def perform_initial_login(email: str, password: str, storage_state_path: str) -> None:
    """
    Performs a one-time, interactive login to create and save the session state.

    This function should be run once to generate the `auth_state.json` file. It
    launches a visible browser so the user can manually solve any CAPTCHA or
    two-factor authentication challenges.

    Args:
        email (str): The LinkedIn login email.
        password (str): The LinkedIn login password.
        storage_state_path (str): The path where the session file will be saved.
    """
    print("No existing session found. Performing initial login...")
    with LinkedInSession.from_password(
        email=email,
        password=password,
        headless=HEADLESS,
        interactive=True,
    ) as session:
        print("Login successful! Saving session state...")
        session.save_storage_state(path=storage_state_path)
        print(f"Session state saved to '{storage_state_path}'")


if __name__ == "__main__":
    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")

    if not email or not password:
        raise ValueError(
            "LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables are required."
        )

    if not os.path.exists(AUTH_STATE_FILE):
        perform_initial_login(email, password, AUTH_STATE_FILE)

    # --- Phase 1: Initial Job Search ---
    print(f"Performing job search for '{JOB_KEYWORDS}' in '{JOB_LOCATION}'...")
    jobs_to_scrape: List[Job] = []

    main_search_launch_args = {
        "args": ["--window-position=0,0", "--window-size=800,600"]
    }

    with LinkedInSession.from_storage_state(
        storage_state_path=AUTH_STATE_FILE,
        headless=HEADLESS,
        launch_args=main_search_launch_args,
    ) as session:
        search_result = session.search_jobs(
            keywords=JOB_KEYWORDS, location=JOB_LOCATION, date_posted_filter="week"
        )

        if search_result.jobs:
            jobs_to_scrape = search_result.jobs[:JOBS_TO_SCRAPE]
            print(
                f"Found {len(search_result.jobs)} jobs. Scraping details for the first {len(jobs_to_scrape)}."
            )
        else:
            print("No jobs found for the given search query.")

    # --- Phase 2: Concurrent Scraping of Job Details ---
    if jobs_to_scrape:
        print("\nStarting concurrent scraping of job details...")
        SCREEN_WIDTH = 1920
        WINDOW_WIDTH = 800
        WINDOW_HEIGHT = 600

        COLS = SCREEN_WIDTH // WINDOW_WIDTH

        with ProcessPoolExecutor(max_workers=len(jobs_to_scrape)) as executor:
            futures = {}
            for i, job in enumerate(jobs_to_scrape):
                row = i // COLS
                col = i % COLS

                x_pos = col * WINDOW_WIDTH
                y_pos = row * (WINDOW_HEIGHT + 40)

                launch_args = {
                    "args": [
                        f"--window-position={x_pos},{y_pos}",
                        f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
                    ]
                }

                future = executor.submit(
                    get_and_save_job_details, job, AUTH_STATE_FILE, launch_args
                )
                futures[future] = job.linkedin_url

            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    result = fut.result()
                    print(result)
                except Exception as e:
                    print(f"ERROR processing {url}: {e!r}")
