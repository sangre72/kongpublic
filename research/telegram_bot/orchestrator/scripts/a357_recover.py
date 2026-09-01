#!/usr/bin/env python3
import json, subprocess, time
from pathlib import Path
K="/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"
OUT=Path("/Users/bumsuklee/git/kong-bot/kaymaps/keynote")
notes=list((OUT/"a357_notes.txt").read_text().splitlines()) if (OUT/"a357_notes.txt").exists() else []
notes.append("---RECOVER---")
def run(a,t=90):
    return subprocess.run(a,capture_output=True,text=True,timeout=t)
def click(x,y): run([K,"--yes","input","click",str(int(round(x))),str(int(round(y)))])
def drag(a,b,c,d): run([K,"--yes","input","drag",str(int(round(a))),str(int(round(b))),str(int(round(c))),str(int(round(d))),"--scale","1"])
def chord(m,k): run([K,"--yes","input","chord",m,k])
def text(s): run([K,"--yes","input","text",s])
def dump(pid):
    r=run([K,"--json","see","--a11y","--pid",str(pid)],60)
    if r.returncode!=0: return []
    j=json.loads(r.stdout); d=j.get("data",j)
    if isinstance(d,list): return d
    for v in d.values():
        if isinstance(v,list) and v and isinstance(v[0],dict): return v
    return []
def list_left(els):
    out=[]
    for e in els:
        lab=(e.get("label") or "").strip(); cx,cy=e.get("cx") or 0,e.get("cy") or 0
        if cx>450 or cy<100 or cy>900 or not lab: continue
        if lab in ("텍스트 상자 삽입","검색"): continue
        if e.get("role") in ("AXTextField","AXStaticText","AXCell"): out.append(e)
    return out
def mi(els,exact=None,contains=None):
    c=[]
    for e in els:
        lab=e.get("label") or ""
        if exact and lab==exact: c.append(e)
        elif contains and contains in lab: c.append(e)
    m=[e for e in c if e.get("role")=="AXMenuItem"]
    return m[0] if m else (c[0] if c else None)
run(["open","-a","Keynote"]); time.sleep(0.8)
pid=run(["pgrep","-x","Keynote"]).stdout.strip().split()[0]
# undo a few times to restore if possible
for i in range(3):
    chord("cmd","z"); time.sleep(0.35)
    notes.append("undo_{}".format(i+1))
els=dump(pid)
notes.append("after_undo={}".format([(e.get("label"),e.get("cy")) for e in list_left(els)]))
rects=[e for e in list_left(els) if "사각" in (e.get("label") or "")]
if not rects:
    ins=next((e for e in els if e.get("role")=="AXMenuBarItem" and e.get("label")=="삽입"),None)
    if ins:
        click(ins["cx"],ins["cy"]); time.sleep(0.5)
        els=dump(pid)
        sh=mi(els,exact="도형")
        if sh:
            click(sh["cx"],sh["cy"]); time.sleep(0.55)
            notes.append("도형={},{}".format(sh["cx"],sh["cy"]))
            els=dump(pid)
            r=mi(els,exact="직사각형")
            if r:
                click(r["cx"],r["cy"]); time.sleep(0.7)
                notes.append("직사각형={},{}".format(r["cx"],r["cy"]))
    click(1028,710); time.sleep(0.4)
    # show list
    click(419,20); time.sleep(0.35)
    els=dump(pid)
    ol=next((e for e in els if e.get("label") and "대상체 목록" in e.get("label")),None)
    if ol: click(ol["cx"],ol["cy"]); time.sleep(0.4)
    els=dump(pid)
    notes.append("after_insert={}".format([(e.get("label"),e.get("cy")) for e in list_left(els)]))
    rects=[e for e in list_left(els) if "사각" in (e.get("label") or "")]

# delete extra rects keep one
rects=[e for e in list_left(dump(pid)) if "사각" in (e.get("label") or "")]
while len(rects)>1:
    r=sorted(rects,key=lambda e:e.get("cy") or 0)[-1]
    click(r["cx"],r["cy"]); time.sleep(0.3)
    run([K,"--yes","input","key","delete"]); time.sleep(0.3)
    notes.append("trim_rect cy={}".format(r.get("cy")))
    rects=[e for e in list_left(dump(pid)) if "사각" in (e.get("label") or "")]
    if not rects:
        chord("cmd","z"); time.sleep(0.3); notes.append("undo_trim"); break

rects=[e for e in list_left(dump(pid)) if "사각" in (e.get("label") or "")]
if rects:
    click(rects[0]["cx"],rects[0]["cy"]); time.sleep(0.45)
    notes.append("selected={}".format(rects[0].get("cy")))
    # center box SE handle
    box_cx, box_cy = 1028.0, 710.0
    half=50
    for i in range(4):
        se_x,se_y=box_cx+half, box_cy+half
        notes.append("drag_start_{} {},{}".format(i+1,se_x,se_y))
        drag(se_x,se_y,1800,1100); time.sleep(0.5)
        half=70+i*40
        # reselect
        rs=[e for e in list_left(dump(pid)) if "사각" in (e.get("label") or "")]
        if rs: click(rs[0]["cx"],rs[0]["cy"]); time.sleep(0.25)
else:
    notes.append("NO_RECT_recover")

# ensure Google if missing
els=dump(pid)
labs=[e.get("label") for e in list_left(els)]
if not any(l and "Google" in l for l in labs) and not any(l=="텍스트" for l in labs):
    ins=next((e for e in els if e.get("role")=="AXMenuBarItem" and e.get("label")=="삽입"),None)
    if ins:
        click(ins["cx"],ins["cy"]); time.sleep(0.4)
        els=dump(pid)
        tb=mi(els,contains="텍스트")
        if tb:
            click(tb["cx"],tb["cy"]); time.sleep(0.5)
            text("Google"); time.sleep(0.3)
            notes.append("retyped_Google")

run(["open","-a","Keynote"]); time.sleep(0.3)
run(["screencapture","-x",str(OUT/"slide_357.png")])
els=dump(pid)
notes.append("objs_final={}".format([(e.get("label"),e.get("cy")) for e in list_left(els)]))
notes.append("wins_final={}".format([{"w":w.get("w"),"h":w.get("h")} for w in windows(els)[:1]]))
notes.append("shot={}".format((OUT/"slide_357.png").stat().st_size if (OUT/"slide_357.png").exists() else 0))
notes.append("RECOVER_ELAPSED={}".format(int(time.time()-t0)) if False else "RECOVER_DONE")
(OUT/"a357_notes.txt").write_text("\n".join(notes)+"\n")
print("DONE")
for n in notes[-30:]: print(n)
t0=time.time()
