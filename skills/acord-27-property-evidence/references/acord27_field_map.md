# ACORD 27 field map

Field names verified against the ACORD 27 (2016/03) PDF in the Zywave content library,
content ID **239003**. The form is a proper AcroForm with **89 named fields** — 79 text,
10 checkbox, all on page 1.

Checkbox on-value is `/1`, off-value is `/Off`. Omit a checkbox rather than writing `/Off`.

**This form is not shaped like the ACORD 24 or 25.** It evidences one policy from one insurer.
There is no insurer A–F grid, no per-line coverage sections, and no certificate holder — the
recipient is an *additional interest* with a declared interest type. Only the producer and
named-insured blocks carry over from the other certificate forms.

If a field name here is rejected by `fill_acord27.py`, ACORD has revised the form — the script
fails loudly rather than silently dropping the value.

---

## Producer / agency

| Field | Source |
|---|---|
| `Form_CompletionDate_A` | certificate.issue_date (today) |
| `Producer_FullName_A` | producer.name |
| `Producer_MailingAddress_LineOne_A` / `_LineTwo_A` | producer.address1 / address2 |
| `Producer_MailingAddress_CityName_A` / `_StateOrProvinceCode_A` / `_PostalCode_A` | producer.city / state / zip |
| `Producer_ContactPerson_PhoneNumber_A` | producer.phone |
| `Producer_FaxNumber_A` | producer.fax |
| `Producer_ContactPerson_EmailAddress_A` | producer.email |
| `Producer_CustomerIdentifier_A` | producer.customer_id (AGENCY CUSTOMER ID #) |
| `Insurer_ProducerIdentifier_A` | producer.producer_code (CODE) |
| `Insurer_SubProducerIdentifier_A` | producer.sub_producer_code (SUB CODE) |
| `Producer_AuthorizedRepresentative_Signature_A` | producer.authorized_representative — **signature field** |

**There is no producer contact-name field on this form** — only phone, fax and email. Do not
try to map `producer.contact_name`; the script will abort because the field does not exist.

Note the `Insurer_` prefix on the producer CODE and SUB CODE fields. That is ACORD's naming
(they are the codes the *insurer* assigns the producer), not a mistake.

## Insurer / company

One insurer, with a full mailing address:

`Insurer_FullName_A`, `Insurer_MailingAddress_AddressLineOne_A`, `_AddressLineTwo_A`,
`_CityName_A`, `_StateOrProvinceCode_A`, `_PostalCode_A`.

Note these use `_AddressLineOne_A`, not `_LineOne_A` as the producer and insured blocks do.

## Named insured

`NamedInsured_FullName_A`, `NamedInsured_MailingAddress_LineOne_A`, `_LineTwo_A`,
`_CityName_A`, `_StateOrProvinceCode_A`, `_PostalCode_A`.

---

## Policy

| Field | Source |
|---|---|
| `Policy_PolicyNumberIdentifier_A` | policy.policy_number |
| `Policy_EffectiveDate_A` | policy.effective |
| `Policy_ExpirationDate_A` | policy.expiration |
| `EvidenceOfProperty_ContinuousBasisIndicator_A` | policy.continuous_until_cancelled |
| `EvidenceOfProperty_PriorEvidenceDate_A` | policy.prior_evidence_date |

**Expiration and the continuous indicator are mutually exclusive.** A policy either runs to a
date or continues until terminated. The script aborts if both are supplied rather than printing
a self-contradicting certificate.

**Causes of loss:**

| `perils[]` value | Field |
|---|---|
| `basic` | `Policy_PolicyType_BasicIndicator_A` |
| `broad` | `Policy_PolicyType_BroadIndicator_A` |
| `special` | `Policy_PolicyType_SpecialIndicator_A` |

`policy.other_peril` sets `Policy_PolicyType_OtherIndicator_A` +
`Policy_PolicyType_OtherDescription_A`.

There is **no flood or earthquake checkbox** on this form, unlike the ACORD 24. If either is
carried or excluded and it matters to the lender, it belongs in a coverage row or the remarks.

## Property location

`EvidenceOfProperty_PhysicalAddress_StreetLineOne_A`, `_StreetLineTwo_A`, `_CityName_A`,
`_CountyName_A`, `_StateOrProvinceCode_A`, `_PostalCode_A`.

This is the **insured location**, which is frequently not the named insured's mailing address.
The county field is real and lenders sometimes require it.

## Property description

`EvidenceOfProperty_PropertyDescription_A` — multiline, roughly 30pt tall (2–3 lines at
auto-fit sizes). Fed from `property_description[]`.

---

## Coverage rows

Ten identical free-form rows, slots **A** through **J**:

- `EvidenceOfProperty_CoverageDescription_{A..J}` — coverage / perils / forms
- `EvidenceOfProperty_LimitAmount_{A..J}` — amount of insurance
- `EvidenceOfProperty_DeductibleAmount_{A..J}` — deductible

Filled in array order from `coverages[]`. Integers are formatted with separators; pass a string
for anything non-numeric (`"INCLUDED"`, `"1% OF COV A"`, `"2% NAMED STORM"`).

More than ten coverages aborts the fill. Attach an ACORD 101 rather than silently truncating —
a dropped coverage row on an evidence form is an omission the lender will rely on.

## Remarks

`EvidenceOfProperty_RemarkText_A` — multiline, roughly 75pt tall, the largest box on the form
(around 8–10 lines at auto-fit sizes). Fed from `remarks[]`.

---

## Additional interest

This block replaces the certificate-holder block on the other forms, and it carries something
they do not: **the interest type**, which determines the holder's rights to loss proceeds.

| Field | Source |
|---|---|
| `AdditionalInterest_FullName_A` | additional_interest.name |
| `AdditionalInterest_MailingAddress_LineOne_A` / `_LineTwo_A` | address1 / address2 |
| `AdditionalInterest_MailingAddress_CityName_A` / `_StateOrProvinceCode_A` / `_PostalCode_A` | city / state / zip |
| `AdditionalInterest_AccountNumberIdentifier_A` | loan_number — **top LOAN NUMBER box** |
| `AdditionalInterest_AccountNumberIdentifier_B` | loan_number — **LOAN # box in this section** |

The two `AccountNumberIdentifier` fields are the same loan number printed in two places on the
form. `additional_interest.loan_number` fills both; there is deliberately no way to set them
independently, because a certificate showing two different loan numbers is a defect.

**Interest type checkboxes** — more than one may apply:

| `interests[]` value | Field |
|---|---|
| `additional_insured` | `AdditionalInterest_Interest_AdditionalInsuredIndicator_A` |
| `lenders_loss_payable` | `AdditionalInterest_Interest_LendersLossPayableIndicator_A` |
| `loss_payee` | `AdditionalInterest_Interest_LossPayeeIndicator_A` |
| `mortgagee` | `AdditionalInterest_Interest_MortgageeIndicator_A` |

`additional_interest.other_interest` sets `AdditionalInterest_Interest_OtherIndicator_A` +
`AdditionalInterest_Interest_OtherDescription_A`.

An unrecognized value aborts the fill. Issuing with no interest checked is allowed but prints a
warning — the holder's rights are undefined on such a certificate.

---

## Unmapped fields

`Form_EditionIdentifier_A` is preprinted by ACORD (its rect is zero-sized) and is not written.
