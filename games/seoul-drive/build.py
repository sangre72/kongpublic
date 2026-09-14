"""index.html 빌드. 기본은 교사 ON(데이터 수집용), --teacher-off 면 교사 OFF(모델 검증용).

WHY: 모델을 검증하려면 교사를 꺼야 하는데, 샌드박스 iframe이라 밖에서 끌 방법이 없다.
     키 입력도 안 들어가고(실측), 콘솔/AppleScript도 막혀 있다.
     그래서 '꺼진 상태로 빌드'가 유일하게 확실한 방법이다.
"""
import sys
off = '--teacher-off' in sys.argv or '--dagger' in sys.argv
dag = '--dagger' in sys.argv
demo = '--demo' in sys.argv      # 강남역 → 종합운동장 자동주행 데모
# ★교통량 3단계(u_4972): --traffic light|medium|heavy. 기본 medium.
#   아티팩트는 샌드박스라 URL 파라미터가 안 들어오므로 빌드에 박아 넣는다.
_tf = 'medium'
if '--traffic' in sys.argv:
    _i = sys.argv.index('--traffic')
    if _i + 1 < len(sys.argv) and sys.argv[_i+1] in ('light','medium','heavy'):
        _tf = sys.argv[_i+1]
# ★목표 주행속도(u_4975): --speed <km/h>. 기본 45.
#   교사가 이 속도를 맞춰 달리고, 앞이 막히면 안전이 우선이다.
_kmh = 45
if '--speed' in sys.argv:
    _i = sys.argv.index('--speed')
    if _i + 1 < len(sys.argv):
        try: _kmh = int(sys.argv[_i+1])
        except ValueError: pass
head = open('games/seoul-drive/index.html').read().split('<script>')[0]
# ★맵 데이터를 저장소 안으로(2026-09-14 u_4960). /tmp 는 재부팅하면 날아간다.
import os as _os
_d = 'games/seoul-drive/data/data6.js'
data = open(_d if _os.path.exists(_d) else '/tmp/data6.js').read()
gm   = open('games/seoul-drive/game.js').read()
te   = open('games/seoul-drive/teacher.js').read()
gm = "window.__TRAFFIC='%s';window.__TARGET_KMH=%d;\n" % (_tf, _kmh) + gm
# ★차로변경 데모(u_4992): --lanedemo 면 1차로에서 달리다 3차로로 옮긴다.
#   아티팩트는 샌드박스라 콘솔/URL 로 못 건드린다 → 빌드에 넣는 수밖에 없다.
if '--sigdemo' in sys.argv:
    # ★신호등 확인용: 가장 가까운 신호등 앞에 차를 세운다(u_4999 검증)
    gm += '''
;(function(){
  function go(){
    if(typeof signals==='undefined'||!signals.length){ setTimeout(go,600); return; }
    var best=null,bd=1e18;
    for(var i=0;i<signals.length;i++){
      var d=(signals[i].x-me.x)*(signals[i].x-me.x)+(signals[i].y-me.y)*(signals[i].y-me.y);
      if(d<bd){bd=d;best=signals[i];}
    }
    if(!best) return;
    /* 신호는 sg.ang 방향을 '바라보는' 차에게 보이도록 배치돼 있다.
       그 반대편(-ang)에서 다가가야 정면으로 보인다. */
    me.x=best.x-Math.cos(best.ang)*16*S; me.y=best.y-Math.sin(best.ang)*16*S;
    me.ang=best.ang; me.v=0;
    cam.x=(me.x+best.x)/2; cam.y=(me.y+best.y)/2;
    if(typeof streamWorld==='function') streamWorld(true);
    if(window.__teach) window.__teach.auto=false;   // 멈춰서 관찰
    cam.z=1.8;
  }
  setTimeout(go,3000);
})();
'''
if '--lanedemo' in sys.argv:
    te += '''
;(function(){
  /* 12초 뒤 1차로(0) -> 3차로(2) 로 변경. 화면 readout 의 ln 에 진행이 보인다. */
  function go(){
    var T=window.__teach; if(!T||!T.setLane){ setTimeout(go,500); return; }
    /* ★목표 차로는 '그 도로에 실제로 있는' 범위여야 한다(u_5001 실측).
       laneMax 를 보고 마지막 차로로 간다 — 2차로 도로에서 3차로를 찍으면
       도로 밖을 목표로 삼아 조향이 포화된다. */
    /* ★시작 차로를 강제하지 않는다(u_5001 실측).
       T.setLane(0) 을 먼저 걸면, 차가 이미 바깥 차로에 있을 때 큰 횡이동이
       즉시 요구돼 조향이 시작부터 포화된다. 지금 있는 차로에서 출발한다. */
    /* ★목표는 lane0 <-> lane1 로만 왕복한다(u_5001).
       도로마다 차로 수가 달라서 '가장 바깥'을 찍으면 좁은 구간에서 범위를
       벗어난다. 0과 1은 어느 도로에나 있으므로 항상 유효하다.
       12초마다 번갈아 바꿔서, 화면에서 오갈 수 있게 한다. */
    var flip = 0;
    setInterval(function(){
      if(!T.laneMax || T.laneMax < 2) return;   // 편도 1차로면 바꿀 곳이 없다
      flip = flip ? 0 : 1;
      T.setLane(flip);
      window.__laneDemo = 'go' + (flip+1);
    }, 12000);
  }
  setTimeout(go, 3000);
})();
'''
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
  /* 무역센터(코엑스) 실좌표 37.5115,127.0595 → 게임좌표 (2649,-1225).
     그 지점 자체는 간선 1개짜리 막다른 노드라 본 도로망과 끊겨 있어서(실측),
     연결된 가장 가까운 지점(2760,-1360, 무역센터에서 175m)을 목적지로 쓴다. */
  var GOAL={x:2760,y:-1360};         // 무역센터 앞 (약 3km)
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
      + (' dagger=ON' if dag else '') + (' demo=ON' if demo else '')
      + ' traffic=' + _tf + ' speed=' + str(_kmh) + 'km/h')
