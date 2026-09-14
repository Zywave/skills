---
name: territory-market-map
description: Build a market intelligence deliverable for a sales territory using Zywave discovery data — an Excel workbook and short memo sizing the commercial or benefits market by industry, employer size, renewal month, incumbent broker and carrier (where filing data exists), PEO/TPA/self-funded penetration, and compliance signals (OSHA, DOT, fidelity bond), with each segment marked as owned in the CRM or not. Runs from stated parameters (states, cities or a radius, line of business, optional industry focus) with no client files, no contact enrichment, and no outreach. Use this whenever someone asks to size, map, analyze, or understand a territory or market; asks "how many X are there in Y," "who are the big brokers in this market," "where should we focus," or wants a market study, whitespace analysis, territory plan, or prospect universe count; or asks a producer-planning or sales-leadership question about a geography. For outreach to a segment use vertical-prospecting-campaign; for a single account use prospect-prep.
---

# Territory Market Map

Turn a geography into a picture of the market: how big, made of what, who holds it, and where the agency already is.

The discovery search returns `totalCount` on every query, which means the shape of a market can be measured with **counts, not crawls**. A 50-state market map does not require downloading 50 states of companies; it requires a grid of well-chosen filtered queries and reading the totals. Pull detail pages only for the segments the producer will actually act on. That keeps the job fast, cheap, and honest — a count is a fact, a sample is an estimate, and the workbook labels which is which.

## Workflow

1. Define the territory and the cuts
2. Measure the market with count queries
3. Sample detail for the priority segments
4. Overlay the agency's own book
5. Build the workbook and memo
6. Report in chat

---

## 1. Define the territory and the cuts

| Input | `discovery_company_search` parameter | Default |
|---|---|---|
| Territory | `states` (list), or `city` + state, or `proximityLatitude/Longitude/RadiusMiles` | Ask if absent — the one thing you can't default |
| Line of business | `lineOfBusiness`: `Commercial` or `Benefits` | Commercial; offer to run both |
| Industry focus | `naicsCodes` — see `references/segment_grid.md` | The full 20-sector grid |
| Size floor | `employeeCountMin` | 10 (drops the long tail of micro-businesses) |
| Quality floor | `minQualityScore` | Leave default (51) |

Confirm in one message, then go. Don't ask what cuts they want — the grid is the answer; they can narrow after they see it.

---

## 2. Measure the market with count queries

Run `discovery_company_search` with `pageSize: 1` for each cell of the grid in `references/segment_grid.md` and record `totalCount`. Three grids:

- **Industry × size band** — 20 NAICS sectors × 4 employee bands (10–49, 50–99, 100–249, 250+). ~80 calls.
- **Renewal month** — 12 calls with `renewalMonths: [m]`, plus one baseline with no renewal filter so you can report what share has a known renewal month.
- **Signals** — one call each for `selfFunded: true`, `hasOshaViolations: true`, `hasDotViolations: true`, `fidelityBondOutOfCompliance: true`, `hasContactEmails: true`.

For Benefits, add **plan type** (`benefitsPlanTypes` Medical / Dental / Vision) and skip the DOT signal.

Save every query and its count to `/home/claude/market/counts.json` as `{filters..., totalCount}` rows as you go. Give the user a one-line progress note every ~25 calls. If a call errors, record `null` and move on; the workbook shows the gap.

Counts are facts about the discovery database at the quality floor you set. State the floor in the memo.

---

## 3. Sample detail for the priority segments

Pick the top segments — by default the five largest industry × size cells plus any cell the producer named. For each, page `discovery_company_search` with `pageSize: 25` to **100 companies** (4 pages) or the cell's total, whichever is smaller. Append the raw results to `/home/claude/market/companies.json`.

From the samples the script derives, per segment: revenue distribution, county/city concentration, quality score distribution, share with compliance flags, share with fidelity bond issues, and the **incumbent broker and carrier tally** from `leadCommercialBroker` / `leadBenefitsBroker` / carrier fields **where populated**. A null broker field means filing data isn't available — the tally is "of companies with broker data, X% show Broker Y," and the memo says how many had data. Never present nulls as "unrepresented" or as whitespace.

Do not call `discovery_company_contacts_get`. This deliverable never enriches or previews contacts.

---

## 4. Overlay the agency's own book

Pull the agency's non-archived accounts in the territory: `account_search` with `filter: "isArchived eq false and state eq 'XX'"` (one call per state, `top: 100`, page by `skip`). Save to `/home/claude/market/book.json`.

The script matches sampled companies to the book by `msid` first, then by normalized name + city. Matches are marked **Owned**. Unmatched are **Not in CRM**. For the count grid, owned share can only be estimated from the samples — the workbook labels it "sampled owned share."

`linesOfBusiness` on the account tells you client vs. prospect (`"P&C Prospect"`, `"Benefits Prospect"`). Show owned-as-client and owned-as-prospect separately.

---

## 5. Build the workbook and memo

```
python3 scripts/market_map.py \
  --counts /home/claude/market/counts.json \
  --companies /home/claude/market/companies.json \
  --book /home/claude/market/book.json \
  --territory "<label>" --lob Commercial \
  --out /mnt/user-data/outputs/Market-Map-<Territory>-<YYYY-MM-DD>.xlsx
```

Tabs: **Summary** (universe size, top segments, renewal curve, signal counts, owned share), **Industry x Size** (the count grid with a heat fill), **Renewal Months**, **Signals**, **Incumbents** (broker and carrier tallies with "n with data" columns), **Segment Detail** (sampled companies, owned flag, one row per company), **Book Overlay** (agency accounts in territory with match status), **Method** (every query run and its count, quality floor, sample sizes).

Then write `Market-Map-<Territory>.md`, one page:

```
# <Territory> — <LOB> Market Map
Prepared <date>. Source: Zywave discovery data (quality score ≥ N) and CRM accounts.

## Size
## Where the volume is (top 5 industry × size cells)
## Renewal curve (which months, share with known renewal)
## Who holds it (incumbent tallies, with n)
## Signals (self-funded / OSHA / DOT / bond)
## Where we already are (owned share, client vs prospect)
## Suggested focus (2–3 segments, each with the count, why, and what the next step would be)
## Method and caveats
```

Present both files.

---

## 6. Report in chat

Five lines: universe count at the quality floor; the largest segment; the renewal month with the most companies; the top incumbent with its `n`; owned share. Then offer the next step — a campaign into one segment (`vertical-prospecting-campaign`) or a deeper cut.

---

## Hard rules

- **Counts before crawls.** Never page through a whole territory to count it.
- **No contact preview, no enrichment, no outreach** from this skill. It is a study.
- Broker and carrier fields are filing-derived and often null. Always report `n with data`; never call a null "unrepresented" or "whitespace."
- Everything in the memo is either a count (fact) or from a labeled sample (estimate). Don't blur them.
- State the quality floor and size floor in every deliverable. Change either and every number moves.
- Segments the agency already owns are the first thing sales leadership will check. Get the overlay right before the prose.
