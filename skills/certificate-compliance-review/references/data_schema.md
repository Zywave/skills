# coi_data.json — shared data contract

Both the **acord-25-new-coi** and **certificate-compliance-review** skills read and write this
one file. Skill 1 creates it during extraction and uses it to fill the ACORD 25. Skill 2 reads
it to build the compliance workbook, and appends its findings back into it.

Keeping a single structured artifact between the two skills means the compliance review never
re-reads the source PDFs and never disagrees with the certificate about what the policies say.
If the two ever disagree, the extraction is wrong — fix it here, then regenerate both outputs.

Write it to the working directory as `coi_data.json`.

---

## Top-level shape

```json
{
  "meta": { ... },
  "certificate": { ... },
  "producer": { ... },
  "insured": { ... },
  "certificate_holder": { ... },
  "insurers": [ ... ],
  "policies": { ... },
  "contract": { ... },
  "description_of_operations": [ ... ]
}
```

---

## meta

```json
"meta": {
  "specimen": true,
  "source_documents": ["contract.pdf", "request_email.txt", "gl_policy.pdf", "wc_policy.pdf"],
  "extracted_on": "2026-08-11"
}
```

`specimen` controls whether a SPECIMEN disclaimer is stamped into the Description of Operations
and the PDF metadata. Set it `false` only for a live certificate the agency is genuinely issuing.

---

## certificate

```json
"certificate": {
  "number": "COI-2026-04417",
  "revision": "0",
  "issue_date": "08/11/2026"
}
```

`issue_date` is **today's date** in MM/DD/YYYY unless the user names a different one. Get it from
the system rather than copying a date out of a source document — a certificate is dated when it
is issued, not when the contract was signed.

---

## producer, insured, certificate_holder

All three use the same address shape:

```json
"producer": {
  "name": "Zywave AI Demo Agency",
  "address1": "10100 W. Innovation Drive",
  "address2": "Suite 300",
  "city": "Wauwatosa", "state": "WI", "zip": "53226",
  "contact_name": "Certificate Services",
  "phone": "(262) 555-0140",
  "fax": "(262) 555-0141",
  "email": "certificates@zywaveaidemoagency.example",
  "authorized_representative": "Brett Cleveringa"
}
```

```json
"certificate_holder": {
  "name": "ABC Company",
  "address1": "Attn: Risk Management",
  "address2": "1150 Corporate Center Drive, Suite 400",
  "city": "Naperville", "state": "IL", "zip": "60563",
  "verbatim_source": "Subcontract Section 9.7",
  "verbatim_match": true
}
```

`verbatim_source` records where the required holder wording came from. `verbatim_match` is your
assertion that what you entered matches it character for character. Holders reject certificates
over this constantly, so if the contract specifies wording, copy it rather than normalizing it.

---

## insurers

One entry per carrier, letter A–F in the order they appear on the form.

```json
"insurers": [
  {"letter": "A", "name": "Northgate Specialty Insurance Company",
   "naic": "99017", "am_best": "A IX", "admitted_states": []}
]
```

Leave `am_best` and `admitted_states` empty if the declarations don't state them — an empty value
is a finding for the compliance review, and inventing one destroys the whole point of the review.

---

## policies

Keys: `general_liability`, `automobile`, `umbrella`, `workers_comp`, `other`.

**Set a key to `null` when no policy exists.** This is load-bearing. `null` means "no such policy
in force," which is a completely different statement from "policy exists but we didn't extract
the limits," and the compliance review treats them differently.

### general_liability

```json
"general_liability": {
  "insurer_letter": "A",
  "policy_number": "NGS-GL-4471982",
  "effective": "03/01/2026",
  "expiration": "03/01/2027",
  "form_basis": "occurrence",
  "additional_insured": "Y",
  "subrogation_waived": "Y",
  "aggregate_applies": "project",
  "limits": {
    "each_occurrence": 1000000,
    "damage_rented_premises": 100000,
    "med_exp": 10000,
    "personal_adv_injury": 1000000,
    "general_aggregate": 2000000,
    "products_completed_ops": 2000000
  },
  "deductible": {"amount": 5000, "basis": "per occurrence, property damage only"},
  "endorsements": [
    {"form": "CG 20 10", "edition": "04 13",
     "title": "Additional Insured — Owners, Lessees or Contractors (Ongoing Operations)",
     "scope": "ongoing operations only",
     "schedule": "ABC Company, its parent, subsidiaries and affiliates"}
  ]
}
```

`form_basis` is `occurrence` or `claims_made`. `aggregate_applies` is `policy`, `project`, `loc`,
or `other`.

`scope` on an endorsement is where the important detail lives. A CG 20 10 grants additional
insured status for ongoing operations only — record that limitation explicitly, because the
ADDL INSD column on the ACORD 25 is a single Y/N box that cannot express it.

### workers_comp

```json
"workers_comp": {
  "insurer_letter": "B",
  "policy_number": "RMC-WC-0093714",
  "effective": "03/01/2026",
  "expiration": "03/01/2027",
  "per_statute": true,
  "states": ["WI", "IL"],
  "other_states": "All except ND, OH, WA, WY",
  "subrogation_waived": "Y",
  "any_excluded": "N",
  "limits": {
    "el_each_accident": 1000000,
    "el_disease_each_employee": 1000000,
    "el_disease_policy_limit": 1000000
  },
  "endorsements": [
    {"form": "WC 00 03 13", "edition": "",
     "title": "Waiver of Our Right to Recover From Others",
     "scope": "blanket, WI and IL"}
  ]
}
```

### automobile

```json
"automobile": {
  "insurer_letter": "C",
  "policy_number": "...", "effective": "...", "expiration": "...",
  "covered_autos": ["any_auto"],
  "additional_insured": "Y", "subrogation_waived": "Y",
  "limits": {
    "combined_single_limit": 1000000,
    "bodily_injury_per_person": null,
    "bodily_injury_per_accident": null,
    "property_damage_per_accident": null
  },
  "endorsements": []
}
```

`covered_autos` values: `any_auto`, `owned`, `scheduled`, `hired`, `non_owned`.

### umbrella

```json
"umbrella": {
  "insurer_letter": "D",
  "policy_type": "umbrella",
  "form_basis": "occurrence",
  "policy_number": "...", "effective": "...", "expiration": "...",
  "additional_insured": "Y", "subrogation_waived": "Y",
  "limits": {"each_occurrence": 5000000, "aggregate": 5000000},
  "retention": {"type": "retention", "amount": 10000},
  "endorsements": []
}
```

`policy_type` is `umbrella` or `excess`. `retention.type` is `deductible` or `retention`.

---

## contract

The requirements side. Each requirement is one row of the compliance matrix.

```json
"contract": {
  "agreement_number": "ABC-SC-2026-0417",
  "project": "Riverside Distribution Center — Phase II Interior Buildout",
  "project_address": "8875 Riverside Commerce Way, Aurora, IL 60502",
  "term_start": "04/06/2026",
  "term_end": "12/18/2026",
  "carrier_rating_floor": "A- VII",
  "cancellation_notice_days": 30,
  "deductible_disclosure_threshold": 25000,
  "completed_ops_tail_years": 2,
  "request": {
    "requested_by": "Daniel Reyes, Contracts Administrator, ABC Company",
    "requested_on": "03/30/2026",
    "deadline": "04/02/2026",
    "mobilization_date": "04/06/2026",
    "holder_flagged_concerns": ["..."]
  },
  "requirements": [
    {
      "id": "GL-01",
      "coverage": "General Liability",
      "requirement": "Each occurrence limit",
      "contract_ref": "Ex. C",
      "required_text": "$1,000,000",
      "required_amount": 1000000,
      "evidence_source": "NGS-GL-4471982 Sec. I",
      "actual_text": "$1,000,000",
      "actual_amount": 1000000,
      "met": "",
      "severity": "Low",
      "action": ""
    }
  ]
}
```

**Field rules for requirements:**

- `id` — prefix by coverage: `GL-`, `AU-`, `WC-`, `EL-`, `UM-`, `GN-` (general/administrative).
- `required_amount` / `actual_amount` — populate **both** only for numeric limit comparisons. The
  workbook derives status by comparing them. Leave both `null` for anything qualitative.
- `met` — `Y`, `N`, or `PARTIAL`. Only used when the amounts are `null`. Leave empty on numeric rows.
- `severity` — `Critical`, `High`, `Medium`, or `Low`. Critical means it blocks issuance or
  mobilization. Low is the normal value for a requirement that passes.
- `action` — leave empty when compliant. When not compliant, say what specifically to request
  and from whom, not just that something is missing.

---

## description_of_operations

An array of paragraphs for the ACORD 25 remarks box. Skill 1 generates these; they are stored so
the compliance review can confirm the certificate actually disclosed each gap.

```json
"description_of_operations": [
  "RE: Agreement No. ABC-SC-2026-0417 - Riverside Distribution Center Phase II...",
  "GENERAL LIABILITY: The certificate holder ... ONGOING OPERATIONS ONLY per CG 20 10 04 13..."
]
```
