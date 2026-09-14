# COBRA notice sets

Which library items go in each packet, and the `content_search` query that surfaces each. Content IDs are hints to confirm a title match — they are Zywave-assigned and can change. Titles are the durable key.

## Items

| Key | Library title (match on this) | Search query | ID hint | Role |
|---|---|---|---|---|
| GEN | DOL Model COBRA Continuation Coverage General Notice | `DOL model COBRA general notice continuation coverage rights` | 45265 | Deliverable |
| ELECT | DOL Model COBRA Continuation Coverage Election Notice | `DOL model COBRA election notice` | 45263 | Deliverable |
| QE-FORM | Employee or Qualified Beneficiary's COBRA Qualifying Event Notice to Plan Administrator | `qualifying event notice to plan administrator form employee qualified beneficiary` | 45246 | Deliverable |
| ER-QE | Employer's notice of qualifying event to plan administrator | `employer notice of qualifying event to plan administrator COBRA form` | — | Deliverable (if present) |
| UNAVAIL | Notice of unavailability of COBRA coverage | `COBRA notice of unavailability of continuation coverage model` | — | Deliverable / guidance |
| EARLY | Notice of early termination of COBRA coverage | `COBRA notice of early termination of continuation coverage` | — | Deliverable / guidance |
| GUIDE | Benefits Toolkit - Employer's Guide to COBRA Administration | `employer's guide to COBRA administration toolkit` | 495650 | Governing text for timeline |
| TOOLKIT | COBRA Compliance Toolkit | `COBRA compliance toolkit employer requirements` | 155703 | Governing text (alternate) |
| FAQ-NOTIF | COBRA Common Questions: Notification Requirements | `COBRA notification requirements common questions` | 45164 | Explainer, always include |
| CHART | Employee Benefit Compliance Chart: Notice and Disclosure Rules | `employee benefit compliance chart notice and disclosure rules` | 13743 | Explainer, always include |
| STATE | <State> continuation coverage | `<State> continuation coverage mini-COBRA small employer` | — | Include when headcount < 20 or state has supplemental rules |

## Packets by event

| Event | Items |
|---|---|
| Coverage start (initial notice) | GEN, GUIDE, FAQ-NOTIF, CHART |
| Qualifying event — employer-known (termination, hours reduction, death, Medicare entitlement) | ER-QE (if present), ELECT, GUIDE, FAQ-NOTIF, CHART |
| Qualifying event — beneficiary-reported (divorce, legal separation, loss of dependent status) | QE-FORM, ELECT, GUIDE, FAQ-NOTIF, CHART |
| Second qualifying event or disability extension | QE-FORM, GUIDE, FAQ-NOTIF |
| Request denied (not a qualified beneficiary / not a qualifying event) | UNAVAIL, GUIDE, FAQ-NOTIF |
| COBRA ending early | EARLY, GUIDE, FAQ-NOTIF |
| Full administration reference | GEN, ELECT, QE-FORM, UNAVAIL, EARLY, GUIDE, TOOLKIT, FAQ-NOTIF, CHART |

## Timeline rules to locate in GUIDE or TOOLKIT

Find each in the retrieved text and cite the item. Do not fill from memory.

1. Employer → administrator notice deadline after a qualifying event
2. Administrator → qualified beneficiary election notice deadline; combined window when employer administers
3. Beneficiary → administrator notice deadline for divorce / dependent-status events
4. Election period length and its start point (later of notice date or loss of coverage)
5. Initial premium due date after election; ongoing grace period
6. General notice deadline from coverage start
7. Maximum coverage periods: 18 / 29 (disability) / 36 months
8. Notice of unavailability timing; early termination notice timing

## Blanks commonly found in the DOL model notices

List these in the memo under "Blanks to complete"; fill only the ones the user supplied:

- Plan name and plan administrator name, address, phone
- Employer name
- Qualified beneficiary names and the qualifying event and date
- Date coverage will be lost / last day of coverage
- Election deadline date (computed)
- Coverage options and monthly premium for each
- Maximum continuation period end date
- Where to send the election form and premium payments
- Contact for questions
