---
name: bulk-account-contact-import
description: Load a spreadsheet of companies and their contacts into Zywave CRM — creating the accounts that don't exist yet and then adding the contacts to them — with validation, market-data enrichment of the new accounts, duplicate detection, and a full dry run before any write. Handles acquisition exports, book migrations, event registration lists, and carrier group lists where most companies are not yet in the CRM. Produces a dry-run workbook (accounts to create, contact outcomes per row) and an import report. Use this whenever someone has a list of companies and people to load and says import, load, upload, bulk add, migrate, "get this book into Zywave," "add these accounts and contacts," or attaches a spreadsheet with a company column alongside any of those words. For one won client use new-account-onboarding; for companies already found in market data use prospect-to-account-conversion; for refreshing contacts on existing accounts use contact-enrichment-refresh.
---

# Bulk Account and Contact Import

Load a spreadsheet of companies and people into the CRM — accounts first, then contacts — without loading its mistakes.

Every agency has this file: the acquired book's export, the trade-show scan, the carrier's group list. Most of the companies in it don't exist in the CRM yet, so a contacts-only import stalls on row one. This skill runs two phases in a single dry run and a single approval: it works out which companies need an account, populates those from Zywave market data where it can, then attaches every contact row to the account it belongs to — matched or newly created. The dry-run workbook is the deliverable as much as the records are, because it's where the producer sees three hundred typos and forty duplicates before they become system-of-record.

## Workflow

1. Read the file and map the columns
2. Phase 1 — resolve companies; propose accounts to create
3. Phase 2 — validate contacts; check duplicates
4. Present the dry run; get one **go**
5. Create accounts, then contacts, in batches
6. Deliver the import report

---

## 1. Read the file and map the columns

Accept .csv, .xlsx, or .xls. Read it yourself (pandas or openpyxl). Show the header row and the first three data rows.

Map columns to fields. Read `references/field_map.md` for contact fields, the account-resolution columns (Account ID, MSID, Company, Company City/State), and common source-column names. Propose the mapping; the producer confirms or corrects in one message. Unmapped columns are reported and ignored, not silently dropped.

Required: a company column (or Account ID / MSID), `firstName`, `lastName`. Ask one question if the file doesn't answer it: **what line of business are these, and are they clients or prospects?** That sets `linesOfBusiness` and `classification` on every account created (e.g. `["Benefits Client"]`, Commercial). One value for the whole file; if the file mixes lines, ask for a column that says which.

---

## 2. Phase 1 — resolve companies; propose accounts to create

Pull the distinct companies (a 2,000-row file is usually ~300). For each:

1. **Account ID** column → `account_get` on distinct IDs. Exists → matched.
2. **MSID** column → `account_search` with `filter: "msid eq 'M...'"`. Exists → matched.
3. **Company name** → `account_search` with `filter: "startswith(name,'<token>')"`, compared on normalized name and, if present, city/state.
   - Exactly one normalized match → **matched**.
   - Several plausible → **ambiguous**; listed for the producer, rows held.
   - None → **to create**.

For every **to create** company, look it up in market data: `discovery_company_search` with `companyName` and `states` (from the file's company state or the contacts' state). One clear hit → take `msid`, address, phone, NAICS, employee count for the account payload and tag the source `market data`. No hit or several → build the payload from the file alone, tag `file only`, and leave `msid` empty. Cap market-data lookups at 300 companies per run; above that, split the file.

Write the resolved map to `resolved_accounts.json` (matched + ambiguous) and the market-data hits to `discovery.json`. These feed the validator.

Nothing is written in this step.

---

## 3. Phase 2 — validate contacts; check duplicates

Pull existing contacts once for the matched accounts: `account_contact_search` with `filter: "isArchived eq false"`, paged, then keep the rows whose `accountId` is in the matched set. Save to `existing_contacts.json`.

Run the validator:

```
python3 scripts/validate_import.py --input <file> --mapping mapping.json \
  --accounts resolved_accounts.json --discovery discovery.json \
  --existing existing_contacts.json --lob "<Line> <Client|Prospect>" --out dry_run.xlsx
```

It checks every contact row against the API's field limits, email format, phone digit count, state length, and the `gender` / `maritalStatus` enumerations; enforces one primary contact per account; and checks duplicates against existing contacts on matched accounts (same normalized email, or same first+last name). Each row lands in one outcome:

| Outcome | Meaning |
|---|---|
| **create_with_new_account** | Company is in phase 1's create list; contact created after the account is |
| **create** | Account matched; contact is new |
| **update** | Account matched; contact exists by name with a different email/phone/title |
| **skip — duplicate** | Identical to an existing contact |
| **fail** | Validation error (message in the row) |
| **ambiguous account** | Company matched several accounts; held for the producer |

Nothing is written in this step either.

---

## 4. Present the dry run; get one go

`dry_run.xlsx` has four tabs: **Summary** (phase 1 and phase 2 counts), **Accounts to create** (one row per company with the exact payload and its source), **All rows**, **Needs review** (fails and ambiguous). Present it.

In chat: the counts; the **Accounts to create** list with how many came from market data versus file-only; the fails and ambiguous rows in full; a sample of the create rows. Then:

> Create **A accounts** and **C contacts**, and update **U** existing contacts, across **K accounts**? Fails, duplicates, and ambiguous rows will be skipped.

Wait for yes. If the producer resolves ambiguous companies by naming the right account, re-run from step 2 — it's cheaper than patching in place. If they fix the file, start over from step 1.

---

## 5. Create accounts, then contacts, in batches

**Accounts first.** `account_create` per row of the Accounts-to-create tab with `name`, `classification`, `linesOfBusiness`, `isActive: true`, address, phone, `naicsCodes`, `numberOfEmployees`, `clientSize` (map headcount to the bucket string, e.g. `"100-499"`). `account_create` runs its own duplicate check; if it returns matches instead of an ID, **hold that company** — record it as *server-detected duplicate*, don't `forceCreate`, and skip its contacts for this run. Capture every returned `accountId` against the company key.

**Then contacts.** Replace the `NEW:<key>` placeholders with the returned IDs. `account_contact_create` per create row with `accountId`, name, `title`, `emailAddress`, phones, address fields, `isEmailAllowed` (default true), `isPrimaryContact` where the file says so and the validator kept it. `account_contact_update` per update row. Server-detected contact duplicates are recorded and skipped, not forced.

Batches of 50. One progress line per batch. Stop on three consecutive errors and report.

---

## 6. Deliver the import report

`import_report.xlsx` with tabs **Summary**, **Accounts created** (key, name, accountId, msid, source), **Contacts created**, **Contacts updated**, **Skipped** (with reason), **Failed** (with message), **Held** (ambiguous companies and server-detected duplicates, with the candidates). Present it.

In chat, five lines: accounts created, contacts created, contacts updated, skipped, failed — and the one next step, usually the held companies: "N companies were held because Zywave found a possible existing match; want to go through them?"

---

## Hard rules

- **Dry run first, every time.** One review, one yes, both phases. No write before the producer has seen the Accounts-to-create tab and the contact outcomes.
- **Accounts before contacts.** A contact row is never written to an account that doesn't exist yet.
- **Ambiguous companies are held, never guessed.** The producer picks; the skill doesn't.
- **No `forceCreate` during a bulk run** — for accounts or contacts. Server-detected duplicates go to the Held tab for review afterwards.
- One line of business and one client/prospect status per file unless a column says otherwise.
- Market data fills in address, phone, NAICS, and headcount; the file wins on the company name the producer gave. Every created account's source is recorded.
- At most one `isPrimaryContact` per account per run.
- No deletes or archives. Import adds and updates.
- The report is delivered even if the run stops early.
