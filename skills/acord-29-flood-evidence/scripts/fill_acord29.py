#!/usr/bin/env python3
"""
Fill an ACORD 29 Evidence of Flood Insurance from flood_data.json.

Usage:
    python3 fill_acord29.py <blank_acord29.pdf> <flood_data.json> <outdir>
                            [--flat-only|--fillable-only]

Produces:
    <outdir>/ACORD29_<insured>_FILLABLE.pdf   AcroForm intact, all fields editable
    <outdir>/ACORD29_<insured>.pdf            flattened, renders anywhere

The form carries three policy blocks: PRIMARY, EXCESS POLICY 1, EXCESS POLICY 2.

ACORD's field suffixes are offset by one between a block's header and its coverage grid:

    block        header fields        coverage grid / form / product
    primary      Policy_*_A           letter suffix _A
    excess_1     ExcessFlood_*_A      letter suffix _B
    excess_2     ExcessFlood_*_B      letter suffix _C

Business income / extra expense / ALE rows exist ONLY on the two excess blocks (suffixes _A
and _B respectively). The primary block has no such row on the form.
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
REMARK_BOX = "Flood_RemarkText_A"
ON = "/1"

# block name -> (letter suffix for the coverage grid, excess header suffix or None,
#                business-income row suffix or None)
BLOCKS = {
    "primary": ("A", None, None),
    "excess_1": ("B", "A", "A"),
    "excess_2": ("C", "B", "B"),
}

MARKET = {"nfip_wyo": "FloodCoverage_NFIPWYOIndicator_{s}",
          "private": "FloodCoverage_PrivateMarketIndicator_{s}"}

POLICY_FORM = {
    "dwelling": "Policy_BroadLineOfBusiness_DwellingIndicator_{s}",
    "general_property": "Policy_BroadLineOfBusiness_GeneralPropertyFormIndicator_{s}",
    "rcbap": "Policy_BroadLineOfBusiness_ResidentialCondominiumAssociationPolicyIndicator_{s}",
}

PRODUCT_TYPE = {
    "standard": "Policy_PolicyType_StandardIndicator_{s}",
    "preferred_risk": "Policy_PolicyType_PreferredRiskIndicator_{s}",
    "other": "Policy_BroadLineOfBusiness_OtherIndicator_{s}",
}

PROGRAMS = {
    "preferred_risk_eligibility_extension":
        "Policy_PolicyType_PreferredRiskEligibilityExtensionIndicator_{s}",
    "group_flood": "Policy_PolicyType_GroupFloodIndicator_{s}",
    "mortgage_portfolio_protection":
        "Policy_BroadLineOfBusiness_MortgagePortfolioProtectionProgramIndicator_{s}",
}

OCCUPANCY = {
    "single_family": "ResidenceOccupancy_OneFamilyIndicator_A",
    "two_to_four_family": "ResidenceOccupancy_TwoToFourFamiliesIndicator_A",
    "other_residential": "ResidenceOccupancy_OtherResidentialIndicator_A",
    "non_residential": "ResidenceOccupancy_NonResidentialIndicator_A",
    "other": "BuildingOccupancy_OtherIndicator_A",
}

CONTENTS_TYPE = {
    "residential": "FloodCoverage_ContentsCoverageType_ResidentialIndicator_A",
    "non_residential": "FloodCoverage_ContentsCoverageType_NonResidentialIndicator_A",
    "other": "FloodCoverage_ContentsCoverageType_OtherIndicator_A",
}

# CONDOMINIUM COVERAGE IS FOR (check one)
CONDO_FOR = {"unit_owner": "FloodInformation_SingleUnitCoverageYesIndicator_A",
             "association_building": "FloodInformation_SingleUnitCoverageNoIndicator_A"}

INTERESTS = {
    "additional_insured": "AdditionalInterest_Interest_AdditionalInsuredIndicator_A",
    "lenders_loss_payable": "AdditionalInterest_Interest_LendersLossPayableIndicator_A",
    "loss_payee": "AdditionalInterest_Interest_LossPayeeIndicator_A",
    "mortgagee": "AdditionalInterest_Interest_MortgageeIndicator_A",
    "unit_owners_mortgagee": "AdditionalInterest_Interest_UnitOwnerMortgageeIndicator_A",
}

# NAMED ON POLICY (check all that apply)
NAMED_ON = {"primary": "AdditionalInterest_AddedToPolicyIndicator_A",
            "excess_1": "AdditionalInterest_AddedToPolicyIndicator_B",
            "excess_2": "AdditionalInterest_AddedToPolicyIndicator_C"}


def amt(x):
    return None if x is None else (money(x) if isinstance(x, (int, float)) else str(x))


def pick(table, key, s, label):
    if key is None:
        return None
    if key not in table:
        raise SystemExit(f"{label} is {key!r}; must be one of {sorted(table)}")
    return table[key].format(s=s)


def build_values(d):
    v = {}
    cert = d.get("certificate", {}) or {}
    v["Form_CompletionDate_A"] = cert.get("issue_date", "")
    for fid, key in [
        ("CertificateOfInsurance_EvidenceNumberIdentifier_A", "evidence_number"),
        ("CertificateOfInsurance_RevisionNumberIdentifier_A", "revision"),
        ("Form_TotalPageNumber_A", "total_pages"),
        ("EvidenceOfProperty_PriorEvidenceDate_A", "prior_evidence_date"),
    ]:
        if cert.get(key) not in (None, ""):
            v[fid] = str(cert[key])

    p = d.get("producer", {}) or {}
    for fid, key in [
        ("Producer_FullName_A", "name"),
        ("Producer_MailingAddress_LineOne_A", "address1"),
        ("Producer_MailingAddress_LineTwo_A", "address2"),
        ("Producer_MailingAddress_CityName_A", "city"),
        ("Producer_MailingAddress_StateOrProvinceCode_A", "state"),
        ("Producer_MailingAddress_PostalCode_A", "zip"),
        ("Producer_ContactPerson_FullName_A", "contact_name"),
        ("Producer_ContactPerson_PhoneNumber_A", "phone"),
        ("Producer_ContactPerson_FaxNumber_A", "fax"),
        ("Producer_ContactPerson_EmailAddress_A", "email"),
        ("Producer_CustomerIdentifier_A", "customer_id"),
        (SIG, "authorized_representative"),
    ]:
        if p.get(key):
            v[fid] = p[key]

    for ins in d.get("insurers", []) or []:
        L = ins.get("letter")
        if L not in ("A", "B", "C"):
            raise SystemExit(
                f"insurer letter {L!r} invalid — the ACORD 29 has three insurer rows, A to C.")
        if ins.get("name"):
            v[f"Insurer_FullName_{L}"] = ins["name"]
        if ins.get("naic"):
            v[f"Insurer_NAICCode_{L}"] = ins["naic"]

    ni = d.get("insured", {}) or {}
    for fid, key in [
        ("NamedInsured_FullName_A", "name"),
        ("NamedInsured_MailingAddress_LineOne_A", "address1"),
        ("NamedInsured_MailingAddress_LineTwo_A", "address2"),
        ("NamedInsured_MailingAddress_CityName_A", "city"),
        ("NamedInsured_MailingAddress_StateOrProvinceCode_A", "state"),
        ("NamedInsured_MailingAddress_PostalCode_A", "zip"),
    ]:
        if ni.get(key):
            v[fid] = ni[key]

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

    # ------------------------------------------------------ coverage / risk info
    r = d.get("risk", {}) or {}
    if r.get("date_of_construction"):
        v["Construction_BuiltDate_A"] = str(r["date_of_construction"])
    if r.get("current_flood_zone"):
        v["FloodCommunity_CurrentFloodZoneCode_A"] = r["current_flood_zone"]
    if r.get("rated_zone"):
        v["FloodCommunity_Rate_FloodZoneCode_A"] = r["rated_zone"]

    gf = r.get("grandfathered")
    if gf not in (None, ""):
        gf = str(gf).upper()
        if gf not in ("Y", "N"):
            raise SystemExit("risk.grandfathered must be 'Y' or 'N' — the form prints the letter.")
        v["FloodCoverage_Building_GrandfatheredCode_A"] = gf

    if r.get("replacement_cost") is not None:
        v["ResidentialStructure_ReplacementCostAmount_A"] = amt(r["replacement_cost"])
    if r.get("unit_count") is not None:
        v["BuildingOccupancy_UnitCount_A"] = str(r["unit_count"])

    fid = pick(CONDO_FOR, r.get("condominium_coverage_for"), "A", "risk.condominium_coverage_for")
    if fid:
        v[fid] = ON

    occ = r.get("building_occupancy")
    fid = pick(OCCUPANCY, occ, "A", "risk.building_occupancy")
    if fid:
        v[fid] = ON
    if occ == "other" and not r.get("occupancy_description"):
        raise SystemExit(
            "risk.building_occupancy is 'other' but no occupancy_description was given. "
            "An unlabeled 'other' box tells the lender nothing.")
    if r.get("occupancy_description"):
        v["BuildingOccupancy_OccupancyDescription_A"] = r["occupancy_description"]

    ct = r.get("contents_coverage_type")
    fid = pick(CONTENTS_TYPE, ct, "A", "risk.contents_coverage_type")
    if fid:
        v[fid] = ON
    if ct == "other" and not r.get("contents_other_description"):
        raise SystemExit(
            "risk.contents_coverage_type is 'other' but no contents_other_description was given.")
    if r.get("contents_other_description"):
        v["FloodCoverage_ContentsCoverageType_OtherDescription_A"] = r["contents_other_description"]

    # -------------------------------------------------------------- policy blocks
    if d.get("excess_1") is None and d.get("excess_2") is not None:
        raise SystemExit(
            "excess_2 is populated but excess_1 is not. Excess flood layers sit above a primary "
            "layer in order; fill EXCESS POLICY 1 first or the form misstates the tower.")
    if d.get("primary") is None and (d.get("excess_1") or d.get("excess_2")):
        raise SystemExit(
            "an excess block is populated but primary is not. Excess flood cannot be evidenced "
            "without the underlying primary policy.")

    for block, (s, hdr, bi_s) in BLOCKS.items():
        b = d.get(block)
        if not b:
            continue

        if b.get("insurer_letter"):
            v[f"Flood_InsurerLetterCode_{s}"] = b["insurer_letter"]

        bld = b.get("building", {}) or {}
        con = b.get("contents", {}) or {}
        if bld.get("deductible") is not None:
            v[f"FloodCoverage_Building_DeductibleAmount_{s}"] = amt(bld["deductible"])
        if bld.get("limit") is not None:
            v[f"FloodCoverage_Building_BasicLimitAmount_{s}"] = amt(bld["limit"])
        if con.get("deductible") is not None:
            v[f"FloodCoverage_Contents_DeductibleAmount_{s}"] = amt(con["deductible"])
        if con.get("limit") is not None:
            v[f"FloodCoverage_Contents_BasicLimitAmount_{s}"] = amt(con["limit"])

        fid = pick(MARKET, b.get("market"), s, f"{block}.market")
        if fid:
            v[fid] = ON
        fid = pick(POLICY_FORM, b.get("policy_form"), s, f"{block}.policy_form")
        if fid:
            v[fid] = ON

        pt = b.get("product_type")
        fid = pick(PRODUCT_TYPE, pt, s, f"{block}.product_type")
        if fid:
            v[fid] = ON
        if pt == "other" and not b.get("product_other_description"):
            raise SystemExit(f"{block}.product_type is 'other' but no product_other_description.")
        if b.get("product_other_description"):
            v[f"Policy_BroadLineOfBusiness_OtherDescription_{s}"] = b["product_other_description"]

        for prog in b.get("programs", []) or []:
            if prog not in PROGRAMS:
                raise SystemExit(f"{block}.programs contains {prog!r}; "
                                 f"must be one of {sorted(PROGRAMS)}")
            v[PROGRAMS[prog].format(s=s)] = ON

        # header: primary uses Policy_*_A; excess blocks use ExcessFlood_*_{hdr}
        if hdr is None:
            if b.get("policy_number"):
                v["Policy_PolicyNumberIdentifier_A"] = b["policy_number"]
            if b.get("effective"):
                v["Policy_EffectiveDate_A"] = b["effective"]
            if b.get("expiration"):
                v["Policy_ExpirationDate_A"] = b["expiration"]
        else:
            if b.get("policy_number"):
                v[f"ExcessFlood_PolicyNumberIdentifier_{hdr}"] = b["policy_number"]
            if b.get("effective"):
                v[f"ExcessFlood_PolicyEffectiveDate_{hdr}"] = b["effective"]
            if b.get("expiration"):
                v[f"ExcessFlood_PolicyExpirationDate_{hdr}"] = b["expiration"]
            if b.get("following_form"):
                v[f"Policy_PolicyType_ExcessFollowingFormIndicator_{hdr}"] = ON

        # business income / extra expense / ALE — excess blocks only
        tl = b.get("time_element", {}) or {}
        if tl and bi_s is None:
            raise SystemExit(
                "primary.time_element was supplied, but the ACORD 29 has no business income / "
                "extra expense / ALE row on the PRIMARY block — only on the excess blocks. "
                "Move it to the excess layer that actually carries it, or state it in remarks.")
        if tl:
            if tl.get("business_income"):
                v[f"FloodCoverage_BusinessIncomeIndicator_{bi_s}"] = ON
            if tl.get("extra_expense"):
                v[f"FloodCoverage_ExtraExpenseIndicator_{bi_s}"] = ON
            if tl.get("additional_living_expense"):
                v[f"FloodCoverage_AdditionalLivingExpenseIndicator_{bi_s}"] = ON
            if tl.get("ale_limit") is not None:
                v[f"FloodCoverage_AdditionalLivingExpense_LimitAmount_{bi_s}"] = amt(tl["ale_limit"])
            if tl.get("actual_loss_sustained"):
                v[f"FloodCoverage_LossSustainedIndicator_{bi_s}"] = ON
                if tl.get("months") is not None:
                    v[f"FloodCoverage_LossSustained_NumberOfMonthsCount_{bi_s}"] = str(tl["months"])

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

    for interest in ai.get("interests", []) or []:
        if interest not in INTERESTS:
            raise SystemExit(
                f"interest {interest!r} is not one of {sorted(INTERESTS)} or 'other'. "
                "The interest type determines rights to loss proceeds — guessing is not safe.")
        v[INTERESTS[interest]] = ON
    if ai.get("other_interest"):
        v["AdditionalInterest_Interest_OtherIndicator_A"] = ON
        v["AdditionalInterest_Interest_OtherDescription_A"] = ai["other_interest"]

    for block in ai.get("named_on", []) or []:
        if block not in NAMED_ON:
            raise SystemExit(f"named_on contains {block!r}; must be one of {sorted(NAMED_ON)}")
        if not d.get(block):
            raise SystemExit(
                f"additional_interest.named_on includes {block!r} but that policy block is empty. "
                "Naming the holder on a policy the form does not describe is a false statement.")
        v[NAMED_ON[block]] = ON

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

    spec = FormSpec(sig_field=SIG, prefix="ACORD29", text_boxes={
        LOC_BOX: d.get("location_description", []),
        REMARK_BOX: d.get("remarks", []),
    })

    sig = d.get("producer", {}).get("authorized_representative", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_",
                  d.get("insured", {}).get("name", "Insured")).strip("_")

    render_both(a.blank, values, spec, sig, slug, a.outdir,
                flat_only=a.flat_only, fillable_only=a.fillable_only)

    used = [b for b in BLOCKS if d.get(b)]
    print("policy blocks filled: " + (", ".join(used) if used else "NONE"))
    ai = d.get("additional_interest", {}) or {}
    if not ai.get("named_on"):
        print("WARNING: no NAMED ON POLICY box checked. The lender cannot tell which layer "
              "of the flood tower they are named on.")
    if not ai.get("interests") and not ai.get("other_interest"):
        print("WARNING: no interest type checked for the additional interest.")


if __name__ == "__main__":
    main()
