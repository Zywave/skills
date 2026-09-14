---
name: book-of-business-audit
description: Audit the CRM book of business in a Zywave tenant using only Zywave reads, no client files. Sweeps every active account and contact and produces an Excel workbook of findings — accounts with no active contact, no primary contact, no reachable email, likely duplicate accounts (same name or phone in the same city), duplicate contacts within an account, stale records, inactive-but-not-archived accounts, and incomplete address or classification data — with a summary tab, a per-check tab, and an account-level roll-up. Also runs as a narrower contact coverage check. Use this whenever someone asks to audit, clean up, review, or assess the book, the CRM, accounts, or contacts; asks which clients are missing a contact, a primary contact, or an email; asks about duplicate accounts or stale records; wants CRM data quality or hygiene; or asks how healthy the book is or which accounts can't be reached. Read-only — never archives, merges, or edits; hands clean-up off to a separate, confirmed request.
---

# Book of Business Audit

Sweep the tenant's accounts and contacts and report what's wrong with the data, in a workbook someone can work from.

The point of an audit is to be **exhaustive and non-destructive**. Every active account gets examined; nothing gets changed. A finding the audit missed is a finding nobody fixes; a record the audit "helpfully" archived is a phone call from an angry account manager. So this skill reads everything, writes nothing to Zywave, and puts the clean-up decisions in front of a human as a list.

## Workflow

1. Scope the sweep
2. Pull accounts and contacts (all pages)
3. Run the checks with the bundled script
4. Deliver the workbook and the summary
5. Offer follow-ons — without executing them

---

## 1. Scope the sweep

Default scope is **every non-archived account and every non-archived contact**. Use `totalCount` from the first page of each to size the job and tell the user before you page through (a 6,000-account, 18,000-contact tenant is ~240 calls at 100 per page; say so and proceed unless told to narrow).

Narrow only when asked, using the filterable fields:

| Ask | `account_search` filter |
|---|---|
| One state | `isArchived eq false and state eq 'MN'` |
| Commercial only | `isArchived eq false and classification eq 'Commercial'` |
| Mid-market | `isArchived eq false and clientSize eq 'From100To499'` |
| Touched recently | `isArchived eq false and updatedDateTime ge 2026-01-01T00:00:00Z` |

`linesOfBusiness` (client vs. prospect, P&C vs. Benefits) is **not filterable**. Pull everything and let the script segment on it.

If the user only asks a contact-coverage question ("which accounts have no contact"), still run the full pull — the marginal cost is the same and the workbook answers the next question before it's asked. Just lead the summary with the coverage findings.

---

## 2. Pull accounts and contacts

**Accounts.** `account_search` with `filter: "isArchived eq false"`, `top: 100`, `orderBy: "id"`, incrementing `skip` by 100 until `hasMoreResults` is false. Append every `items` array to `/home/claude/audit/accounts.json`.

**Contacts.** `account_contact_search` with `filter: "isArchived eq false"`, `top: 100`, `orderBy: "id"`, same paging. Append to `/home/claude/audit/contacts.json`.

Pull contacts globally and join on `accountId` in the script. Do **not** call `account_contact_search` once per account — that turns 180 calls into 6,000.

Write each page to disk as it arrives (append to a JSON-lines file, then combine) so a mid-run failure doesn't lose the pages already fetched. Give the user a one-line progress note every ~20 pages.

Record fields observed in the tenant: accounts carry `id, name, isActive, isArchived, classification, primaryPhone, addressLine1, city, state, postalCode, linesOfBusiness, clientSize` and may carry `msid, updatedDateTime`; contacts carry `id, accountId, firstName, lastName, emailAddress, isActive, isArchived, isEmailAllowed, isPrimaryContact, linesOfBusiness`. The script tolerates missing keys.

---

## 3. Run the checks

```
python3 scripts/audit.py \
  --accounts /home/claude/audit/accounts.json \
  --contacts /home/claude/audit/contacts.json \
  --out /mnt/user-data/outputs/Book-of-Business-Audit-<YYYY-MM-DD>.xlsx \
  --stale-months 18
```

The script runs these checks; see `references/checks.md` for exact logic and severity:

| Check | What it flags |
|---|---|
| NO_CONTACT | Active account with zero active contacts |
| NO_PRIMARY | Active account with contacts but none marked primary |
| NO_EMAIL | Active account with no active contact that has an email |
| EMAIL_NOT_ALLOWED | Account whose only emailed contacts have `isEmailAllowed` false |
| DUP_ACCOUNT_NAME | Two or more accounts with the same normalized name in the same city/state |
| DUP_ACCOUNT_PHONE | Two or more accounts sharing a phone number |
| DUP_CONTACT | Two contacts on one account with the same email, or same first+last |
| STALE | `updatedDateTime` older than the threshold (skipped if the field is absent) |
| INACTIVE_NOT_ARCHIVED | `isActive` false but `isArchived` false |
| INCOMPLETE_ADDRESS | Missing `city`, `state`, or `postalCode` |
| NO_CLASSIFICATION | `classification` empty |
| PROSPECT_NO_CONTACT | Prospect (per `linesOfBusiness`) with no contact — can't be worked |

Workbook tabs: **Summary** (counts per check, % of book, segmented by classification and client/prospect), **Findings** (one row per account × check, filterable), **Duplicates** (grouped candidate sets with a suggested survivor — suggestion only), **Accounts** (full roll-up: contact count, primary Y/N, email Y/N, flags).

If the script errors on a field it didn't expect, fix the script's field access — do not hand-compute the checks in chat.

---

## 4. Deliver

Present the workbook. In chat, five to eight lines:

- Book size (accounts, contacts, client/prospect split)
- The three findings with the largest counts, as counts and percentages
- The single most actionable one (usually NO_EMAIL or NO_CONTACT on clients — those are accounts the agency literally cannot reach)
- Duplicate candidate set count, described as candidates

Don't narrate the checks that found nothing beyond a single "no issues" line.

---

## 5. Offer follow-ons without executing them

The audit is read-only. If the user wants to act, each of these is a **separate request with its own confirmation**, and you describe them in one line each:

- Archive inactive-not-archived accounts (`account_delete`, `permanent: false`, restorable)
- Archive duplicate accounts after they pick a survivor (`account_delete`, `permanent: false`)
- Archive duplicate contacts (`account_contact_delete`, `permanent: false`)
- Add missing contacts (`account_contact_create`; duplicate detection is built in, respect it)

Never run any of these from within the audit, even if the user says "and clean it up" in the same message. Show the list, get an explicit yes per category, then act — and never use `permanent: true` in a clean-up derived from an audit. Archive is reversible; delete is not.

---

## Hard rules

- **No writes to Zywave in this skill.** Not one. The follow-on section exists so that the boundary is obvious.
- Pull the whole scope. A sampled audit is a guess with a spreadsheet attached.
- Duplicate sets are *candidates*. The workbook suggests a survivor by completeness; the human decides.
- `linesOfBusiness` values like "P&C Prospect" and "Benefits Prospect" mark prospects; anything else is treated as client. Say this assumption in the Summary tab.
- If `updatedDateTime` isn't present on returned records, the STALE check is skipped and the Summary says so — don't infer staleness from anything else.
