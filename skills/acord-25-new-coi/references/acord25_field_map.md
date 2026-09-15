# ACORD 25 field map

Field names verified against the ACORD 25 (2025/12) PDF in the Zywave content library,
content ID **239001**. The form is a proper AcroForm with **129 named fields** — 105 text,
24 checkbox. Field names are ACORD-standard and stable, so this map saves you from
re-deriving them on every run.

Checkbox on-value is `/1`, off-value is `/Off`, for every checkbox on the form.

If a field name below is ever rejected by `fill_acord25.py`, ACORD has revised the form.
Re-derive with `python3 scripts/extract_form_field_info.py <form.pdf> field_info.json`
from the public pdf skill and update this file.

---

## Header

| Field | Source |
|---|---|
| `Form_CompletionDate_A` | certificate.issue_date (today) |
| `CertificateOfInsurance_CertificateNumberIdentifier_A` | certificate.number |
| `CertificateOfInsurance_RevisionNumberIdentifier_A` | certificate.revision |

## Producer

| Field | Source |
|---|---|
| `Producer_FullName_A` | producer.name |
| `Producer_MailingAddress_LineOne_A` | producer.address1 |
| `Producer_MailingAddress_LineTwo_A` | producer.address2 |
| `Producer_MailingAddress_CityName_A` | producer.city |
| `Producer_MailingAddress_StateOrProvinceCode_A` | producer.state |
| `Producer_MailingAddress_PostalCode_A` | producer.zip |
| `Producer_ContactPerson_FullName_A` | producer.contact_name |
| `Producer_ContactPerson_PhoneNumber_A` | producer.phone |
| `Producer_FaxNumber_A` | producer.fax |
| `Producer_ContactPerson_EmailAddress_A` | producer.email |
| `Producer_AuthorizedRepresentative_Signature_A` | producer.authorized_representative — **signature field** |

## Insured

`NamedInsured_FullName_A`, `NamedInsured_MailingAddress_LineOne_A`,
`NamedInsured_MailingAddress_LineTwo_A`, `NamedInsured_MailingAddress_CityName_A`,
`NamedInsured_MailingAddress_StateOrProvinceCode_A`, `NamedInsured_MailingAddress_PostalCode_A`

## Certificate holder

`CertificateHolder_FullName_A`, `CertificateHolder_MailingAddress_LineOne_A`,
`CertificateHolder_MailingAddress_LineTwo_A`, `CertificateHolder_MailingAddress_CityName_A`,
`CertificateHolder_MailingAddress_StateOrProvinceCode_A`,
`CertificateHolder_MailingAddress_PostalCode_A`

## Insurers affording coverage

Letters A–F: `Insurer_FullName_{A..F}` and `Insurer_NAICCode_{A..F}`

---

## General Liability

| Field | Type | Notes |
|---|---|---|
| `GeneralLiability_CoverageIndicator_A` | checkbox | COMMERCIAL GENERAL LIABILITY — always check when a GL policy exists |
| `GeneralLiability_OccurrenceIndicator_A` | checkbox | form_basis == "occurrence" |
| `GeneralLiability_ClaimsMadeIndicator_A` | checkbox | form_basis == "claims_made" |
| `GeneralLiability_InsurerLetterCode_A` | text | insurer_letter |
| `CertificateOfInsurance_GeneralLiability_AdditionalInsuredCode_A` | text | `Y` / `N` |
| `Policy_GeneralLiability_SubrogationWaivedCode_A` | text | `Y` / `N` |
| `Policy_GeneralLiability_PolicyNumberIdentifier_A` | text | |
| `Policy_GeneralLiability_EffectiveDate_A` | text | MM/DD/YYYY |
| `Policy_GeneralLiability_ExpirationDate_A` | text | MM/DD/YYYY |
| `GeneralLiability_EachOccurrence_LimitAmount_A` | text | |
| `GeneralLiability_FireDamageRentedPremises_EachOccurrenceLimitAmount_A` | text | damage to rented premises |
| `GeneralLiability_MedicalExpense_EachPersonLimitAmount_A` | text | |
| `GeneralLiability_PersonalAndAdvertisingInjury_LimitAmount_A` | text | |
| `GeneralLiability_GeneralAggregate_LimitAmount_A` | text | |
| `GeneralLiability_ProductsAndCompletedOperations_AggregateLimitAmount_A` | text | |

Aggregate-applies-per checkboxes (pick one):
`GeneralLiability_GeneralAggregate_LimitAppliesPerPolicyIndicator_A`,
`...LimitAppliesPerProjectIndicator_A`, `...LimitAppliesPerLocationIndicator_A`,
`...LimitAppliesToOtherIndicator_A` (with text in `..._LimitAppliesToCode_A`)

## Automobile Liability

| Field | Type |
|---|---|
| `Vehicle_InsurerLetterCode_A` | text |
| `CertificateOfInsurance_AutomobileLiability_AdditionalInsuredCode_A` | text |
| `Policy_AutomobileLiability_SubrogationWaivedCode_A` | text |
| `Policy_AutomobileLiability_PolicyNumberIdentifier_A` | text |
| `Policy_AutomobileLiability_EffectiveDate_A` / `..._ExpirationDate_A` | text |
| `Vehicle_CombinedSingleLimit_EachAccidentAmount_A` | text |
| `Vehicle_BodilyInjury_PerPersonLimitAmount_A` | text |
| `Vehicle_BodilyInjury_PerAccidentLimitAmount_A` | text |
| `Vehicle_PropertyDamage_PerAccidentLimitAmount_A` | text |

Covered-auto checkboxes: `Vehicle_AnyAutoIndicator_A`, `Vehicle_AllOwnedAutosIndicator_A`,
`Vehicle_ScheduledAutosIndicator_A`, `Vehicle_HiredAutosIndicator_A`,
`Vehicle_NonOwnedAutosIndicator_A`

## Umbrella / Excess

| Field | Type |
|---|---|
| `Policy_PolicyType_UmbrellaIndicator_A` | checkbox |
| `Policy_PolicyType_ExcessIndicator_A` | checkbox |
| `ExcessUmbrella_OccurrenceIndicator_A` / `ExcessUmbrella_ClaimsMadeIndicator_A` | checkbox |
| `ExcessUmbrella_DeductibleIndicator_A` / `ExcessUmbrella_RetentionIndicator_A` | checkbox |
| `ExcessUmbrella_InsurerLetterCode_A` | text |
| `CertificateOfInsurance_ExcessLiability_AdditionalInsuredCode_A` | text |
| `Policy_ExcessLiability_SubrogationWaivedCode_A` | text |
| `Policy_ExcessLiability_PolicyNumberIdentifier_A` | text |
| `Policy_ExcessLiability_EffectiveDate_A` / `..._ExpirationDate_A` | text |
| `ExcessUmbrella_Umbrella_EachOccurrenceAmount_A` | text |
| `ExcessUmbrella_Umbrella_AggregateAmount_A` | text |
| `ExcessUmbrella_Umbrella_DeductibleOrRetentionAmount_A` | text |

## Workers Compensation / Employers Liability

| Field | Type | Notes |
|---|---|---|
| `WorkersCompensationEmployersLiability_WorkersCompensationStatutoryLimitIndicator_A` | checkbox | PER STATUTE |
| `WorkersCompensationEmployersLiability_OtherCoverageIndicator_A` | checkbox | OTHER |
| `WorkersCompensationEmployersLiability_InsurerLetterCode_A` | text | |
| `WorkersCompensationEmployersLiability_AnyPersonsExcludedIndicator_A` | text | `Y` / `N` — proprietor/partner excluded |
| `Policy_WorkersCompensation_SubrogationWaivedCode_A` | text | `Y` / `N` |
| `Policy_WorkersCompensationAndEmployersLiability_PolicyNumberIdentifier_A` | text | |
| `Policy_WorkersCompensationAndEmployersLiability_EffectiveDate_A` / `..._ExpirationDate_A` | text | |
| `WorkersCompensationEmployersLiability_EmployersLiability_EachAccidentLimitAmount_A` | text | |
| `WorkersCompensationEmployersLiability_EmployersLiability_DiseaseEachEmployeeLimitAmount_A` | text | |
| `WorkersCompensationEmployersLiability_EmployersLiability_DiseasePolicyLimitAmount_A` | text | |

Note there is no ADDL INSD field for the WC row — the form prints `N/A` there.

## Description of Operations

`CertificateOfLiabilityInsurance_ACORDForm_RemarkText_A` — rect is roughly 568 × 54 points,
which holds about 8 lines at 5.2pt. The fill script auto-fits the font size; if the text
still overflows, shorten it rather than shrinking below 4.8pt.

## Other Policy rows

`OtherPolicy_CoverageCode_{A,B,C}`, `OtherPolicy_CoverageLimitAmount_{A,B,C}`,
`OtherPolicy_InsurerLetterCode_A`, `OtherPolicy_PolicyNumberIdentifier_A`,
`OtherPolicy_PolicyEffectiveDate_A`, `OtherPolicy_PolicyExpirationDate_A`,
`CertificateOfInsurance_OtherPolicy_AdditionalInsuredCode_A`,
`OtherPolicy_SubrogationWaivedCode_A`, `OtherPolicy_OtherPolicyDescription_A`

---

## Rendering note

The blank form ships with `NeedAppearances = true`, which tells viewers to regenerate field
appearances. Most do, but the behaviour is inconsistent — and any renderer that isn't given a
form environment will show the page as blank.

`fill_acord25.py` sidesteps this by generating an explicit appearance stream for every populated
field and setting `NeedAppearances = false`. The result renders identically in every viewer and
stays fully editable. Don't "simplify" this by just setting field values and trusting the viewer.

If you need to verify output with pypdfium2, call `pdf.init_forms()` before
`render(..., may_draw_forms=True)`, or form fields won't be drawn and you'll misdiagnose a
perfectly good file.
