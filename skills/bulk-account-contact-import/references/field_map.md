# Field map

Contact target fields are the parameters of `account_contact_create` / `account_contact_update`. Account payloads built in phase 1 use `account_create` fields (name, classification, linesOfBusiness, primaryAddress*, workPhoneNumber, naicsCodes, numberOfEmployees, clientSize).
Limits are enforced by the API; the validator enforces them first so the run doesn't fail
halfway.

| Target field | Limit | Common source column names |
|---|---|---|
| `firstName` * | 50 | First, First Name, Given Name, FName |
| `lastName` * | 50 | Last, Last Name, Surname, LName |
| (split) | — | Name, Full Name, Contact, Contact Name → split on last space |
| `emailAddress` | 100, must contain `@` and a dot after it | Email, E-mail, Email Address, Work Email |
| `title` | 100 | Title, Job Title, Position, Role |
| `salutation` | 50 | Salutation, Prefix, Mr/Ms |
| `workPhoneNumber` | 50, ≥10 digits | Phone, Work Phone, Office, Business Phone, Direct |
| `mobilePhoneNumber` | 50, ≥10 digits | Mobile, Cell, Cell Phone |
| `homePhoneNumber` | 50 | Home Phone |
| `faxNumber` | 50 | Fax |
| `primaryAddressLine1` | 255 | Address, Address 1, Street |
| `primaryAddressLine2` | 255 | Address 2, Suite, Unit |
| `primaryAddressCity` | 75 | City |
| `primaryAddressState` | 4 | State, ST, Province |
| `primaryAddressPostalCode` | 50 | Zip, ZIP, Postal Code |
| `primaryAddressCountry` | 2 (ISO alpha-2) | Country → normalize "USA"/"United States" → "US" |
| `isPrimaryContact` | bool | Primary, Is Primary, Main Contact → Y/Yes/True/1 |
| `isEmailAllowed` | bool | Email Opt-In, Opt In, Do Not Email (inverted) |
| `isActive` | bool | Active, Status → Active/Inactive |
| `gender` | "Male" / "Female" | Gender, Sex |
| `maritalStatus` | Single / Married / Separated / Divorced / Widowed | Marital Status |
| `birthDate` | ISO 8601 date-time | DOB, Birth Date, Birthday → convert to YYYY-MM-DDT00:00:00Z |

\* required. A row missing either is a **fail**.

## Account resolution columns (not written to the contact)

| Purpose | Common source column names |
|---|---|
| Account ID | Account ID, AccountId, Zywave ID, Client ID |
| MSID | MSID, miEdge ID |
| Company name | Company, Account, Account Name, Organization, Employer, Client |
| City / State (for disambiguation) | Company City, Company State, or the contact's own city/state as a weak fallback |

## Normalization rules the validator applies

- Trim whitespace; collapse internal double spaces.
- Email lowercased.
- Phones: keep digits and a leading `+`; require ≥10 digits; store as given otherwise.
- State: uppercase; 2 letters preferred; ≤4 chars accepted.
- Booleans: `y, yes, true, 1, x` → true; `n, no, false, 0, blank` → false.
- Company name for matching: lowercase, strip punctuation, strip suffixes
  (inc, llc, ltd, co, corp, company, lp, llp), remove spaces.

## Duplicate rule

Within the resolved account: same normalized email → duplicate; else same normalized
first + last name → duplicate. Identical on every mapped field → **skip**; different email or
phone → **update**.
