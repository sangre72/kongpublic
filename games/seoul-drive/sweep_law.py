#!/usr/bin/env python3
"""30구간 법규 준수 일제 점검 (u_5345).

오너: "한 코스가 완벽하게 되면 또 코스를 어제처럼 30 군데 정도 정해서 테스트"

law_monitor 의 판정을 구간마다 돌리고, 위반만 모아 구간별/유형별로 집계한다.
정상 프레임은 저장하지 않는다(용량).

사용: python3 sweep_law.py [--secs 150] [--pairs pairs30.json] [--out /tmp/sweep_law.json]
"""
import json, os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))

def arg(name, default):
    return sys.argv[sys.argv.index(name)+1] if name in sys.argv else default

def main():
    secs = float(arg('--secs', 150))
    pairs = json.load(open(arg('--pairs', f'{BASE}/pairs30.json')))
    out = arg('--out', '/tmp/sweep_law.json')
    results, agg = [], {}
    t_start = time.time()

    for i, pr in enumerate(pairs, 1):
        a, b = pr['from'], pr['to']
        tmp = f'/tmp/_law_{i}.json'
        print(f"\n=== [{i}/{len(pairs)}] {a} > {b} ===", flush=True)
        try:
            subprocess.run(['python3', f'{BASE}/law_monitor.py', str(secs), f'{a}>{b}',
                            '--out', tmp], timeout=secs+400,
                           capture_output=True, text=True)
            d = json.load(open(tmp))
        except Exception as e:
            print(f'   FAIL {type(e).__name__}', flush=True)
            results.append({'route': f'{a}>{b}', 'error': type(e).__name__}); continue
        s = d['summary']
        results.append(s)
        for k, n in (s.get('violations') or {}).items():
            agg[k] = agg.get(k, 0) + n
        print('   ' + json.dumps({k: s.get(k) for k in
              ('driven_m','violations','cr','tpN')}, ensure_ascii=False), flush=True)
        try: os.remove(tmp)
        except Exception: pass

    total_m = sum(r.get('driven_m', 0) for r in results if 'driven_m' in r)
    crashes = sum((r.get('cr') or 0) for r in results if 'cr' in r)
    tps     = sum((r.get('tpN') or 0) for r in results if 'tpN' in r)
    # 구조적 결함(사고·복귀)이 있는 구간 = 우선 조치 대상
    bad = [r for r in results if (r.get('cr') or 0) or (r.get('tpN') or 0)]
    summary = {'courses': len(results), 'total_driven_m': total_m,
               'crashes': crashes, 'recoveries': tps,
               'violations_total': agg,
               'per_10km': {k: round(n/max(total_m/10000, 1e-9), 1) for k, n in agg.items()},
               'courses_with_structural_defect': [r['route'] for r in bad],
               'elapsed_min': round((time.time()-t_start)/60, 1)}
    json.dump({'summary': summary, 'courses': results}, open(out,'w',encoding='utf8'),
              ensure_ascii=False, indent=1)
    print('\n' + json.dumps({'SWEEP': summary}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
