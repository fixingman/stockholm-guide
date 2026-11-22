#!/usr/bin/env python3
"""No-email acceptance test of the LIVE GitHub Pages Stockholm Guide calendar.

Runs in GitHub Actions with Chromium. Checks public HTTP, JS and CSS loading,
real FullCalendar interactions, issue data, organizer links, filters and phone UI.
No private subscriber or Gmail data is accessed.
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://fixingman.github.io/stockholm-guide/calendar.html"
EXPECTED = json.loads(Path("issues/current.json").read_text(encoding="utf-8"))
REPORT = Path("live-calendar-test-report.json")


def assert_that(ok, message):
    if not ok:
        raise AssertionError(message)


def run():
    checks = []
    failures = []
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1180, "height": 880}, device_scale_factor=1)
            page.on("pageerror", lambda error: errors.append(str(error)))
            data = None
            for attempt in range(7):
                response = page.goto(URL, wait_until="domcontentloaded", timeout=45000)
                if response and response.status == 200:
                    try:
                        data = json.loads(page.locator("#calendar-data").text_content(timeout=15000))
                    except Exception:
                        data = None
                    if data and data.get("issue_number") == EXPECTED["issue_number"]:
                        break
                time.sleep(6)
            assert_that(response is not None and response.status == 200, "Public calendar URL did not return HTTP 200")
            assert_that(data is not None, "Missing embedded public calendar JSON")
            assert_that(data["issue_number"] == EXPECTED["issue_number"],
                        f"Stale public edition {data['issue_number']!r}, expected {EXPECTED['issue_number']!r}")
            checks.append("Live URL HTTP 200; current issue number matches repository")
            assert_that(data["event_count"] == len(data["events"]), "Event count differs from visible source data")
            assert_that(len(data["events"]) >= 15, "Calendar unexpectedly sparse")
            expected_picks = {x["title"] for x in EXPECTED["top3"]}
            actual_picks = {x["title"] for x in data["events"] if x["section"] == "top3"}
            assert_that(expected_picks == actual_picks, "Current Top 3 differ from issue data")
            assert_that(all(e["url"].startswith("https://") and "@" not in e["url"].split("/")[2]
                            for e in data["events"]), "Unsafe public event link")
            assert_that(all(e["section"] != "unavailable" for e in data["events"]),
                        "An unavailable event is presented as bookable")
            checks.append(f"Editorial data: {len(data['events'])} experiences, 3 exact current Top Picks, HTTPS organizers")
            page.locator(".fc-daygrid").wait_for(timeout=30000)
            assert_that(page.locator(".fc-daygrid-event").count() >= 1, "No real events in FullCalendar month grid")
            assert_that(not errors, f"Browser JavaScript error(s): {errors[:3]}")
            checks.append("FullCalendar JavaScript loaded and populated real month grid")

            assert_that(page.locator('link[href="./calendar.css"]').count() == 1, "Missing calendar CSS")
            assert_that(page.locator('script[src="./calendar.js"]').count() == 1, "Missing local adapter")
            style = page.evaluate("getComputedStyle(document.querySelector('.calendar-shell')).borderTopStyle")
            assert_that(style != "none", "Website stylesheet not applied")
            checks.append("Live calendar CSS and JS loaded")

            page.get_by_role("button", name="All events", exact=True).click()
            page.locator(".fc-list").wait_for(timeout=12000)
            assert_that(page.locator(".fc-list-event").count() >= 3, "Agenda list is empty")
            checks.append("Maintained FullCalendar agenda/list view functions")

            page.get_by_role("button", name="Top picks", exact=True).click()
            page.wait_for_timeout(150)
            initial_month = guide_month = data["window_start"][:7]
            picks_visible = [e for e in data["events"] if e["section"] == "top3"
                             and e["date"] and e["date"].startswith(initial_month)]
            if not picks_visible:
                page.locator(".fc-next-button").click()
                candidates = [e for e in data["events"] if e["section"] == "top3"
                              and e["date"] and e["date"][:7] != guide_month]
                initial_month = candidates[0]["date"][:7] if candidates else guide_month
                picks_visible = [e for e in candidates if e["date"].startswith(initial_month)]
            assert_that(bool(picks_visible), "No dated Top Picks found in current or adjacent month")
            assert_that(page.locator(".fc-list-event").count() == len(picks_visible),
                        "Top Picks filter does not match dated featured events")
            checks.append("Top Picks filter matches actual featured event dates")

            page.locator("#search").fill(picks_visible[0]["title"])
            page.wait_for_timeout(150)
            assert_that(page.locator(".fc-list-event").count() == 1,
                        "Search did not isolate an exact featured event")
            page.locator("#search").fill("")
            page.get_by_role("button", name="All", exact=True).click()
            page.get_by_role("button", name="Calendar", exact=True).click()
            page.locator(".fc-daygrid").wait_for(timeout=12000)
            checks.append("Live search, filter reset, month/list switching")

            date_buckets = {}
            for event in data["events"]:
                if event["date"] and event["date"][:7] == initial_month:
                    date_buckets.setdefault(event["date"], []).append(event)
            assert_that(bool(date_buckets), "No source events found in issue's first month")
            target_date, corresponding = max(date_buckets.items(), key=lambda x: len(x[1]))
            page.locator(f'.fc-daygrid-day[data-date="{target_date}"]').click()
            assert_that(page.locator("#day-heading").inner_text(),
                        "Date drill-down heading not present")
            assert_that(page.locator("#day-events .event-card").count() == len(corresponding),
                        "Selected date did not show all corresponding event details")
            assert_that(page.locator("#day-events .event-card a[href^='https://']").count() == len(corresponding),
                        "Date drill-down missing official event links")
            checks.append("Clicking day opens event cards with official organizer links")

            page.screenshot(path="live-calendar-desktop.png", full_page=True)
            mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
            mobile.on("pageerror", lambda error: errors.append(str(error)))
            r = mobile.goto(URL, wait_until="domcontentloaded", timeout=45000)
            assert_that(r and r.status == 200, "Mobile page did not load")
            mobile.locator(".fc-daygrid").wait_for(timeout=30000)
            mobile.wait_for_timeout(500)
            days = mobile.locator(".fc-col-header-cell")
            assert_that(days.count() == 7, f"Mobile calendar has {days.count()} day columns, not 7")
            left, right = days.first.bounding_box(), days.last.bounding_box()
            assert_that(left and right and left["x"] >= -2 and right["x"] + right["width"] <= 393,
                        "Weekday columns clipped at mobile width")
            assert_that(mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3"),
                        "Horizontal overflow on 390px phone viewport")
            assert_that(mobile.locator(".fc-daygrid-event").count() >= 1,
                        "Mobile month grid hides all event indicators")
            assert_that(not errors, f"Unexpected JS errors: {errors[:4]}")
            mobile.screenshot(path="live-calendar-mobile.png", full_page=True)
            checks.append("390px mobile: seven weekdays, event markers, no horizontal overflow, no JS exceptions")

            # Confirm flexible exhibitions are distinguishable from dated sessions.
            flexible = [e for e in data["events"] if e["kind"] == "flexible"]
            nondated = [e for e in data["events"] if e["kind"] != "event"]
            assert_that(all(e["date"] is None for e in flexible), "Flexible date incorrectly has a session pin")
            assert_that(mobile.locator("#flexible-events .event-card").count() == len(nondated),
                        "Flexible and last-chance experiences not displayed")
            checks.append("Flexible exhibitions separated from dated sessions")
        except Exception as exc:
            failures.append(str(exc))
        finally:
            browser.close()
    outcome = {"site": URL, "expected_issue": EXPECTED["issue_number"],
               "passed": not failures, "checks": checks, "failures": failures,
               "javascript_errors": errors}
    REPORT.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(run())
