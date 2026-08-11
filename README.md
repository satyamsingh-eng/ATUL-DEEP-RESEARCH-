# C3A Labs — Confidential Founder / Board Brief

> **Private repository only.** This is internal relationship intelligence for authorised C3A Labs review. Do not fork, share, publish, or use for outreach without explicit C3A approval.

## Purpose

This repository delivers an evidence-bounded intelligence brief on Atul Bansal for founder and board review. It is designed to support an operator-first conversation, not a lead-generation, fundraising, or relationship-access assumption.

The report explicitly separates:

- verified historical evidence;
- bounded third-party vendor reconciliation;
- inferences that require validation; and
- claims that must **not** be assumed.

## Open the brief

Open `Atul_Bansal_C3A_Network_Intelligence_Report.html` directly in a modern browser. It is self-contained and makes no runtime network calls.

Board-facing controls:

- **Evidence ledger** — jumps to the source register.
- **Inline citations** — open a source-specific evidence dialog.
- **Source register** — inspect one source at a time or open all 19.
- **Print / PDF** — produces a flattened, readable print view.

## Rebuild and validate

```bash
python -m pip install -r requirements.txt
python render_report.py
python evidence/apollo_validation/run_focused_report_qa.py
```

The QA gate runs against the direct local HTML file in the available Playwright engines and checks:

- desktop, tablet, and 390px mobile geometry;
- no page-level horizontal overflow;
- responsive evidence-card treatment for every 3+ column table;
- citation-to-source mapping and the evidence dialog lifecycle;
- keyboard Escape, focus restoration, source-ledger and reading-mode controls;
- print styles; and
- no external runtime resources.

## Release boundary

The tracked release intentionally contains only the final source Markdown, self-contained HTML, renderer, release manifest, and UI QA harness.

It deliberately excludes raw connector output, contact data, profile URLs, detailed locations, credentials, local filesystem paths, screenshots, transient logs, and intermediate research exports. The canonical report preserves citations and evidence limitations; restricted internal material remains restricted.

## Ownership

Copyright © 2026 C3A Labs. All rights reserved. See `LICENSE`.