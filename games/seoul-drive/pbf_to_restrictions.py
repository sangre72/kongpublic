"""OSM relation[type=restriction] -> GraphHopper-style turn-cost table (a_5046).

WHY: ar_5034 Q3 — our chunks carry {n,l,o,p} only, no way ids and no relation members, so
     no_left_turn / no_right_turn cannot be reconstructed client-side. That report called for a
     FETCH-SIDE change; this is it. Owner incident u_5042 ("turns right where it must not").

Adopted shape = GraphHopper turn-cost table, NOT OSRM edge-expansion (ar_5034: expansion is
overkill for us). Key "<from_way>|<via_node>|<to_way>" -> restriction value.

Tag/role semantics per ar_5034 Q3 + OSM Relation:restriction:
  roles from(way) / via(node | way(s)) / to(way)
  prohibitory no_right_turn no_left_turn no_u_turn no_straight_on no_entry no_exit
  mandatory   only_right_turn only_left_turn only_u_turn only_straight_on
via-way restrictions are recorded separately (via_ways list) — a single via-node key cannot
express them, and inventing one would be wrong.

Does NOT touch games/seoul-drive/*.js — data pipeline only.

usage: python3 pbf_to_restrictions.py <pbf> <out.json> [--bbox la0,lo0,la1,lo1]
"""
import sys, os, json, time
import osmium

PROHIBIT = {'no_right_turn', 'no_left_turn', 'no_u_turn', 'no_straight_on',
            'no_entry', 'no_exit'}
MANDATORY = {'only_right_turn', 'only_left_turn', 'only_u_turn', 'only_straight_on'}
KNOWN = PROHIBIT | MANDATORY


class Restr(osmium.SimpleHandler):
    def __init__(self, keep_ways=None):
        super().__init__()
        self.keep = keep_ways          # set of way ids in our area, or None = keep all
        self.table = {}                # "from|via|to" -> value      (via-node form)
        self.via_way = []              # via-way form, kept separately
        self.by_type = {}
        self.n_rel = 0
        self.n_skip_tag = 0            # unknown/ignored restriction value
        self.n_skip_area = 0           # outside our way set
        self.n_incomplete = 0          # missing from/via/to

    def relation(self, r):
        t = r.tags
        if t.get('type') != 'restriction':
            return
        self.n_rel += 1

        # value may live on `restriction` or a vehicle-qualified key (restriction:hgv=...)
        val = t.get('restriction')
        if val is None:
            for tag in t:
                if tag.k.startswith('restriction:'):
                    val = tag.v
                    break
        if val is None:
            self.n_skip_tag += 1
            return
        # OSRM parser convention (ar_5034): accept only_*/no_*, drop no_*_on_red + unknown
        if val not in KNOWN:
            self.n_skip_tag += 1
            return

        # no_entry allows several `from`, no_exit several `to` (ar_5034 Q3 / OSM wiki), and a
        # handful of ordinary relations carry multiples too (29 nationwide, measured). Collect
        # lists and emit the cross-product so none is silently dropped.
        froms, tos, via_ways = [], [], []
        via_node = None
        for m in r.members:
            if m.role == 'from' and m.type == 'w':
                froms.append(m.ref)
            elif m.role == 'to' and m.type == 'w':
                tos.append(m.ref)
            elif m.role == 'via':
                if m.type == 'n':
                    via_node = m.ref
                elif m.type == 'w':
                    via_ways.append(m.ref)

        if not froms or not tos or (via_node is None and not via_ways):
            self.n_incomplete += 1
            return

        # area filter: keep pairs whose from AND to both exist in our chunk area
        pairs = [(f, t) for f in froms for t in tos
                 if self.keep is None or (f in self.keep and t in self.keep)]
        if not pairs:
            self.n_skip_area += 1
            return

        for f, t in pairs:
            if via_node is not None:
                self.table[f'{f}|{via_node}|{t}'] = val
            else:
                self.via_way.append({'from': f, 'via_ways': via_ways, 'to': t, 'r': val})
            self.by_type[val] = self.by_type.get(val, 0) + 1


class WayIds(osmium.SimpleHandler):
    """Collect ids of routable ways inside bbox, so restrictions match our chunk area."""

    def __init__(self, bbox, road_set):
        super().__init__()
        self.bbox = bbox
        self.road = road_set
        self.ids = set()

    def way(self, w):
        if w.tags.get('highway') not in self.road:
            return
        try:
            n0 = next(n for n in w.nodes if n.location.valid())
        except (StopIteration, Exception):
            return
        if self.bbox:
            a0, o0, a1, o1 = self.bbox
            if not (a0 <= n0.lat <= a1 and o0 <= n0.lon <= o1):
                return
        self.ids.add(w.id)


def main():
    pbf, out = sys.argv[1], sys.argv[2]
    bbox = None
    if '--bbox' in sys.argv:
        bbox = [float(v) for v in sys.argv[sys.argv.index('--bbox') + 1].split(',')]

    # same ROAD set as pbf_to_chunks.py so the id universe matches the chunks
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pbf_to_chunks import ROAD

    t0 = time.time()
    keep = None
    if bbox:
        wi = WayIds(bbox, ROAD)
        wi.apply_file(pbf, locations=True, idx='flex_mem')
        keep = wi.ids
        print(json.dumps({'pass1_ways_in_bbox': len(keep),
                          's': round(time.time() - t0)}), flush=True)

    h = Restr(keep)
    h.apply_file(pbf)          # relations need no node locations
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    payload = {
        'turn_costs': h.table,
        'via_way': h.via_way,
        'meta': {
            'source': os.path.basename(pbf),
            'bbox': bbox,
            'relations_seen': h.n_rel,
            'kept_via_node': len(h.table),
            'kept_via_way': len(h.via_way),
            'skipped_unknown_tag': h.n_skip_tag,
            'skipped_outside_area': h.n_skip_area,
            'skipped_incomplete': h.n_incomplete,
            'by_type': h.by_type,
        },
    }
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    print(json.dumps({**payload['meta'],
                      'out': out,
                      'size_kb': round(os.path.getsize(out) / 1024, 1),
                      'total_s': round(time.time() - t0)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
