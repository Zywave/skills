# Segment grid

## Industry sectors (NAICS 2-digit, 20 cells)

| Label | `naicsCodes` |
|---|---|
| Agriculture, forestry, fishing | `["11"]` |
| Mining, oil & gas | `["21"]` |
| Utilities | `["22"]` |
| Construction | `["23"]` |
| Manufacturing | `["31","32","33"]` |
| Wholesale trade | `["42"]` |
| Retail trade | `["44","45"]` |
| Transportation & warehousing | `["48","49"]` |
| Information | `["51"]` |
| Finance & insurance | `["52"]` |
| Real estate, rental & leasing | `["53"]` |
| Professional, scientific & technical | `["54"]` |
| Management of companies | `["55"]` |
| Administrative, support, waste | `["56"]` |
| Educational services | `["61"]` |
| Health care & social assistance | `["62"]` |
| Arts, entertainment & recreation | `["71"]` |
| Accommodation & food services | `["72"]` |
| Other services | `["81"]` |
| Public administration | `["92"]` |

When a producer names a focus vertical, replace the grid with 3-digit subsectors of that sector (e.g. Construction → 236, 237, 238; Health care → 621, 622, 623, 624) and, if they go one deeper, 4-digit groups.

## Size bands (`employeeCountMin` / `employeeCountMax`)

| Band | Min | Max |
|---|---|---|
| 10–49 | 10 | 49 |
| 50–99 | 50 | 99 |
| 100–249 | 100 | 249 |
| 250+ | 250 | (omit) |

For Benefits, the 50–99 and 100–249 bands are where ALE and self-funding conversations start; call that out in the memo.

## Renewal months

`renewalMonths: [m]` for m in 1..12, plus a baseline query with no renewal filter. Share with known renewal = sum of the twelve / baseline (companies can have multiple renewal months; if the sum exceeds the baseline, report the twelve counts and skip the share).

## Signals

| Signal | Parameter | LOB |
|---|---|---|
| Self-funded health plan | `selfFunded: true` | Benefits (also useful in Commercial for size proxy) |
| OSHA violations on record | `hasOshaViolations: true` | Commercial |
| DOT violations / inspections on record | `hasDotViolations: true` | Commercial |
| Fidelity bond out of compliance | `fidelityBondOutOfCompliance: true` | Benefits (ERISA bond) |
| Reachable (contact email on file) | `hasContactEmails: true` | Both — this is the sequenceable universe |
| Medical / Dental / Vision plan on file | `benefitsPlanTypes: ["Medical"]` etc. | Benefits |

## Fields observed on discovery results

`msid, name, ein, phoneNumber, city, state, county, zipCode, latitude, longitude, revenueRange{min,max}, isOutOfBusiness, qualityScore, fidelityBonds[{bond_value, plan_assets, bond_ratio, is_compliant}], complianceReport{checks[{compliance_type, result}]}`. Broker, carrier, employee count, NAICS and renewal fields appear only when populated; the script treats absence as null.
