---
name: contact-enrichment-refresh
description: Refresh the decision-maker contacts on a set of Zywave CRM accounts against Zywave market data — finding accounts whose contacts are missing, unreachable, or stale, previewing the current decision-makers at each company by name and title at no cost, and then, only after the producer reviews the preview and approves a named scope, enriching those contacts (email and phone, metered) and adding or updating them in the CRM with duplicate detection. Runs on a producer's book, a segment (state, size, classification), or a named list of accounts. Use this whenever someone asks to refresh contacts, update decision-makers, fix stale or bounced contacts, "who's the CFO there now," find current contacts for a client, re-enrich the book, or wants to know what a contact refresh would cost before doing it. For finding which accounts lack contacts use book-of-business-audit; for loading a spreadsheet use bulk-contact-import.
---

# Contact Enrichment Refresh

Bring the CRM's contacts back in line with who actually works at the client — and show the bill before running it.

Contacts rot. The CFO who signed three years ago retired; the HR director's email bounces; the account has one contact and it's the receptionist. Zywave's market data knows who the decision-makers are today. The catch is that fetching their email and phone is metered, and a careless refresh across a 6,000-account book is an invoice. So this skill is built around a cost preview: it finds the gap, shows the producer exactly which contacts it proposes to enrich, quotes the count, and enriches nothing until they say which.

## Workflow

1. Scope the refresh
2. Find the accounts that need it
3. Preview decision-makers — free
4. Present the proposal with the count
5. Enrich the approved scope
6. Write to the CRM, with duplicate handling
7. Report

---

## 1. Scope the refresh

| Scope | How |
|---|---|
| Named accounts | `account_search` by name or ID |
| A segment | `account_search` with `filter: "isArchived eq false and classification eq 'Commercial'"`, paged, then filter `state` in memory — `state eq` currently returns `INTERNAL_ERROR` (platform defect, Sep 2026) |
| The whole book | Same, no segment — confirm first; say the account count |
| Only accounts with a gap | Default — see step 2 |

Ask one thing if unstated: **refresh everyone in scope, or only accounts with a contact gap?** Default to gap-only; it's cheaper and it's usually what's meant.

---

## 2. Find the accounts that need it

Pull contacts for the scoped accounts: `account_contact_search` with `filter: "isArchived eq false"` paged (join on `accountId` in memory — one global pull, not one call per account).

An account has a **gap** when any of these is true:

- zero active contacts
- no contact with an `emailAddress`
- no `isPrimaryContact`
- the producer has said a named contact is gone or bouncing

Accounts with `msid` starting `M` can be looked up directly. Accounts without an MSID need `discovery_company_search` by name + city first; if no match, list them under **could not resolve** and leave them.

Show the gap count and the total before going further.

---

## 3. Preview decision-makers — free

For each gap account, `discovery_company_contacts_get` with `msid` and `enrich: false`, `pageSize: 10`. This returns names, titles, and availability flags (`HasEmail`, `HasDirectPhone`, `HasMobilePhone`) and **costs nothing**.

From the preview, pick the proposed contacts per account — typically the top one or two by title relevance (owner, CEO, CFO, controller, HR/benefits director for Benefits; owner, CFO, operations, risk/safety manager for Commercial) that have `HasEmail` true. Skip anyone already in the CRM by name.

Cap the preview pass at 200 accounts per run. Above that, narrow the scope.

---

## 4. Present the proposal with the count

A table: account, proposed contact name, title, availability flags, and whether the contact is **new** or **matches an existing CRM contact by name** (in which case the refresh updates email/phone rather than adding).

Then the line that matters:

> This would enrich **N contacts across M accounts** (metered). Approve all, approve by account, or give me the names.

Wait. Do not enrich on "looks good" — ask for the scope explicitly. Record what was approved.

---

## 5. Enrich the approved scope

`discovery_company_contacts_get` with `enrich: true` **only for the approved companies**, and take only the approved contacts from each response. If a company's approved contact isn't in the enriched response, record it as "not returned" — don't substitute someone else.

---

## 6. Write to the CRM, with duplicate handling

For each enriched contact:

- **Existing CRM contact (name match)** → `account_contact_update` with the new `emailAddress`, `title`, phones. Preserve `isPrimaryContact`.
- **New** → `account_contact_create` with `accountId`, name, `title`, `emailAddress`, `workPhoneNumber`/`mobilePhoneNumber`, `isEmailAllowed: true`. Set `isPrimaryContact: true` only if the account has none.
- Contact creation runs its own duplicate check; if it returns matches, show them and ask before `forceCreate`.

Never archive or delete an existing contact in this skill. If the producer says the old CFO is gone, note it in the report and offer `account_contact_delete(permanent: false)` as a separate, confirmed step.

---

## 7. Report

Five lines: accounts in scope, accounts with gaps, contacts enriched (the metered count), contacts created versus updated, and the **could not resolve** list. Offer to save the report as a workbook if the run touched more than 25 accounts.

---

## Hard rules

- **Preview is free; enrichment is metered; the producer approves the exact scope in between.** Never enrich on a general yes. Never enrich a company not in the approved list.
- Quote the count before enriching, every time.
- No deletions or archives from this skill. Adds and updates only.
- Existing contacts are updated, not duplicated. Match by name within the account before creating.
- `forceCreate` only after the producer sees the matches.
- Cap 200 accounts per run.
