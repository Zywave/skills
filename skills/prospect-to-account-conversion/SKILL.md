---
name: prospect-to-account-conversion
description: Promote one or more companies the producer found in Zywave market data — from a prospect list, a research brief, a campaign shortlist, or a company they name — into Zywave CRM accounts as prospects, with firmographics populated from the market-data record, the primary decision-maker added as a contact when the producer chooses, and one explicit confirmation before any write. Handles single companies and batches up to 50, checks each against the existing book so nothing is created twice, and reports what was created versus skipped. Use this whenever a producer says add these to my pipeline, save these prospects, track this in CRM, "add [company] as a prospect," put this list in Zywave, or wants the output of a prospecting skill to become CRM records; or after any prospecting list when the producer asks to keep it. For a won client with a signed document use new-account-onboarding; for a spreadsheet of contacts use bulk-contact-import.
---

# Prospect-to-Account Conversion

Take what the prospecting skills found and make it a pipeline the CRM can see.

Every prospecting skill in the library ends with a list. Without this one, the list lives in a chat window and the producer re-keys the three they liked into Zywave by hand — or doesn't, and the CRM never reflects the pipeline. This skill closes that loop: MSIDs in, prospect accounts out, firmographics already populated, no duplicates, one confirmation. It's deliberately narrow. It doesn't research, doesn't email, and doesn't decide who's worth pursuing. The producer decided that already; this just records it.

## Workflow

1. Collect the companies
2. Check each against the book
3. Show the batch; get a **go**
4. Create the accounts
5. Add primary contacts (optional, gated)
6. Report

---

## 1. Collect the companies

Inputs arrive three ways:

- **MSIDs** from an earlier skill in the same conversation (renewal list, displacement shortlist, PEO list, market map sample). Use them directly.
- **Company names** the producer types. Resolve each with `discovery_company_search` (`companyName`, `states`); show candidates when ambiguous.
- **A campaign's prospects** — the producer says "save the companies from that campaign." Use the shortlist MSIDs from that conversation.

For each MSID, take from the market-data record: `name`, address, `city`, `state`, `zipCode`, `phoneNumber`, NAICS if present, employee count if present, `revenueRange`, `ein` if present.

Cap a batch at 50. Beyond that, split and confirm each batch.

Ask one question if it isn't obvious: **which line of business** are these prospects for — Commercial Lines, P&C, Benefits, or Personal Lines? The answer sets `linesOfBusiness` (e.g. `["Commercial Lines Prospect"]`) and `classification`.

---

## 2. Check each against the book

For each company: `account_search` with `filter: "msid eq '<M...>'"`. If that returns nothing, try `filter: "startswith(name,'<token>')"` and compare city.

- **Exists as client** for that line → skip, count as "already a client."
- **Exists as prospect** → skip, count as "already tracked." (Offer `account_update` if the producer wants to refresh firmographics — not by default.)
- **Exists under a different line** → offer to add the new Prospect line via `account_update` (fetch with `account_get` first; the update replaces the whole `linesOfBusiness` list). Count as "line added."
- **Not found** → create.

---

## 3. Show the batch; get a go

One table, one row per company: name, city, state, action (**create** / **add line** / **skip — client** / **skip — tracked**), and the fields that will be written. For creates, show `linesOfBusiness`, `classification`, address, phone, `clientSize` bucket, `naicsCodes`.

Then: "Create N prospect accounts and add a line to M existing ones?" Wait for yes. Remove rows first if asked.

`clientSize` on create takes bucket strings (`"51-99"`); map employee count to the bucket. Omit fields the record doesn't have rather than guessing.

---

## 4. Create the accounts

`account_create` per row, with `isActive: true`. `account_create` runs its own duplicate check; if it returns matches instead of an ID, **stop that row**, show the matches, and ask. `forceCreate: true` only on the producer's explicit word for that specific company.

`account_update` for the add-line rows, with the full `linesOfBusiness` list.

Record every returned `accountId` against its MSID.

---

## 5. Add primary contacts (optional, gated)

After the accounts exist, offer: "Add the primary decision-maker to each as a contact? I'll preview names and titles first; getting emails and phones is metered."

If yes: `discovery_company_contacts_get` with `enrich: false` per company (at most 50 calls), show the preview, and ask which to enrich. Then `enrich: true` **only** for the named contacts, and `account_contact_create` with `accountId`, name, `title`, `emailAddress`, phone, `isPrimaryContact: true`. Contact creation also detects duplicates; surface and confirm.

If the producer declines, the accounts stand without contacts. That's fine — `book-of-business-audit` will show them as NO_CONTACT later, which is a truthful state.

---

## 6. Report

Four lines: created (count, with IDs), lines added, skipped with reasons, contacts added. One line on what's next: `prospect-prep` on any of them before the first call, or `vertical-prospecting-campaign` to sequence them.

---

## Hard rules

- **One explicit yes before the first write**, on a table that shows exactly what will be written.
- **Never create a duplicate.** MSID check, then name+city check, then trust `account_create`'s own detection. `forceCreate` only per-company on explicit instruction.
- `account_update` with `linesOfBusiness` replaces the list. Always fetch first.
- Prospects are created as **Prospect** lines. This skill never marks anything a client.
- Enrichment is a second, separate yes, naming the contacts.
- Maximum 50 per batch.
