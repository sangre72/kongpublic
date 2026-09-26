"""오프라인 라우터 복제(u_5642 충정로7길 C자 우회 원인 조사, 2026-09-26).
game.js buildGlobalGraph/gStartNode/gAstar 를 파이썬으로 그대로 옮겨, 브라우저 없이
출발 후보·거부 간선·경로를 열거한다. 사용: python3 cases/route_u5642_replica.py [--dump]
"""
import json, math, sys, os, re, heapq, time
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
S=6.0; LANE_M=3.25; LW=LANE_M*S

def load_pack(path=os.path.join(ROOT,'data/data6.js')):
    txt=open(path,encoding='utf-8').read()
    def grab(name):
        i=txt.index('const '+name+'='); j=txt.index(';\n',i)
        return json.loads(txt[i+len(name)+7:j])
    return grab('CHUNKS'), grab('TURNS')

def lane_fix(l,o):
    l=l or 2
    if o and l>=7: return max(1,l//2)
    return l

class Graph:
    def __init__(self, CH, TURNS):
        self.N=[]; self.E=[]; self.blds=[]; key={}
        def nid(x,y):
            k=(round(x*10),round(y*10)); i=key.get(k)
            if i is None: i=len(self.N); key[k]=i; self.N.append({'x':x*S,'y':y*S,'e':[]})
            return i
        for ck,c in CH.items():
            for g in c.get('b',[]): self.blds.append(g)
            for r in c.get('r',[]):
                p=r.get('p')
                if not p or len(p)<2: continue
                nd=r.get('nd')
                for i in range(len(p)-1):
                    a=nid(*p[i]); b=nid(*p[i+1])
                    if a==b: continue
                    A=self.N[a];B=self.N[b]
                    ln=math.hypot(B['x']-A['x'],B['y']-A['y'])
                    si=len(self.E)
                    self.E.append({'a':a,'b':b,'len':ln,'l':lane_fix(r.get('l',2),bool(r.get('o'))),'o':bool(r.get('o')),
                                   'w':r.get('w',0),'n':r.get('n',''),'tl':r.get('tl'),
                                   'n0':(nd[0] if nd and i==0 else 0) or 0,'n1':(nd[1] if nd and i+2==len(p) else 0) or 0,
                                   'v':0,'r':r,'chunk':ck})
                    A['e'].append(si); B['e'].append(si)
        self.stitch()
        self.R=TURNS or {}; self.RONLY={}
        for k,v in self.R.items():
            if v.startswith('only_'):
                f,via,t=k.split('|'); self.RONLY.setdefault(f+'|'+via,[]).append(t)
        self.base=(len(self.N),len(self.E)); self.split=[]
    def stitch(self):
        N=len(self.N); comp=[-1]*N; nc=0
        for i in range(N):
            if comp[i]>=0: continue
            st=[i]; comp[i]=nc
            while st:
                u=st.pop()
                for si in self.N[u]['e']:
                    sg=self.E[si]; v=sg['b'] if sg['a']==u else sg['a']
                    if comp[v]<0: comp[v]=nc; st.append(v)
            nc+=1
        self.ncomp=nc
        if nc<2: return
        size=[0]*nc
        for i in range(N): size[comp[i]]+=1
        main=max(range(nc),key=lambda c:size[c])
        R=25*S; g={}
        for i in range(N):
            if comp[i]!=main: continue
            k=(int(self.N[i]['x']/R),int(self.N[i]['y']/R)); g.setdefault(k,[]).append(i)
        byc={}
        for i in range(N): byc.setdefault(comp[i],[]).append(i)
        joined=rej=0
        for c in range(nc):
            if c==main: continue
            bi=bj=-1; bd=R*R
            for i in byc[c]:
                x=self.N[i]['x'];y=self.N[i]['y'];gx=int(x/R);gy=int(y/R)
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        for j in g.get((gx+dx,gy+dy),[]):
                            d=(self.N[j]['x']-x)**2+(self.N[j]['y']-y)**2
                            if d<bd: bd=d;bi=i;bj=j
            if bi>=0:
                if self.gap_ok(self.N[bi]['x'],self.N[bi]['y'],self.N[bj]['x'],self.N[bj]['y']):
                    ln=math.hypot(self.N[bj]['x']-self.N[bi]['x'],self.N[bj]['y']-self.N[bi]['y'])
                    si=len(self.E); self.E.append({'a':bi,'b':bj,'len':ln,'v':1,'o':False,'l':2,'w':0,'n':'(가상)','n0':0,'n1':0,'tl':None})
                    self.N[bi]['e'].append(si); self.N[bj]['e'].append(si); joined+=1
                else: rej+=1
        self.stitch_info=f'{nc}->{nc-joined} (기각 {rej})'
    def gap_ok(self,ax,ay,bx,by):
        # 건물 관통 검사(느리지만 stitch 에서만)
        for gb in self.blds:
            p=gb.get('p')
            if not p or len(p)<3: continue
            # 빠른 bbox 거름
            xs=[q[0]*S for q in p]; ys=[q[1]*S for q in p]
            if max(xs)<min(ax,bx) or min(xs)>max(ax,bx) or max(ys)<min(ay,by) or min(ys)>max(ay,by): continue
            for i in range(len(p)):
                q=p[i]; r=p[(i+1)%len(p)]
                if seg_int(ax,ay,bx,by,q[0]*S,q[1]*S,r[0]*S,r[1]*S): return False
        return True
    # ---- planTo 의 그래프 복원 ----
    def restore(self):
        bn,bs=self.base
        if len(self.N)>bn:
            for si in range(bs,len(self.E)):
                sg=self.E[si]
                for nd in (sg['a'],sg['b']):
                    if nd<bn and si in self.N[nd]['e']: self.N[nd]['e'].remove(si)
            del self.N[bn:]; del self.E[bs:]
            for sp in self.split: self.E[sp]['v']=0
            self.split=[]
    def nearest(self,x,y):
        return min(range(len(self.N)),key=lambda i:(self.N[i]['x']-x)**2+(self.N[i]['y']-y)**2)
    def start_node(self,x,y,ang,log=None):
        fx=math.cos(ang);fy=math.sin(ang); bsi=-1;bem=-1;bt=0;cands=[]
        for si,sg in enumerate(self.E):
            if sg['v']: continue
            A=self.N[sg['a']];B=self.N[sg['b']]; vx=B['x']-A['x'];vy=B['y']-A['y'];L=math.hypot(vx,vy)
            if L<1: continue
            t=((x-A['x'])*vx+(y-A['y'])*vy)/(L*L); t=max(0,min(1,t))
            d=math.hypot(A['x']+vx*t-x,A['y']+vy*t-y)
            if d>50*S: continue
            dot=(vx*fx+vy*fy)/L; align=dot if sg['o'] else abs(dot)
            c=max(0,align); em=math.exp(-0.5*(d/(8*S))**2)*c*c
            cands.append((em,si,d/S,align,t))
            if em>bem: bem=em;bsi=si;bt=t
        if log is not None: log.extend(sorted(cands,reverse=True)[:8])
        if bsi<0: return self.nearest(x,y)
        sg=self.E[bsi];A=self.N[sg['a']];B=self.N[sg['b']]; vx=B['x']-A['x'];vy=B['y']-A['y']
        px=A['x']+vx*bt;py=A['y']+vy*bt
        fa=(A['x']-x)*fx+(A['y']-y)*fy; fb=(B['x']-x)*fx+(B['y']-y)*fy
        fwd=sg['b'] if sg['o'] else (sg['a'] if fa>fb else sg['b'])
        F=self.N[fwd]
        if math.hypot(F['x']-x,F['y']-y)<=8*S and ((F['x']-x)*fx+(F['y']-y)*fy)>0: return fwd
        pi=len(self.N); self.N.append({'x':px,'y':py,'e':[]})
        la=math.hypot(px-A['x'],py-A['y']); lb=math.hypot(B['x']-px,B['y']-py)
        for (a,b,ln) in ((sg['a'],pi,la),(pi,sg['b'],lb)):
            s2=len(self.E); e=dict(sg); e.update({'a':a,'b':b,'len':ln,'v':0}); self.E.append(e)
            self.N[a]['e'].append(s2); self.N[b]['e'].append(s2)
        sg['v']=1; self.split.append(bsi)
        return pi
    def hd(self,a,b):
        A=self.N[a];B=self.N[b]; return math.atan2(B['y']-A['y'],B['x']-A['x'])
    def turn_blocked(self,prev_si,via,next_si):
        if prev_si<0: return False
        A=self.E[prev_si];B=self.E[next_si]
        if not A['w'] or not B['w']: return False
        v=A['n0'] if (A['n0'] and A['a']==via) else (A['n1'] if (A['n1'] and A['b']==via) else 0)
        if not v: return False
        fw=A['w'];tw=B['w']; only=self.RONLY.get(f'{fw}|{v}')
        if only and str(tw) in only: return False
        r=self.R.get(f'{fw}|{v}|{tw}')
        if r and r.startswith('no_'): return True
        if only and fw!=tw: return True
        return False
    def astar(self,s,t,start_ang=None,relax=False,opt=None):
        """opt: dict(prep=True/False, prep_per_lane='old'|'new', prep_nsj=False/True, first_hop=True, upen=60, uminw=19.5, uturn=True, log_rej=list, rej_r=300)"""
        o=opt or {}
        prep=o.get('prep',True); per_new=o.get('prep_per_lane','new'); nsj_gate=o.get('prep_nsj',True); first_hop=o.get('first_hop',True)
        UP=o.get('upen',60)*S; UMINW=o.get('uminw',19.5)*S; allow_u=o.get('uturn',True); rej=o.get('log_rej'); rejR=o.get('rej_r',300)*S
        N=self.N;E=self.E; s0=N[s]
        def _rej(a,b,si,why):
            if rej is None: return
            A=N[a]
            if math.hypot(A['x']-s0['x'],A['y']-s0['y'])>rejR: return
            rej.append((a,b,si,why,E[si]['n'],E[si]['w'],round(math.hypot(A['x']-s0['x'],A['y']-s0['y'])/S)))
        NSj=lambda n: len(N[n]['e'])>=3
        def turn(ai,ao): return ((ao-ai+math.pi*3)%(math.pi*2))-math.pi
        def dl(g): return (g['l'] or 1) if g['o'] else max(1,(g['l'] or 2)//2)
        h=lambda a: math.hypot(N[a]['x']-N[t]['x'],N[a]['y']-N[t]['y'])
        G={(s,-1):0.0}; came={}; seen=set(); heap=[(h(s),s,-1)]; guard=0; t0=time.time()
        stats={'ban':0,'eval':[]}
        while heap and guard<400000:
            guard+=1
            f,n,si_in=heapq.heappop(heap); ck=(n,si_in)
            if n==t:
                p=[n];k=ck
                while k in came: pv=came[k]; p.insert(0,pv[0]); k=pv
                return p,stats
            if ck in seen: continue
            seen.add(ck)
            for si in N[n]['e']:
                sg=E[si]; isU=(si==si_in)
                if isU:
                    if not allow_u: continue
                    if not (NSj(n) and not sg['o'] and (sg.get('roadW') or (sg['l'] or 2)*LW)>=UMINW): continue
                if sg['o'] and sg['a']!=n: _rej(n, sg['a'], si, 'oneway'); continue
                if self.turn_blocked(si_in,n,si): _rej(n, sg['b'] if sg['a']==n else sg['a'], si, 'restrict'); continue
                nb=sg['b'] if sg['a']==n else sg['a']
                if si_in==-1 and start_ang is not None and first_hop:
                    ea=self.hd(n,nb); dd=((ea-start_ang+math.pi*3)%(math.pi*2))-math.pi
                    if abs(dd)>math.pi/2: _rej(n,nb,si,'first-hop>90'); continue
                if prep and not relax and si_in!=-1:
                    pk=came.get(ck); fromN=pk[0] if pk else None
                    if fromN is not None:
                        aIn=self.hd(fromN,n); aOut=self.hd(n,nb); d0=turn(aIn,aOut)
                        leftOrU=isU or (d0<-0.70); rightT=(not isU and d0>0.70)
                        if leftOrU or rightT:
                            want=-1 if leftOrU else 1
                            dist=E[si_in]['len']; node=n; segi=si_in; prev=pk; hops=0; blocked=None; cum=0
                            while prev and hops<12:
                                hops+=1
                                pp=came.get(prev)
                                if prev[1]==-1 or not pp:
                                    if leftOrU and not o.get('free_start'): blocked='opp'
                                    break
                                a1=self.hd(pp[0],prev[0]); a2=self.hd(prev[0],node)
                                if (not nsj_gate) or NSj(prev[0]): cum+=turn(a1,a2)
                                if cum*want<-0.35: blocked='opp'; break
                                if cum*want>0.70: break
                                dist+=E[prev[1]]['len']; node=prev[0]; segi=prev[1]; prev=pp
                            dlc=dl(E[si_in]); per=(50 if dlc>=4 else 25) if per_new=='new' else 50
                            need=(dlc-1)*per*S+30*S
                            if len(stats['eval'])<12: stats['eval'].append(('L' if leftOrU else 'R',round(dist/S),round(need/S),blocked,hops))
                            if blocked=='opp' and dist<need:
                                stats['ban']+=1; _rej(n,nb,si,('L' if leftOrU else 'R')+f'-prep {round(dist/S)}<{round(need/S)}'); continue
                narrow=12 if (sg['l'] or 2)<=1 else (2.5 if (sg['l'] or 2)<=2 else 1)
                rw=sg.get('roadW') or (sg['l'] or 2)*LW
                ng=G[ck]+sg['len']*(40 if sg['v'] else 1)*narrow+((UP+(UP if rw<11*S else 0)) if isU else 0)
                nk=(nb,si)
                if nk not in G or ng<G[nk]:
                    came[nk]=ck; G[nk]=ng
                    if nk not in seen: heapq.heappush(heap,(ng+h(nb),nb,si))
        if not relax and prep:
            stats['relaxed']=1
            p,st2=self.astar(s,t,start_ang,True,opt); st2['relaxed']=1; return p,st2
        return None,stats

def seg_int(x1,y1,x2,y2,x3,y3,x4,y4):
    d=(x2-x1)*(y4-y3)-(y2-y1)*(x4-x3)
    if abs(d)<1e-9: return False
    t=((x3-x1)*(y4-y3)-(y3-y1)*(x4-x3))/d; u=((x3-x1)*(y2-y1)-(y3-y1)*(x2-x1))/d
    return 0<t<1 and 0<u<1

def edge_between(G,a,b):
    for si in G.N[a]['e']:
        sg=G.E[si]
        if (sg['a']==a and sg['b']==b) or (sg['a']==b and sg['b']==a): return si,sg
    return -1,None

def describe(G,p,maxrows=40):
    rows=[]; cum=0
    for i in range(len(p)-1):
        si,sg=edge_between(G,p[i],p[i+1])
        A=G.N[p[i]]
        rows.append((round(cum/S),sg['w'],sg['n'],sg['l'],int(sg['o']),'a>b' if sg['a']==p[i] else 'b>a',round(A['x']/S,1),round(A['y']/S,1)))
        cum+=sg['len']
    total=sum(G.E[edge_between(G,p[i],p[i+1])[0]]['len'] for i in range(len(p)-1))/S
    return rows[:maxrows], total

if __name__=='__main__':
    CH,TURNS=load_pack(); G=Graph(CH,TURNS)
    print('nodes',len(G.N),'segs',len(G.E),'stitch',G.stitch_info,'turns',len(TURNS))
