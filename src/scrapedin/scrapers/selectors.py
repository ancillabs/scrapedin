"""
Central repository for CSS selectors used in LinkedIn scraping.
"""

# Selectors for Person Profile Scraping
PERSON_MAIN_LIST_CONTAINER = "main .pvs-list__container"
PERSON_LIST_ITEM = ".pvs-list__paged-list-item"
PERSON_ENTITY_CONTAINER = "div[data-view-name='profile-component-entity']"

# Selectors for Basic Info (Top Card)
TOP_CARD_CONTAINER = ".mt2.relative"
TOP_CARD_NAME = "h1"
TOP_CARD_LOCATION = ".text-body-small.inline.t-black--light.break-words"
TOP_CARD_HEADLINE_SELECTORS = [
    # Direct approach: find h1 then get the next generic element
    "h1 + div",
    "h1 ~ div:first-of-type",
    # Alternative: look in the main profile section
    ".mt2.relative div:has(h1) + div",
    # Fallback: find elements that typically contain headlines
    ".pv-text-details__left-panel > div:nth-child(2)",
    ".pv-top-card-v2-section-info > div:nth-child(2)",
]

# Selectors for About Section
ABOUT_SECTION = "#about"
ABOUT_SECTION_TEXT = ".."  # Using relative selector from #about

# Selectors for Open To Work
OPEN_TO_WORK_IMAGE = ".pv-top-card-profile-picture img"

COMPANY_NAME = ".org-top-card-summary__title"
COMPANY_TAGLINE = ".org-top-card-summary__tagline"
COMPANY_ABOUT_OVERVIEW = (
    "section.org-page-details-module__card-spacing > p.white-space-pre-wrap"
)

# Selectors for Company Employee Scraping
COMPANY_EMPLOYEE_LIST_CONTAINER = "div.scaffold-finite-scroll__content"
COMPANY_EMPLOYEE_CARD = "li.org-people-profile-card__profile-card-spacing"
COMPANY_EMPLOYEE_LINK_AND_NAME = "div.artdeco-entity-lockup__title a"
COMPANY_EMPLOYEE_POSITION = "div.artdeco-entity-lockup__subtitle"
COMPANY_EMPLOYEE_SHOW_MORE_BUTTON = "button.scaffold-finite-scroll__load-button"
COMPANY_EMPLOYEE_SEARCH_INPUT = "#people-search-keywords"

# Selectors for Job Search Scraping.
JOB_SEARCH_LIST_CONTAINER = "div.scaffold-layout__list"
JOB_SEARCH_LIST = "div.scaffold-layout__list ul"
JOB_SEARCH_ITEM = "li.scaffold-layout__list-item"  # Each job card

JOB_SEARCH_KEYWORDS_INPUT = "input[id^='jobs-search-box-keyword-id-']"
JOB_SEARCH_LOCATION_INPUT = "input[id^='jobs-search-box-location-id-']"
JOB_SEARCH_LOCATION_SUGGESTION_LIST = "div.jobs-search-box__typeahead-results--location ul.jobs-search-box__typeahead-results-list"

# Selectors for Job Search Page Filters
JOB_SEARCH_ONSITE_REMOTE_FILTER_BUTTON = "button[aria-label='Remote filter. Clicking this button displays all Remote filter options.']"
JOB_SEARCH_REMOTE_FILTER_CHECKBOX = "label[for='workplaceType-2']"
JOB_SEARCH_APPLY_FILTER_BUTTON = "div[data-basic-filter-parameter-name='workplaceType'] button.artdeco-button--primary"
JOB_SEARCH_REMOTE_APPLIED = "button[id='searchFilter_workplaceType'] > span"

JOB_SEARCH_DATE_POSTED_FILTER_BUTTON = "button[id='searchFilter_timePostedRange']"
# JOB_SEARCH_DATE_POSTED_FILTER_BUTTON = "button[aria-label='Date posted filter. Clicking this button displays all Date posted filter options.']"
JOB_SEARCH_PAST_MONTH_FILTER_CHECKBOX = "label[for='timePostedRange-r2592000']"
JOB_SEARCH_PAST_WEEK_FILTER_CHECKBOX = "label[for='timePostedRange-r604800']"
JOB_SEARCH_PAST_DAY_FILTER_CHECKBOX = "label[for='timePostedRange-r86400']"
JOB_SEARCH_DATE_APPLY_FILTER_BUTTON = "div[data-basic-filter-parameter-name='timePostedRange'] button.artdeco-button--primary"


JOB_SEARCH_ITEM_LINK = "a.job-card-container__link"
JOB_SEARCH_ITEM_TITLE = "div.artdeco-entity-lockup__title a span > strong"
JOB_SEARCH_ITEM_COMPANY = "div.artdeco-entity-lockup__subtitle"
JOB_SEARCH_ITEM_LOCATION = "div.artdeco-entity-lockup__caption"
JOB_SEARCH_ITEM_POSTED_DATE = "li.job-card-container__footer-item time"
JOB_SEARCH_PAGINATION_NEXT = "button[aria-label='View next page']"

JOB_DETAILS_TITLE = "h1.t-24"
JOB_DETAILS_COMPANY_LINK = "div.job-details-jobs-unified-top-card__company-name a"
JOB_DETAILS_METADATA_CONTAINER = (
    "div.job-details-jobs-unified-top-card__primary-description-container"
)
JOB_DETAILS_DESCRIPTION = "div#job-details"
JOB_DETAILS_SHOW_MORE_BUTTON = "button.jobs-description__footer-button"
