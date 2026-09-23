---
name: peo-graduation-prospects
description: Find employers on a Professional Employer Organization (PEO) that have grown large enough to consider leaving it, using the PEO field in Zywave market data (Form 5500-derived) filtered by headcount and territory, with the agency's book overlaid and the attorney-reviewed PEO-versus-direct-benefits explainer attached. Returns a ranked list with PEO name, headcount, revenue, renewal month where present, and CRM status. No outreach, no enrichment. Use this whenever a benefits producer asks about PEO clients, PEO exits, companies on a PEO, "who's on TriNet or Justworks in my area," graduating off a PEO, co-employment, or wants a list of mid-size employers whose benefits are still bundled with payroll; or when someone asks how to prospect against PEOs. For outreach use vertical-prospecting-campaign with this list.
---

# PEO Graduation Prospects

Find the companies that have outgrown their PEO and don't know it yet.

A PEO makes sense at fifteen employees. At seventy-five, the per-employee administrative fee has grown into a number that would fund a benefits broker, an HR platform, and a better plan. Every benefits producer knows these accounts exist; none of them can find them, because "on a PEO" doesn't show up in any list they can buy. It shows up in Form 5500 filings, and Zywave's market data carries it as a field. This skill turns that field into a prospecting list and brings the piece that explains the trade-off, so the producer opens with math rather than a pitch.

## Workflow

1. Set the scope
2. Pull PEO-sponsored employers
3. Overlay the book
4. Pull the explainer
5. Present and hand off

---

## 1. Set the scope

| Input | Parameter | Default |
|---|---|---|
| Territory | `states`, `city`, or `proximity*` | Ask if absent |
| Headcount floor | `employeeCountMin` | 50 — below this the PEO is usually still the right answer |
| Headcount ceiling | `employeeCountMax` | 500 |
| Specific PEO (optional) | `peoName` — a name filters to that PEO; omit to get all | all PEOs |
| Vertical (optional) | `naicsCodes` | none |
| Reachability | `hasContactEmails: true` | always |

`lineOfBusiness` is `Benefits`. If the producer names a PEO, treat the name like a competitor name: filings spell it several ways (TriNet / TriNet Group / TriNet HR; Justworks; Insperity / Administaff; ADP TotalSource; Paychex PEO; Vensure). Search each variant and merge on `msid`.

> **Verified (Sep 2026):** the `peoName` filter works — a PEO name narrows Wisconsin benefits employers from ~4,800 to a handful. But **the returned record does not carry a PEO field**, so there is nothing to spot-check on the record. The PEO column in the output is the name the query used, not a value read back. Run one query per PEO variant and tag rows by which query returned them. Omitting `peoName` does not filter to "any PEO" — always name at least one.

One clarifying message at most.

---

## 2. Pull PEO-sponsored employers

`discovery_company_search` with the scope. Read `totalCount`; page with `pageSize: 25` up to 200 records. Above that, raise the headcount floor or narrow geography — the best targets are the largest ones anyway.

Drop `isOutOfBusiness: true`. Keep the PEO name from each record; it's the most useful column in the output.

---

## 3. Overlay the book

`account_search` with `filter: "isArchived eq false and state eq 'XX'"` per state, paged. Match on `msid`, then normalized name + city.

> **Known platform defect (Sep 2026):** `account_search` returns `INTERNAL_ERROR` on `state eq` and `city eq` filters even though they are documented as filterable. `isArchived`, `classification`, `msid eq`, and `startswith(name,…)` work. So: try the state filter once; on error, pull the whole non-archived book (`filter: "isArchived eq false"`, `top: 100`, page by `skip`, ~65 calls for 6,500 accounts) and filter on `state` in memory. Cache the pull for the rest of the run. For lists of 50 or fewer, `msid eq '<M…>'` per candidate is cheaper. Tell the user which path you took.

- **Existing Benefits client** → remove from the list and count it. If the agency already has the benefits, the PEO conversation is a service conversation, not a prospecting one; note it separately for the account manager.
- **Benefits Prospect in CRM** → keep, flag.
- **Not in book** → keep.

---

## 4. Pull the explainer

`content_search` for `PEO professional employer organization employers` (the shorter query is the one that returns the library's piece; verified Sep 2026: "Professional Employer Organizations", an advantages-and-disadvantages article). Select by title, dedupe on `contentId`, `content_download` with `convertToPdf: true` — the item carries no `fileDownloadUrl`. If `content_search` returns `INTERNAL_ERROR`, wait a minute and retry once before giving up; the service has brief outages.

If the library has a piece on **exiting a PEO** (timing, notice periods, what transfers), take that too. Leaving a PEO mid-year is disruptive; the explainer that says so is the one that builds trust.

---

## 5. Present and hand off

Table: company, city, state, PEO (from the query), revenue range, benefits broker on file **as the filing shows it**, quality score, CRM status, MSID. **The response carries no employee count**, so sort by `revenueRange.max` descending and say so — revenue is the available proxy for the PEO fee. Show the benefits-broker column deliberately: a company on a PEO normally has the PEO as plan sponsor, so a populated broker means either a stale filing or a partial arrangement, and the producer should see that tension rather than assume. Below the table: counts of removed clients and flagged prospects.

For more than 25 rows, write an .xlsx with **Prospects** and **Method** tabs and present it with the explainer PDF.

In chat, four lines: universe size, the largest three targets by revenue, the explainer title, and the next step — `vertical-prospecting-campaign` with the PEO comparison as the lead pain point and the PEO's name in `sequenceExclusions` (the email should be about the prospect's headcount, not about their vendor), or `prospect-prep` on any single name.

---

## Hard rules

- **No outreach, no enrichment, no CRM writes.** List plus explainer.
- The PEO column is the query's `peoName`, tagged per row. Never present a list built without a `peoName` filter as a PEO list.
- Existing Benefits clients come off the list and get counted, not emailed.
- The comparison comes from the library piece, not from memory. Fee percentages and plan-design claims in the deliverable are the explainer's, cited, or absent.
- Never state that a specific company is overpaying its PEO. State the headcount and let the explainer make the general case.
