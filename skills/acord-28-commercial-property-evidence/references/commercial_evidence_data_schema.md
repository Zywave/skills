# commercial_evidence_data.json — data contract

The extraction artifact for the ACORD 28. Closest sibling is `evidence_data.json` (ACORD 27),
but the coverage section is entirely different: instead of ten free-form rows, the ACORD 28 is a
fixed **Yes / No / N/A questionnaire**.

Write it to the working directory as `commercial_evidence_data.json`.

```json
{
  "meta": { ... },
  "certificate": { "issue_date": "08/19/2026" },
  "producer": { ... },
  "insurer": { ... },
  "insured": { ... },
  "policy": { ... },
  "location": { ... },
  "location_description": [ ... ],
  "coverages": { ... },
  "additional_interest": { ... },
  "lender_servicing_agent": { ... }
}
```

---

## The three answers, and why they differ

Every line in `coverages` takes a `response` of `"yes"`, `"no"`, or `"na"`:

- **`yes`** — the coverage or condition is in force
- **`no`** — it is **not** in force. An affirmative negative statement.
- **`na`** — the question does not apply to this policy or location

**`no` and `na` are not interchangeable, and neither is the same as omitting the line.**
A lender reading `N/A` beside flood on a Zone AE building learns nothing. `No` tells them the
exposure is uninsured. An unanswered line tells them less than either, and the script reports
which lines you left blank so you can decide deliberately rather than by accident.

An unrecognized `response` aborts the fill. There is no default.

---

## meta, certificate, producer, insurer, insured

Largely as `evidence_data.json`, with these differences:

- **`producer.contact_name`** is used here. The ACORD 28 has a contact-name box; the 27 does not.
- **`insurer.naic`** is used here. The 27 has no NAIC box.
- **`insured.additional_named_insured`** fills the ADDITIONAL NAMED INSURED(S) box — a separate
  entity, commonly the operating company where the property sits in a real-estate LLC.

`certificate.issue_date` is today in MM/DD/YYYY, read from the system.

## policy

```json
"policy": {
  "type": "COMMERCIAL PROPERTY - SPECIAL FORM",
  "policy_number": "NGS-CP-8841027",
  "effective": "03/01/2026",
  "expiration": "03/01/2027",
  "continued_until_terminated": false,
  "perils": ["special"],
  "other_peril": "",
  "covers": {"building": true, "business_personal_property": true},
  "limit": 16700000,
  "deductible": 25000,
  "prior_evidence_date": ""
}
```

- `type` — free text for the TYPE OF POLICY box.
- `perils` — any of `basic`, `broad`, `special`. Only what the policy provides.
- `covers` — the BUILDING **OR** BUSINESS PERSONAL PROPERTY heading. Both may be true.
- `limit` / `deductible` — the COMMERCIAL PROPERTY COVERAGE AMOUNT OF INSURANCE row.
- `continued_until_terminated` — set `true` **and omit `expiration`**. Both aborts the fill.
- `prior_evidence_date` — fills THIS REPLACES PRIOR EVIDENCE DATED, for a reissue.

## location

```json
"location": {"address1": "8875 Riverside Commerce Way", "address2": "",
             "city": "Aurora", "state": "IL", "zip": "60502"}
```

No county field on this form. `location_description[]` feeds the LOCATION / DESCRIPTION box
(~24pt, two to three lines) — construction, square footage, year built, protection.

---

## coverages

### Simple tri-state lines

```json
"terrorism": {"response": "yes"},
"terrorism_exclusion": {"response": "no"},
"domestic_terrorism_exclusion": {"response": "no"},
"replacement_cost": {"response": "yes"},
"agreed_value": {"response": "yes"},
"subrogation_waiver": {"response": "yes"}
```

### Tri-state with limit and deductible

```json
"limited_fungus": {"response": "yes", "limit": 15000, "deductible": 25000},
"equipment_breakdown": {"response": "yes", "limit": 16700000, "deductible": 25000},
"ordinance_undamaged_portion": {"response": "yes", "limit": "INCLUDED", "deductible": 25000},
"ordinance_demolition": {"response": "yes", "limit": 1000000, "deductible": 25000},
"ordinance_increased_cost": {"response": "yes", "limit": 1000000, "deductible": 25000},
"earth_movement": {"response": "no"},
"flood": {"response": "no"}
```

Integers get separators; pass a **string** for anything non-numeric (`"INCLUDED"`,
`"2% OF TIV"`, `"5% NAMED STORM"`).

### coinsurance

```json
"coinsurance": {"response": "no", "percent": null}
```

`percent` prints in the IF YES ___% box. Supply it only with a `yes` response.

### fungus_exclusion

```json
"fungus_exclusion": {"response": "yes", "form": "CP 01 40", "form_date": "07 06",
                     "copyright_owner": "ISO"}
```

The form asks which exclusion form is used **only if the answer is yes**. Supplying `form`,
`form_date` or `copyright_owner` alongside a `no` response aborts the fill — a form number
printed beside "No" reads as the opposite of what was meant.

### business_income_rental_value

```json
"business_income_rental_value": {
  "response": "yes",
  "business_income": true,
  "rental_value": false,
  "limit": 3000000,
  "actual_loss_sustained": true,
  "months": 12
}
```

`business_income` and `rental_value` are the two sub-checkboxes indicating which applies.
`actual_loss_sustained` with `months` fills the ALS box and month count.

### wind_hail and named_windstorm

Two questions on one row, both explicit:

```json
"wind_hail": {"included": true, "subject_to_provisions": "yes",
              "limit": "INCLUDED", "deductible": "2% OF TIV"},
"named_windstorm": {"included": true, "subject_to_provisions": "yes",
                    "limit": "INCLUDED", "deductible": "5% OF TIV"}
```

- `included` — boolean, is the peril covered at all
- `subject_to_provisions` — tri-state, does it carry different provisions (a separate
  deductible or sublimit) than the rest of the policy

These are independent. A peril can be included and not subject to different provisions, or
excluded outright. Answer both.

### blanket

```json
"blanket": {"response": "yes", "value": 16700000}
```

`value` is the value reported on the property identified above.

---

## additional_interest

The party with an interest in the property.

```json
"additional_interest": {
  "name": "First Meridian Bank, ISAOA/ATIMA",
  "address1": "Attn: Loan Servicing", "address2": "400 N LaSalle Street, Suite 1200",
  "city": "Chicago", "state": "IL", "zip": "60654",
  "interests": ["mortgagee", "lenders_loss_payable"],
  "other_interest": "",
  "loan_number": "FMB-CRE-2026-0918"
}
```

`interests` — one or more of `contract_of_sale`, `lenders_loss_payable`, `loss_payee`,
`mortgagee`. Note `contract_of_sale` exists here and not on the ACORD 27. An unrecognized value
aborts the fill.

**Get the interest type right.** Mortgagee and lender's loss payable protect the holder's
interest even when the insured's own act or neglect would void coverage. **Loss payee grants
payment rights only, with no such protection.** Substituting it quietly strips the lender.
Read the loan document.

## lender_servicing_agent

```json
"lender_servicing_agent": {
  "name": "Midwest Commercial Loan Servicing, Inc.",
  "address1": "2200 Corporate Ridge Parkway, Suite 700",
  "city": "Overland Park", "state": "KS", "zip": "66210"
}
```

A **separate company** from the additional interest — the servicer, and where notices actually
go. Commercial loans are frequently sold and serviced by a third party. Do not fill it with a
copy of the lender; omit it entirely if there is no servicing agent.

---

## No remarks box

Unlike the ACORD 24, 25 and 27, **the ACORD 28 has no remarks or special conditions box.** The
questionnaire is the disclosure. That means:

- Every gap has to be expressed as a `no` answer on the right line
- Anything the questionnaire cannot express goes on an attached ACORD 101, referenced in
  `location_description` if it will fit
- There is no red-warning mechanism on this form, so the chat report back to the producer
  carries more weight — say plainly which requirements the evidence fails
