---
name: vertical-prospecting-campaign
description: Run a complete new-business prospecting motion for one industry vertical with Zywave MCP tools — turn a plain-language ideal customer profile (industry, geography, size, line of business, optional renewal window or compliance signals) into a discovery list, a reviewed shortlist, a multi-touch email sequence with AI drafts, an approval pass, and a scheduled send, with hard confirmation gates before contact enrichment and before anything is sent. Runs from stated parameters only. Use this whenever a producer wants to prospect, target, go after, or build a campaign or sequence for an industry, class of business, or vertical ("go after contractors in Wisconsin," "build me a trucking campaign," "sequence dental practices renewing in Q1"); asks to find prospects and email them; or names a NAICS code, renewal month, self-funded plans, or OSHA/DOT flags as targeting criteria. For a single named account use prospect-prep; for market sizing with no outreach use territory-market-map.
---

# Vertical Prospecting Campaign

Take a producer from "I want to go after X" to a scheduled sequence, in one motion, with the producer in control at the two points that cost money or send email.

The sequence tooling already exists and is complete. What this skill adds is judgment in three places: turning a vertical into the right discovery filters, making the shortlist small and defensible before anything is metered, and never letting a campaign go out without the producer's explicit word. A producer who wakes up to 50 emails they didn't approve is a producer who never uses this again.

## Workflow

1. Confirm the ICP in one message
2. Build the discovery list
3. Present the shortlist and get a **go** to create the campaign
4. Create the campaign and wait for drafts
5. Review drafts with the producer; approve and edit
6. Schedule — only on an explicit send instruction
7. Hand off with the campaign link

---

## 1. Confirm the ICP in one message

Translate the ask into `discovery_company_search` parameters. Read `references/vertical_naics.md` to map the vertical to NAICS codes.

| ICP element | Parameter | Default if unstated |
|---|---|---|
| Vertical | `naicsCodes` (prefixes are fine: `"238"` matches all specialty trades) | Ask — this is the one thing you can't default |
| Line of business | `lineOfBusiness`: `Commercial` or `Benefits` | Commercial |
| Geography | `states`, or `city`, or `proximityLatitude/Longitude/RadiusMiles` | Producer's state if known from context; else ask in the same message |
| Size | `employeeCountMin/Max`, `revenueMin/Max` | 10–250 employees |
| Renewal timing | `renewalMonths` (1–12) | none |
| Benefits signals | `selfFunded`, `benefitsPlanTypes`, `benefitsCarrierName`, `tpaName`, `peoName` | none |
| P&C signals | `policyTypes`, `hasOshaViolations`, `hasDotViolations`, `driverMin`, `vehicleMin`, `fidelityBondOutOfCompliance` | none |
| Reachability | `hasContactEmails: true` | always true — a prospect with no email can't be sequenced |
| Data quality | `minQualityScore` | leave the default (51) |

Send one message: "Here's how I'll target this — [table]. Campaign name, touches, send window, and start date I'll set to [defaults] unless you say otherwise. Go?" Defaults: 3 touches, Morning window, start next business day, hook rotation TIMELINE → NUMBERS → SOCIAL_PROOF. Proceed on a yes. Don't ask a second round of questions.

---

## 2. Build the discovery list

Call `discovery_company_search` with the ICP. Note `totalCount` on the first response — it tells you the size of the universe before you page. Page with `pageToken` (`pageSize: 25`) until you have **up to 50 companies** or run out.

If `totalCount` is over ~200, tell the producer and tighten (narrower NAICS, smaller size band, a renewal window) rather than taking the first 50 arbitrarily. If it's under 10, loosen one constraint and say which. The shortlist should be the *best* 50, not the *first* 50.

Rank within the pull: quality score descending, then renewal month proximity if a window was given, then revenue. Drop `isOutOfBusiness: true`.

Do **not** call `discovery_company_contacts_get` at this step. Contact preview isn't needed to build the shortlist, and `sequence_campaign_create` resolves each company's primary contact from the MSID on its own.

---

## 3. Present the shortlist and get a go

Show a table: company, city/state, revenue range, quality score, renewal month (if returned), compliance flags (if any), incumbent broker **only if the field is populated** — a null broker field means the data is unavailable, never "unrepresented." Say so under the table.

Then state plainly what happens next and what it costs:

> Creating the campaign will resolve and enrich a primary contact at each of these N companies (metered) and generate N × touches email drafts. Nothing is sent at this step. Create it?

Wait for a yes. If the producer wants to drop or add companies, do that first. If they want to see who the contact would be at a few key targets, call `discovery_company_contacts_get` with `enrich: false` for **those** companies only and show names and titles; do not enrich.

---

## 4. Create the campaign and wait for drafts

Call `sequence_campaign_create`:

- `prospects`: JSON string, `[{"msid":"M..."}, ...]` — omit `contact_id` to let the system pick the primary contact, or include it if the producer chose a specific person from a preview
- `lineOfBusiness`, `name`, `numTouches`, `sendWindow`, `startDate` (YYYY-MM-DD), `useRenewalModel` (true if the ICP used `renewalMonths`, else false)
- `hookRotation`, `painPointPool` (three to five vertical-specific pain points from the reference), `sequenceExclusions` (anything the producer said not to mention)

Capture `campaign_id`. Poll `sequence_campaign_status` every 30 seconds until `status` is `needs_review`. Tell the producer roughly how long (a few minutes) and give one progress line per minute, not per poll.

---

## 5. Review drafts

Call `sequence_drafts_list` with `touchNumber: 1` first — the cold open is the one that matters most. Show each draft's **full body** (never truncate) with its `draft_id`, and always show `campaign_url`.

Ask the producer how they want to review: all at once, by touch, or by company. Then approve with `sequence_drafts_approve` using the matching `approveMode` (`all`, `by_touch`, `by_draft_ids`, `by_company`). Apply wording changes through `edits` (`[{"draft_id":123,"field":"subject","value":"..."}]`) in the same call rather than asking them to edit in the UI.

If the producer rejects the whole tone, don't try to rewrite 150 drafts by hand. Suggest adjusting `painPointPool` / `sequenceExclusions` and creating a fresh campaign; the old one can sit unscheduled.

---

## 6. Schedule — only on an explicit send

`sequence_schedule` with `confirm: true` is called **only** after the producer says send, schedule it, go, or an unambiguous equivalent *in response to a question about sending*. "Looks good" is approval of drafts, not an instruction to send. Ask: "Approved drafts are ready. Schedule the send starting [date], [window]?" and wait.

Only approved drafts go out. If some are still pending, say how many and confirm they want to send without them.

---

## 7. Hand off

Three lines: campaign name and ID, how many contacts and touches are scheduled and the first send date, and the `campaign_url`. Offer to build a follow-up list from companies that didn't make the shortlist.

---

## Hard rules

- **Two gates, always**: one yes before `sequence_campaign_create` (metered enrichment), one yes before `sequence_schedule` (email leaves the building). A single early "yes, do it all" does not cover both; ask again at the send.
- Never enrich contacts broadly. Preview (`enrich: false`) only for companies the producer names; enrichment happens inside campaign creation for shortlisted companies only.
- Never describe a company as unrepresented or "without a broker" from a null broker field.
- Maximum 50 prospects per campaign. Split into two campaigns if the producer insists on more, each with its own gates.
- Never fabricate renewal months, headcount, or incumbent carriers. Show what discovery returned; leave blanks blank.
- This skill sends email on the producer's behalf. Every message the producer approves is theirs; make it easy to read them in full.
