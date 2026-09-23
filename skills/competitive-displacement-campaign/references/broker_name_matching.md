# Matching a competitor's name in filing data

The `commercialBrokerName` and `benefitsBrokerName` fields come from public filings (Form 5500
Schedule A/C for benefits, state filings for commercial). They are free text as the filer typed
them. The same firm appears under several spellings, and acquisitions leave old names in place
for years.

## Field shape

The broker fields are objects, not strings: `{name, name_normalized, broker_bin, city, state}`. `broker_bin` is Zywave's normalized firm key ("MARSH AND MCLENNAN AGENCY", "GALLAGHER", "BROWN AND BROWN") and collapses most spelling variants — an acquired agency filing under its own name still carries the parent's `broker_bin`. Match and display on `broker_bin`; show `name` as the filing wrote it.

## Bins within one competitor

One competitor can carry more than one `broker_bin`. A Twin Cities search on "Marsh" returned 257 companies split between **MARSH AND MCLENNAN AGENCY** (MMA — the middle-market agency and its acquired shops: McGriff, RJF, Cline Wood) and **MARSH** (Marsh USA, Marsh Risk — the large-account side). After the sample check, show the bin counts and let the producer choose; for a mid-market agency the MMA rows are the realistic targets and the MARSH rows are usually Fortune-1000 accounts.

Market data also carries **duplicate company records** — the same employer under two MSIDs (one with an EIN, one without). Collapse on normalized name + city for display, keep both MSIDs, and pass only one to the campaign.

## Approach

1. **Ask the producer for variants.** They know the market: legal name, DBA, pre-acquisition
   name, common abbreviation. "Who else do they operate as around here?"
2. **Search each variant separately** and merge on `msid`. The filter is a contains-match on the
   server side, so a short distinctive token ("Gallagher") usually catches more than a full legal
   name ("Arthur J. Gallagher & Co.").
3. **Spot-check five records per variant.** Read the returned broker field. If a token is too
   short and pulls unrelated firms ("Hub" matches "Hub International" and "Insurance Hub of
   Iowa"), drop that variant or add a second token.
4. **Tell the producer which variants matched and how many each returned.** They can veto one.

## Common patterns

| Firm as producers say it | Variants seen in filings |
|---|---|
| Marsh | Marsh & McLennan; Marsh McLennan Agency; MMA; Marsh USA |
| Gallagher | Arthur J. Gallagher; AJG; Gallagher Benefit Services |
| Aon | Aon Risk Services; Aon Consulting; Aon Hewitt |
| Willis | WTW; Willis Towers Watson; Willis of [State] |
| Hub | Hub International; HUB Int'l [Region] |
| Lockton | Lockton Companies; Lockton Benefit Group |
| USI | USI Insurance Services; USI Consulting Group |
| Brown & Brown | Brown & Brown of [State]; B&B |
| Acrisure | Acrisure LLC; plus the pre-acquisition agency name, often unchanged |
| Alliant | Alliant Insurance Services; Alliant Employee Benefits |

Regional firms: expect the legal entity name and one or two DBAs. Acquired agencies: the filing
often still carries the acquired agency's name, so target both.

## What not to do

- Don't broaden to a single generic token ("Insurance") to increase the count.
- Don't assume a null broker field is a company without a broker. It's a company without filing
  data.
- Don't put any of these names in the emails. `sequenceExclusions` carries them for that reason.
