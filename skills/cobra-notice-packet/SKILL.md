---
name: cobra-notice-packet
description: Assemble the correct COBRA notice packet for a specific event — coverage start (General Notice), qualifying event (Election Notice plus employer-to-administrator notice), or an unavailability or early-termination situation — from the DOL model notices and compliance guides in Zywave's content library, with a deadline timeline computed from the event date and a list of every blank the plan administrator must fill. Runs from stated parameters (employer, event type, event date, who administers the plan) with no client documents. Use this whenever someone asks for COBRA notices, a COBRA election notice, a COBRA general or initial notice, "what do we send when someone terminates," COBRA deadlines for a specific employee, a notice of unavailability, or mentions a qualifying event, continuation coverage, or a qualified beneficiary — even if they don't say "packet." For annual health plan notices use eb-annual-notice-packet.
---

# COBRA Notice Packet

Assemble the right COBRA notices for an event, from Zywave's library, with a deadline timeline the client can act on.

COBRA is deadline law. The notices are standardized (the DOL publishes model forms); what employers get wrong is **which notice, to whom, by when**. So this skill's output is organized around the timeline, and the model notices are attachments to it. An election notice sent on day 50 when it was due on day 44 is a violation even if every word of it is perfect.

## Workflow

1. Identify the event and the parties
2. Select the notice set
3. Pull the model notices and the governing guide
4. Compute the timeline from the library's rules
5. Download, bundle, write the memo
6. Report in chat

---

## 1. Identify the event and the parties

| Parameter | Why it matters | If missing |
|---|---|---|
| Event type | Determines the notice set (see step 2) | Ask — this is the fork in the road |
| Event date | Anchors every deadline | Ask if the event is a qualifying event; for a General Notice, use coverage start date |
| Who is the plan administrator | Employer-as-administrator has a combined 44-day window; separate TPA splits it 30 + 14 (verify) | Assume employer administers; flag |
| Employer headcount | Federal COBRA applies at 20+ employees; below that, state continuation ("mini-COBRA") may apply | Assume 20+; flag if unknown |
| Plan(s) affected | Each group health plan covered (medical, dental, vision, HRA, health FSA nuances) | List medical only; flag |
| Qualified beneficiaries | Employee, spouse, dependents — each has independent election rights | Assume employee only; flag |
| State | State continuation rules can extend or supplement | Take from account record if a client name is given |

If a client account name is given, call `account_search` (`filter: "startswith(name,'<Name>')"`) to pick up `state` and `clientSize`. `clientSize` of `From0To25` should trigger the small-employer flag.

One clarifying message at most. Default and flag everything else.

---

## 2. Select the notice set

Read `references/notice_sets.md` for the full mapping. Summary:

| Event | Packet contents |
|---|---|
| **Coverage start** (new enrollee, new spouse) | DOL Model General Notice; guide on initial notice timing |
| **Qualifying event** (termination, hours reduction, death, divorce, Medicare entitlement, loss of dependent status) | Employer/QB notice to plan administrator; DOL Model Election Notice; premium and payment terms; guide on election-notice timing |
| **Second qualifying event / disability extension** | QB notice to administrator form; guidance on 18→29 or 18→36 month extension |
| **Notice of unavailability** (someone requested COBRA but isn't entitled) | Unavailability notice guidance and model language |
| **Early termination of COBRA** (nonpayment, plan ends, other coverage) | Early termination notice guidance |
| **Full administration reference** (client wants the whole thing) | Compliance Toolkit; Employer's Guide to COBRA Administration; notification-requirements Q&A |

Always add the notification-requirements Q&A and the compliance chart to any packet: they are what the client will read when a question comes up later.

---

## 3. Pull the model notices and the governing guide

For each item, call `content_search` with the query from `references/notice_sets.md`. Then:

- **Dedupe on `contentId`** — the library repeats rows for the same item.
- **Select on title, not score.** The DOL model notices have distinctive titles ("DOL Model COBRA Continuation Coverage Election Notice", "... General Notice"). Match the title; do not take the top-scored row.
- **Pull the deliverable and the explainer separately.** The model notice goes in the packet; the toolkit or compliance overview backs the timeline.
- Content IDs in the reference are hints to confirm a match. Titles are the durable key; IDs are Zywave-assigned and can move.
- If an item is not found after one reformulation, mark it **"not in library"** in the memo and continue.

---

## 4. Compute the timeline from the library's rules

Call `content_get_full_text` on the Employer's Guide to COBRA Administration (or the Compliance Toolkit) **before writing any deadline**. Read the notice-timing section and the election/payment section. Then compute dates from the event date using the rules as the library states them.

The rules you are expected to find and verify (do not state them from memory):

- Employer's deadline to notify the plan administrator of a qualifying event
- Administrator's deadline to send the election notice, and the combined window when the employer is the administrator
- Qualified beneficiary's election period and what date it runs from
- Initial premium payment grace period and the ongoing monthly grace period
- General notice deadline from coverage start
- Maximum coverage periods by event type (18 / 29 / 36 months)

If the library text gives a rule, use it and cite the item. If it doesn't, write "verify — not stated in retrieved library text" in the memo rather than filling it in. The timeline table must never contain a date you cannot trace to a retrieved source.

Compute calendar dates with Python (`datetime`), not by hand. Show both the rule and the computed date.

---

## 5. Download, bundle, write the memo

**Downloads.** For each selected item call `content_download` with `convertToPdf: true` and fetch from the presigned URL into `/home/claude/cobra-packet/`. Name files `NN - <Item title>.pdf`. Do not rely on `fileDownloadUrl` from search results. If a download fails, note it and continue.

**Memo.** Write `00 - COBRA Notice Memo.md`:

```
# <Employer> — COBRA Notices: <Event type>, <Event date>
Prepared <date>. Source: Zywave attorney-reviewed content library.

## Timeline
| Step | Rule (as stated in <library item>) | Computed date | Owner |

## Notices in this packet
| # | Notice | Send to | Send by | File |

## Blanks to complete before sending
(per model notice: plan name, administrator name/address/phone, premium amount, payment address, coverage period end date, etc. — list only; fill only values the user gave you)

## Flags
(small-employer / state continuation, TPA vs employer administrator, plans not addressed, beneficiaries not addressed)

## Sources
(library titles used for each rule)
```

**Bundle.** Zip the folder as `<Employer>-COBRA-<EventType>-<YYYY-MM-DD>.zip`. Copy the zip and the memo to `/mnt/user-data/outputs/` and present them.

---

## 6. Report in chat

Lead with the next deadline and how many days away it is. Then the flags. Then anything not found. Four to six lines.

---

## Hard rules

- Never state a COBRA deadline you did not read in library text during this session. "Verify" is a valid entry; a guessed date is not.
- Never fill a model notice blank with invented data. List the blank; fill only what the user supplied.
- Never assert federal COBRA applies to an employer with fewer than 20 employees. Flag state continuation instead and search the library for the state's rule (`<State> continuation coverage mini-COBRA`).
- Never tell a client whether a specific individual is or isn't a qualified beneficiary or whether a specific event qualifies. Describe the rule from the library and mark the determination as the plan's.
- This is not legal advice; one sentence in the memo footer says so.
