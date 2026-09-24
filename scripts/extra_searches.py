"""Collect the documented spelling/disambiguation searches separately."""
import argparse
import json
from geocode import ROOT, search


def collect_extra(refresh=False):
    queries = json.loads((ROOT / 'data/extra_queries.json').read_text(encoding='utf-8'))
    results = {}
    pending = ROOT / 'data/extra_candidates.partial.json'
    for row_id, items in queries.items():
        results[row_id] = [search(query, refresh=refresh) for query in items]
        print(row_id, json.dumps([[c['name'], c['address'], c['lat'], c['long']] for r in results[row_id] for c in r['candidates']]), flush=True)
        pending.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(ROOT / 'data/extra_candidates.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch again instead of using the local cache.')
    collect_extra(refresh=parser.parse_args().refresh)
