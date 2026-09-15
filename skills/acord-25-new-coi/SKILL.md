---
name: acord-25-new-coi
description: Issue an ACORD 25 Certificate of Liability Insurance from a certificate request. Takes a contract or insurance requirements document, a certificate request email, and the insured's policy documents, pulls the blank ACORD 25 from the Zywave content library, compares policy data against contract requirements, and produces a filled certificate — fillable and flattened — dated today and signed with a generated authorized-representative signature. Use this whenever someone asks to issue, produce, generate, create, or "cut" a certificate of insurance, COI, ACORD 25, or cert; whenever a certificate holder or general contractor emails asking for a certificate; whenever someone uploads a subcontract or insurance requirements exhibit alongside policy documents; or whenever they mention certificate requests, cert issuance, additional insured status, waivers of subrogation, or evidence of insurance. Use it even if they only say "handle this cert request" without naming ACORD 25.
---

# ACORD 25 New COI

Issue an ACORD 25 from a certificate request package.

A certificate is a statement to a third party about what coverage exists. The single most
important property of the output is that **every statement on it is true**. A certificate that
overstates coverage exposes the agency to E&O liability and misleads a holder who is making
decisions — like letting a crew onto a job site — based on it. Accuracy beats completeness every
time: a certificate showing two of five required coverages, with the gaps disclosed, is correct.
One showing five when only two exist is not.

## Workflow

1. Collect the inputs
2. Extract into `coi_data.json`
3. Resolve and pull the blank ACORD 25 from Zywave
4. Compare policies to requirements, and write the disclosures
5. Fill, sign, and deliver
6. Report the gaps in chat

---

## 1. Collect the inputs

A complete request package has three kinds of document:

| Input | What it gives you |
|---|---|
| Contract / insurance requirements exhibit | Required limits, endorsements, holder wording, carrier rating floor, notice terms |
| Certificate request email | Who is asking, deadline, holder's specific concerns |
| Policy documents (dec pages) | What coverage actually exists |

Missing pieces are workable but change what you can promise:

- **No contract** — you can still issue from the policies, but you cannot verify compliance or
  write meaningful disclosures. Say so, and ask for the requirements exhibit.
- **No request email** — fine. Take the holder details from the contract.
- **A coverage line with no policy document** — this is the common and important case. It means
  no such policy is in force. Leave that row blank; do not guess.

Ask before proceeding only when the certificate holder is genuinely unidentifiable. Everything
else you can flag in the output.

---

## 2. Extract into coi_data.json

Read `references/data_schema.md` and build `coi_data.json` in the working directory.

This file is the contract between this skill and **certificate-compliance-review**. Getting it
right once means the certificate and the compliance review can never disagree about what the
policies say.

Extraction rules that matter:

- **Set a policy key to `null` when no policy exists.** Not `{}`, not a stub with empty limits.
  `null` is what makes the fill script leave the row blank and what makes the compliance review
  report a missing coverage rather than a missing extraction.
- **Copy holder wording verbatim** when the contract specifies it. Contracts often require exact
  text ("ABC Company", not "ABC Co."), and holders reject certificates over this. If the contract
  gives a block of holder text, reproduce it exactly, including the attention line.
- **Record endorsement scope, not just presence.** A CG 20 10 grants additional insured status for
  ongoing operations only. That limitation cannot be expressed in the form's Y/N column, so capture
  it in the endorsement's `scope` field where the disclosure logic can reach it.
- **Leave unknown values empty.** If a declarations page doesn't state the A.M. Best rating, leave
  `am_best` empty. An empty value becomes a finding. An invented one becomes a false assurance.

Set `certificate.issue_date` to **today's date** in MM/DD/YYYY. Read it from the system
(`date +%m/%d/%Y`), not from a source document. A certificate is dated when issued.

Set `certificate.number` from the agency's numbering scheme if one is evident, otherwise generate
one like `COI-<year>-<sequence>` and say in chat that you assigned it.

Set `meta.specimen` to `true` for demo, test, or training data, which stamps a SPECIMEN
disclaimer into the certificate. Set it `false` only for a certificate the agency is genuinely
issuing on real policies.

---

## 3. Resolve and pull the blank ACORD 25 from Zywave

| | |
|---|---|
| Form | ACORD 25 — Certificate of Liability Insurance |
| Exact library title | `ACORD 25 - Certificate of Liability Insurance` |
| Content ID, last verified 2026-09-10 | `239001` |
| Edition this field map was built against | 2025/12 |

**Resolve the form by title, then verify the ID.** `content_search` does index these forms and
does return them by form number. Search is the lookup; the content ID above is the cross-check,
not the other way round. The ID is a Zywave library identifier and can move when content is
re-indexed or a new edition is loaded. The form number never changes — ACORD 25 is always the
Certificate of Liability Insurance — which is what makes the title a safe key.

```
Zywave:content_search(query="ACORD 25 certificate of liability insurance form")
```

Resolve the result in this order. Do not skip ahead to the download.

1. **Match the title exactly** — `ACORD 25 - Certificate of Liability Insurance`. Do not take the
   highest-scoring result.
   Relevance scores tie between sibling forms: a search for ACORD 27 returns ACORD 27 and
   ACORD 28 at identical scores, so rank alone will hand you the wrong form. Exact title is the
   only safe selector.
2. **Ignore duplicate rows.** The same form comes back more than once with different scores.
   Distinct `contentId` values are what matter, not the row count.
3. **Cross-check the resolved ID against the table above.** If it matches, proceed. If it
   differs, the library has been re-indexed or a new edition loaded — proceed with the ID search
   returned, and say so in chat, because the field map may no longer apply.
4. **If nothing matches the title exactly**, fall back to `contentId=239001` and verify hard at
   step 6. Do not settle for a near-miss title: ACORD 20, 21, 23, 24, 26 and 30 are different forms,
   not variants of this one.

```
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

That returns a presigned `downloadUrl`. Download it to the working directory as `acord25.pdf`.
Some search results also carry a `fileDownloadUrl` and some do not, so `content_download` is the
reliable path.

Three checks before filling:

5. Confirm the download is a real PDF (`file acord25.pdf`). An expired presigned URL returns an
   error page, not a form.
6. **Confirm the returned `fileName` contains "ACORD 25."** A wrong content ID returns a
   *different form*, not an error — without this check an agent will fill an ACORD 24 with
   liability data and produce a document that looks finished and is false.
7. `fill_acord25.py` validates every field name and aborts on a mismatch. That is the last
   gate, not the first. If title and filename were both right and field validation still fails,
   the library holds a **newer edition** than the 2025/12 this map was built against. Stop and
   report that. Do not edit the field map to make the run pass.

Carry the resolved content ID, the returned `fileName` and the edition into what you report in
chat, so an issued form can be traced to the exact artifact it was built from.

---

## 4. Compare, then write the disclosures

Walk each requirement in the contract against what the policies actually provide. The comparison
you do here drives two things: which rows get filled, and what the Description of Operations says.

For the ADDL INSD and SUBR WVD columns, answer the literal question the form asks. If the holder
is an additional insured for ongoing operations, `additional_insured` is `Y` — that is true. The
limitation belongs in the remarks, not in a falsified `N`.

**This is the judgment that matters most in the whole skill.** A bare `Y` in a column, with a
limitation the holder can't see, is how a technically-accurate certificate becomes a misleading
one. The form's Y/N columns are too coarse to carry the truth, so the remarks box has to.

Build `description_of_operations` as an array of paragraphs covering, in this order:

1. **Project reference** — agreement number, project name, site address
2. **Each coverage's endorsement detail** — which forms are in force, and any scope limitation
   stated plainly ("ONGOING OPERATIONS ONLY per CG 20 10 04 13. Completed-operations additional
   insured status (CG 20 37) is NOT carried on this policy.")
3. **Coverages not provided** — name every required coverage with no policy in force, and state
   which contract requirement it fails
4. **Endorsement copies** accompanying the certificate

Write these in the plain declarative voice a risk manager reads quickly. Say "is NOT carried"
rather than "may not extend to."

The remarks box holds roughly 8 lines at 5.2pt. The fill script auto-fits and will not go below
4.8pt — if your text overflows, tighten the prose rather than dropping a disclosure.

---

## 5. Fill, sign, deliver

```bash
python3 scripts/fill_acord25.py acord25.pdf coi_data.json <output_dir>
```

Produces both versions:

- `ACORD25_<insured>_FILLABLE.pdf` — AcroForm intact, every field editable
- `ACORD25_<insured>.pdf` — flattened, renders identically in any viewer

The script generates an explicit appearance stream for every populated field and sets
`NeedAppearances = false`, so the fillable version renders correctly everywhere instead of
depending on viewer behaviour. It prints which coverage rows it left blank — check that list
against your extraction before delivering.

The authorized-representative signature is drawn from `producer.authorized_representative` as
vector outlines via `scripts/signature.py`, so it embeds with no font dependency and scales
cleanly. This matches how agency management systems handle certificate signatures — a stored
signature image applied at issuance.

**The signature is a graphic, not an e-signature.** No identity verification, no audit trail, no
tamper-evidence. That is the correct model for COIs, but if someone asks whether it is legally
binding, the honest answer is that its authority comes from the agency's issuance controls — who
is permitted to issue — not from the mark itself.

Deliver both files with `present_files`. If a compliance review is also wanted, hand off to the
**certificate-compliance-review** skill; it reads the same `coi_data.json`.

---

## 6. Report the gaps

Do not deliver the certificate silently. In chat, state plainly:

- Which coverages were issued and which rows were left blank, and why
- Every contract requirement the certificate does not satisfy
- Anything you assigned or assumed (certificate number, missing contact details)

If the certificate does not fully satisfy the contract, say so directly rather than letting the
PDF speak for itself. The producer needs to know before it reaches the holder — particularly when
there is a deadline or a mobilization date in the request, because a gap discovered at the gate
is a much worse outcome than a phone call today.

---

## Failure modes worth avoiding

**Filling a row for a policy that does not exist.** The most damaging error available here. If
`policies.automobile` is `null`, the entire auto section stays empty.

**Normalizing the certificate holder's name.** "ABC Company, Inc." when the contract says
"ABC Company" gets the certificate rejected.

**Dating the certificate from the contract.** Use today.

**Reporting a Y/N column without its limitation.** See section 4.

**Trusting a renderer that shows a blank form.** If verifying with pypdfium2, call
`pdf.init_forms()` and render with `may_draw_forms=True`, or form fields won't be drawn and you
will "fix" a file that was never broken.

---

## Bundled resources

- `references/data_schema.md` — the `coi_data.json` contract. Read before extracting.
- `references/acord25_field_map.md` — all 129 ACORD 25 field names mapped to schema paths. Read
  when a field won't populate or when the form revision changes.
- `scripts/fill_acord25.py` — fills and signs both output versions.
- `scripts/signature.py` — vector signature renderer.
