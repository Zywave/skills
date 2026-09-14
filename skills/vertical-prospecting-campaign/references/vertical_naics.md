# Vertical → NAICS → pain points

`naicsCodes` accepts prefixes; `"238"` matches every specialty-trade code. Use the shortest prefix that captures the vertical without pulling in neighbors. Pain points feed `painPointPool` — pick three to five per campaign, adjusted for line of business.

| Vertical (as producers say it) | NAICS | Typical size band | Commercial pain points | Benefits pain points |
|---|---|---|---|---|
| Contractors / construction | 23 (all); 236 building; 237 heavy/civil; 238 specialty trades | 10–200 | Subcontractor COIs and additional insured tracking; workers' comp mod; fleet and tool theft; contractual risk transfer | Seasonal workforce eligibility; PEO vs. direct; ACA hours tracking for variable-hour crews |
| Electrical / HVAC / plumbing | 2382 | 10–150 | Completed ops; service vehicle fleet; technician injury | Recruiting/retention benefits; apprentice eligibility |
| Roofing | 238160 | 10–100 | Height exposure and WC cost; hail-season capacity; sub verification | High WC cost pressure on total comp |
| Landscaping / lawn | 56173 | 10–100 | Seasonal fleet; equipment theft; herbicide exposure | Seasonal eligibility; H-2B workforce |
| Trucking / freight | 484 | drivers 5–100 | FMCSA compliance and CSA scores; auto liability severity; cargo; driver retention | Driver benefits as retention; DOT physical coordination |
| Warehousing / logistics | 4931 | 25–500 | Forklift injuries; property and stock; tenant/landlord risk transfer | Shift-worker eligibility; leave administration |
| Manufacturing (general) | 31–33 | 25–500 | Product liability; equipment breakdown; supply-chain BI; OSHA recordables | Self-funding at 100+; stop-loss; union vs. non-union plans |
| Metal fabrication | 3323, 3327 | 20–250 | Machine guarding and WC; welding fire; product recall | Same as manufacturing |
| Plastics / rubber | 3261, 3262 | 25–300 | Fire load; environmental; product liability | Same as manufacturing |
| Food & beverage manufacturing | 311, 3121 | 25–500 | Recall and contamination; spoilage; refrigeration breakdown | Same as manufacturing |
| Breweries / distilleries / wineries | 31212, 31214, 31213 | 5–100 | Liquor liability; taproom premises; tank rupture | Tipped and part-time eligibility |
| Restaurants / food service | 722 | 10–250 | Liquor liability; slip-and-fall; food contamination; EPLI | Variable-hour ACA tracking; turnover |
| Hotels / lodging | 7211 | 25–300 | Guest property; premises; pool; cyber (PMS data) | Seasonal and part-time eligibility |
| Retail | 44–45 | 10–250 | Premises; theft; product liability; cyber/PCI | Part-time eligibility; turnover |
| Auto dealers | 4411 | 25–300 | Garage liability; dealers open lot (hail); F&I E&O; cyber | Sales comp plans and 401(k); dealership groups |
| Auto repair / body shops | 8111 | 5–75 | Garagekeepers; paint booth fire; environmental | Small-group options; level-funding |
| Medical practices / clinics | 6211 | 10–200 | Medical malpractice coordination; cyber/HIPAA; EPLI | Professional recruiting benefits; 401(k)/cash balance |
| Dental practices | 6212 | 5–75 | Malpractice; equipment; cyber/HIPAA | Small-group medical; owner-favorable plan design |
| Home health / hospice | 6216, 62161 | 25–500 | Non-owned auto; abuse & molestation; WC for in-home caregivers | Part-time caregiver eligibility; ACA tracking |
| Senior living / nursing | 623, 6233 | 50–500 | Professional and general liability; abuse & molestation; WC lifting injuries | Shift workers; turnover; self-funding |
| Daycare / childcare | 6244 | 10–100 | Abuse & molestation; transportation; premises | Small-group; low-wage eligibility |
| Schools / private education | 611 | 25–500 | Abuse & molestation; D&O; athletics; cyber | Summer eligibility gaps; retirement plans |
| Nonprofits | 813 (excl. 8131) | 10–250 | D&O; volunteer accident; abuse & molestation; cyber | Budget-constrained plan design; ICHRA |
| Religious organizations | 8131 | 5–100 | Property; abuse & molestation; auto (vans) | Clergy housing and benefits nuances |
| Municipalities / public entities | 921 | 25–1000 | Public officials liability; law enforcement; property; cyber | Public-sector plan compliance |
| Law firms | 5411 | 5–200 | LPL/E&O; cyber; EPLI | Partner vs. staff plan design |
| Accounting firms | 5412 | 5–200 | Professional liability; cyber (tax data); EPLI | Same |
| Architects / engineers | 5413 | 10–250 | Professional liability; project-specific coverage | Recruiting benefits for licensed staff |
| Staffing / PEO clients | 5613 | 25–1000 | WC on placed workers; EPLI; crime/fidelity | Co-employment benefits structure |
| Software / IT services | 5112, 5415 | 10–250 | Tech E&O; cyber; IP | Recruiting/retention benefits; equity-heavy comp |
| Real estate / property management | 531, 5313 | 5–150 | Habitational property; premises; E&O | Small-group; commission-based eligibility |
| Agriculture / farms | 111, 112 | 5–100 | Farm property; equipment; pollution; WC for farm labor | Seasonal/H-2A workforce |
| Fitness / gyms | 71394 | 5–100 | Participant injury; abuse & molestation; premises | Part-time trainer eligibility |
| Golf courses / clubs | 71391 | 25–200 | Property (turf equipment, clubhouse); liquor; premises | Seasonal workforce |
| Security services | 56161 | 25–500 | Assault & battery; E&O; firearms; WC | Turnover; part-time eligibility |
| Janitorial / building services | 56172 | 25–500 | Bonding; WC; third-party property damage | Low-wage eligibility; ACA |
| Printing | 3231 | 10–150 | Equipment breakdown; fire; product | Same as manufacturing |
| Wholesale distribution | 42 | 25–300 | Product liability; fleet; cargo; stock | Self-funding at scale |

## Renewal-window campaigns

When the producer gives a window ("renewing in Q1", "next 90 days"), set `renewalMonths` to the matching month numbers and `useRenewalModel: true`. Renewal-model drafts open on timing; the TIMELINE hook first is the right default.

## Compliance-signal campaigns

`hasOshaViolations: true` (manufacturing, construction, warehousing) and `hasDotViolations: true` (trucking, distribution, landscaping fleets) surface companies with a public reason to talk. Lead the `painPointPool` with the matching compliance topic. Do not quote a specific violation in the campaign unless the producer has read it in the research brief.
