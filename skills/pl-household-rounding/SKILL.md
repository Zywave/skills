---
name: pl-household-rounding
description: Surface cross-sell and rounding opportunities across an agency's existing personal lines clients by matching each client account to its household record in Zywave's household database and reading back total property value, number of properties, income and net-worth ranges, and out-of-state property — signals that a client with one policy probably needs a second home policy, an umbrella, or higher limits. Returns a ranked workbook of clients with the signal, the suggested conversation, and the matching library explainer. Read-only; no enrichment, no outreach, no CRM writes. Use this whenever a personal lines producer or account manager asks about rounding accounts, cross-selling home and auto, umbrella opportunities, monoline clients, "which of my PL clients should have an umbrella," second-home or vacation-property exposure, or wants to find revenue inside the existing PL book. For new households use pl-household-prospecting.
---

# Personal Lines Household Rounding

Find the revenue already sitting in the personal lines book.

Rounding — getting the second and third policy from a household that has one — is the highest-margin growth a personal lines agency has, and the hardest to systematize because the signal lives outside the agency's system. The AMS knows a client has a homeowners policy; it doesn't know they also own a lake place in another state, or that their property values crossed the line where an umbrella stops being optional. Zywave's household database knows both. This skill joins the book to that data and returns a list of conversations, each with the reason to have it.

## Workflow

1. Pull the personal lines book
2. Match each client to a household
3. Score the rounding signals
4. Pull the explainers
5. Present and hand off

---

## 1. Pull the personal lines book

`account_search` with `filter: "isArchived eq false and classification eq 'Personal'"`, `top: 100`, paged by `skip`. Narrow by `state` in memory if the producer asks for a territory — the `state eq` filter on `account_search` is unreliable, so pull the PL book and filter client-side. Keep only accounts whose `linesOfBusiness` includes a Personal Lines value that isn't "Prospect" — the skill is about clients.

Tell the producer the count before matching. A 3,000-household book is 3,000 lookups; say so and proceed unless told to narrow (by state, or by a producer's own accounts if the CRM carries that).

---

## 2. Match each client to a household

For each account, find its household:

1. If the account carries an `msid` starting with `H`, call `discovery_household_search` with `msids: ["H..."]` — direct lookup, one call.
2. Otherwise search by the account's `postalCode` (`zipCodes`) and match on the account's street against the household `street`, normalizing abbreviations (St/Street, Ave/Avenue, suite and unit stripped). Take a match only when street number and normalized street name both agree.
3. No match → record "no household match" and move on. Don't force a match on ZIP alone.

Batch ZIP searches: many clients share ZIPs, so one `zipCodes` search with paging serves several accounts. Report the match rate at the end; 60–80% is typical, and the unmatched are a data-quality finding worth showing.

---

## 3. Score the rounding signals

Read `references/rounding_signals.md`. For each matched client, compute and record the signals the household record supports:

| Signal | From | Suggested conversation |
|---|---|---|
| **Multiple properties** | `numberOfProperties` ≥ 2 | Second-home or rental dwelling coverage; is every property scheduled? |
| **Out-of-state property** | any property state ≠ primary state (visible when `numberOfProperties` ≥ 2 and the record's state differs from the account's) | Non-resident dwelling policy; check the carrier writes that state |
| **Umbrella threshold** | `totalPropertyValue` ≥ $750,000 or `netWorthRange.min` ≥ $1,000,000 | Personal umbrella if not already carried; the agency's own records say whether it is |
| **High-value home** | `totalPropertyValue` ≥ $1,500,000 with `numberOfProperties` = 1 | High-value homeowners market, guaranteed replacement cost, scheduled personal property |
| **Income step-up** | `incomeRange.min` ≥ $250,000 | Umbrella limit review; excess liability |

Score = count of signals, weighted (umbrella 2, out-of-state 2, others 1). Rank by score, then `totalPropertyValue`.

The skill can see property, income, and net worth. **It cannot see what the client already carries** — that's the AMS's job, not the CRM's. Every suggestion is therefore "worth a look," never "missing." The account manager confirms against the policy file.

---

## 4. Pull the explainers

`content_search` for two or three client-facing pieces: `personal umbrella insurance why you need it`, `insuring a second home or vacation property`, `high value home insurance coverage considerations`. Select on title, dedupe on `contentId`, `content_download` each with `convertToPdf: true`. These are the leave-behinds for the conversation; include the matching one per signal in the workbook's suggestion column.

---

## 5. Present and hand off

Write an .xlsx with tabs **Opportunities** (account, city, state, signals, score, total property value, properties, income range, net-worth range, suggested conversation, explainer title), **Unmatched** (accounts with no household match — a clean-up list), and **Method** (filters, match rule, thresholds, match rate). Present it with the explainer PDFs.

In chat, five lines: clients matched and the match rate; how many carry an umbrella-threshold signal; how many have out-of-state property; the top three by score; and the next step — the account manager calls, or `vertical-prospecting-campaign` with `lineOfBusiness: PersonalLines` for a rounding email to the top tier.

---

## Hard rules

- **Read-only.** No enrichment, no `discovery_household_contact_get` in bulk, no CRM writes, no email.
- Match on street + ZIP or MSID. Never on ZIP alone; a wrong household on a client's row is a privacy problem and a trust problem.
- Every suggestion is phrased as "worth reviewing," because the skill cannot see what's already carried.
- Income and net worth are vendor ranges. They stay as ranges and never appear in a client-facing document.
- The unmatched list is delivered, not hidden. It's where the CRM's address quality shows.
- Thresholds are stated in the Method tab so the producer can change them.
