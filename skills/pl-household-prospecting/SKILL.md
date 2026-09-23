---
name: pl-household-prospecting
description: Build a personal lines prospect list of real households — not investors or property portfolios — in target states or ZIP codes and a total-property-value band, using Zywave's household database, with income and net-worth ranges, property counts, and a reachable-contact flag on every row, and the agency's personal lines book overlaid so existing clients drop out. Returns a ranked list, optionally as a workbook. No contact enrichment, no outreach. Use this whenever a personal lines producer asks for households, homeowners, high-value homes, new PL prospects, "who lives in these ZIPs," affluent households, umbrella or high-net-worth prospects, or wants to build a personal lines campaign list; or when someone asks what the household database can find. For cross-selling existing PL clients use pl-household-rounding; for outreach, hand the list to vertical-prospecting-campaign with the PersonalLines line of business.
---

# Personal Lines Household Prospecting

Find real households worth a personal lines conversation, and only real households.

Zywave's household database is the one asset in the catalog no agency management system has: tens of millions of owner records with property value, income, and net-worth ranges. It also has a trap. A "household" is an owner or group of co-owners and everything they own, and a search on property value alone returns portfolio entities first — a record with 29 properties and 14 owners is a real estate LLC, not a family. The skill's job is to filter those out before the producer sees them, because a PL producer who gets a list of investment trusts stops trusting the list.

## Workflow

1. Set the profile
2. Search, and filter to real households
3. Overlay the personal lines book
4. Present and hand off

---

## 1. Set the profile

| Input | `discovery_household_search` parameter | Default |
|---|---|---|
| Geography | `stateCodes` and/or `zipCodes` | Ask — the producer's territory can't be defaulted; ZIPs are better than states |
| Property value band | `totalPropertyValue: {min, max}` | $400,000 – $2,500,000 — **always set a max** |
| Reachability | `hasEmail: true` | always |
| Real-household filters (post-search) | `numberOfProperties ≤ 3`, `numberOfOwners ≤ 2` | always; say so |
| Optional | income or net-worth band as a post-filter | none |

**The max on property value is not optional.** Without it the top of the result set is portfolios worth hundreds of millions. Tell the producer the band you used and why.

One clarifying message at most. If the producer gives only a city, ask for ZIPs or take the state and narrow with a tighter value band.

---

## 2. Search, and filter to real households

`discovery_household_search` with the parameters. Read `totalCount` first; the universe for a value band in a state can be tens of thousands, so page with `pageSize: 25` to at most 200 records and tighten geography or the band beyond that.

> **Verified (Sep 2026) — two behaviors that shape the list:**
> 1. **Results come back sorted by `totalPropertyValue` descending, and there's no way to change it.** Two Wayzata ZIPs at $600K–$2M returned 1,410 households, and the first 25 were all between $1.94M and $2.0M. A 200-record cap on a wide band only ever shows the top of the band. For any band wider than about 2×, split it into slices (e.g. $600–900K, $900K–$1.3M, $1.3–2M) and take pages from each, so the producer sees the whole range and not just the ceiling.
> 2. **The ZIP filter matches any property the household owns; the record's `street`/`city`/`zipcode` is the primary residence.** In the same run, 4 of 18 kept households lived outside the target ZIPs — Mound, Chanhassen, and one in Scottsdale, AZ — and owned a property inside them. Those are second-home and seasonal-resident prospects, often the best ones. Keep them, and tag every row **resides in target** or **owns property in target, resides elsewhere** so the producer can see which conversation it is.

Post-filter every record:

- `numberOfProperties` > 3 → drop (investor or trust)
- `numberOfOwners` > 2 → drop (LLC, trust, or estate)
- `hasEmail` false → drop (should already be filtered)

Report the drop counts: "Searched 200, kept 143 real households; dropped 57 portfolios/entities." That line is what tells the producer the list is clean.

Household MSIDs start with `H`. Keep them; they are what the campaign tool needs.

---

## 3. Overlay the personal lines book

`account_search` with `filter: "isArchived eq false and classification eq 'Personal' and state eq 'XX'"`, paged.

> **Known platform defect (Sep 2026):** `account_search` returns `INTERNAL_ERROR` on `state eq` and `city eq` filters even though they are documented as filterable. `isArchived`, `classification`, `msid eq`, and `startswith(name,…)` work. So: try the state filter once; on error, pull the PL book (`filter: "isArchived eq false and classification eq 'Personal'"`, `top: 100`, page by `skip`, ~65 calls for 6,500 accounts) and filter on `state` in memory. Cache the pull for the rest of the run. For lists of 50 or fewer, `msid eq '<M…>'` per candidate is cheaper. Tell the user which path you took. Match on `msid` first, then normalized last name + street + ZIP (household records carry `street` and `zipcode`).

- **Existing PL client** → remove, count. (For those, use `pl-household-rounding` instead.)
- **PL Prospect in CRM** → keep, flag.
- **Not in book** → keep.

Name matching on households is looser than on companies — a household record may not carry a name until contacts are fetched. When `msid` doesn't match and address is unavailable, leave the row unmatched and say the overlay is address-based.

---

## 4. Present and hand off

Rank by `totalPropertyValue` descending within each slice, then `netWorthRange.max` descending. Table: MSID, city, state, ZIP (of residence), residence-vs-target tag, total property value, number of properties, income range, net-worth range, CRM status. **No street addresses in the chat table** — they're in the workbook if the producer asks for one, and only then.

For more than 25 rows, write an .xlsx with **Households** and **Method** tabs (filters, drop counts, band rationale) and present it.

In chat, four lines: universe count at the band, households kept after filtering, the largest three by value, and next steps — `vertical-prospecting-campaign` with `lineOfBusiness: PersonalLines` and the household MSIDs (it resolves the primary contact itself), or `discovery_household_contact_get` on a single household the producer names to see who lives there.

---

## Hard rules

- **No contact fetches, no enrichment, no outreach from this skill.** `discovery_household_contact_get` is called only for a household the producer names, and never in bulk.
- **Always set a property-value max and always apply the properties/owners filter.** A list with portfolios in it is a defect, not a bonus.
- Report drop counts so the cleaning is visible.
- Street addresses stay out of chat. They belong in a file the producer explicitly asks for.
- Income and net worth are ranges from a data vendor, not facts about a person. Present them as ranges and never as a statement about an individual.
- Existing PL clients come off the list.
- Wide value bands are sliced so the list isn't just the top of the range. Say which slices were used.
- Households that own property in the target area but live elsewhere are kept and tagged, never silently dropped or silently mixed in.
