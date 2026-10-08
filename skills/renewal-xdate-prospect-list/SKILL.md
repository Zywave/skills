---
name: renewal-xdate-prospect-list
description: Build a list of companies in a territory whose policies renew in a chosen window (next 60, 90, or 120 days, or named months) and that are not already in the agency's book, using Zywave market data's renewal-month field and a CRM overlay. Returns a ranked prospect list with renewal month, size, revenue, quality score, and incumbent broker where filing data exists, plus a count of how many are already clients or prospects in the CRM. No outreach, no enrichment. Use this whenever a producer asks for X-dates, renewal dates, "who renews in Q1," "what's coming up for renewal in my territory," a renewal calendar for prospecting, or wants to time outreach to a renewal window; or when someone asks what the pipeline looks like for a given month. For outreach to the list use vertical-prospecting-campaign; for a named competitor's renewals use competitive-displacement-campaign.
---

# Renewal X-Date Prospect List

Find the companies in a territory that renew soon and aren't yours yet.

X-dates are the currency of P&C prospecting. A producer who calls 90 days before renewal is in the conversation; one who calls after is a year late. Zywave's market data carries renewal months on a scale no producer can assemble by hand, and this skill turns that into a list they can work this week. It stops at the list. Sending is a different skill and a different decision.

## Workflow

1. Set the window and the territory
2. Pull the renewal universe
3. Remove what's already in the book
4. Rank and present
5. Hand off

---

## 1. Set the window and the territory

| Input | `discovery_company_search` parameter | Default |
|---|---|---|
| Renewal window | `renewalMonths` (1–12) | Next 90 days → the next three calendar months from today |
| Territory | `states`, or `city` + state, or `proximityLatitude/Longitude/RadiusMiles` | Ask — this can't be defaulted |
| Line of business | `lineOfBusiness`: `Commercial` or `Benefits` | Commercial |
| Size | `employeeCountMin/Max` | 10–500 |
| Vertical (optional) | `naicsCodes` | none — this skill is timing-first, not vertical-first |
| Reachability | `hasContactEmails: true` | always, so the list is workable |

Convert the window to month numbers explicitly and show them: "Next 90 days from Sep 21 → renewalMonths [10, 11, 12]." A window that straddles year-end wraps: December through February is `[12, 1, 2]`.

One clarifying message at most. Default and state everything else.

---

## 2. Pull the renewal universe

Call `discovery_company_search` **once per month in the window**, not once with all months. The response carries no per-record renewal month, so a combined query can't be ranked soonest-first; per-month queries give every row its month and keep each `totalCount` smaller. Read each `totalCount` and tell the producer the size of the universe before paging.

> **Benefits is January-heavy.** For `lineOfBusiness: Benefits`, the renewal month is effectively the Form 5500 plan-year start, and most plans run on the calendar year. In a WI + IL, 50–500 lives sample, Q1 broke down January 1,613, February 38, March 68. Expect this. Say it to the producer before they ask why the list is lopsided. Tighten **January** by state, size band, or vertical rather than truncating it, and present February and March as the small, less-contested set — those off-cycle groups get far fewer calls. Commercial renewals are spread across the year and don't need this treatment.

- Under 25: loosen one constraint (widen the size band or add a month) and say so.
- 25–300: page it all (`pageSize: 25`, `pageToken`).
- Over 300: tighten — narrower geography or a single month — or ask the producer to pick a vertical. Don't truncate silently.

Drop `isOutOfBusiness: true`. Keep everything else.

---

## 3. Remove what's already in the book

Pull the agency's accounts in the territory: `account_search` with `filter: "isArchived eq false and state eq 'XX'"`, `top: 100`, paging by `skip`. One call per state.

> **Note:** `account_search`'s `state eq` and `city eq` filters are unreliable and can return `INTERNAL_ERROR` even though they're documented as filterable. `isArchived`, `classification`, `msid eq`, and `startswith(name,…)` work reliably. So: try the state filter once; on error, pull the whole non-archived book (`filter: "isArchived eq false"`, `top: 100`, page by `skip`, ~65 calls for 6,500 accounts) and filter on `state` in memory. Cache the pull for the rest of the run. For lists of 50 or fewer, `msid eq '<M…>'` per candidate is cheaper. Tell the user which path you took.

Match discovery results to accounts on `msid` first, then on normalized name + city (strip punctuation, suffixes like Inc/LLC, and spaces; compare lowercase). Mark each discovery record:

- **In book — client**: account exists and `linesOfBusiness` has a non-Prospect value → exclude from the list, count it
- **In book — prospect**: account exists, all `linesOfBusiness` values contain "Prospect" → keep, flag "already a prospect in CRM"
- **Not in book**: keep

A renewal-window list that includes existing clients wastes the producer's morning and looks careless. The exclusion is the whole point of the overlay.

---

## 4. Rank and present

Rank: renewal month ascending (soonest first), then `qualityScore` descending, then revenue descending.

Show a table: company, city, state, renewal month, employees (if present), revenue range, quality score, incumbent broker **only where the field is populated**, and CRM status. Below the table, one line: "N companies renew in [window]; M already clients (removed); K already prospects in CRM (kept, flagged)."

A null broker field means filing data isn't available. Say "not available." Never "unrepresented."

If the producer wants the list as a file, write it as an .xlsx with the same columns plus MSID, and present it. Otherwise the table in chat is the deliverable.

---

## 5. Hand off

Three lines: how many are ready to work this month, how many the month after, and the two next steps — `vertical-prospecting-campaign` to sequence a slice of this list (pass the MSIDs), or `prospect-prep` on any single name. Offer to save the list to CRM as prospects via `prospect-to-account-conversion` if they want to track them.

---

## Hard rules

- **No outreach, no enrichment, no CRM writes from this skill.** It produces a list.
- Existing clients are removed from the list, and the count is shown. A list that includes your own clients is a defect.
- Never describe a company as unrepresented from a null broker field.
- Never invent a renewal month. The month on each row is the single `renewalMonths` value of the query that returned it — which is why the skill queries month by month. A company returned by more than one month's query renews in each; list it once with all months.
- State the window as month numbers and dates so the producer can see the arithmetic.
