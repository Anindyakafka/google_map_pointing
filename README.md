# Odisha panchayat locations for Google My Maps

Coordinates for the **70 panchayats in `Sheet1` of `Odisha List.xlsx`**, with the original District, Block, Panchayat, Remarks, Sr. No., Generated and Comments preserved. `Sheet2` is not used. The source workbook is unchanged.

## Outputs

| File | Contents |
| --- | --- |
| [panchayats_coordinates.csv](output/panchayats_coordinates.csv) | All 70 source rows; 69 have Google Maps coordinates in separate `lat` and `long` columns. |
| [panchayats_coordinates.xlsx](output/panchayats_coordinates.xlsx) | Same data in `Sheet1`, with review/unresolved rows highlighted yellow. |
| [panchayats_map_ready.csv](output/panchayats_map_ready.csv) | 65 matches, excluding the four provisional pins and one unresolved row. Recommended initial import. |
| [panchayats_needs_review.csv](output/panchayats_needs_review.csv) | Five rows needing confirmation, including the unresolved row. |
| [validation_summary.json](output/validation_summary.json) | Counts and SHA-256 of the source workbook. |

Collected on 24 September 2026. District counts: Keonjhar 11, Koraput 14, Angul 21, Dhenkanal 24.

**These are representative locality/place pins, not GP boundaries, surveyed centroids, or systematically verified GP offices.** Seven decimal places preserve Google's returned values and do not imply survey accuracy. One provisional pin uses a school landmark, explicitly identified in `coordinate_type`.

### Remaining review

| Source row | Panchayat | Issue |
| --- | --- | --- |
| 19 | Gangarajpi | Provisional interpretation as Gangarajpur, Pottangi. Confirm the intended spelling. |
| 30 | Potsunga | Provisional interpretation as Pokatunga, Angul. Confirm the intended spelling. |
| 38 | Basudevpur | **Coordinates blank.** The relevant village is Basudebapur in Kiakata/Athmallik. Searches returned other Basudevpurs, headquarters or an unsuitable private-home POI; no reliable locality/public-office match was found. |
| 40 | Ambasarmunda | Coordinates are for Ambasarmunda Sevashram School as a locality landmark. Confirm suitability or replace with a verified GP location. |
| 60 | Analabereni | Selected the exact-name locality, but Google also lists Anlabereni roughly 2 km away. Confirm the intended point. |

All provisional coordinates remain in the full outputs, with `match_status=needs_review`. Do not interpret a populated coordinate as proof of a confirmed GP identity. The 65-row file excludes these cases but is still desktop geocoding, not field verification.

## Import into Google My Maps

1. Open [Google My Maps](https://www.google.com/mymaps) and create a map.
2. Add a layer, click **Import**, and choose `output/panchayats_map_ready.csv`.
3. Select **lat** and **long** as the location columns; `lat` is latitude and `long` is longitude.
4. Choose **Panchayat** for the marker title.
5. Optionally style markers by **Remarks** to distinguish FES, LSFP and Control.

The original `control`/`Control` capitalization is preserved, so Google may show these as separate categories. District, Block, Remarks and the other columns remain available in each marker's data. After reviewing the provisional rows and completing Basudevpur, regenerate and import the full file. Avoid importing the unresolved blank-coordinate row as a confirmed location.

Google supports CSV/XLSX imports with latitude and longitude: [official My Maps import help](https://support.google.com/mymaps/answer/3024836?hl=en).

## Repository layout

```text
Odisha List.xlsx               Original input, retained at its original path
requirements.txt              Python dependency
scripts/
  geocode.py                  Read Sheet1; collect Google Maps candidates
  extra_searches.py           Collect documented alternate-name searches
  export.py                   Apply selections; write CSV and XLSX outputs
  validate.py                 Check source preservation and coordinate provenance
data/
  candidates.json             Original queries, Google place candidates, timestamps
  extra_queries.json          Additional spelling/disambiguation queries by row ID
  extra_candidates.json       Saved results of those additional searches
  selections.json             Explicit match decisions and supporting source links
  cache/                      Ignored per-query cache for reruns
output/                       Deliverables and validation summary
```

## Reproduce the files offline

Use Python 3.10 or newer (tested with Python 3.14 and openpyxl 3.1.5). From this repository in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/export.py
.\.venv\Scripts\python.exe scripts/validate.py
```

Export uses the saved candidate snapshots and selections, so it needs no Google credentials or network access after dependency installation. No coordinates are invented or derived from district/block headquarters to fill missing rows.

## Refresh Google Maps results

```powershell
.\.venv\Scripts\python.exe scripts/geocode.py --refresh
.\.venv\Scripts\python.exe scripts/extra_searches.py --refresh
# Review candidates and update data/selections.json before exporting.
.\.venv\Scripts\python.exe scripts/export.py
.\.venv\Scripts\python.exe scripts/validate.py
```

Omit `--refresh` to reuse cached queries. Run the collectors sequentially. They write a partial checkpoint and only replace the completed snapshot once all requests succeed. Failed requests stop the run after three attempts; completed queries remain cached.

The collector uses Google's publicly accessible Maps search response (`https://www.google.com/search?tbm=map&q=...&hl=en`), **not an authenticated Geocoding API**. This undocumented response format can change or be unavailable. A future refresh may therefore need parser updates; it is not a supported production API integration. No API key or paid request was used for this collection. Saved snapshots preserve the evidence for the delivered files.

## Matching and provenance

- Each initial lookup includes the panchayat, block, district, Odisha and India; a second omits the block to check agreement.
- Automatic acceptance requires an exact normalized name and the same Google place ID in every associated search. This is query agreement, not an administrative boundary test.
- Ambiguous names, alternate spellings and misleading headquarters/road results are handled explicitly in `data/selections.json`. Supporting administrative links are included in the notes. These sources help identify the place; **all exported coordinates come from saved Google Maps place records**.
- Google place coordinates are extracted from the result record, never from the map viewport or a search page's camera center.
- `match_status` is `name_and_query_agreement`, `reviewed_match`, `needs_review`, or `unresolved`. `reviewed_match` means desktop selection of a candidate, not field verification.
- Original names and remarks are never corrected in place. `matched_name`, `matched_address`, `match_note`, `coordinate_type`, `google_id`, `google_maps_url`, `source_query`, `source_url` and `retrieved_utc` explain each pin.
- To resolve a row, add any necessary query to `data/extra_queries.json`, run `extra_searches.py`, and set its `google_id` and explanatory note in `data/selections.json`. IDs must refer to a saved candidate for that row. Mark uncertain decisions `needs_review`.
- If a refreshed result no longer contains a selected ID, export fails rather than silently selecting another place. Changes to source rows require recollection and a review of row-ID selections.

## Validation

`scripts/validate.py` checks every source field against the full CSV, matches every populated coordinate to saved Google evidence, checks finite numeric values and a broad Odisha envelope, rejects duplicate pins, verifies CSV/XLSX agreement, and checks the ready/review subsets. These checks catch data handling errors; they do not prove that each point lies within the named GP's administrative boundary.

Current result: **70 rows preserved; 69 coordinate pairs; 65 map-ready rows; 4 provisional pins; 1 unresolved row.**
