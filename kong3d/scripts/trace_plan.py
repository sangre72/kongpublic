"""Traced-polygon plan v2: per-CONNECTED-COMPONENT boundary polygons (real shapes,
not icons, not bowties). Each region mask -> label components -> for each big
component, trace its outer contour as an ordered polygon (many verts).
usage: python3 trace_plan.py <ref.jpg> <out.json>
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

path, out = sys.argv[1], sys.argv[2]
GW, GH = 320, 240
im = Image.open(path).convert("RGB").resize((GW, GH)).filter(ImageFilter.MedianFilter(5))
a = np.asarray(im, float)
cw, ch = 1000.0/GW, 740.0/GH
def CX(gx): return round(gx*cw,1)
def CY(gy): return round(gy*ch,1)
R,G,B = a[...,0],a[...,1],a[...,2]; lum=a.mean(2); sat=a.max(2)-a.min(2)

cloud = (lum>180)&(sat<28)
green = (G>R+3)&(G>B)
water = (sat<40)&(lum>70)&(lum<175)&~green&~cloud
# brown bank = only lower-half + right-of-center (kills false-brown inside left dark conifers)
xg,yg=np.meshgrid(np.arange(GW),np.arange(GH))
region_bank=(yg>0.55*GH)&(xg>0.42*GW)
brown = (R>=G)&(G>B)&(lum<175)&(lum>60)&~green&~cloud&region_bank
tdark = green&(lum<70); tmid=green&(lum>=70)&(lum<110); tlite=green&(lum>=110)

from skimage import measure
def contour_poly(compmask, nverts=40):
    """ordered outer boundary via marching-squares (find_contours) — follows the real
       silhouette without self-crossing. take the longest contour, decimate to nverts."""
    if compmask.sum()<30: return None
    padded=np.pad(compmask.astype(float),1)
    cs=measure.find_contours(padded,0.5)
    if not cs: return None
    c=max(cs,key=len)                 # longest = outer boundary
    c=c-1                             # undo pad
    if len(c)>nverts:
        idx=np.linspace(0,len(c)-1,nverts).astype(int)
        c=c[idx]
    return [[CX(x),CY(y)] for (y,x) in c]   # find_contours gives (row,col)=(y,x)

def components(mask, minpx=180, maxn=8):
    lab,n=ndimage.label(mask)
    sizes=[(i,(lab==i).sum()) for i in range(1,n+1)]
    sizes=[s for s in sizes if s[1]>=minpx]
    sizes.sort(key=lambda t:-t[1])
    return [lab==i for i,_ in sizes[:maxn]]

polys=[]
def add_region(mask,color,minpx=180,maxn=8,nv=40):
    for comp in components(mask,minpx,maxn):
        p=contour_poly(comp,nv)
        if p: polys.append({"c":color,"pts":p})

# order back->front: clouds(on sky), tree tones dark->light, water, brown, grass
add_region(cloud,"#eef2f6",minpx=120,maxn=10,nv=32)
add_region(tdark,"#2f4230",minpx=300,maxn=6,nv=44)
add_region(tmid ,"#3d5636",minpx=300,maxn=6,nv=44)
add_region(tlite,"#5c7d45",minpx=300,maxn=6,nv=44)
add_region(water,"#96988c",minpx=200,maxn=3,nv=32)
add_region(brown,"#8a7355",minpx=200,maxn=4,nv=28)
gf=green.copy(); gf[:int(0.60*GH),:]=False
add_region(gf,"#8aa54a",minpx=400,maxn=3,nv=28)

json.dump({"polys":polys}, open(out,"w"))
print("polys",len(polys),"verts",sum(len(p["pts"]) for p in polys))
from collections import Counter
c=Counter(p["c"] for p in polys)
for k,v in c.items(): print(k,v)
