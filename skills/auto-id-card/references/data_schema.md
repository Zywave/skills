# autoid_data.json

The contract between extraction and `fill_autoid.py`. Build this file, then fill from it.

Splitting extraction from filling is what makes the validation step possible: the user reviews
this structure, not a PDF, and a correction here costs one edit instead of a reissue.

```json
{
  "meta": {
    "specimen": false,
    "source_document": "Declarations page, Westfield policy BA-7719440-02, dated 10/01/2026",
    "form_title": "ACORD 50 IL - Illinois Insurance Identification Card",
    "content_id": 239293,
    "form_file": "ACORD 0050 IL 2024-11 Acroform.pdf"
  },
  "insured": {
    "name": "NORTHSHORE MECHANICAL CONTRACTORS LLC",
    "address_line_1": "4400 W CANAL ST",
    "address_line_2": "",
    "city": "MILWAUKEE",
    "state": "WI",
    "zip": "53208"
  },
  "carrier": { "name": "WESTFIELD NATIONAL INSURANCE COMPANY", "naic": "24112" },
  "producer": {
    "name": "HILB GROUP OF WISCONSIN",
    "address_line_1": "200 S EXECUTIVE DR",
    "city": "BROOKFIELD", "state": "WI", "zip": "53005",
    "phone": "262-555-0140"
  },
  "policy": {
    "number": "BA-7719440-02",
    "effective_date": "10/01/2026",
    "expiration_date": "10/01/2027",
    "line_of_business": "commercial",
    "fleet": false
  },
  "routing": {
    "state": "IL",
    "state_name": "ILLINOIS",
    "basis": "garaging",
    "fallback": false
  },
  "vehicles": [
    { "year": "2023", "make": "FORD", "model": "F-150",
      "vin": "1HGCM82633A004352", "garaging_state": "IL" }
  ]
}
```

## Optional keys for state-specific fields

Most cards need nothing beyond the block above. A handful of state forms ask for one or two
more things, and those things are never on a dec page. The producer has them, so the fill
script names each unanswered one and says what to ask for. Add only the keys a form asks for.

| Key | Goes on | What it is |
|---|---|---|
| `policy.registered_owner` | ACORD 52 NV and other fleet cards | Registered owner when the FLEET box is checked. Defaults to the insured's name if `policy.fleet` is true. A vehicle-level `registered_owner` overrides it. |
| `vehicles[].plate` | ACORD 50 WV | License plate number |
| `vehicles[].body_type` | Forms with a body code field | Body type code |
| `vehicles[].additional_interest` | ACORD 50 WV | Lienholder or lessor name |
| `vehicles[].excluded_driver` | IL, ME x2, MI, OK, AR, LA | `{"surname": "", "given_name": "", "middle_initial": ""}` for a named-driver exclusion |
| `vehicles[].pip` | ACORD 50 FL | `true` if PIP is in force |
| `vehicles[].bodily_injury` | ACORD 50 FL | `true` if BI is in force |
| `vehicles[].named_driver` | ACORD 50 TX | `true` for a named-driver policy |
| `carrier.adot_code` | ACORD 50 AZ | Carrier's Arizona DOT code |
| `carrier.state_id` | Forms with a state ID field | Carrier's state identification number |
| `carrier.claims_phone` | ACORD 50 WV | Claims reporting number |
| `carrier.medical_treatment_contact` | ACORD 50 and 51 NJ | `{"name","address_line_1","city","state","zip","fax","email"}` |
| `remark` | Countrywide ACORD 50 | Free text the carrier or a state requires |

The script rejects keys it does not recognize rather than dropping them quietly, so a typo
surfaces instead of turning into a blank field nobody notices.

## Field notes

`meta.specimen`: `true` for demo, training, or test data. Set it `false` only for cards an
agency is genuinely issuing. Test output that can pass for a real card is a liability.

`meta.source_document`: name the document and its date. This is what the skill reports back,
and it is the honest limit of what a card can claim: a dec page states coverage as of its own
date and can be superseded by endorsement.

`policy.line_of_business`: `commercial` or `personal`. Drives the checkbox. Both are left
clear if the document does not say, rather than guessed.

`routing.basis`: `garaging` or `mailing`, whichever the state code came from. Say which in the
report. They differ often on commercial accounts.

`routing.fallback`: `true` when the state has no card of its own and the countrywide ACORD 50
is being used. Surfaced to the user, because that fallback is inferred from library contents
rather than a verified filing rule.

`vehicles[].vin`: validated against the position-9 check digit before anything is written.
Set `"vin_override": true` on a vehicle to issue past a failure, which is the right escape
hatch for a pre-1981 or imported vehicle whose VIN does not carry a check digit.

`vehicles[].garaging_state`: per vehicle, because a fleet can span states. Group by this value
and run once per state.

## What to leave out

Omit a key rather than inventing a value. An empty field on a card is a visible gap the producer
can fix. A plausible wrong value is not.

`fill_autoid.py` prints any element you supplied that the form does not carry, so extra keys are
safe. Florida's card, for instance, has no NAIC code and no producer block at all.
