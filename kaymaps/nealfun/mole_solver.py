import numpy as np, microvis, time, subprocess
B=np.load('n9_board.npy'); X0,X1,Y0,Y1=[int(v) for v in B]
CB=[1,331,665,1000,1330]; RB=[2,333,667,1002,1336]

def board(): return microvis.grab_rect(X0,Y0,X1-X0,Y1-Y0)

def read(a=None):
    a = board() if a is None else a
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mole=(r>g+15)&(g>b+10)&(r>80)&(r<200)
    chk=(np.abs(r-70)<45)&(np.abs(g-130)<45)&(np.abs(b-225)<45)
    M=set(); C=set()
    for ri in range(4):
        for ci in range(4):
            ys=slice(RB[ri],RB[ri+1]); xs=slice(CB[ci],CB[ci+1])
            if mole[ys,xs].sum()>2500: M.add((ri,ci))
            if chk[ys,xs].sum()>500: C.add((ri,ci))
    return M,C

def tap(ri,ci):
    cx=(CB[ci]+CB[ci+1])//2; cy=(RB[ri]+RB[ri+1])//2
    microvis.click((X0+cx)/2.0,(Y0+cy)/2.0)

def clear_all(maxiter=40):
    for _ in range(maxiter):
        M,C=read()
        if not C: return True
        tap(*next(iter(C))); time.sleep(0.05)
    return False
