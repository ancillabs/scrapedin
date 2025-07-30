#!/usr/bin/env python3

import json
import os

from dotenv import load_dotenv

from scrapedin import LinkedInSession
from scrapedin.models import Person
from concurrent.futures import ProcessPoolExecutor, as_completed

load_dotenv()

load_dotenv()

# --- Configuration ---
HEADLESS = False
USERNAMES = ["alexischevalier1", "andrewyng", "sadjy"]
OUTPUT_DIR = "output"
AUTH_STATE_FILE = "auth_state.json"


def get_and_save_person_profile(username: str, storage_state_path: str) -> str:
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
    profile_url = f"https://www.linkedin.com/in/{username}/"

    with LinkedInSession.from_storage_state(
        storage_state_path=storage_state_path, headless=True
    ) as session:
        person: Person = session.get_profile(profile_url)

        tests_output_dir = os.path.join("tests", OUTPUT_DIR)
        os.makedirs(tests_output_dir, exist_ok=True)
        filename = os.path.join(tests_output_dir, f"{username}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(person.model_dump(), f, indent=2, default=str, ensure_ascii=False)

        return f"Profile saved to: {filename}"


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

    print("\nStarting concurrent scraping using saved session...")
    with ProcessPoolExecutor(max_workers=min(10, len(USERNAMES))) as executor:
        futures = {
            executor.submit(
                get_and_save_person_profile, username, AUTH_STATE_FILE
            ): username
            for username in USERNAMES
        }

        for fut in as_completed(futures):
            username = futures[fut]
            try:
                result = fut.result()
                print(result)
            except Exception as e:
                print(f"ERROR processing {username}: {e!r}")
