"""Offline checks for source preservation, coordinate provenance and export consistency."""
import csv
import json
import math
from openpyxl import load_workbook
from geocode import ROOT, source_rows


def read_csv(name):
    with (ROOT / 'output' / name).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def validate():
    original = source_rows()
    rows = read_csv('panchayats_coordinates.csv')
    assert len(rows) == len(original)
    assert len({r['Sr. No.'] for r in rows}) == len(rows)
    candidates = json.loads((ROOT / 'data/candidates.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'data/extra_candidates.json').read_text(encoding='utf-8'))
    book = load_workbook(ROOT / 'output/panchayats_coordinates.xlsx', data_only=True)
    values = list(book['Sheet1'].values)
    assert list(values[0]) == list(rows[0])
    assert len(values) == len(rows) + 1
    for index, (source, row) in enumerate(zip(original, rows)):
        for key, value in source.items():
            assert row[key] == (str(value) if value is not None else ''), (index, key)
        assert bool(row['lat']) == bool(row['long'])
        if row['lat']:
            lat, lon = float(row['lat']), float(row['long'])
            assert math.isfinite(lat) and math.isfinite(lon)
            assert 17.5 <= lat <= 22.7 and 81.3 <= lon <= 87.6
            matches = [c for s in candidates[index]['searches'] + extra.get(row['Sr. No.'], [])
                       for c in s['candidates'] if c['google_id'] == row['google_id']]
            assert matches, f'Coordinate lacks Google candidate: {index}'
            assert any(abs(lat-c['lat']) < 1e-7 and abs(lon-c['long']) < 1e-7 for c in matches)
            assert row['source_url'].startswith('https://www.google.com/search?')
            assert row['google_maps_url'].startswith('https://www.google.com/maps?cid=')
        else:
            assert row['match_status'] == 'unresolved'
        for key, value in zip(values[0], values[index+1]):
            if key in ('lat', 'long') and row[key]:
                assert isinstance(value, (int, float)) and abs(value-float(row[key])) < 1e-10
            else:
                assert (str(value) if value is not None else '') == row[key], (index, key)
    assert len({(r['lat'],r['long']) for r in rows if r['lat']}) == sum(bool(r['lat']) for r in rows), 'Duplicate pins need review'
    ready = read_csv('panchayats_map_ready.csv')
    review = read_csv('panchayats_needs_review.csv')
    assert ready == [r for r in rows if r['lat'] and r['match_status'] != 'needs_review']
    assert review == [r for r in rows if r['match_status'] in ('needs_review', 'unresolved')]
    print(f'PASS: {len(rows)} source rows preserved; {len(ready)} map-ready; {len(review)} need review.')
    print('PASS: CSV/XLSX agree; numeric coordinates trace to saved Google place records; no duplicate pins.')
    book.close()


if __name__ == '__main__':
    validate()
