# SPDX-License-Identifier: MIT
# © 2026 Vijayakumar Yeddula · MIT (code) · Mechanical Design Basics (C4)
"""Fill [F: key] placeholders in Markdown files from one or more Facts JSON files.
Narration lines (starting with ">") get the spoken form; every other line gets the printed value.
usage: python3 fill_facts.py <src_dir> <out_dir> <facts1.json> [facts2.json ...]
       (old form also accepted: fill_facts.py <facts.json> <src_dir> <out_dir>)
Prints ONE line: PASS / n unresolved keys (listed in fill_facts.log)."""
import json, os, re, sys

args = sys.argv[1:]
if args and args[0].endswith('.json'):
    jsons, src, out = [args[0]], args[1], args[2]
else:
    src, out, jsons = args[0], args[1], args[2:]
facts = {}
for j in jsons:
    facts.update({k: d for k, d in json.load(open(j)).items() if not k.startswith('_')})  # '_' keys = notices, not facts


def printed(d):
    if d.get('printed') not in (None, ''):
        return str(d['printed'])
    v = d['value']
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


os.makedirs(out, exist_ok=True)
missing, narr = set(), [False]


def rep(m):
    k = m.group(1)
    if k in ('name', 'key', 'k'):   # documentation keys only
        return m.group(0)
    if k not in facts:
        missing.add(k)
        return m.group(0)
    d = facts[k]
    return (d.get('spoken') or printed(d)) if narr[0] else printed(d)


for f in sorted(os.listdir(src)):
    if not f.endswith('.md'):
        continue
    lines = []
    for ln in open(os.path.join(src, f)).read().split('\n'):
        narr[0] = ln.lstrip().startswith('>')
        new = re.sub(r'\[F: ([A-Za-z0-9_]+)\]', rep, ln)
        for m in re.finditer(r'\{PENDING: ?([A-Za-z0-9_]+)\}', new):
            if m.group(1) not in ('name', 'key', 'k'):
                missing.add('PENDING:' + m.group(1))
        lines.append(new)
    open(os.path.join(out, f), 'w').write('\n'.join(lines))
open(os.path.join(out, 'fill_facts.log'), 'w').write('\n'.join(sorted(missing)))
print('PASS 0 unresolved' if not missing else f'FAIL {len(missing)} unresolved: ' + ', '.join(sorted(missing)[:10]))
