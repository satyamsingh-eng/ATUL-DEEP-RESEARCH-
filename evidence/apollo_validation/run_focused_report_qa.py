#!/usr/bin/env python
"""Artifact-bound release QA for the board-ready Atul intelligence report.

Runs directly against the local file URL in Chromium, Firefox, and WebKit when
available. It checks geometry, source-card mapping, functional interactions,
keyboard dialog behavior, print mode, accessibility basics, and offline direct
file behavior. No external network is required or allowed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Atul_Bansal_C3A_Network_Intelligence_Report.html"
OUT = Path(__file__).resolve().parent / "Atul_Bansal_Report_Focused_QA.json"
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 1024, "height": 768},
    "mobile": {"width": 390, "height": 844},
}
EXPECTED_SOURCE_COUNT = 19


def audit_state(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const visible = el => {
            const s = getComputedStyle(el); const r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0' && r.width > 0 && r.height > 0;
          };
          const buttons = [...document.querySelectorAll('button')].filter(visible).map(button => {
            const r = button.getBoundingClientRect();
            return {id: button.id, text: button.textContent.trim(), width: Math.round(r.width), height: Math.round(r.height), aria: button.getAttribute('aria-label')};
          });
          const summaries = [...document.querySelectorAll('.source-card summary')].map(summary => {
            const r = summary.getBoundingClientRect();
            return {text: summary.textContent.trim(), width: Math.round(r.width), height: Math.round(r.height)};
          });
          const headings = [...document.querySelectorAll('h1,h2,h3')]
            .filter(heading => !heading.closest('dialog:not([open])'))
            .map(heading => {
            const r = heading.getBoundingClientRect(); const s = getComputedStyle(heading);
            return {text: heading.textContent.trim(), visible: visible(heading), width: Math.round(r.width), height: Math.round(r.height), color: s.color};
          });
          const sourceCards = [...document.querySelectorAll('.source-card')];
          const citations = [...document.querySelectorAll('.citation[data-source-ref]')];
          const tables = [...document.querySelectorAll('table')].map((table, index) => {
            const columns = table.querySelectorAll('thead th').length;
            const style = getComputedStyle(table);
            return {
              index, columns, className: table.className, scrollWidth: table.scrollWidth,
              clientWidth: table.clientWidth, overflowX: style.overflowX,
              mobileCardsRequired: innerWidth <= 720 && columns >= 3,
              mobileCardsPresent: table.classList.contains('mobile-card-table'),
              contained: table.scrollWidth <= table.clientWidth || table.closest('.table-shell') !== null,
            };
          });
          const duplicateIds = [...document.querySelectorAll('[id]')].map(el => el.id).filter((id, index, ids) => ids.indexOf(id) !== index);
          const sourceIds = sourceCards.map(card => card.id);
          const missingCitationTargets = [...new Set(citations.map(link => link.dataset.sourceRef).filter(number => !document.getElementById('source-' + number)))];
          const emptyButtons = buttons.filter(button => !button.text && !button.aria);
          const malformedSources = sourceCards.filter(card => !card.querySelector('summary') || !card.querySelector('.source-body')).map(card => card.id);
          return {
            viewport: {width: innerWidth, height: innerHeight},
            documentWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
            externalResources: [...document.querySelectorAll('script[src], img[src], link[rel="stylesheet"][href]')]
              .map(element => element.getAttribute('src') || element.getAttribute('href'))
              .filter(value => /^https?:/i.test(value)).length,
            headingProblems: headings.filter(heading => !heading.visible || !heading.text || !heading.width || !heading.height),
            sourceCards: sourceCards.length,
            sourceIds,
            malformedSources,
            citations: citations.length,
            missingCitationTargets,
            tables,
            duplicateIds,
            emptyButtons,
            buttons,
            summaries,
            hasDialog: !!document.getElementById('evidence-dialog'),
            dialogSemantics: {
              role: document.getElementById('evidence-dialog')?.getAttribute('role'),
              modal: document.getElementById('evidence-dialog')?.getAttribute('aria-modal'),
            },
            hasProgress: !!document.getElementById('scroll-progress'),
            progressSemantics: {
              role: document.getElementById('scroll-progress')?.getAttribute('role'),
              minimum: document.getElementById('scroll-progress')?.getAttribute('aria-valuemin'),
              maximum: document.getElementById('scroll-progress')?.getAttribute('aria-valuemax'),
              current: document.getElementById('scroll-progress')?.getAttribute('aria-valuenow'),
            },
            hasSkipLink: !!document.querySelector('.skip-link[href="#brief-content"]'),
            noGradient: !document.documentElement.outerHTML.includes('linear-gradient') && !document.documentElement.outerHTML.includes('radial-gradient'),
            noBoxShadow: !document.documentElement.outerHTML.includes('box-shadow')
          };
        }"""
    )


def exercise_interactions(page: Page) -> dict[str, Any]:
    # Focus mode is intentionally unavailable on phone widths to conserve header space.
    focus = page.locator("#focus-toggle")
    focus_result: dict[str, Any] = {"available": focus.count() == 1 and focus.is_visible()}
    if focus_result["available"]:
        focus.focus()
        focus_result["focus_outline"] = page.evaluate("getComputedStyle(document.getElementById('focus-toggle')).outlineStyle")
        focus.click()
        focus_result["enabled"] = page.evaluate("document.body.classList.contains('focus-mode')")
        focus_result["aria_when_enabled"] = focus.get_attribute("aria-pressed")
        focus.click()
        focus_result["restored"] = not page.evaluate("document.body.classList.contains('focus-mode')")

    page.locator("#open-evidence").click()
    page.wait_for_timeout(550)
    evidence_scroll = page.evaluate("window.scrollY")

    source_toggle = page.locator("#sources-toggle")
    source_toggle.click()
    open_count = page.locator(".source-card[open]").count()
    source_toggle_state = source_toggle.get_attribute("aria-expanded")
    source_toggle.click()
    closed_count = page.locator(".source-card[open]").count()

    citation = page.locator(".citation[data-source-ref]").first
    citation.click()
    page.wait_for_timeout(90)
    dialog = page.locator("#evidence-dialog")
    dialog_open = dialog.evaluate("node => node.open")
    dialog_title = page.locator("#dialog-title").inner_text()
    page.keyboard.press("Tab")
    tab_trapped = page.evaluate("document.getElementById('evidence-dialog').contains(document.activeElement)")
    page.keyboard.press("Shift+Tab")
    shift_tab_trapped = page.evaluate("document.getElementById('evidence-dialog').contains(document.activeElement)")
    page.keyboard.press("Escape")
    page.wait_for_timeout(90)
    dialog_closed = not dialog.evaluate("node => node.open")
    focus_restored = page.evaluate("document.activeElement?.classList.contains('citation')")

    citation.click()
    page.locator("#dialog-open-ledger").click()
    page.wait_for_timeout(220)
    source_two_open = page.locator("#source-2").evaluate("node => node.open")
    dialog_ledger_closed = not dialog.evaluate("node => node.open")

    nav = page.locator(".side-rail nav a[data-nav-target]").nth(1)
    nav_target = nav.get_attribute("data-nav-target")
    nav.click()
    page.wait_for_timeout(1150)
    nav_hash = page.evaluate("location.hash")
    nav_current = nav.get_attribute("aria-current")

    return {
        "focus": focus_result,
        "evidence_scroll_y": evidence_scroll,
        "source_toggle": {"open_count": open_count, "aria_expanded": source_toggle_state, "closed_count": closed_count},
        "dialog": {
            "opened": dialog_open,
            "title": dialog_title,
            "tab_trapped": tab_trapped,
            "shift_tab_trapped": shift_tab_trapped,
            "closed_by_escape": dialog_closed,
            "focus_restored": focus_restored,
            "ledger_action_closed": dialog_ledger_closed,
            "source_two_open": source_two_open,
        },
        "nav": {"target": nav_target, "hash": nav_hash, "aria_current": nav_current},
    }


def audit_print(browser: Browser) -> dict[str, Any]:
    page = browser.new_page(viewport=VIEWPORTS["desktop"])
    try:
        page.goto(REPORT.resolve().as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        return page.evaluate(
            """() => ({
              bodyBackground: getComputedStyle(document.body).backgroundColor,
              navDisplay: getComputedStyle(document.querySelector('.topbar')).display,
              railDisplay: getComputedStyle(document.querySelector('.side-rail')).display,
              tableHeaderColor: getComputedStyle(document.querySelector('thead th')).color,
              sourceBodyDisplay: getComputedStyle(document.querySelector('.source-card .source-body')).display,
            })"""
        )
    finally:
        page.close()


def audit_offline(browser: Browser) -> dict[str, Any]:
    context = browser.new_context(viewport=VIEWPORTS["desktop"])
    blocked: list[str] = []
    try:
        context.route("http://**/*", lambda route: (blocked.append(route.request.url), route.abort()))
        context.route("https://**/*", lambda route: (blocked.append(route.request.url), route.abort()))
        page = context.new_page()
        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(REPORT.resolve().as_uri(), wait_until="networkidle")
        page.locator(".citation[data-source-ref]").first.click()
        dialog_open = page.locator("#evidence-dialog").evaluate("node => node.open")
        return {"blocked_requests": blocked, "console_errors": console_errors, "page_errors": page_errors, "dialog_open": dialog_open}
    finally:
        context.close()


def check_result(label: str, state: dict[str, Any], interactions: dict[str, Any], print_state: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if state["pageOverflow"]:
        failures.append(f"{label}: horizontal page overflow")
    if state["sourceCards"] != EXPECTED_SOURCE_COUNT:
        failures.append(f"{label}: expected {EXPECTED_SOURCE_COUNT} source cards, found {state['sourceCards']}")
    if state["malformedSources"] or state["missingCitationTargets"]:
        failures.append(f"{label}: source/citation mapping issue")
    if state["headingProblems"] or state["duplicateIds"] or state["emptyButtons"]:
        failures.append(f"{label}: semantic structure issue")
    if not state["hasDialog"] or not state["hasProgress"] or not state["hasSkipLink"]:
        failures.append(f"{label}: expected executive interaction missing")
    if state["dialogSemantics"] != {"role": "dialog", "modal": "true"}:
        failures.append(f"{label}: evidence dialog semantics missing")
    if state["progressSemantics"].get("role") != "progressbar" or state["progressSemantics"].get("minimum") != "0" or state["progressSemantics"].get("maximum") != "100":
        failures.append(f"{label}: reading progress semantics missing")
    if state["externalResources"]:
        failures.append(f"{label}: external runtime resource detected")
    if not state["noGradient"] or not state["noBoxShadow"]:
        failures.append(f"{label}: non-flat styling detected")
    for table in state["tables"]:
        if not table["contained"]:
            failures.append(f"{label}: table {table['index']} breaks containment")
        if table["mobileCardsRequired"] and not table["mobileCardsPresent"]:
            failures.append(f"{label}: table {table['index']} lacks mobile evidence-card semantics")
    for button in state["buttons"]:
        if button["height"] < 44:
            failures.append(f"{label}: touch target below 44px ({button['id'] or button['text']})")
    for summary in state["summaries"]:
        if summary["height"] < 44:
            failures.append(f"{label}: source disclosure below 44px ({summary['text'][:48]})")
    focus = interactions["focus"]
    if focus["available"] and not (focus["enabled"] and focus["restored"] and focus["aria_when_enabled"] == "true" and focus["focus_outline"] not in ("none", "", None)):
        failures.append(f"{label}: focus-reading toggle or visible focus state failed")
    toggle = interactions["source_toggle"]
    if toggle["open_count"] != EXPECTED_SOURCE_COUNT or toggle["closed_count"] != 0 or toggle["aria_expanded"] != "true":
        failures.append(f"{label}: source ledger toggle failed")
    dialog = interactions["dialog"]
    if not all((dialog["opened"], dialog["tab_trapped"], dialog["shift_tab_trapped"], dialog["closed_by_escape"], dialog["focus_restored"], dialog["ledger_action_closed"], dialog["source_two_open"])):
        failures.append(f"{label}: evidence dialog lifecycle or focus trap failed")
    nav = interactions["nav"]
    if nav["hash"] != f"#{nav['target']}" or nav["aria_current"] != "true":
        failures.append(f"{label}: rail navigation failed")
    if print_state["navDisplay"] != "none" or print_state["railDisplay"] != "none" or print_state["sourceBodyDisplay"] == "none":
        failures.append(f"{label}: print presentation failed")
    return failures


def main() -> None:
    report_hash = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    results: dict[str, Any] = {
        "report": REPORT.name,
        "report_sha256": report_hash,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "available_engines": [],
        "unavailable_engines": {},
        "browsers": {},
        "failures": [],
    }
    with sync_playwright() as playwright:
        for name in ("chromium", "firefox", "webkit"):
            browser_type = getattr(playwright, name)
            try:
                browser = browser_type.launch(headless=True)
            except Exception as error:  # browser availability varies by machine
                results["unavailable_engines"][name] = str(error).splitlines()[0]
                continue
            results["available_engines"].append(name)
            browser_result: dict[str, Any] = {"viewports": {}, "print": {}, "offline": {}}
            try:
                browser_result["print"] = audit_print(browser)
                browser_result["offline"] = audit_offline(browser)
                offline = browser_result["offline"]
                if offline["blocked_requests"] or offline["console_errors"] or offline["page_errors"] or not offline["dialog_open"]:
                    results["failures"].append(f"{name}: offline direct-file gate failed")
                for label, viewport in VIEWPORTS.items():
                    page = browser.new_page(viewport=viewport)
                    console_errors: list[str] = []
                    page_errors: list[str] = []
                    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                    page.on("pageerror", lambda error: page_errors.append(str(error)))
                    try:
                        page.goto(REPORT.resolve().as_uri(), wait_until="networkidle")
                        state = audit_state(page)
                        interactions = exercise_interactions(page)
                        browser_result["viewports"][label] = {
                            "state": state,
                            "interactions": interactions,
                            "console_errors": console_errors,
                            "page_errors": page_errors,
                        }
                        results["failures"].extend(check_result(f"{name}/{label}", state, interactions, browser_result["print"]))
                        if console_errors or page_errors:
                            results["failures"].append(f"{name}/{label}: runtime errors")
                    except Exception as error:
                        browser_result["viewports"][label] = {"audit_error": str(error)}
                        results["failures"].append(f"{name}/{label}: audit error")
                    finally:
                        page.close()
            finally:
                browser.close()
            results["browsers"][name] = browser_result
    results["result"] = "PASS" if not results["failures"] else "FAIL"
    OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("QA_RESULT", results["result"])
    print("ENGINES", ",".join(results["available_engines"]))
    print("FAILURES", results["failures"])
    print("WROTE", OUT)
    raise SystemExit(0 if results["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
