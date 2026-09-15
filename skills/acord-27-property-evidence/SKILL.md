---
name: acord-27-property-evidence
description: Issue an ACORD 27 Evidence of Property Insurance from a lender or mortgagee request. Takes a mortgage commitment or loan agreement plus the insured's property policy, pulls the blank ACORD 27 from the Zywave content library, and produces a filled evidence form — fillable and flattened — dated today and signed. Use this whenever a mortgage lender, loan servicer, escrow officer, or title company asks for evidence of property insurance, an ACORD 27, proof of hazard insurance, or binder confirmation ahead of a closing or loan funding; whenever a mortgagee, loss payee, or lender's loss payable interest must be evidenced on a dwelling or single property; or whenever they mention hazard insurance verification, ISAOA/ATIMA, escrow insurance requirements, or replacing a prior evidence. Use it even if they only say "the lender needs proof of insurance." For commercial property with multiple coverage lines use ACORD 28 or 24; for liability use acord-25-new-coi.
---

# ACORD 27 Evidence of Property Insurance

Issue an ACORD 27 from a lender or mortgagee request.

An evidence of property insurance is read by someone deciding whether to fund a loan or close a
sale. Two things on it carry the most weight: **the interest type checked in the additional
interest block**, which determines the holder's rights to loss proceeds, and **whether the
coverage rows say what the loan actually requires**. Both are easy to get subtly wrong and
neither error is visible to the reader.

Accuracy beats completeness. An evidence showing the coverages that exist, with the gaps
disclosed in red, is correct. One padded to look compliant is not.

## Scope — is this the right form?

| Situation | Form |
|---|---|
| One policy, one property, lender needs hazard evidence | **ACORD 27** — this skill |
| Commercial property, multiple coverage lines (property + IM + crime + boiler) | ACORD 24 — `acord-24-property-cert` |
| Commercial property evidence for a lender | ACORD 28 |
| Liability certificate for a GC or contract | ACORD 25 — `acord-25-new-coi` |

If the request involves several coverage lines each with their own policy, stop and use the
ACORD 24. Forcing them into the ACORD 27's ten free-form rows loses the line-level structure
the reader expects.

## Workflow

1. Collect the inputs
2. Extract into `evidence_data.json`
3. Resolve and pull the blank ACORD 27 from Zywave
4. Determine the interest type, and write the disclosures
5. Fill, sign, and deliver
6. Report the gaps in chat

---

## 1. Collect the inputs

| Input | What it gives you |
|---|---|
| Mortgage commitment / loan agreement | Required coverage, mortgagee wording, interest type, loan number, closing date |
| Request email | Who is asking, deadline, whether it replaces a prior evidence |
| Property policy (dec page) | What coverage actually exists |

Missing pieces are workable but change what you can promise:

- **No loan document** — you can issue from the policy, but you are guessing at the interest
  type and cannot verify compliance. Ask for the commitment or the insurance requirements
  section; do not default to `mortgagee`.
- **A required coverage with nothing in the policy** — leave it out of the rows and disclose it
  in the remarks. Do not write a row for coverage that does not exist.

Ask before proceeding when the loan document doesn't state the interest type, or when the
insured owns several properties and the request doesn't identify which one.

---

## 2. Extract into evidence_data.json

Read `references/evidence_data_schema.md` and build `evidence_data.json` in the working
directory.

Extraction rules that matter here:

- **The property location is not the mailing address.** Rentals, second homes and
  LLC-held property routinely differ. Take the location from the dec page's insured-premises
  section, not the insured's address block.
- **Use strings for non-numeric limits and deductibles.** `"INCLUDED"`, `"1% OF COV A"`,
  `"2% NAMED STORM"`. Forcing a percentage deductible into a number loses the basis.
- **`continuous_until_cancelled` and `expiration` are mutually exclusive.** Set one.
- **Leave unknown values empty.** An empty field is a finding; an invented one is a false
  assurance.

Set `certificate.issue_date` to today, read from the system. Set `meta.specimen` to `true` for
demo or training data.

---

## 3. Resolve and pull the blank ACORD 27 from Zywave

| | |
|---|---|
| Form | ACORD 27 — Evidence of Property Insurance |
| Exact library title | `ACORD 27 - Evidence of Property Insurance` |
| Content ID, last verified 2026-09-10 | `239003` |
| Edition this field map was built against | 2016/03 |

**Resolve the form by title, then verify the ID.** `content_search` does index these forms and
does return them by form number. Search is the lookup; the content ID above is the cross-check,
not the other way round. The ID is a Zywave library identifier and can move when content is
re-indexed or a new edition is loaded. The form number never changes — ACORD 27 is always the
Evidence of Property Insurance — which is what makes the title a safe key.

```
Zywave:content_search(query="ACORD 27 evidence of property insurance form")
```

Resolve the result in this order. Do not skip ahead to the download.

1. **Match the title exactly** — `ACORD 27 - Evidence of Property Insurance`. Do not take the
   highest-scoring result.
   Relevance scores tie between sibling forms: a search for ACORD 27 returns ACORD 27 and
   ACORD 28 at identical scores, so rank alone will hand you the wrong form. Exact title is the
   only safe selector.
2. **Ignore duplicate rows.** The same form comes back more than once with different scores.
   Distinct `contentId` values are what matter, not the row count.
3. **Cross-check the resolved ID against the table above.** If it matches, proceed. If it
   differs, the library has been re-indexed or a new edition loaded — proceed with the ID search
   returned, and say so in chat, because the field map may no longer apply.
4. **If nothing matches the title exactly**, fall back to `contentId=239003` and verify hard at
   step 6. Do not settle for a near-miss title: ACORD 24, 28 and 29 are different forms,
   not variants of this one.

```
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

That returns a presigned `downloadUrl`. Download it to the working directory as `acord27.pdf`.
Some search results also carry a `fileDownloadUrl` and some do not, so `content_download` is the
reliable path.

Three checks before filling:

5. Confirm the download is a real PDF (`file acord27.pdf`). An expired presigned URL returns an
   error page, not a form.
6. **Confirm the returned `fileName` contains "ACORD 27."** A wrong content ID returns a
   *different form*, not an error — without this check an agent will fill an ACORD 28 with
   single-property data and produce a document that looks finished and is false.
7. `fill_acord27.py` validates every field name and aborts on a mismatch. That is the last
   gate, not the first. If title and filename were both right and field validation still fails,
   the library holds a **newer edition** than the 2016/03 this map was built against. Stop and
   report that. Do not edit the field map to make the run pass.

Carry the resolved content ID, the returned `fileName` and the edition into what you report in
chat, so an issued form can be traced to the exact artifact it was built from.

---

## 4. Determine the interest type, then write the disclosures

**This is the judgment that matters most in this skill.** The four interest types are not
interchangeable:

- **Mortgagee** — the standard mortgage clause. Protects the lender's interest even when the
  insured's own act or neglect would void coverage. This is what most residential loan
  documents require.
- **Lender's loss payable** — similar protection, used on commercial and personal property
  where a mortgage clause doesn't apply.
- **Loss payee** — payment rights only. **No protection when the insured voids coverage.**
  Substituting this for mortgagee quietly strips the lender's protection.
- **Additional insured** — coverage as an insured, a different thing entirely, and unusual on a
  property evidence.

Read the loan document and check what it requires. More than one may apply. If the document is
silent and you cannot ask, say so in chat rather than picking one.

Build `remarks` as an array of paragraphs covering, in order:

1. **Loan reference** and closing or funding date
2. **The holder's interest** and the clause or endorsement granting it
3. **Valuation and premium status** — replacement cost, extended replacement cost, paid through
   date, whether premium is escrowed
4. **Coverages not provided** that the loan requires — one `***` paragraph each, naming the
   requirement it fails

The ACORD 27 has **no flood or earthquake checkbox**. If either is carried, it belongs in a
coverage row. If either is excluded and the property is in a mapped flood zone or a seismic
area, it belongs in a `***` remark — this is the single most common gap on residential evidence
and the one most likely to surface at closing.

When reissuing a corrected evidence, set `policy.prior_evidence_date` so the lender knows which
document this supersedes.

---

## 5. Fill, sign, deliver

```bash
python3 scripts/fill_acord27.py acord27.pdf evidence_data.json <output_dir>
```

Produces:

- `ACORD27_<insured>_FILLABLE.pdf` — AcroForm intact, every field editable
- `ACORD27_<insured>.pdf` — flattened, renders identically in any viewer

The script generates an explicit appearance stream for every populated field and sets
`NeedAppearances = false`, so the fillable copy renders correctly everywhere rather than
depending on viewer behaviour. It reports how many of the ten coverage rows were used and warns
if no interest type was checked.

The authorized-representative signature is drawn as vector outlines via `scripts/signature.py`,
so it embeds with no font dependency. **It is a graphic, not an e-signature** — no identity
verification, no audit trail, no tamper-evidence. Its authority comes from the agency's
issuance controls, not from the mark.

Deliver both files with `present_files`.

---

## 6. Report the gaps

Do not deliver silently. In chat, state:

- The interest type you checked and what in the loan document supports it
- Which coverages were evidenced and which required ones were not
- Whether flood or earthquake is excluded, and whether the loan requires either
- Anything you assumed

If the evidence doesn't satisfy the loan requirements, say so directly. A lender finding a gap
at the closing table is a far worse outcome than a phone call today.

---

## Failure modes worth avoiding

**Checking loss payee when the loan requires mortgagee.** Strips the lender's protection against
the insured's own acts, and nothing on the face of the document reveals it.

**Defaulting to mortgagee because the holder is a bank.** Read the document.

**Using the insured's mailing address as the property location.** Common on rentals and second
homes, and it makes the evidence describe the wrong building.

**Silently truncating past ten coverage rows.** The script aborts instead. Attach an ACORD 101.

**Asserting both an expiration date and continuous-until-cancelled.** The script aborts.

**Mapping `producer.contact_name`.** This form has no such field.

**Trusting a renderer that shows a blank form.** If verifying with pypdfium2, call
`pdf.init_forms()` and render with `may_draw_forms=True`, or form fields won't be drawn and you
will "fix" a file that was never broken.

---

## Bundled resources

- `references/evidence_data_schema.md` — the `evidence_data.json` contract. Read before extracting.
- `references/acord27_field_map.md` — all 89 ACORD 27 field names mapped to schema paths.
- `references/example_evidence_data.json` — a worked residential mortgagee example.
- `scripts/fill_acord27.py` — mapping and CLI.
- `scripts/acord_fill.py` — shared fill engine, identical to the copy in `acord-24-property-cert`.
  Keep changes backward-compatible across both skills.
- `scripts/signature.py` — vector signature renderer, shared with `acord-25-new-coi`.

## Related skills

- **acord-24-property-cert** — ACORD 24, commercial property certificates with multiple lines.
- **acord-25-new-coi** — ACORD 25, liability certificates.
- **certificate-compliance-review** — reads `coi_data.json`; not yet wired to this form's data
  contract, so compliance findings for the ACORD 27 stay in chat.
