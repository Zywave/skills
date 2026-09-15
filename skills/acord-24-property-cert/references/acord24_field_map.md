# ACORD 24 field map

Field names verified against the ACORD 24 (2016/03) PDF in the Zywave content library,
content ID **239000**. The form is a proper AcroForm with **144 named fields** — 109 text,
35 checkbox, all on page 1.

Checkbox on-value is `/1`, off-value is `/Off`. Omit a checkbox rather than writing `/Off`.

**The header block is identical to the ACORD 25.** Producer, insured, insurers, certificate
holder, certificate number and signature all use the same field names, which is why
`acord_fill.py` is shared across the certificate skills.

If a field name here is rejected by `fill_acord24.py`, ACORD has revised the form — the
script fails loudly rather than silently dropping the value. Re-derive with
`build_form_map.py` from the acord-map toolkit and update this file.

---

## Header — shared with ACORD 25

| Field | Source |
|---|---|
| `Form_CompletionDate_A` | certificate.issue_date (today) |
| `CertificateOfInsurance_CertificateNumberIdentifier_A` | certificate.number |
| `CertificateOfInsurance_RevisionNumberIdentifier_A` | certificate.revision |
| `Producer_FullName_A` … `Producer_MailingAddress_PostalCode_A` | producer.* |
| `Producer_ContactPerson_FullName_A` | producer.contact_name |
| `Producer_ContactPerson_PhoneNumber_A` | producer.phone |
| `Producer_FaxNumber_A` | producer.fax |
| `Producer_ContactPerson_EmailAddress_A` | producer.email |
| `Producer_CustomerIdentifier_A` | producer.customer_id |
| `Producer_AuthorizedRepresentative_Signature_A` | producer.authorized_representative — **signature field** |
| `NamedInsured_*` | insured.* |
| `CertificateHolder_*` | certificate_holder.* |
| `Insurer_FullName_{A..F}`, `Insurer_NAICCode_{A..F}` | insurers[] |

Address suffixes on all three parties: `_FullName_A`, `_MailingAddress_LineOne_A`,
`_MailingAddress_LineTwo_A`, `_MailingAddress_CityName_A`,
`_MailingAddress_StateOrProvinceCode_A`, `_MailingAddress_PostalCode_A`.

---

## Two text boxes — do not confuse them

| Field | Box on form | Source |
|---|---|---|
| `CertificateOfLiabilityInsurance_ACORDForm_RemarkText_A` | LOCATION OF PREMISES / DESCRIPTION OF PROPERTY (upper, ~2 lines) | `location_description[]` |
| `CertificateOfLiabilityInsurance_ACORDForm_RemarkText_B` | SPECIAL CONDITIONS / OTHER COVERAGES (lower, ~6 lines) | `remarks[]` |

Both carry the `CertificateOfLiabilityInsurance_` prefix despite this being a property form —
that is ACORD's naming, not an error. The `_A` box is small; keep the property description to
one or two tight lines and put everything else in `_B`.

---

## Property section

| Field | Source |
|---|---|
| `Property_InsurerLetterCode_A` | policies.property.insurer_letter |
| `Policy_PolicyType_PropertyIndicator_A` | set when property is non-null |
| `Policy_Property_PolicyNumberIdentifier_A` | policy_number |
| `Policy_Property_EffectiveDate_A` / `_ExpirationDate_A` | effective / expiration |

**Causes of loss** — `perils[]` values map to:

| Value | Field |
|---|---|
| `basic` | `Policy_PolicyType_BasicIndicator_A` |
| `broad` | `Policy_PolicyType_BroadIndicator_A` |
| `special` | `Policy_PolicyType_SpecialIndicator_A` |
| `earthquake` | `CommercialPropertyCoverage_EarthquakeOption_IncludedIndicator_A` |
| `wind` | `Policy_PolicyType_WindIndicator_A` |
| `flood` | `CommercialPropertyCoverage_Flood_YesIndicator_A` |

`other_perils[]` fills `Policy_PolicyType_OtherIndicator_{A,B}` +
`Policy_PolicyType_OtherDescription_{A,B}` (max 2).

**Deductibles** — `deductibles[]` fills `CommercialProperty_Premises_DeductibleAmount_{A..G}`
in order. Slot A is the BUILDING deductible, B is CONTENTS; the rest are unlabeled rows.

**Covered property limits** — each sets its checkbox and limit together:

| limits key | Checkbox | Limit field |
|---|---|---|
| `building` | `Property_Building_CoverageIndicator_A` | `Property_Building_LimitAmount_A` |
| `personal_property` | `Property_PersonalProperty_CoverageIndicator_A` | `Property_PersonalProperty_LimitAmount_A` |
| `business_income` | `CommercialPropertyCoverage_BusinessIncomeOption_IncludedIndicator_A` | `CommercialPropertyCoverage_BusinessIncome_LimitAmount_A` |
| `extra_expense` | `CommercialPropertyCoverage_ExtraExpenseOption_IncludedIndicator_A` | `CommercialPropertyCoverage_ExtraExpense_LimitAmount_A` |
| `rental_value` | `CommercialPropertyCoverage_RentalValueOption_IncludedIndicator_A` | `CommercialPropertyCoverage_RentalValue_LimitAmount_A` |

**Blanket limits** — mapped by name, never by position:

| `blanket[].type` | Slot | Form line |
|---|---|---|
| `building` | A | BLANKET BUILDING |
| `personal_property` | B | BLANKET PERS PROP |
| `building_and_pp` | C | BLANKET BLDG & PP |

An unrecognized type aborts the fill. Positional mapping was the original design and it is
wrong: a blanket building-and-contents limit landing on the BLANKET BUILDING line understates
what is actually blanketed, on a document a lender relies on.

`other_coverages[]` fills `PropertyCoverage_OtherOption_IncludedIndicator_{A,B}` +
`PropertyCoverage_Other_CoverageDescription_{A,B}` + `PropertyCoverage_Other_LimitAmount_{A,B}`.

---

## Inland marine

`CommercialInlandMarineLineOfBusiness_InsurerLetterCode_A`,
`Policy_PolicyType_InlandMarineIndicator_A`,
`Policy_InlandMarine_PolicyNumberIdentifier_A`,
`Policy_InlandMarine_EffectiveDate_A`, `Policy_InlandMarine_ExpirationDate_A`,
`CommercialInlandMarineCoverage_Option_NamedPerilsIndicator_A`,
`Policy_PolicyType_OtherDescription_C` (causes of loss text).

Coverage rows A–D: `CommercialInlandMarineCoverage_Other_CoverageIndicator_{A..D}`,
`_CoverageDescription_{A..D}`, `_LimitAmount_{A..D}`.

## Crime

`CrimeLineOfBusiness_InsurerLetterCode_A`, `CrimeLineOfBusiness_CoverageIndicator_A`,
`Policy_Crime_PolicyNumberIdentifier_A`, `Policy_Crime_EffectiveDate_A`,
`Policy_Crime_ExpirationDate_A`, `Policy_PolicyType_OtherDescription_E` (type of policy).

Coverage rows A–C: `CrimeCoverage_OtherCoverage_CoverageIndicator_{A..C}`,
`_CoverageDescription_{A..C}`, `_LimitAmount_{A..C}`.

## Boiler & machinery / equipment breakdown

`BoilerAndMachineryLineOfBusiness_InsurerLetterCode_A`,
`BoilerAndMachineryLineOfBusiness_CoverageIndicator_A`,
`Policy_BoilerAndMachineryEquipmentBreakdown_PolicyNumberIdentifier_A`,
`Policy_BoilerAndMachinery_EffectiveDate_A`, `Policy_BoilerAndMachinery_ExpirationDate_A`.

Coverage rows A–B: `BoilerAndMachineryCoverage_OtherCoverage_CoverageIndicator_{A,B}`,
`_CoverageDescription_{A,B}`, `_LimitAmount_{A,B}`.

## Other policy

`OtherPolicy_InsurerLetterCode_A`, `OtherPolicy_OtherPolicyDescription_A`,
`OtherPolicy_PolicyNumberIdentifier_A`, `OtherPolicy_PolicyEffectiveDate_A`,
`OtherPolicy_PolicyExpirationDate_A`, and coverage rows
`OtherPolicy_CoverageIndicator_{A,B}` / `_CoverageDescription_{A,B}` / `_CoverageLimitAmount_{A,B}`.

---

## Unmapped fields

`Form_EditionIdentifier_A` is preprinted by ACORD and is not written.
`Policy_PolicyType_OtherIndicator_D` / `_OtherDescription_D` sit in the inland marine block and
are unused by the current mapping — available if a form revision needs them.
