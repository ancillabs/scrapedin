#!/usr/bin/env python3

import json
import os

from dotenv import load_dotenv

from scrapedin import LinkedInSession
from scrapedin.models import Company

load_dotenv()

# --- Configuration ---
HEADLESS = False
OUTPUT_DIR = "output"
AUTH_STATE_FILE = "auth_state.json"
COMPANIES = ["unicast-ai", "llamaindex"]


def get_and_save_company_profile(name: str, storage_state_path: str) -> str:
    """
    Worker function designed to run in a separate process.

    It initializes a LinkedInSession from a saved storage state file, scrapes the
    specified profile, and saves the resulting data to a JSON file.

    Args:
        username (str): The LinkedIn profile username to scrape.
        storage_state_path (str): The path to the authentication state file.

    Returns:
        str: A message indicating where the profile was saved.
    """
    company_url = f"https://www.linkedin.com/company/{name}/"

    with LinkedInSession.from_storage_state(
        storage_state_path=storage_state_path, headless=HEADLESS
    ) as session:
        # company: Company = session.get_company(company_url, get_employees=False)
        company: Company = session.get_company(
            company_url, get_employees=True, employee_keyword="CEO"
        )

        return json.dumps(
            company.model_dump(),
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
        headless=HEADLESS,  # Must be visible for potential challenges
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

    print(get_and_save_company_profile(COMPANIES[0], AUTH_STATE_FILE))
