import json,re,sys
rows=[]
for ln in open(sys.argv[1],encoding='utf-8'):
    ln=re.sub(r'"stema":auto','"stema":"auto"',ln.strip())
    if not ln: continue
    try: rows.append(json.loads(ln))
    except Exception as e: print('skip',e); continue
print(f"{'class':9}{'ema':<7}{'sc':<8}{'amp':<8}{'sr':<8}{'xt95':<7}{'n':<6}{'prog':<7}")
for x in rows:
    d=x['res']; w=d.get('weave') or {}; m=(d.get('corner') or {}).get('model') or {}
    print(f"{x['class']:9}{str(x['stema']):<7}{w.get('sc_min'):<8}{w.get('amp_p95'):<8}{m.get('steer_rate_p95'):<8}{m.get('xt_p95'):<7}{m.get('n'):<6}{round((d.get('prog') or 0)*100,1):<7}")
