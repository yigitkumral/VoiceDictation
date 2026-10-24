"""Son dikte tani kayitlarini pane, surum ve baglam durumuna gore karsilastir."""
import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import statistics


def summarize(records):
    groups = defaultdict(list)
    for row in records:
        if row.get('operation', 'dictation') != 'dictation':
            continue
        source = row.get('source', {}).get('selection') or {}
        context = row.get('stages', {}).get('context', {})
        client = row.get('source', {}).get('client') or {}
        key = (row.get('build', '?'), source.get('machine') or 'local',
               source.get('pane_id') or 'unmatched', context.get('kind', 'not_reached'),
               context.get('reason', {}).get('status', 'unknown'),
               client.get('channel', 'unknown'), client.get('device_type', 'unknown'),
               client.get('client_id', 'unknown'))
        groups[key].append(row)
    result = []
    for key, rows in groups.items():
        item = dict(zip(('build', 'machine', 'source_pane', 'context', 'context_status',
                         'channel', 'device_type', 'client_id'), key))
        item['count'] = len(rows)
        item['outcomes'] = dict(Counter(r.get('timings', {}).get('status', 'unknown') for r in rows))
        item['cleanup'] = dict(Counter(r.get('timings', {}).get('cleanup_status', 'not_run') for r in rows))
        for field in ('audio_seconds', 'input_chars', 'context_words', 'total_ms', 'whisper_ms', 'cleanup_ms', 'paste_ms'):
            values = sorted(r['timings'][field] for r in rows if isinstance(r.get('timings', {}).get(field), (int, float)))
            if values:
                item[field] = dict(median=round(statistics.median(values), 2), maximum=round(values[-1], 2))
        result.append(item)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--last', type=int, default=100)
    args = parser.parse_args()
    if args.last < 1:
        parser.error('--last must be positive')
    records = deque(maxlen=args.last)
    invalid = 0
    root = Path(__file__).resolve().parents[2] / '.local' / 'diagnostics'
    for path in sorted(root.glob('*.jsonl')):
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                    if row.get('schema') == 1:
                        records.append(row)
                except (ValueError, AttributeError):
                    invalid += 1
    print(json.dumps(dict(samples=len(records), invalid_lines=invalid,
                         operations=dict(Counter(r.get('operation', 'dictation') for r in records)),
                         groups=summarize(records)),
                     ensure_ascii=True, indent=2))
