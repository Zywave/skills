# Audit checks — exact logic

All checks run over non-archived accounts and non-archived contacts. "Active contact" means `isActive` is true or absent.

| Check | Severity | Logic | Why it matters |
|---|---|---|---|
| NO_CONTACT | High | Active client account with zero active contacts | The agency has no one to call or email |
| PROSPECT_NO_CONTACT | High | Active prospect account with zero active contacts | Prospect cannot be worked or sequenced |
| NO_EMAIL | High | Active account with contacts, none with a non-empty `emailAddress` | Unreachable by campaign, renewal notice, or newsletter |
| EMAIL_NOT_ALLOWED | Low | Emailed contacts exist but all have `isEmailAllowed` false | Reachable only by phone; excluded from sequences |
| NO_PRIMARY | Medium | Active contacts exist, none has `isPrimaryContact` true | Ambiguous addressee for correspondence and certificates |
| DUP_CONTACT | Medium | Two active contacts on one account share a normalized email, or share normalized first+last name | Split history, double sends |
| DUP_ACCOUNT_NAME | Medium | ≥2 accounts with the same normalized name (suffixes like Inc/LLC stripped, punctuation and spaces removed) in the same city and state | Split policies and contacts across records |
| DUP_ACCOUNT_PHONE | Medium | ≥2 accounts with different names sharing a normalized 10-digit phone | Often the same entity under a DBA and a legal name |
| INACTIVE_NOT_ARCHIVED | Medium | `isActive` false and `isArchived` false | Clutters searches and counts; archive is reversible |
| STALE | Low | `updatedDateTime` older than the threshold (default 18 months). Skipped entirely when the field is absent from the data | Signals a record nobody owns |
| INCOMPLETE_ADDRESS | Low | Missing any of `city`, `state`, `postalCode` | Breaks state filtering and territory reporting |
| NO_CLASSIFICATION | Low | `classification` empty | Commercial vs Personal segmentation fails |

## Client vs prospect

Derived from `linesOfBusiness`. If the list is non-empty and every value contains "Prospect" (e.g. `["P&C Prospect"]`, `["Benefits Prospect"]`), the account is a **Prospect**. Anything else — including an empty list — is treated as **Client**. This is an assumption; it is printed on the Summary tab.

## Duplicate survivor suggestion

Within a candidate set, the suggested survivor is the record with the highest completeness score: one point each for address line, city, state, postal code, phone, classification, MSID; up to five points for contact count; two points for having any emailed contact. It is a suggestion. The human picks.

## What the audit does not check

- Policy, coverage, or renewal data — not exposed by the Zywave account tools
- Account-level documents — not exposed
- Contact phone validity — no verification source available
- Whether a "client" is actually still a client — `linesOfBusiness` is the only signal
