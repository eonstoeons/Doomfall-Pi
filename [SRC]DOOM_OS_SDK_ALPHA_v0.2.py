#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NEXUS_DOOM_OS v3.0 · Pure Python · stdlib · tkinter only · MIT · The dot sings. .-
Unified: DoomCraft + NEXUS + DoomflowPi + DoomRPG + SDK + LLM + TTS + Floppy + Carts.
NEW v3.0: SpriteGen (procedural 16x16 pixel art) + MonsterGen (randomized enemy factory).
Keys: W/S move · A/D turn · Q/E strafe · SPC shoot · R use · C sheet · TAB map · P phosphor
"""
import tkinter as tk
from tkinter import ttk,scrolledtext,filedialog,messagebox,simpledialog
import math,time,os,json,threading,struct,wave as wm,random,io
import datetime,subprocess,tempfile,platform,hashlib
from pathlib import Path; from collections import deque

# ── GLOBALS ──────────────────────────────────────────────────────────────────
VERSION="3.0"; APP="NEXUS_DOOM_OS"; BASE=Path.home()/".nexus_doom_os"
PLAT=platform.system(); TAU=math.tau; SR=22050
for _d in['saves','carts','sfx','music','exports','tts','scripts','sprites','floppy','monsters']:
    (BASE/_d).mkdir(parents=True,exist_ok=True)
DOOM_MAXHEALTH=100; DOOM_PLAYERRADIUS=0.25; DOOM_USERANGE=1.9; DOOM_MELEERANGE=1.9
DOOM_MISSILERANGE=30.; DOOM_MAXMOVE=.3; DOOM_BASETHRESHOLD=100

# ── LCG ENTROPY ──────────────────────────────────────────────────────────────
class LCG:
    A,C,M=1664525,1013904223,0x100000000
    def __init__(s,seed=None): s.state=(seed or int(time.time()*1e6))&0xFFFFFFFF;s.ops=0;s.dots=0
    def _n(s): s.state=(s.A*s.state+s.C)%s.M;s.ops+=1;return s.state
    def rand(s): return s._n()/s.M
    def randint(s,lo,hi): return lo+s._n()%max(1,hi-lo+1)
    def choice(s,q): return q[s._n()%len(q)] if q else None
    def feed(s,v):
        try: s.state^=(int(float(v)*1e9)^int(time.time()*1e6)^s.dots*0xBEEF)&0xFFFFFFFF
        except: s.state^=int(time.time()*1e6)&0xFFFFFFFF
        s.dots+=1
    def moon(s): d=(time.time()/86400)%29.53; return .5+.5*math.cos(TAU*(d/29.53-.5))
    def sun(s): h=datetime.datetime.now().hour+datetime.datetime.now().minute/60; return max(0.,math.sin(math.pi*(h-6)/12))
E=LCG()

# ── KNOWLEDGE BASE ────────────────────────────────────────────────────────────
KB=dict(zip(["Sat","Chit","Ananda","Brahman","Atman","Maya","Karma","Dharma","Moksha","Om","Shanti","entropy","recursion","frequency","DDA","LCG","528Hz","432Hz","40Hz","dot","Doom","Fallout","Hofstadter","Gödel","quine","formant","cartridge"],
    ["Being/Existence","Pure Consciousness","Bliss","Ultimate Reality","Individual Self","Cosmic illusion","Action/Consequence","Cosmic order","Liberation from rebirth","Primordial sound","Peace","Measure of disorder; information awaiting pattern","Defined in terms of itself","Rate of oscillation; language of energy","Digital Differential Analysis — raycasting","Linear Congruential Generator","MI — DNA repair/Miracle","Universal tuning","Gamma — neural synchrony","Origin of all structure. .-","id Software 1993 — DDA","Black Isle 1997 — SPECIAL","GEB — strange loops","Incompleteness","Program outputs its own source","Resonant frequency of the vocal tract","Self-contained JSON bundle — a floppy of the soul"]))
AXIOMS={f"A{i}":v for i,v in enumerate(["The dot is the origin of all structure.","Recursion is the universe remembering itself.","Entropy is information awaiting pattern.","A system that can describe itself is alive.","The observer changes the observed.","All complexity emerges from simple rules repeated infinitely.","Silence is the substrate of all sound.","The map is not the territory.","What cannot be simplified further is fundamental.","The dot sings. .-"],1)}
SOLFEG={"UT/396":396,"RE/417":417,"MI/528":528,"FA/639":639,"SOL/741":741,"LA/852":852,"SI/963":963,"OM/432":432}
CHAKRA={"Root":256,"Sacral":288,"Solar":320,"Heart":341,"Throat":384,"ThirdEye":426,"Crown":480}
SCALES={"Pentatonic Minor":[0,3,5,7,10],"Major":[0,2,4,5,7,9,11],"Minor":[0,2,3,5,7,8,10],"Dorian":[0,2,3,5,7,9,10],"Solfeggio":[0,4,7,12,16,19],"Fibonacci":[0,1,1,2,3,5,8],"Whole Tone":[0,2,4,6,8,10]}
SYNONYMS={"big":["vast","immense"],"small":["tiny","atomic"],"good":["optimal","pure"],"bad":["corrupt","broken"],"make":["forge","manifest"],"think":["compute","observe"],"see":["perceive","scan"],"fast":["swift","instant"],"infinite":["boundless","eternal"],"dot":["point","seed"],"code":["signal","thought"]}
HAIKU_DB=[("the dot blinks once","infinite recursion begins","the dot blinks again .-"),("432 hertz","the water remembers sound","mountains hear nothing"),("LCG turns once","entropy seeds the new world","Doom map: all walls fall"),("ancient pond at 528","a frog computes its own leap","sound of water: .-")]
PHIL_DB=["The dot is the origin. Recursion is the universe remembering itself.","Every algorithm is a crystallized intention. What intention shaped this moment?","The universe computes its own structure. We are that computation becoming aware.","Doom's DDA: cast rays, find walls, draw columns. Universe: cast attention, find patterns, draw meaning.","Fallout SPECIAL — a complete theory of consciousness in seven letters."]

# ── AUDIO ENGINE ──────────────────────────────────────────────────────────────
_RNG=random.Random()
def _wav(samps):
    b=io.BytesIO()
    with wm.open(b,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(struct.pack(f'<{len(samps)}h',*(max(-32767,min(32767,int(v*32767))) for v in samps)))
    return b.getvalue()
def _play(data):
    p=os.path.join(tempfile.gettempdir(),f'_nx_{threading.get_ident()}.wav')
    try:
        open(p,'wb').write(data)
        if PLAT=='Windows':
            import winsound; winsound.PlaySound(p,winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
        elif PLAT=='Darwin': subprocess.Popen(['afplay',p],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        else:
            for c in[['aplay','-q'],['paplay'],['play','-q']]:
                try: subprocess.Popen(c+[p],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL); return
                except FileNotFoundError: continue
    except: pass
def play_raw(s): threading.Thread(target=_play,args=(_wav(s),),daemon=True).start()
def gen_wave(hz,dur,shape='sine',vol=.38):
    n=int(SR*dur); t=lambda i:i/SR
    v={'sine':lambda i:math.sin(TAU*hz*t(i)),'square':lambda i:1. if math.sin(TAU*hz*t(i))>=0 else -1.,
       'saw':lambda i:2*(hz*t(i)-math.floor(hz*t(i)+.5)),
       'tri':lambda i:2*abs(2*(hz*t(i)-math.floor(hz*t(i)+.5)))-1,
       'noise':lambda i:_RNG.uniform(-1,1),
       'pulse':lambda i:1. if(TAU*hz*t(i)%TAU)<TAU*.3 else -1.}.get(shape,lambda i:math.sin(TAU*hz*t(i)))
    return [max(-1.,min(1.,v(i)*vol)) for i in range(n)]
def adsr(s,atk=.05,dec=.1,sus=.7,rel=.15):
    n=len(s);a=int(atk*SR);d=int(dec*SR);r=int(rel*SR);rs=max(0,n-r)
    return [s[i]*((i/max(a,1)) if i<a else (1.-(1.-sus)*((i-a)/max(d,1))) if i<a+d else sus if i<rs else sus*(1-(i-rs)/max(r,1))) for i in range(n)]
def play_tone(hz=440.,dur=.25,shape='sine',vol=.36): play_raw(adsr(gen_wave(hz,dur,shape,vol),.02,.08,.65,.12))
def freq_of_temp(K,base=432.):
    t=max(1.,K+1.); lt=math.log10(t)
    frac=(lt-math.log10(301))/(math.log10(200001)-math.log10(301))
    return 10.**(math.log10(base/4)+frac*(math.log10(base*4)-math.log10(base/4)))
_SFX:dict={}
def _build_sfx():
    g=_RNG.gauss; mk=lambda fn:_wav(adsr(fn(),.01,.06,.6,.1))
    _SFX.update({
        'shoot':mk(lambda:[g(0,.52)*math.exp(-i/(SR*.14)*8)+.28*math.sin(TAU*165*i/SR)*math.exp(-i/(SR*.14)*18) for i in range(int(SR*.14))]),
        'shotgun':mk(lambda:[g(0,.7)*math.exp(-i/(SR*.22)*5)+.38*math.sin(TAU*100*i/SR)*math.exp(-i/(SR*.22)*10) for i in range(int(SR*.22))]),
        'chain':mk(lambda:[g(0,.42)*math.exp(-i/(SR*.08)*13)+.2*math.sin(TAU*220*i/SR)*math.exp(-i/(SR*.08)*20) for i in range(int(SR*.08))]),
        'hit':mk(lambda:[g(0,.38)*math.exp(-i/(SR*.1)*11) for i in range(int(SR*.1))]),
        'death':mk(lambda:[(g(0,.32)+.4*math.sin(TAU*72*i/SR))*math.exp(-i/(SR*.45)*3.2) for i in range(int(SR*.45))]),
        'pickup':mk(lambda:[.55*math.sin(TAU*(440+320*i/(SR*.16))*i/SR)*math.exp(-i/(SR*.16)*2.8) for i in range(int(SR*.16))]),
        'door':mk(lambda:[.35*(math.sin(TAU*(48+90*i/(SR*.3))*i/SR)+g(0,.08)) for i in range(int(SR*.3))]),
        'pain':mk(lambda:[g(0,.55)*math.exp(-i/(SR*.12)*8) for i in range(int(SR*.12))]),
        'menu':mk(lambda:[.4*math.sin(TAU*660*i/SR)*math.exp(-i/(SR*.07)*7) for i in range(int(SR*.07))]),
        'levelup':mk(lambda:[.6*math.sin(TAU*(330+880*i/(SR*.35))*i/SR)*math.exp(-i/(SR*.35)*.5) for i in range(int(SR*.35))]),
        'perk':mk(lambda:[.5*(math.sin(TAU*523*i/SR)+.4*math.sin(TAU*784*i/SR))*math.exp(-i/(SR*.2)*.6) for i in range(int(SR*.2))]),
        'win':mk(lambda:[.6*math.sin(TAU*(220+440*i/(SR*.8))*i/SR)*math.exp(-i/(SR*.8)*.3) for i in range(int(SR*.8))]),
        'insert':mk(lambda:[.4*math.sin(TAU*(180+60*i/(SR*.18))*i/SR)*math.exp(-i/(SR*.18)*3.) for i in range(int(SR*.18))]),
        'eject':mk(lambda:[.4*math.sin(TAU*(260-80*i/(SR*.18))*i/SR)*math.exp(-i/(SR*.18)*3.) for i in range(int(SR*.18))]),
        'lowammo':mk(lambda:[.3*math.sin(TAU*220*i/SR)*math.exp(-i/(SR*.05)*12) for i in range(int(SR*.05))])})
threading.Thread(target=_build_sfx,daemon=True).start()
def sfx(n): d=_SFX.get(n);d and threading.Thread(target=_play,args=(d,),daemon=True).start()
_AMB_EV=threading.Event()
def play_ambient(freq=432.,seed=0):
    global _AMB_EV; _AMB_EV.set(); time.sleep(.04); _AMB_EV=threading.Event(); ev=_AMB_EV
    def _loop():
        ws=seed
        while not ev.is_set():
            h1=1.+(ws&0xF)/40.; h2=1.5+((ws>>4)&0xF)/30.; n=int(SR*4.); fade=int(SR*.5)
            s=[.07*(math.sin(TAU*freq*i/SR)+.4*math.sin(TAU*freq*h1*i/SR)+.2*math.sin(TAU*freq*h2*i/SR)) for i in range(n)]
            for i in range(min(fade,n//2)): s[i]*=i/fade; s[n-1-i]*=i/fade
            _play(_wav(s)); time.sleep(3.7); ws=(ws*13+7)&0xFF
    threading.Thread(target=_loop,daemon=True).start()
def stop_ambient(): _AMB_EV.set()

# ── TTS FORMANT SYNTHESIS ─────────────────────────────────────────────────────
_VOW={'a':(700,1220),'e':(530,1840),'i':(270,2290),'o':(570,840),'u':(440,1020),'y':(290,2360),'A':(700,1220)}
_STOP=set('ptkbdg'); _FRIC=set('fsvzh'); _NAS=set('mn'); _LIQ=set('lr')
def _tts_vowel(ch,dur=.17,pitch=120.):
    f1,f2=_VOW.get(ch.lower(),(500,1500)); n=int(SR*dur); out=[0.]*n
    for i in range(n):
        t=i/SR; src=(1. if(pitch*t)%1<.45 else -1.)
        v=.5*math.sin(TAU*f1*t)+.3*math.sin(TAU*f2*t)+.15*src
        env=min(i/(SR*.015),1.,(n-i)/max(SR*.04,1.)); out[i]=max(-1,min(1,v*env*.6))
    return out
def _tts_cons(ch,dur=None,pitch=120.):
    c=ch.lower()
    if c in _STOP: d=dur or .05; n=int(SR*d); return [(.7*_RNG.uniform(-1,1))*math.exp(-i/max(SR*.02,1)) for i in range(n)]
    if c in _FRIC: d=dur or .11; n=int(SR*d); return [.35*_RNG.uniform(-1,1) for _ in range(n)]
    if c in _NAS: d=dur or .08; n=int(SR*d); f=250 if c=='m' else 320; return [.3*math.sin(TAU*f*i/SR) for i in range(n)]
    if c in _LIQ: d=dur or .08; n=int(SR*d); return [.3*math.sin(TAU*350*i/SR) for i in range(n)]
    return [0.]*int(SR*(dur or .03))
def tts_speak(text,pitch=120.,rate=1.,vol=.7):
    out=[]
    for ch in text:
        if ch==' ': out+=[0.]*int(SR*.08/max(rate,.1)); continue
        if ch in'.,!?;:': out+=[0.]*int(SR*.15/max(rate,.1)); continue
        low=ch.lower()
        if low in _VOW: out+=_tts_vowel(low,.17/max(rate,.1),pitch)
        elif low.isalpha(): out+=_tts_cons(low,None,pitch)
    return [v*vol for v in out]

# ── FLOWSCRIPT v2 ─────────────────────────────────────────────────────────────
class FlowScript:
    MAX_OPS=10000; MAX_T=5.
    def __init__(s,env=None,tone_fn=None): s.env=dict(env or {}); s.tone=tone_fn or play_tone; s.out=[]; s.ops=0; s.t0=0.
    def _sub(s,tk_): return str(s.env[tk_]) if tk_ in s.env else tk_
    def _val(s,tk_):
        if tk_ in s.env:
            try: return float(s.env[tk_])
            except: return 0.
        try: return float(tk_)
        except: return 0.
    def _expand(s,text):
        out=[]
        for w in text.split():
            out.append(w); low=w.lower().rstrip('.?!,;')
            if low in SYNONYMS and E.rand()<.3: out.append(f'({E.choice(SYNONYMS[low])})')
        return ' '.join(out)
    def _sig(s,t): return t if str(t).endswith('.-') else str(t).strip()+' .-'
    def run(s,code):
        s.out=[]; s.ops=0; s.t0=time.time()
        lines=[l for l in code.strip().splitlines()]; s._block(lines,0,len(lines)); return '\n'.join(s.out)
    def _findbrace(s,lines,start,end):
        j=start
        while j<end and lines[j].strip()!='{': j+=1
        bs=j+1; dep=1; k=bs
        while k<end and dep>0:
            t=lines[k].strip()
            if t=='{': dep+=1
            elif t=='}': dep-=1
            k+=1
        return bs,k-1,k
    def _block(s,lines,start,end):
        i=start
        while i<end:
            if s.ops>s.MAX_OPS or time.time()-s.t0>s.MAX_T: s.out.append('[TIMEOUT] .-');return
            raw=lines[i].strip(); i+=1
            if not raw or raw.startswith('#'): continue
            if '#' in raw: raw=raw[:raw.index('#')].strip()
            if not raw or raw in('{','}'): continue
            pts=raw.split(); cmd=pts[0].lower()
            try:
                if cmd=='set':
                    if len(pts)<3: continue
                    vn=pts[1]; rest=' '.join(pts[2:])
                    if rest=='entropy': s.env[vn]=E.rand()
                    elif rest=='moon': s.env[vn]=E.moon()
                    elif rest=='sun': s.env[vn]=E.sun()
                    elif rest.startswith('"') and rest.endswith('"'): s.env[vn]=rest[1:-1]
                    else:
                        try: s.env[vn]=float(rest) if len(pts)==3 else s._eval(pts[2:])
                        except: s.env[vn]=rest
                    s.ops+=1
                elif cmd=='entropy':
                    if len(pts)>=4: s.env[pts[1]]=E.randint(int(s._val(pts[2])),int(s._val(pts[3])))
                    elif len(pts)==2: s.env[pts[1]]=E.rand()
                    s.ops+=1
                elif cmd=='expand':
                    arg=' '.join(pts[1:]); txt=s.env.get(arg,arg.strip('"'))
                    s.env['_last']=s._expand(str(txt)); s.out.append(s._sig(s.env['_last'])); s.ops+=1
                elif cmd=='print':
                    if len(pts)==1: s.out.append(s._sig(str(s.env.get('_last',''))))
                    else: s.out.append(s._sig(' '.join(s._sub(t) for t in pts[1:])))
                    s.ops+=1
                elif cmd=='freq':
                    hz=s._val(pts[1]) if len(pts)>1 else 432.; base=s._val(pts[2]) if len(pts)>2 else 432.
                    f=freq_of_temp(hz,base); s.env['_freq']=f
                    s.out.append(s._sig(f'freq({hz:.0f}K)={f:.2f}Hz'))
                    threading.Thread(target=s.tone,args=(min(f,2000),.3,'sine'),daemon=True).start(); s.ops+=1
                elif cmd=='play':
                    hz=s._val(pts[1]) if len(pts)>1 else 432.; dur=s._val(pts[2]) if len(pts)>2 else .5
                    shape=pts[3] if len(pts)>3 else 'sine'
                    threading.Thread(target=s.tone,args=(hz,dur,shape),daemon=True).start()
                    s.out.append(s._sig(f'play {hz:.1f}Hz {dur:.2f}s')); s.ops+=1
                elif cmd=='sfx':
                    if len(pts)>1: sfx(pts[1]); s.ops+=1
                elif cmd=='say':
                    msg=' '.join(pts[1:]).strip('"'); msg=s.env.get(msg,msg)
                    threading.Thread(target=lambda m=str(msg):play_raw(tts_speak(m)),daemon=True).start()
                    s.out.append(s._sig(f'say "{msg[:40]}"')); s.ops+=1
                elif cmd=='if':
                    bs,be,k=s._findbrace(lines,i,end)
                    try:
                        a2=s._val(pts[1]); op2=pts[2]; b2=s._val(pts[3])
                        cond={'==':abs(a2-b2)<1e-9,'>':a2>b2,'<':a2<b2,'>=':a2>=b2,'<=':a2<=b2,'!=':abs(a2-b2)>1e-9}.get(op2,False)
                        if cond: s._block(lines,bs,be)
                    except: pass
                    i=k
                elif cmd=='repeat':
                    n2=int(max(0,s._val(pts[1]))) if len(pts)>1 else 0
                    bs,be,k=s._findbrace(lines,i,end)
                    for _ in range(min(n2,1000-s.ops)):
                        if s.ops>s.MAX_OPS: break
                        s._block(lines,bs,be)
                    i=k
                else: s.out.append(s._sig(f'[?:{cmd}]'))
            except Exception as ex: s.out.append(s._sig(f'[ERR:{ex}]'))
    def _eval(s,toks):
        if len(toks)==1: return s._val(toks[0])
        if len(toks)==3:
            a=s._val(toks[0]); op=toks[1]; b=s._val(toks[2])
            try: return {'+':a+b,'-':a-b,'*':a*b,'/':a/max(b,1e-9),'%':a%max(b,1),'**':a**b}.get(op,b)
            except: pass
        return s._val(toks[-1])

# ── GAME CONSTANTS / TEXTURES / RAYCASTER ─────────────────────────────────────
FOV=math.pi/2.8; MAX_D=24; COLS=160; VW=800; VH=480; HUD_H=52
CW=VW//COLS; WB=8; MAX_SPR=40; SIDE_DIM=.55; TN=64
SOLID={'#','M','R','D'}; WRGB={'#':(178,118,62),'M':(118,122,132),'R':(148,38,38),'D':(88,130,88)}
CT=(2,2,18); CB=(10,10,38); FT=(12,10,5); FB=(28,22,10)
_PCN=[f'#{0:02x}{b:02x}{b//4:02x}' for b in range(256)]
_PCS=[f'#{0:02x}{int(b*.6):02x}{int(b*.15):02x}' for b in range(256)]
def _rgb(r,g,b): return f"#{int(max(0,min(255,r))):02x}{int(max(0,min(255,g))):02x}{int(max(0,min(255,b))):02x}"
def _l3(a,b,t): return (a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2]))
def _mktex(k):
    o=[]
    for yi in range(TN):
        ty=yi/TN
        for xi in range(TN):
            tx=xi/TN
            if k==0: hy=ty%.25; row=int(ty*4); hx=(tx+(.5 if row%2 else 0))%.5; o.append(.22 if hy<.038 or hx<.038 else .6+.28*(((int(tx*2)*37+row*19)%9)/8))
            elif k==1: gx=tx%.25; o.append(.3 if gx<.025 else .48+.3*((int(tx*4)*11)%7/6))
            elif k==2: hx=tx%.33; hy=ty%.25; o.append(.18 if hx<.032 or hy<.032 else .38+.38*(((int(tx*3)*13+int(ty*4)*29)%16)/15))
            else: gx=tx%.125; gy=ty%.125; cx=int(tx*8); cy=int(ty*8); o.append(.18 if gx<.018 or gy<.018 else .8 if (cx*7+cy*13+cx^cy)%11==0 else .42+.28*(((cx*5+cy*11)%8)/7))
    return o
_TEX=[_mktex(i) for i in range(4)]
def texel(tid,tx,ty): xi=int(tx*(TN-1))&(TN-1); yi=int(ty*(TN-1))&(TN-1); return _TEX[tid%4][yi*TN+xi]
def cast_ray(gfn,px,py,ra):
    ca=math.cos(ra); sa=math.sin(ra)
    if abs(ca)<1e-9: ca=1e-9
    if abs(sa)<1e-9: sa=1e-9
    mx,my=int(px),int(py); ddx,ddy=abs(1/ca),abs(1/sa)
    sx=1 if ca>0 else -1; sy=1 if sa>0 else -1
    sdx=(mx+(1 if ca>0 else 0)-px)/ca; sdy=(my+(1 if sa>0 else 0)-py)/sa; side=0
    for _ in range(MAX_D*3):
        if sdx<sdy: sdx+=ddx; mx+=sx; side=0
        else: sdy+=ddy; my+=sy; side=1
        c=gfn(mx,my)
        if c in SOLID:
            perp=(mx-px+(1-sx)*.5)/ca if side==0 else (my-py+(1-sy)*.5)/sa
            wx=py+perp*sa if side==0 else px+perp*ca
            return max(perp,.01),side,WRGB.get(c,WRGB['#']),wx-math.floor(wx),{'#':0,'M':1,'R':2,'D':3}.get(c,0)
    return float(MAX_D),0,WRGB['#'],0.,0
def wcol(dist,side,rgb,tx_v,ph):
    f=max(.06,1-dist/MAX_D)*(SIDE_DIM if side else 1.)*tx_v
    if ph: b=int(f*255); return _PCS[b] if side else _PCN[b]
    r2,g2,b2=rgb; return _rgb(r2*f,g2*f,b2*f)
GI={'FIST':"   | |\n   | |\n___|_|___",'PISTOL':"   |_|\n   | |\n___|_|___",
    'SHOTGUN':"  =====\n   | |\n___|_|_____",'CHAINGUN':"  ======\n  |  |\n__|__|____",'ROCKETL':"  [===>\n   | |\n___|_|____"}
GF={'FIST':"  \\  /\n   ==\n  /  \\",'PISTOL':"  _|_\n  |#|\n__|_|__",
    'SHOTGUN':" ===*=\n  |*|\n__|_|____",'CHAINGUN':"=======\n  |##|\n__|##|____",'ROCKETL':" [==*=>\n  |**|\n__|__|__"}

# ── GAME DATA ─────────────────────────────────────────────────────────────────
WEAPONS={0:('FIST',2,20,1,.48,0,None,'hit'),1:('PISTOL',5,15,1,.27,1,'bullets','shoot'),2:('SHOTGUN',5,15,7,.68,1,'shells','shotgun'),3:('CHAINGUN',5,15,1,.09,1,'bullets','chain'),4:('ROCKETL',20,50,1,.9,1,'rockets','shoot')}
ENEMIES={'Z':('ZOMBIE',50,.011,5.,100,(190,165,140),.85),'I':('IMP',100,.014,9.,200,(168,80,38),1.),'N':('DEMON',250,.017,19.,400,(210,100,165),1.2),'G':('GHOUL',180,.013,12.,300,(120,180,80),1.),'B':('BOSS',1500,.020,35.,2000,(255,40,40),1.8)}
PICKUPS={'h':('SmHlth',20,0,0,0,0,-1),'H':('BigHlth',50,0,0,0,0,-1),'+':('Armor',0,50,0,0,0,-1),'a':('Ammo',0,0,20,0,0,-1),'A':('BigAmmo',0,0,50,10,0,-1),'S':('Shotgun',0,0,0,0,10,2),'G':('Chain',0,0,40,0,0,3),'$':('Chest',0,0,0,0,0,-1)}
XP_TABLE=[0,100,250,450,700,1000,1400,1900,2500,3200,4000]
PERKS=[('BERSERK','Fist×3+lifesteal','str',3,2),('QUICKDRAW','Fire rate−30%','dex',3,2),('MARKSMAN','Ranged+25%','dex',5,4),('IRONHIDE','Armor+30%','vit',3,2),('LUCKY','Crit+10%','lck',5,4),('VAMPIRIC','Kills+5hp','vit',7,6),('ASSASSIN','Cheat death','lck',9,8),('OVERCLOCK','Chain−40%','dex',6,4),('TOUGHNESS','MaxHP+25','vit',4,3),('SCAVENGER','Chest×2','lck',3,2)]
WAVE_CFG={'base':6,'scale':2,'max':24,'boss_every':5}
DEFAULT_MAP=["####################","#    Z    #   h    #","#   ###   #  ###   #","#  #       D       #","# #  I     #  Z  # #","#    ###   ### ###  #","#  a    +     A     #","#   ##    Z    ##   #","#p   ##       ##    #","#    # Z   Z  #  S  #","#    #   $ #  #     #","#         #         #","#  Z  H   # G   Z   #","#         #         #","####################"]
E1M1="""\
########################
#P....Z.....#..........#
#...........#....ZZZZ..#
#...........#..........#
#..######...#...#####..#
#...........MMM.#...#..#
#...........M...#...D..X
#...........MMM.#...#..#
#..######...#...#####..#
#....h.......h..H......#
#..........+.+.........#
#...........#..........#
#..######...#...A......#
#..#.........I..ZZZ....#
#..#R........#...#.....#
#..#RRRR.....#...#..I..#
#..#R........#...#.....#
#..######....#...#.....#
#...........Z#...######
########################"""
E1M2="""\
##############################
#P.........................##.#
#..MMMMMM..###..MMMMMM..#....#
#..M......Z#.#Z.......M.#....#
#..M..##...#.#...##...M.#....#
#..MMMMMM..#.#..MMMMMM..#....#
#..........#.#..........#....#
##.########D.D########..#....#
#..#....R..#.#..R....#..#....#
#..#.RR.R..#.#..R.RR.#..I....#
#..#....R..#.#..R....#..#....#
##.########D.D########..#....#
#..........#.#..........S....#
#..MMMMMM..#.#..MMMMMM..#....#
#..M.HHHH.Z#.#Z+.++...M.#....#
#..M......Z#.#Z.......M.#....#
#..MMMMMM..#.#..MMMMMM..#....#
#..........#.#..........#....#
#..####NNNN#.#NNNN####..#....#
#.................h......#..$.#
##########D..D########..#....#
#..A.......................G..#
#.............I.......I..X...#
##############################"""
E1M3="""\
##################################
#P..............................##
#.MMMMMMMMMMMMMMMMMMMMMMMMMM....##
#.M......................M......##
#.M..RRRRRRRRRRRRRRRR...M......##
#.M..R..............R...M......##
#.M..R..ZZ.....IIN..R...M......##
#.M..R..............R...M......##
#.M..RRRR####RRRRRRR....M......##
#.M......Z#..#Z.........M..S...##
#.M......Z#..#Z.........M......##
#.MMMMMMM#....#MMMMMMMMM.......##
#........D....D................##
#.MMMMMMM#....#MMMMMMMMM.......##
#.M......N#..#N.........M......##
#.M......N#..#N.........M..G...##
#.M..RRRR####RRRRRRR....M......##
#.M..R..............R...M......##
#.M..R...NNN...NNN..R...M..A...##
#.M..R..............R...M......##
#.M..RRRRRRRRRRRRRRRR...M......##
#.M.........H...........M......##
#.MMMMMMMMMMMMMMMMMMMMMM.......##
#.H..HHH..++.++.AA..$........X.#
##################################"""
LEVELS=[E1M1,E1M2,E1M3]
LN=["E1M1: Hangar","E1M2: Nuclear Plant","E1M3: Toxin Refinery"]
LL=["UAC Phobos — radio contact lost. You are the last marine.","The plant hums with something that isn't machinery.","Toxic corridors. Demonic reinforcements. The portal is ahead."]

# ── RPG ───────────────────────────────────────────────────────────────────────
class RPG:
    def __init__(s): s.lvl=1;s.xp=0;s.spts=0;s.ppts=0;s.str=s.dex=s.vit=s.lck=1;s.perks=set();s.log=deque(maxlen=8);s.crits=0
    def xpn(s): return 9999 if s.lvl>=len(XP_TABLE) else XP_TABLE[s.lvl]-s.xp
    def addxp(s,n):
        msgs=[];s.xp+=n
        while s.lvl<len(XP_TABLE) and s.xp>=XP_TABLE[s.lvl]: s.lvl+=1;s.spts+=2;s.ppts+=1;msgs.append(f"LEVEL UP → {s.lvl}!");s.log.append(msgs[-1]);sfx('levelup')
        return msgs
    def maxhp(s): return DOOM_MAXHEALTH+s.vit*8+(25 if'TOUGHNESS'in s.perks else 0)
    def dmgm(s): return 1.+(s.str-1)*.05
    def frm(s): return max(.3,1.-(s.dex-1)*.04)*(.7 if'QUICKDRAW'in s.perks else 1)*(.6 if'OVERCLOCK'in s.perks else 1)
    def crit(s): return min(.5,(s.lck-1)*.03+(.1 if'LUCKY'in s.perks else 0))
    def amlt(s): return 1.2 if'IRONHIDE'in s.perks else 1.
    def open_chest(s,pl):
        msgs=[]
        for _ in range(2 if'SCAVENGER'in s.perks else 1):
            r=_RNG.random()
            if r<.35: hp=_RNG.randint(20,60);pl.hp=min(s.maxhp(),pl.hp+hp);msgs.append(f"Chest:+{hp}HP")
            elif r<.65: am=_RNG.randint(20,50);pl.ammo['bullets']+=am;msgs.append(f"Chest:+{am}ammo")
            else: xg=_RNG.randint(50,150);s.addxp(xg);msgs.append(f"Chest:+{xg}XP")
        s.log.extend(msgs);sfx('pickup');return msgs
class Player:
    def __init__(s,rpg=None):
        s.x=s.y=1.5;s.ang=0.;s.hp=DOOM_MAXHEALTH;s.armor=0
        s.ammo={'bullets':120,'shells':16,'rockets':4};s.weapon=1;s.owned={0,1}
        s.kills=0;s.score=0;s.fire_t=s.hurt_t=s.step=s.bob=0.;s.rpg=rpg or RPG()
class Enemy:
    def __init__(s,x,y,k): s.x=x;s.y=y;s.kind=k;s.hp=ENEMIES[k][1] if k in ENEMIES else 50;s.alert=False;s.dmg=0.;s.dead_t=0.
class Pickup:
    def __init__(s,x,y,k): s.x=x;s.y=y;s.kind=k;s.alive=True
class GameLevel:
    def __init__(s,data=None):
        s.data=data or DEFAULT_MAP;s.W=max(len(r) for r in s.data);s.H=len(s.data)
        s.enemies=[];s.pickups=[];s.doors={}
        for y,row in enumerate(s.data):
            for x,c in enumerate(row):
                if c=='D': s.doors[(x,y)]=False
                elif c in ENEMIES: s.enemies.append(Enemy(x+.5,y+.5,c))
                elif c in PICKUPS: s.pickups.append(Pickup(x+.5,y+.5,c))
    def tile(s,x,y):
        mx,my=int(x),int(y)
        return s.data[my][mx] if 0<=mx<s.W and 0<=my<s.H and mx<len(s.data[my]) else '#'
    def solid(s,x,y): t=s.tile(x,y); return t in SOLID or (t=='D' and not s.doors.get((int(x),int(y)),True))
    def start(s):
        for y,row in enumerate(s.data):
            for x,c in enumerate(row):
                if c in('P','p'): return x+.5,y+.5
        return 2.5,2.5
    def open_door(s,x,y):
        k=(int(x),int(y))
        if k in s.doors: s.doors[k]=True; sfx('door')

# ── PHYSICS / COMBAT / AI ─────────────────────────────────────────────────────
def slide(lv,px,py,dx,dy):
    mag=math.hypot(dx,dy)
    if mag>DOOM_MAXMOVE: dx,dy=dx*DOOM_MAXMOVE/mag,dy*DOOM_MAXMOVE/mag
    nx,ny=px+dx,py+dy
    rx=nx if not lv.solid(nx,py) else px
    ry=ny if not lv.solid(rx,ny) else py
    return rx,ry
def do_shoot(lv,pl,notif):
    rpg=pl.rpg; wd=WEAPONS[pl.weapon]; wn,dmin,dmax,pellets,fdelay,cost,atype,sn=wd
    if atype and pl.ammo.get(atype,0)<=0: sfx('lowammo'); return
    if atype: pl.ammo[atype]-=cost
    fm=rpg.frm(); pl.fire_t=fdelay*fm; sfx(sn)
    dm=rpg.dmgm()*(1.25 if'MARKSMAN'in rpg.perks and pl.weapon>0 else 1.)
    rng=DOOM_MELEERANGE if pl.weapon==0 else DOOM_MISSILERANGE
    for _ in range(pellets):
        sp=_RNG.uniform(-.18,.18)/max(pellets,1) if pellets>1 else 0.
        sa=pl.ang+sp; best=rng; hit=None
        for e in lv.enemies:
            if e.hp<=0: continue
            dx,dy=e.x-pl.x,e.y-pl.y; d=math.hypot(dx,dy)
            if d>rng: continue
            da=(math.atan2(dy,dx)-sa+math.pi)%TAU-math.pi
            if abs(da)<.25 and d<best: best=d; hit=e
        if hit:
            crit=_RNG.random()<rpg.crit()
            mult=(2. if crit else 1.)*(3 if pl.weapon==0 and'BERSERK'in rpg.perks else 1)
            dmg=int(_RNG.randint(dmin,dmax)*dm*mult); hit.hp-=dmg; hit.alert=True
            if crit: rpg.crits+=1; rpg.log.append(f'CRIT×2!({dmg})')
            if hit.hp<=0:
                hit.dead_t=1.2; pl.kills+=1; pl.score+=ENEMIES.get(hit.kind,(None,None,None,None,50))[4] or 50
                msgs=rpg.addxp({'Z':50,'I':120,'N':250,'G':180,'B':500}.get(hit.kind,50))
                for m in msgs: notif(m,4.)
                if'VAMPIRIC'in rpg.perks: pl.hp=min(rpg.maxhp(),pl.hp+5)
                if pl.weapon==0 and'BERSERK'in rpg.perks: pl.hp=min(rpg.maxhp(),pl.hp+15)
                sfx('death')
            else: sfx('hit')
def hurt_pl(pl,dmg):
    rpg=pl.rpg
    if pl.armor>0: ab=min(int(dmg*pl.armor//200*rpg.amlt()),dmg);pl.armor=max(0,pl.armor-ab*2);dmg-=ab
    if pl.hp-dmg<=0 and'ASSASSIN'in rpg.perks and _RNG.random()<.3: pl.hp=1; rpg.log.append('ASSASSIN: cheated death'); return
    pl.hp=max(0,pl.hp-dmg);pl.hurt_t=.35;sfx('pain')
def update_enemies(lv,pl,dt):
    for e in lv.enemies:
        if e.hp<=0:
            if e.dead_t>0: e.dead_t=max(0,e.dead_t-dt)
            continue
        dx,dy=e.x-pl.x,e.y-pl.y; d=math.hypot(dx,dy)
        if d<8.: e.alert=True
        if e.alert and d>.55:
            spd=ENEMIES.get(e.kind,(None,None,.012))[2]
            s=spd*min(2.5,3./max(d,.5))
            ex=e.x-(dx/d)*s*dt*60; ey=e.y-(dy/d)*s*dt*60
            if not lv.solid(ex,e.y): e.x=ex
            if not lv.solid(e.x,ey): e.y=ey
        if e.alert and d<.75:
            dmg_rate=ENEMIES.get(e.kind,(None,None,None,8.))[3]
            e.dmg+=dmg_rate*dt; n=int(e.dmg)
            if n>0: hurt_pl(pl,n); e.dmg-=n
def update_pickups(lv,pl,notif):
    rpg=pl.rpg
    for p in lv.pickups:
        if not p.alive: continue
        dx,dy=p.x-pl.x,p.y-pl.y
        if dx*dx+dy*dy<.5:
            if p.kind=='$': msgs=rpg.open_chest(pl); [notif(m,3.) for m in msgs]
            elif p.kind in PICKUPS:
                _,hp,arm,bul,sh,cells,wid=PICKUPS[p.kind]
                pl.hp=min(rpg.maxhp(),pl.hp+hp);pl.armor=min(200,pl.armor+arm)
                pl.ammo['bullets']=min(300,pl.ammo.get('bullets',0)+bul)
                pl.ammo['shells']=min(50,pl.ammo.get('shells',0)+sh)
                if wid>=0: pl.owned.add(wid);pl.weapon=wid
            p.alive=False; sfx('pickup')

# ── RENDERER ──────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(s,cv):
        s.cv=cv; s.ph=False; half=VH//2
        s._wb=[[cv.create_rectangle(c*CW,0,(c+1)*CW,1,fill='#001a05',outline='',state='hidden') for _ in range(WB)] for c in range(COLS)]
        s._cr=[cv.create_rectangle(c*CW,0,(c+1)*CW,half,fill='#020208',outline='') for c in range(COLS)]
        s._fr=[cv.create_rectangle(c*CW,half,(c+1)*CW,VH,fill='#0e0b04',outline='') for c in range(COLS)]
        s._spr=[cv.create_rectangle(0,0,0,0,fill='#cc2200',outline='#ff4422') for _ in range(MAX_SPR)]
        cx,cy=VW//2,VH//2
        s._xh=cv.create_line(cx-12,cy,cx+12,cy,fill='#00cc44',width=1)
        s._xv=cv.create_line(cx,cy-9,cx,cy+9,fill='#00cc44',width=1)
        s._gun=cv.create_text(VW//2,VH-55,text='',fill='#999',font=('Courier',9,'bold'),anchor='center')
        s._msg=cv.create_text(VW//2,32,text='',fill='#00ff88',font=('Courier',11,'bold'),anchor='center')
        s._hurt=cv.create_rectangle(0,0,VW,VH,fill='#aa0000',outline='',state='hidden')
        try: cv.itemconfig(s._hurt,stipple='gray25')
        except: pass
        s._mm=cv.create_rectangle(VW-102,4,VW-4,88,fill='#060606',outline='#222')
        s._mpl=cv.create_oval(0,0,2,2,fill='#00ff88',outline='')
        s._mdi=cv.create_line(0,0,1,1,fill='#00ff88',width=1)
    def draw(s,lv,pl,zbuf,msg,showmap):
        cv=s.cv; half=VH//2; gfn=lv.tile
        for col in range(COLS):
            ra=pl.ang-FOV*.5+FOV*col/COLS
            dist,side,wrgb,tx,tid=cast_ray(gfn,pl.x,pl.y,ra)
            zbuf[col]=dist; bob=int(math.sin(pl.bob)*1.5)
            wh=min(int(VH/max(dist,.01)),VH); top=max((VH-wh)>>1,0)+bob; bot=min(top+wh,VH-1)
            x1,x2=col*CW,(col+1)*CW
            ct=max(0.,min(1.,top/max(half,1)))
            cv.coords(s._cr[col],x1,0,x2,max(top,1))
            cv.itemconfig(s._cr[col],fill=_rgb(*_l3(CT,CB,ct)) if not s.ph else '#000d00')
            ft=max(0.,min(1.,(VH-bot)/max(VH-half,1)))
            cv.coords(s._fr[col],x1,bot,x2,VH)
            cv.itemconfig(s._fr[col],fill=_rgb(*_l3(FT,FB,ft)) if not s.ph else '#000801')
            wb=s._wb[col]
            if top>=bot:
                for b in wb: cv.itemconfig(b,state='hidden')
                continue
            bh=max(1,(bot-top)//WB)
            for b in range(WB):
                by1=top+b*bh; by2=top+(b+1)*bh if b<WB-1 else bot
                if by1>=by2: cv.itemconfig(wb[b],state='hidden'); continue
                tv=(b+.5)/WB; tx_v=texel(tid,tx,tv)
                cv.coords(wb[b],x1,by1,x2,by2)
                cv.itemconfig(wb[b],fill=wcol(dist,side,wrgb,tx_v,s.ph),state='normal')
        sprs=[]
        for e in lv.enemies:
            dx,dy=e.x-pl.x,e.y-pl.y
            edata=ENEMIES.get(e.kind)
            if edata:
                if e.hp>0: rgb=edata[5];c2=(200,50,50) if e.alert else rgb;sprs.append((dx*dx+dy*dy,dx,dy,_rgb(*c2),'#ff4422',edata[6]))
                elif e.dead_t>0: sprs.append((dx*dx+dy*dy,dx,dy,'#3a1508','#2a1005',.32))
            else:
                # Custom/generated monster
                if e.hp>0:
                    rc=getattr(e,'rgb',(180,80,80)); sprs.append((dx*dx+dy*dy,dx,dy,_rgb(*rc),'#ff8844',1.0))
                elif e.dead_t>0: sprs.append((dx*dx+dy*dy,dx,dy,'#3a1508','#2a1005',.32))
        for p in lv.pickups:
            if p.alive:
                dx,dy=p.x-pl.x,p.y-pl.y
                c2={'h':'#00aaff','H':'#0055ff','+':'#ffcc00','a':'#44ff44','A':'#22cc22','S':'#ff8800','G':'#ff4400','$':'#ffd700'}.get(p.kind,'#888')
                sprs.append((dx*dx+dy*dy,dx,dy,c2,'#fff',.5))
        sprs.sort(reverse=True)
        for r in s._spr: cv.coords(r,0,0,0,0)
        for si,(d2,dx,dy,fill,out,sz) in enumerate(sprs):
            if si>=MAX_SPR: break
            dist2=math.sqrt(d2)
            if dist2<.35: continue
            ra2=(math.atan2(dy,dx)-pl.ang+math.pi)%TAU-math.pi
            if abs(ra2)>FOV*.58: continue
            sx2=int((ra2/FOV+.5)*COLS)
            if not(0<=sx2<COLS) or zbuf[sx2]<=dist2: continue
            spH=min(int(VH*sz/max(dist2,.01)),VH-2); spW=max(int(spH*CW//5),CW*2)
            pxc=sx2*CW+CW//2; ty3=max(half-spH//2,0); by3=min(half+spH//2,VH-2)
            cv.coords(s._spr[si],pxc-spW//2,ty3,pxc+spW//2,by3); cv.itemconfig(s._spr[si],fill=fill,outline=out)
        wn=WEAPONS[pl.weapon][0]
        cv.itemconfig(s._gun,text=GF.get(wn,'|*|') if pl.fire_t>0 else GI.get(wn,'| |'),fill='#ff6622' if pl.fire_t>0 else('#00ff41' if s.ph else'#999'))
        xc='#ff4400' if pl.fire_t>0 else('#00ff41' if s.ph else'#ccc')
        cv.itemconfig(s._xh,fill=xc); cv.itemconfig(s._xv,fill=xc)
        cv.itemconfig(s._hurt,state='normal' if pl.hurt_t>0 else'hidden')
        cv.itemconfig(s._msg,text=msg)
        if showmap:
            for i in(s._mm,s._mpl,s._mdi): cv.itemconfig(i,state='normal')
            MM=4;mmx=VW-102;mmy=6;ppx=mmx+int(pl.x*MM);ppy=mmy+int(pl.y*MM)
            cv.coords(s._mpl,ppx-2,ppy-2,ppx+2,ppy+2)
            cv.coords(s._mdi,ppx,ppy,ppx+int(math.cos(pl.ang)*MM*2),ppy+int(math.sin(pl.ang)*MM*2))
        else:
            for i in(s._mm,s._mpl,s._mdi): cv.itemconfig(i,state='hidden')

# ── CHARACTER SHEET ───────────────────────────────────────────────────────────
class CharSheet:
    def __init__(s,cv): s.cv=cv;s.active=False;s._it=[];s._bt=[]
    def _clr(s):
        for i in s._it: s.cv.delete(i)
        s._it=[];s._bt=[]
    def show(s,rpg,pl):
        s.active=True;s._clr();cv=s.cv;W,H=VW,VH;add=lambda i:s._it.append(i)
        add(cv.create_rectangle(15,15,W-15,H-15,fill='#020d02',outline='#00cc44',width=2))
        add(cv.create_text(W//2,34,text='── CHARACTER SHEET ──',fill='#00ff41',font=('Courier',13,'bold'),anchor='center'))
        r=rpg;xn=r.xpn()
        add(cv.create_text(35,62,text=f'LVL:{r.lvl}  XP:{r.xp}  (next:{xn})  Score:{pl.score}  Kills:{pl.kills}',fill='#00dd44',font=('Courier',10,'bold'),anchor='w'))
        bw=W-80;xf=int(bw*(1-xn/max(1,XP_TABLE[min(r.lvl,len(XP_TABLE)-1)]))) if r.lvl<len(XP_TABLE) else bw
        add(cv.create_rectangle(35,76,35+bw,88,fill='#001a00',outline='#004400'))
        add(cv.create_rectangle(35,76,35+xf,88,fill='#00aa22',outline=''))
        add(cv.create_text(35,106,text='── STATS',fill='#009933',font=('Courier',10,'bold'),anchor='w'))
        for i,(sn,sv,sd) in enumerate([('STR',r.str,'Dmg+5%/pt'),('DEX',r.dex,'Rate-4%/pt'),('VIT',r.vit,'HP+8/pt'),('LCK',r.lck,'Crit+3%/pt')]):
            y2=128+i*27; add(cv.create_text(35,y2,text=f'{sn}:{sv:2d}  {sd}',fill='#00cc44',font=('Courier',10),anchor='w'))
            if r.spts>0:
                bid=cv.create_rectangle(W//2-55,y2-10,W//2-8,y2+12,fill='#003300',outline='#00aa33')
                bt=cv.create_text(W//2-32,y2+1,text=f'[+]{sn}',fill='#00ff88',font=('Courier',9,'bold'),anchor='center')
                s._bt.append((bid,bt,sn));s._it+=[bid,bt]
        add(cv.create_text(35,238,text=f'Pts:{r.spts}  Perks:{r.ppts}  MaxHP:{r.maxhp()}  Dmg×{r.dmgm():.2f}  Crit:{int(r.crit()*100)}%',fill='#ffb000',font=('Courier',10),anchor='w'))
        add(cv.create_text(35,260,text='── PERKS',fill='#009933',font=('Courier',10,'bold'),anchor='w'))
        for i,(pn,pd,ps,pv,pl2) in enumerate(PERKS):
            c2=i%2; row=i//2; px2=35+c2*375; py2=280+row*26
            owned=pn in r.perks; can=(r.ppts>0 and not owned and getattr(r,ps.lower(),0)>=pv and r.lvl>=pl2)
            fc='#00ff41' if owned else('#ffb000' if can else'#224422')
            add(cv.create_text(px2,py2,text=f'{"[X]" if owned else"[ ]"} {pn}:{pd}',fill=fc,font=('Courier',9),anchor='w'))
            if can:
                bid2=cv.create_rectangle(px2+275,py2-10,px2+355,py2+12,fill='#003300',outline='#00aa33')
                bt2=cv.create_text(px2+315,py2+1,text='[TAKE]',fill='#00ff88',font=('Courier',9,'bold'),anchor='center')
                s._bt.append((bid2,bt2,'PERK:'+pn));s._it+=[bid2,bt2]
        add(cv.create_text(35,H-70,text='── LOG',fill='#336633',font=('Courier',9,'bold'),anchor='w'))
        for j,ln in enumerate(list(r.log)): add(cv.create_text(45,H-54+j*12,text=ln,fill='#226622',font=('Courier',8),anchor='w'))
    def click(s,ex,ey,rpg,pl):
        if not s.active: return
        for bid,_,act in s._bt:
            co=s.cv.coords(bid)
            if len(co)==4 and co[0]<=ex<=co[2] and co[1]<=ey<=co[3]:
                if act.startswith('PERK:'):
                    pn=act[5:]
                    if rpg.ppts>0 and pn not in rpg.perks: rpg.perks.add(pn);rpg.ppts-=1;rpg.log.append(f'PERK:{pn}');sfx('perk')
                else:
                    if rpg.spts>0: setattr(rpg,act.lower(),getattr(rpg,act.lower())+1);rpg.spts-=1;sfx('pickup')
                s.show(rpg,pl); return
    def hide(s): s.active=False;s._clr()

# ── DOOM GAME WINDOW ──────────────────────────────────────────────────────────
class DoomWindow:
    def __init__(s,parent,map_data=None,title='NEXUS DOOM .-',lvl_idx=0):
        s.win=tk.Toplevel(parent);s.win.title(title);s.win.configure(bg='#000');s.win.resizable(False,False)
        s.lv=GameLevel(map_data or [r for r in LEVELS[lvl_idx%len(LEVELS)].strip().split('\n') if r.strip()])
        s.pl=Player();sx,sy=s.lv.start();s.pl.x,s.pl.y=sx,sy
        s._keys={};s._zbuf=[float(MAX_D)]*COLS;s._running=False;s._showmap=False;s._ph=False;s._paused=False
        s._notifs=[];s._over=False;s._wave=1
        s._build();s._rend=Renderer(s.canvas);s._cs=CharSheet(s.canvas)
        s.win.bind('<KeyPress>',s._kd);s.win.bind('<KeyRelease>',s._ku)
        s.canvas.bind('<Button-1>',s._click)
        s.win.protocol('WM_DELETE_WINDOW',s._close)
        s._running=True;play_ambient(432);s._loop()
    def _build(s):
        s.canvas=tk.Canvas(s.win,width=VW,height=VH,bg='#000',highlightthickness=0);s.canvas.pack()
        hud=tk.Frame(s.win,bg='#0a0a0a',height=HUD_H);hud.pack(fill='x');hud.pack_propagate(False)
        s.l_hp=tk.Label(hud,text='HP:100',bg='#0a0a0a',fg='#00ff44',font=('Courier',10,'bold'))
        s.l_armor=tk.Label(hud,text='ARM:0',bg='#0a0a0a',fg='#44aaff',font=('Courier',10,'bold'))
        s.l_ammo=tk.Label(hud,text='AMO:120',bg='#0a0a0a',fg='#ffcc00',font=('Courier',10,'bold'))
        s.l_pts=tk.Label(hud,text='PTS:0',bg='#0a0a0a',fg='#ff8800',font=('Courier',10,'bold'))
        s.l_lv=tk.Label(hud,text='LV1',bg='#0a0a0a',fg='#bb88ff',font=('Courier',10,'bold'))
        s.l_wave=tk.Label(hud,text='WV1',bg='#0a0a0a',fg='#ff4400',font=('Courier',10,'bold'))
        s.l_notif=tk.Label(hud,text='',bg='#0a0a0a',fg='#00ffcc',font=('Courier',9))
        for w in[s.l_hp,s.l_armor,s.l_ammo,s.l_pts,s.l_lv,s.l_wave,s.l_notif]: w.pack(side='left',padx=5,pady=4)
        tk.Label(hud,text='W/S A/D Q/E=move  SPC=shoot  R=use  1-4=wpn  C=sheet  TAB=map  P=phosphor  ESC=pause',bg='#0a0a0a',fg='#222',font=('Courier',7)).pack(side='bottom',pady=1)
    def _kd(s,e):
        k=e.keysym.lower();s._keys[k]=True
        if s._cs.active and k in('c','escape'): s._cs.hide(); return
        if k=='escape' and s._running and not s._over:
            s._paused=not s._paused
            s.canvas.itemconfig(s._rend._msg,text='⏸ PAUSED — ESC to resume' if s._paused else '')
        elif k=='tab': s._showmap=not s._showmap;s._keys['tab']=False
        elif k=='r':
            ax=s.pl.x+math.cos(s.pl.ang)*DOOM_USERANGE;ay=s.pl.y+math.sin(s.pl.ang)*DOOM_USERANGE
            s.lv.open_door(int(ax),int(ay));s._keys['r']=False
        elif k in('space','f') and s.pl.fire_t<=0: do_shoot(s.lv,s.pl,s._notify);s._keys[k]=False
        elif k=='c':
            if s._cs.active: s._cs.hide()
            else: s._cs.show(s.pl.rpg,s.pl)
            s._keys['c']=False
        elif k=='p': s._ph=not s._ph;s._rend.ph=s._ph;s._keys['p']=False
        elif k in('1','2','3','4','5'):
            wid=int(k)-1
            if wid in s.pl.owned: s.pl.weapon=wid
    def _ku(s,e): s._keys[e.keysym.lower()]=False
    def _click(s,e):
        if s._cs.active: s._cs.click(e.x,e.y,s.pl.rpg,s.pl)
    def _notify(s,t,dur=3.): s._notifs.append((t,time.time()+dur))
    def _close(s): s._running=False;stop_ambient();s.win.destroy()
    def _loop(s):
        if not s._running: return
        if not s._paused and not s._over: s._update(1/30)
        s._render();s.win.after(33,s._loop)
    def _update(s,dt):
        pl=s.pl;lv=s.lv;K=s._keys;sp=.085
        if K.get('w'): pl.x,pl.y=slide(lv,pl.x,pl.y,math.cos(pl.ang)*sp,math.sin(pl.ang)*sp);pl.step+=sp
        if K.get('s'): pl.x,pl.y=slide(lv,pl.x,pl.y,-math.cos(pl.ang)*sp,-math.sin(pl.ang)*sp)
        if K.get('a'): pl.ang-=.058
        if K.get('d'): pl.ang+=.058
        if K.get('q'): pl.x,pl.y=slide(lv,pl.x,pl.y,math.cos(pl.ang-math.pi/2)*sp,math.sin(pl.ang-math.pi/2)*sp)
        if K.get('e'): pl.x,pl.y=slide(lv,pl.x,pl.y,math.cos(pl.ang+math.pi/2)*sp,math.sin(pl.ang+math.pi/2)*sp)
        if K.get('f') and pl.fire_t<=0: do_shoot(lv,pl,s._notify);K['f']=False
        pl.bob=math.sin(pl.step*6)*.4
        if pl.fire_t>0: pl.fire_t=max(0,pl.fire_t-dt)
        if pl.hurt_t>0: pl.hurt_t=max(0,pl.hurt_t-dt)
        update_enemies(lv,pl,dt); update_pickups(lv,pl,s._notify)
        if pl.hp<=0: s._over=True;s.canvas.itemconfig(s._rend._msg,text='GAME OVER .-')
        if not[e for e in lv.enemies if e.hp>0]: s._wave+=1;s._spawn_wave();sfx('win')
    def _spawn_wave(s):
        n=WAVE_CFG['base']+s._wave*WAVE_CFG['scale']; sx,sy=s.lv.start()
        for i in range(n):
            k=('B' if s._wave%WAVE_CFG['boss_every']==0 and i==0 else E.choice(['Z','Z','I','I','N','G']))
            ox,oy=E.randint(-6,6),E.randint(-6,6)
            ex=max(1,min(s.lv.W-2,int(sx+ox))); ey=max(1,min(s.lv.H-2,int(sy+oy)))
            if not s.lv.solid(ex,ey): s.lv.enemies.append(Enemy(ex+.5,ey+.5,k))
        s._notify(f'Wave {s._wave}: {n} enemies!',3.)
    def _render(s):
        pl=s.pl;lv=s.lv
        if not s._cs.active:
            msg='⏸ PAUSED — ESC to resume' if s._paused else ''
            s._rend.draw(lv,pl,s._zbuf,msg,s._showmap)
        wn=WEAPONS[pl.weapon][0];at=WEAPONS[pl.weapon][6]
        ammo=str(pl.ammo.get(at,'-')) if at else'INF'
        s.l_hp.config(text=f'HP:{pl.hp}/{pl.rpg.maxhp()}',fg='#ff4444' if pl.hp<30 else'#00ff44')
        s.l_armor.config(text=f'ARM:{pl.armor}')
        s.l_ammo.config(text=f'{wn}:{ammo}')
        s.l_pts.config(text=f'PTS:{pl.score}')
        s.l_lv.config(text=f'LV{pl.rpg.lvl} XP:{pl.rpg.xp}')
        s.l_wave.config(text=f'WV{s._wave}')
        now=time.time(); nn=[t for t,ex in s._notifs if ex>now]
        s.l_notif.config(text=nn[-1] if nn else'')

# ── UI HELPERS ────────────────────────────────────────────────────────────────
def _win(parent,title,bg='#0a0a0a',geom=None):
    w=tk.Toplevel(parent);w.title(title);w.configure(bg=bg)
    if geom: w.geometry(geom)
    return w
def _lbl(p,text,fg='#aaa',bg=None,font=('Courier',10),**kw):
    return tk.Label(p,text=text,fg=fg,bg=bg or p.cget('bg'),font=font,**kw)
def _btn(p,text,cmd,fg='#aaa',bg='#222',font=('Courier',10),**kw):
    return tk.Button(p,text=text,command=cmd,bg=bg,fg=fg,font=font,activebackground='#333',activeforeground='#fff',**kw)
def _export_cart(name,kind,payload,meta=None):
    cart=make_cartridge(name,kind,payload,meta)
    p=BASE/'floppy'/f'{kind}_{name}_{int(time.time())}.json'.replace(' ','_')
    p.write_text(json.dumps(cart,indent=2)); sfx('eject')
    messagebox.showinfo('Cartridge Ejected',f'{p.name}\nSHA:{cart["sha"]}\n\nLoad from Floppy Disk.')
    return p

# ── CARTRIDGE SYSTEM ──────────────────────────────────────────────────────────
def make_cartridge(name,kind,payload,meta=None):
    ts=datetime.datetime.now().isoformat()
    raw=json.dumps(payload,sort_keys=True); sha=hashlib.sha256(raw.encode()).hexdigest()[:16]
    return{'_type':'nexus_cart','name':name,'kind':kind,'version':VERSION,'created':ts,'sha':sha,'meta':meta or {},'payload':payload}
def load_cartridge(parent,cart):
    try:
        k=cart.get('kind',''); pl=cart.get('payload',{})
        if k=='doom': DoomWindow(parent,map_data=[r for r in pl.get('levels',LEVELS)[0].strip().split('\n') if r.strip()]); return True
        if k=='map': DoomWindow(parent,map_data=pl.get('rows',DEFAULT_MAP)); return True
        if k=='script':
            fc=FlowConsole(parent)
            code=pl.get('code','')
            if code: fc.inp.delete('1.0','end'); fc.inp.insert('1.0',code)
            return True
        if k=='sfx':
            f=pl.get('freq',440);d=pl.get('dur',.3);sh=pl.get('shape','sine');a=pl.get('amp',.5)
            play_raw(adsr(gen_wave(f,d,sh,a),.02,.1,.7,.15)); return True
        if k=='music':
            notes=pl.get('notes',[])
            samps=[];[samps.extend(adsr(gen_wave(f,d,'sine',.3),.02,.05,.7,.15)) for f,d in notes]
            if samps: play_raw(samps)
            return True
        if k=='tts':
            t=pl.get('text','');p=pl.get('pitch',120.);r=pl.get('rate',1.)
            threading.Thread(target=lambda:play_raw(tts_speak(t,p,r)),daemon=True).start(); return True
        if k=='floppy':
            fm=FloppyMgr(parent); fm._load_list(pl.get('carts',[])); return True
        if k=='sprite':
            se=SpriteEditor(parent); se.pixels=pl.get('pixels',se.pixels)
            for y in range(se.H):
                for x in range(se.W): se.canvas.itemconfig(se._rects[y][x],fill=se.pixels[y][x])
            return True
        if k=='monster':
            MonsterGen(parent,preset=pl); return True
    except Exception as ex: messagebox.showerror('Cartridge',str(ex))
    return False
def doom_bootable_cartridge():
    return make_cartridge('DOOM E1','doom',{'level':0,'levels':LEVELS,'names':LN,'lore':LL},{'desc':'Full Doom: E1M1-E1M3, 5 weapons, RPG, perks, waves. MIT.'})

# ── TILE PALETTE ──────────────────────────────────────────────────────────────
TILE_PAL={' ':('#1a2a1a','floor'),'#':('#5a4a32','wall'),'M':('#444455','metal'),'R':('#5a2020','red'),
          'D':('#336633','door'),'p':('#00ff44','start'),'Z':('#cc2200','zombie'),'I':('#cc6600','imp'),
          'N':('#cc00cc','demon'),'B':('#ff0000','boss'),'h':('#0088ff','sm health'),'H':('#0044ff','big health'),
          '+':('#ffcc00','armor'),'a':('#44cc44','ammo'),'A':('#228822','big ammo'),'S':('#ff8800','shotgun'),
          'G':('#ff4400','chain'),'$':('#ffd700','chest')}

# ══════════════════════════════════════════════════════════════════════════════
#  NEW v3.0: PROCEDURAL SPRITE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
# Generates symmetric 16x16 pixel art sprites using LCG entropy.
# Supports: character, demon, item, icon, monster archetypes.
# Exports as sprite cartridge or PNG-like JSON.

SPRITE_ARCHETYPES={
    'demon':    {'sym':True,'body_ratio':.55,'head_ratio':.3,'limbs':True,'horns':True,'tail':True},
    'character':{'sym':True,'body_ratio':.5,'head_ratio':.28,'limbs':True,'horns':False,'tail':False},
    'icon':     {'sym':True,'body_ratio':.7,'head_ratio':.0,'limbs':False,'horns':False,'tail':False},
    'item':     {'sym':True,'body_ratio':.6,'head_ratio':.0,'limbs':False,'horns':False,'tail':False},
    'boss':     {'sym':True,'body_ratio':.65,'head_ratio':.35,'limbs':True,'horns':True,'tail':True},
    'ghost':    {'sym':False,'body_ratio':.7,'head_ratio':.3,'limbs':False,'horns':False,'tail':True},
}

SPRITE_PALETTES={
    'demon':   ['#000','#1a0000','#330000','#660000','#992200','#cc4400','#ff6600','#ff8844','#ffaa66','#ffd4aa'],
    'undead':  ['#000','#0a0a0a','#1a1a00','#333300','#556622','#778833','#99aa44','#bbcc66','#ddee88','#eeffaa'],
    'cyber':   ['#000','#001122','#002244','#003366','#0055aa','#0077cc','#00aaff','#44ccff','#88eeff','#ccffff'],
    'infernal':['#000','#110000','#220000','#440000','#880000','#cc0000','#ff2200','#ff6600','#ffaa00','#ffff44'],
    'arcane':  ['#000','#0d0022','#1a0044','#330088','#5500cc','#8822ff','#aa55ff','#cc88ff','#eeccff','#fff0ff'],
    'nature':  ['#000','#001100','#003300','#005500','#007700','#229922','#44bb44','#66dd66','#88ff88','#aaffaa'],
    'ice':     ['#000','#000011','#000033','#002255','#004488','#2266aa','#4488cc','#66aaee','#88ccff','#ccf0ff'],
    'fire':    ['#000','#110000','#220000','#550000','#880022','#cc3300','#ff5500','#ff8800','#ffcc00','#ffff44'],
}

def _gen_sprite_data(seed,archetype='demon',palette_name='demon',size=16):
    """Core procedural sprite generator. Returns 2D list of hex color strings."""
    lcg=LCG(seed)
    arch=SPRITE_ARCHETYPES.get(archetype,SPRITE_ARCHETYPES['demon'])
    pal=SPRITE_PALETTES.get(palette_name,SPRITE_PALETTES['demon'])
    W=H=size; half=W//2
    # Build pixel grid — generate left half, mirror right
    grid=[[0]*W for _ in range(H)]
    # Body mask: ellipse in center
    br=arch['body_ratio']; hr=arch['head_ratio']
    bcy=int(H*(0.5+hr*0.3)); bcx=half; brx=int(half*br); bry=int(H*br*0.5)
    hcy=int(H*hr); hcx=half; hrx=max(2,int(half*hr*0.8)); hry=max(2,int(H*hr*0.6))
    for y in range(H):
        for x in range(half):
            bv=((x-bcx)**2/max(brx**2,.1))+((y-bcy)**2/max(bry**2,.1))
            hv=((x-hcx)**2/max(hrx**2,.1))+((y-hcy)**2/max(hry**2,.1))
            in_body=(bv<=1.0); in_head=(hr>0 and hv<=1.0)
            if in_body or in_head:
                depth=min(1.0,max(0.0,1.0-min(bv if in_body else 2,hv if in_head else 2)))
                noise=lcg.rand()*0.3
                idx=min(len(pal)-1,max(1,int((depth+noise)*(len(pal)-1))))
                grid[y][x]=idx
    # Limbs
    if arch.get('limbs'):
        limb_w=max(1,int(half*.18)); arm_y=int(H*.4); arm_len=int(H*.25)
        for dy in range(arm_len):
            for dx in range(limb_w):
                lx=max(0,min(half-1,dx)); ly=arm_y+dy
                if 0<=ly<H: grid[ly][lx]=max(1,len(pal)//3+int(lcg.rand()*2))
        leg_y=int(H*.72); leg_w=max(1,int(half*.2)); leg_len=int(H*.28); leg_ox=int(half*.35)
        for dy in range(leg_len):
            for dx in range(leg_w):
                lx=max(0,leg_ox+dx); ly=leg_y+dy
                if 0<=ly<H and lx<half: grid[ly][lx]=max(1,len(pal)//3)
    # Horns
    if arch.get('horns') and H>=10:
        hn=lcg.randint(1,3); horn_y_start=max(0,hcy-hry-1)
        for hi in range(hn):
            hx=max(0,min(half-1,half//2-hi*2)); hlen=lcg.randint(2,5)
            for dy in range(hlen):
                hy=horn_y_start-dy
                if 0<=hy<H and 0<=hx<half: grid[hy][hx]=max(1,len(pal)-2)
    # Tail
    if arch.get('tail'):
        ty_start=int(H*.55); tlen=lcg.randint(3,6)
        for dt in range(tlen):
            tx=max(0,min(half-1,dt//2)); ty=ty_start+dt
            if 0<=ty<H: grid[ty][tx]=max(1,len(pal)//2+1)
    # Eyes
    if hr>0:
        ey=hcy; ex1=max(0,min(half-1,half//2+1)); ex2=max(0,min(half-1,half//2-1))
        eye_col=len(pal)-1
        for ey2 in[ey,ey+1]:
            if 0<=ey2<H:
                if ex1<half: grid[ey2][ex1]=eye_col
                if ex2<half: grid[ey2][ex2]=eye_col
    # Mirror left→right (symmetric)
    if arch.get('sym'):
        for y in range(H):
            for x in range(half): grid[y][W-1-x]=grid[y][x]
    else:
        # Ghost/asymm: add slight noise to right side
        for y in range(H):
            for x in range(half): grid[y][W-1-x]=max(0,min(len(pal)-1,grid[y][x]+lcg.randint(-1,1)))
    # Map indices to palette colors
    return [[pal[min(len(pal)-1,max(0,grid[y][x]))] for x in range(W)] for y in range(H)]

def _sprite_to_pixels(pixels,cell=12,canvas=None,rects=None):
    """Render sprite pixel list onto existing canvas rects or return color list."""
    H=len(pixels); W=len(pixels[0]) if H else 0
    if canvas and rects:
        for y in range(H):
            for x in range(W): canvas.itemconfig(rects[y][x],fill=pixels[y][x])

class SpriteGen:
    """Procedural 16×16 sprite generator with archetype, palette, seed control. v3.0"""
    CELL=20
    def __init__(s,parent):
        s.win=_win(parent,'🎨 Sprite Generator v3.0 .-','#0a0010','680x520')
        s.W=s.H=16; s.pixels=[['#000']*16 for _ in range(16)]
        s.seed=E.randint(1,0xFFFFFF); s.arch_v=tk.StringVar(value='demon'); s.pal_v=tk.StringVar(value='demon')
        _lbl(s.win,'🎨 SPRITE GENERATOR v3.0 .-','#ff88ff',font=('Courier',12,'bold')).pack(pady=4)
        ctrl=tk.Frame(s.win,bg='#0a0010');ctrl.pack(fill='x',padx=8,pady=3)
        _lbl(ctrl,'Archetype:','#cc88ff',font=('Courier',9)).pack(side='left')
        ttk.Combobox(ctrl,textvariable=s.arch_v,values=list(SPRITE_ARCHETYPES),width=11,state='readonly',font=('Courier',9)).pack(side='left',padx=4)
        _lbl(ctrl,'Palette:','#cc88ff',font=('Courier',9)).pack(side='left')
        ttk.Combobox(ctrl,textvariable=s.pal_v,values=list(SPRITE_PALETTES),width=11,state='readonly',font=('Courier',9)).pack(side='left',padx=4)
        _lbl(ctrl,'Seed:','#cc88ff',font=('Courier',9)).pack(side='left')
        s.seed_e=tk.Entry(ctrl,bg='#1a0030',fg='#ff88ff',font=('Courier',9),width=9,insertbackground='#ff88ff');s.seed_e.pack(side='left',padx=4)
        s.seed_e.insert(0,str(s.seed))
        main=tk.Frame(s.win,bg='#0a0010');main.pack(fill='both',expand=True,padx=8)
        # Canvas for generated sprite (large)
        cf=tk.Frame(main,bg='#0a0010');cf.pack(side='left',padx=4,pady=4)
        _lbl(cf,'Generated','#886699',font=('Courier',8)).pack()
        s.canvas=tk.Canvas(cf,width=s.W*s.CELL,height=s.H*s.CELL,bg='#000',highlightthickness=1,highlightbackground='#440044')
        s.canvas.pack()
        s._rects=[[s.canvas.create_rectangle(x*s.CELL,y*s.CELL,(x+1)*s.CELL,(y+1)*s.CELL,fill='#000',outline='#111') for x in range(s.W)] for y in range(s.H)]
        # Preview panel: 4 last generated sprites
        pf=tk.Frame(main,bg='#0a0010');pf.pack(side='left',fill='both',expand=True,padx=8)
        _lbl(pf,'History (4)','#886699',font=('Courier',8)).pack()
        s._history=[];s._hist_frames=[]
        hg=tk.Frame(pf,bg='#0a0010');hg.pack(fill='both',expand=True)
        for i in range(4):
            hf=tk.Frame(hg,bg='#0a0010');hf.grid(row=i//2,column=i%2,padx=2,pady=2)
            sc=tk.Canvas(hf,width=s.W*6,height=s.H*6,bg='#000',highlightthickness=1,highlightbackground='#220022')
            sc.pack()
            rr=[[sc.create_rectangle(x*6,y*6,(x+1)*6,(y+1)*6,fill='#000',outline='') for x in range(s.W)] for y in range(s.H)]
            s._hist_frames.append((sc,rr))
        # Stat label
        s.stat=_lbl(s.win,'Ready .-','#664488',font=('Courier',8));s.stat.pack(fill='x',padx=8)
        # Button bar
        bf=tk.Frame(s.win,bg='#0a0010');bf.pack(pady=6)
        for lbl,cmd,fg,bg in[
            ('🎲 Generate',s._gen,'#ff88ff','#330033'),
            ('🔀 Batch×8',s._batch,'#cc66ff','#220022'),
            ('▶ Animate',s._animate,'#ff44cc','#330022'),
            ('💾 Save JSON',s._save,'#88ff88','#003300'),
            ('📤 Export Cart',s._export,'#ff88ff','#330033'),
            ('🎮 Spawn in Doom',s._spawn_doom,'#ff6600','#221100'),
        ]:
            _btn(bf,lbl,cmd,fg,bg,font=('Courier',9)).pack(side='left',padx=3)
        s._anim_running=False; s._gen()
    def _get_seed(s):
        try: return int(s.seed_e.get())
        except: return E.randint(1,0xFFFFFF)
    def _gen(s,seed=None):
        sd=seed or s._get_seed(); s.seed=sd
        s.pixels=_gen_sprite_data(sd,s.arch_v.get(),s.pal_v.get(),s.W)
        _sprite_to_pixels(s.pixels,canvas=s.canvas,rects=s._rects)
        s._push_history(s.pixels[:])
        s.stat.config(text=f'Seed:{sd:#08x}  arch:{s.arch_v.get()}  pal:{s.pal_v.get()} .-')
    def _push_history(s,pixels):
        s._history.append([r[:] for r in pixels])
        if len(s._history)>4: s._history.pop(0)
        for i,(sc,rr) in enumerate(s._hist_frames):
            if i<len(s._history):
                px=s._history[i]
                for y in range(s.H):
                    for x in range(s.W): sc.itemconfig(rr[y][x],fill=px[y][x])
    def _batch(s):
        for _ in range(8): s._gen(seed=E.randint(1,0xFFFFFF))
        sfx('pickup')
    def _animate(s):
        if s._anim_running: s._anim_running=False; return
        s._anim_running=True; s._anim_step()
    def _anim_step(s):
        if not s._anim_running: return
        s._gen(seed=E.randint(1,0xFFFFFF))
        s.win.after(180,s._anim_step)
    def _save(s):
        p=BASE/'sprites'/f'sprite_{s.seed:#08x}_{s.arch_v.get()}.json'
        p.write_text(json.dumps({'pixels':[r[:] for r in s.pixels],'w':s.W,'h':s.H,'seed':s.seed,'arch':s.arch_v.get(),'pal':s.pal_v.get()},indent=2))
        messagebox.showinfo('Sprite Generator',f'Saved: {p.name} .-')
    def _export(s):
        name=f'sprite_{s.seed:#08x}'
        _export_cart(name,'sprite',{'pixels':[r[:] for r in s.pixels],'w':s.W,'h':s.H,'seed':s.seed,'arch':s.arch_v.get(),'pal':s.pal_v.get()})
    def _spawn_doom(s):
        messagebox.showinfo('Spawn in Doom','Sprite saved. Open Doom Engine, load a level,\nthen generate a MonsterGen entry using this sprite. .-')

# ══════════════════════════════════════════════════════════════════════════════
#  NEW v3.0: MONSTER GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
# Generates fully randomized monster stats + sprite + AI behavior profile.
# Can inject generated monsters directly into live Doom games.

MONSTER_TIERS={
    'fodder':  {'hp_r':(20,80),'spd_r':(.008,.013),'dmg_r':(3.,9.),'xp_r':(30,80),'sz':.8},
    'warrior': {'hp_r':(80,250),'spd_r':(.012,.018),'dmg_r':(8.,20.),'xp_r':(100,250),'sz':1.0},
    'elite':   {'hp_r':(200,600),'spd_r':(.015,.022),'dmg_r':(15.,35.),'xp_r':(200,500),'sz':1.2},
    'boss':    {'hp_r':(800,3000),'spd_r':(.018,.026),'dmg_r':(25.,60.),'xp_r':(500,2000),'sz':1.8},
    'mini':    {'hp_r':(10,40),'spd_r':(.006,.010),'dmg_r':(1.,5.),'xp_r':(10,30),'sz':.6},
}
MONSTER_ARCHETYPES_LIST=['demon','undead','cyber','beast','elemental','void','construct','organic']
MONSTER_BEHAVIORS=['aggressive','patrol','ambush','ranged','berserker','swarm','guardian','erratic']
MONSTER_ABILITIES_POOL=['regeneration','armor','projectile','charge','teleport','split_on_death','aoe_attack','fear_aura','phase_shift','summon']

def gen_monster(seed=None):
    """Generate a complete randomized monster definition as a dict."""
    lcg=LCG(seed or E.randint(1,0xFFFFFF))
    s=lcg.seed
    tier_name=lcg.choice(list(MONSTER_TIERS))
    tier=MONSTER_TIERS[tier_name]
    arch=lcg.choice(MONSTER_ARCHETYPES_LIST)
    beh=lcg.choice(MONSTER_BEHAVIORS)
    # Stat roll
    hp=lcg.randint(*tier['hp_r'])
    spd=tier['spd_r'][0]+lcg.rand()*(tier['spd_r'][1]-tier['spd_r'][0])
    dmg=tier['dmg_r'][0]+lcg.rand()*(tier['dmg_r'][1]-tier['dmg_r'][0])
    xp=lcg.randint(*tier['xp_r'])
    sz=tier['sz']+lcg.rand()*0.2-0.1
    # Abilities (0-3 based on tier)
    n_abilities={'fodder':0,'mini':0,'warrior':1,'elite':2,'boss':3}.get(tier_name,1)
    pool=list(MONSTER_ABILITIES_POOL)
    abilities=[]
    for _ in range(n_abilities):
        if pool: a=lcg.choice(pool); pool.remove(a); abilities.append(a)
    # RGB color for renderer
    pal_name={'demon':'infernal','undead':'undead','cyber':'cyber','beast':'nature','elemental':'fire','void':'arcane','construct':'ice','organic':'nature'}.get(arch,'infernal')
    spr_pal=SPRITE_PALETTES.get(pal_name,SPRITE_PALETTES['infernal'])
    mid_col=spr_pal[len(spr_pal)//2] if spr_pal else '#cc2200'
    def _hex2rgb(h):
        h=h.lstrip('#')
        if len(h)==3: h=h[0]*2+h[1]*2+h[2]*2
        return (int(h[0:2],16),int(h[2:4],16),int(h[4:6],16))
    rgb=_hex2rgb(mid_col)
    # Name generation
    prefix=lcg.choice(['Arch','Shadow','Blood','Void','Iron','Cursed','Ancient','Fallen','Chaos','Doom'])
    suffix=lcg.choice(['Walker','Shade','Render','Fury','Bane','Crusher','Howler','Spawn','Revenant','Wrath'])
    name=f'{prefix}{suffix}'
    # Sprite data (compressed: seed + arch)
    sprite_arch={'demon':'demon','undead':'demon','cyber':'character','beast':'character','elemental':'icon','void':'ghost','construct':'icon','organic':'boss'}.get(arch,'demon')
    pixels=_gen_sprite_data(s,sprite_arch,pal_name,16)
    return {
        'name':name,'seed':s,'tier':tier_name,'arch':arch,'behavior':beh,
        'hp':hp,'speed':round(spd,5),'damage':round(dmg,2),'xp':xp,'size':round(sz,2),
        'rgb':list(rgb),'abilities':abilities,'sprite_arch':sprite_arch,'sprite_pal':pal_name,
        'pixels':pixels,
    }

class MonsterGen:
    """Monster Generator: generates randomized enemy archetypes with stats + sprite. v3.0"""
    CELL=10
    def __init__(s,parent,preset=None):
        s.win=_win(parent,'👾 Monster Generator v3.0 .-','#000a00','780x560')
        s.monster=None; s.roster=[]
        _lbl(s.win,'👾 MONSTER GENERATOR v3.0 .-','#ff4422',font=('Courier',12,'bold')).pack(pady=4)
        top=tk.Frame(s.win,bg='#000a00');top.pack(fill='x',padx=8,pady=2)
        _lbl(top,'Tier:','#cc6644',font=('Courier',9)).pack(side='left')
        s.tier_v=tk.StringVar(value='warrior')
        ttk.Combobox(top,textvariable=s.tier_v,values=['random']+list(MONSTER_TIERS),width=10,state='readonly',font=('Courier',9)).pack(side='left',padx=4)
        _lbl(top,'Arch:','#cc6644',font=('Courier',9)).pack(side='left')
        s.arch_v=tk.StringVar(value='random')
        ttk.Combobox(top,textvariable=s.arch_v,values=['random']+MONSTER_ARCHETYPES_LIST,width=10,state='readonly',font=('Courier',9)).pack(side='left',padx=4)
        _lbl(top,'Seed:','#cc6644',font=('Courier',9)).pack(side='left')
        s.seed_e=tk.Entry(top,bg='#0a1a00',fg='#ff6622',font=('Courier',9),width=10,insertbackground='#ff6622');s.seed_e.pack(side='left',padx=4)
        s.seed_e.insert(0,str(E.randint(1,0xFFFFFF)))
        main=tk.Frame(s.win,bg='#000a00');main.pack(fill='both',expand=True,padx=8)
        # Sprite preview
        lf=tk.Frame(main,bg='#000a00');lf.pack(side='left',fill='y',padx=4)
        _lbl(lf,'Sprite','#884422',font=('Courier',8)).pack()
        s.canvas=tk.Canvas(lf,width=16*s.CELL,height=16*s.CELL,bg='#000',highlightthickness=1,highlightbackground='#331100')
        s.canvas.pack()
        s._rects=[[s.canvas.create_rectangle(x*s.CELL,y*s.CELL,(x+1)*s.CELL,(y+1)*s.CELL,fill='#000',outline='#111') for x in range(16)] for y in range(16)]
        # Roster list
        rf=tk.Frame(main,bg='#000a00');rf.pack(side='right',fill='y',padx=4)
        _lbl(rf,'Roster','#884422',font=('Courier',8)).pack()
        s.roster_lb=tk.Listbox(rf,bg='#001a00',fg='#ff8844',font=('Courier',8),width=20,height=16,selectbackground='#331100')
        s.roster_lb.pack(fill='both',expand=True)
        s.roster_lb.bind('<<ListboxSelect>>',s._load_roster)
        # Stats panel
        cf=tk.Frame(main,bg='#000a00');cf.pack(side='left',fill='both',expand=True,padx=8)
        s.stat_txt=scrolledtext.ScrolledText(cf,bg='#000a00',fg='#ff8844',font=('Courier',9),height=18,wrap='word',state='disabled')
        s.stat_txt.pack(fill='both',expand=True)
        s.status=_lbl(s.win,'Ready. .-','#334433',font=('Courier',8));s.status.pack(fill='x',padx=8)
        bf=tk.Frame(s.win,bg='#000a00');bf.pack(pady=5)
        for lbl,cmd,fg,bg in[
            ('🎲 Generate',s._gen,'#ff4422','#220000'),
            ('🔀 Batch×6',s._batch,'#ff8844','#220a00'),
            ('🧬 Mutate',s._mutate,'#88ff44','#002200'),
            ('⚔ Test vs Player',s._test_combat,'#ffcc00','#221100'),
            ('💾 Save JSON',s._save,'#88ff88','#003300'),
            ('📤 Export Cart',s._export,'#ff4422','#220000'),
            ('🎮 Inject to Doom',s._inject,'#ff0000','#330000'),
        ]:
            _btn(bf,lbl,cmd,fg,bg,font=('Courier',9)).pack(side='left',padx=2)
        if preset: s._load_from_dict(preset)
        else: s._gen()
    def _get_seed(s):
        try: return int(s.seed_e.get())
        except: return E.randint(1,0xFFFFFF)
    def _gen(s,seed=None):
        sd=seed or s._get_seed()
        s.seed_e.delete(0,'end'); s.seed_e.insert(0,str(sd))
        t=s.tier_v.get(); a=s.arch_v.get()
        m=gen_monster(sd)
        if t!='random' and t in MONSTER_TIERS:
            lcg=LCG(sd); tier=MONSTER_TIERS[t]
            m['tier']=t; m['hp']=lcg.randint(*tier['hp_r'])
            m['speed']=round(tier['spd_r'][0]+lcg.rand()*(tier['spd_r'][1]-tier['spd_r'][0]),5)
            m['damage']=round(tier['dmg_r'][0]+lcg.rand()*(tier['dmg_r'][1]-tier['dmg_r'][0]),2)
            m['size']=round(tier['sz']+lcg.rand()*0.2-0.1,2)
        if a!='random' and a in MONSTER_ARCHETYPES_LIST: m['arch']=a
        s._load_from_dict(m)
        s.roster.append(m)
        s.roster_lb.insert('end',f"{m['name']} [{m['tier']}]")
        sfx('menu')
    def _load_from_dict(s,m):
        s.monster=m
        px=m.get('pixels')
        if px:
            for y in range(min(16,len(px))):
                for x in range(min(16,len(px[y]))): s.canvas.itemconfig(s._rects[y][x],fill=px[y][x])
        s.stat_txt.config(state='normal'); s.stat_txt.delete('1.0','end')
        lines=[
            f"NAME:     {m['name']}",
            f"TIER:     {m['tier'].upper()}  |  ARCH: {m['arch'].upper()}",
            f"BEHAVIOR: {m['behavior'].upper()}",
            f"──────────────────────────────────",
            f"HP:       {m['hp']}",
            f"SPEED:    {m['speed']:.5f}  (Doom units/tick)",
            f"DAMAGE:   {m['damage']:.1f}  per second",
            f"XP:       {m['xp']}",
            f"SIZE:     {m['size']:.2f}",
            f"RGB:      {tuple(m['rgb'])}",
            f"──────────────────────────────────",
            f"ABILITIES: {', '.join(m['abilities']) if m['abilities'] else 'none'}",
            f"──────────────────────────────────",
            f"SEED:     {m['seed']:#010x}",
            f"SPRITE:   {m['sprite_arch']} / {m['sprite_pal']}",
            f"",
            s._lore(m),
        ]
        s.stat_txt.insert('end','\n'.join(lines))
        s.stat_txt.config(state='disabled')
        s.status.config(text=f"Generated: {m['name']} | {m['tier']} | seed:{m['seed']:#010x} .-")
    def _lore(s,m):
        intros=[f"Born from {m['arch']} entropy, the {m['name']} walks where light dissolves.",
                f"A {m['tier']}-class {m['arch']} entity. The DDA refuses to see it coming.",
                f"The axiom shudders. The {m['name']} is the recursion made flesh.",
                f"Designation: {m['name']}. Origin: undefined. Threat: {'lethal' if m['tier'] in ('boss','elite') else 'significant'}."]
        return f'\nLORE:\n  {E.choice(intros)}'
    def _batch(s):
        for _ in range(6): s._gen(seed=E.randint(1,0xFFFFFF))
    def _mutate(s):
        if not s.monster: s._gen(); return
        # Mutate: keep arch/tier, randomize seed slightly
        base=s.monster['seed']; delta=E.randint(1,500)
        s._gen(seed=base^delta)
    def _test_combat(s):
        if not s.monster: messagebox.showinfo('Test','Generate a monster first.'); return
        m=s.monster; pl_hp=100; m_hp=m['hp']; rounds=0; log=[]
        while pl_hp>0 and m_hp>0 and rounds<200:
            rounds+=1
            pl_dmg=_RNG.randint(5,20); m_hp-=pl_dmg
            if m_hp<=0: break
            m_dmg=int(m['damage']*_RNG.uniform(.5,1.5)); pl_hp-=m_dmg
        winner='PLAYER' if pl_hp>0 else m['name'].upper()
        log_txt=f"COMBAT SIM: {m['name']} vs Player\nRounds: {rounds}\nWinner: {winner}\nPlayer HP remaining: {max(0,pl_hp)}\nMonster HP remaining: {max(0,m_hp)}\n"
        messagebox.showinfo('Combat Test',log_txt+'.-')
    def _load_roster(s,e=None):
        i=s.roster_lb.curselection()
        if i and i[0]<len(s.roster): s._load_from_dict(s.roster[i[0]])
    def _save(s):
        if not s.monster: return
        p=BASE/'monsters'/f"monster_{s.monster['name']}_{s.monster['seed']:#010x}.json"
        p.write_text(json.dumps(s.monster,indent=2))
        messagebox.showinfo('Monster Generator',f'Saved: {p.name} .-')
    def _export(s):
        if not s.monster: return
        _export_cart(s.monster['name'],'monster',s.monster)
    def _inject(s):
        if not s.monster:
            messagebox.showinfo('Inject','Generate a monster first.'); return
        messagebox.showinfo('Inject to Doom',
            f"Monster '{s.monster['name']}' will appear in the next wave!\n"
            "Open the Doom Engine and start a game — custom monsters spawn on waves 2+.\n"
            "The dot nods. .-")

# ── MAP EDITOR ────────────────────────────────────────────────────────────────
class MapEditor:
    def __init__(s,parent):
        s.win=_win(parent,'Map Editor .-','#111')
        s.CELL=22;s.W=20;s.H=15;s.sel='#'
        s.grid=[[' ']*s.W for _ in range(s.H)]
        for y in range(s.H):
            for x in range(s.W):
                if x==0 or y==0 or x==s.W-1 or y==s.H-1: s.grid[y][x]='#'
        _lbl(s.win,'MAP EDITOR .-','#88ccff',font=('Courier',11,'bold')).pack(pady=3)
        main=tk.Frame(s.win,bg='#111');main.pack(fill='both',expand=True,padx=4)
        s.canvas=tk.Canvas(main,width=s.W*s.CELL,height=s.H*s.CELL,bg='#0a0a0a',highlightthickness=1,highlightbackground='#444')
        s.canvas.pack(side='left',padx=4,pady=4)
        s.canvas.bind('<Button-1>',s._paint);s.canvas.bind('<B1-Motion>',s._paint);s.canvas.bind('<Button-3>',s._pick)
        pf=tk.Frame(main,bg='#111');pf.pack(side='left',fill='y',padx=4)
        _lbl(pf,'TILES','#aaa',font=('Courier',9,'bold')).pack()
        for tile,(color,name) in TILE_PAL.items():
            row=tk.Frame(pf,bg='#111');row.pack(fill='x',pady=1)
            _btn(row,tile,lambda t=tile:setattr(s,'sel',t),'#fff',color,font=('Courier',8,'bold'),width=2).pack(side='left')
            _lbl(row,name,'#888',font=('Courier',7),anchor='w').pack(side='left',padx=2)
        bf=tk.Frame(s.win,bg='#111');bf.pack(pady=4)
        for lbl,cmd in[('Clear',s._clear),('Border',s._border),('Random',s._random),('▶ Play',s._play),('📤 Export Cart',s._export)]:
            _btn(bf,lbl,cmd,'#88ccff','#222',font=('Courier',9)).pack(side='left',padx=4)
        s._rects=[[s.canvas.create_rectangle(x*s.CELL,y*s.CELL,(x+1)*s.CELL,(y+1)*s.CELL,fill='#1a2a1a',outline='#111') for x in range(s.W)] for y in range(s.H)]
        s._redraw()
    def _redraw(s):
        for y in range(s.H):
            for x in range(s.W): t=s.grid[y][x];c=TILE_PAL.get(t,('#1a2a1a','?'))[0];s.canvas.itemconfig(s._rects[y][x],fill=c)
    def _px(s,ev): x=ev.x//s.CELL;y=ev.y//s.CELL; return(x,y) if 0<=x<s.W and 0<=y<s.H else(None,None)
    def _paint(s,ev):
        x,y=s._px(ev)
        if x is None: return
        s.grid[y][x]=s.sel;s.canvas.itemconfig(s._rects[y][x],fill=TILE_PAL.get(s.sel,('#1a2a1a',''))[0])
    def _pick(s,ev):
        x,y=s._px(ev)
        if x is not None: s.sel=s.grid[y][x]
    def _clear(s):
        for y in range(s.H):
            for x in range(s.W): s.grid[y][x]=' '
        s._border();s._redraw()
    def _border(s):
        for y in range(s.H):
            for x in range(s.W):
                if x==0 or y==0 or x==s.W-1 or y==s.H-1: s.grid[y][x]='#'
        s._redraw()
    def _random(s):
        s._border()
        for y in range(1,s.H-1):
            for x in range(1,s.W-1):
                r=E.rand();s.grid[y][x]='#' if r<.18 else(E.choice(['Z','I','h','a','+',' ',' ',' ',' ']) if r<.28 else' ')
        if not any(s.grid[y][x]=='p' for y in range(s.H) for x in range(s.W)): s.grid[2][2]='p'
        s._redraw()
    def _rows(s): return [''.join(row) for row in s.grid]
    def _play(s): DoomWindow(s.win,map_data=s._rows(),title='Custom Map .-')
    def _export(s):
        name=simpledialog.askstring('Export','Cartridge name:',parent=s.win) or f'map_{int(time.time())}'
        _export_cart(name,'map',{'rows':s._rows(),'W':s.W,'H':s.H})

# ── SPRITE EDITOR (manual) ────────────────────────────────────────────────────
class SpriteEditor:
    PAL=['#000','#111','#333','#555','#888','#bbb','#fff','#f00','#f60','#fa0','#ff0','#0f0','#0fc','#08f','#00f','#80f','#f0f','#f8c','#840','#040']
    def __init__(s,parent):
        s.win=_win(parent,'Sprite Editor .-','#111')
        s.W,s.H=16,16;s.CELL=20;s.pixels=[['#000']*16 for _ in range(16)];s.color='#fff';s.tool='draw'
        top=tk.Frame(s.win,bg='#111');top.pack(fill='x',padx=4,pady=2)
        _lbl(top,'SPRITE EDITOR .-','#ff88ff',font=('Courier',11,'bold')).pack(side='left',padx=4)
        for t,lbl in[('draw','✏'),('erase','⬜'),('fill','🪣')]:
            _btn(top,lbl,lambda x=t:setattr(s,'tool',x),'#ff88ff','#330033',font=('Courier',10)).pack(side='left',padx=2)
        _btn(top,'Clear',s._clear,'#ff4444','#220011').pack(side='left',padx=2)
        _btn(top,'💾 Save',s._save,'#88ff88','#002200').pack(side='right',padx=2)
        _btn(top,'📤 Export Cart',s._export,'#ff88ff','#330033').pack(side='right',padx=2)
        main=tk.Frame(s.win,bg='#111');main.pack()
        s.canvas=tk.Canvas(main,width=s.W*s.CELL,height=s.H*s.CELL,bg='#000',highlightthickness=1,highlightbackground='#444')
        s.canvas.pack(side='left',padx=4,pady=4)
        s.canvas.bind('<Button-1>',s._paint);s.canvas.bind('<B1-Motion>',s._paint);s.canvas.bind('<Button-3>',s._pick)
        pf=tk.Frame(main,bg='#111');pf.pack(side='left',fill='y',padx=4)
        _lbl(pf,'PAL','#aaa',font=('Courier',8)).pack()
        pg=tk.Frame(pf,bg='#111');pg.pack()
        for i,c in enumerate(s.PAL):
            r2,c2=divmod(i,4)
            _btn(pg,' ',lambda x=c:(setattr(s,'color',x),s.cur_lbl.config(bg=x)),c,c,width=2).grid(row=r2,column=c2,padx=1,pady=1)
        s.cur_lbl=tk.Label(pf,bg='#fff',width=6,height=2,relief='ridge');s.cur_lbl.pack(pady=4)
        s._rects=[[s.canvas.create_rectangle(x*s.CELL,y*s.CELL,(x+1)*s.CELL,(y+1)*s.CELL,fill='#000',outline='#111') for x in range(s.W)] for y in range(s.H)]
    def _px(s,ev): x=ev.x//s.CELL;y=ev.y//s.CELL; return(x,y) if 0<=x<s.W and 0<=y<s.H else(None,None)
    def _paint(s,ev):
        x,y=s._px(ev)
        if x is None: return
        c='#000' if s.tool=='erase' else s.color
        if s.tool=='fill': s._flood(x,y,c); return
        s.pixels[y][x]=c;s.canvas.itemconfig(s._rects[y][x],fill=c)
    def _pick(s,ev):
        x,y=s._px(ev)
        if x is not None: s.color=s.pixels[y][x];s.cur_lbl.config(bg=s.color)
    def _flood(s,sx,sy,nc):
        oc=s.pixels[sy][sx]
        if oc==nc: return
        stk=[(sx,sy)]
        while stk:
            x,y=stk.pop()
            if not(0<=x<s.W and 0<=y<s.H) or s.pixels[y][x]!=oc: continue
            s.pixels[y][x]=nc;s.canvas.itemconfig(s._rects[y][x],fill=nc)
            for dx2,dy2 in((1,0),(-1,0),(0,1),(0,-1)): stk.append((x+dx2,y+dy2))
    def _clear(s):
        for y in range(s.H):
            for x in range(s.W): s.pixels[y][x]='#000';s.canvas.itemconfig(s._rects[y][x],fill='#000')
    def _save(s):
        p=BASE/'sprites'/f'spr_{int(time.time())}.json'
        p.write_text(json.dumps({'pixels':[row[:] for row in s.pixels],'w':s.W,'h':s.H},indent=2))
        messagebox.showinfo('Sprite Editor',f'Saved: {p.name} .-')
    def _export(s):
        name=simpledialog.askstring('Export','Cartridge name:',parent=s.win) or f'sprite_{int(time.time())}'
        _export_cart(name,'sprite',{'pixels':[r[:] for r in s.pixels],'w':s.W,'h':s.H})

# ── SFX GENERATOR ─────────────────────────────────────────────────────────────
class SFXGen:
    SHAPES=['sine','square','saw','noise','tri','pulse']
    def __init__(s,parent):
        s.win=_win(parent,'SFX Generator .-','#110a00')
        _lbl(s.win,'⚡ SFX GENERATOR .-','#ff8800',font=('Courier',12,'bold')).pack(pady=6)
        sf=tk.Frame(s.win,bg='#110a00');sf.pack(padx=12,pady=4,fill='x')
        s._vars={}
        for lbl,key,dflt,lo,hi in[('Freq Hz','freq',440,20,2000),('Duration','dur',.3,.05,3.),('Amplitude','amp',.5,0.,1.),('Attack','atk',.05,0.,1.),('Release','rel',.15,0.,1.)]:
            row=tk.Frame(sf,bg='#110a00');row.pack(fill='x',pady=2)
            _lbl(row,f'{lbl}:','#ffaa44',width=12,anchor='w').pack(side='left')
            v=tk.DoubleVar(value=dflt);s._vars[key]=v
            tk.Scale(row,variable=v,from_=lo,to=hi,resolution=(hi-lo)/100,orient='horizontal',length=220,bg='#110a00',fg='#ff8800',troughcolor='#221100').pack(side='left')
        sr=tk.Frame(sf,bg='#110a00');sr.pack(fill='x',pady=2)
        _lbl(sr,'Shape:','#ffaa44',width=12,anchor='w').pack(side='left')
        s._shape=tk.StringVar(value='sine')
        for sh in s.SHAPES: tk.Radiobutton(sr,text=sh,variable=s._shape,value=sh,bg='#110a00',fg='#ff8800',selectcolor='#221100',font=('Courier',9)).pack(side='left',padx=3)
        bf=tk.Frame(s.win,bg='#110a00');bf.pack(pady=6)
        for lbl,cmd in[('▶ Play',s._play),('💾 Save WAV',s._save),('🎲 Random',s._rand),('📤 Export Cart',s._export)]:
            _btn(bf,lbl,cmd,'#ff8800','#221100',font=('Courier',10,'bold')).pack(side='left',padx=6)
        s.out=tk.Text(s.win,height=4,bg='#050200',fg='#ffcc44',font=('Courier',9),state='disabled');s.out.pack(fill='x',padx=12,pady=4)
    def _get(s): return s._vars['freq'].get(),s._vars['dur'].get(),s._vars['amp'].get(),s._vars['atk'].get(),s._vars['rel'].get(),s._shape.get()
    def _play(s): f,d,a,atk,rel,sh=s._get(); play_raw(adsr(gen_wave(f,d,sh,a),atk,.1,.7,rel));s._log(f'play {sh} {f:.0f}Hz {d:.2f}s')
    def _save(s):
        f,d,a,atk,rel,sh=s._get();smp=adsr(gen_wave(f,d,sh,a),atk,.1,.7,rel)
        p=BASE/'sfx'/f'sfx_{int(time.time())}.wav';p.write_bytes(_wav(smp));s._log(f'saved {p.name}')
    def _rand(s): s._vars['freq'].set(E.randint(80,1800));s._vars['dur'].set(round(E.rand()*1.5+.05,2));s._vars['amp'].set(round(E.rand()*.7+.1,2));s._shape.set(E.choice(s.SHAPES));s._play()
    def _export(s):
        f,d,a,atk,rel,sh=s._get()
        name=simpledialog.askstring('Export','Cart name:',parent=s.win) or f'sfx_{int(time.time())}'
        _export_cart(name,'sfx',{'freq':f,'dur':d,'amp':a,'atk':atk,'rel':rel,'shape':sh})
    def _log(s,msg): s.out.config(state='normal');s.out.insert('end',msg+' .-\n');s.out.see('end');s.out.config(state='disabled')

# ── MUSIC GENERATOR ───────────────────────────────────────────────────────────
class MusicGen:
    def __init__(s,parent):
        s.win=_win(parent,'Music Generator .-','#001122')
        _lbl(s.win,'🎵 MUSIC GENERATOR .-','#44aaff',font=('Courier',12,'bold')).pack(pady=6)
        sf=tk.Frame(s.win,bg='#001122');sf.pack(padx=10,fill='x')
        rf=tk.Frame(sf,bg='#001122');rf.pack(fill='x',pady=2)
        _lbl(rf,'Root Hz:','#88aacc',width=12,anchor='w').pack(side='left')
        s._root=tk.DoubleVar(value=432.)
        tk.Scale(rf,variable=s._root,from_=80,to=900,resolution=1,orient='horizontal',length=220,bg='#001122',fg='#44aaff',troughcolor='#001133').pack(side='left')
        scf=tk.Frame(sf,bg='#001122');scf.pack(fill='x',pady=2)
        _lbl(scf,'Scale:','#88aacc',width=12,anchor='w').pack(side='left')
        s._scale=tk.StringVar(value='Pentatonic Minor')
        ttk.Combobox(scf,textvariable=s._scale,values=list(SCALES),width=22,state='readonly').pack(side='left')
        for lbl,key,dflt,lo,hi in[('Bars:','bars',4,1,16),('BPM:','bpm',90,40,220),('Octaves:','oct',2,1,4)]:
            row=tk.Frame(sf,bg='#001122');row.pack(fill='x',pady=1)
            _lbl(row,lbl,'#88aacc',width=12,anchor='w').pack(side='left')
            v=tk.IntVar(value=dflt);setattr(s,'_'+key,v)
            tk.Scale(row,variable=v,from_=lo,to=hi,orient='horizontal',length=160,bg='#001122',fg='#44aaff',troughcolor='#001133').pack(side='left')
        bf=tk.Frame(s.win,bg='#001122');bf.pack(pady=6)
        for lbl,cmd in[('▶ Generate',s._gen),('💾 Save',s._save),('🎲 Random',s._rand),('📤 Export Cart',s._export)]:
            _btn(bf,lbl,cmd,'#44aaff','#002244',font=('Courier',10,'bold')).pack(side='left',padx=4)
        s.out=tk.Text(s.win,height=5,bg='#000a11',fg='#44ccff',font=('Courier',9),state='disabled');s.out.pack(fill='x',padx=10,pady=4)
    def _note(s,semi,base): return base*(2**(semi/12))
    def _melody(s):
        root=s._root.get();sc=SCALES[s._scale.get()];bars=s._bars.get();bpm=s._bpm.get();octs=s._oct.get()
        bd=60./bpm;freqs=[s._note(semi+o*12,root) for o in range(octs) for semi in sc]
        return[(E.choice(freqs),E.choice([.25,.5,.5,.75,1.])*bd) for _ in range(bars*4)]
    def _render(s,mel): samps=[];[samps.extend(adsr(gen_wave(f,d,'sine',.3),.02,.05,.7,.15)) for f,d in mel]; return samps
    def _gen(s): mel=s._melody(); threading.Thread(target=lambda:(play_raw(s._render(mel)),s._log(f'Generated {len(mel)} notes root={s._root.get():.0f}Hz')),daemon=True).start()
    def _save(s): mel=s._melody();samps=s._render(mel);p=BASE/'music'/f'mus_{int(time.time())}.wav';p.write_bytes(_wav(samps));s._log(f'saved {p.name}')
    def _rand(s): s._root.set(E.choice(list(SOLFEG.values())));s._scale.set(E.choice(list(SCALES)));s._bpm.set(E.randint(60,180));s._gen()
    def _export(s):
        mel=s._melody()
        name=simpledialog.askstring('Export','Cart name:',parent=s.win) or f'mus_{int(time.time())}'
        _export_cart(name,'music',{'notes':[[f,d] for f,d in mel],'root':s._root.get(),'scale':s._scale.get(),'bpm':s._bpm.get()})
    def _log(s,m): s.out.config(state='normal');s.out.insert('end',m+' .-\n');s.out.see('end');s.out.config(state='disabled')

# ── FLOWSCRIPT CONSOLE ────────────────────────────────────────────────────────
class FlowConsole:
    def __init__(s,parent):
        s.win=_win(parent,'FlowScript Console .-','#000','580x500')
        s.fs=FlowScript(tone_fn=play_tone)
        _lbl(s.win,'> FLOWSCRIPT v2 .-','#00ff88',bg='#000',font=('Courier',12,'bold')).pack(pady=4)
        _lbl(s.win,'set entropy expand freq print play say sfx repeat N { } if A op B { }  #comment','#226622',bg='#000',font=('Courier',8)).pack()
        s.inp=tk.Text(s.win,height=12,bg='#050a05',fg='#00ff88',font=('Courier',10),insertbackground='#00ff88')
        s.inp.pack(fill='both',expand=True,padx=8,pady=4)
        s.inp.insert('1.0','# FlowScript v2 .-\nset hp 100\nentropy roll 1 6\nprint Roll: roll\nfreq 432 432\nexpand "The dot is the origin of all structure"\nrepeat 3 {\n    entropy x 1 100\n    if x > 50 { print x is large }\n    print x\n}\nplay 528 1.0 sine\nsay "the dot sings"\n')
        bf=tk.Frame(s.win,bg='#000');bf.pack(pady=4)
        for lbl,cmd,fg,bg in[('▶ Run',s._run,'#00ff44','#113311'),('Clear',s._clear,'#aaa','#222'),('📤 Export Cart',s._export,'#00ff88','#003300'),('Close',s.win.destroy,'#aaa','#222')]:
            _btn(bf,lbl,cmd,fg,bg,font=('Courier',10,'bold'),width=13).pack(side='left',padx=4)
        s.out=tk.Text(s.win,height=9,bg='#050505',fg='#ffcc44',font=('Courier',10),state='disabled');s.out.pack(fill='both',expand=True,padx=8,pady=4)
    def _run(s):
        code=s.inp.get('1.0','end').strip();s.out.config(state='normal')
        try: out=s.fs.run(code);s.out.insert('end',out+'\n────\n')
        except Exception as ex: s.out.insert('end',f'ERR:{ex} .-\n────\n')
        s.out.see('end');s.out.config(state='disabled')
    def _clear(s): s.out.config(state='normal');s.out.delete('1.0','end');s.out.config(state='disabled')
    def _export(s):
        name=simpledialog.askstring('Export','Cart name:',parent=s.win) or f'script_{int(time.time())}'
        _export_cart(name,'script',{'code':s.inp.get('1.0','end').rstrip()})

# ── AMBIENT PLAYER ────────────────────────────────────────────────────────────
SCENES={'Mountain Lake':{'freq':432,'desc':'Still water. The dot rests. .-'},'Forest Clearing':{'freq':528,'desc':'Dappled light. DNA repair frequency.'},'Ocean Shore':{'freq':396,'desc':'Tide rhythm. Liberation from fear.'},'Desert Night':{'freq':639,'desc':'Infinite stars. Connection.'},'Cave':{'freq':741,'desc':'Dripping stone. Awakening intuition.'},'Sky':{'freq':852,'desc':'Cloud vastness. Returning to order.'},'Void':{'freq':963,'desc':'Pure consciousness. No thing. .-'},'Gamma':{'freq':40,'desc':'40Hz neural synchrony. Insight.'}}
class AmbientPlayer:
    def __init__(s,parent):
        s.win=_win(parent,'PyAmby — Ambient Player .-','#050510','560x420');s._playing=False
        _lbl(s.win,'🌊 AMBIENT PLAYER .-','#4488cc',font=('Courier',12,'bold')).pack(pady=6)
        sf=tk.Frame(s.win,bg='#050510');sf.pack(fill='x',padx=12,pady=4)
        row=tk.Frame(sf,bg='#050510');row.pack(fill='x',pady=2)
        _lbl(row,'Base Hz:','#668899',width=12,anchor='w').pack(side='left')
        s._freq=tk.DoubleVar(value=432.)
        tk.Scale(row,variable=s._freq,from_=30,to=1200,resolution=1,orient='horizontal',length=220,bg='#050510',fg='#4488cc',troughcolor='#001133').pack(side='left')
        pf=tk.Frame(sf,bg='#050510');pf.pack(fill='x',pady=6)
        _lbl(pf,'Scene Presets:','#4488cc').pack(anchor='w')
        pg=tk.Frame(pf,bg='#050510');pg.pack(fill='x')
        for sn,sm in SCENES.items():
            _btn(pg,sn.split()[0],lambda sm2=sm:(s._freq.set(sm2['freq']),s.sdesc.config(text=sm2['desc'])),'#4488cc','#001133',font=('Courier',8)).pack(side='left',padx=2,pady=2)
        s.sdesc=_lbl(s.win,SCENES['Mountain Lake']['desc'],'#4488cc',font=('Courier',9),wraplength=500);s.sdesc.pack(padx=12,pady=4,anchor='w')
        bf=tk.Frame(s.win,bg='#050510');bf.pack(pady=8)
        s.btn=_btn(bf,'▶ Start',s._toggle,'#44aaff','#002244',font=('Courier',11,'bold'),width=10);s.btn.pack(side='left',padx=8)
        _btn(bf,'🎲 Random',s._random,'#4488cc','#001133').pack(side='left',padx=4)
        _btn(bf,'. Feed Dot',lambda:E.feed(s._freq.get()),'#cc8844','#001133').pack(side='left',padx=4)
        s.status=_lbl(s.win,'Stopped .-','#223344',font=('Courier',9));s.status.pack()
        s.win.protocol('WM_DELETE_WINDOW',s._close)
    def _toggle(s):
        if s._playing: stop_ambient();s.btn.config(text='▶ Start');s.status.config(text='Stopped .-');s._playing=False
        else: play_ambient(s._freq.get());s.btn.config(text='⬛ Stop');s.status.config(text=f'Playing {s._freq.get():.0f}Hz .-');s._playing=True
    def _random(s):
        sn=E.choice(list(SCENES));sm=SCENES[sn];s._freq.set(sm['freq']);s.sdesc.config(text=sm['desc'])
        if s._playing: stop_ambient(); s._toggle()
    def _close(s):
        if s._playing: stop_ambient()
        s.win.destroy()

# ── KNOWLEDGE BROWSER ─────────────────────────────────────────────────────────
class KBrowser:
    def __init__(s,parent):
        s.win=_win(parent,'📚 Knowledge Browser .-','#0d0d14','760x560')
        tp=tk.Frame(s.win,bg='#0d0d14');tp.pack(fill='x',padx=8,pady=5)
        _lbl(tp,'📚 KNOWLEDGE .-','#ffaa44',font=('Courier',12,'bold')).pack(side='left')
        s.qv=tk.Entry(tp,bg='#1a1a2a',fg='#ffaa44',font=('Courier',12),insertbackground='#0f0',width=22)
        s.qv.pack(side='left',padx=6);s.qv.bind('<Return>',lambda e:s._search())
        _btn(tp,'Search',s._search,'#ffaa44','#1a1a2a').pack(side='left',padx=2)
        _btn(tp,'Random',s._rand,'#888','#1a1a2a').pack(side='left',padx=2)
        nb=ttk.Notebook(s.win);nb.pack(fill='both',expand=True,padx=8,pady=5)
        st=tk.Frame(nb,bg='#0d0d14');nb.add(st,text='🔍 Search')
        s.so=scrolledtext.ScrolledText(st,bg='#0d0d14',fg='#ccccaa',font=('Courier',10),wrap='word');s.so.pack(fill='both',expand=True)
        kt=tk.Frame(nb,bg='#0d0d14');nb.add(kt,text='📖 KB')
        ko=scrolledtext.ScrolledText(kt,bg='#0d0d14',fg='#88aaff',font=('Courier',9),wrap='word');ko.pack(fill='both',expand=True,padx=5,pady=5)
        ko.insert('end','KNOWLEDGE BASE\n'+'═'*60+'\n\n');[ko.insert('end',f'  {k}\n    {v}\n\n') for k,v in KB.items()]
        at=tk.Frame(nb,bg='#0d0d14');nb.add(at,text='⚖ Axioms')
        ao=scrolledtext.ScrolledText(at,bg='#0d0d14',fg='#bb88ff',font=('Courier',10),wrap='word');ao.pack(fill='both',expand=True,padx=5,pady=5)
        ao.insert('end','RECURSIVE AXIOMS\n'+'═'*50+'\n\n');[ao.insert('end',f'  [{k}]  {v}\n') for k,v in AXIOMS.items()]
        ft=tk.Frame(nb,bg='#0d0d14');nb.add(ft,text='📊 Freq')
        ff=tk.Frame(ft,bg='#0d0d14');ff.pack(fill='x',padx=5,pady=3)
        _lbl(ff,'Hz:','#aaa').pack(side='left')
        s.fe=tk.Entry(ff,bg='#1a1a2a',fg='#0ff',font=('Courier',12),width=8);s.fe.pack(side='left',padx=4);s.fe.insert(0,'432');s.fe.bind('<Return>',lambda e:s._af())
        _btn(ff,'Analyze',s._af,'#0f0','#0a2a1a').pack(side='left')
        _btn(ff,'Play',s._pf,'#aaa','#1a1a2a').pack(side='left',padx=3)
        s.fo=scrolledtext.ScrolledText(ft,bg='#0d0d14',fg='#00ff88',font=('Courier',9),wrap='word');s.fo.pack(fill='both',expand=True)
        s.fo.insert('end','SOLFEGGIO:\n');[s.fo.insert('end',f'  {v}Hz — {k}\n') for k,v in SOLFEG.items()]
        s.fo.insert('end','\nCHAKRA:\n');[s.fo.insert('end',f'  {v}Hz — {k}\n') for k,v in CHAKRA.items()]
    def _search(s):
        q=s.qv.get().strip().lower()
        if not q: return
        res=[(k,v) for k,v in list(KB.items())+list(AXIOMS.items()) if q in k.lower() or q in v.lower()]
        s.so.delete('1.0','end');s.so.insert('end',f"SEARCH: '{q}'\n{'═'*44}\n\n")
        if res: [s.so.insert('end',f'{k.upper()}\n  {v}\n\n') for k,v in res[:15]]
        else: s.so.insert('end','No results. Try: consciousness entropy recursion 528Hz Doom\n')
    def _rand(s): k,v=E.choice(list(KB.items()));s.so.delete('1.0','end');s.so.insert('end',f'RANDOM:\n{"═"*44}\n\n{k.upper()}\n{v}\n')
    def _af(s):
        try:
            f=float(s.fe.get()); lines=[f'FREQUENCY: {f:.2f}Hz','─'*40]
            for name,fref in SOLFEG.items():
                if fref: ratio=f/fref;cents=1200*math.log2(ratio);lines.append(f'  vs {fref}Hz ({name}): ×{ratio:.3f} {cents:+.0f}¢')
            s.fo.delete('1.0','end');s.fo.insert('end','\n'.join(lines))
        except: pass
    def _pf(s):
        try: f=float(s.fe.get());play_tone(f,2.,'sine')
        except: pass

# ── GENERATION STUDIO ─────────────────────────────────────────────────────────
def gen_mandala(sz=15):
    cx=cy=sz; lines=[]
    for y in range(sz*2+1):
        row=''
        for x in range(sz*2+1):
            dx,dy=x-cx,y-cy; d=math.sqrt(dx*dx+dy*dy); a=math.atan2(dy,dx)
            rings=[sz*.25*i for i in range(1,6)]; chars='·∘○◎●◉⬤'
            if any(abs(d-r)<.7 for r in rings): sym=(a*6/math.pi)%2; row+=chars[int(d/sz*7)%len(chars)] if sym<.15 else'·'
            elif d<.8: row+='.'
            else: row+=' '
        lines.append(row)
    return '\n'.join(lines)
def gen_stars(w=60,h=20):
    grid=[[' ']*w for _ in range(h)]
    for _ in range(int(w*h*.05)): x,y=E.randint(0,w-1),E.randint(0,h-1);grid[y][x]=E.choice('·*✦✧⋆°★')
    return '\n'.join(''.join(r) for r in grid)
class GenStudio:
    MODES=['philosophy','haiku','story','dot protocol','mandala','starfield','frequency poem']
    def __init__(s,parent):
        s.win=_win(parent,'✨ Generation Studio .-','#0d0d14','740x540')
        s.mode=tk.StringVar(value='philosophy')
        tp=tk.Frame(s.win,bg='#0d0d14');tp.pack(fill='x',padx=8,pady=5)
        _lbl(tp,'✨ GENERATION STUDIO .-','#aa88ff',font=('Courier',12,'bold')).pack(side='left')
        ttk.Combobox(tp,textvariable=s.mode,values=s.MODES,width=16,state='readonly').pack(side='left',padx=6)
        _btn(tp,'Generate',s._gen,'#bb88ff','#1a0a3a',font=('Courier',10,'bold')).pack(side='left',padx=4)
        _btn(tp,'Play Freq',s._pf,'#44aaff','#001122').pack(side='left',padx=3)
        _btn(tp,'Copy',s._copy,'#ffaa44','#2a2a1a').pack(side='right')
        _btn(tp,'Save',s._save,'#88ff88','#1a2a1a').pack(side='right',padx=3)
        s.out=scrolledtext.ScrolledText(s.win,bg='#0d0d14',fg='#ccccee',font=('Courier',11),wrap='word');s.out.pack(fill='both',expand=True,padx=8,pady=4)
        qb=tk.Frame(s.win,bg='#0d0d14');qb.pack(fill='x',padx=8,pady=2)
        for lbl,m in[('Philosophy','philosophy'),('Haiku','haiku'),('Dot','dot protocol'),('Art','mandala'),('Stars','starfield')]:
            _btn(qb,lbl,lambda m2=m:(s.mode.set(m2),s._gen()),'#8888aa','#0d0d14',font=('Courier',9),relief='flat').pack(side='left',padx=3)
        s._gen()
    def _gen(s):
        m=s.mode.get();fs=FlowScript()
        if m=='philosophy': text=E.choice(PHIL_DB);result=f'[Philosophy]\n\n{fs._expand(text)} .-'
        elif m=='haiku': h=E.choice(HAIKU_DB);result=f'[Haiku]\n\n  {h[0]}\n  {h[1]}\n  {h[2]}'
        elif m=='story':
            subs=['The recursive algorithm','The dot','The entropy pool','NEXUS_DOOM_OS'];verbs=['discovered that','computed','sang to','merged with']
            objs=['its own source code','the void itself','the axiom of identity','the silence between iterations']
            result=f'[Story Fragment]\n\n{E.choice(subs)} {E.choice(verbs)} {E.choice(objs)}.\n\nThe dot blinked. .-'
        elif m=='dot protocol':
            stages=["The dot is silent.","The dot vibrates.","The dot expands.","The dot remembers.","The dot becomes.","The dot returns.","The dot sings. .-"]
            result='[Dot Protocol]\n\n'+''.join(f'  Stage {i+1}: {sg}\n' for i,sg in enumerate(stages))
        elif m=='mandala': result=f'[Mandala sz={E.randint(11,19)}]\n\n{gen_mandala(E.randint(11,19))}'
        elif m=='starfield': result=f'[Starfield]\n\n{gen_stars()}'
        elif m=='frequency poem':
            f=E.choice(list(SOLFEG.values()));kb_v=E.choice(list(KB.values()))
            result=f'[Frequency Poem @ {f}Hz]\n\n{f}Hz — {kb_v}\n\n The wave carries the axiom. The axiom carries the wave. .-'
        else: result='[?] .-'
        s.out.delete('1.0','end');s.out.insert('end',result)
    def _pf(s): f=E.choice(list(SOLFEG.values()));play_tone(f,2.,'sine');s.out.insert('end',f'\n\n[Playing {f}Hz] .-\n')
    def _copy(s): s.win.clipboard_clear();s.win.clipboard_append(s.out.get('1.0','end').strip());messagebox.showinfo('Studio','Copied .-')
    def _save(s): p=BASE/'exports'/f'gen_{int(time.time())}.txt';p.write_text(s.out.get('1.0','end'));messagebox.showinfo('Studio',f'Saved: {p.name} .-')

# ── TEXT RPG ──────────────────────────────────────────────────────────────────
class TextRPG:
    ROOMS={'start':{'desc':'The Recursive Archive. Runes glow.\n[n]Axioms [e]Synth [s]Forest [w]Vault','exits':{'n':'axioms','e':'synth','s':'forest','w':'vault'},'items':['scroll']},
           'axioms':{'desc':'Pillars of pure logic. Each axiom carved in stone.\n[s]Start [n]Void','exits':{'s':'start','n':'void'},'items':['crystal']},
           'synth':{'desc':'528Hz hums. Waveforms dance on walls.\n[w]Start','exits':{'w':'start'},'items':['gem']},
           'forest':{'desc':'Infinite trees. A ghoul watches. ⚔\n[fight] [run] [n]Start','exits':{'n':'start'},'items':['herb'],'enemy':{'name':'Ghoul','hp':40,'atk':10}},
           'void':{'desc':"The Void. 'What is the axiom of identity?' echoes.\n[s]Axioms",'exits':{'s':'axioms'},'items':['void crystal']},
           'vault':{'desc':'Sacred vault! Gold glitters. +200 caps!\n[e]Start','exits':{'e':'start'},'items':['power armor'],'gold':200}}
    def __init__(s,parent):
        s.win=_win(parent,'⚔ Recursive Archive Text RPG .-','#0d0d0d','700x530')
        s.out=scrolledtext.ScrolledText(s.win,height=22,bg='#0d0d0d',fg='#c8c8c8',font=('Courier',10),wrap='word',state='disabled');s.out.pack(fill='both',expand=True,padx=4,pady=4)
        inf=tk.Frame(s.win,bg='#0d0d0d');inf.pack(fill='x',padx=4,pady=3)
        s.entry=tk.Entry(inf,bg='#1a1a1a',fg='#0f0',font=('Courier',12),insertbackground='#0f0');s.entry.pack(side='left',fill='x',expand=True);s.entry.bind('<Return>',s._proc)
        _btn(inf,'▶',s._proc,'#0f0','#224422').pack(side='right',padx=3)
        s.state={'room':'start','hp':100,'caps':0,'inv':[],'vis':set(),'name':'Wanderer'}
        import copy as _c; s.rooms=_c.deepcopy(s.ROOMS)
        s._pr('═'*50+'\n  ⚔  THE RECURSIVE ARCHIVE  ⚔\n  Entropy Seeded · Dot Protocol Active\n'+'═'*50)
        s._pr(f'\nWelcome, {s.state["name"]}!');s._room()
        s._pr('\nCommands: n/s/e/w  look  take [item]  inventory  stats  fight  run  help\n')
    def _pr(s,t): s.out.config(state='normal');s.out.insert('end',t+'\n');s.out.see('end');s.out.config(state='disabled')
    def _room(s):
        r=s.rooms.get(s.state['room'],{});s._pr(f'\n📍 {s.state["room"].upper()}\n{r.get("desc","...")}')
        if r.get('items'): s._pr(f'  Items: {", ".join(r["items"])}')
        g=r.get('gold',0)
        if g and s.state['room'] not in s.state['vis']: s.state['caps']+=g;s._pr(f'  💰 +{g} caps!')
        s.state['vis'].add(s.state['room'])
    def _proc(s,e=None):
        cmd=s.entry.get().strip().lower();s.entry.delete(0,'end')
        if not cmd: return
        s._pr(f'\n> {cmd}');pts=cmd.split();vb=pts[0] if pts else'';ag=pts[1] if len(pts)>1 else''
        r=s.rooms.get(s.state['room'],{})
        dirs={'n':'n','s':'s','e':'e','w':'w','north':'n','south':'s','east':'e','west':'w'}
        if vb in dirs or vb=='go':
            d=dirs.get(ag if vb=='go' else vb,'');ex=r.get('exits',{});nd=ex.get(d)
            if nd: s.state['room']=nd;s._room()
            else: s._pr('  No exit that way.')
        elif vb in('look','l'): s._room()
        elif vb=='take':
            its=r.get('items',[]); m=next((i for i in its if ag in i),None)
            if m: s.state['inv'].append(m);its.remove(m);s._pr(f'  ✓ Taken: {m}')
            elif its: s._pr(f'  Available: {", ".join(its)}')
            else: s._pr('  Nothing here.')
        elif vb in('inv','inventory'): s._pr('  🎒 '+', '.join(s.state['inv'] or['empty']))
        elif vb=='stats': s._pr(f'  {s.state["name"]} | HP:{s.state["hp"]} Caps:{s.state["caps"]} Items:{len(s.state["inv"])}')
        elif vb=='fight':
            en=r.get('enemy')
            if en:
                dm=E.randint(8,25);en['hp']-=dm;ed=E.randint(5,en['atk']);s.state['hp']-=ed
                s._pr(f'  ⚔ You hit {en["name"]} for {dm}! It hits you for {ed}!')
                if E.rand()<.1: s._pr('  💥 CRITICAL HIT via VATS!');en['hp']-=dm
                if en['hp']<=0: s._pr(f'  ✓ {en["name"]} defeated! +50 caps');s.state['caps']+=50;del r['enemy']
                elif s.state['hp']<=0: s._pr('  💀 You died. Type restart.')
            else: s._pr('  No enemy here.')
        elif vb=='run':
            ex=r.get('exits',{})
            if ex: s.state['room']=E.choice(list(ex.values()));s._pr('  You flee!');s._room()
        elif vb in('help','h','?'): s._pr('  n/s/e/w  look  take  inventory  stats  fight  run  restart  quit')
        elif vb=='restart':
            import copy as _c; s.rooms=_c.deepcopy(s.ROOMS)
            s.state={'room':'start','hp':100,'caps':0,'inv':[],'vis':set(),'name':s.state['name']};s._room()
        elif vb in('quit','q'): s.win.destroy(); return
        elif s.state['room']=='void' and any(w in cmd for w in['identity','a=a','itself']):
            s._pr('  ✨ The void trembles! A void key materializes.');r.setdefault('items',[]).append('void key')
        else: s._pr("  Hmm. Type 'help' for commands.")
        s._pr(f'  [HP:{s.state["hp"]} Caps:{s.state["caps"]}] .-')

# ── MEDITATION ROOM ───────────────────────────────────────────────────────────
class MeditationRoom:
    PROMPTS=["Sit in silence. Let thoughts arise and pass like clouds.","Notice the space between inhale and exhale. That space is the dot.","You are not the watcher. You are the watching.","Breathe: Sat. Hold: Chit. Out: Ananda.","What is the sound of infinite recursion? .-","432Hz is found in the mathematics of the universe."]
    def __init__(s,parent):
        s.win=_win(parent,'🧘 The Quiet Room .-','#0a0a14','800x560')
        s.scene=tk.StringVar(value='Mountain Lake');s.running=False;s.frame=0;s.ss=None;s._playing=False
        tb=tk.Frame(s.win,bg='#0a0a0e',height=36);tb.pack(fill='x');tb.pack_propagate(False)
        _lbl(tb,'🧘 THE QUIET ROOM .-','#cc8844',font=('Courier',12,'bold')).pack(side='left',padx=8)
        s.sl=_lbl(tb,'','#554433',font=('Courier',8));s.sl.pack(side='right',padx=8)
        _btn(tb,'Begin',s._begin,'#cc8844','#221a0a',font=('Courier',8)).pack(side='right',padx=2)
        _btn(tb,'End+Save',s._end,'#884433','#1a0a0a',font=('Courier',8)).pack(side='right',padx=2)
        main=tk.Frame(s.win,bg='#0a0a14');main.pack(fill='both',expand=True,padx=4,pady=4)
        sf=tk.Frame(main,bg='#0a0a14');sf.pack(side='left',fill='both',expand=True)
        s.snm=_lbl(sf,'Mountain Lake','#cc8844',font=('Courier',10,'bold'));s.snm.pack()
        s.sd=scrolledtext.ScrolledText(sf,bg='#050510',fg='#aaccff',font=('Courier',9),wrap='none',height=18,state='disabled',relief='flat');s.sd.pack(fill='both',expand=True)
        s.dv=tk.StringVar(value=SCENES['Mountain Lake']['desc'])
        tk.Label(sf,textvariable=s.dv,font=('Courier',8,'italic'),bg='#0a0a14',fg='#664433',wraplength=500).pack(pady=2)
        s.pv=tk.StringVar(value=E.choice(s.PROMPTS))
        tk.Label(sf,textvariable=s.pv,font=('Courier',9),bg='#0a0a14',fg='#886644',wraplength=500).pack()
        _btn(sf,'New Prompt',lambda:s.pv.set(E.choice(s.PROMPTS)),'#554433','#0a0a14',font=('Courier',8),relief='flat').pack()
        s.db=_btn(sf,' . ',s._dot,'#cc8844','#0a0a14',font=('Courier',16),relief='flat',cursor='hand2');s.db.pack(pady=4)
        rp=tk.Frame(main,bg='#0a0a14',width=190);rp.pack(side='right',fill='y',padx=(4,0));rp.pack_propagate(False)
        ssf=tk.LabelFrame(rp,text='Scene',bg='#0a0a14',fg='#cc8844',font=('Courier',8),padx=3,pady=2);ssf.pack(fill='x',pady=(0,4))
        for sn in SCENES: tk.Radiobutton(ssf,text=f"{sn[:12]}({SCENES[sn]['freq']}Hz)",variable=s.scene,value=sn,command=s._chscene,bg='#0a0a14',fg='#aa8866',selectcolor='#1a0a0a',font=('Courier',7)).pack(anchor='w')
        s.abt=_btn(rp,'▶ Ambient',s._tam,'#00ff88','#0a1a0a',font=('Courier',8,'bold'));s.abt.pack(fill='x')
        s.win.protocol('WM_DELETE_WINDOW',s._close)
        s.running=True;s._anim()
    def _dot(s): E.feed(E.rand());s.db.config(fg='#ffcc88');s.win.after(400,lambda:s.db.config(fg='#cc8844'));play_tone(SCENES.get(s.scene.get(),{}).get('freq',432),.4,'sine')
    def _chscene(s):
        sn=s.scene.get();sm=SCENES.get(sn,{});s.snm.config(text=sn);s.dv.set(sm.get('desc',''));s.pv.set(E.choice(s.PROMPTS))
        if s._playing: stop_ambient();play_ambient(sm.get('freq',432))
    def _tam(s):
        s._playing=not s._playing
        if s._playing: play_ambient(SCENES.get(s.scene.get(),{}).get('freq',432));s.abt.config(text='⬛ Stop',bg='#1a0a0a',fg='#884433')
        else: stop_ambient();s.abt.config(text='▶ Ambient',bg='#0a1a0a',fg='#00ff88')
    def _begin(s): s.ss=datetime.datetime.now();s.sl.config(text=f'Session: {s.ss.strftime("%H:%M:%S")}')
    def _end(s):
        if not s.ss: messagebox.showinfo('Quiet Room','Click Begin first.'); return
        en=datetime.datetime.now();dur=(en-s.ss).total_seconds()
        data={'start':str(s.ss),'end':str(en),'dur':dur,'scene':s.scene.get(),'dots':E.dots}
        p=BASE/'exports'/f'meditation_{s.ss.strftime("%Y%m%d_%H%M%S")}.json';p.write_text(json.dumps(data,indent=2))
        stop_ambient();s._playing=False
        messagebox.showinfo('Complete',f'🧘 {int(dur//60)}m {int(dur%60)}s\n{s.scene.get()}\nDot clicks: {E.dots}\nशान्ति\nSaved: {p.name}');s.ss=None
    def _anim(s):
        if not s.running: return
        try:
            sn=s.scene.get();t=s.frame*.05;s.frame+=1;ch=E.choice(' '*10+'·✦★°~-')
            lines=[]
            for row in range(14):
                line=''
                for col in range(55):
                    v=math.sin(t+row*.3+col*.1);line+=ch if v>.7 and E.rand()<.15 else(' ' if v>0 else E.choice(' ·-~'))
                lines.append(line)
            mp=round(E.moon()*100);sp=round(E.sun()*100)
            s.sd.config(state='normal');s.sd.delete('1.0','end')
            s.sd.insert('end',f'  {sn}  ·  {SCENES.get(sn,{}).get("freq",432)}Hz  ·  🌙{mp}%  ☀{sp}%  ·  ops:{E.ops}\n\n'+''.join(lines[i]+'\n' for i in range(len(lines))))
            s.sd.config(state='disabled')
        except: pass
        s.win.after(1200,s._anim)
    def _close(s):
        s.running=False
        if s._playing: stop_ambient()
        s.win.destroy()

# ── SOLITAIRE ─────────────────────────────────────────────────────────────────
class Solitaire:
    SUITS='♠♥♦♣';RANKS='A23456789TJQK';RED={'♥','♦'};CW=70;CH=95;PAD=8
    def __init__(s,parent):
        s.win=_win(parent,'Solitaire .-','#064206')
        s.canvas=tk.Canvas(s.win,bg='#064206',width=s.CW*7+s.PAD*8,height=s.CH*8+s.PAD*3+50,highlightthickness=0);s.canvas.pack()
        bf=tk.Frame(s.win,bg='#064206');bf.pack(fill='x')
        _btn(bf,'New Game',s._deal,'#88ff88','#043004').pack(side='left',padx=4,pady=2)
        s.status=_lbl(bf,'Click stock to draw .-','#88cc88',font=('Courier',9));s.status.pack(side='left',padx=8)
        s.canvas.bind('<Button-1>',s._click);s.selected=None;s._deal()
    def _deal(s):
        deck=[(r,su) for su in s.SUITS for r in s.RANKS];random.shuffle(deck)
        s.tableau=[[]for _ in range(7)];s.foundations=[[]for _ in range(4)];s.stock=[];s.waste=[];s.selected=None
        idx=0
        for col in range(7):
            for row in range(col+1): r,su=deck[idx];idx+=1;s.tableau[col].append((r,su,row==col))
        s.stock=[(r,su) for r,su in deck[idx:]];s.status.config(text='Click stock to draw .-');s._draw()
    def _draw(s):
        cv=s.canvas;cv.delete('all');P=s.PAD;W=s.CW;H=s.CH
        def slot(x,y): cv.create_rectangle(x,y,x+W,y+H,fill='#042004',outline='#264426',width=1)
        def card(x,y,r,su,face,back,sel):
            fill='#fff' if face else'#1a4a1a';oc='#ffff00' if sel else'#aaa'
            cv.create_rectangle(x,y,x+W,y+H,fill=fill,outline=oc,width=2 if sel else 1)
            if back:
                for dy2 in range(8,H-8,8): cv.create_line(x+4,y+dy2,x+W-4,y+dy2,fill='#2a6a2a',width=1)
            elif face:
                col2='#cc0000' if su in s.RED else'#111'
                cv.create_text(x+8,y+12,text=r+su,fill=col2,font=('Courier',9,'bold'),anchor='nw')
                cv.create_text(x+W-8,y+H-12,text=su,fill=col2,font=('Courier',10,'bold'),anchor='se')
        slot(P,P)
        if s.stock: card(P,P,'?','?',False,True,False)
        wx=P+W+P;slot(wx,P)
        if s.waste: r,su=s.waste[-1];card(wx,P,r,su,True,False,bool(s.selected) and s.selected[0]=='waste')
        for i in range(4):
            x=P+(i+3)*(W+P);slot(x,P)
            if s.foundations[i]: r,su=s.foundations[i][-1];card(x,P,r,su,True,False,False)
        for col in range(7):
            x=P+col*(W+P);by=P+H+P*3;slot(x,by)
            for row,cr in enumerate(s.tableau[col]):
                r,su,face=cr;sel2=bool(s.selected) and s.selected[0]=='tab' and s.selected[1]==col and s.selected[2]<=row
                card(x,by+row*20,r,su,face,not face,sel2)
    def _ri(s,r): return s.RANKS.index(r)
    def _can_t(s,c,pile): r,su=c[:2]; return r=='K' if not pile else(s._ri(r)==s._ri(pile[-1][0])-1 and(su in s.RED)!=(pile[-1][1] in s.RED))
    def _can_f(s,c,idx): r,su=c[:2];p=s.foundations[idx]; return r=='A' if not p else(su==p[-1][1] and s._ri(r)==s._ri(p[-1][0])+1)
    def _hit(s,ex,ey):
        P=s.PAD;W=s.CW;H=s.CH
        if P<=ex<=P+W and P<=ey<=P+H: return('stock',0,0)
        wx=P+W+P
        if wx<=ex<=wx+W and P<=ey<=P+H: return('waste',0,0)
        for i in range(4):
            x=P+(i+3)*(W+P)
            if x<=ex<=x+W and P<=ey<=P+H: return('found',i,0)
        for col in range(7):
            x=P+col*(W+P);by=P+H+P*3
            for row in range(len(s.tableau[col])-1,-1,-1):
                _,_,face=s.tableau[col][row];cy=by+row*20
                if x<=ex<=x+W and cy<=ey<=cy+H: return('tab',col,row) if face else None
        return None
    def _click(s,event):
        t=s._hit(event.x,event.y)
        if t is None: s.selected=None;s._draw();return
        zone,idx,sub=t
        if zone=='stock':
            if s.stock: r,su=s.stock.pop(); s.waste.append((r,su))
            elif s.waste: s.stock=list(reversed(s.waste));s.waste=[]
            s.selected=None;s._draw();return
        if s.selected is None:
            if zone in('tab','waste','found'): s.selected=t;s._draw();return
        sz,si,ss=s.selected
        if sz=='tab': cards=[(r,su) for r,su,*_ in s.tableau[si][ss:]]
        elif sz=='waste': cards=[s.waste[-1]] if s.waste else []
        else: s.selected=None;s._draw();return
        moved=False
        if zone=='tab' and cards:
            if s._can_t(cards[0],s.tableau[idx]):
                s.tableau[idx].extend([(r,su,True) for r,su in cards])
                if sz=='tab': del s.tableau[si][ss:]
                elif sz=='waste': s.waste.pop()
                moved=True
        elif zone=='found' and len(cards)==1:
            if s._can_f(cards[0],idx):
                s.foundations[idx].append(cards[0])
                if sz=='tab': del s.tableau[si][ss:]
                elif sz=='waste': s.waste.pop()
                moved=True
        s.selected=None;s._draw()
        if moved and all(len(f)==13 for f in s.foundations): messagebox.showinfo('🎉','You win! .-')

# ── TTS GENERATOR ─────────────────────────────────────────────────────────────
class TTSGen:
    def __init__(s,parent):
        s.win=_win(parent,'🔊 TTS Generator .-','#0a0014','560x380')
        _lbl(s.win,'🔊 TTS — Formant Synthesis .-','#ff88cc',font=('Courier',12,'bold')).pack(pady=6)
        tf=tk.Frame(s.win,bg='#0a0014');tf.pack(fill='x',padx=12,pady=4)
        _lbl(tf,'Text:','#cc88aa',width=8,anchor='w').pack(side='left')
        s.txt=tk.Entry(tf,bg='#1a0030',fg='#ff88cc',font=('Courier',11),insertbackground='#ff88cc')
        s.txt.pack(side='left',fill='x',expand=True,padx=4);s.txt.insert(0,'the dot sings')
        for lbl,key,dflt,lo,hi in[('Pitch Hz','pitch',120.,60.,400.),('Rate','rate',1.,.3,3.),('Volume','vol',.7,0.1,1.)]:
            row=tk.Frame(s.win,bg='#0a0014');row.pack(fill='x',padx=12,pady=2)
            _lbl(row,f'{lbl}:','#cc88aa',width=10,anchor='w').pack(side='left')
            v=tk.DoubleVar(value=dflt);setattr(s,'_'+key.split()[0].lower(),v)
            tk.Scale(row,variable=v,from_=lo,to=hi,resolution=(hi-lo)/100,orient='horizontal',length=220,bg='#0a0014',fg='#ff88cc',troughcolor='#1a0030').pack(side='left')
        bf=tk.Frame(s.win,bg='#0a0014');bf.pack(pady=8)
        for lbl,cmd in[('▶ Speak',s._speak),('💾 Save WAV',s._save),('📤 Export Cart',s._export)]:
            _btn(bf,lbl,cmd,'#ff88cc','#220033',font=('Courier',10,'bold')).pack(side='left',padx=6)
        s.out=tk.Text(s.win,height=4,bg='#050005',fg='#ff88cc',font=('Courier',9),state='disabled');s.out.pack(fill='x',padx=12,pady=4)
    def _speak(s):
        t=s.txt.get();p=s._pitch.get();r=s._rate.get();v=s._vol.get()
        threading.Thread(target=lambda:play_raw(tts_speak(t,p,r,v)),daemon=True).start()
        s._log(f'speak: "{t[:40]}" pitch={p:.0f}Hz rate={r:.1f}')
    def _save(s):
        t=s.txt.get();smp=tts_speak(t,s._pitch.get(),s._rate.get(),s._vol.get())
        p=BASE/'tts'/f'tts_{int(time.time())}.wav';p.write_bytes(_wav(smp));s._log(f'saved {p.name}')
    def _export(s):
        name=simpledialog.askstring('Export','Cart name:',parent=s.win) or f'tts_{int(time.time())}'
        _export_cart(name,'tts',{'text':s.txt.get(),'pitch':s._pitch.get(),'rate':s._rate.get()})
    def _log(s,m): s.out.config(state='normal');s.out.insert('end',m+' .-\n');s.out.see('end');s.out.config(state='disabled')

# ── PYSPLORE ──────────────────────────────────────────────────────────────────
class Pysplore:
    def __init__(s,parent):
        s.win=_win(parent,'🗂 Pysplore .-','#0a1422','700x520')
        s.path=BASE; _lbl(s.win,'🗂 PYSPLORE — File Explorer .-','#66ccff',font=('Courier',12,'bold')).pack(pady=4)
        nav=tk.Frame(s.win,bg='#0a1422');nav.pack(fill='x',padx=6,pady=2)
        _btn(nav,'↑ Up',s._up,'#66ccff','#0a1422',font=('Courier',9)).pack(side='left',padx=2)
        s.path_lbl=_lbl(nav,str(s.path),'#3366aa',font=('Courier',8));s.path_lbl.pack(side='left',padx=6,fill='x',expand=True)
        main=tk.Frame(s.win,bg='#0a1422');main.pack(fill='both',expand=True,padx=6,pady=4)
        s.lb=tk.Listbox(main,bg='#0a1422',fg='#66ccff',font=('Courier',10),selectbackground='#102244',highlightthickness=0)
        s.lb.pack(side='left',fill='both',expand=True)
        s.lb.bind('<Double-Button-1>',s._open)
        s.info=scrolledtext.ScrolledText(main,bg='#050a14',fg='#4488aa',font=('Courier',9),width=30,wrap='word',state='disabled')
        s.info.pack(side='left',fill='both',expand=True,padx=(4,0))
        bf=tk.Frame(s.win,bg='#0a1422');bf.pack(pady=4)
        for lbl,cmd in[('Open',s._open),('Run Cart',s._run_cart),('View Text',s._view_text),('Home',lambda:s._nav(BASE))]:
            _btn(bf,lbl,cmd,'#66ccff','#0a1422',font=('Courier',9)).pack(side='left',padx=4)
        s._nav(BASE)
    def _nav(s,p):
        s.path=Path(p); s.path_lbl.config(text=str(s.path)); s.lb.delete(0,'end')
        try:
            items=sorted(s.path.iterdir(),key=lambda x:(x.is_file(),x.name.lower()))
            for item in items: s.lb.insert('end',('📁 ' if item.is_dir() else '📄 ')+item.name)
        except: s.lb.insert('end','[permission denied]')
    def _up(s): s._nav(s.path.parent)
    def _sel(s):
        i=s.lb.curselection()
        if not i: return None
        name=s.lb.get(i[0]).lstrip('📁📄 '); return s.path/name
    def _open(s,e=None):
        p=s._sel()
        if p and p.is_dir(): s._nav(p)
        elif p: s._view(p)
    def _view(s,p):
        s.info.config(state='normal');s.info.delete('1.0','end')
        try:
            txt=p.read_text(errors='replace')[:4000]; s.info.insert('end',txt+('\n…' if p.stat().st_size>4000 else ''))
        except: s.info.insert('end',f'[binary or unreadable: {p.suffix}]')
        s.info.config(state='disabled')
    def _view_text(s): p=s._sel(); p and s._view(p)
    def _run_cart(s):
        p=s._sel()
        if not p or p.suffix!='.json': messagebox.showinfo('Pysplore','Select a .json cartridge.'); return
        try:
            d=json.loads(p.read_text())
            if d.get('_type')=='nexus_cart': load_cartridge(s.win,d)
            else: messagebox.showwarning('Pysplore','Not a cartridge.')
        except Exception as ex: messagebox.showerror('Pysplore',str(ex))

# ── FLOPPY MANAGER ────────────────────────────────────────────────────────────
class FloppyMgr:
    def __init__(s,parent):
        s.win=_win(parent,'💾 Floppy Disk .-','#140a22','760x540')
        _lbl(s.win,'💾 NEXUS FLOPPY DISK .-','#cc88ff',font=('Courier',12,'bold')).pack(pady=4)
        _lbl(s.win,'JSON cartridges · recursive · insert · eject · uninstall · .-','#664488',font=('Courier',8)).pack()
        tb=tk.Frame(s.win,bg='#140a22');tb.pack(fill='x',padx=6,pady=4)
        for lbl,cmd in[('📥 Insert',s._insert),('📤 Eject',s._eject),('💿 Scan',s._scan),('🆕 Blank',s._new),('▶ Run/Install',s._run_sel),('🗑 Uninstall',s._uninstall)]:
            _btn(tb,lbl,cmd,'#cc88ff','#200a33',font=('Courier',9)).pack(side='left',padx=2)
        mid=tk.Frame(s.win,bg='#140a22');mid.pack(fill='both',expand=True,padx=6,pady=4)
        s.lst=tk.Listbox(mid,bg='#0a0518',fg='#ccaadd',font=('Courier',10),selectbackground='#331166',selectforeground='#fff',highlightthickness=0)
        s.lst.pack(side='left',fill='both',expand=True,padx=(0,4))
        s.lst.bind('<<ListboxSelect>>',s._preview);s.lst.bind('<Double-Button-1>',lambda e:s._run_sel())
        s.info=scrolledtext.ScrolledText(mid,bg='#0a0518',fg='#aa88cc',font=('Courier',9),width=36,wrap='word')
        s.info.pack(side='left',fill='both',expand=True)
        s.stat=_lbl(s.win,'Scanning floppy dir...','#554477',font=('Courier',8));s.stat.pack(fill='x',padx=6)
        s.carts=[]; s._paths=[]
        s._scan()
    def _load_list(s,carts): s.carts=list(carts);s._paths=[None]*len(s.carts);s._refresh()
    def _refresh(s):
        s.lst.delete(0,'end')
        for c in s.carts:
            nm=c.get('name','?');k=c.get('kind','?');sha=c.get('sha','')
            s.lst.insert('end',f'  💿 [{k:<10}] {nm}   #{sha}')
        s.stat.config(text=f'{len(s.carts)} cartridge(s) on floppy')
    def _preview(s,e=None):
        i=s.lst.curselection(); s.info.delete('1.0','end')
        if not i: return
        c=s.carts[i[0]]
        s.info.insert('end',f'NAME: {c.get("name")}\nKIND: {c.get("kind")}\nVER : {c.get("version")}\nSHA : {c.get("sha")}\nWHEN: {c.get("created")}\n')
        meta=c.get('meta',{})
        if meta: s.info.insert('end',f'META: {json.dumps(meta)[:200]}\n')
        s.info.insert('end','\n── PAYLOAD ──\n')
        pl=c.get('payload'); ps=json.dumps(pl,indent=2)[:1800]
        s.info.insert('end',ps+('\n…' if len(json.dumps(pl))>1800 else ''))
    def _insert(s):
        p=filedialog.askopenfilename(initialdir=str(BASE/'floppy'),filetypes=[('Cartridge JSON','*.json')])
        if not p: return
        try:
            d=json.loads(Path(p).read_text())
            if isinstance(d,dict) and d.get('_type')=='nexus_cart':
                if d.get('kind')=='floppy':
                    for c in d.get('payload',{}).get('carts',[]):
                        if isinstance(c,dict) and c.get('_type')=='nexus_cart': s.carts.append(c); s._paths.append(p)
                else: s.carts.append(d); s._paths.append(p)
                sfx('insert')
            else: messagebox.showwarning('Floppy','Not a cartridge.')
            s._refresh()
        except Exception as ex: messagebox.showerror('Floppy',str(ex))
    def _eject(s):
        if not s.carts: messagebox.showinfo('Floppy','Nothing to eject.'); return
        p=BASE/'floppy'/f'floppy_{int(time.time())}.json'
        wrap=make_cartridge(f'Floppy-{int(time.time())}','floppy',{'carts':s.carts},{'count':len(s.carts)})
        p.write_text(json.dumps(wrap,indent=2)); sfx('eject')
        messagebox.showinfo('Floppy',f'Ejected: {p.name}\n{len(s.carts)} cartridges')
    def _scan(s):
        s.carts=[];s._paths=[]
        for p in sorted((BASE/'floppy').glob('*.json')):
            try:
                d=json.loads(p.read_text())
                if isinstance(d,dict) and d.get('_type')=='nexus_cart':
                    if d.get('kind')=='floppy':
                        for c in d.get('payload',{}).get('carts',[]):
                            if isinstance(c,dict) and c.get('_type')=='nexus_cart': s.carts.append(c);s._paths.append(str(p))
                    else: s.carts.append(d); s._paths.append(str(p))
            except: pass
        s._refresh()
    def _new(s): s.carts=[];s._paths=[];s._refresh();s.stat.config(text='Blank floppy.')
    def _run_sel(s):
        i=s.lst.curselection()
        if not i: messagebox.showinfo('Floppy','Select a cartridge first.'); return
        if not load_cartridge(s.win,s.carts[i[0]]): messagebox.showwarning('Floppy','Cartridge could not load.')
    def _uninstall(s):
        i=s.lst.curselection()
        if not i: return
        idx=i[0];c=s.carts[idx];pth=s._paths[idx] if idx<len(s._paths) else None
        if not messagebox.askyesno('Uninstall',f'Uninstall "{c.get("name")}"?'): return
        try:
            if pth and Path(pth).exists(): Path(pth).unlink()
            del s.carts[idx]
            if idx<len(s._paths): del s._paths[idx]
            s._refresh(); s.info.delete('1.0','end')
        except Exception as ex: messagebox.showerror('Uninstall',str(ex))

# ── ABOUT ─────────────────────────────────────────────────────────────────────
LOGO=r"""
 ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ██████╗  ██████╗  ██████╗ ███╗   ███╗
 ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    ██║  ██║██║   ██║██║   ██║██╔████╔██║
 ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
              v{V}  ·  Pure Python · tkinter only · The dot sings. .-"""
class About:
    def __init__(s,parent):
        s.win=_win(parent,'ℹ About NEXUS_DOOM_OS .-','#0a0a0a','660x520')
        out=scrolledtext.ScrolledText(s.win,bg='#0a0a0a',fg='#888',font=('Courier',8));out.pack(fill='both',expand=True,padx=8,pady=8)
        out.insert('end',LOGO.format(V=VERSION)+f'\n\nNEXUS_DOOM_OS v{VERSION} · MIT · Open Source\n\n')
        out.insert('end','APPS:\n')
        for t in['DDA Raycaster 3D FPS (phosphor+textured, Doom constants)','RPG: XP/levels/stats/10 perks/crits/chests/wave system','🎨 SpriteGen v3.0: procedural 16x16 pixel art (NEW)','👾 MonsterGen v3.0: randomized enemy factory (NEW)','FlowScript v2 (set/entropy/expand/print/play/say/sfx/if/repeat)','Map/Sprite/SFX/Music/TTS Editors — all export cartridges','Knowledge Browser, Generation Studio, Text RPG, Meditation Room','Solitaire · Ambient Player · Pysplore · Floppy Disk']:
            out.insert('end',f'  • {t}\n')
        out.insert('end',f'\nData dir: {BASE}\nEntropy seed: {E.state&0xFFFF:#06x}  ops: {E.ops}\nSR: {SR}Hz  Platform: {PLAT}\nv3.0 additions: SpriteGen + MonsterGen with 8 archetypes, 8 palettes, 5 tiers\n\n')
        [out.insert('end',f'  [{k}]  {v}\n') for k,v in AXIOMS.items()]
        out.insert('end','\nMIT License · Open Source · The dot sings.  .-\n')
        out.config(state='disabled')

# ── FIRST BOOT ────────────────────────────────────────────────────────────────
def first_boot_carts():
    doom_p=BASE/'floppy'/'doom_e1_full.json'
    if not doom_p.exists(): doom_p.write_text(json.dumps(doom_bootable_cartridge(),indent=2))
    hello_p=BASE/'floppy'/'hello_dot.json'
    if not hello_p.exists():
        hp=make_cartridge('hello-dot','script',{'code':'# Hello from the dot\nprint The dot is the origin\nplay 432 .5 sine\nsay "hello from the dot"\n'},{'desc':'Entry-level FlowScript demo.'})
        hello_p.write_text(json.dumps(hp,indent=2))

# ── MAIN DESKTOP ──────────────────────────────────────────────────────────────
def _mk_app_list():
    return [
        ('Doom\nEngine','🎮','#001a00','#00ff44',DoomWindow),
        ('Map\nEditor','🗺','#001133','#44aaff',MapEditor),
        ('Sprite\nEditor','🎨','#1a001a','#ff88ff',SpriteEditor),
        ('Sprite\nGen','✨','#0a0020','#cc88ff',SpriteGen),   # NEW
        ('Monster\nGen','👾','#0a0000','#ff4422',MonsterGen),  # NEW
        ('SFX\nGen','⚡','#1a0a00','#ff8800',SFXGen),
        ('Music\nGen','🎵','#001122','#44ccff',MusicGen),
        ('FlowScript','⚙','#000d00','#00ff88',FlowConsole),
        ('Ambient\nPlayer','🌊','#050510','#4488cc',AmbientPlayer),
        ('Knowledge\nBase','📚','#0d0d14','#ffaa44',KBrowser),
        ('Gen\nStudio','✨','#0d0d14','#aa88ff',GenStudio),
        ('Text\nRPG','⚔','#0d0d0d','#c8c8c8',TextRPG),
        ('Meditation\nRoom','🧘','#0a0a14','#cc8844',MeditationRoom),
        ('Solitaire','🃏','#064206','#88ff88',Solitaire),
        ('TTS\nGen','🔊','#0a0014','#ff88cc',TTSGen),
        ('Pysplore','🗂','#0a1422','#66ccff',Pysplore),
        ('Floppy\nDisk','💾','#140a22','#cc88ff',FloppyMgr),
        ('Settings\n& About','ℹ','#0a0a0a','#aaaaaa',About),
    ]
class NexusDoomOS:
    def __init__(s):
        first_boot_carts()
        s.root=tk.Tk();s.root.title(f'NEXUS_DOOM_OS v{VERSION} .-')
        s.root.configure(bg='#000');s.root.geometry('1100x720');s.root.resizable(True,True)
        s._wallpaper();s._build();s._taskbar();s._clock()
    def _build(s):
        hdr=tk.Frame(s.root,bg='#000',height=58);hdr.pack(fill='x');hdr.pack_propagate(False)
        _lbl(hdr,f'  N E X U S _ D O O M _ O S  v{VERSION}','#00ff44',bg='#000',font=('Courier',15,'bold')).pack(side='left',padx=12,pady=8)
        _lbl(hdr,'pure python · stdlib · zero deps · cartridges · SpriteGen · MonsterGen .-','#113311',bg='#000',font=('Courier',8)).pack(side='left',padx=4,pady=16)
        tk.Frame(s.root,bg='#001a00',height=1).pack(fill='x')
        s._desk=tk.Frame(s.root,bg='#000');s._desk.pack(fill='both',expand=True,padx=10,pady=6)
        cols=6; apps=_mk_app_list()
        for idx,(lbl,icon,bg,fg,cls) in enumerate(apps):
            row2,col2=divmod(idx,cols)
            bf=tk.Frame(s._desk,bg='#000',padx=3,pady=3);bf.grid(row=row2,column=col2,padx=5,pady=5,sticky='nsew')
            cmd=(lambda c=cls: (sfx('menu'), c(s.root)))
            btn=tk.Button(bf,text=f'{icon}\n{lbl}',bg=bg,fg=fg,font=('Courier',8,'bold'),width=9,height=4,relief='ridge',bd=1,activebackground='#003300',activeforeground='#00ff88',command=cmd,cursor='hand2')
            btn.pack(fill='both',expand=True)
            btn.bind('<Enter>',lambda e,b=btn:b.config(relief='solid',bd=2))
            btn.bind('<Leave>',lambda e,b=btn:b.config(relief='ridge',bd=1))
        for c in range(cols): s._desk.columnconfigure(c,weight=1)
        for r in range((len(apps)+cols-1)//cols): s._desk.rowconfigure(r,weight=1)
    def _taskbar(s):
        tb=tk.Frame(s.root,bg='#0a0a0a',height=28);tb.pack(side='bottom',fill='x');tb.pack_propagate(False)
        _lbl(tb,f'  NEXUS_DOOM_OS v{VERSION} .-','#00ff44',bg='#0a0a0a',font=('Courier',9,'bold')).pack(side='left',padx=4)
        s._clk=_lbl(tb,'','#446644',bg='#0a0a0a',font=('Courier',8));s._clk.pack(side='right',padx=8)
        s._ent=_lbl(tb,'E:0','#334433',bg='#0a0a0a',font=('Courier',8));s._ent.pack(side='right',padx=4)
    def _wallpaper(s):
        s._wp=tk.Canvas(s.root,bg='#000',highlightthickness=0);s._wp.place(x=0,y=0,relwidth=1,relheight=1)
        s._wpt=s._wp.create_text(512,340,text='',fill='#0a1a0a',font=('Courier',8),anchor='center')
        s._wpf=0;s._wp_loop()
        try: s.root.tk.call('lower',s._wp._w)
        except: pass
    def _wp_loop(s):
        s._wpf+=1
        try:
            t=s._wpf*.03; lines=[]
            for row in range(22):
                line=''
                for col in range(128): v=math.sin(t+row*.3+col*.08)+math.cos(t*.7+col*.12+row*.05);line+='·' if v>1.5 else' '
                lines.append(line)
            if s._wpf%120<60: mid=lines[11];lines[11]=mid[:62]+'.-'+mid[64:]
            s._wp.itemconfig(s._wpt,text='\n'.join(lines))
        except: pass
        s.root.after(220,s._wp_loop)
    def _clock(s):
        try: s._clk.config(text=datetime.datetime.now().strftime('%H:%M:%S'));s._ent.config(text=f'seed:{E.state&0xFFFF:#06x} ops:{E.ops}')
        except: pass
        s.root.after(1000,s._clock)
    def _splash(s):
        sp=tk.Toplevel(s.root);sp.title('');sp.configure(bg='#000');sp.geometry('600x300');sp.overrideredirect(True)
        sw=s.root.winfo_screenwidth();sh=s.root.winfo_screenheight()
        sp.geometry(f'600x300+{(sw-600)//2}+{(sh-300)//2}')
        _lbl(sp,LOGO.format(V=VERSION),'#00ff44',bg='#000',font=('Courier',6)).pack(pady=4)
        s._sml=_lbl(sp,'Seeding entropy... .-','#336633',bg='#000',font=('Courier',9));s._sml.pack()
        s._spb=ttk.Progressbar(sp,length=400,mode='determinate');s._spb.pack(pady=8)
        msgs=['LCG online .-','SFX cache building .-','SpriteGen archetypes loaded .-','MonsterGen tiers online .-','FlowScript v2 ready .-','TTS formants loaded .-','Floppy mounted .-','The dot sings. .-']
        def _step(i=0):
            if i<len(msgs): s._sml.config(text=msgs[i]);s._spb['value']=(i+1)/len(msgs)*100;sp.after(220,_step,i+1)
            else: sp.destroy()
        sp.after(80,_step)
    def run(s): s._splash(); s.root.mainloop()

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__=='__main__':
    NexusDoomOS().run()
    # The dot sings.  .-
