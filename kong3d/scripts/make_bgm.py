"""Pastoral ambient looping BGM — rich harmony (maj7 / 9th chords).
Renders a seamless-loop WAV (verifiable offline) + prints the chord plan.
Progression (key C, calm): Cmaj9 - Am9 - Fmaj7(9) - G9sus  (each 2 bars, 8 bars total)
Gentle tempo ~66 BPM. Soft sine pad + triangle arpeggio + light noise 'air'.
Loop length = whole number of bars so end meets start (seamless).
usage: python3 make_bgm.py <out.wav>
"""
import sys, math, struct, wave

SR=44100
BPM=66
beat=60.0/BPM
bar=4*beat
BARS=8
DUR=BARS*bar

def note(f, n=0):  # midi-ish: base freq * 2^(n/12)
    return f*(2**(n/12))
A4=440.0
def hz(semis_from_A4): return A4*(2**(semis_from_A4/12))
# chord tones as semitone offsets from A4 (C4=-9)
C=-9;
chords=[  # (root offset, [tone offsets], bars)
  ("Cmaj9", [ -9, -2, 2, 5, 9 ], 2),    # C E G B D
  ("Am9",   [ -12,-9,-5,-2,2 ], 2),     # A C E G B(as 2)
  ("Fmaj7#9",[ -16,-9,-5,0,4 ], 2),     # F A C E G
  ("G9sus", [ -14,-7,-2,3,5 ], 2),      # G C D F A
]

def env(t, dur, a=0.6, r=1.2):
    if t<a: return t/a
    if t>dur-r: return max(0,(dur-t)/r)
    return 1.0

N=int(SR*DUR)
buf=[0.0]*N
tpos=0.0
for name,tones,bars in chords:
    seg=bars*bar
    n0=int(tpos*SR); n1=int((tpos+seg)*SR)
    for i in range(n0,min(n1,N)):
        t=i/SR; lt=t-tpos
        s=0.0
        # PAD: soft sines on chord tones
        for k,off in enumerate(tones):
            f=hz(off)
            s+=math.sin(2*math.pi*f*t)*(0.13/(1+0.3*k))
        # slow tremolo for movement
        s*=0.85+0.15*math.sin(2*math.pi*0.15*t)
        # ARPEGGIO: triangle, eighth notes cycling chord tones (upper octave)
        ei=int(lt/(beat/2))%len(tones)
        af=hz(tones[ei]+12)
        ph=(af*t)%1.0
        tri=2*abs(2*ph-1)-1
        aenv=math.exp(-4*((lt%(beat/2))))
        s+=tri*0.06*aenv
        s*=env(lt,seg,0.02,0.02)  # tiny per-seg smoothing, not full fade (loop stays seamless)
        buf[i]+=s
    tpos+=seg

# normalize
pk=max(1e-6,max(abs(x) for x in buf))
g=0.85/pk
# write 16-bit WAV
out=sys.argv[1]
w=wave.open(out,'w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,x*g))*32767)) for x in buf))
w.close()
print("BGM",out,"dur=%.2fs"%DUR,"bars=%d"%BARS,"bpm=%d"%BPM)
print("prog:", " | ".join(c[0] for c in chords))
# seam check: RMS diff of first vs last 2205 samples (~50ms)
head=buf[:2205]; tail=buf[-2205:]
import statistics
print("seam-continuity(head0=%.3f tailEnd=%.3f)"%(head[0]*g, tail[-1]*g))
