#!/usr/bin/env python3
"""
Fill an ACORD 28 Evidence of Commercial Property Insurance from commercial_evidence_data.json.

Usage:
    python3 fill_acord28.py <blank_acord28.pdf> <commercial_evidence_data.json> <outdir>
                            [--flat-only|--fillable-only]

Produces:
    <outdir>/ACORD28_<insured>_FILLABLE.pdf   AcroForm intact, all fields editable
    <outdir>/ACORD28_<insured>.pdf            flattened, renders anywhere

The ACORD 28 is a Yes / No / N/A questionnaire. Nearly every coverage line asks a question
with three possible answers, and they mean different things:

    yes  - the coverage or condition is in force
    no   - it is NOT in force. This is an affirmative negative statement.
    na   - the question does not apply to this policy or location

"No" and "N/A" are not interchangeable. A lender reading "N/A" against flood on a Zone AE
building learns nothing; "No" tells them the exposure is uninsured. Leaving a line unanswered
tells them less than either. Answer every line the policy speaks to.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acord_fill import FormSpec, money, render_both

SIG = "Producer_AuthorizedRepresentative_Signature_A"
LOC_BOX = "Location_LocationDescription_A"
ON = "/1"

CPC = "CommercialPropertyCoverage_"
CP = "CommercialProperty_"
BOL = CP + "BuildingOrdinanceOrLaw_"

# key -> (yes_field, no_field, na_field, limit_field|None, deductible_field|None)
TRISTATE = {
    "terrorism": (CPC + "Terrorism_YesIndicator_A", CPC + "Terrorism_NoIndicator_A",
                  CPC + "Terrorism_NotApplicableIndicator_A", None, None),
    "terrorism_exclusion": (CPC + "TerrorismExclusion_YesIndicator_A",
                            CPC + "TerrorismExclusion_NoIndicator_A",
                            CPC + "TerrorismExclusion_NotApplicableIndicator_A", None, None),
    "domestic_terrorism_exclusion": (CPC + "DomesticTerrorismExclusion_YesIndicator_A",
                                     CPC + "DomesticTerrorismExclusion_NoIndicator_A",
                                     CPC + "DomesticTerrorismExclusion_NotApplicableIndicator_A",
                                     None, None),
    "limited_fungus": (CPC + "LimitedFungus_YesIndicator_A", CPC + "LimitedFungus_NoIndicator_A",
                       CPC + "LimitedFungus_NotApplicableIndicator_A",
                       CPC + "LimitedFungus_LimitAmount_A", CPC + "LimitedFungus_DeductibleAmount_A"),
    "fungus_exclusion": (CPC + "FungusExclusion_YesIndicator_A",
                         CPC + "FungusExclusion_NoIndicator_A",
                         CPC + "FungusExclusion_NotApplicableIndicator_A", None, None),
    "replacement_cost": (CPC + "ReplacementCost_YesIndicator_A",
                         CPC + "ReplacementCost_NoIndicator_A",
                         CPC + "ReplacementCost_NotApplicableIndicator_A", None, None),
    "agreed_value": (CPC + "AgreedValue_YesIndicator_A", CPC + "AgreedValue_NoIndicator_A",
                     CPC + "AgreedValue_NotApplicableIndicator_A", None, None),
    "coinsurance": (CPC + "Coinsurance_YesIndicator_A", CPC + "Coinsurance_NoIndicator_A",
                    CPC + "Coinsurance_NotApplicableIndicator_A", None, None),
    "equipment_breakdown": (CPC + "EquipmentBreakdown_YesIndicator_A",
                            CPC + "EquipmentBreakdown_NoIndicator_A",
                            CPC + "EquipmentBreakdown_NotApplicableIndicator_A",
                            CPC + "EquipmentBreakdown_LimitAmount_A",
                            CPC + "EquipmentBreakdown_DeductibleAmount_A"),
    "ordinance_undamaged_portion": (BOL + "UndamagedPortionOfBuildingYesIndicator_A",
                                    BOL + "UndamagedPortionOfBuildingNoIndicator_A",
                                    BOL + "UndamagedPortionOfBuildingNotApplicableIndicator_A",
                                    CPC + "BuildingOrdinanceOrLaw_UndamagedPortionBuildingLimitAmount_A",
                                    CPC + "BuildingOrdinanceOrLaw_UndamagedPortionBuildingDeductibleAmount_A"),
    "ordinance_demolition": (BOL + "DemolitionCostsYesIndicator_A",
                             BOL + "DemolitionCostsNoIndicator_A",
                             BOL + "DemolitionCostsNotApplicableIndicator_A",
                             BOL + "DemolitionCostsLimitAmount_A",
                             BOL + "DemolitionCostsDeductibleAmount_A"),
    "ordinance_increased_cost": (BOL + "IncreasedCostOfConstructionYesIndicator_A",
                                 BOL + "IncreasedCostOfConstructionNoIndicator_A",
                                 BOL + "IncreasedCostOfConstructionNotApplicableIndicator_A",
                                 BOL + "IncreasedCostOfConstructionLimitAmount_A",
                                 BOL + "IncreasedCostOfConstructionDeductibleAmount_A"),
    "earth_movement": (CPC + "EarthMovement_YesIndicator_A", CPC + "EarthMovement_NoIndicator_A",
                       CPC + "EarthMovement_NotApplicableIndicator_A",
                       CPC + "EarthMovement_LimitAmount_A", CPC + "EarthMovement_DeductibleAmount_A"),
    "flood": (CPC + "Flood_YesIndicator_A", CPC + "Flood_NoIndicator_A",
              CPC + "Flood_NotApplicableIndicator_A",
              CPC + "Flood_LimitAmount_A", CPC + "Flood_DeductibleAmount_A"),
    "subrogation_waiver": (CP + "SubrogationWaiver_YesIndicator_A",
                           CP + "SubrogationWaiver_NoIndicator_A",
                           CP + "SubrogationWaiver_NotApplicableIndicator_A", None, None),
}

# Wind/hail and named windstorm ask two questions on one row: is the peril included, and is it
# subject to different provisions. Both are modelled explicitly rather than collapsed.
WIND_ROWS = {
    "wind_hail": {
        "incl_yes": CPC + "WindHail_YesIndicator_A",
        "incl_no": CPC + "WindHail_NoIndicator_A",
        "prov_yes": CPC + "WindHail_SubjectToProvisionsIndicator_A",
        "prov_no": CPC + "WindHail_SubjectToProvisionsNoIndicator_A",
        "prov_na": CPC + "WindHail_NotApplicableIndicator_A",
        "limit": CPC + "WindHail_LimitAmount_A",
        "deductible": CPC + "WindHail_DeductibleAmount_A",
    },
    "named_windstorm": {
        "incl_yes": CPC + "NamedWindstorm_YesIndicator_A",
        "incl_no": CPC + "NamedWindstorm_NoIndicator_A",
        "prov_yes": CPC + "NamedWindstorm_SubjectToProvisionsIndicator_A",
        "prov_no": CPC + "NamedWindstorm_SubjectToProvisionsNoIndicator_A",
        "prov_na": CPC + "NamedWindstorm_SubjectToProvisionsNotApplicableIndicator_A",
        "limit": CPC + "NamedWindstorm_LimitAmount_A",
        "deductible": CPC + "NamedWindstorm_DeductibleAmount_A",
    },
}

PERILS = {
    "basic": "Policy_PolicyType_BasicIndicator_A",
    "broad": "Policy_PolicyType_BroadIndicator_A",
    "special": "Policy_PolicyType_SpecialIndicator_A",
}

INTERESTS = {
    "contract_of_sale": "AdditionalInterest_Interest_ContractOfSaleIndicator_A",
    "lenders_loss_payable": "AdditionalInterest_Interest_LendersLossPayableIndicator_A",
    "loss_payee": "AdditionalInterest_Interest_LossPayeeIndicator_A",
    "mortgagee": "AdditionalInterest_Interest_MortgageeIndicator_A",
}

RESPONSES = ("yes", "no", "na")


def amt(x):
    if x is None:
        return None
    return money(x) if isinstance(x, (int, float)) else str(x)


def build_values(d):
    v = {}
    v["Form_CompletionDate_A"] = d.get("certificate", {}).get("issue_date", "")

    p = d.get("producer", {})
    for fid, key in [
        ("Producer_FullName_A", "name"),
        ("Producer_ContactPerson_FullName_A", "contact_name"),
        ("Producer_MailingAddress_LineOne_A", "address1"),
        ("Producer_MailingAddress_LineTwo_A", "address2"),
        ("Producer_MailingAddress_CityName_A", "city"),
        ("Producer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Producer_MailingAddress_PostalCode_A", "zip"),
        ("Producer_ContactPerson_PhoneNumber_A", "phone"),
        ("Producer_FaxNumber_A", "fax"),
        ("Producer_ContactPerson_EmailAddress_A", "email"),
        ("Producer_CustomerIdentifier_A", "customer_id"),
        ("Insurer_ProducerIdentifier_A", "producer_code"),
        ("Insurer_SubProducerIdentifier_A", "sub_producer_code"),
        (SIG, "authorized_representative"),
    ]:
        if p.get(key):
            v[fid] = p[key]

    ins = d.get("insurer", {}) or {}
    for fid, key in [
        ("Insurer_FullName_A", "name"),
        ("Insurer_NAICCode_A", "naic"),
        ("Insurer_MailingAddress_AddressLineOne_A", "address1"),
        ("Insurer_MailingAddress_AddressLineTwo_A", "address2"),
        ("Insurer_MailingAddress_CityName_A", "city"),
        ("Insurer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Insurer_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ins.get(key):
            v[fid] = ins[key]

    ni = d.get("insured", {}) or {}
    for fid, key in [
        ("NamedInsured_FullName_A", "name"),
        ("NamedInsured_MailingAddress_LineOne_A", "address1"),
        ("NamedInsured_MailingAddress_LineTwo_A", "address2"),
        ("NamedInsured_MailingAddress_CityName_A", "city"),
        ("NamedInsured_MailingAddress_StateOrProvinceCode_A", "state"),
        ("NamedInsured_MailingAddress_PostalCode_A", "zip"),
        ("NamedInsured_FullName_B", "additional_named_insured"),
    ]:
        if ni.get(key):
            v[fid] = ni[key]

    pol = d.get("policy", {}) or {}
    if pol.get("type"):
        v["Policy_TypeDescription_A"] = pol["type"]
    if pol.get("policy_number"):
        v["Policy_PolicyNumberIdentifier_A"] = pol["policy_number"]
    if pol.get("effective"):
        v["Policy_EffectiveDate_A"] = pol["effective"]

    continued = bool(pol.get("continued_until_terminated"))
    if continued and pol.get("expiration"):
        raise SystemExit(
            "policy.continued_until_terminated is true but an expiration date was also given. "
            "A policy either runs to a date or continues until terminated — pick one.")
    if continued:
        v["Policy_ContinuedUntilTerminatedIndicator_A"] = ON
    elif pol.get("expiration"):
        v["Policy_ExpirationDate_A"] = pol["expiration"]

    if pol.get("prior_evidence_date"):
        v["EvidenceOfProperty_PriorEvidenceDate_A"] = pol["prior_evidence_date"]

    for peril in pol.get("perils", []):
        if peril in PERILS:
            v[PERILS[peril]] = ON
    if pol.get("other_peril"):
        v["Policy_PolicyType_OtherIndicator_A"] = ON
        v["Policy_PolicyType_OtherDescription_A"] = pol["other_peril"]

    # which property is covered
    for key, fid in [("building", "Property_Building_CoverageIndicator_A"),
                     ("business_personal_property",
                      "Property_BusinessPersonalProperty_CoverageIndicator_A")]:
        if pol.get("covers", {}).get(key):
            v[fid] = ON

    loc = d.get("location", {}) or {}
    for fid, key in [
        ("Location_PhysicalAddress_LineOne_A", "address1"),
        ("Location_PhysicalAddress_LineTwo_A", "address2"),
        ("Location_PhysicalAddress_CityName_A", "city"),
        ("Location_PhysicalAddress_StateOrProvinceCode_A", "state"),
        ("Location_PhysicalAddress_PostalCode_A", "zip"),
    ]:
        if loc.get(key):
            v[fid] = loc[key]

    if pol.get("limit") is not None:
        v[CPC + "Property_LimitAmount_A"] = amt(pol["limit"])
    if pol.get("deductible") is not None:
        v[CPC + "Property_DeductibleAmount_A"] = amt(pol["deductible"])

    covs = d.get("coverages", {}) or {}

    # ---------------------------------------------- business income / rental value
    bi = covs.get("business_income_rental_value")
    if bi:
        resp = bi.get("response")
        if resp not in RESPONSES:
            raise SystemExit(f"business_income_rental_value.response must be one of {RESPONSES}")
        pre = CPC + "BusinessIncomeOrRentalValue_"
        v[{"yes": pre + "YesIndicator_A", "no": pre + "NoIndicator_A",
           "na": pre + "NotApplicableIndicator_A"}[resp]] = ON
        if bi.get("business_income"):
            v[pre + "BusinessIncomeCoverageIndicator_A"] = ON
        if bi.get("rental_value"):
            v[pre + "RentalValueCoverageIndicator_A"] = ON
        if bi.get("limit") is not None:
            v[pre + "LimitAmount_A"] = amt(bi["limit"])
        if bi.get("actual_loss_sustained"):
            v[pre + "ActualLossSustainedIndicator_A"] = ON
            if bi.get("months") is not None:
                v[pre + "ActualLossSustainedMonthCount_A"] = str(bi["months"])

    # -------------------------------------------------------------------- blanket
    bl = covs.get("blanket")
    if bl:
        resp = bl.get("response")
        if resp not in RESPONSES:
            raise SystemExit(f"blanket.response must be one of {RESPONSES}")
        v[{"yes": CP + "Blanket_YesIndicator_A", "no": CP + "Blanket_NoIndicator_A",
           "na": CP + "Blanket_NotApplicableIndicator_A"}[resp]] = ON
        if bl.get("value") is not None:
            v["StatementOfValues_Premises_ValueAmount_A"] = amt(bl["value"])

    # ------------------------------------------------------------ tri-state lines
    for key, (yf, nf, naf, lf, df) in TRISTATE.items():
        c = covs.get(key)
        if not c:
            continue
        resp = c.get("response")
        if resp not in RESPONSES:
            raise SystemExit(
                f"coverages.{key}.response is {resp!r}; must be one of {RESPONSES}. "
                "'no' and 'na' are different statements — do not guess between them.")
        v[{"yes": yf, "no": nf, "na": naf}[resp]] = ON
        if lf and c.get("limit") is not None:
            v[lf] = amt(c["limit"])
        if df and c.get("deductible") is not None:
            v[df] = amt(c["deductible"])

    if covs.get("coinsurance", {}).get("percent") is not None:
        v[CP + "Premises_CoinsurancePercent_A"] = str(covs["coinsurance"]["percent"])

    fe = covs.get("fungus_exclusion", {})
    fe_details = {k: fe.get(k) for k in ("form", "form_date", "copyright_owner") if fe.get(k)}
    if fe_details and fe.get("response") != "yes":
        raise SystemExit(
            "coverages.fungus_exclusion has form details but response is "
            f"{fe.get('response')!r}. The form only asks for the exclusion form when the answer "
            "is 'yes'; printing a form number beside a 'no' says the opposite of what is meant.")
    for fid, key in [("FormEndorsement_FormIdentifier_A", "form"),
                     ("FormEndorsement_FormDate_A", "form_date"),
                     ("FormEndorsement_CopyrightOwnerCode_A", "copyright_owner")]:
        if fe.get(key):
            v[fid] = fe[key]

    # ---------------------------------------------------------------- wind rows
    for key, f in WIND_ROWS.items():
        c = covs.get(key)
        if not c:
            continue
        incl = c.get("included")
        if incl is not None:
            v[f["incl_yes"] if incl else f["incl_no"]] = ON
        resp = c.get("subject_to_provisions")
        if resp is not None:
            if resp not in RESPONSES:
                raise SystemExit(
                    f"coverages.{key}.subject_to_provisions must be one of {RESPONSES}")
            v[{"yes": f["prov_yes"], "no": f["prov_no"], "na": f["prov_na"]}[resp]] = ON
        if c.get("limit") is not None:
            v[f["limit"]] = amt(c["limit"])
        if c.get("deductible") is not None:
            v[f["deductible"]] = amt(c["deductible"])

    # ------------------------------------------------------- additional interest
    ai = d.get("additional_interest", {}) or {}
    for fid, key in [
        ("AdditionalInterest_FullName_A", "name"),
        ("AdditionalInterest_MailingAddress_LineOne_A", "address1"),
        ("AdditionalInterest_MailingAddress_LineTwo_A", "address2"),
        ("AdditionalInterest_MailingAddress_CityName_A", "city"),
        ("AdditionalInterest_MailingAddress_StateOrProvinceCode_A", "state"),
        ("AdditionalInterest_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ai.get(key):
            v[fid] = ai[key]
    if ai.get("loan_number"):
        v["AdditionalInterest_AccountNumberIdentifier_A"] = ai["loan_number"]
    for interest in ai.get("interests", []):
        fid = INTERESTS.get(interest)
        if not fid:
            raise SystemExit(
                f"interest {interest!r} is not one of {sorted(INTERESTS)} or 'other'. "
                "The interest type determines rights to loss proceeds — guessing is not safe.")
        v[fid] = ON
    if ai.get("other_interest"):
        v["AdditionalInterest_Interest_OtherIndicator_A"] = ON
        v["AdditionalInterest_Interest_OtherDescription_A"] = ai["other_interest"]

    # --------------------------------------------------- lender servicing agent
    # A separate party from the additional interest — the servicer, not the lender.
    la = d.get("lender_servicing_agent", {}) or {}
    for fid, key in [
        ("AdditionalInterest_FullName_B", "name"),
        ("AdditionalInterest_MailingAddress_LineOne_B", "address1"),
        ("AdditionalInterest_MailingAddress_LineTwo_B", "address2"),
        ("AdditionalInterest_MailingAddress_CityName_B", "city"),
        ("AdditionalInterest_MailingAddress_StateOrProvinceCode_B", "state"),
        ("AdditionalInterest_MailingAddress_PostalCode_B", "zip"),
    ]:
        if la.get(key):
            v[fid] = la[key]

    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blank")
    ap.add_argument("data")
    ap.add_argument("outdir")
    ap.add_argument("--flat-only", action="store_true")
    ap.add_argument("--fillable-only", action="store_true")
    a = ap.parse_args()

    d = json.load(open(a.data))
    values = build_values(d)

    spec = FormSpec(sig_field=SIG, prefix="ACORD28", text_boxes={
        LOC_BOX: d.get("location_description", []),
    })

    sig = d.get("producer", {}).get("authorized_representative", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_",
                  d.get("insured", {}).get("name", "Insured")).strip("_")

    render_both(a.blank, values, spec, sig, slug, a.outdir,
                flat_only=a.flat_only, fillable_only=a.fillable_only)

    covs = d.get("coverages", {}) or {}
    answerable = set(TRISTATE) | {"business_income_rental_value", "blanket"} | set(WIND_ROWS)
    unanswered = sorted(answerable - set(covs))
    if unanswered:
        print(f"{len(unanswered)} coverage lines left unanswered (blank on the form): "
              + ", ".join(unanswered))
    ai = d.get("additional_interest", {}) or {}
    if not ai.get("interests") and not ai.get("other_interest"):
        print("WARNING: no interest type checked for the additional interest. "
              "The holder's rights to loss proceeds are undefined on this evidence.")


if __name__ == "__main__":
    main()
