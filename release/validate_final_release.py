#!/usr/bin/env python
"""Final publication gate for the private C3A Atul Bansal decision brief.

Checks the canonical report, self-contained HTML, release file set, source map,
and release privacy boundary. It writes machine-readable release metadata without
including local paths, raw research payloads, or contact information.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
MARKDOWN = ROOT / "Atul_Bansal_C3A_Network_Intelligence_Report.md"
HTML = ROOT / "Atul_Bansal_C3A_Network_Intelligence_Report.html"

ARTIFACTS = (
    ".gitignore",
    "README.md",
    "LICENSE",
    "requirements.txt",
    "Atul_Bansal_C3A_Network_Intelligence_Report.md",
    "Atul_Bansal_C3A_Network_Intelligence_Report.html",
    "render_report.py",
    "evidence/apollo_validation/run_focused_report_qa.py",
    "release/validate_final_release.py",
)
COMMITTED_METADATA = (
    "release/final-release-validation.json",
    "release/manifest.json",
    "release/pre-push-security-audit.json",
    "release/ui-qa-summary.json",
)
RELEASE_SURFACE = ARTIFACTS + COMMITTED_METADATA
REPORT_ARTIFACTS = (
    "README.md",
    "Atul_Bansal_C3A_Network_Intelligence_Report.md",
    "Atul_Bansal_C3A_Network_Intelligence_Report.html",
)
REQUIRED_SECTIONS = (
    "Executive decision",
    "Evidence and release boundary",
    "1. Identity controls — avoid contaminated research",
    "2. Current activity — what is actually established",
    "3. Operating and transaction record",
    "4. Investor and angel assessment",
    "5. Operating lens — how to make SARVAX legible",
    "6. Network map — pathways, not promises",
    "7. Adjacent advisor research queue — not presumed Atul routes",
    "8. C3A positioning and the first ask",
    "9. Relationship progression",
    "10. Claim firewall — what remains unproven",
    "11. Final priority actions",
    "12. Research limits",
    "Sources",
)
# Construct the expression in parts so this detector does not flag its own
# portable detection logic as a real hard-coded local path.
LOCAL_PATH_RE = re.compile(
    r"(?:/" + r"Users/[A-Za-z0-9_.-]+/|/" + r"home/[A-Za-z0-9_.-]+/|file:" + r"///)",
    re.I,
)
# Deliberately require a phone-like grouping pattern so years, money, source IDs,
# and dates do not become false positive PII findings.
PHONE_RE = re.compile(
    r"(?<![\w$])(?:\+\d{1,3}[ .-]?)?(?:(?:\(?\d{2,4}\)?[ .-])\d{3,4}[ .-]\d{3,4}|\d{5}[ .-]\d{5})(?!\w)"
)
FORBIDDEN_REPORT_PATTERNS = {
    "email_like": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "phone_like": PHONE_RE,
    "mailto": re.compile(r"mailto:", re.I),
    "linkedin_profile": re.compile(r"linkedin\.com/in/", re.I),
    "restricted_register": re.compile(r"SECTION_13_RESTRICTED_CONTACT_REGISTER|CONFIDENTIAL CONTACT DATA|Apollo-verified business email", re.I),
    "raw_vendor_identifier": re.compile(r"apollo[_ -]?(?:id|person[_ -]?id|contact[_ -]?id)", re.I),
    "local_path": LOCAL_PATH_RE,
}
SECRET_PATTERNS = {
    "openai": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "github": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws": re.compile(r"AKIA[0-9A-Z]{16}"),
    "google": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "huggingface": re.compile(r"hf_[A-Za-z0-9]{34,}"),
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def artifacts() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative in ARTIFACTS:
        path = ROOT / relative
        records.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
    return records


def check_report() -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body, separator, sources = markdown.partition("\n## Sources\n")
    if not separator:
        errors.append("missing Sources heading")
    for section in REQUIRED_SECTIONS[:-1]:
        if f"## {section}" not in body:
            errors.append(f"missing section: {section}")
    source_rows = re.findall(r"^\[(\d+)\]\s+(https://\S+)\s+—\s+(.+)$", sources, re.M)
    source_ids = [int(number) for number, _, _ in source_rows]
    expected_ids = list(range(1, 18))
    if source_ids != expected_ids:
        errors.append(f"source IDs must be 1..17 exactly; found {source_ids}")
    cited_ids = sorted({int(item) for item in re.findall(r"(?<!\w)\[(\d+)\]", body)})
    if cited_ids != expected_ids:
        errors.append(f"citation IDs must be 1..17 exactly; found {cited_ids}")
    if any(not url.startswith("https://") for _, url, _ in source_rows):
        errors.append("all source routes must use HTTPS")
    if any("[unverified]" in line.lower() for line in body.splitlines()):
        errors.append("unresolved [unverified] marker found in final report")
    return errors, {"section_count": len(REQUIRED_SECTIONS) - 1, "source_count": len(source_rows), "cited_source_ids": cited_ids}


def check_report_privacy() -> list[str]:
    errors: list[str] = []
    for relative in REPORT_ARTIFACTS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_REPORT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative}: forbidden {label} pattern")
    return errors


def check_metadata_privacy() -> list[str]:
    """Reject personal/contact material from generated committed metadata."""
    errors: list[str] = []
    for relative in COMMITTED_METADATA:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_REPORT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative}: forbidden {label} pattern")
    return errors


def check_release_code() -> list[str]:
    errors: list[str] = []
    for relative in RELEASE_SURFACE:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative}: potential {label} credential")
        if LOCAL_PATH_RE.search(text):
            errors.append(f"{relative}: local absolute path")
    return errors


def check_html() -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    html = HTML.read_text(encoding="utf-8")
    source_cards = len(re.findall(r'class="source-card"', html))
    source_ids = sorted({int(item) for item in re.findall(r'id="source-(\d+)"', html)})
    if "<title>Atul Bansal — Final C3A Decision Brief</title>" not in html:
        errors.append("final title missing from HTML")
    if source_cards != 17 or source_ids != list(range(1, 18)):
        errors.append(f"HTML source ledger mismatch: cards={source_cards}, ids={source_ids}")
    if re.search(r"<script[^>]+\bsrc=|<link[^>]+rel=\"stylesheet\"[^>]+https?://", html, re.I):
        errors.append("external runtime dependency found in HTML")
    if "linear-gradient" in html or "radial-gradient" in html or "box-shadow" in html:
        errors.append("non-flat visual treatment found in HTML")
    if "<dialog" not in html or 'id="evidence-dialog"' not in html:
        errors.append("evidence dialog missing from HTML")
    return errors, {"source_cards": source_cards, "source_ids": source_ids, "self_contained": not errors}


def main() -> int:
    errors: list[str] = []
    missing = [relative for relative in ARTIFACTS if not (ROOT / relative).is_file()]
    if missing:
        errors.extend(f"missing release artifact: {relative}" for relative in missing)
    report_errors, report_summary = check_report()
    html_errors, html_summary = check_html()
    errors.extend(report_errors)
    errors.extend(html_errors)
    errors.extend(check_report_privacy())
    errors.extend(check_metadata_privacy())
    errors.extend(check_release_code())
    if not (ROOT / "LICENSE").is_file():
        errors.append("LICENSE missing")
    if not (ROOT / ".gitignore").is_file():
        errors.append(".gitignore missing")

    now = datetime.now(timezone.utc).isoformat()
    artifact_records = artifacts()
    result = "PASS" if not errors else "BLOCK"
    validation = {
        "release": "final-r1-r2-synthesis",
        "result": result,
        "validated_at_utc": now,
        "private_repository_required": True,
        "report": report_summary,
        "html": html_summary,
        "artifacts": artifact_records,
        "errors": errors,
    }
    manifest = {
        "release": "final-r1-r2-synthesis",
        "visibility": "private_required",
        "generated_at_utc": now,
        "artifacts": artifact_records,
        "verification": {
            "final_release_gate": result,
            "section_count": report_summary["section_count"],
            "source_count": report_summary["source_count"],
            "self_contained_html": html_summary["self_contained"],
        },
        "release_boundary": {
            "included": "Final combined report, self-contained HTML, deterministic renderer, focused browser QA, and release validation code.",
            "excluded": [
                "contact data and profile URLs",
                "raw Apollo or enrichment payloads and identifiers",
                "restricted relationship material",
                "credentials, local paths, screenshots, logs, and transient research outputs",
            ],
        },
    }
    audit = {
        "result": "PASS_WITH_PRIVATE_REPOSITORY_REQUIREMENT" if not errors else "BLOCK",
        "reviewed_at_utc": now,
        "scope": "canonical final release artifacts",
        "release_policy": "The target repository must remain private. This is internal C3A relationship and product decision material.",
        "checks": {
            "secrets_tokens_api_keys": "PASS" if not any("credential" in item for item in errors) else "BLOCK",
            "contact_data_and_profile_urls": "PASS" if not any("forbidden" in item for item in errors) else "BLOCK",
            "local_absolute_paths": "PASS" if not any("local absolute path" in item for item in errors) else "BLOCK",
            "source_map_and_structure": "PASS" if not report_errors else "BLOCK",
            "self_contained_html": "PASS" if not html_errors else "BLOCK",
            "license_and_allowlist": "PASS" if not any(item.endswith("missing") for item in errors) else "BLOCK",
        },
        "errors": errors,
    }
    (RELEASE / "final-release-validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    (RELEASE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (RELEASE / "pre-push-security-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"FINAL_RELEASE_GATE {result}")
    print(f"SOURCES {report_summary['source_count']} | SECTIONS {report_summary['section_count']} | SOURCE_CARDS {html_summary['source_cards']}")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
