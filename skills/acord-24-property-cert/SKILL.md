---
name: acord-24-property-cert
description: Issue an ACORD 24 Certificate of Property Insurance from a certificate request. Takes a loan agreement or lease plus the insured's property policies, pulls the blank ACORD 24 from the Zywave content library, compares coverage against the requirements, and produces a filled certificate — fillable and flattened — dated today and signed. Use this whenever someone asks for a property certificate, an ACORD 24, evidence of property insurance, or proof of coverage for a building; whenever a lender, mortgagee, loss payee, landlord, or property manager requests a certificate; or whenever they mention mortgagee clauses, ISAOA/ATIMA, loss payee status, blanket property limits, or evidence of flood or equipment breakdown coverage. Use it even if they only say "handle this property cert request." For liability certificates use acord-25-new-coi; for single-property lender evidence use acord-27-property-evidence.
---

# ACORD 24 Property Certificate

Issue an ACORD 24 from a property certificate request.

A property certificate is a statement to a lender or landlord about what coverage exists on a
specific building. The reader is usually making a funding or occupancy decision on it. The
single most important property of the output is that **every statement on it is true** —
particularly the peril checkboxes, because earthquake and flood are commonly required and
commonly excluded, and a checked box the policy doesn't support is a direct E&O exposure.

Accuracy beats completeness. A certificate showing three of five required coverages, with the
gaps disclosed in red, is correct. One showing five when only three exist is not.

## Workflow

1. Collect the inputs
2. Extract into `property_data.json`
3. Resolve and pull the blank ACORD 24 from Zywave
4. Compare coverage to requirements, and write the disclosures
5. Fill, sign, and deliver
6. Report the gaps in chat

---

## 1. Collect the inputs

| Input | What it gives you |
|---|---|
| Loan agreement / lease / requirements exhibit | Required limits, valuation basis, mortgagee wording, flood and quake requirements, carrier rating floor |
| Certificate request email | Who is asking, deadline, loan number, closing date |
| Property policy documents (dec pages) | What coverage actually exists |

Missing pieces are workable but change what you can promise:

- **No loan agreement or lease** — you can issue from the policy, but you cannot verify
  compliance or write meaningful disclosures. Say so and ask for the requirements section.
- **No request email** — fine. Take holder details from the loan document.
- **A coverage line with no policy document** — this means no such policy is in force. Leave
  the section blank; do not guess.

Ask before proceeding only when the certificate holder is genuinely unidentifiable, or when
the request doesn't identify which location it covers and the insured has several. Everything
else you can flag in the output.

---

## 2. Extract into property_data.json

Read `references/property_data_schema.md` and build `property_data.json` in the working
directory.

Extraction rules that matter here:

- **Set a policy key to `null` when no policy exists.** Not `{}`, not a stub. `null` is what
  makes the fill script leave the whole section blank.
- **Only list a peril the policy actually covers.** `perils: ["special"]` on a special-form
  policy with no quake or flood endorsement. Do not add `flood` because the loan requires it —
  the requirement belongs in the remarks as a gap, not in a checkbox as a false assurance.
- **Get the blanket type right.** `building`, `personal_property`, or `building_and_pp`. The
  script aborts on anything else rather than printing a limit on the wrong line.
- **Copy mortgagee wording verbatim,** including ISAOA/ATIMA and the attention line.
- **Leave unknown values empty.** An empty A.M. Best rating is a finding. An invented one is a
  false assurance.

Set `certificate.issue_date` to today, read from the system. Set `meta.specimen` to `true` for
demo or training data.

---

## 3. Resolve and pull the blank ACORD 24 from Zywave

| | |
|---|---|
| Form | ACORD 24 — Certificate of Property Insurance |
| Exact library title | `ACORD 24 - Certificate of Property Insurance` |
| Content ID, last verified 2026-09-10 | `239000` |
| Edition this field map was built against | 2016/03 |

**Resolve the form by title, then verify the ID.** `content_search` does index these forms and
does return them by form number. Search is the lookup; the content ID above is the cross-check,
not the other way round. The ID is a Zywave library identifier and can move when content is
re-indexed or a new edition is loaded. The form number never changes — ACORD 24 is always the
Certificate of Property Insurance — which is what makes the title a safe key.

```
Zywave:content_search(query="ACORD 24 certificate of property insurance form")
```

Resolve the result in this order. Do not skip ahead to the download.

1. **Match the title exactly** — `ACORD 24 - Certificate of Property Insurance`. Do not take the
   highest-scoring result.
   Relevance scores tie between sibling forms: a search for ACORD 27 returns ACORD 27 and
   ACORD 28 at identical scores, so rank alone will hand you the wrong form. Exact title is the
   only safe selector.
2. **Ignore duplicate rows.** The same form comes back more than once with different scores.
   Distinct `contentId` values are what matter, not the row count.
3. **Cross-check the resolved ID against the table above.** If it matches, proceed. If it
   differs, the library has been re-indexed or a new edition loaded — proceed with the ID search
   returned, and say so in chat, because the field map may no longer apply.
4. **If nothing matches the title exactly**, fall back to `contentId=239000` and verify hard at
   step 6. Do not settle for a near-miss title: ACORD 20, 21, 23, 25, 26 and 30 are different forms,
   not variants of this one.

```
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

That returns a presigned `downloadUrl`. Download it to the working directory as `acord24.pdf`.
Some search results also carry a `fileDownloadUrl` and some do not, so `content_download` is the
reliable path.

Three checks before filling:

5. Confirm the download is a real PDF (`file acord24.pdf`). An expired presigned URL returns an
   error page, not a form.
6. **Confirm the returned `fileName` contains "ACORD 24."** A wrong content ID returns a
   *different form*, not an error — without this check an agent will fill an ACORD 25 with
   property data and produce a document that looks finished and is false.
7. `fill_acord24.py` validates every field name and aborts on a mismatch. That is the last
   gate, not the first. If title and filename were both right and field validation still fails,
   the library holds a **newer edition** than the 2016/03 this map was built against. Stop and
   report that. Do not edit the field map to make the run pass.

Carry the resolved content ID, the returned `fileName` and the edition into what you report in
chat, so an issued form can be traced to the exact artifact it was built from.

---

## 4. Compare, then write the disclosures

Walk each requirement in the loan agreement or lease against what the policy provides. The
comparison drives which boxes get checked and what the remarks say.

The peril checkboxes are the crux. They are coarse — a single box for FLOOD cannot express
"flood is covered at $500,000 against a $14.5M building in Zone AE." When coverage exists but
falls short, check the box and state the shortfall in the remarks. When it doesn't exist, leave
the box clear and open a `***` paragraph.

Build `remarks` as an array of paragraphs covering, in order:

1. **Loan or agreement reference** and the holder's interest, with the endorsement granting it
2. **Valuation and form basis** — replacement cost, agreed value, coinsurance waiver, blanket
3. **Coverages not provided** that the agreement requires — one `***` paragraph each, naming
   the requirement it fails
4. **Separately-carried coverages** and which policy holds them

Put the property description in `location_description`, not `remarks` — they are two different
boxes on the form and the description box is small.

---

## 5. Fill, sign, deliver

```bash
python3 scripts/fill_acord24.py acord24.pdf property_data.json <output_dir>
```

Produces:

- `ACORD24_<insured>_FILLABLE.pdf` — AcroForm intact, every field editable
- `ACORD24_<insured>.pdf` — flattened, renders identically in any viewer

The script generates an explicit appearance stream for every populated field and sets
`NeedAppearances = false`, so the fillable copy renders correctly everywhere rather than
depending on viewer behaviour. It prints which sections it left blank — check that list against
your extraction before delivering.

The authorized-representative signature is drawn as vector outlines via `scripts/signature.py`,
so it embeds with no font dependency. **It is a graphic, not an e-signature** — no identity
verification, no audit trail, no tamper-evidence. That is the correct model for certificates,
but if asked whether it is legally binding, the honest answer is that its authority comes from
the agency's issuance controls, not from the mark.

Deliver both files with `present_files`.

---

## 6. Report the gaps

Do not deliver silently. In chat, state:

- Which sections were completed and which were left blank, and why
- Every requirement the certificate does not satisfy — especially flood and earthquake
- Anything you assigned or assumed

If the certificate doesn't satisfy the loan requirements, say so directly rather than letting
the PDF speak for itself. A lender discovering a flood gap at closing is a much worse outcome
than a phone call today.

---

## Failure modes worth avoiding

**Checking a peril the policy doesn't cover.** The most damaging error on this form. Flood and
earthquake especially — they are the two the lender is looking for.

**Mapping a blanket limit to the wrong line.** A building-and-contents blanket shown on the
BLANKET BUILDING line understates what is blanketed. The script enforces named types; don't
work around it.

**Putting the property description in the remarks box.** Two different fields. The upper box is
`RemarkText_A`, the lower is `RemarkText_B`, and both carry a
`CertificateOfLiabilityInsurance_` prefix despite this being a property form.

**Normalizing the mortgagee's name.** ISAOA/ATIMA and the exact entity name are copied, not
tidied.

**Dating the certificate from the loan document.** Use today.

**Trusting a renderer that shows a blank form.** If verifying with pypdfium2, call
`pdf.init_forms()` and render with `may_draw_forms=True`, or form fields won't be drawn and you
will "fix" a file that was never broken.

---

## Bundled resources

- `references/property_data_schema.md` — the `property_data.json` contract. Read before extracting.
- `references/acord24_field_map.md` — all 144 ACORD 24 field names mapped to schema paths. Read
  when a field won't populate or when the form revision changes.
- `scripts/fill_acord24.py` — mapping and CLI.
- `scripts/acord_fill.py` — shared fill engine. Also used by the ACORD 27, 28 and 29 skills;
  keep changes backward-compatible.
- `scripts/signature.py` — vector signature renderer, shared with acord-25-new-coi.

## Related skills

- **acord-25-new-coi** — ACORD 25, liability certificates. Same header block and data shape.
- **certificate-compliance-review** — reads `coi_data.json`; the property equivalent is not yet
  wired up, so compliance findings for the ACORD 24 stay in chat for now.
