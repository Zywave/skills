# ACORD 29 field map

Field names verified against the ACORD 29 (2016/03) PDF in the Zywave content library,
content ID **239009**. The form is a proper AcroForm with **146 named fields** — 84 text,
62 checkbox, all on page 1.

Checkbox on-value is `/1`, off-value is `/Off`. Omit a checkbox rather than writing `/Off`.

---

## The suffix offset — read this first

The form has three policy blocks. **ACORD's field suffixes are offset by one between a block's
header row and its coverage grid.** This is the single most likely thing to get wrong.

| Block on the form | Header fields | Coverage grid / market / form / product | Time-element row |
|---|---|---|---|
| PRIMARY POLICY | `Policy_PolicyNumberIdentifier_A`, `Policy_EffectiveDate_A`, `Policy_ExpirationDate_A` | suffix **`_A`** | **none — the form has no such row on primary** |
| EXCESS POLICY 1 | `ExcessFlood_PolicyNumberIdentifier_A`, `_PolicyEffectiveDate_A`, `_PolicyExpirationDate_A`, `Policy_PolicyType_ExcessFollowingFormIndicator_A` | suffix **`_B`** | suffix **`_A`** |
| EXCESS POLICY 2 | `ExcessFlood_*_B`, `ExcessFollowingFormIndicator_B` | suffix **`_C`** | suffix **`_B`** |

So Excess Policy 1's policy number is `ExcessFlood_PolicyNumberIdentifier_A` while its building
limit is `FloodCoverage_Building_BasicLimitAmount_B`. Verified by rendering the blank form, not
inferred from the names.

---

## Header

| Field | Source |
|---|---|
| `Form_CompletionDate_A` | certificate.issue_date |
| `CertificateOfInsurance_EvidenceNumberIdentifier_A` | certificate.evidence_number |
| `CertificateOfInsurance_RevisionNumberIdentifier_A` | certificate.revision |
| `Form_TotalPageNumber_A` | certificate.total_pages |
| `EvidenceOfProperty_PriorEvidenceDate_A` | certificate.prior_evidence_date |

Note this form uses **EvidenceNumber**, not CertificateNumber, and it has a total-page-count
field the other certificate forms lack — relevant when an ACORD 101 is attached.

## Producer

`Producer_FullName_A`, `Producer_MailingAddress_LineOne_A` / `_LineTwo_A` / `_CityName_A` /
`_StateOrProvinceCode_A` / `_PostalCode_A`, `Producer_ContactPerson_FullName_A`,
`Producer_ContactPerson_PhoneNumber_A`, **`Producer_ContactPerson_FaxNumber_A`**,
`Producer_ContactPerson_EmailAddress_A`, `Producer_CustomerIdentifier_A`,
`Producer_AuthorizedRepresentative_Signature_A`.

The fax field is `Producer_ContactPerson_FaxNumber_A` here — the ACORD 24, 27 and 28 all use
`Producer_FaxNumber_A`. Different field family for the same box.

## Insurers

Three rows only: `Insurer_FullName_{A,B,C}` and `Insurer_NAICCode_{A,B,C}`. The letter is then
referenced from each policy block's `Flood_InsurerLetterCode_{A,B,C}` (INS LTR column).

## Named insured and location

`NamedInsured_FullName_A` + `_MailingAddress_*_A`.

`Location_PhysicalAddress_LineOne_A` / `_LineTwo_A` / `_CityName_A` /
`_StateOrProvinceCode_A` / `_PostalCode_A`, and `Location_LocationDescription_A` (multiline,
~24pt) fed from `location_description[]`.

No county field on this form.

---

## Coverage / risk information

| Field | Source | Note |
|---|---|---|
| `Construction_BuiltDate_A` | risk.date_of_construction | DATE OF CONSTRUCTION |
| `FloodCommunity_CurrentFloodZoneCode_A` | risk.current_flood_zone | |
| `FloodCommunity_Rate_FloodZoneCode_A` | risk.rated_zone | FLOOD RISK / RATED ZONE — can differ from current |
| `FloodCoverage_Building_GrandfatheredCode_A` | risk.grandfathered | **text field, prints "Y" or "N"** — not a checkbox |
| `ResidentialStructure_ReplacementCostAmount_A` | risk.replacement_cost | |
| `BuildingOccupancy_UnitCount_A` | risk.unit_count | # UNITS |

**Condominium coverage is for (check one)** — the field names are misleading:

| Value | Field | Form label |
|---|---|---|
| `unit_owner` | `FloodInformation_SingleUnitCoverageYesIndicator_A` | UNIT OWNER |
| `association_building` | `FloodInformation_SingleUnitCoverageNoIndicator_A` | ASSOCIATION BUILDING |

These are named as a Yes/No pair but function as a two-way choice. Confirmed against the
rendered form.

**Building occupancy type:**

| Value | Field |
|---|---|
| `single_family` | `ResidenceOccupancy_OneFamilyIndicator_A` |
| `two_to_four_family` | `ResidenceOccupancy_TwoToFourFamiliesIndicator_A` |
| `other_residential` | `ResidenceOccupancy_OtherResidentialIndicator_A` |
| `non_residential` | `ResidenceOccupancy_NonResidentialIndicator_A` |
| `other` | `BuildingOccupancy_OtherIndicator_A` + `BuildingOccupancy_OccupancyDescription_A` |

**Contents coverage type:** `FloodCoverage_ContentsCoverageType_ResidentialIndicator_A`,
`_NonResidentialIndicator_A`, `_OtherIndicator_A` + `_OtherDescription_A`.

---

## Per-block fields

Substitute the grid suffix `{s}` from the offset table above.

| Purpose | Field |
|---|---|
| INS LTR | `Flood_InsurerLetterCode_{s}` |
| Building deductible / limit | `FloodCoverage_Building_DeductibleAmount_{s}` / `FloodCoverage_Building_BasicLimitAmount_{s}` |
| Contents deductible / limit | `FloodCoverage_Contents_DeductibleAmount_{s}` / `FloodCoverage_Contents_BasicLimitAmount_{s}` |

**Market** (`market`): `FloodCoverage_NFIPWYOIndicator_{s}` = `nfip_wyo`,
`FloodCoverage_PrivateMarketIndicator_{s}` = `private`.

**Policy form** (`policy_form`):

| Value | Field |
|---|---|
| `dwelling` | `Policy_BroadLineOfBusiness_DwellingIndicator_{s}` |
| `general_property` | `Policy_BroadLineOfBusiness_GeneralPropertyFormIndicator_{s}` |
| `rcbap` | `Policy_BroadLineOfBusiness_ResidentialCondominiumAssociationPolicyIndicator_{s}` |

**Product type** (`product_type`):

| Value | Field |
|---|---|
| `standard` | `Policy_PolicyType_StandardIndicator_{s}` |
| `preferred_risk` | `Policy_PolicyType_PreferredRiskIndicator_{s}` |
| `other` | `Policy_BroadLineOfBusiness_OtherIndicator_{s}` + `Policy_BroadLineOfBusiness_OtherDescription_{s}` |

Note the product-type "other" checkbox lives in the `BroadLineOfBusiness` family while standard
and preferred risk live in `PolicyType`. ACORD's inconsistency, reproduced.

**Programs** (`programs[]`, any combination):

| Value | Field |
|---|---|
| `preferred_risk_eligibility_extension` | `Policy_PolicyType_PreferredRiskEligibilityExtensionIndicator_{s}` |
| `group_flood` | `Policy_PolicyType_GroupFloodIndicator_{s}` |
| `mortgage_portfolio_protection` | `Policy_BroadLineOfBusiness_MortgagePortfolioProtectionProgramIndicator_{s}` |

**Time element** — excess blocks only, suffix `{t}` from the offset table:

`FloodCoverage_BusinessIncomeIndicator_{t}`, `FloodCoverage_ExtraExpenseIndicator_{t}`,
`FloodCoverage_AdditionalLivingExpenseIndicator_{t}`,
`FloodCoverage_AdditionalLivingExpense_LimitAmount_{t}`,
`FloodCoverage_LossSustainedIndicator_{t}`,
`FloodCoverage_LossSustained_NumberOfMonthsCount_{t}`.

Supplying `time_element` on the primary block aborts the fill — there is no such row on the
form for primary, so the data would be silently discarded.

## Remarks

`Flood_RemarkText_A` — multiline but only ~24pt tall, roughly **two lines**. Much smaller than
the ACORD 27's remarks box. Attach an ACORD 101 for anything longer and bump
`certificate.total_pages`.

---

## Additional interest

| Field | Source |
|---|---|
| `AdditionalInterest_FullName_A` + `_MailingAddress_*_A` | additional_interest |
| `AdditionalInterest_AccountNumberIdentifier_A` | loan_number (LOAN NUMBER) |

**Interest type:**

| Value | Field |
|---|---|
| `additional_insured` | `AdditionalInterest_Interest_AdditionalInsuredIndicator_A` |
| `lenders_loss_payable` | `AdditionalInterest_Interest_LendersLossPayableIndicator_A` |
| `loss_payee` | `AdditionalInterest_Interest_LossPayeeIndicator_A` |
| `mortgagee` | `AdditionalInterest_Interest_MortgageeIndicator_A` |
| `unit_owners_mortgagee` | `AdditionalInterest_Interest_UnitOwnerMortgageeIndicator_A` |

Plus `AdditionalInterest_Interest_OtherIndicator_A` + `_OtherDescription_A`.

`unit_owners_mortgagee` is specific to this form, and the form itself prints
"(Does not imply interest)" beside it — checking it is not a statement that the holder has an
insurable interest in the association's policy. Don't use it as a substitute for `mortgagee`.

**NAMED ON POLICY (check all that apply)** — which layer of the flood tower the holder is
named on:

| Value | Field | Form label |
|---|---|---|
| `primary` | `AdditionalInterest_AddedToPolicyIndicator_A` | PRIMARY |
| `excess_1` | `AdditionalInterest_AddedToPolicyIndicator_B` | EXCESS POLICY 1 |
| `excess_2` | `AdditionalInterest_AddedToPolicyIndicator_C` | EXCESS POLICY 2 |

Despite the `AddedToPolicy` naming these are not a generic yes/no — they are three independent
boxes identifying the layers. Checking one whose block is empty aborts the fill.

---

## Unmapped fields

`Form_EditionIdentifier_A` is preprinted by ACORD (zero-sized rect) and is not written.
