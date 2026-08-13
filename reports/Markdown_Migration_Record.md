# Markdown Migration Record — Atul Bansal Intelligence Package

> **PRIVATE · C3A Labs · SARVAX**
> **Decision:** legacy HTML is deliberately removed. The replacement is a Markdown-first board decision package with explicit evidence and uncertainty controls.

## Why this migration exists

The prior HTML dossier was visually elaborate but weak as a founder/board decision product: it made the narrative too broad, mixed strong historical evidence with non-decision-changing topology, and let the unresolved present-tense questions sit too far below the fold.

The replacement resets the reader journey:

1. **The board call first** — what C3A should do now.
2. **The present-tense gap second** — what is unknown and must not be assumed.
3. **The career/transaction record third** — only the historical evidence that changes the operating hypothesis.
4. **Ecosystem topology fourth** — visibly limited to organization-level context.
5. **Source notes and full evidence ledger last** — inspectable without making the report read like a scrapbook.

## Apple design-system translation for Markdown

`DESIGN-apple.md` remains the visual authority. Markdown cannot carry its color/typography layer, so the report applies its usable information-design principles:

| Apple principle | Markdown implementation |
|---|---|
| One product / one message | One board decision and one recommended first ask at the top. |
| Tight hierarchy, generous whitespace | Short sections, decisive headings, dividers, and no narrative walls. |
| Alternating scene rhythm | Decision → boundary → evidence → action progression; tables only where comparison improves clarity. |
| Accent restraint | Bold is reserved for verdicts, evidence class, and explicit constraints. |
| Clear interaction affordance | Relative links, a compact source ledger, and explicit reading order. |
| Accessibility / responsive reading | Plain Markdown, semantic headings, compact tables, and prose that remains usable without a browser UI. |

## Preservation mapping

| Legacy artifact | Preserved/reconciled in Markdown | Disposition |
|---|---|---|
| `Atul_Bansal_C3A_Network_Intelligence_Report.html` | `Atul_Bansal_C3A_Network_Intelligence_Report.md` and the new board brief | Removed after retaining the canonical combined research source. |
| `reports/Atul_Bansal_Professional_Kundali_Final_2026.html` | `Atul_Bansal_Board_Decision_Brief.md`, `reports/Atul_Bansal_Professional_Kundali_Evidence_Ledger.md`, and the unresolved-claims ledger | Removed after reconciling all 25 released evidence cards into Markdown. |
| `reports/Atul_Bansal_Professional_Kundali_Evidence_2026.json` | `reports/Atul_Bansal_Professional_Kundali_Evidence_Ledger.md` | Removed after every evidence-card ID, claim, rationale, source/date, confidence, and boundary was migrated into Markdown. |
| `SARVAX_Founder_Operator_One_Pager_Draft.html` | `SARVAX_Founder_Operator_One_Pager_Draft.md` | Removed after its internal product-context content was preserved. |
| HTML renderer, browser QA, release manifest/validator | Markdown-first structure/privacy/citation validation record | Removed as obsolete HTML-only tooling. |

## Material source reconciliation

- **Citation-route correction:** a post-rebuild audit found that the board brief’s ECI 2005 Form 6-K citation pointed to the filing wrapper rather than its acquisition-release exhibit. The canonical board and ledger links now point to the SEC Exhibit 3 source text. The TimeSys CEO appointment ledger link likewise uses the full canonical article route; both repaired URLs returned HTTP 200 on 14 August 2026.
- **Non-fit source-drift material:** preserved in the full audit archive only. It is excluded from the board brief and Board-Fit Claims Ledger because it does not affect the operator-fit decision.
- **Operator-fit consequence:** no report layer may treat adjacent people, historic co-listings, stale labels, or transaction advisers as a relationship, route, board/advisory position, current operating status, investment capacity, or authority.

## What remains intentionally unresolved

The migration preserves uncertainty rather than hiding it. The board path does not establish a 2026 title, active investment mandate, board/advisory status, relationship strength, warm access, wealth-management buyer route, or personal transaction economics.

## Canonical files after migration

- [Professional Kundali: Board Decision Brief](../Atul_Bansal_Board_Decision_Brief.md)
- [Board-Fit Claims Ledger](Atul_Bansal_Evidence_and_Unresolved_Claims_Ledger.md)
- [Full Audit Evidence Ledger](Atul_Bansal_Professional_Kundali_Evidence_Ledger.md) — retained provenance archive, outside the board path.
- [Markdown Citation Validation](Markdown_Citation_Validation_2026-08-13.md)
- [Markdown-First Release Validation](Markdown_First_Release_Validation_2026-08-13.md)
- [Preserved SARVAX Founder / Operator Context](../SARVAX_Founder_Operator_One_Pager_Draft.md)

These files are the complete review surface. Local raw source extracts are not a parallel report, nor a substitute for the boundaries stated in the ledgers.

No outbound communication was sent as part of this migration.
