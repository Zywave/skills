---
name: new-account-onboarding
description: Onboard a newly won client into the Zywave CRM from whatever the producer has — a broker of record letter, a signed application, a forwarded email, or just the company name — by resolving the company in Zywave market data, creating the account with firmographics populated, adding the decision-maker contacts, and assembling a welcome packet from the attorney-reviewed content library, with duplicate detection surfaced and one explicit confirmation before anything is written. Use this whenever someone says add this client, set up a new account, onboard, "add [company] to my book," BOR came in, we won the account, or asks to create an account or contact in Zywave; or when a document that names a new client is uploaded with any of those phrasings. For converting a prospect the producer already found in market data use prospect-to-account-conversion; for adding contacts in bulk use bulk-contact-import.
---

# New Account Onboarding

Turn a won account into a CRM record, correctly, once.

The moment an agency wins an account is the moment its data is most likely to be wrong for the next five years: the name gets typed from memory, the address from a business card, the contacts from whoever signed. This skill uses Zywave market data as the source of truth for the firmographics, lets the producer confirm what's about to be written, writes it in two calls, and hands the new client a welcome packet from the library. One motion, no re-keying, no duplicate.

## Workflow

1. Gather what's known
2. Resolve the company in market data
3. Check for an existing account
4. Show the record; get a **go**
5. Create the account and contacts
6. Assemble the welcome packet
7. Report

---

## 1. Gather what's known

From the document or the message, extract: legal name, DBA, address, city, state, ZIP, phone, website, headcount, NAICS or class of business, lines of business won (Commercial, Benefits, Personal Lines), effective date, the people named and their titles/emails/phones.

A BOR letter gives the legal name, address, effective date, and one signer. An application gives nearly everything. A bare company name gives a name. All three are workable — the skill fills gaps from market data in step 2.

Read any uploaded file yourself; don't ask the producer to retype what's in it.

---

## 2. Resolve the company in market data

`discovery_company_search` with `companyName` and `states` (and `city` if known). Show the top candidates if there's more than one plausible match and ask which. Capture: `msid`, `name`, address, `phoneNumber`, `revenueRange`, employee count if present, NAICS if present, `ein` if present.

Prefer market-data values for **address, phone, NAICS, headcount, year founded, website** — they're normalized and current. Prefer the **document's** value for legal name and lines of business — that's what the client signed. When they disagree on the name, show both and ask.

If no match: proceed with the document's data alone and say the account will lack an MSID (which means the prospecting skills won't overlay it later). Offer to retry with a variant name.

---

## 3. Check for an existing account

`account_search` with `filter: "startswith(name,'<first distinctive token>')"` and, if there's an MSID, `filter: "msid eq '<M...>'"`. Also try the phone: `filter: "phoneNumber eq '<digits>'"`.

If a match exists:

- Already a **client** for the same line → stop. Tell the producer the account exists, show it, and offer `account_update` to add the new line of business or correct fields. Nothing is created.
- Exists as a **prospect** → this is the common case. Don't create a second account. Use `account_update` to change `linesOfBusiness` (fetch first with `account_get`; the update replaces the whole list, so include every existing value and swap Prospect → Client for the won line). Then add contacts to the existing account.
- No match → create.

`account_create` has its own duplicate detection and will return matches instead of creating. If it does, show them and stop; never pass `forceCreate: true` without the producer looking at the matches and saying yes.

---

## 4. Show the record; get a go

Present exactly what will be written, field by field, with the source of each value tagged `[document]`, `[market data]`, or `[producer]`:

```
Account
  name                Riverside Freight LLC           [document]
  classification      Commercial                      [producer]
  linesOfBusiness     ["Commercial Lines Client"]     [document]
  primaryAddress      675 Industrial Pkwy, Madison WI 53713   [market data]
  workPhoneNumber     +1 608 555 0142                 [market data]
  clientSize          100-499                         [market data: 140 employees]
  numberOfEmployees   140                             [market data]
  naicsCodes          ["484121"]                      [market data]
  yearFounded         2004                            [market data]
  url                 riversidefreight.example        [market data]

Contacts
  Dana Ortiz, CFO, dortiz@…, (608) 555-0143, primary   [document]
  Luis Herrera, HR Director, lherrera@…                [document]
```

Then: "Create this account and 2 contacts in Zywave?" Wait for yes. Edits first if asked.

`clientSize` on create/update takes the bucket strings (`"100-499"`), not the search-filter enum. Map headcount to the bucket.

---

## 5. Create the account and contacts

`account_create` with the fields above. Capture the returned `accountId`.

Then `account_contact_create` once per contact with `accountId`, name, `title`, `emailAddress`, phones, `isPrimaryContact` on exactly one, `isEmailAllowed: true` unless the document says otherwise. Contact creation also detects duplicates; if it returns matches, show them and ask before `forceCreate`.

If contacts weren't in the document, offer to preview decision-makers with `discovery_company_contacts_get` (`enrich: false`) and add the ones the producer picks. Enriching (emails and phones) is metered — name the contacts and confirm before `enrich: true`.

---

## 6. Assemble the welcome packet

`content_search` for two or three client-facing pieces matched to the line of business and class: for Commercial, a risk-management overview for the NAICS and a certificate-request guide; for Benefits, a compliance-calendar overview and an employee-communications piece; for Personal Lines, a coverage-review checklist. Select on title, dedupe on `contentId`, `content_download` with `convertToPdf: true`.

Bundle as `<Client>-Welcome-Packet.zip` with a one-page `00 - Welcome.md` naming the account manager, the effective date, and what's enclosed. Present it.

Skip this step if the producer says so; it's the part they're most likely to already have a process for.

---

## 7. Report

Four lines: account created (or updated) with its ID and MSID; contacts added by name; what came from market data versus the document; the packet. If anything was skipped or couldn't be resolved, say which.

---

## Hard rules

- **One explicit yes before the first write.** The preview in step 4 is not optional and not a summary — it's the exact payload.
- **Never create when a match exists.** Update the prospect, or stop on the client. Duplicate accounts are the thing this skill exists to prevent.
- `forceCreate: true` only after the producer has seen the duplicate matches and said to proceed.
- `account_update` with `linesOfBusiness` replaces the list. Fetch first, include everything that should remain.
- Every written value has a stated source. Market data fills gaps; the signed document wins on name and lines of business.
- No enrichment without naming the contacts and confirming.
