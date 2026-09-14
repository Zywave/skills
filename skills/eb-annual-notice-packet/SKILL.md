---
name: eb-annual-notice-packet
description: Assemble an employer's annual group health plan notice packet from Zywave's attorney-reviewed content library — Medicare Part D creditable coverage, CHIP, WHCRA, Newborns' Act, HIPAA privacy, wellness, grandfathered plan, patient protections, SBC and Summary Annual Report — as downloaded model notices plus a distribution memo listing who gets each notice, when it is due, how it may be delivered, and which blanks the plan administrator must fill. Runs from stated parameters (client name, plan year, states, headcount, funding, Rx coverage) with no client documents. Use this whenever someone asks for annual notices, open enrollment notices, required employee notices, a Part D notice, a CHIP notice, "what notices does my client owe this year," an OE compliance packet, or wants to know which benefits notices are due and when — even if they only name one notice. For COBRA event notices use cobra-notice-packet.
---

# EB Annual Notice Packet

Assemble the notices a group health plan sponsor must distribute each year, pulled from the Zywave content library, with a distribution memo that tells the client exactly what to do with each one.

The value of this packet is that it is **complete and correctly timed**. An employer who misses the Part D notice before October 15 or omits the CHIP notice has a compliance exposure regardless of how good the other notices look. Completeness beats polish: include every notice that could apply and mark the conditional ones "confirm applies" rather than silently dropping them.

## Workflow

1. Collect parameters
2. Resolve the notice list
3. Pull each item from the library
4. Verify timing against the library's own text
5. Download, bundle, and write the memo
6. Report gaps in chat

---

## 1. Collect parameters

Everything runs from stated parameters. If a client account name is given, call `account_search` (`filter: "name eq '<Name>'"` or `startswith(name,'<Name>')`) and take `state`, `clientSize`, and `classification` from the record. Otherwise take them from the request.

| Parameter | Why it matters | If missing |
|---|---|---|
| Plan year start / open enrollment date | Anchors every deadline | Ask; this is the one you cannot default |
| State(s) where employees live | CHIP notice applies only in states with premium assistance | Use employer's state; flag multi-state |
| Headcount | Some notices scale with size (e.g. 5500/SAR threshold at 100 participants) | Assume ≥100; flag |
| Funding (fully insured / self-funded) | Self-funded plans owe HIPAA privacy notice directly; insured plans may rely on carrier | Assume fully insured; flag |
| Prescription drug coverage in the plan | Part D creditable coverage notice applies only if Rx is covered | Assume yes |
| Grandfathered status | Grandfathered plan notice applies only if grandfathered | Assume not grandfathered |
| Wellness program with HRA or biometric screening | Wellness notice applies only then | Assume none |
| Plan requires PCP designation (HMO-style) | Patient protections notice applies only then | Assume no |
| Files Form 5500 | SAR owed only if 5500 is filed | Infer from headcount; flag |

Do not stall on missing parameters. Take the default, mark the notice **conditional**, and move on. One clarifying message at most.

---

## 2. Resolve the notice list

Read `references/notice_catalog.md`. It lists each notice, the trigger, the audience, the timing rule, and the `content_search` query that reliably surfaces it. Build the packet list from it:

- **Always include**: Medicare Part D creditable coverage notice, CHIP notice, WHCRA annual notice, Newborns' and Mothers' Health Protection Act notice, HIPAA notice of privacy practices (or 3-year reminder), HIPAA special enrollment rights notice, Summary of Benefits and Coverage reminder.
- **Include if condition met**: Wellness program notice, grandfathered plan notice, patient protections notice, Summary Annual Report, Michelle's Law notice, Mental Health Parity disclosure notice.
- **Not annual — mention in the memo as "at hire" so the client doesn't think they were forgotten**: Marketplace (Exchange) notice, COBRA general notice, SPD.

The catalog is a starting point, not an authority. The authority is the library text you retrieve in step 4.

---

## 3. Pull each item from the library

For each notice, call `content_search` with the query from the catalog. Then apply these selection rules, which exist because the library returns noisy results:

- **Dedupe on `contentId`.** Search results repeat the same item on multiple rows. Count distinct IDs, not rows.
- **Prefer the model notice over the overview.** A title containing "Model" or "Notice" (the deliverable) ranks above one containing "Compliance Overview" or "Bulletin" (the explanation). Pull both when both exist: the model notice goes in the packet, the overview backs the memo.
- **Prefer the current-year item when years appear in titles.** "Medicare Part D Notices Are Due Before Oct. 15, 2026" beats an undated equivalent when the plan year is 2026.
- **Do not trust relevance score ordering between near-identical titles.** Sibling items can tie. Select on title match.
- **Never hardcode content IDs in your reasoning as if they were stable.** IDs are Zywave-assigned and can change; the title pattern is the durable key. IDs listed in the catalog are hints to confirm a match, not a retrieval path.
- If a search returns nothing usable after one reformulation, mark the notice **"not in library — source externally"** and keep going.

---

## 4. Verify timing against the library's own text

Call `content_get_full_text` on the overview or bulletin for each notice whose deadline you are about to state. Confirm the timing rule and the audience from that text. If the library text and the catalog disagree, the library wins and you correct the memo.

The single item that covers most notices at once is the notice-and-disclosure compliance chart (search: "employee benefit compliance chart notice and disclosure rules"). Pull its full text first; it will settle most timing questions in one read.

Do not state a deadline you have not seen in library text. State the rule as the library states it (e.g. "before Oct. 15") rather than converting it to a specific weekday unless the client asks.

---

## 5. Download, bundle, and write the memo

**Downloads.** For each selected model notice and overview, call `content_download` with `convertToPdf: true`. Use the presigned URL it returns; do not rely on `fileDownloadUrl` from search results, which is frequently absent. Fetch each file into `/home/claude/packet/` with a filename of the form `NN - <Notice name>.pdf` in catalog order. If a download fails, record it and continue; the memo will list the item with its library title so the client can retrieve it.

**Memo.** Write `00 - Distribution Memo.md` using this exact structure:

```
# <Client> — Annual Notice Packet, Plan Year <YYYY>
Prepared <date>. Source: Zywave attorney-reviewed content library.

## Distribution schedule
| # | Notice | Who receives it | Due | Delivery | Status |
(one row per notice; Status = Included / Conditional — confirm applies / Not in library)

## Fill-in fields the plan administrator must complete
(per model notice: the blanks — plan name, administrator contact, creditable/non-creditable determination, etc.)

## Notices that are not annual
(Exchange notice, COBRA general notice, SPD — one line each on when they are owed)

## Assumptions made
(every default you took from section 1)

## Items included
(file list with the library title for each)
```

**Bundle.** Zip the packet folder as `<Client>-Annual-Notices-<YYYY>.zip`, copy it and the memo to `/mnt/user-data/outputs/`, and present both.

---

## 6. Report gaps in chat

Three to six lines. Lead with what is due soonest relative to today. Then the conditionals that need a yes/no from the client. Then anything not found in the library. Do not restate the memo.

---

## Hard rules

- Never fill blanks in a model notice with invented plan data. List the blanks; fill only values the user supplied.
- Never state whether the client's prescription drug coverage is creditable or non-creditable. That is an actuarial determination the plan makes; the memo says "plan must determine and select the matching notice."
- Never drop a notice because you guessed a condition wasn't met. Mark it conditional.
- Every deadline in the memo traces to library text you retrieved in this session.
- This packet is not legal advice. The memo footer says so in one sentence and points to the library sources.
