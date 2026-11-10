
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import sys

URL = "https://webgrity.net/pms2/work-log-hour.php"
PROFILE_DIR = str(Path(__file__).resolve().parent / "webgrity_profile")

WORK_LOGS = [
    {
        "from": "09:45",
        "to": "13:30",
        "activity": "Worked",
        "manager": "Uttam Kumar Majumder",
        "project": "ACTS Website",
        "job_type": "Coding - Php",
        "details": "acts",
    },
    {
        "from": "13:30",
        "to": "14:05",
        "activity": "Lunch",
    },
    {
        "from": "14:05",
        "to": "17:45",
        "activity": "Worked",
        "manager": "Uttam Kumar Majumder",
        "project": "ACTS Website",
        "job_type": "Coding - Php",
        "details": "acts",
    },
    {
        "from": "17:45",
        "to": "18:15",
        "activity": "Recess",
    },
    {
        "from": "18:15",
        "to": "19:15",
        "activity": "Worked",
        "manager": "Uttam Kumar Majumder",
        "project": "ACTS Website",
        "job_type": "Coding - Php",
        "details": "acts",
    },
]


def navigate_to_work_log(page):
    print("Opening Work Log...", flush=True)

    page.goto(URL, wait_until="domcontentloaded", timeout=30000)

    if "work-log-hour.php" not in page.url:
        print("Trying Work Log sidebar...", flush=True)

        link = page.get_by_text("Work Log", exact=True)
        link.click(timeout=10000)

    page.wait_for_url(
        "**/work-log-hour.php",
        timeout=15000
    )

    page.get_by_text("WORK HOUR LOG").first.wait_for(
        state="visible",
        timeout=15000
    )

    print("Work Log page ready.", flush=True)


def get_selects(page):
    """
    The visible form in the screenshots contains:
    From hour, From minute,
    To hour, To minute,
    Activity, Manager, Project, Job Type.
    """
    return page.locator("select:visible")


def choose_option(select, desired):
    desired = str(desired).strip()

    options = select.locator("option").evaluate_all(
        """elements => elements.map(e => ({
            value: e.value,
            text: e.textContent.trim()
        }))"""
    )

    for option in options:
        if option["text"].casefold() == desired.casefold():
            select.select_option(value=option["value"])
            return

    # Match numeric values such as 9 and 09
    if desired.isdigit():
        for option in options:
            if option["text"].isdigit():
                if int(option["text"]) == int(desired):
                    select.select_option(value=option["value"])
                    return

    raise ValueError(
        f"Option '{desired}' not found. Available: {options}"
    )


def select_time(page, field, value):
    hour, minute = value.split(":")

    selects = get_selects(page)

    if field == "from":
        choose_option(selects.nth(0), hour)
        choose_option(selects.nth(1), minute)
    else:
        choose_option(selects.nth(2), hour)
        choose_option(selects.nth(3), minute)


def fill_work_log(page, log):
    print("Setting start time...", flush=True)
    select_time(page, "from", log["from"])

    print("Setting end time...", flush=True)
    select_time(page, "to", log["to"])

    print("Setting activity...", flush=True)
    choose_option(get_selects(page).nth(4), log["activity"])

    if log["activity"] == "Worked":
        print("Setting work details...", flush=True)

        selects = get_selects(page)

        choose_option(selects.nth(5), log["manager"])
        choose_option(selects.nth(6), log["project"])
        choose_option(selects.nth(7), log["job_type"])

        page.locator("textarea:visible").last.fill(
            log["details"]
        )

    print("Form completed.", flush=True)


def matching_saved_rows(page, log):
    """
    Find saved rows matching the start/end time
    and activity. Assumes table columns match
    the screenshots.
    """
    start = log["from"]
    end = log["to"]

    def to_12h(value):
        from datetime import datetime
        return datetime.strptime(
            value, "%H:%M"
        ).strftime("%I:%M %p")

    start_text = to_12h(start)
    end_text = to_12h(end)

    rows = page.locator("table tbody tr")
    matches = 0

    for i in range(rows.count()):
        cells = rows.nth(i).locator("td")

        if cells.count() < 3:
            continue

        actual_start = cells.nth(0).inner_text().strip()
        actual_end = cells.nth(1).inner_text().strip()
        actual_activity = cells.nth(2).inner_text().strip()

        if (
            actual_start == start_text
            and actual_end == end_text
            and actual_activity.casefold()
            == log["activity"].casefold()
        ):
            matches += 1

    return matches


def submit_log(page, log, index):
    print(
        f"\nProcessing log {index}/{len(WORK_LOGS)}",
        flush=True
    )

    if matching_saved_rows(page, log) > 0:
        print("Record already exists. Skipping.")
        return

    fill_work_log(page, log)

    print("Form completed.", flush=True)

    click_add_button(page)

    try:
        page.wait_for_function(
            """({start, end, activity}) => {
                const rows = [...document.querySelectorAll(
                    'table tbody tr'
                )];

                return rows.some(row => {
                    const cells = row.querySelectorAll('td');

                    if (cells.length < 3) return false;

                    return (
                        cells[0].textContent.trim() === start &&
                        cells[1].textContent.trim() === end &&
                        cells[2].textContent.trim().toLowerCase()
                            === activity.toLowerCase()
                    );
                });
            }""",
            arg={
                "start": format_12h(log["from"]),
                "end": format_12h(log["to"]),
                "activity": log["activity"],
            },
            timeout=15000,
        )

    except PlaywrightTimeoutError:
        raise RuntimeError(
            "Submission could not be verified. "
            "Stopped to avoid duplicate records."
        )

    print(
        f"Log {index} saved successfully.",
        flush=True
    )

def click_add_button(page):
    print("Looking for ADD button...", flush=True)

    selectors = [
        'input[type="submit"][value="ADD"]',
        'input[type="button"][value="ADD"]',
        'button:has-text("ADD")',
        'a:has-text("ADD")',
        '[role="button"]:has-text("ADD")',
        'input[value="Add"]',
    ]

    for selector in selectors:
        locator = page.locator(selector)

        for i in range(locator.count()):
            button = locator.nth(i)

            if button.is_visible() and button.is_enabled():
                print(
                    f"ADD button found: {selector}",
                    flush=True
                )

                button.scroll_into_view_if_needed()
                button.click(timeout=15000)

                print("ADD clicked.", flush=True)
                return

    raise RuntimeError(
        "ADD button not found. "
        "Inspect the button HTML using F12."
    )

def format_12h(value):
    from datetime import datetime
    return datetime.strptime(
        value, "%H:%M"
    ).strftime("%I:%M %p")


def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            viewport={"width": 1400, "height": 900},
        )

        page = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )

        page.set_default_timeout(10000)

        try:
            navigate_to_work_log(page)

            for index, log in enumerate(WORK_LOGS, 1):
                submit_log(page, log, index)

            print(
                "\nAll work logs submitted successfully!",
                flush=True
            )

        except Exception as error:
            print(f"\nAutomation stopped: {error}", flush=True)

            page.screenshot(
                path="automation_error.png",
                full_page=True
            )

            sys.exit(1)

        finally:
            context.close()


if __name__ == "__main__":
    main()
