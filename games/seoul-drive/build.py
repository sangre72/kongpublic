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
# ★u_5256 온디맨드 로드. 청크의 'b'(건물)가 바이트의 ~75%인데 차 주변 3x3 에서만 쓴다.
#   도로('r')는 전역 경로탐색이 전부 필요하므로 인라인 유지 → 경로·검색 결과는 바이트 동일.
#   건물만 games/seoul-drive/data/chunks6/<i>_<j>.b.json 으로 쪼개고 게임이 필요할 때 fetch 한다.
#   ★data/seoul/chunks 는 다른(더 큰) 데이터셋이라 쓰지 않는다 — 지도 자체가 바뀐다.
import json as _json
_i0 = data.index('{')
_obj, _end = _json.JSONDecoder().raw_decode(data[_i0:])
_tail = data[_i0+_end:]                       # 객체 뒤 문장들(ROADS/BLDS/POI 선언 등) 보존
_outdir = 'games/seoul-drive/data/chunks6'; _os.makedirs(_outdir, exist_ok=True)
_nb = 0
for _k, _c in _obj.items():
    _bl = _c.pop('b', None)
    if _bl is not None:
        open(f"{_outdir}/{_k.replace(',', '_')}.b.json", 'w', encoding='utf8').write(
            _json.dumps(_bl, separators=(',', ':'), ensure_ascii=False))
        _nb += len(_bl)
data = data[:_i0] + _json.dumps(_obj, separators=(',', ':'), ensure_ascii=False) + _tail
print(f"chunks6: buildings {_nb} split into {_outdir} ({len(_obj)} chunks); inline map now {len(data)/1048576:.1f} MB")
# ★검색 인덱스(u_5003) — 없으면 검색창은 뜨되 결과가 없다. build_search_index.py 로 생성.
_si = 'games/seoul-drive/data/search.js'
search_js = open(_si).read() if _os.path.exists(_si) else 'const SEARCH=[];'
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
# ★수집 모드(u_5108): 차로변경·추월·정지출발을 교사가 실제로 시연한다.
#   --lanedemo 는 12초 타이머로 무작정 차로를 바꾼다 — 그건 추월이 아니다.
#   여기서는 '앞차가 느리면 옆차로를 확인하고 나갔다가 돌아온다'는 실제 판단을 넣는다.
#   ★모드다. 기본 주행 동작은 건드리지 않는다(이 블록이 없으면 예전 그대로).
if '--collect-ot' in sys.argv:
    te += r"""
;(function(){
  /* 추월/차로변경/정지출발 수집 모드.
     상태기계: KEEP -> (앞차 느림 & 옆차로 빔) -> OUT -> PASS -> BACK -> KEEP */
  function go(){
    var T=window.__teach;
    if(!T||!T.setLane||typeof cars==='undefined'){ setTimeout(go,500); return; }

    /* 옆차로가 비었나 — gap() 은 '내 진행방향 앞'만 본다.
       차로를 옮길지 판단하려면 옆으로 dx 만큼 떨어진 가상의 지점에서
       앞뒤를 같이 봐야 한다(뒤에서 오는 차를 놓치면 사고가 난다). */
    function laneClear(dx, fwdM, backM){
      var ca=Math.cos(me.ang), sa=Math.sin(me.ang);
      /* 내 차 기준 좌우 dx(m) 이동한 가상 위치 */
      var ox=me.x - Math.sin(me.ang)*dx*S, oy=me.y + Math.cos(me.ang)*dx*S;
      for(var i=0;i<cars.length;i++){
        var o=cars[i]; if(!o.alive||o===me) continue;
        var ddx=o.x-ox, ddy=o.y-oy;
        var f=(ddx*ca+ddy*sa)/S;        // 전방 성분(m)
        var l=(-ddx*sa+ddy*ca)/S;       // 횡 성분(m)
        if(Math.abs(l) > 2.2) continue; // 그 차로에 없음
        if(f < fwdM && f > -backM) return false;
      }
      return true;
    }
    /* 앞차(같은 차로, 전방 40m 이내) */
    function lead(){
      var ca=Math.cos(me.ang), sa=Math.sin(me.ang), best=null, bd=1e9;
      for(var i=0;i<cars.length;i++){
        var o=cars[i]; if(!o.alive||o===me) continue;
        var dx=o.x-me.x, dy=o.y-me.y;
        var f=(dx*ca+dy*sa)/S, l=(-dx*sa+dy*ca)/S;
        if(f<=0||f>40) continue;
        if(Math.abs(l)>2.0) continue;
        if(f<bd){bd=f;best=o;}
      }
      return best?{car:best,d:bd}:null;
    }

    var st='KEEP', t0=0, home=null, passT=0;
    window.__ot={st:st,n:0};
    setInterval(function(){
      var now=Date.now()/1000;
      var L=lead();
      var nl=T.laneMax||1;
      var cur=Math.round(T.laneF!==undefined?T.laneF:0);

      if(st==='KEEP'){
        /* 추월 판단: 앞차가 있고, 나보다 느리고, 간격이 좁혀졌다 */
        if(L && L.d<22 && L.car.v < me.v*0.85 && nl>=2){
          /* 옆차로 선택: 안쪽(추월차로)이 우선, 없으면 바깥 */
          var tgt = (cur>0)? cur-1 : cur+1;
          if(tgt>=0 && tgt<nl){
            var dx = (tgt-cur)*3.25;      // 차로폭(m), 부호 포함
            if(laneClear(dx, 45, 18)){
              home=cur; T.setLane(tgt); st='OUT'; t0=now;
              window.__ot={st:st,n:(window.__ot.n||0)+1};
            }
          }
        }
      } else if(st==='OUT'){
        /* 차로 이동이 끝났나 */
        if(!T.laneMoving || now-t0>4){ st='PASS'; t0=now; passT=now; }
      } else if(st==='PASS'){
        /* 추월당한 차를 실제로 지나쳤나 — 뒤로 보내야 복귀한다 */
        var done = true;
        if(L && L.d<30) done=false;       // 아직 앞에 뭔가 있으면 더 간다
        if(done && now-passT>1.5){ st='BACK'; t0=now; }
        if(now-t0>8){ st='BACK'; t0=now; } // 안전장치
      } else if(st==='BACK'){
        /* 원래 차로로 복귀 — 비었을 때만 */
        if(home!==null && laneClear((home-cur)*3.25, 30, 14)){
          T.setLane(home); st='KEEP'; home=null;
          window.__ot={st:st,n:window.__ot.n};
        } else if(now-t0>6){ st='KEEP'; home=null; }
      }
      window.__ot.st=st;
    }, 250);
  }
  setTimeout(go, 3000);
})();
"""

# ★정지-출발 + 이탈복구 수집 모드(u_5108).
#   왜 따로 두나: 현재 데이터는 v<0.5 가 0프레임, on_road=0 이 0.29% 다.
#   '멈춘 차'와 '차로를 벗어난 차'를 모델이 한 번도 본 적이 없다.
#   주기적으로 (a) 완전정지 후 재출발, (b) 차를 비스듬히/차로 밖으로 밀어놓고
#   교사가 스스로 되돌아오게 한다. 그 복구 장면이 라벨로 남는다.
if '--collect-recover' in sys.argv:
    # ★이탈 허용 플래그를 실제로 켠다(u_5158 실측: 이 단계에서 이탈 1건뿐이었다).
    #   game.js 는 __COLLECT_RECOVER 를 읽어 '도로 밖으로 나가려는 이동'의 되돌림을
    #   끄는데, 그걸 true 로 만드는 곳이 어디에도 없었다. 그래서 차가 물리적으로
    #   도로를 못 벗어났고, 복구 장면이 라벨에 안 남았다.
    te += "\n;window.__COLLECT_RECOVER=1;\n"
    te += r"""
;(function(){
  function go(){
    var T=window.__teach;
    if(!T||typeof me==='undefined'||typeof nearestSeg!=='function'){ setTimeout(go,500); return; }
    window.__rec={n:0,st:'-'};
    var busy=false;
    setInterval(function(){
      if(busy) return;
      /* 사고 직후에는 건드리지 않는다(복구 로직과 충돌) */
      if(typeof crashHold!=='undefined' && crashHold) return;
      var r=Math.random();
      if(r<0.18){
        /* ★정지는 경로주행 중에도 안전하다 — 위치를 옮기지 않기 때문이다.
           단 정지 자체가 길어지면 driveAuto 의 정체복구가 끼어드니 2.5초로 짧게 끊는다. */
        /* (a) 완전 정지 -> 2.5초 대기 -> 재출발.
           ★me.v=0 를 한 번만 찍으면 heavy 교통에서 앞차에 막혀 그대로 눌러앉는다
             (실측: 의도한 2.5초 대신 10초 정지가 나왔다). 정지 구간 동안만
             매 프레임 0 으로 눌러두고, 끝나면 확실히 놓아준다. */
        busy=true; window.__rec.st='STOP';
        var hold=setInterval(function(){ me.v=0; }, 30);
        setTimeout(function(){ clearInterval(hold); busy=false;
                               window.__rec.st='GO'; window.__rec.n++; }, 2500);
      } else {
        /* (b) 차로 밖으로 밀어낸다 — ★도로 폭에 비례해서 민다(u_5158 실측).
           고정 2.5~4.5m 로는 4차로(반폭 6.5m)·6차로(10.5m)에서 **도로 안에 그대로 남는다.**
           실측: 이탈복구 단계인데 이탈이 352프레임 중 7건(2%)뿐이었다.
           오드가 실제로 달리는 건 3~5차로라, 이 폭에서 못 나가면 복구 장면이 안 생긴다.
           ⇒ 반폭보다 확실히 크게(1.15~1.5배) 민다.
           교사의 cross-track 보정이 스스로 되돌아오는 장면을 만든다. */
        var n=nearestSeg(me.x,me.y); if(!n) return;
        /* ★경로주행 중에는 밀어내지 않는다(u_5108 실측).
           driveAuto 는 웨이포인트 인덱스를 들고 있어서, 차를 옆으로 순간이동시키면
           경로에서 벗어났다고 판단해 복구/재계획에 들어간다. 실측: 이 모드를 켜면
           진행률이 0.18 에서 더 안 오르고 v<0.5 가 77% 였다(끄면 0.91 까지 간다).
           이탈복구 장면은 '경로 없이 교사가 직접 모는' 구간에서만 만든다. */
        if(typeof auto!=='undefined' && auto.on && auto.wp && auto.wp.length) return;
        var side=Math.random()<0.5?-1:1;
        /* ★도로 반폭에 비례해 민다. 고정값이면 넓은 도로에서 못 나간다. */
        var _n=nearestSeg(me.x,me.y);
        var _half=_n&&_n.s ? (_n.s.roadW/S)/2 : 3.5;
        var dx=_half*(1.15+Math.random()*0.35)*side;   // 반폭의 1.15~1.5배
        me.x += -Math.sin(me.ang)*dx*S;
        me.y +=  Math.cos(me.ang)*dx*S;
        me.ang += side*(0.21+Math.random()*0.23);
        /* 목표 차로 추종 상태를 초기화해 '현재 위치에서' 다시 수렴하게 한다 */
        T.laneF=undefined; T.laneSet=false;
        window.__rec.st='OFF'; window.__rec.n++;
      }
    }, 4500);   /* ★14초 -> 4.5초(u_5158). 이탈 유발이 너무 드물어 복구 장면이
                   240초에 7건(2%)밖에 안 모였다. 교사가 1~2초면 복귀하므로
                   짧게 반복해야 '벗어남 -> 되돌아옴' 쌍이 충분히 쌓인다. */
  }
  setTimeout(go, 4000);
})();
"""

# ★수집 빌드는 교사를 반드시 켠 상태로 시작한다(u_5108 실사고).
#   T.last 는 T.auto 가 true 일 때만 갱신된다(game.js 2882/2930). 꺼져 있으면
#   steer/thr/brake 코드픽셀이 첫 프레임 값에 얼어붙은 채로 수집된다 —
#   실측: 145프레임 내내 steer=-0.034 단일값(v 만 정상 변동).
#   localStorage 의 kb_teach 가 'off' 로 남아 있으면(모델 검증 작업 뒤) 그대로
#   꺼진 채 수집되므로, 빌드에서 강제로 덮어쓴다.
if '--collect-ot' in sys.argv or '--collect-recover' in sys.argv:
    # 문자열 치환은 공백 한 칸에도 깨진다(실측: 치환 실패로 라벨이 계속 얼어 있었다).
    # 로드 후 실행되는 블록으로 확실하게 켠다.
    te += r"""
;(function(){
  try{ localStorage.setItem('kb_teach','fwd'); }catch(e){}
  function on(){
    var T=window.__teach;
    if(!T){ setTimeout(on,300); return; }
    T.auto=true; if(!T.mode||T.mode==='off') T.mode='fwd';
  }
  on();
  /* teacher.js 의 300ms 폴러가 localStorage 를 다시 읽어 끄지 않도록 계속 눌러둔다 */
  setInterval(function(){
    var T=window.__teach; if(T && !T.auto){ T.auto=true; if(T.mode==='off') T.mode='fwd'; }
  }, 500);
})();
"""

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
    head + '<script>' + data + '</script>\n<script>' + search_js + '</script>\n'
         + '<script>' + gm + '</script>\n<script>' + te + '</script>\n')
print('built teacher=' + ('OFF' if off else 'ON')
      + (' dagger=ON' if dag else '') + (' demo=ON' if demo else '')
      + ' traffic=' + _tf + ' speed=' + str(_kmh) + 'km/h')
