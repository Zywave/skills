# ACORD 28 field map

Field names verified against the ACORD 28 (2016/03) PDF in the Zywave content library,
content ID **239006**. The form is a proper AcroForm with **159 named fields** — 83 text,
**76 checkbox**, all on page 1.

Checkbox on-value is `/1`, off-value is `/Off`. Omit a checkbox rather than writing `/Off`.

**The defining feature of this form is the Yes / No / N/A triad.** Most coverage lines are a
question with three answer columns. Two thirds of the fields on the form are those checkboxes.
See the tri-state table below.

---

## Producer / agency

Same names as the ACORD 27, **plus** a contact-name field the 27 lacks:

| Field | Source |
|---|---|
| `Form_CompletionDate_A` | certificate.issue_date |
| `Producer_FullName_A` | producer.name |
| `Producer_ContactPerson_FullName_A` | producer.contact_name — **present here, absent on the 27** |
| `Producer_MailingAddress_LineOne_A` / `_LineTwo_A` / `_CityName_A` / `_StateOrProvinceCode_A` / `_PostalCode_A` | producer address |
| `Producer_ContactPerson_PhoneNumber_A` | producer.phone |
| `Producer_FaxNumber_A` | producer.fax |
| `Producer_ContactPerson_EmailAddress_A` | producer.email |
| `Producer_CustomerIdentifier_A` | producer.customer_id |
| `Insurer_ProducerIdentifier_A` / `Insurer_SubProducerIdentifier_A` | producer_code / sub_producer_code |
| `Producer_AuthorizedRepresentative_Signature_A` | **signature field** |

## Insurer

`Insurer_FullName_A`, `Insurer_NAICCode_A` (the 27 has no NAIC field),
`Insurer_MailingAddress_AddressLineOne_A`, `_AddressLineTwo_A`, `_CityName_A`,
`_StateOrProvinceCode_A`, `_PostalCode_A`.

## Named insured

`NamedInsured_FullName_A` plus address lines, and `NamedInsured_FullName_B` for the
**ADDITIONAL NAMED INSURED(S)** box — a separate entity, commonly the operating company where
the property is held by a real-estate LLC.

## Policy

| Field | Source |
|---|---|
| `Policy_TypeDescription_A` | policy.type (free text) |
| `Policy_PolicyNumberIdentifier_A` | policy.policy_number |
| `Policy_EffectiveDate_A` / `Policy_ExpirationDate_A` | effective / expiration |
| `Policy_ContinuedUntilTerminatedIndicator_A` | policy.continued_until_terminated |
| `EvidenceOfProperty_PriorEvidenceDate_A` | policy.prior_evidence_date |
| `AdditionalInterest_AccountNumberIdentifier_A` | additional_interest.loan_number |

Note the field is `Policy_ContinuedUntilTerminatedIndicator_A` here — the ACORD 27 calls the
same concept `EvidenceOfProperty_ContinuousBasisIndicator_A`. Expiration and the continued
indicator are mutually exclusive; the script aborts if both are given.

**Causes of loss:** `Policy_PolicyType_BasicIndicator_A`, `_BroadIndicator_A`,
`_SpecialIndicator_A`, `_OtherIndicator_A` + `_OtherDescription_A`.

**What is covered:** `Property_Building_CoverageIndicator_A` and
`Property_BusinessPersonalProperty_CoverageIndicator_A` — the BUILDING **OR** BUSINESS PERSONAL
PROPERTY heading. Both may be checked.

## Location

`Location_PhysicalAddress_LineOne_A`, `_LineTwo_A`, `_CityName_A`, `_StateOrProvinceCode_A`,
`_PostalCode_A`, and `Location_LocationDescription_A` (multiline, ~24pt, fed from
`location_description[]`).

There is **no county field** on this form, unlike the ACORD 27.

## Property limit

`CommercialPropertyCoverage_Property_LimitAmount_A` and
`CommercialPropertyCoverage_Property_DeductibleAmount_A` — the COMMERCIAL PROPERTY COVERAGE
AMOUNT OF INSURANCE row.

---

## Tri-state coverage lines

Each key in `coverages` maps to a Yes / No / N/A trio. Prefixes below:
`CPC` = `CommercialPropertyCoverage_`, `CP` = `CommercialProperty_`,
`BOL` = `CommercialProperty_BuildingOrdinanceOrLaw_`.

| `coverages` key | Yes / No / N/A field stem | Limit / deductible |
|---|---|---|
| `terrorism` | `CPC Terrorism_*` | — |
| `terrorism_exclusion` | `CPC TerrorismExclusion_*` | — |
| `domestic_terrorism_exclusion` | `CPC DomesticTerrorismExclusion_*` | — |
| `limited_fungus` | `CPC LimitedFungus_*` | yes |
| `fungus_exclusion` | `CPC FungusExclusion_*` | form fields, see below |
| `replacement_cost` | `CPC ReplacementCost_*` | — |
| `agreed_value` | `CPC AgreedValue_*` | — |
| `coinsurance` | `CPC Coinsurance_*` | percent, see below |
| `equipment_breakdown` | `CPC EquipmentBreakdown_*` | yes |
| `ordinance_undamaged_portion` | `BOL UndamagedPortionOfBuilding*` | yes |
| `ordinance_demolition` | `BOL DemolitionCosts*` | yes |
| `ordinance_increased_cost` | `BOL IncreasedCostOfConstruction*` | yes |
| `earth_movement` | `CPC EarthMovement_*` | yes |
| `flood` | `CPC Flood_*` | yes |
| `subrogation_waiver` | `CP SubrogationWaiver_*` | — |

Suffixes are `YesIndicator_A`, `NoIndicator_A`, `NotApplicableIndicator_A`, and where a limit
applies, `LimitAmount_A` / `DeductibleAmount_A`. The ordinance-or-law limit fields are
inconsistently prefixed in the source form — the undamaged-portion limits carry the `CPC`
prefix while demolition and increased-cost carry the `BOL` prefix. The script has the exact
names; don't infer them.

**`coinsurance`** — the percent goes in `CommercialProperty_Premises_CoinsurancePercent_A`.

**`fungus_exclusion`** — when the answer is yes, the form asks which form is used:
`FormEndorsement_FormIdentifier_A`, `FormEndorsement_FormDate_A`,
`FormEndorsement_CopyrightOwnerCode_A`. Supplying these with a `no` answer aborts the fill —
a form number printed beside "No" says the opposite of what is meant.

## Business income / rental value

One row, several fields. Prefix `CPC BusinessIncomeOrRentalValue_`:

| Field | Source |
|---|---|
| `BusinessIncomeCoverageIndicator_A` | business_income (which of the two applies) |
| `RentalValueCoverageIndicator_A` | rental_value |
| `YesIndicator_A` / `NoIndicator_A` / `NotApplicableIndicator_A` | response |
| `LimitAmount_A` | limit |
| `ActualLossSustainedIndicator_A` | actual_loss_sustained |
| `ActualLossSustainedMonthCount_A` | months |

## Blanket

`CommercialProperty_Blanket_YesIndicator_A` / `_NoIndicator_A` / `_NotApplicableIndicator_A`,
and the reported value in `StatementOfValues_Premises_ValueAmount_A` — note the different field
family for the amount.

## Wind/hail and named windstorm

These rows ask **two** questions: is the peril included, and is it subject to different
provisions. Both are modelled, neither is inferred from the other.

| Purpose | wind_hail | named_windstorm |
|---|---|---|
| Included — yes | `CPC WindHail_YesIndicator_A` | `CPC NamedWindstorm_YesIndicator_A` |
| Included — no | `CPC WindHail_NoIndicator_A` | `CPC NamedWindstorm_NoIndicator_A` |
| Provisions — yes | `CPC WindHail_SubjectToProvisionsIndicator_A` | `CPC NamedWindstorm_SubjectToProvisionsIndicator_A` |
| Provisions — no | `CPC WindHail_SubjectToProvisionsNoIndicator_A` | `CPC NamedWindstorm_SubjectToProvisionsNoIndicator_A` |
| Provisions — N/A | `CPC WindHail_NotApplicableIndicator_A` | `CPC NamedWindstorm_SubjectToProvisionsNotApplicableIndicator_A` |
| Limit / deductible | `CPC WindHail_LimitAmount_A` / `_DeductibleAmount_A` | `CPC NamedWindstorm_LimitAmount_A` / `_DeductibleAmount_A` |

The N/A field names are asymmetric between the two rows — wind/hail uses
`NotApplicableIndicator_A`, named windstorm uses `SubjectToProvisionsNotApplicableIndicator_A`.
This is ACORD's inconsistency, faithfully reproduced.

---

## Two parties at the bottom

The bottom of the form has **two distinct blocks**, side by side. They are not duplicates.

**Left — ADDITIONAL INTEREST** (`_A` suffix), with interest-type checkboxes:

| `interests[]` value | Field |
|---|---|
| `contract_of_sale` | `AdditionalInterest_Interest_ContractOfSaleIndicator_A` |
| `lenders_loss_payable` | `AdditionalInterest_Interest_LendersLossPayableIndicator_A` |
| `loss_payee` | `AdditionalInterest_Interest_LossPayeeIndicator_A` |
| `mortgagee` | `AdditionalInterest_Interest_MortgageeIndicator_A` |

Plus `AdditionalInterest_Interest_OtherIndicator_A` + `_OtherDescription_A`, and
`AdditionalInterest_FullName_A` with `_MailingAddress_*_A`.

Note `contract_of_sale` appears here and not on the ACORD 27.

**Right — LENDER SERVICING AGENT NAME AND ADDRESS** (`_B` suffix):
`AdditionalInterest_FullName_B` with `_MailingAddress_*_B`, fed from
`lender_servicing_agent`.

Despite sharing the `AdditionalInterest_` prefix, this is the loan **servicer** — a different
company from the lender, and where notices actually go. Do not populate it with a copy of the
additional interest.

---

## Unmapped fields

`Form_EditionIdentifier_A` is preprinted by ACORD (zero-sized rect) and is not written.
