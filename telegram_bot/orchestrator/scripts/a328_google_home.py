#!/usr/bin/env python3
import json, subprocess, time, os
from pathlib import Path

K = str(Path("/Users/bumsuklee/git/kong-bot/kongtrol/target/release/kongtrol"))
ROOT = Path("/Users/bumsuklee/git/kong-bot")
OUT = ROOT / "kaymaps/keynote"
PID = subprocess.check_output(["pgrep", "-x", "Keynote"], text=True).split()[0]
t0 = time.time()
notes = []

def run(a, timeout=90):
    return subprocess.run(a, capture_output=True, text=True, timeout=timeout)

def click(x,y):
    run([K,"--yes","input","click",str(int(x)),str(int(y))])

def key(n):
    run([K,"--yes","input","key",n])

def chord(m,k):
    run([K,"--yes","input","chord",m,k])

def text(s):
    run([K,"--yes","input","text",s])

def dump():
    r=run([K,"--json","see","--a11y","--pid",PID],timeout=60)
    if r.returncode!=0: return []
    j=json.loads(r.stdout); d=j.get("data",j)
    if isinstance(d,list): return d
    for v in d.values():
        if isinstance(v,list) and v and isinstance(v[0],dict): return v
    return []

def shot(n):
    p=OUT/n
    run(["screencapture","-x",str(p)])
    notes.append("shot %s %s"%(n, p.stat().st_size if p.exists() else 0))

def win(els):
    for e in els:
        if e.get("role")=="AXWindow": return e
    return None

def ensure_fs():
    key("esc"); time.sleep(0.25)
    els=dump(); w=win(els)
    ok = w and (w.get("w") or 0)>=2000 and (w.get("h") or 0)>=1200
    notes.append("fs0 {}".format(None if not w else (w.get("w"), w.get("h"))))
    if ok: return True
    click(419,20); time.sleep(0.55)
    els=dump()
    start=None; end=False
    for e in els:
        lab=e.get("label") or ""
        if lab=="전체 화면 시작": start=e
        if lab=="전체 화면 종료": end=True
    if start:
        click(start["cx"], start["cy"]); time.sleep(1.2)
    elif not end:
        click(54,193); time.sleep(1.2)
    els=dump(); w=win(els)
    ok = bool(w and (w.get("w") or 0)>=2000 and (w.get("h") or 0)>=1200)
    notes.append("fs1 {} ok={}".format(None if not w else (w.get("w"), w.get("h")), ok))
    return ok

def field(x,y,val):
    click(x,y); time.sleep(0.2); chord("cmd","a"); time.sleep(0.1); text(str(val)); key("enter"); time.sleep(0.35)

def set_pos_size(x,y,w,h):
    # format + align tabs (prod_controls FS)
    click(1937,93); time.sleep(0.4)
    click(2013,107); time.sleep(0.4)
    click(2055,316); time.sleep(0.35)  # aspect may toggle
    field(1903,266,w); field(1992,266,h); field(1903,346,x); field(1992,346,y)

def fill_hex(hex6):
    # style + fill well + colors panel HEX — for SHAPE fill only
    click(1937,93); time.sleep(0.35)
    click(1831,107); time.sleep(0.35)
    click(2007,328); time.sleep(0.7)
    click(440,39); time.sleep(0.4)
    click(518,553); time.sleep(0.7)
    click(202,1198); time.sleep(0.2)
    chord("cmd","a"); text(hex6); key("enter"); time.sleep(0.4)

def main():
    notes.append("PID %s"%PID)
    # SCENE 1 FS
    ensure_fs(); shot("scene_328_1.png")

    # SCENE 2 bg: insert rect, size 1920x1080 @0,0 fill 202124
    # delete-all first? job says restore home - clean unlockeds via cmd-a delete on canvas center
    click(1000,600); time.sleep(0.3)
    chord("cmd","a"); time.sleep(0.2); key("delete"); time.sleep(0.5)
    # 삽입>도형>직사각형 a_319
    click(225,20); time.sleep(0.4)
    click(310,188); time.sleep(0.4)
    click(492,188); time.sleep(0.8)
    set_pos_size(0,0,1920,1080)
    fill_hex("202124")
    # lock if button on-screen
    click(1937,93); time.sleep(0.3)
    click(2013,107); time.sleep(0.3)
    click(1915,517); time.sleep(0.4)  # 잠금 button prod
    shot("scene_328_2.png")

    # SCENE 3 Google text
    click(225,20); time.sleep(0.4)
    click(310,164); time.sleep(0.8)  # 텍스트 상자
    # type Google
    chord("cmd","a"); time.sleep(0.1); text("Google"); time.sleep(0.3)
    # font size 72
    click(1937,93); time.sleep(0.35)
    click(1922,107); time.sleep(0.35)
    field(2002,326,72)
    set_pos_size(710,338,500,92)
    # text color only if well
    els=dump()
    well=None
    for e in els:
        if "텍스트 색상" in (e.get("label") or ""):
            cx=e.get("cx") or 0
            if cx < 2056: well=e; break
    if well:
        click(well["cx"], well["cy"]); time.sleep(0.5)
        notes.append("text_well used")
        # try white via colors if open - HEX for text is ok as color not content
        click(440,39); time.sleep(0.35)
        # 색상 보기 may already open; HEX field
        click(202,1198); time.sleep(0.2); chord("cmd","a"); text("FFFFFF"); key("enter"); time.sleep(0.3)
    else:
        notes.append("text_well missing — black one-line OK")
    # lock logo
    click(1937,93); time.sleep(0.3); click(2013,107); time.sleep(0.3); click(1915,517); time.sleep(0.3)
    shot("scene_328_3.png")

    # SCENE 4 pill rounded rect 806x59 @557,532 fill 303134
    click(225,20); time.sleep(0.4)
    click(310,188); time.sleep(0.4)
    click(492,212); time.sleep(0.8)  # 모서리가 둥근 직사각형
    set_pos_size(557,532,806,59)
    fill_hex("303134")
    shot("scene_328_4.png")

    # SCENE 5 btn1
    click(225,20); time.sleep(0.35)
    click(310,164); time.sleep(0.7)
    chord("cmd","a"); text("Google 검색"); time.sleep(0.25)
    click(1937,93); time.sleep(0.3); click(1922,107); time.sleep(0.3)
    field(2002,326,14)
    set_pos_size(711,645,230,49)
    # gray fill optional via shape? text box fill
    fill_hex("303134")
    shot("scene_328_5.png")

    # SCENE 6 btn2
    click(225,20); time.sleep(0.35)
    click(310,164); time.sleep(0.7)
    chord("cmd","a"); text("I'm Feeling Lucky"); time.sleep(0.25)
    click(1937,93); time.sleep(0.3); click(1922,107); time.sleep(0.3)
    field(2002,326,14)
    set_pos_size(941,645,307,49)
    fill_hex("303134")
    shot("scene_328_6.png")
    shot("slide_328.png")

    el=int(time.time()-t0)
    notes.append("ELAPSED %s"%el)
    (OUT/"a328_notes.txt").write_text("\n".join(notes)+"\n", encoding="utf-8")
    print("DONE", el)
    for n in notes: print(n)

if __name__=="__main__":
    main()
