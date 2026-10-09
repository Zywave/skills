---
name: auto-id-card
description: Generate ACORD automobile insurance ID cards for personal and commercial auto, pulling the right state form from the Zywave content library and mapping data from whatever the user has. Takes a dec page, policy, binder, Excel vehicle schedule, email, screenshot, or pasted text, routes by garaging state, validates every VIN, and returns a fillable and a flattened PDF. Use this whenever someone asks for an auto ID card, insurance ID card, auto ID, ACORD 50, ACORD 51/52/53/54, proof of insurance card, financial responsibility card, no-fault certificate, or a card for the glovebox; whenever they want cards for a fleet, a new vehicle, a replacement, or a renewal reissue; and whenever they attach a vehicle schedule or dec page and mention cards. Use it even if they only say "cut me an ID card for this vehicle" or "the insured needs cards." For liability certificates use acord-25-new-coi; for property evidence use the ACORD 24/27/28 skills.
---

# Auto ID Card

Issue ACORD auto identification cards from whatever the producer has on hand.

An ID card is what a driver hands to a police officer or shows at a registration counter. Its
whole job is to be correct and legible in that moment. That shapes every choice in this skill:
a card with a mistyped VIN is worse than no card at all, because it looks finished. Accuracy
beats speed, and a visible gap beats an invented value.

Two facts about these forms drive the mechanics:

**One card carries one vehicle.** There is no multi-vehicle ID card and no overflow schedule for
one. Twenty vehicles means twenty cards. What differs between forms is how many cards print per
sheet: one, two, four, or eight. Issuing for a fleet is repetition, not a different document.

Counting that capacity is less obvious than it looks, and `fill_autoid.py` handles it so you do
not have to. Three layouts hide in the set. Most forms put every card slot on one page, and the
slot count is the capacity. Some repeat the same card on a later page as an alternate print
layout: the countrywide ACORD 50 says to use pages 2 and 3 for two-sided printing, and the
Nevada 51, 53 and 54 do the same, so those pages get the *same* vehicle rather than the next
one. And two forms pair slots as copies of a single card, Michigan labelling them VEHICLE COPY
and SECRETARY OF STATE'S COPY and Kentucky telling the policyholder to hand one copy to the
County Clerk. Counting widgets instead of cards on any of these puts two different vehicles on
what is physically one card.

**The garaging state picks the form.** A state-specific card exists to satisfy that state's
financial responsibility statute, and that attaches to the registered vehicle rather than to
where the insured collects mail. A truck garaged in Illinois needs the Illinois card even when
the company's headquarters are in Wisconsin. The insured's *mailing* address is what prints on
the card; the *garaging* state is what selects which card.

## Workflow

1. Collect the inputs
2. Extract into `autoid_data.json`
3. Route to a state and resolve the form
4. Pull the blank form from the Zywave content library
5. Show the mapped data and let the user correct it
6. Fill and deliver
7. Report what you did and did not do

---

## 1. Collect the inputs

Anything that states bound coverage and identifies vehicles will work:

| Input | What it gives you |
|---|---|
| Declarations page | The best source. Insured, carrier, policy number, dates, and usually a vehicle schedule with garaging |
| Policy | Same, plus endorsements that may have changed a vehicle list |
| Binder | Valid source. Coverage is bound even though the policy has not issued |
| Excel vehicle schedule | The usual shape of commercial fleet data. See the section below |
| Email | Often carries the request and the vehicle details but not the policy. Combine with a dec page |
| Screenshot | Workable, with care. See the VIN section |
| Pasted or typed text | Fine. A producer reading values off a screen is a legitimate path |

**Refuse a quote.** A quote is not bound coverage, so a card issued from one asserts insurance
that does not exist. Say that plainly and ask for the binder or dec page instead. This is the
one input that is not a judgment call.

**Refuse an expired policy.** If the expiration date has passed, do not issue. Say which date
you read and where you read it.

A stale document is different from an expired one. A dec page from eight months ago is still
usable, but name its date in your report, because a dec page describes coverage as of its own
date and an endorsement since then could have changed the vehicle list.

When two inputs disagree, the declarations page wins, and you say in chat that they disagreed.
Silently picking one is how a wrong effective date reaches a card.

### Excel vehicle schedules

Fleet data usually arrives as a spreadsheet, and the column headers are never the same twice.
Read the sheet, find the columns that hold year, make, model, VIN, and garaging location, and
show the user your column mapping before you rely on it. Headers like `Unit #`, `Yr`, `Desc`,
`Serial`, `Loc`, and `Gar State` are all common. A 17-character alphanumeric column is almost
certainly the VIN even when it is labelled something else.

Watch for schedules that mix vehicles with trailers or equipment. Trailers do get ID cards;
mowers and forklifts do not. If a row has no VIN, ask rather than skipping it quietly.

---

## 2. Extract into autoid_data.json

Read `references/data_schema.md` and build the file in the working directory.

The reason extraction is a separate artifact rather than something you hold in your head: the
user reviews this structure in step 5. A correction there costs one edit. A correction found
after the cards are cut costs a reissue.

Rules that matter more than the rest:

**Copy names verbatim.** "ABC Company, Inc." stays exactly that. Normalizing an insured or
carrier name is how a card stops matching the policy it evidences.

**Dates are MM/DD/YYYY.** Read them from the document, not from today.

**Leave unknowns out.** Omit the key. Do not put a plausible NAIC code, a guessed model, or an
inferred address on a card. `fill_autoid.py` reports every field it left blank, which gives the
producer something to act on.

**Set `meta.specimen` to `true`** for anything that is a demo, a test, or training data. A card
that can pass for real when it was never meant to is a liability, and the stamp is cheap.

### VINs deserve their own paragraph

A VIN is 17 characters, never contains I, O, or Q, and from 1981 on carries a check digit in
position 9 that catches most single-character errors. `scripts/vin.py` implements the check and
`fill_autoid.py` refuses to write cards when any VIN fails it.

This matters most with screenshots and photos, where optical recognition reliably confuses 0
with O, 1 with I, 5 with S, and 8 with B. The check digit turns a silent wrong VIN into a
caught error, so run it and believe it.

When a VIN legitimately fails, which happens with pre-1981 and some imported vehicles, set
`"vin_override": true` on that vehicle and say in your report that you did and why. Do not
reach for the override to get past an error you have not understood.

---

## 3. Route to a state and resolve the form

Read `references/state_routing.md`. It resolves all fifty states.

The lookup is the vehicle's garaging state. Fall back to the insured's mailing state only when
garaging is genuinely absent from every input, and say which basis you used in your report.

Three outcomes:

- **AUTO**: one card form exists for that state. Use it.
- **ASK**: the state publishes more than one card and the choice is real. California splits
  standard against commercial fleet; Maine and New Jersey split permanent against temporary;
  Oklahoma splits owner against operator; Nevada splits both ways at once, giving four options.
  Ask once per state per run. Prompting per vehicle on a twenty unit fleet is unusable.
- **FALLBACK**: no dedicated card exists for that state, so the countrywide ACORD 50 applies.
  Tell the user, because this fallback is read off library contents rather than a verified state
  filing rule, and a producer may know better for their own state.

**A fleet can span states.** Group vehicles by garaging state and run steps 3 through 6 once per
state. Four states means four form pulls and four sets of output.

---

## 4. Pull the blank form from the content library

Search is the lookup. `state_routing.md` is the verification.

```
Zywave:content_search(query="ACORD 50 IL Illinois insurance identification card")
Zywave:content_download(contentId=<resolved ID>, convertToPdf=true)
```

Resolve in this order, and do not skip to the download:

1. **Match the `ACORD <number> <ST>` prefix, not the title and not the score.** Titles are not
   unique. ACORD 52 NV and ACORD 54 NV both come back under the byte-identical title
   `Nevada Permanent Insurance Identification Card`, and the two countrywide watermark forms
   differ by the single word `Set`. Only the form number separates them. Scores are worse still:
   sibling forms tie, so the top result is regularly the wrong card for the right state.
2. **Ignore duplicate rows.** The same form returns several times at different scores. Distinct
   `contentId` values are what matter, not the row count.
3. **Cross-check the content ID against `state_routing.md`.** A match means proceed. A difference
   means the library was re-indexed or a new edition loaded, so proceed with what search returned
   and say so in your report, because the field map may no longer apply.
4. **Verify the downloaded file.** Confirm it is a real PDF (`file form.pdf`), since an expired
   presigned URL returns an error page rather than an error. Confirm the returned `fileName`
   carries the form number you asked for. A wrong content ID returns a *different form*, not a
   failure, so nothing downstream will catch it: you would fill the wrong state's card and
   produce something that looks finished and is wrong.

`fill_autoid.py` is the last gate: it exits if the PDF has no `Vehicle_VINIdentifier` field,
which means what came down is not an auto ID card at all.

---

## 5. Show the mapped data and let the user correct it

Before filling anything, put the extraction in front of the user as a table they can correct.

This step exists because the errors that reach a card almost always come from reading the source
documents, not from filling the form. Catching them here is one edit. Catching them later is a
reissue, and catching them never means a driver is carrying a card with the wrong VIN.

Show:

- The header data once: insured, carrier and NAIC, policy number, effective and expiration dates
- Every vehicle as a row: year, make, model, VIN, garaging state
- The routing decision and its basis, and the form you are about to use
- Any VIN that failed validation, and why
- The source document and its date

Then ask them to confirm or tell you what to change. Apply corrections to `autoid_data.json`
and show the affected rows again. Keep it to the vehicle list and the form choice. Asking them
to confirm every field on a twenty unit fleet defeats the point of automating it.

**Ask for what the form wants and the documents do not have.** Some state cards ask for a
registered owner, a plate number, an excluded driver, a claims phone number, a carrier's
Arizona DOT code. None of those appear on a dec page, so extraction will never produce them,
but the producer has them to hand. `fill_autoid.py` names every one of these a form asks for
and nothing answered, with the plain-language question to put to the user, so run it once and
bring those questions into this step rather than delivering a card with a visible hole in it.
`references/data_schema.md` lists the optional keys that carry the answers.

---

## 6. Fill and deliver

```bash
python3 scripts/fill_autoid.py <blank_form.pdf> autoid_data.json <output_dir>
```

The script reads the blank form, discovers its own fields and card slots, batches vehicles
across sheets at the form's capacity, and writes both versions per sheet:

- `AutoID_<insured>_<ST>[_sheetN]_FILLABLE.pdf`: AcroForm intact, every field editable
- `AutoID_<insured>_<ST>[_sheetN].pdf`: flattened, renders anywhere

Read its output rather than assuming success. It reports the form, cards per sheet, sheet count,
fields written, any element you supplied that this form does not carry, unused card slots, and
any text it truncated to fit.

Two lines of that output need passing on to the user:

**Truncated text.** Card fields are narrow and the forms declare a fixed 8pt font, so the script
shrinks text and then clips whatever still will not fit. Clipping a long model name is fine.
Clipping a policy number is not, and the producer is the one who can tell the difference.

**Unused card slots.** A partial sheet prints blank cards in the leftover slots: three vehicles
on a four card sheet leaves one. Say so when you deliver, because a blank card next to real ones
reads as a card that failed to generate.

It also separates two kinds of gap, and only one of them is a problem. "Nowhere to put"
means the form has no such field, which is fine. "This form asks for the following" means the
form does have the field and nothing filled it, which is a question for the producer. Unknown
keys in the data file are reported too, so a typo surfaces rather than turning into a blank
field nobody notices.

When `meta.specimen` is true, every card is watermarked SPECIMEN on the page content, where
neither flattening nor editing the form fields can remove it.

Deliver both files with `present_files`. Tell the user the fillable version opens in their own
PDF viewer, where they can edit any field directly and save. Leaving the AcroForm intact is the
point: a producer who spots something at the last second should not have to come back here.

**Auto ID cards carry no signature.** Unlike certificates, these forms have no authorized
representative signature field, and the only signature fields anywhere in the set belong to an
additional interest on the West Virginia form. Do not generate or apply one.

---

## 7. Report what you did

Do not deliver files silently. In chat, state:

- The form title, edition, and resolved content ID, so an issued card traces to the artifact it
  came from
- The routing decision and its basis: which state, garaging or mailing, and whether it fell back
  to the countrywide form
- Vehicle count and sheet count
- Every field left blank, and why
- Any VIN override, any conflict between inputs, any text trimmed to fit
- The source document and its date, phrased as what the document says rather than as a claim
  about current coverage

On partial success, issue what validated and name what did not. Seventeen of twenty cards plus a
clear account of the three failures is a good outcome. Nineteen cards and a silent omission is not.

---

## Failure modes worth avoiding

**Issuing from a quote.** The most damaging error available here. A quote is not coverage.

**Resolving a form by title or by score.** Both fail. Titles collide (ACORD 52 NV and 54 NV are
identical strings) and sibling forms tie on relevance. Match the form number and state code.

**Using the mailing state to pick the form.** Correct for most personal lines by coincidence,
wrong for commercial fleets, and wrong in exactly the cases where it matters.

**Trusting a VIN read off a screenshot.** Run the check digit.

**Filling one card with multiple vehicles.** The form has one VIN field per card for a reason.
Do not reason about sheet capacity from the number of VIN fields in the file: five forms repeat
the same card on a variant page and two pair their slots as copies. Let the script work it out
and read what it reports.

**Pairing slots to satisfy a two-card rule.** Connecticut, Missouri, New Jersey, South Dakota
and Arizona all state the insured must be issued two cards. That is a print instruction, not a
layout: those forms give one slot per card, and the script says so in its output. Print the
sheet twice. Writing one vehicle into two slots to look compliant just loses a card slot.

**Editing `references/` to make a run pass.** If field validation fails after the title and
filename both checked out, the library holds a newer edition than these references describe.
Stop and report that. A reference file edited to silence an error hides a real change.

**Verifying with a renderer that does not draw form fields.** A filled AcroForm looks blank in
pypdfium2 unless you call `pdf.init_forms()` and render with `may_draw_forms=True`. Skip that and
you will "fix" a file that was never broken.

---

## Bundled resources

- `references/state_routing.md`: all fifty states to a form, with content IDs. Read in step 3.
- `references/data_schema.md`: the `autoid_data.json` contract. Read before extracting.
- `references/form_catalog.md`: every card form and the elements it carries. Read when a value
  did not appear and you need to know whether the form has that field at all.
- `scripts/fill_autoid.py`: fills and flattens, discovers slots, batches sheets, guards VINs.
- `scripts/vin.py`: VIN format and check digit. Runnable on its own for a quick check.
