# State routing

One lookup. The vehicle's garaging state picks the form. Where a state publishes no card of its
own, the countrywide ACORD 50 is the answer.

## Match on the ACORD form number, not the title

Resolve a form by its **form number plus state code**, then use the content ID to confirm.
Titles are not unique. Nevada is the clearest case: ACORD 52 NV and ACORD 54 NV both return
from `content_search` under the byte-identical title `Nevada Permanent Insurance Identification
Card`, and only the form number prefix tells them apart. The two countrywide watermark forms
collide the same way, differing by the single word `Set`.

So: match the `ACORD <number> <ST>` prefix, verify the content ID against this table, and treat
the full title as confirmation rather than as the key.

## The table

`AUTO` means one card exists for that state. Use it.

`ASK` means the state publishes more than one and the choice is a real one the producer makes.
Ask once per state per run, never per vehicle.

`FALLBACK` means no dedicated card exists in the library. Use the countrywide ACORD 50 and tell
the user you did, because this fallback is read off library contents and is not a verified state
filing rule. A producer may know better for their own state.

| State | Name | Action | Form number | Content ID | Cards/sheet | Library title |
|---|---|---|---|---|---|---|
| AL | Alabama | AUTO | `ACORD 50 AL` | 239131 | 4 | ACORD 50 AL - Alabama Insurance Identification Card |
| AK | Alaska | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| AZ | Arizona | AUTO | `ACORD 50 AZ` | 239140 | 4 | ACORD 50 AZ - Arizona Insurance Identification Card |
| AR | Arkansas | AUTO | `ACORD 50 AR` | 239146 | 1 | ACORD 50 AR - Arkansas Proof of Insurance Card |
| CA | California | ASK | `ACORD 50 CA` | 239865 | 4 | ACORD 50 CA - California Insurance Identification Card |
| | | | `ACORD 52 CA` | 239168 | 1 | ACORD 52 CA - California Fleet Auto Insurance Identification Card |
| CO | Colorado | AUTO | `ACORD 50 CO` | 239191 | 4 | ACORD 50 CO - Colorado Insurance Identification Card |
| CT | Connecticut | AUTO | `ACORD 50 CT` | 239207 | 4 | ACORD 50 CT - Connecticut Insurance Identification Card |
| DE | Delaware | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| FL | Florida | AUTO | `ACORD 50 FL` | 239250 | 8 | ACORD 50 FL - Florida Auto ID Card |
| GA | Georgia | AUTO | `ACORD 50 GA` | 239267 | 1 | ACORD 50 GA - Georgia Insurance Policy Information Card |
| HI | Hawaii | AUTO | `ACORD 50 HI` | 239277 | 8 | ACORD 50 HI - Hawaii Auto ID Card |
| ID | Idaho | AUTO | `ACORD 50 ID` | 239285 | 4 | ACORD 50 ID - State of Idaho Liability Insurance Identification Card |
| IL | Illinois | AUTO | `ACORD 50 IL` | 239293 | 4 | ACORD 50 IL - Illinois Insurance Identification Card |
| IN | Indiana | AUTO | `ACORD 50 IN` | 239303 | 4 | ACORD 50 IN - Indiana Insurance Identification Card |
| IA | Iowa | AUTO | `ACORD 50 IA` | 239310 | 1 | ACORD 50 IA - Iowa Financial Responsibility Card |
| KS | Kansas | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| KY | Kentucky | AUTO | `ACORD 50 KY` | 239339 | 1 | ACORD 50 KY - Commonwealth of KY Proof of Insurance (2 part) |
| LA | Louisiana | AUTO | `ACORD 50 LA` | 239351 | 1 | ACORD 50 LA - Louisiana Auto Insurance Identification Card |
| ME | Maine | ASK | `ACORD 50 ME` | 239366 | 4 | ACORD 50 ME - Maine Motor Vehicle Insurance Identification Card |
| | | | `ACORD 51 ME` | 489320 | 4 | ACORD 51 ME - Maine Temporary Motor Vehicle Insurance |
| MD | Maryland | AUTO | `ACORD 50 MD` | 239372 | 1 | ACORD 50 MD - Maryland Motor Vehicle Liability Insurance Identification Card |
| MA | Massachusetts | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| MI | Michigan | AUTO | `ACORD 50 MI` | 239866 | 2 | ACORD 50 MI - State of Michigan Certificate of No-Fault Insurance |
| MN | Minnesota | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| MS | Mississippi | AUTO | `ACORD 50 MS` | 239428 | 1 | ACORD 50 MS - Mississippi Auto Insurance ID Card |
| MO | Missouri | AUTO | `ACORD 50 MO` | 239437 | 2 | ACORD 50 MO - Missouri Auto Insurance ID Card |
| MT | Montana | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| NE | Nebraska | AUTO | `ACORD 50 NE` | 239458 | 4 | ACORD 50 NE - Nebraska Auto Liability Insurance Identification Card |
| NV | Nevada | ASK | `ACORD 51 NV` | 239464 | 1 | ACORD 51 NV - Nevada Temporary Insurance Identification Card |
| | | | `ACORD 52 NV` | 239465 | 4 | ACORD 52 NV - Nevada Permanent Insurance Identification Card |
| | | | `ACORD 53 NV` | 239466 | 1 | ACORD 53 NV - Nevada Temporary Insurance Identification Card, Evidence of Operator’s Policy of Liability Insurance |
| | | | `ACORD 54 NV` | 239868 | 1 | ACORD 54 NV - Nevada Permanent Insurance Identification Card |
| NH | New Hampshire | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| NJ | New Jersey | ASK | `ACORD 50 NJ` | 239486 | 2 | ACORD 50 NJ - State of New Jersey Temporary Evidence of Insurance |
| | | | `ACORD 51 NJ` | 239488 | 2 | ACORD 51 NJ - State of New Jersey Insurance Identification Card |
| NM | New Mexico | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| NY | New York | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| NC | North Carolina | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| ND | North Dakota | AUTO | `ACORD 50 ND` | 239548 | 4 | ACORD 50 ND - North Dakota Insurance Identification Card |
| OH | Ohio | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| OK | Oklahoma | ASK | `ACORD 50 OK` | 239572 | 2 | ACORD 50 OK - Oklahoma Owners Security Verification Form |
| | | | `ACORD 51 OK` | 239573 | 1 | ACORD 51 OK - Oklahoma Operators Security Verification Form |
| OR | Oregon | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| PA | Pennsylvania | AUTO | `ACORD 50 PA` | 239591 | 1 | ACORD 50 PA - Pennsylvania Financial Responsibility Identification Card |
| RI | Rhode Island | AUTO | `ACORD 50 RI` | 239603 | 1 | ACORD 50 RI - Rhode Island Insurance Identification Card |
| SC | South Carolina | AUTO | `ACORD 50 SC` | 239918 | 4 | ACORD 50 SC - South Carolina Insurance Identification Card |
| SD | South Dakota | AUTO | `ACORD 50 SD` | 239630 | 4 | ACORD 50 SD - South Dakota Insurance Identification Card |
| TN | Tennessee | AUTO | `ACORD 50 TN` | 239639 | 4 | ACORD 50 TN - Tennessee Insurance Identification Card |
| TX | Texas | AUTO | `ACORD 50 TX` | 239645 | 1 | ACORD 50 TX - Texas Liability Insurance Card |
| UT | Utah | AUTO | `ACORD 51 UT` | 239662 | 1 | ACORD 51 UT - Utah Insurance Identification Card |
| VT | Vermont | AUTO | `ACORD 50 VT` | 239673 | 4 | ACORD 50 VT - Vermont Automobile Insurance Identification Card |
| VA | Virginia | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| WA | Washington | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| WV | West Virginia | AUTO | `ACORD 50 WV` | 239701 | 2 | ACORD 50 WV - West Virginia Certificate of Insurance |
| WI | Wisconsin | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |
| WY | Wyoming | FALLBACK | ACORD 50 | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card |

## What to ask in the five ASK states

| State | The choice |
|---|---|
| California | Standard card, or ACORD 52 CA if the policy is a commercial or fleet policy. |
| Maine | Permanent card (50 ME), or temporary (51 ME). |
| New Jersey | Temporary evidence (50 NJ), or the standard ID card (51 NJ). |
| Nevada | Four options. Temporary or permanent, and owner’s policy or operator’s policy. |
| Oklahoma | Owner’s security verification (50 OK), or operator’s (51 OK). |

## Countrywide forms

| Form number | Content ID | Cards/sheet | Library title | Use when |
|---|---|---|---|---|
| `ACORD 50` | 239054 | 1 | ACORD 50 - Automobile Insurance ID Card | The fallback form, and the default when no state applies. |
| `ACORD 50 WM` | 239057 | 1 | ACORD 50 WM - Automobile ID Card (with watermark) | A single card on watermark stock. |
| `ACORD 50 WM (Set)` | 814034 | 4 | ACORD 50 WM - Automobile ID Card Set (with watermark) | Fleet batches on four part perforated stock. Note the title differs from 239057 by one word. |

## States with no dedicated card

  AK, DE, KS, MA, MN, MT, NH, NM, NY, NC, OH, OR, VA, WA, WI, WY

Sixteen states. All fall through to the countrywide ACORD 50.
