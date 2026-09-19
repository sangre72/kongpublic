/* turn:lanes(tl) 파서·차로 선택 단위시험 (2026-09-19)
   실행: node games/seoul-drive/test_turn_lanes.js
   game.js 의 parseTurnLanes / tlPickLane / tlSetsFor 를 원문 그대로 잘라 실행한다(재구현 드리프트 방지).
   차로 규약: 인덱스 0 = 진행방향 맨 왼쪽(1차로), l-1 = 맨 오른쪽. */
const fs=require('fs'), vm=require('vm'), path=require('path'), assert=require('assert');
const src=fs.readFileSync(path.join(__dirname,'game.js'),'utf8');
function grab(name){
  const i=src.indexOf('function '+name+'('); assert(i>=0, name+' not found in game.js');
  let depth=0, j=src.indexOf('{',i);
  for(;j<src.length;j++){ if(src[j]==='{')depth++; else if(src[j]==='}'){depth--; if(!depth)break;} }
  return src.slice(i,j+1);
}
const ctx={window:{}}; vm.createContext(ctx);
vm.runInContext(grab('parseTurnLanes')+'\n'+grab('tlPickLane')+'\n'+grab('tlSetsFor'), ctx);
const {parseTurnLanes,tlPickLane,tlSetsFor}=ctx;
// vm 컨텍스트의 Array 는 다른 realm 이라 deepStrictEqual 이 프로토타입 불일치로 실패한다 → JSON 비교
const eq=(a,b,m)=>assert.strictEqual(JSON.stringify(a),JSON.stringify(b),m);

// parser
eq(parseTurnLanes("left|through|through;right"), [['left'],['through'],['through','right']]);
eq(parseTurnLanes("|through|"), [['none'],['through'],['none']], 'empty token = none');
eq(parseTurnLanes(" Left | Slight_Right "), [['left'],['slight_right']], 'trim+lowercase');
eq(parseTurnLanes(""), null); eq(parseTurnLanes(undefined), null); eq(parseTurnLanes(42), null);
eq(parseTurnLanes("through"), [['through']]);

// picks
const A=parseTurnLanes("left|through|through;right");
eq(tlPickLane(A,'R'), 2, 'R = rightmost lane containing right');
eq(tlPickLane(A,'L'), 0, 'L = leftmost lane containing left');
eq(tlPickLane(A,'S',2), 2, 'S: through;right lane is still through');
eq(tlPickLane(A,'S',0), 1, 'S: lane0 is left-only -> nearest through = 1');
const B=parseTurnLanes("left|left|through|right|right");
eq(tlPickLane(B,'L'), 0, 'two left lanes -> leftmost left = 0');
eq(tlPickLane(B,'R'), 4, 'two right lanes -> rightmost right = 4');
eq(tlPickLane(B,'S',4), 2, 'right-only lane -> nearest through');
eq(tlPickLane(B,'U'), 0, 'U without reverse falls back to L rule (leftmost left)');
eq(tlPickLane(parseTurnLanes("reverse;left|through"),'U'), 0, 'U prefers reverse lane');
eq(tlPickLane(parseTurnLanes("through|through"),'R'), -1, 'no right lane -> -1');
eq(tlPickLane(parseTurnLanes("left|right"),'S',0), -1, 'no through lane -> -1');
eq(tlPickLane(null,'R'), -1);

// tlSetsFor: lane-count guard + cache + mismatch counter
const sg={tl:"left|through|through;right", l:3, o:true};
eq(tlSetsFor(sg,3), A, 'count matches -> sets');
assert.strictEqual(tlSetsFor(sg,3), sg._tlc, 'cached on seg');
const sg2={tl:"left|through", l:8, o:true};
eq(tlSetsFor(sg2,8), null, 'count mismatch -> null'); eq(ctx.window.__tlMismatch, 1);
tlSetsFor(sg2,8); eq(ctx.window.__tlMismatch, 1, 'mismatch counted once per seg (cache)');
eq(tlSetsFor({l:2},1), null, 'no tl -> null');
console.log('test_turn_lanes: all OK');
