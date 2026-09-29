#!/usr/bin/env python3
"""u_5751: deficit class by DISTINCT ROADS drawn, not frames.
Frames are past target (60.8k vs 40k), so the only thing left to buy is road diversity.
The frame-based quota stalls arterial at 4 roads: arterial routes yield many frames per round,
so arterial hits its frame share fast and stops being selected while its road pool stays untouched.
Targets (u_5751): arterial 12, two 20, alley best-effort.
Prints: "<deficit_class> alley=<n> two=<n> arterial=<n>"  (n = distinct roads drawn)
"""
import json, re, sys, glob, os
TARGET = {'alley': 40, 'two': 20, 'arterial': 12}
logs = os.environ.get('COVLOG', '/Users/bumsuklee/.claude/jobs/ccf4ec97/tmp/l12_*.log')
cls = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/scope_road_class.json')))
roads = set()
for f in sorted(set(sum((glob.glob(g) for g in logs.split()), []))):
    try:
        for ln in open(f, encoding='utf-8', errors='ignore'):
            m = re.match(r'^=== r\d+ (.+?) turns=', ln)
            if m:
                for side in m.group(1).split('>'):
                    n = side.strip()
                    if n: roads.add(n)
    except Exception: pass
c = {'alley': 0, 'two': 0, 'arterial': 0}
for n in roads:
    k = cls.get(n)
    if k in c: c[k] += 1
# deficit = largest shortfall vs target, as a fraction of target
defi = max(TARGET, key=lambda k: (TARGET[k] - c[k]) / TARGET[k])
print(f"{defi} alley={c['alley']} two={c['two']} arterial={c['arterial']}")
