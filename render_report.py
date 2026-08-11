#!/usr/bin/env python
"""Build the self-contained, board-ready C3A intelligence brief.

The Markdown file remains the canonical evidence-bearing source. This renderer
only upgrades presentation, navigation, source inspection, and accessibility.
It intentionally has no external network or CDN dependency so the final brief
works when opened directly from disk.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "Atul_Bansal_C3A_Network_Intelligence_Report.md"
OUTPUT = ROOT / "Atul_Bansal_C3A_Network_Intelligence_Report.html"

SOURCE_HEADER = re.compile(r"^\[(\d+)\]\s+(https?://\S+)\s+—\s+(.+)$")
CITATION = re.compile(r"\[(\d+)\]")


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def add_class(tag: Tag, *classes: str) -> None:
    existing = list(tag.get("class") or [])
    for item in classes:
        if item not in existing:
            existing.append(item)
    tag["class"] = existing


def is_tag(node: object, name: str | None = None) -> bool:
    return isinstance(node, Tag) and (name is None or node.name == name)


def build_heading_ids(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Give every reader-facing heading a stable fragment and build the rail."""
    toc: list[tuple[str, str]] = []
    seen: set[str] = set()
    for heading in soup.find_all(["h2", "h3"]):
        title = heading.get_text(" ", strip=True)
        base = slugify(title)
        identifier = base
        counter = 2
        while identifier in seen:
            identifier = f"{base}-{counter}"
            counter += 1
        seen.add(identifier)
        heading["id"] = identifier
        if heading.name == "h2" and title not in {"Sources", "Internal source registry"}:
            toc.append((identifier, title))
    return toc


def split_source_block(markdown_text: str) -> tuple[str, str, list[tuple[str, str, str, str]]]:
    """Extract raw markdown sources before normal rendering collapses them into one paragraph."""
    marker = "\n## Sources\n"
    if marker not in markdown_text:
        return markdown_text, "", []
    report_markdown, source_markdown = markdown_text.split(marker, 1)
    introduction: list[str] = []
    entries: list[tuple[str, str, str, str]] = []
    current: list[str] | None = None
    for line in source_markdown.splitlines():
        match = SOURCE_HEADER.match(line.strip())
        if match:
            if current is not None:
                entries.append((current[0], current[1], current[2], "\n".join(current[3:])))
            current = [match.group(1), match.group(2), match.group(3)]
        elif current is None:
            introduction.append(line)
        else:
            current.append(line)
    if current is not None:
        entries.append((current[0], current[1], current[2], "\n".join(current[3:])))
    return report_markdown, "\n".join(introduction).strip(), entries


def append_source_ledger(
    soup: BeautifulSoup,
    introduction_markdown: str,
    entries: list[tuple[str, str, str, str]],
) -> int:
    """Render each retained source as a compact, inspectable details card."""
    source_heading = soup.new_tag("h2")
    source_heading.string = "Sources"
    soup.append(source_heading)
    if introduction_markdown:
        intro_fragment = BeautifulSoup(
            markdown.markdown(introduction_markdown, extensions=["nl2br"], output_format="html5"),
            "html.parser",
        )
        for node in list(intro_fragment.contents):
            soup.append(node.extract())

    ledger = soup.new_tag("div", attrs={"class": "source-ledger", "data-source-count": str(len(entries))})
    ledger_intro = soup.new_tag("div", attrs={"class": "ledger-toolbar"})
    intro_copy = soup.new_tag("p", attrs={"class": "ledger-label"})
    intro_copy.string = "Exact retained excerpts · open any source to inspect its bounded evidence"
    ledger_intro.append(intro_copy)
    toggle = soup.new_tag(
        "button",
        attrs={
            "id": "sources-toggle",
            "class": "utility-button",
            "type": "button",
            "aria-expanded": "false",
        },
    )
    toggle.string = f"Open all {len(entries)} sources"
    ledger_intro.append(toggle)
    ledger.append(ledger_intro)

    for number, url, title, supporting_markdown in entries:
        details = soup.new_tag(
            "details",
            attrs={
                "class": "source-card",
                "id": f"source-{number}",
                "data-source-index": number,
            },
        )
        summary = soup.new_tag("summary")
        number_span = soup.new_tag("span", attrs={"class": "source-number"})
        number_span.string = f"[{number}]"
        summary.append(number_span)
        title_span = soup.new_tag("span", attrs={"class": "source-title"})
        title_span.string = title
        summary.append(title_span)
        domain_span = soup.new_tag("span", attrs={"class": "source-domain"})
        domain_span.string = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url)).split("/")[0]
        summary.append(domain_span)
        details.append(summary)

        source_body = soup.new_tag("div", attrs={"class": "source-body"})
        source_link = soup.new_tag("p", attrs={"class": "source-link"})
        source_anchor = soup.new_tag(
            "a",
            attrs={"href": url, "target": "_blank", "rel": "noopener noreferrer"},
        )
        source_anchor.string = "Open official source"
        source_link.append(source_anchor)
        source_body.append(source_link)
        quote_fragment = BeautifulSoup(
            markdown.markdown(
                supporting_markdown.strip(),
                extensions=["fenced_code", "sane_lists", "nl2br"],
                output_format="html5",
            ),
            "html.parser",
        )
        for node in list(quote_fragment.contents):
            source_body.append(node.extract())
        details.append(source_body)
        ledger.append(details)

    soup.append(ledger)
    return len(entries)


def sectionize(soup: BeautifulSoup) -> None:
    """Give each major chapter a spacious, navigable report surface."""
    headings = list(soup.find_all("h2"))
    for heading in headings:
        title = heading.get_text(" ", strip=True)
        section = soup.new_tag(
            "section",
            attrs={
                "class": ["report-section", f"section-{slugify(title)}"],
                "data-anchor": heading["id"],
                "aria-labelledby": heading["id"],
            },
        )
        if title == "Executive summary":
            add_class(section, "summary-section")
        if title == "Sources":
            add_class(section, "sources-section")
        if title in {"What C3A should do next", "Final action close — WHAT C3A SHOULD DO NEXT"}:
            add_class(section, "action-section")
        if title == "Risks and red flags":
            add_class(section, "risk-section")
        if title == "Major-claim source and confidence table":
            add_class(section, "claims-section")

        heading.insert_before(section)
        node: Tag | NavigableString | None = heading
        while node is not None:
            following = node.next_sibling
            section.append(node.extract())
            if is_tag(following, "h2"):
                break
            node = following


def enhance_tables(soup: BeautifulSoup) -> None:
    """Preserve dense desktop comparisons and produce readable mobile cards."""
    for table in soup.find_all("table"):
        headers = [header.get_text(" ", strip=True) for header in table.select("thead th")]
        for header in table.select("thead th"):
            header["scope"] = "col"
        if len(headers) >= 3:
            add_class(table, "mobile-card-table")
            for row in table.select("tbody tr"):
                for index, cell in enumerate(row.find_all("td", recursive=False)):
                    if index < len(headers):
                        cell["data-label"] = headers[index]
        wrapper = soup.new_tag("div", attrs={"class": "table-shell", "tabindex": "0", "role": "region", "aria-label": "Report table"})
        if len(headers) >= 3:
            add_class(wrapper, "table-shell--mobile-card")
        table.wrap(wrapper)


def mark_evidence_language(soup: BeautifulSoup) -> None:
    """Make FACT / INFERENCE / HYPOTHESIS boundaries scannable without changing text."""
    for strong in soup.find_all("strong"):
        label = strong.get_text(" ", strip=True).upper().rstrip(".")
        if label.startswith("FACT"):
            add_class(strong, "evidence-tag", "evidence-tag--fact")
        elif label.startswith("INFERENCE"):
            add_class(strong, "evidence-tag", "evidence-tag--inference")
        elif label.startswith("HYPOTHESIS"):
            add_class(strong, "evidence-tag", "evidence-tag--hypothesis")
        elif label.startswith("NOT ESTABLISHED"):
            add_class(strong, "evidence-tag", "evidence-tag--unknown")


def link_citations(soup: BeautifulSoup) -> None:
    """Attach evidence-drawer behavior to report citations while leaving ledger text intact."""
    for text_node in list(soup.find_all(string=CITATION)):
        if text_node.find_parent(class_="source-ledger") or text_node.find_parent("code"):
            continue
        text = str(text_node)
        if not CITATION.search(text):
            continue
        parts = CITATION.split(text)
        replacement: list[Tag | NavigableString] = []
        for index, part in enumerate(parts):
            if index % 2 == 1:
                link = soup.new_tag(
                    "a",
                    attrs={
                        "class": "citation",
                        "href": f"#source-{part}",
                        "data-source-ref": part,
                        "aria-label": f"Open source {part} evidence",
                    },
                )
                link.string = f"[{part}]"
                replacement.append(link)
            elif part:
                replacement.append(NavigableString(part))
        if replacement:
            text_node.replace_with(*replacement)


def build_nav(toc: list[tuple[str, str]]) -> str:
    links = []
    for index, (identifier, title) in enumerate(toc, 1):
        links.append(
            f'<a href="#{escape(identifier)}" data-nav-target="{escape(identifier)}">'
            f'<span class="nav-index">{index:02d}</span>'
            f'<span class="nav-title">{escape(title)}</span></a>'
        )
    return "".join(links)


def render() -> None:
    markdown_text = INPUT.read_text(encoding="utf-8")
    report_markdown, source_intro, source_entries = split_source_block(markdown_text)
    soup = BeautifulSoup(
        markdown.markdown(
            report_markdown,
            extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
            output_format="html5",
        ),
        "html.parser",
    )
    source_count = append_source_ledger(soup, source_intro, source_entries)
    toc = build_heading_ids(soup)
    sectionize(soup)
    enhance_tables(soup)
    mark_evidence_language(soup)
    link_citations(soup)

    content = str(soup)
    reading_words = len(re.findall(r"\b[\w’'-]+\b", markdown_text))
    reading_minutes = max(1, round(reading_words / 210))
    nav = build_nav(toc)

    css = r'''
:root {
  --black: #000000;
  --canvas: #08080a;
  --surface: #111114;
  --surface-raised: #17171b;
  --surface-hover: #1d1d22;
  --line: #303035;
  --line-quiet: #252529;
  --text: #f5f5f7;
  --soft: #e5e5ea;
  --muted: #a1a1aa;
  --muted-2: #74747c;
  --accent: #0a84ff;
  --accent-soft: #d9ecff;
  --accent-wash: #101a25;
  --danger: #ff9f9a;
  --max: 1560px;
  --rail: 286px;
  --display: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
  --body: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
}
* { box-sizing: border-box; }
html { background: var(--black); scroll-behavior: smooth; }
body {
  margin: 0;
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
  background: var(--black);
  color: var(--text);
  font-family: var(--body);
  font-size: 16px;
  line-height: 1.64;
  letter-spacing: -0.012em;
}
button, a { font: inherit; }
a { color: inherit; }
button { -webkit-tap-highlight-color: transparent; }
::selection { background: var(--accent); color: #fff; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.skip-link {
  position: fixed; left: 18px; top: -70px; z-index: 2000;
  background: var(--text); color: var(--black); padding: 11px 14px;
  border-radius: 8px; text-decoration: none; font-weight: 750;
}
.skip-link:focus { top: 16px; }
.scroll-progress {
  position: fixed; inset: 0 auto auto 0; z-index: 1050;
  width: 0; height: 2px; background: var(--accent);
}
.topbar {
  position: sticky; top: 0; z-index: 1000;
  width: 100%; border-bottom: 1px solid rgba(255,255,255,.12);
  background: rgba(0,0,0,.88); backdrop-filter: saturate(180%) blur(18px);
}
.topbar-inner {
  width: min(100%, var(--max)); min-height: 64px; margin: 0 auto; padding: 0 28px;
  display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1fr); align-items: center; gap: 20px;
}
.brand {
  justify-self: start; color: var(--text); text-decoration: none; font-size: 12px;
  line-height: 1.1; letter-spacing: .13em; font-weight: 800; text-transform: uppercase;
}
.brand span { color: var(--muted); font-weight: 650; }
.topbar-context { color: var(--muted); font-size: 12px; text-align: center; white-space: nowrap; }
.topbar-actions { justify-self: end; display: flex; align-items: center; gap: 8px; }
.utility-button, .topbar-button {
  min-height: 44px; border: 1px solid var(--line); border-radius: 9px;
  padding: 8px 12px; color: var(--soft); background: transparent;
  cursor: pointer; font-size: 12px; font-weight: 700; line-height: 1.2;
  transition: border-color .2s ease, color .2s ease, background .2s ease, transform .2s ease;
}
.utility-button:hover, .topbar-button:hover { border-color: #6d6d75; color: var(--text); background: var(--surface-hover); transform: translateY(-1px); }
.topbar-button--accent { border-color: var(--accent); color: var(--accent-soft); }
.topbar-button--accent[aria-pressed="true"] { background: var(--accent); color: #fff; }
.shell { width: min(100%, var(--max)); margin: 0 auto; padding: 26px 28px 46px; }
.hero {
  display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(320px, .76fr); gap: 28px;
  min-height: 518px; padding: clamp(34px, 5vw, 76px); border: 1px solid var(--line);
  background: var(--surface); border-radius: 18px;
}
.hero-copy { display: flex; min-width: 0; flex-direction: column; justify-content: space-between; }
.eyebrow, .rail-label, .section-kicker, .metric-label, .decision-label, .source-number {
  color: var(--accent-soft); font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase;
}
.hero h1 {
  margin: 18px 0 18px; max-width: 860px; color: var(--text); font-family: var(--display);
  font-size: clamp(54px, 7.2vw, 96px); font-weight: 720; letter-spacing: -.062em; line-height: .96;
}
.hero-lead { max-width: 775px; margin: 0; color: var(--soft); font-size: clamp(19px, 2vw, 25px); line-height: 1.38; letter-spacing: -.027em; }
.hero-footnote { margin-top: 40px; color: var(--muted); font-size: 13px; }
.decision-panel {
  align-self: stretch; display: flex; flex-direction: column; justify-content: space-between;
  border: 1px solid #3b5e80; border-radius: 14px; padding: 24px; background: var(--accent-wash);
}
.decision-panel h2 { margin: 12px 0; max-width: 360px; color: var(--text); font-family: var(--display); font-size: 29px; line-height: 1.08; letter-spacing: -.042em; }
.decision-panel p { margin: 0; color: var(--soft); font-size: 14px; line-height: 1.5; }
.decision-boundary { padding-top: 20px; border-top: 1px solid rgba(255,255,255,.14); color: var(--accent-soft); font-size: 13px; font-weight: 700; }
.signal-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; margin-top: 22px;
  border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: var(--line);
}
.signal { min-width: 0; min-height: 154px; padding: 22px; background: var(--surface); }
.signal:hover { background: var(--surface-hover); }
.signal .metric-label { display: block; color: var(--muted); }
.signal strong { display: block; margin-top: 15px; color: var(--text); font-family: var(--display); font-size: 30px; letter-spacing: -.045em; line-height: 1; }
.signal p { margin: 10px 0 0; color: var(--soft); font-size: 13px; line-height: 1.4; }
.citation { color: var(--accent-soft); text-decoration: none; font-size: .8em; font-weight: 800; white-space: nowrap; }
.citation:hover { color: #fff; text-decoration: underline; text-underline-offset: 3px; }
.board-snapshot {
  display: grid; grid-template-columns: .76fr 1.24fr; gap: 1px; margin-top: 22px;
  border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: var(--line);
}
.snapshot-heading { display: flex; flex-direction: column; justify-content: space-between; min-height: 236px; padding: 28px; background: #f5f5f7; color: #17171b; }
.snapshot-heading .section-kicker { color: #0066cc; }
.snapshot-heading h2 { max-width: 380px; margin: 14px 0 0; font-family: var(--display); font-size: clamp(28px, 3vw, 42px); letter-spacing: -.05em; line-height: 1.02; }
.snapshot-heading p { margin: 0; color: #56565d; font-size: 14px; line-height: 1.5; }
.snapshot-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 1px; background: var(--line); }
.snapshot-card { min-width: 0; padding: 28px; background: var(--surface); }
.snapshot-card h3 { margin: 12px 0 10px; color: var(--text); font-family: var(--display); font-size: 20px; line-height: 1.15; letter-spacing: -.03em; }
.snapshot-card p { margin: 0; color: var(--soft); font-size: 14px; line-height: 1.52; }
.workspace { display: grid; grid-template-columns: var(--rail) minmax(0, 1fr); align-items: start; gap: 24px; margin-top: 24px; }
.side-rail {
  position: sticky; top: 80px; max-height: calc(100vh - 96px); overflow: auto;
  border: 1px solid var(--line); border-radius: 14px; background: #0e0e11; padding: 14px;
}
.rail-header { padding: 8px 9px 16px; border-bottom: 1px solid var(--line-quiet); }
.rail-header h2 { margin: 7px 0 0; color: var(--text); font-family: var(--display); font-size: 20px; line-height: 1.1; letter-spacing: -.03em; }
.rail-progress { margin-top: 11px; color: var(--muted); font-size: 12px; }
.side-rail nav { margin-top: 10px; }
.side-rail nav a {
  display: grid; grid-template-columns: 27px minmax(0, 1fr); column-gap: 7px; align-items: start;
  padding: 10px 9px; border-radius: 8px; color: var(--soft); text-decoration: none; font-size: 12px; line-height: 1.35;
  transition: color .2s ease, background .2s ease;
}
.side-rail nav a:hover, .side-rail nav a[aria-current="true"] { color: var(--text); background: var(--surface-hover); }
.side-rail nav a[aria-current="true"] .nav-index { color: var(--accent-soft); }
.nav-index { color: var(--muted-2); font-variant-numeric: tabular-nums; }
.rail-footer { margin-top: 14px; padding: 15px 9px 6px; border-top: 1px solid var(--line-quiet); }
.rail-footer p { margin: 8px 0 14px; color: var(--muted); font-size: 12px; line-height: 1.45; }
.rail-footer .utility-button { width: 100%; }
.report { min-width: 0; }
.report-section {
  min-width: 0; padding: 58px clamp(26px, 4.5vw, 64px); border: 1px solid var(--line); border-radius: 14px;
  background: var(--surface); scroll-margin-top: 84px;
}
.report-section + .report-section { margin-top: 20px; }
.summary-section { padding-top: clamp(34px, 4.5vw, 62px); }
.report-section h1 { display: none; }
.report-section h2 {
  max-width: 920px; margin: 0 0 24px; color: var(--text); font-family: var(--display);
  font-size: clamp(32px, 4vw, 52px); font-weight: 720; letter-spacing: -.054em; line-height: 1.02;
}
.report-section h2::before { content: "Decision record"; display: block; margin-bottom: 12px; color: var(--accent-soft); font-family: var(--body); font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.sources-section h2::before { content: "Evidence ledger"; }
.claims-section h2::before { content: "Proof boundary"; }
.risk-section h2::before { content: "Founder guardrails"; }
.action-section h2::before { content: "Action sequence"; }
.report-section h3 { max-width: 860px; margin: 42px 0 14px; color: var(--text); font-family: var(--display); font-size: 24px; line-height: 1.16; letter-spacing: -.034em; }
.report-section p { max-width: 900px; margin: 0 0 18px; color: var(--soft); }
.report-section p + p { margin-top: 3px; }
.report-section strong { color: var(--text); font-weight: 720; }
.report-section em { color: var(--soft); }
.report-section code { overflow-wrap: anywhere; word-break: break-word; color: var(--accent-soft); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .88em; }
.report-section hr { border: 0; border-top: 1px solid var(--line); margin: 48px 0; }
.report-section ul, .report-section ol { max-width: 920px; margin: 0 0 22px; padding-left: 22px; color: var(--soft); }
.report-section li { margin: 9px 0; padding-left: 3px; }
.evidence-tag {
  display: inline-block; border: 1px solid #3b5e80; border-radius: 999px; padding: 3px 7px;
  color: var(--accent-soft) !important; background: var(--accent-wash); font-size: .72em; letter-spacing: .06em; line-height: 1.1;
}
.evidence-tag--unknown, .evidence-tag--hypothesis { border-color: #5e5e65; color: var(--soft) !important; background: #1a1a1e; }
.evidence-tag--inference { border-color: #494955; color: var(--soft) !important; background: #17171b; }
blockquote {
  max-width: 900px; margin: 28px 0; padding: 21px 23px; border: 1px solid #36536e; border-left: 3px solid var(--accent); border-radius: 0 10px 10px 0;
  background: #101720;
}
blockquote p { margin: 0; color: var(--soft); }
.table-shell { width: 100%; max-width: 100%; margin: 26px 0 34px; overflow-x: auto; border: 1px solid var(--line); border-radius: 11px; -webkit-overflow-scrolling: touch; }
table { width: 100%; min-width: 660px; border-collapse: collapse; color: var(--soft); font-size: 13px; line-height: 1.5; }
thead th { background: #1a1a1f; color: var(--text); font-size: 11px; font-weight: 800; letter-spacing: .07em; text-transform: uppercase; }
th, td { padding: 15px 16px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); vertical-align: top; text-align: left; }
th:last-child, td:last-child { border-right: 0; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:nth-child(even) td { background: #151519; }
td:first-child { color: var(--text); font-weight: 680; }
.risk-section { border-color: #4d4648; background: #131214; }
.risk-section ol { counter-reset: risk; list-style: none; padding-left: 0; }
.risk-section ol li { position: relative; padding: 13px 0 13px 41px; border-top: 1px solid var(--line-quiet); }
.risk-section ol li::before { content: counter(risk, decimal-leading-zero); counter-increment: risk; position: absolute; left: 0; top: 14px; color: var(--danger); font-size: 12px; font-weight: 800; letter-spacing: .08em; }
.action-section > ol {
  display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 1px; max-width: none; padding: 1px; list-style: none;
  counter-reset: action; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: var(--line);
}
.action-section > ol li { min-width: 0; min-height: 178px; margin: 0; padding: 22px; background: var(--surface-raised); }
.action-section > ol li::before { content: counter(action, decimal-leading-zero); counter-increment: action; display: block; margin-bottom: 23px; color: var(--accent-soft); font-size: 11px; font-weight: 800; letter-spacing: .1em; }
.sources-section { background: #0d0d10; }
.ledger-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 0 0 16px; padding: 17px 18px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface-raised); }
.ledger-label { margin: 0 !important; color: var(--muted) !important; font-size: 13px; }
.source-ledger { display: grid; gap: 10px; max-width: 100%; }
.source-card { border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.source-card summary { display: grid; grid-template-columns: 45px minmax(0, 1fr) auto; align-items: center; min-height: 44px; gap: 12px; cursor: pointer; padding: 16px 18px; color: var(--text); list-style: none; }
.source-card summary::-webkit-details-marker { display: none; }
.source-card summary::after { content: "+"; display: none; }
.source-card[open] summary { border-bottom: 1px solid var(--line); background: var(--surface-raised); }
.source-number { color: var(--accent-soft); }
.source-title { min-width: 0; font-size: 14px; font-weight: 700; line-height: 1.35; }
.source-domain { color: var(--muted); font-size: 11px; white-space: nowrap; }
.source-body { padding: 18px; }
.source-body p { max-width: none; font-size: 13px; }
.source-body blockquote { max-width: none; margin: 12px 0; padding: 13px 15px; font-size: 13px; background: #111820; }
.source-body blockquote:last-child { margin-bottom: 0; }
.source-link { margin-bottom: 14px !important; }
.source-link a { color: var(--accent-soft); font-weight: 750; text-underline-offset: 3px; }
.footer { margin: 24px 0 0; padding: 22px 4px 0; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; line-height: 1.5; }
.dialog {
  width: min(720px, calc(100vw - 32px)); max-height: min(78vh, 760px); border: 1px solid #4f6376; border-radius: 14px;
  padding: 0; color: var(--text); background: var(--surface); overflow: auto;
}
.dialog::backdrop { background: rgba(0,0,0,.72); }
.dialog-header { position: sticky; top: 0; z-index: 1; display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 18px 20px; border-bottom: 1px solid var(--line); background: #151519; }
.dialog-title { margin: 0; color: var(--text); font-family: var(--display); font-size: 20px; line-height: 1.2; letter-spacing: -.03em; }
.dialog-body { padding: 20px; }
.dialog-body .source-body { padding: 0; }
.dialog-body p { color: var(--soft); }
.dialog-actions { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 20px 20px; }
.visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
body.focus-mode .workspace { grid-template-columns: minmax(0, 1fr); }
body.focus-mode .side-rail { display: none; }
body.focus-mode .report-section p, body.focus-mode .report-section h2, body.focus-mode .report-section h3 { max-width: 1050px; }
@media (max-width: 1220px) {
  :root { --rail: 250px; }
  .hero { grid-template-columns: minmax(0, 1.35fr) minmax(300px, .82fr); }
  .signal-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .action-section > ol { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 980px) {
  .topbar-inner { grid-template-columns: minmax(0,1fr) auto; }
  .topbar-context { display: none; }
  .hero { grid-template-columns: 1fr; min-height: 0; }
  .decision-panel { min-height: 220px; }
  .board-snapshot { grid-template-columns: 1fr; }
  .snapshot-heading { min-height: 0; }
  .workspace { grid-template-columns: 1fr; }
  .side-rail { position: static; max-height: none; }
  .side-rail nav { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px; }
  .rail-footer { display: flex; align-items: center; gap: 18px; }
  .rail-footer p { flex: 1; margin: 0; }
  .rail-footer .utility-button { width: auto; }
}
@media (max-width: 720px) {
  body { font-size: 15px; }
  .shell { padding: 12px 12px 32px; }
  .topbar-inner { min-height: 62px; padding: 0 12px; gap: 8px; }
  .brand { font-size: 11px; }
  .brand span { display: none; }
  .topbar-actions { gap: 5px; }
  .topbar-button { min-height: 44px; padding: 8px 9px; font-size: 11px; }
  .topbar-button--focus { display: none; }
  .hero { gap: 22px; padding: 30px 24px; border-radius: 13px; }
  .hero h1 { font-size: clamp(45px, 15vw, 62px); letter-spacing: -.058em; }
  .hero-lead { font-size: 19px; }
  .hero-footnote { margin-top: 28px; }
  .decision-panel { padding: 20px; min-height: 0; }
  .signal-grid, .snapshot-grid { grid-template-columns: 1fr; }
  .signal { min-height: 0; padding: 19px; }
  .snapshot-heading, .snapshot-card { padding: 24px; }
  .workspace { gap: 12px; margin-top: 12px; }
  .side-rail { padding: 10px; border-radius: 13px; }
  .side-rail nav { grid-template-columns: 1fr; }
  .rail-footer { display: block; }
  .rail-footer p { margin: 8px 0 14px; }
  .rail-footer .utility-button { width: 100%; }
  .report-section { padding: 38px 22px; border-radius: 13px; }
  .report-section + .report-section { margin-top: 12px; }
  .report-section h2 { font-size: 33px; letter-spacing: -.047em; }
  .report-section h3 { margin-top: 34px; font-size: 22px; }
  .report-section p { font-size: 15px; line-height: 1.6; }
  .table-shell { margin: 22px 0 29px; border: 1px solid var(--line); border-radius: 11px; overflow-x: auto; }
  .table-shell--mobile-card { border: 0; border-radius: 0; overflow: visible; }
  table.mobile-card-table { display: block; min-width: 0; border: 0; }
  table.mobile-card-table thead { display: none; }
  table.mobile-card-table tbody, table.mobile-card-table tr, table.mobile-card-table td { display: block; width: 100%; }
  table.mobile-card-table tr { margin: 12px 0; padding: 14px 16px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface-raised); }
  table.mobile-card-table td { padding: 8px 0; border: 0; background: transparent !important; color: var(--soft); }
  table.mobile-card-table td::before { content: attr(data-label); display: block; margin-bottom: 4px; color: var(--muted); font-size: 10px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
  table.mobile-card-table td:first-child { color: var(--text); }
  .action-section > ol { grid-template-columns: 1fr; padding: 0; border: 0; background: transparent; gap: 10px; }
  .action-section > ol li { min-height: 0; border: 1px solid var(--line); border-radius: 10px; padding: 18px; }
  .action-section > ol li::before { margin-bottom: 14px; }
  .ledger-toolbar { display: block; padding: 16px; }
  .ledger-label { margin-bottom: 13px !important; }
  .ledger-toolbar .utility-button { width: 100%; }
  .source-card summary { grid-template-columns: 40px minmax(0,1fr); padding: 15px; }
  .source-domain { grid-column: 2; white-space: normal; }
  .source-body { padding: 15px; }
  .dialog { width: calc(100vw - 20px); max-height: 84vh; }
  .dialog-header { padding: 16px; }
  .dialog-body { padding: 16px; }
  .dialog-actions { padding: 0 16px 16px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
@media print {
  :root { --black:#fff; --canvas:#fff; --surface:#fff; --surface-raised:#fff; --line:#d2d2d7; --text:#111114; --soft:#2c2c31; --muted:#55555c; --accent:#0066cc; --accent-soft:#005bb5; }
  html, body { width: 100%; max-width: none; overflow: visible; background: #fff !important; color: #111114 !important; font-size: 10.2pt; }
  .skip-link, .scroll-progress, .topbar, .side-rail, .utility-button, .topbar-button, .dialog { display: none !important; }
  .shell { width: 100%; max-width: none; padding: 0; }
  .hero { display: block; min-height: 0; border: 0; border-radius: 0; padding: 22mm 18mm; background: #fff; page-break-after: always; }
  .hero h1, .decision-panel h2, .snapshot-heading h2, .report-section h2, .report-section h3, .signal strong { color: #111114 !important; }
  .hero-lead, .hero-footnote, .decision-panel p, .decision-boundary, .snapshot-heading p, .snapshot-card p, .report-section p, .report-section li { color: #2c2c31 !important; }
  .decision-panel { margin-top: 16mm; border-color: #bfc6cc; background: #f5f5f7; }
  .signal-grid, .board-snapshot { border-color: #d2d2d7; background: #d2d2d7; }
  .signal, .snapshot-card { background: #fff; }
  .snapshot-heading { background: #f5f5f7; }
  .workspace { display: block; margin: 0; }
  .report-section { margin: 0 !important; padding: 18mm 14mm; border: 0; border-radius: 0; background: #fff; break-before: page; }
  .summary-section { break-before: auto; }
  .report-section h2::before { color: #0066cc; }
  .table-shell { overflow: visible; border-color: #d2d2d7; }
  table { min-width: 0; font-size: 8.8pt; }
  thead th, tbody tr:nth-child(even) td { background: #f5f5f7 !important; color: #111114 !important; }
  th, td { border-color: #d2d2d7; color: #2c2c31 !important; }
  td:first-child { color: #111114 !important; }
  blockquote { border-color: #bfc6cc; border-left-color: #0066cc; background: #f5f5f7; }
  .source-card { display: block; border-color: #d2d2d7; break-inside: avoid; }
  .source-card summary { color: #111114; background: #f5f5f7; }
  .source-card:not([open]) .source-body { display: block !important; }
  .source-body { display: block !important; }
  .source-body blockquote { background: #f5f5f7; }
  .footer { color: #55555c; }
  a { color: inherit; text-decoration: none; }
}
'''

    html_document = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="Internal, evidence-bounded founder and board intelligence brief for C3A Labs." />
  <meta name="color-scheme" content="dark" />
  <link rel="icon" href="data:," />
  <title>Atul Bansal — C3A Labs Intelligence Brief</title>
  <style>{css}</style>
</head>
<body>
  <a class="skip-link" href="#brief-content">Skip to brief content</a>
  <div id="scroll-progress" role="progressbar" aria-label="Report reading progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"></div>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="#executive-summary">C3A Labs <span>/ internal decision brief</span></a>
      <div class="topbar-context">Founder / operator / advisor intelligence · evidence-bound</div>
      <div class="topbar-actions" aria-label="Brief controls">
        <button class="topbar-button topbar-button--focus" id="focus-toggle" type="button" aria-pressed="false">Focus reading</button>
        <button class="topbar-button topbar-button--accent" id="open-evidence" type="button">Evidence ledger</button>
        <button class="topbar-button" id="print-report" type="button">Print / PDF</button>
      </div>
    </div>
  </header>
  <main class="shell">
    <section class="hero" aria-labelledby="cover-title">
      <div class="hero-copy">
        <div>
          <div class="eyebrow">Internal founder / board intelligence</div>
          <h1 id="cover-title">Atul Bansal</h1>
          <p class="hero-lead">A relationship-first decision brief: where an experienced enterprise operator can change C3A’s trajectory—and how to earn, rather than extract, relevant introductions.</p>
        </div>
        <p class="hero-footnote">Prepared for C3A Labs · internal use only · research cut-off stated within the record</p>
      </div>
      <aside class="decision-panel" aria-label="Decision at a glance">
        <div>
          <div class="decision-label">Recommended posture</div>
          <h2>Operator judgment before capital or network asks.</h2>
          <p>Start with a hard critique of focus, enterprise readiness, and the proof threshold. Let any advisory, investment, or introduction role emerge only after value exchange.</p>
        </div>
        <div class="decision-boundary">The historic network is context—not promised access.</div>
      </aside>
    </section>

    <section class="signal-grid" aria-label="Evidence-backed decision signals">
      <article class="signal"><span class="metric-label">Verified transaction</span><strong>$88m</strong><p>Laurel acquisition by ECI, primary SEC evidence <a class="citation" href="#source-2" data-source-ref="2" aria-label="Open source 2 evidence">[2]</a></p></article>
      <article class="signal"><span class="metric-label">Founder-exit record</span><strong>1</strong><p>Documented founder exit; Timesys is a later acquisition during CEO tenure.</p></article>
      <article class="signal"><span class="metric-label">Revalidation scope</span><strong>56</strong><p>Named people audited through privacy-minimised vendor-record reconciliation.</p></article>
      <article class="signal"><span class="metric-label">Primary route</span><strong>45 min</strong><p>A bounded founder/operator critique, not an opening funding or introductions request.</p></article>
    </section>

    <section class="board-snapshot" aria-labelledby="snapshot-title">
      <div class="snapshot-heading">
        <div>
          <div class="section-kicker">Board read</div>
          <h2 id="snapshot-title">The decision in three moves.</h2>
        </div>
        <p>Read the opportunity as an operating relationship to earn—not an investor database to extract from.</p>
      </div>
      <div class="snapshot-grid">
        <article class="snapshot-card"><div class="section-kicker">01 / Start</div><h3>Send a crisp one-pager</h3><p>Frame SARVAX as approval-aware work execution for financial operations. Leave KARAX, pricing, and broad claims out.</p></article>
        <article class="snapshot-card"><div class="section-kicker">02 / Prove</div><h3>Show one governed workflow</h3><p>Demonstrate input, structured action, human approval, and controlled downstream completion—not platform theatre.</p></article>
        <article class="snapshot-card"><div class="section-kicker">03 / Earn</div><h3>Ask for one category</h3><p>After visible follow-through, ask which single operator or investor archetype would add the most useful pressure test.</p></article>
      </div>
    </section>

    <div class="workspace">
      <aside class="side-rail" aria-label="Report navigation">
        <div class="rail-header">
          <div class="rail-label">Brief sequence</div>
          <h2>Decision record</h2>
          <div class="rail-progress" id="rail-progress">0% read · ~{reading_minutes} min</div>
        </div>
        <nav aria-label="Report sections">{nav}</nav>
        <div class="rail-footer">
          <p>Documented formal ties, organization-level context, and unverified hypotheses are deliberately separated.</p>
          <button class="utility-button" id="rail-evidence" type="button">Open evidence ledger</button>
        </div>
      </aside>
      <article class="report" id="brief-content">{content}</article>
    </div>
    <footer class="footer">Evidence-first internal brief. Citations open a bounded retained excerpt; source accessibility does not turn historic wording into a current-role claim.</footer>
  </main>

  <dialog class="dialog" id="evidence-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
    <div class="dialog-header">
      <h2 class="dialog-title" id="dialog-title">Evidence</h2>
      <button class="utility-button" id="dialog-close" type="button">Close</button>
    </div>
    <div class="dialog-body" id="dialog-body"></div>
    <div class="dialog-actions">
      <button class="utility-button topbar-button--accent" id="dialog-open-ledger" type="button">Open in ledger</button>
    </div>
  </dialog>
  <div class="visually-hidden" id="interaction-status" aria-live="polite"></div>

  <script>
  (() => {{
    const documentElement = document.documentElement;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const status = document.getElementById('interaction-status');
    const progress = document.getElementById('scroll-progress');
    const railProgress = document.getElementById('rail-progress');
    const dialog = document.getElementById('evidence-dialog');
    const dialogTitle = document.getElementById('dialog-title');
    const dialogBody = document.getElementById('dialog-body');
    const dialogClose = document.getElementById('dialog-close');
    const dialogLedger = document.getElementById('dialog-open-ledger');
    let sourceTrigger = null;
    let sourceId = null;

    const announce = (message) => {{ status.textContent = ''; window.setTimeout(() => {{ status.textContent = message; }}, 20); }};
    const scrollToElement = (element) => {{
      if (!element) return;
      element.scrollIntoView({{ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' }});
    }};
    const updateProgress = () => {{
      const available = Math.max(1, documentElement.scrollHeight - documentElement.clientHeight);
      const percent = Math.min(100, Math.max(0, (window.scrollY / available) * 100));
      progress.style.width = `${{percent}}%`;
      progress.setAttribute('aria-valuenow', String(Math.round(percent)));
      railProgress.textContent = `${{Math.round(percent)}}% read · ~{reading_minutes} min`;
    }};
    window.addEventListener('scroll', updateProgress, {{ passive: true }});
    updateProgress();

    const focusToggle = document.getElementById('focus-toggle');
    focusToggle.addEventListener('click', () => {{
      const active = document.body.classList.toggle('focus-mode');
      focusToggle.setAttribute('aria-pressed', String(active));
      focusToggle.textContent = active ? 'Show navigation' : 'Focus reading';
      announce(active ? 'Focus reading enabled.' : 'Report navigation restored.');
    }});

    const sourcesHeading = document.getElementById('sources');
    const sourcesSection = sourcesHeading?.closest('.report-section');
    const openEvidence = () => {{
      scrollToElement(sourcesHeading);
      window.setTimeout(() => {{ sourcesSection?.classList.add('evidence-attention'); }}, reducedMotion ? 0 : 280);
      window.setTimeout(() => {{ sourcesSection?.classList.remove('evidence-attention'); }}, 1050);
      announce('Evidence ledger opened.');
    }};
    document.getElementById('open-evidence').addEventListener('click', openEvidence);
    document.getElementById('rail-evidence').addEventListener('click', openEvidence);

    const sourceToggle = document.getElementById('sources-toggle');
    if (sourceToggle) {{
      sourceToggle.addEventListener('click', () => {{
        const cards = [...document.querySelectorAll('.source-card')];
        const shouldOpen = cards.some(card => !card.open);
        cards.forEach(card => {{ card.open = shouldOpen; }});
        sourceToggle.setAttribute('aria-expanded', String(shouldOpen));
        sourceToggle.textContent = shouldOpen ? 'Close source entries' : `Open all ${{cards.length}} sources`;
        announce(shouldOpen ? 'All retained sources expanded.' : 'All retained sources collapsed.');
      }});
    }}

    const openSource = (number, trigger) => {{
      const source = document.getElementById(`source-${{number}}`);
      const body = source?.querySelector('.source-body');
      const title = source?.querySelector('.source-title')?.textContent?.trim();
      if (!source || !body || !title) return;
      sourceId = number;
      sourceTrigger = trigger || null;
      dialogTitle.textContent = `Source [${{number}}] · ${{title}}`;
      dialogBody.replaceChildren(body.cloneNode(true));
      if (!dialog.open) dialog.showModal();
      dialogClose.focus();
      announce(`Source ${{number}} evidence opened.`);
    }};
    document.querySelectorAll('.citation[data-source-ref]').forEach(citation => {{
      citation.addEventListener('click', event => {{
        event.preventDefault();
        openSource(citation.dataset.sourceRef, citation);
      }});
    }});
    dialogClose.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {{ if (event.target === dialog) dialog.close(); }});
    dialog.addEventListener('keydown', event => {{
      if (event.key !== 'Tab') return;
      const focusable = [...dialog.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')]
        .filter(element => element.getClientRects().length > 0);
      if (!focusable.length) return;
      const current = focusable.indexOf(document.activeElement);
      const next = event.shiftKey
        ? (current <= 0 ? focusable.length - 1 : current - 1)
        : (current < 0 || current >= focusable.length - 1 ? 0 : current + 1);
      event.preventDefault();
      focusable[next].focus();
    }});
    dialog.addEventListener('close', () => {{
      if (sourceTrigger) sourceTrigger.focus();
      sourceTrigger = null;
    }});
    dialogLedger.addEventListener('click', () => {{
      const source = sourceId ? document.getElementById(`source-${{sourceId}}`) : null;
      if (source) {{
        source.open = true;
        dialog.close();
        scrollToElement(source);
        announce(`Source ${{sourceId}} opened in the evidence ledger.`);
      }}
    }});

    document.querySelectorAll('.side-rail nav a[data-nav-target]').forEach(link => {{
      link.addEventListener('click', event => {{
        event.preventDefault();
        const target = document.getElementById(link.dataset.navTarget);
        if (!target) return;
        history.replaceState(null, '', `#${{link.dataset.navTarget}}`);
        activate(link.dataset.navTarget);
        scrollToElement(target);
        link.focus({{ preventScroll: true }});
      }});
    }});

    const sections = [...document.querySelectorAll('.report-section[data-anchor]')];
    const navLinks = [...document.querySelectorAll('.side-rail nav a[data-nav-target]')];
    const activate = (anchor) => {{
      navLinks.forEach(link => link.setAttribute('aria-current', String(link.dataset.navTarget === anchor)));
    }};
    const updateActiveByScroll = () => {{
      const threshold = Math.max(100, window.innerHeight * .27);
      let activeSection = sections[0];
      for (const section of sections) {{
        const heading = section.querySelector('h2');
        if (heading && heading.getBoundingClientRect().top <= threshold) activeSection = section;
        else break;
      }}
      if (activeSection) activate(activeSection.dataset.anchor);
    }};
    window.addEventListener('scroll', updateActiveByScroll, {{ passive: true }});
    updateActiveByScroll();
    const sourceHash = location.hash.match(/^#source-(\d+)$/);
    if (sourceHash) {{
      const source = document.getElementById(`source-${{sourceHash[1]}}`);
      if (source) source.open = true;
    }}
    document.getElementById('print-report').addEventListener('click', () => window.print());
  }})();
  </script>
</body>
</html>'''

    OUTPUT.write_text(html_document, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes; {source_count} source cards)")


if __name__ == "__main__":
    render()
