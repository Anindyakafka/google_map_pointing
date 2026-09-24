"""Retrieve Google Maps place candidates and export Sheet1 without changing source values."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data' / 'cache'


def search(query, refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(query.encode()).hexdigest() + '.json')
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding='utf-8'))
    url = 'https://www.google.com/search?' + urlencode({'tbm': 'map', 'q': query, 'hl': 'en'})
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40) as response:
                raw = response.read().decode('utf-8')
            payload = json.loads(raw.removeprefix(")]}'\n"))
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    candidates = []
    # Public Maps search response: each search result's place record is item 14.
    # The coordinates at record[9] belong to the place, not the map viewport.
    records = payload[0][1] if payload and payload[0] and len(payload[0]) > 1 else []
    for record in records or []:
        if not isinstance(record, list) or len(record) <= 14 or not record[14]:
            continue
        place = record[14]
        if len(place) <= 11 or not isinstance(place[9], list) or len(place[9]) < 4:
            continue
        lat, lon = place[9][2:4]
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        candidates.append({'name': place[11], 'address': place[18] if len(place) > 18 else '',
                           'lat': lat, 'long': lon, 'google_id': place[10],
                           'place_id': place[78] if len(place) > 78 else None,
                           'maps_url': place[42] if len(place) > 42 else None})
    result = {'query': query, 'source_url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
              'candidates': candidates}
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    time.sleep(0.4)
    return result


def source_rows():
    book = load_workbook(ROOT / 'Odisha List.xlsx', data_only=True)
    values = list(book['Sheet1'].values)
    required = {'Sr. No.', 'District', 'Block', 'Panchayat', 'Remarks', 'Generated', 'Comments'}
    if not required.issubset(values[0]):
        raise ValueError('Sheet1 does not contain the expected headers.')
    rows = [dict(zip(values[0], row)) for row in values[1:] if any(v is not None for v in row)]
    for row in rows:
        if any(not row[key] for key in ('District', 'Block', 'Panchayat')):
            raise ValueError(f'Missing location field in source row {row}')
    book.close()
    return rows


def collect(refresh=False):
    output = []
    pending = ROOT / 'data' / 'candidates.partial.json'
    for row in source_rows():
        queries = [f"{row['Panchayat']}, {row['Block']}, {row['District']}, Odisha, India",
                   f"{row['Panchayat']}, {row['District']}, Odisha, India"]
        results = [search(q, refresh=refresh) for q in dict.fromkeys(queries)]
        output.append({'row': row, 'searches': results})
        print(row['Sr. No.'], row['Panchayat'], json.dumps([[c['name'], c['address'], c['lat'], c['long']] for r in results for c in r['candidates']], ensure_ascii=True), flush=True)
        pending.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(ROOT / 'data' / 'candidates.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch again instead of using the local cache.')
    collect(refresh=parser.parse_args().refresh)
