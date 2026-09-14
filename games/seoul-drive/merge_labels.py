"""read_db 로 내려받은 프레임 문서들(JSON) → 하나의 라벨 배열.
사용: python3 merge_labels.py <dir_with_fNNNNNN.json> out_labels.json
"""
import sys, json, glob, os

def main(d, out):
    rows = []
    for f in sorted(glob.glob(os.path.join(d, '**', 'f*.json'), recursive=True)):
        o = json.load(open(f))
        rows.extend(o.get('rows') or o.get('data', {}).get('rows') or [])
    rows.sort(key=lambda r: r['t'])
    json.dump([{'rows': rows}], open(out, 'w'))
    if rows:
        st = [r['steer'] for r in rows]
        print(json.dumps({'rows': len(rows),
                          'span_s': round((rows[-1]['t']-rows[0]['t'])/1000, 1),
                          'steer_min': min(st), 'steer_max': max(st),
                          'brake_frames': sum(1 for r in rows if r['brake'] > .2),
                          'crash_frames': sum(1 for r in rows if r['hold'])}))
    else:
        print('{"rows":0}')

if __name__ == '__main__':
    main(*sys.argv[1:3])
