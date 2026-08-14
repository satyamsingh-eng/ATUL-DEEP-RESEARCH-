# Additional Public-Source Research Log — Atul Bansal

**Research cut-off:** 11 August 2026  
**Purpose:** Resolve or constrain current-affiliation claims after the privacy-minimised Apollo cross-check.  
**Rule:** A current public page may corroborate only the exact text it displays. It cannot establish authority, ownership, investment capacity, personal relationships, or willingness to help C3A.

## 1. Innosential historical page capture and source drift

- **Historical source capture:** https://innosential.com/ (undated page retrieved 11 August 2026; earlier report source [17]).
- **Retained exact text from that capture:** “Mr. Atul Bansal Founder, CEO Timesys.”
- **Current recheck:** on 13 August 2026, both the public root page and `https://innosential.com/about-us/` no longer displayed `Atul Bansal` or `Timesys` in their rendered public text.
- **What the historical capture supports:** only that the earlier captured page displayed an Atul Bansal entry described through Timesys.
- **What neither source state supports:** Apollo’s `Strategic Advisor`, `Co-Founder`, or `Past Chairman` fields; an Innosential operational remit; ownership; board status; investment capacity; current Timesys status; or any current relationship.
- **Report treatment:** classify as **SOURCE DRIFT / WITHHELD**. Preserve the historical text as research context; do not promote it as a present role or current public co-listing.

## 2. aicas official-site check

- **Pages checked:** https://www.aicas.com/about-us/leadership/ plus the official WordPress REST search endpoints for `Atul Bansal` and `Bansal`.
- **Retained evidence:** `evidence/S19_aicas_leadership_page.txt`, `evidence/S21_aicas_wp_search_atul_bansal.json`, and `evidence/S21_aicas_wp_search_bansal.json`.
- **Result:** No returned Atul Bansal text match on the reviewed leadership page or the two official-site search queries.
- **Interpretation:** This is a defined-source absence check only. It does **not** disprove Apollo’s `Investor at aicas` record. It means the report has no direct official aicas confirmation of the position, remit, equity, or investment activity.

## 3. TiE Pittsburgh Angels SEC submissions index

- **Source:** https://data.sec.gov/submissions/CIK0001843925.json (report source [18]).
- **Result at retrieval:** The endpoint identifies TiE Pittsburgh Angels, LLC and returns its 2021 Form D in the `recent` filing index.
- **What this supports:** The SEC entity/filing record is current to the retrieval, alongside the underlying 2021 Form D already retained as source [7].
- **What it does not support:** A current fund, current assets under management, later activity outside that index, Atul’s present management role, or his personal investment amount.

## 4. Source reachability check

- The direct-source check recorded 17/18 successful lightweight HTTP fetches.
- Monta Vista source [16] rejected the lightweight fetch with HTTP 403, then loaded successfully in a normal browser session on 11 August 2026. This is an access-method difference, not a source failure.
- Retained files: `evidence/source_live_check_2026-08-11.json` and `evidence/Source_Live_Check_Addendum_2026-08-11.md`.

## Resulting decision boundary

The evidence still supports an initial founder/operator/advisor conversation. It does not justify calling Atul a current VC, fund partner, active investor, Innosential co-founder/chairman, aicas decision-maker, or a source of guaranteed introductions.
