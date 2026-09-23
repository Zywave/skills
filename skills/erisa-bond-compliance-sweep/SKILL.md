---
name: erisa-bond-compliance-sweep
description: Find employers whose ERISA fidelity bond is out of compliance with the 10-percent-of-plan-assets requirement, using the Form 5500-derived bond data in Zywave market data, split into the agency's own benefits clients (a service obligation) and non-clients (a prospecting list), with the attorney-reviewed explainer on ERISA bonding requirements attached for the conversation. Returns a workbook or table with plan assets, bond value, bond ratio, shortfall, and CRM status per employer. No outreach, no enrichment. Use this whenever a benefits producer or account manager asks about fidelity bonds, ERISA bonds, bond compliance, the 10 percent rule, Form 5500 bond findings, DOL bond audits, or wants a compliance-based opener for benefits prospecting; or whenever someone asks "which of my clients have a bond problem." Pairs with vertical-prospecting-campaign for outreach.
---

# ERISA Fidelity Bond Compliance Sweep

Find the employers whose fidelity bond is too small, split them into yours and not-yours, and bring the piece that explains the rule.

ERISA requires every person who handles plan funds to be bonded for at least 10% of the funds handled, generally between $1,000 and $500,000. The bond value and plan assets are both on the Form 5500, which means the shortfall is a matter of public record. Zywave's market data computes the ratio; almost nobody else surfaces it. For a client, an undersized bond is a DOL finding waiting to happen and the agency's job to catch. For a non-client, it's the most concrete benefits opener there is: not "let me quote your plan" but "your bond is $30,000 short and here's the rule."

## Workflow

1. Set the scope
2. Pull the out-of-compliance universe
3. Split clients from prospects
4. Pull the explainer
5. Present, then hand off

---

## 1. Set the scope

| Input | Parameter | Default |
|---|---|---|
| Territory | `states`, `city`, or `proximity*` | Ask if absent; for a client-only sweep, skip geography and use the book instead |
| Size | `employeeCountMin/Max` | 20–1,000 |
| Mode | client sweep, prospect sweep, or both | Both |

`lineOfBusiness` is `Benefits`. Add `hasContactEmails: true` only for the prospect half.

> **Known platform defect (Sep 2026):** the `fidelityBondOutOfCompliance` filter is **ignored** by `discovery_company_search` — `true` and `false` return the same `totalCount` and the same records. Pass it anyway (so the skill starts working the day it's fixed), but **never trust the count it returns as the out-of-compliance universe**. Compliance is determined client-side from `fidelityBonds[].is_compliant` on each record. In a Wisconsin sample, roughly 1 in 8 records had a non-compliant bond; plan page budgets accordingly.

---

## 2. Pull the out-of-compliance universe

Because the server filter is ignored, this step is a **scan, not a lookup**. Run it in two modes:

**Client mode (always first, always tractable).** For each Benefits client in the book, resolve its market-data record — `discovery_company_search` with `companyName` and `states` (one call per client; `msid` match if the account carries one) — and read `fidelityBonds[]`. A 300-group book is 300 calls. Tell the user the count and proceed.

**Prospect mode (budgeted).** `discovery_company_search` with the scope, `pageSize: 25`, paging with `pageToken`. Set a page budget up front — 40 pages (~1,000 companies) is a reasonable default and yields roughly 100–150 non-compliant employers at the observed hit rate — and narrow geography (a metro radius) or raise the headcount floor rather than exceeding it. Say the budget and the hit rate in the deliverable's Method tab.

Each result carries `fidelityBonds[]` with `bond_value`, `plan_assets`, `bond_ratio`, and `is_compliant`. **Keep only records with at least one bond where `is_compliant` is `false`.** Records with an empty `fidelityBonds` array have no Form 5500 bond data and are neither compliant nor non-compliant — count them separately as "no bond data" and leave them out of both lists. Compute the shortfall for each non-compliant bond:

```
required = min(max(plan_assets * 0.10, 1000), 500000)
shortfall = max(required - bond_value, 0)
```

Show the arithmetic once in the deliverable so the reader can check it. The $500,000 cap rises to $1,000,000 for plans holding employer securities; if the record doesn't say, use $500,000 and note the assumption.

Drop `isOutOfBusiness: true`. Skip any record where `plan_assets` is null — you can't compute a shortfall from nothing, and guessing one is worse than omitting.

---

## 3. Split clients from prospects

Pull the agency's benefits accounts: `account_search` with `filter: "isArchived eq false and state eq 'XX'"` per state (or the whole book for a client-only sweep), `top: 100`, paged by `skip`. Match on `msid`, then normalized name + city.

> **Known platform defect (Sep 2026):** `account_search` returns `INTERNAL_ERROR` on `state eq` and `city eq` filters even though they are documented as filterable. `isArchived`, `classification`, `msid eq`, and `startswith(name,…)` work. So: try the state filter once; on error, pull the whole non-archived book (`filter: "isArchived eq false"`, `top: 100`, page by `skip`, ~65 calls for 6,500 accounts) and filter on `state` in memory. Cache the pull for the rest of the run. For lists of 50 or fewer, `msid eq '<M…>'` per candidate is cheaper. Tell the user which path you took.

Two lists:

- **Clients** — accounts whose `linesOfBusiness` includes a Benefits value that is not "Prospect." This is the service list. Lead with it; these are the agency's own exposure.
- **Not in book, or Benefits Prospect** — the prospecting list.

Sort each by shortfall descending. A $400,000 shortfall on a $5M plan is a different conversation than a $3,000 one.

---

## 4. Pull the explainer

`content_search` for `ERISA fidelity bond requirements plan sponsor` and select, by title, the compliance overview or bulletin on fidelity bonding. Dedupe on `contentId`; select on title, not score. Call `content_download` with `convertToPdf: true` and include it with the deliverable. If the library has a client-facing piece and an internal one, take the client-facing one for the prospect list and both for the client list.

Don't paraphrase the rule from memory in the deliverable. Quote the explainer's framing, or point to it.

---

## 5. Present, then hand off

For more than 25 employers, write an .xlsx with tabs **Clients**, **Prospects**, and **Method** (query, counts, formula, assumptions), one row per employer: name, city, state, employees, plan assets, bond value, bond ratio, required bond, shortfall, CRM status, MSID. Present it with the explainer PDF. For 25 or fewer, a table in chat is enough.

In chat, five lines: how many clients are exposed and the largest shortfall; how many prospects and the largest; the one-line rule; the explainer title; next steps.

Next steps, one line each: for clients, the account manager reaches out — this is service, not sales, and it shouldn't wait for a campaign. For prospects, `vertical-prospecting-campaign` with the ERISA bond content as the lead pain point, or `prospect-prep` on any single name.

---

## Hard rules

- **No outreach, no enrichment, no CRM writes.** This is a list and an explainer.
- Clients come first in every deliverable. An agency that emails prospects about bond shortfalls while its own clients have the same problem has its priorities inverted.
- Show the shortfall formula and the $500,000 cap assumption in the deliverable. Never present a number the reader can't reproduce.
- Skip records with null plan assets rather than estimating. Records with no bond data at all are reported as a count, not as findings.
- The universe count in the deliverable is the number of records **scanned**, and the finding count is the number with a non-compliant bond. Never present the server's `totalCount` as either.
- The rule text comes from the library piece, not from memory. If the library has nothing, say so and give only the numbers.
- This is not legal advice; one line in the workbook's Method tab says so.
