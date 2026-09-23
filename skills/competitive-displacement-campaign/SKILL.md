---
name: competitive-displacement-campaign
description: Target the accounts held by a named competing broker or agency and run a multi-touch email sequence against them, using the incumbent-broker fields in Zywave market data (filing-derived, commercial or benefits) to build the list, then the sequence tools to draft, review, approve, and schedule, with hard confirmation gates before enrichment is metered and before any email is sent. Runs from stated parameters — competitor name, territory, size, line of business — with no files. Use this whenever a producer wants to go after a competitor's book, names a rival agency or broker as the target, asks "who does [competitor] write," wants a displacement or takeover campaign, or asks to build a list of accounts a specific broker holds. For timing-driven lists use renewal-xdate-prospect-list; for industry-driven campaigns use vertical-prospecting-campaign.
---

# Competitive Displacement Campaign

Find the accounts a named competitor holds, and sequence them.

The incumbent-broker field in Zywave market data comes from public filings. It is the only place a producer can see, at scale, which accounts a specific competitor writes. That makes this the sharpest targeting in the library and also the one most in need of restraint: the emails must never name the incumbent, never disparage them, and never claim knowledge the producer wouldn't say out loud. The data tells you *who* to call. The pitch is still about the prospect, not about the competitor.

This skill shares its chassis with `vertical-prospecting-campaign`. The differences are the filter, the pain-point framing, and one extra rule about what the drafts may say.

## Workflow

1. Confirm the target and the ICP
2. Build the list and verify the broker match
3. Present the shortlist; get a **go** to create
4. Create the campaign; wait for drafts
5. Review drafts for the naming rule; approve and edit
6. Schedule — only on an explicit send
7. Hand off

---

## 1. Confirm the target and the ICP

| Input | Parameter | Default |
|---|---|---|
| Competitor | `commercialBrokerName` (Commercial) or `benefitsBrokerName` (Benefits) | Ask — this is the skill |
| Line of business | `lineOfBusiness` | Commercial |
| Territory | `states`, `city`, or `proximity*` | Producer's state if known; else ask in the same message |
| Size | `employeeCountMin/Max` | 10–500 |
| Renewal window (optional) | `renewalMonths` | none; if given, set `useRenewalModel: true` |
| Reachability | `hasContactEmails: true` | always |

Broker names in filing data are inconsistent: "Marsh," "Marsh & McLennan," "Marsh McLennan Agency," and "MMA" may all appear. Ask the producer for the variants they know, and try each. Read `references/broker_name_matching.md` for the approach.

One message to confirm; defaults for touches (3), window (Morning), start (next business day), hooks (TIMELINE → NUMBERS → SOCIAL_PROOF).

---

## 2. Build the list and verify the broker match

Call `discovery_company_search` once per broker-name variant. Merge on `msid`. Read `totalCount` and page to at most 50 companies, ranked by `qualityScore` then revenue.

**Verify the match before showing anything.** Spot-check five records: does the returned broker field actually contain the competitor's name? If a variant returns unrelated brokers, drop it and say so. A displacement list that turns out to be someone else's book is worse than no list.

Drop `isOutOfBusiness: true`.

---

## 3. Present the shortlist; get a go

Table: company, city/state, employees, revenue, quality score, renewal month if present, and the incumbent broker **as the filing shows it**. The producer should see the name they targeted in every row.

Then, plainly:

> Creating the campaign will resolve and enrich one primary contact at each of these N companies (metered) and generate N × 3 drafts. Nothing is sent. Create it?

Wait for yes. Trim first if asked. Preview contacts (`discovery_company_contacts_get`, `enrich: false`) only for companies the producer names.

---

## 4. Create the campaign; wait for drafts

`sequence_campaign_create` with `prospects` as `[{"msid": "M..."}, ...]`, the line of business, name (include the competitor for the producer's own tracking, e.g. "Q4 displacement — MMA — WI contractors"), `numTouches`, `sendWindow`, `startDate`, `useRenewalModel`, `hookRotation`.

`painPointPool`: pain points about the **prospect's business** — renewal timing, market conditions in their class, service responsiveness, coverage review. Not about the competitor.

`sequenceExclusions`: **always include the competitor's name and its variants.** This is the mechanical enforcement of the naming rule. Also exclude "your current broker," "your agent," and "switching."

Poll `sequence_campaign_status` every 30 seconds until `needs_review`.

---

## 5. Review drafts for the naming rule

`sequence_drafts_list`, touch 1 first, then the rest. Read every draft with one question in mind: **does it name, imply, or disparage the incumbent?** Any draft that does is edited via `edits` in `sequence_drafts_approve` or left unapproved. Show the producer the full body of each draft and the `campaign_url`.

The right tone is the tone of a producer who happens to know the account renews in March and has something useful to say about the market. Not "we noticed you're with X."

Approve with the matching `approveMode`; apply wording changes through `edits`.

---

## 6. Schedule — only on an explicit send

`sequence_schedule` with `confirm: true` only after the producer answers a direct question about sending. "Looks good" approves drafts; it does not send. Ask: "Approved drafts are ready. Schedule the send starting [date], [window]?"

---

## 7. Hand off

Campaign name, ID, contact and touch counts, first send date, `campaign_url`. Offer the companies that didn't make the top 50 as a second wave.

---

## Hard rules

- **Two gates, always.** One before `sequence_campaign_create` (metered), one before `sequence_schedule` (email). An early "yes, do it all" does not cover the send.
- **The competitor is never named in an email.** Enforced twice: in `sequenceExclusions` at creation and by reading every draft before approval. This is a legal and reputational rule, not a style preference.
- Verify the broker match on a sample before presenting the list. A mis-matched variant produces a list of someone else's clients.
- Never call a null broker field "unrepresented." This skill filters on the field being populated, so nulls shouldn't appear; if one does, drop the record.
- Maximum 50 prospects per campaign.
- Never fabricate renewal months, headcount, or the reason a company might be unhappy with its broker.
