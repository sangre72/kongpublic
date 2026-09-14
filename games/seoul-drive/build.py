"""index.html 빌드. 기본은 교사 ON(데이터 수집용), --teacher-off 면 교사 OFF(모델 검증용).

WHY: 모델을 검증하려면 교사를 꺼야 하는데, 샌드박스 iframe이라 밖에서 끌 방법이 없다.
     키 입력도 안 들어가고(실측), 콘솔/AppleScript도 막혀 있다.
     그래서 '꺼진 상태로 빌드'가 유일하게 확실한 방법이다.
"""
import sys
off = '--teacher-off' in sys.argv or '--dagger' in sys.argv
dag = '--dagger' in sys.argv
demo = '--demo' in sys.argv      # 강남역 → 종합운동장 자동주행 데모
head = open('games/seoul-drive/index.html').read().split('<script>')[0]
# ★맵 데이터를 저장소 안으로(2026-09-14 u_4960). /tmp 는 재부팅하면 날아간다.
import os as _os
_d = 'games/seoul-drive/data/data6.js'
data = open(_d if _os.path.exists(_d) else '/tmp/data6.js').read()
gm   = open('games/seoul-drive/game.js').read()
te   = open('games/seoul-drive/teacher.js').read()
if off:
    te = te.replace("let mode='fwd';", "let mode='off';   /* 검증 빌드: 교사 OFF */")
    # 교사가 꺼져 있어도 도로 위에서 출발해야 모델이 길을 볼 수 있다.
    gm = 'window.__SPAWN_ON_ROAD=true;\n' + gm
if dag:
    # 교사는 주행 안 하고 정답만 계산 → 모델이 겪는 상황에 대한 라벨을 모은다(DAgger).
    te = te.replace('T.dagger = false;', 'T.dagger = true;')
if demo:
    # ★데모(u_4947/u_4948): 짧은 구간 목적지 주행 — Tim Hortons → 삼성딜라이트 홍보관.
    #   4km(종합운동장)는 3x3 청크(±1.5km)만 그래프에 올리는 구조라 경로가 안 잡힌다.
    #   같은 청크 범위 안(약 870m)이면 기존 planTo 로 문제없이 동작한다.
    gm += '''
;(function(){
  var FROM={x:0,y:0};                // 강남역
  var GOAL={x:3842,y:-1225};         // 잠실종합운동장 (약 4km)
  function start(){
    window.__demoTry=(window.__demoTry||0)+1;
    try{
      if(typeof segs==='undefined'||!segs.length){ window.__demoWhy='nosegs'; return; }
      if(typeof planTo!=='function'){ window.__demoWhy='noplanTo'; return; }
      if(typeof nearestSeg!=='function'){ window.__demoWhy='nonearest'; return; }
      var s0=nearestSeg(FROM.x*S, FROM.y*S);
      if(s0){ me.x=s0.px; me.y=s0.py; me.ang=s0.s.ang; me.v=0;
              if(typeof streamWorld==='function') streamWorld(true); }
      planTo(GOAL.x*S, GOAL.y*S);
      window.__demoGoal=GOAL;
      window.__demoWhy = (auto.wp&&auto.wp.length) ? 'ok' : 'nopath';
    }catch(e){ window.__demoWhy='err:'+(e&&e.message||'?'); }
  }
  var tries=0;
  function ensure(){
    tries++;
    try{
      if(!auto.on || !auto.wp || !auto.wp.length) start();
      if(tries<20) setTimeout(ensure, 900);
    }catch(e){ if(tries<20) setTimeout(ensure,900); }
  }
  setTimeout(ensure, 2500);
})();
'''
open('games/seoul-drive/index.html','w').write(
    head + '<script>' + data + '</script>\n<script>' + gm + '</script>\n<script>' + te + '</script>\n')
print('built teacher=' + ('OFF' if off else 'ON')
      + (' dagger=ON' if dag else '') + (' demo=ON' if demo else ''))
