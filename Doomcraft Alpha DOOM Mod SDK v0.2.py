#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Emacs style mode select   -*- Python -*-
# =============================================================================
#
# $Id: doomcraft.py,v 1.0 2026 DoomCraft Mod SDK $
#
# Copyright (C) 2026  DoomCraft SDK — built on the spirit of id Software
#
# DOOMCRAFT.PY — DOOM Mod SDK
# A limitless, recursive game creation tool.
# FlowScript · LCG Entropy · Recursive Dot Protocol · Self-Referential Optimization
#
# "The dot sings.  .-"
#
# =============================================================================
#
# ██████╗  ██████╗  ██████╗ ███╗   ███╗ ██████╗██████╗  █████╗ ███████╗████████╗
# ██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝
# ██║  ██║██║   ██║██║   ██║██╔████╔██║██║     ██████╔╝███████║█████╗     ██║
# ██║  ██║██║   ██║██║   ██║██║╚██╔╝██║██║     ██╔══██╗██╔══██║██╔══╝     ██║
# ██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║╚██████╗██║  ██║██║  ██║██║        ██║
# ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝
#
#   MOD SDK v1.0  ·  DOOM · ZOMBIES · FLOWSCRIPT · RAYCASTER · PURE PYTHON
#   "Rip and tear until it is done."
#
# =============================================================================

import sys, os, math, time, random, struct, wave, io, json, hashlib
import threading, subprocess, tempfile, platform, base64, traceback
from collections import deque

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
except ImportError:
    print("Needs tkinter.  Linux: sudo apt-get install python3-tk"); sys.exit(1)

TAU   = math.tau
_RNG  = random.Random()
_PLAT = platform.system()

# =============================================================================
# §0  AUTO-INSTALLER  (only triggered on Play Mode launch)
# =============================================================================
def auto_install_deps():
    """Attempt to pip-install pygame and pyttsx3 with multiple fallback strategies."""
    missing = []
    try: import pygame
    except ImportError: missing.append('pygame')
    try: import pyttsx3
    except ImportError: missing.append('pyttsx3')
    if not missing:
        return True
    print(f"[DoomCraft] Installing: {', '.join(missing)} ...")
    for pkg in missing:
        for flags in [[], ['--user'], ['--break-system-packages'], ['--user','--break-system-packages']]:
            try:
                cmd = [sys.executable, '-m', 'pip', 'install', pkg] + flags
                r = subprocess.run(cmd, capture_output=True, timeout=60)
                if r.returncode == 0:
                    print(f"[DoomCraft] Installed {pkg} OK")
                    break
            except Exception:
                continue
    # Re-check
    ok = True
    try: import pygame
    except ImportError: ok = False; print("[DoomCraft] WARNING: pygame install failed – Play Mode limited")
    try: import pyttsx3
    except ImportError: print("[DoomCraft] WARNING: pyttsx3 not available – TTS disabled")
    return ok

# =============================================================================
# §1  GLOBAL TUNABLE DICTIONARIES  (edit freely!)
# =============================================================================

# --- WEAPON STATS ---  name, dmg_min, dmg_max, pellets, fire_delay, ammo_cost, ammo_type, sfx
WEAPONS = {
    0: ('FIST',     2, 20,  1, 0.48, 0, None,      'hit'),
    1: ('PISTOL',   5, 15,  1, 0.28, 1, 'bullets',  'shoot'),
    2: ('SHOTGUN',  5, 15,  7, 0.70, 1, 'shells',   'shotgun'),
    3: ('CHAINGUN', 4, 12,  1, 0.09, 1, 'bullets',  'chaingun'),
    4: ('ROCKETL', 20, 50,  1, 0.90, 1, 'rockets',  'rocket'),
}

# --- WALL WEAPON PURCHASE COSTS (points) ---
WALL_WEAPONS = {
    1: ('PISTOL',    500),
    2: ('SHOTGUN',  1500),
    3: ('CHAINGUN', 2000),
    4: ('ROCKETL',  3000),
}

# --- PERK-A-COLA DEFINITIONS ---  name, cost, description
PERKS_COLA = {
    'JUGGERNOG':  ('JUGGERNOG',  2500, 'Max HP x2'),
    'SPEEDCOLA':  ('SPEED COLA', 3000, 'Reload 2x faster'),
    'DOUBLETAP':  ('DOUBLE TAP', 2000, 'Fire rate x1.5'),
    'STAMINUP':   ('STAMIN-UP',  2000, 'Move 30% faster'),
    'MULEKICK':   ('MULE KICK',  4000, 'Carry 3rd weapon'),
}

# --- ENEMY STATS ---  name, base_hp, speed, dps, points, rgb, scale
ENEMY_DEFS = {
    'Z': ('ZOMBIE',    50,  0.011,  5.0,  100, (190,165,140), 0.85),
    'I': ('IMP',      100,  0.014,  9.0,  200, (168, 80, 38), 1.00),
    'N': ('DEMON',    250,  0.017, 19.0,  400, (210,100,165), 1.20),
    'B': ('BOSS',    1500,  0.020, 35.0, 2000, (255, 40,  40), 1.80),
}

# --- WAVE CONFIG ---  enemies per wave = base + round * scale
WAVE_CONFIG = {
    'base_enemies':  6,
    'scale_per_round': 2,
    'health_scale':   1.15,  # enemy HP multiplied each round
    'max_enemies_alive': 24,
    'boss_every_n_rounds': 5,
}

# --- PLAYER BASE STATS ---
PLAYER_BASE = {
    'hp': 100, 'max_hp': 100, 'armor': 0,
    'bullets': 120, 'shells': 16, 'rockets': 4,
    'move_speed': 0.090, 'strafe_speed': 0.072, 'turn_speed': 0.058,
    'points': 500,
}

# --- MYSTERY BOX ---  weapon_id : weight
MYSTERY_BOX_POOL = {2: 40, 3: 30, 4: 20, 1: 10}

# --- PACK-A-PUNCH COST ---
PACK_A_PUNCH_COST = 5000

# --- ELECTRIC TRAP COST ---
TRAP_COST = 1000
TRAP_DAMAGE = 150
TRAP_COOLDOWN = 5.0

# --- SKILL LEVELS ---
SKILL_LEVELS = {
    0: ('EASY',    0.60, 0.70),   # name, enemy_hp_mult, enemy_dmg_mult
    1: ('NORMAL',  1.00, 1.00),
    2: ('HARD',    1.35, 1.25),
    3: ('ULTRA',   1.80, 1.60),
}

# --- VEHICLE STATS ---
VEHICLE_DEFS = {
    'CAR':   {'speed': 0.22, 'turn': 0.05, 'color': '#cc8800', 'width': 1.2, 'height': 0.7},
    'TANK':  {'speed': 0.11, 'turn': 0.03, 'color': '#448844', 'width': 1.6, 'height': 1.1},
    'BIKE':  {'speed': 0.30, 'turn': 0.07, 'color': '#cc3300', 'width': 0.7, 'height': 0.4},
}

# =============================================================================
# §2  LCG ENTROPY ENGINE  (deterministic, seed-driven)
# =============================================================================
class LCG:
    """Linear Congruential Generator — Doom-style deterministic entropy. .-"""
    A = 1664525; C = 1013904223; M = 2**32

    def __init__(self, seed=12345):
        self.state = seed & 0xFFFFFFFF

    def next(self):
        self.state = (self.A * self.state + self.C) % self.M
        return self.state

    def rand(self):
        return self.next() / self.M

    def randint(self, lo, hi):
        return lo + int(self.rand() * (hi - lo + 1))

    def choice(self, seq):
        return seq[self.randint(0, len(seq)-1)]

    def seed_from_hash(self, hex_str):
        """Feed a SHA-256 hex string into the entropy state."""
        val = int(hex_str[:8], 16)
        self.state = val & 0xFFFFFFFF

_ENTROPY = LCG(42)

# =============================================================================
# §3  FLOWSCRIPT INTERPRETER  (6 commands: set, entropy, expand, freq, print, repeat)
# =============================================================================
class FlowScript:
    """
    FlowScript v1.0 — embedded scripting engine.
    Commands:
      set    <var> <value>         — assign a variable
      entropy <var> <lo> <hi>      — assign random int in [lo,hi] to var
      expand  <var> <factor>       — multiply var by factor
      freq    <hz>                 — emit a tone at given frequency
      print   <message...>        — print tokens (vars are substituted)
      repeat  <n> { <block> }     — repeat block n times
    All output lines end with " .-"
    """
    def __init__(self, env=None, tone_fn=None):
        self.env = env or {}
        self.tone_fn = tone_fn  # callable(hz) → play tone
        self.output = []

    def _sub(self, token):
        if token in self.env:
            return str(self.env[token])
        return token

    def run(self, code):
        """Execute FlowScript code string. Returns list of output lines."""
        self.output = []
        lines = [l.strip() for l in code.strip().splitlines() if l.strip() and not l.strip().startswith('//')]
        self._exec_block(lines, 0, len(lines))
        return self.output

    def _exec_block(self, lines, start, end):
        i = start
        while i < end:
            line = lines[i]
            if not line or line == '}':
                i += 1; continue
            parts = line.split()
            cmd = parts[0].lower()

            if cmd == 'set':
                if len(parts) >= 3:
                    try: self.env[parts[1]] = float(parts[2]) if '.' in parts[2] else int(parts[2])
                    except ValueError: self.env[parts[1]] = parts[2]
                i += 1

            elif cmd == 'entropy':
                if len(parts) >= 4:
                    try:
                        lo, hi = int(parts[2]), int(parts[3])
                        self.env[parts[1]] = _ENTROPY.randint(lo, hi)
                    except ValueError: pass
                i += 1

            elif cmd == 'expand':
                if len(parts) >= 3:
                    try:
                        factor = float(parts[2])
                        if parts[1] in self.env:
                            self.env[parts[1]] = self.env[parts[1]] * factor
                    except ValueError: pass
                i += 1

            elif cmd == 'freq':
                if len(parts) >= 2:
                    try:
                        hz = float(self._sub(parts[1]))
                        if self.tone_fn:
                            self.tone_fn(hz)
                    except ValueError: pass
                i += 1

            elif cmd == 'print':
                msg = ' '.join(self._sub(t) for t in parts[1:])
                self.output.append(msg + ' .-')
                i += 1

            elif cmd == 'repeat':
                # repeat N { ... }
                try:
                    n = int(self._sub(parts[1]))
                except (ValueError, IndexError):
                    n = 0
                # find matching '{'
                j = i + 1
                while j < end and lines[j].strip() != '{':
                    j += 1
                block_start = j + 1
                # find matching '}'
                depth = 1; k = block_start
                while k < end and depth > 0:
                    if lines[k].strip() == '{': depth += 1
                    elif lines[k].strip() == '}': depth -= 1
                    k += 1
                block_end = k - 1
                for _ in range(n):
                    self._exec_block(lines, block_start, block_end)
                i = k

            else:
                i += 1

    def eval_expr(self, expr):
        """Quick single-expression evaluator for console use."""
        parts = expr.strip().split()
        if len(parts) >= 3:
            result = self.run('\n'.join([expr]))
            return result
        return self.run(f'print {expr}')

# =============================================================================
# §4  AUDIO ENGINE  (pure Python struct/wave + system player)
# =============================================================================
SR = 22050

def _wav(samps):
    pk = struct.pack(f'<{len(samps)}h',
        *(max(-32767, min(32767, int(s * 32767))) for s in samps))
    b = io.BytesIO()
    with wave.open(b, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pk)
    return b.getvalue()

def _play_wav(data, path=None):
    p = path or os.path.join(tempfile.gettempdir(), f'_dc_{threading.get_ident()}.wav')
    try:
        with open(p, 'wb') as f: f.write(data)
        if _PLAT == 'Windows':
            import winsound
            winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        elif _PLAT == 'Darwin':
            subprocess.Popen(['afplay', p], stderr=subprocess.DEVNULL)
        else:
            for cmd in [['aplay', '-q'], ['paplay'], ['play', '-q']]:
                try: subprocess.Popen(cmd + [p], stderr=subprocess.DEVNULL); return
                except FileNotFoundError: continue
    except Exception: pass

def sfx(name):
    d = _SFX_CACHE.get(name)
    if d: threading.Thread(target=_play_wav, args=(d,), daemon=True).start()

def play_tone(hz, dur=0.15, vol=0.3):
    """FlowScript freq command — synthesize and play a sine tone."""
    n = int(SR * dur)
    fade = int(SR * 0.02)
    s = [vol * math.sin(TAU * hz * i / SR) for i in range(n)]
    for i in range(min(fade, n)): s[i] *= i / fade; s[n-1-i] *= i / fade
    threading.Thread(target=_play_wav, args=(_wav(s),), daemon=True).start()

def _build_sfx_cache():
    g = _RNG.gauss
    def shoot():    n=int(SR*.14); return [g(0,.55)*math.exp(-i/n*8)+.3*math.sin(TAU*165*i/SR)*math.exp(-i/n*18) for i in range(n)]
    def shotgun():  n=int(SR*.22); return [g(0,.7)*math.exp(-i/n*5)+.4*math.sin(TAU*100*i/SR)*math.exp(-i/n*10) for i in range(n)]
    def chaingun(): n=int(SR*.08); return [g(0,.42)*math.exp(-i/n*13)+.22*math.sin(TAU*220*i/SR)*math.exp(-i/n*20) for i in range(n)]
    def rocket():   n=int(SR*.35); return [(g(0,.5)+.5*math.sin(TAU*80*i/SR))*math.exp(-i/n*2.5) for i in range(n)]
    def hit():      n=int(SR*.10); return [g(0,.38)*math.exp(-i/n*11) for i in range(n)]
    def death():    n=int(SR*.45); return [(g(0,.32)+.4*math.sin(TAU*72*i/SR))*math.exp(-i/n*3.2) for i in range(n)]
    def pickup():   n=int(SR*.16); return [.55*math.sin(TAU*(440+320*i/n)*i/SR)*math.exp(-i/n*2.8) for i in range(n)]
    def door():     n=int(SR*.30); return [.35*(math.sin(TAU*(48+90*i/n)*i/SR)+g(0,.08)) for i in range(n)]
    def pain():     n=int(SR*.12); return [g(0,.55)*math.exp(-i/n*8) for i in range(n)]
    def beep():     n=int(SR*.07); return [.4*math.sin(TAU*660*i/SR)*math.exp(-i/n*7) for i in range(n)]
    def buy():      n=int(SR*.20); return [.5*(math.sin(TAU*523*i/SR)+.4*math.sin(TAU*784*i/SR))*math.exp(-i/n*.6) for i in range(n)]
    def powerup():  n=int(SR*.50); return [.6*math.sin(TAU*(330+880*i/n)*i/SR)*math.exp(-i/n*.4) for i in range(n)]
    def trap_zap(): n=int(SR*.18); return [g(0,.7)*math.exp(-i/n*6)+.3*math.sin(TAU*440*i/SR)*math.exp(-i/n*12) for i in range(n)]
    def box_spin(): n=int(SR*.40); return [.4*(math.sin(TAU*(200+300*i/n)*i/SR)) for i in range(n)]
    def round_end():n=int(SR*.80); return [.6*math.sin(TAU*(220+440*i/n)*i/SR)*math.exp(-i/n*.3) for i in range(n)]
    return {k:_wav(v()) for k,v in {
        'shoot':shoot,'shotgun':shotgun,'chaingun':chaingun,'rocket':rocket,
        'hit':hit,'death':death,'pickup':pickup,'door':door,'pain':pain,
        'menu':beep,'buy':buy,'powerup':powerup,'trap':trap_zap,
        'box':box_spin,'roundend':round_end,
    }.items()}

_SFX_CACHE: dict = {}
threading.Thread(target=lambda: _SFX_CACHE.update(_build_sfx_cache()), daemon=True).start()

# Generative ambient drone — evolves each wave via FREEFLOW OMEGA logic
_AMB_STOP = threading.Event()

def _make_drone(base_freq, wave_seed=0, dur=4.0, vol=0.07):
    """Recursive FREEFLOW OMEGA: wave_seed XORs into harmonic ratios."""
    n = int(SR * dur); fade = int(SR * 0.5)
    h1 = 1.0 + (wave_seed & 0xF) / 40.0
    h2 = 1.5 + ((wave_seed >> 4) & 0xF) / 30.0
    s = [vol * (math.sin(TAU*base_freq*i/SR)
               + 0.4*math.sin(TAU*base_freq*h1*i/SR)
               + 0.2*math.sin(TAU*base_freq*h2*i/SR)) for i in range(n)]
    for i in range(min(fade, n//2)): s[i] *= i/fade; s[n-1-i] *= i/fade
    return _wav(s)

def play_ambient(freq=55, wave_seed=0):
    global _AMB_STOP
    _AMB_STOP.set(); time.sleep(0.04); _AMB_STOP = threading.Event()
    ev = _AMB_STOP
    p = os.path.join(tempfile.gettempdir(), '_dc_amb.wav')
    def _loop():
        while not ev.is_set():
            d = _make_drone(freq, wave_seed)
            _play_wav(d, p); time.sleep(3.7)
    threading.Thread(target=_loop, daemon=True).start()

def stop_ambient(): _AMB_STOP.set()

# =============================================================================
# §5  TTS ENGINE  (pyttsx3 if available, else silent)
# =============================================================================
_TTS_ENGINE = None
_TTS_LOCK = threading.Lock()

def init_tts():
    global _TTS_ENGINE
    try:
        import pyttsx3
        _TTS_ENGINE = pyttsx3.init()
        _TTS_ENGINE.setProperty('rate', 165)
    except Exception: _TTS_ENGINE = None

def speak(text):
    if not _TTS_ENGINE: return
    def _do():
        with _TTS_LOCK:
            try: _TTS_ENGINE.say(text); _TTS_ENGINE.runAndWait()
            except Exception: pass
    threading.Thread(target=_do, daemon=True).start()

# =============================================================================
# §6  CARTRIDGE SYSTEM  (JSON map + SHA-256 seed signature)
# =============================================================================
DEFAULT_CARTRIDGE = {
    'name': 'Untitled Map',
    'width': 20, 'height': 15,
    'grid': {},        # "x,y": tile_type
    'entities': [],    # [{type, x, y, rotation, props}]
    'settings': {
        'wave_base': WAVE_CONFIG['base_enemies'],
        'wave_scale': WAVE_CONFIG['scale_per_round'],
        'health_scale': WAVE_CONFIG['health_scale'],
        'player_hp': PLAYER_BASE['hp'],
        'skill': 1,
        'power_active': False,
    },
    'wall_weapons': {},   # "x,y": weapon_id
    'perks': {},          # "x,y": perk_name
    'sprites': {},        # name: base64_png_16x16
    'dialogue': {},       # entity_id: [line1, line2, ...]
    'seed_signature': '',
}

def cartridge_hash(cart):
    data = json.dumps(cart, sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()

def load_cartridge(path):
    with open(path, 'r') as f:
        cart = json.load(f)
    cart['seed_signature'] = cartridge_hash(cart)
    return cart

def save_cartridge(cart, path):
    cart['seed_signature'] = cartridge_hash(cart)
    with open(path, 'w') as f:
        json.dump(cart, f, indent=2)

# =============================================================================
# §7  SPECTRAL SIGNATURE  (recursive difficulty evolution)
# =============================================================================
def compute_spectral_signature(shots, hits, damage_taken, points_earned, wave):
    """
    Compute a 32-bit integer from gameplay metrics.
    This XORs with the cartridge seed to produce the next wave's LCG seed.
    """
    acc = int((hits / max(shots, 1)) * 255) & 0xFF
    dmg_byte = min(damage_taken, 255) & 0xFF
    pts_byte = min(points_earned // 10, 255) & 0xFF
    wave_byte = (wave * 37) & 0xFF
    sig = (wave_byte << 24) | (dmg_byte << 16) | (acc << 8) | pts_byte
    return sig

def evolve_wave_params(cart_seed_hex, spectral_sig, wave_num):
    """XOR cartridge seed + spectral signature → next wave LCG params."""
    seed_int = int(cart_seed_hex[:8], 16) if cart_seed_hex else 0
    combined = seed_int ^ spectral_sig ^ (wave_num * 0xDEAD)
    _ENTROPY.state = combined & 0xFFFFFFFF
    # Enemy spawn delays vary with entropy
    delay_spread = 0.3 + _ENTROPY.rand() * 0.7
    hp_bonus = 1.0 + _ENTROPY.rand() * 0.3 * (wave_num / 5.0)
    return {'delay_spread': delay_spread, 'hp_bonus': hp_bonus}

# =============================================================================
# §8  RAYCASTING ENGINE  (DDA, tkinter canvas, phosphor skin option)
# =============================================================================
FOV       = math.pi / 2.8
MAX_DEPTH = 24
COLS      = 160
VIEW_W    = 800
VIEW_H    = 480
HUD_H     = 56
COL_W     = VIEW_W // COLS
WALL_BANDS= 8
MAX_SPR   = 40
SIDE_DIM  = 0.55

_TN = 64

def _gen_brick():
    o=[]
    for yi in range(_TN):
        ty=yi/_TN
        for xi in range(_TN):
            tx=xi/_TN; hy=ty%0.25
            if hy<0.038 or hy>0.212: o.append(0.22); continue
            row=int(ty*4); hx=(tx+(0.5 if row%2 else 0.0))%0.5
            if hx<0.038: o.append(0.22); continue
            bx=int((tx+(0.5 if row%2 else 0))*2); by=int(ty*4)
            o.append(0.60+0.28*(((bx*37+by*19+bx^by)%9)/8.0))
    return o

def _gen_metal():
    o=[]
    for yi in range(_TN):
        ty=yi/_TN
        for xi in range(_TN):
            tx=xi/_TN; px=tx%0.25; py=ty%0.5
            if (px<0.025 or px>0.225) and (py<0.05 or py>0.45): o.append(0.28)
            else: o.append(0.48+0.30*((int(tx*4)*11)%7/6.0))
    return o

def _gen_stone():
    o=[]
    for yi in range(_TN):
        ty=yi/_TN
        for xi in range(_TN):
            tx=xi/_TN; hx=tx%0.33; hy=ty%0.25
            if hx<0.032 or hy<0.032: o.append(0.18); continue
            bx=int(tx*3); by=int(ty*4)
            o.append(0.38+0.38*(((bx*13+by*29+bx*by*7)%16)/15.0))
    return o

def _gen_tech():
    o=[]
    for yi in range(_TN):
        ty=yi/_TN
        for xi in range(_TN):
            tx=xi/_TN; gx=tx%0.125; gy=ty%0.125
            if gx<0.018 or gy<0.018: o.append(0.18); continue
            cx=int(tx*8); cy=int(ty*8)
            o.append(0.80 if (cx*7+cy*13+cx^cy)%11==0 else 0.42+0.28*(((cx*5+cy*11)%8)/7.0))
    return o

_TEXTURES = [_gen_brick(), _gen_metal(), _gen_stone(), _gen_tech()]

WALL_COLORS = {
    '#': (178,118, 62), 'M': (118,122,132), 'R': (148, 38, 38),
    'D': ( 88,130, 88), 'W': (100,100,200), 'T': (200,100, 40),
}
SOLID_SET = {'#','M','R','D'}
CEIL_TOP=(2,2,18);   CEIL_BOT=(10,10,38)
FLR_TOP=(12,10,5);   FLR_BOT=(28,22,10)
_PC_NORM=[f'#{0:02x}{b:02x}{b//4:02x}' for b in range(256)]
_PC_SIDE=[f'#{0:02x}{int(b*.6):02x}{int(b*.15):02x}' for b in range(256)]

def _rgb(r,g,b): return f"#{int(max(0,min(255,r))):02x}{int(max(0,min(255,g))):02x}{int(max(0,min(255,b))):02x}"
def _lerp3(a,b,t): return (a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2]))

def get_texel(tid,tx,ty):
    xi=int(tx*(_TN-1))&(_TN-1); yi=int(ty*(_TN-1))&(_TN-1)
    return _TEXTURES[tid%4][yi*_TN+xi]

def cast_ray(grid_fn, px, py, ra):
    ca=math.cos(ra); sa=math.sin(ra)
    if abs(ca)<1e-9: ca=1e-9
    if abs(sa)<1e-9: sa=1e-9
    mx,my=int(px),int(py); ddx,ddy=abs(1/ca),abs(1/sa)
    sx=1 if ca>0 else -1; sy=1 if sa>0 else -1
    sdx=(mx+(1 if ca>0 else 0)-px)/ca; sdy=(my+(1 if sa>0 else 0)-py)/sa
    side=0
    for _ in range(MAX_DEPTH*3):
        if sdx<sdy: sdx+=ddx; mx+=sx; side=0
        else:       sdy+=ddy; my+=sy; side=1
        c = grid_fn(mx,my)
        if c in SOLID_SET:
            perp=((mx-px+(1-sx)*.5)/ca if side==0 else (my-py+(1-sy)*.5)/sa)
            wx=(py+perp*sa if side==0 else px+perp*ca)
            wrgb=WALL_COLORS.get(c, WALL_COLORS['#'])
            return max(perp,.01),side,wrgb,wx-math.floor(wx),c
    return float(MAX_DEPTH),0,WALL_COLORS['#'],0.0,'#'

def _wall_color(dist,side,tile_rgb,texel,phosphor):
    f=max(.06,1-dist/MAX_DEPTH)*(SIDE_DIM if side else 1.)*texel
    if phosphor:
        b=int(f*255); return _PC_SIDE[b] if side else _PC_NORM[b]
    r2,g2,b2=tile_rgb; return _rgb(r2*f,g2*f,b2*f)

GUN_IDLE={'FIST':"   | |\n   | |\n___|_|___",'PISTOL':"   |_|\n   | |\n___|_|___",
          'SHOTGUN':"  =====\n   | |\n___|_|_____",'CHAINGUN':"  ======\n  |  |\n__|__|____",
          'ROCKETL':"  [===>\n   | |\n___|_|____"}
GUN_FIRE={'FIST':"  \\  /\n   ==\n  /  \\",'PISTOL':"  _|_\n  |#|\n__|_|__",
          'SHOTGUN':" ===*=\n  |*|\n__|_|____",'CHAINGUN':"=======\n  |##|\n__|##|____",
          'ROCKETL':" [==*=>\n  |**|\n__|__|__"}

# =============================================================================
# §9  PLAY MODE GAME STATE
# =============================================================================
class PlayPlayer:
    def __init__(self, settings, skill=1):
        self.x = 2.5; self.y = 2.5; self.ang = 0.0
        skill_mult = SKILL_LEVELS[skill][1]
        self.hp   = settings.get('player_hp', 100)
        self.max_hp = self.hp
        self.armor = 0
        self.ammo  = {'bullets': 120, 'shells': 16, 'rockets': 4}
        self.weapon = 1
        self.weapons_owned = {0, 1}
        self.perks = set()
        self.points = settings.get('start_points', 500)
        self.kills = 0; self.score = 0
        self.fire_t = 0.0; self.hurt_t = 0.0
        self.step_acc = 0.0; self.bob = 0.0
        self.in_vehicle = None
        self.pap_weapons = set()   # pack-a-punched

class PlayEnemy:
    def __init__(self, x, y, kind, hp_mult=1.0):
        self.x=x; self.y=y; self.kind=kind
        base_hp = ENEMY_DEFS[kind][1]
        self.hp = int(base_hp * hp_mult)
        self.max_hp = self.hp
        self.alert=False; self.dmg_acc=0.0; self.dead_t=0.0

class PlayVehicle:
    def __init__(self, x, y, kind='CAR'):
        self.x=x; self.y=y; self.ang=0.0; self.kind=kind
        self.vx=0.0; self.vy=0.0; self.speed=0.0
        self.occupied_by=None

class ElectricTrap:
    def __init__(self, x, y):
        self.x=x; self.y=y; self.active=True; self.cooldown=0.0

class PlayGameState:
    """Full Nacht Der Untoten / Der Riese zombie survival state."""
    def __init__(self, cart, skill=1):
        self.cart = cart
        self.skill = skill
        self.skill_hp_mult, self.skill_dmg_mult = SKILL_LEVELS[skill][1], SKILL_LEVELS[skill][2]
        settings = cart.get('settings', {})
        self.player = PlayPlayer(settings, skill)
        self.enemies = []
        self.vehicles = []
        self.traps = []
        self.round = 1
        self.round_state = 'spawning'   # 'spawning', 'active', 'intermission'
        self.intermission_t = 0.0
        self.enemies_to_spawn = 0
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.wave_params = {}
        self.power_active = settings.get('power_active', False)
        self.box_x = 5.0; self.box_y = 3.0  # mystery box position
        self.box_active = True; self.box_spinning = False; self.box_timer = 0.0
        self.pap_teleporter_linked = False
        self.shots_this_wave = 0; self.hits_this_wave = 0
        self.damage_taken_this_wave = 0; self.points_earned_this_wave = 0
        self.notifications = deque(maxlen=8)   # (text, expire_time)
        self.flowscript = FlowScript(env={'wave':1,'hp':100,'points':500}, tone_fn=play_tone)
        self.console_output = deque(maxlen=20)
        self.console_open = False
        self.console_input = ''
        self.dead = False; self.victory = False
        self.race_timer = 0.0; self.lap_times = []; self.checkpoints_hit = set()
        self.checkpoints_total = 0
        self.minimap_visible = True
        # Parse cartridge map
        self._build_map()
        self._start_round(1)

    def _build_map(self):
        cart = self.cart
        W, H = cart.get('width', 20), cart.get('height', 15)
        self.map_w = W; self.map_h = H
        self.grid = {}
        for k,v in cart.get('grid', {}).items():
            x,y = map(int, k.split(','))
            self.grid[(x,y)] = v
        # Entities
        for ent in cart.get('entities', []):
            ex, ey = ent.get('x', 0), ent.get('y', 0)
            etype = ent.get('type','')
            if etype == 'player_start':
                self.player.x = ex + 0.5; self.player.y = ey + 0.5
            elif etype in VEHICLE_DEFS:
                self.vehicles.append(PlayVehicle(ex+0.5, ey+0.5, etype))
            elif etype == 'electric_trap':
                self.traps.append(ElectricTrap(ex+0.5, ey+0.5))
            elif etype == 'mystery_box':
                self.box_x = ex+0.5; self.box_y = ey+0.5
            elif etype == 'checkpoint':
                self.checkpoints_total += 1
        # Wall weapons
        self.wall_weapons = {}
        for k,v in cart.get('wall_weapons', {}).items():
            x,y = map(int, k.split(','))
            self.wall_weapons[(x,y)] = int(v)
        # Perks
        self.perk_machines = {}
        for k,v in cart.get('perks', {}).items():
            x,y = map(int, k.split(','))
            self.perk_machines[(x,y)] = v
        # Dialogue
        self.dialogue = cart.get('dialogue', {})
        self.npc_spoken = set()
        # Doors
        self.doors = {}
        for pos,val in self.grid.items():
            if val == 'D': self.doors[pos] = False  # False=closed

    def get_tile(self, x, y):
        mx,my = int(x), int(y)
        v = self.grid.get((mx,my))
        if v is not None: return v
        # Default: border is wall
        if mx<0 or my<0 or mx>=self.map_w or my>=self.map_h: return '#'
        return ' '

    def is_solid(self, x, y):
        t = self.get_tile(x, y)
        if t in SOLID_SET: return True
        if t == 'D' and self.doors.get((int(x),int(y)), False) is False: return True
        return False

    def _start_round(self, rnum):
        self.round = rnum
        base = self.cart.get('settings', {}).get('wave_base', WAVE_CONFIG['base_enemies'])
        scale = self.cart.get('settings', {}).get('wave_scale', WAVE_CONFIG['scale_per_round'])
        self.enemies_to_spawn = base + (rnum - 1) * scale
        if rnum % WAVE_CONFIG['boss_every_n_rounds'] == 0:
            self.enemies_to_spawn = max(1, self.enemies_to_spawn // 3)
        # Evolve wave from spectral signature
        sig = compute_spectral_signature(
            self.shots_this_wave, self.hits_this_wave,
            self.damage_taken_this_wave, self.points_earned_this_wave, rnum)
        self.wave_params = evolve_wave_params(
            self.cart.get('seed_signature',''), sig, rnum)
        self.shots_this_wave = 0; self.hits_this_wave = 0
        self.damage_taken_this_wave = 0; self.points_earned_this_wave = 0
        # Update FlowScript env
        self.flowscript.env['wave'] = rnum
        self.flowscript.env['hp'] = self.player.hp
        self.flowscript.env['points'] = self.player.points
        # Build spawn queue
        hp_mult = (self.cart.get('settings',{}).get('health_scale', 1.15) ** (rnum-1)) * self.skill_hp_mult
        hp_mult *= self.wave_params.get('hp_bonus', 1.0)
        boss_wave = (rnum % WAVE_CONFIG['boss_every_n_rounds'] == 0)
        kinds = ['B'] if boss_wave else ['Z','Z','Z','I','I','N']
        self.spawn_queue = [(_ENTROPY.choice(kinds), hp_mult)
                            for _ in range(self.enemies_to_spawn)]
        self.spawn_timer = 0.0
        self.round_state = 'spawning'
        self.notify(f'=== ROUND {rnum} BEGIN ===', 4.0)
        sfx('roundend')
        play_ambient(55 + rnum * 4, rnum)

    def notify(self, text, dur=3.0):
        self.notifications.append((text, time.time() + dur))

    def get_notifications(self):
        t = time.time()
        return [txt for txt,exp in self.notifications if exp > t]

    def update(self, dt, keys):
        if self.dead or self.victory: return
        pl = self.player

        # Update flame-timers
        if pl.fire_t > 0: pl.fire_t = max(0, pl.fire_t - dt)
        if pl.hurt_t > 0: pl.hurt_t = max(0, pl.hurt_t - dt)

        # Vehicle movement
        if pl.in_vehicle:
            self._update_vehicle(dt, keys)
        else:
            self._update_movement(dt, keys)

        # Spawn enemies
        if self.round_state == 'spawning' and self.spawn_queue:
            self.spawn_timer -= dt
            alive_count = sum(1 for e in self.enemies if e.hp > 0)
            if self.spawn_timer <= 0 and alive_count < WAVE_CONFIG['max_enemies_alive']:
                kind, hm = self.spawn_queue.pop(0)
                sx,sy = self._find_spawn()
                self.enemies.append(PlayEnemy(sx, sy, kind, hm))
                spread = self.wave_params.get('delay_spread', 0.5)
                self.spawn_timer = 0.3 + _ENTROPY.rand() * spread

        # Round end check
        if self.round_state == 'spawning' and not self.spawn_queue:
            self.round_state = 'active'
        alive_enemies = [e for e in self.enemies if e.hp > 0]
        if self.round_state == 'active' and not alive_enemies and not self.spawn_queue:
            self.round_state = 'intermission'
            self.intermission_t = 5.0
            self.notify(f'ROUND {self.round} CLEARED!  Starting next round in 5s...', 5.0)
            sfx('roundend')
        if self.round_state == 'intermission':
            self.intermission_t -= dt
            if self.intermission_t <= 0:
                self._start_round(self.round + 1)
                self.enemies = [e for e in self.enemies if e.hp > 0]

        # Update enemies
        self._update_enemies(dt)

        # Update traps
        for trap in self.traps:
            if trap.cooldown > 0: trap.cooldown -= dt

        # Check death
        if pl.hp <= 0:
            self.dead = True; self.notify('YOU DIED — Game Over', 99)

        # NPC dialogue
        self._check_npc_proximity()

    def _find_spawn(self):
        """Find a random empty tile far from player."""
        for _ in range(60):
            x = _ENTROPY.randint(1, self.map_w-2) + 0.5
            y = _ENTROPY.randint(1, self.map_h-2) + 0.5
            if not self.is_solid(x, y):
                dx = x - self.player.x; dy = y - self.player.y
                if dx*dx + dy*dy > 16: return x,y
        return 1.5, 1.5

    def _update_movement(self, dt, keys):
        pl = self.player
        spd = PLAYER_BASE['move_speed']
        if 'STAMINUP' in pl.perks: spd *= 1.30
        turn = PLAYER_BASE['turn_speed']
        if keys.get('Left')  or keys.get('a'): pl.ang -= turn
        if keys.get('Right') or keys.get('d'): pl.ang += turn
        dx = math.cos(pl.ang); dy = math.sin(pl.ang)
        pdx = -dy; pdy = dx  # strafe perpendicular
        mx=my=0.0
        if keys.get('Up')    or keys.get('w'): mx+=dx*spd; my+=dy*spd
        if keys.get('Down')  or keys.get('s'): mx-=dx*spd; my-=dy*spd
        if keys.get('q'):  mx+=pdx*spd*.75; my+=pdy*spd*.75
        if keys.get('e') and not pl.in_vehicle:
            mx+=pdx*spd*.75; my+=pdy*spd*.75
            # Also: enter vehicle
            self._try_enter_vehicle()
        nx,ny = pl.x+mx, pl.y+my
        if not self.is_solid(nx, pl.y): pl.x = nx
        if not self.is_solid(pl.x, ny): pl.y = ny
        pl.bob = math.fmod(pl.bob + dt * 5.5, TAU) if (mx or my) else 0.0

    def _update_vehicle(self, dt, keys):
        veh = pl = self.player.in_vehicle
        veh_def = VEHICLE_DEFS[veh.kind]
        max_spd = veh_def['speed']
        turn = veh_def['turn']
        if keys.get('Up') or keys.get('w'):   veh.speed = min(veh.speed + 0.005, max_spd)
        if keys.get('Down') or keys.get('s'): veh.speed = max(veh.speed - 0.008, -max_spd*0.5)
        if abs(veh.speed) > 0.001:
            if keys.get('Left') or keys.get('a'):   veh.ang -= turn
            if keys.get('Right') or keys.get('d'):  veh.ang += turn
        # Handbrake
        if keys.get('space'): veh.speed *= 0.85
        # Friction
        veh.speed *= 0.96
        dx = math.cos(veh.ang)*veh.speed; dy = math.sin(veh.ang)*veh.speed
        nx,ny = veh.x+dx, veh.y+dy
        if not self.is_solid(nx, veh.y): veh.x = nx
        if not self.is_solid(veh.x, ny): veh.y = ny
        self.player.x = veh.x; self.player.y = veh.y; self.player.ang = veh.ang
        # Exit
        if keys.get('e_tap'):
            self.player.in_vehicle = None
            veh.occupied_by = None
            keys['e_tap'] = False

    def _try_enter_vehicle(self):
        pl = self.player
        for veh in self.vehicles:
            dx,dy = veh.x-pl.x, veh.y-pl.y
            if dx*dx+dy*dy < 2.0 and veh.occupied_by is None:
                pl.in_vehicle = veh
                veh.occupied_by = pl
                self.notify(f'Entered {veh.kind}  |  E=exit  SPACE=brake', 3.0)
                break

    def _update_enemies(self, dt):
        pl = self.player
        for e in self.enemies:
            if e.hp <= 0:
                if e.dead_t > 0: e.dead_t = max(0, e.dead_t-dt)
                continue
            _,_,spd,dps,*_ = ENEMY_DEFS[e.kind]
            dps *= self.skill_dmg_mult
            dx,dy = e.x-pl.x, e.y-pl.y; d=math.sqrt(dx*dx+dy*dy)
            if d < 9.0: e.alert=True
            if e.alert and d > 0.55:
                s = spd*min(2.8, 3.5/max(d,.5))
                nx=e.x-(dx/d)*s; ny=e.y-(dy/d)*s
                if not self.is_solid(nx, e.y): e.x=nx
                if not self.is_solid(e.x, ny): e.y=ny
            # Melee attack
            if e.alert and d < 1.5:
                e.dmg_acc += dps*dt; n=int(e.dmg_acc)
                if n>0:
                    self._damage_player(n); e.dmg_acc-=n

    def _damage_player(self, dmg):
        pl = self.player
        if 'JUGGERNOG' in pl.perks: dmg = int(dmg * 0.5)
        if pl.armor > 0:
            absorb=min(int(dmg*0.5), pl.armor); pl.armor-=absorb; dmg-=absorb
        pl.hp = max(0, pl.hp - dmg)
        pl.hurt_t = 0.35; self.damage_taken_this_wave += dmg; sfx('pain')

    def shoot(self):
        pl = self.player
        if pl.fire_t > 0: return
        if pl.weapon not in pl.weapons_owned: return
        wdat = WEAPONS.get(pl.weapon)
        if not wdat: return
        _,dmin,dmax,pellets,fdelay,cost,atype,sfxname = wdat
        if atype and pl.ammo.get(atype,0) < cost: return
        if atype: pl.ammo[atype] -= cost
        # Speed Cola halves fire delay
        delay = fdelay * (0.5 if 'SPEEDCOLA' in pl.perks else 1.0)
        # Double Tap
        if 'DOUBLETAP' in pl.perks: delay *= 0.67
        pl.fire_t = delay
        self.shots_this_wave += 1
        sfx(sfxname)
        for _ in range(pellets):
            spread = _RNG.uniform(-0.08, 0.08) if pellets > 1 else 0.0
            sang = pl.ang + spread
            best=20.0; hit_e=None
            for e in self.enemies:
                if e.hp<=0: continue
                dx,dy=e.x-pl.x,e.y-pl.y; d=math.sqrt(dx*dx+dy*dy)
                if d>16: continue
                da=(math.atan2(dy,dx)-sang+math.pi)%TAU-math.pi
                if abs(da)<0.22 and d<best: best=d; hit_e=e
            if hit_e:
                pap = pl.weapon in pl.pap_weapons
                dmg = _RNG.randint(dmin,dmax) * (2 if pap else 1)
                hit_e.hp -= dmg; hit_e.alert=True; self.hits_this_wave+=1
                sfx('hit')
                if hit_e.hp <= 0:
                    pts = ENEMY_DEFS[hit_e.kind][4]
                    pl.points += pts; pl.kills+=1; pl.score+=pts
                    self.points_earned_this_wave += pts
                    hit_e.dead_t=1.2; sfx('death')
                    self.notify(f'+{pts} pts  [{ENEMY_DEFS[hit_e.kind][0]}]', 1.5)

    def use_action(self):
        """Player pressed F/R/Use — interact with nearby objects."""
        pl = self.player
        # Check doors
        ax=int(pl.x+math.cos(pl.ang)*1.8); ay=int(pl.y+math.sin(pl.ang)*1.8)
        if self.doors.get((ax,ay)) is False:
            # Open doors cost points (zombies mechanic)
            if pl.points >= 250:
                self.doors[(ax,ay)] = True
                self.grid[(ax,ay)] = ' '
                pl.points -= 250
                self.notify('Door opened! (-250 pts)', 2.0); sfx('door'); return

        # Wall weapons
        for pos, wid in self.wall_weapons.items():
            dx=pos[0]+0.5-pl.x; dy=pos[1]+0.5-pl.y
            if dx*dx+dy*dy < 2.5:
                wname, cost = WALL_WEAPONS.get(wid, ('?',999))
                if pl.points >= cost:
                    pl.points -= cost
                    pl.weapons_owned.add(wid); pl.weapon=wid
                    # Top up ammo
                    atype = WEAPONS[wid][6]
                    if atype: pl.ammo[atype] = min(pl.ammo.get(atype,0)+60, 300)
                    self.notify(f'Bought {wname}! (-{cost} pts)', 2.5); sfx('buy'); return
                else:
                    self.notify(f'Need {cost} pts for {wname}', 1.5); return

        # Perk machines
        for pos, pname in self.perk_machines.items():
            dx=pos[0]+0.5-pl.x; dy=pos[1]+0.5-pl.y
            if dx*dx+dy*dy < 2.5:
                pdef = PERKS_COLA.get(pname)
                if not pdef: continue
                _,cost,desc = pdef
                if pname in pl.perks:
                    self.notify(f'Already have {pname}', 1.5); return
                if pl.points >= cost:
                    pl.points -= cost; pl.perks.add(pname)
                    if pname=='JUGGERNOG': pl.max_hp=int(pl.max_hp*2); pl.hp=pl.max_hp
                    self.notify(f'{pname}! {desc} (-{cost} pts)', 3.0); sfx('powerup'); return
                else:
                    self.notify(f'Need {cost} pts for {pname}', 1.5); return

        # Mystery box
        dx=self.box_x-pl.x; dy=self.box_y-pl.y
        if dx*dx+dy*dy < 2.5 and self.box_active and not self.box_spinning:
            if pl.points >= 950:
                pl.points -= 950; self.box_spinning=True; self.box_timer=3.0
                self.notify('Mystery Box spinning...', 3.0); sfx('box'); return
            else:
                self.notify('Need 950 pts for Mystery Box', 1.5); return

        # Pack-a-Punch (needs power + linked teleporters)
        if self.power_active:
            # Check if near a teleporter entity
            for ent in self.cart.get('entities',[]):
                if ent.get('type')=='teleporter':
                    tx,ty=ent.get('x',0)+0.5, ent.get('y',0)+0.5
                    dx2=tx-pl.x; dy2=ty-pl.y
                    if dx2*dx2+dy2*dy2 < 2.5:
                        if pl.points >= PACK_A_PUNCH_COST and pl.weapon not in pl.pap_weapons:
                            pl.points -= PACK_A_PUNCH_COST
                            pl.pap_weapons.add(pl.weapon)
                            wn=WEAPONS[pl.weapon][0]
                            self.notify(f'PACK-A-PUNCHED {wn}!! (-{PACK_A_PUNCH_COST} pts)', 4.0)
                            sfx('powerup'); return
                        elif pl.weapon in pl.pap_weapons:
                            self.notify(f'{WEAPONS[pl.weapon][0]} already PaP\'d', 1.5); return
                        else:
                            self.notify(f'Need {PACK_A_PUNCH_COST} pts for Pack-a-Punch', 1.5); return

        # Electric trap
        for trap in self.traps:
            dx=trap.x-pl.x; dy=trap.y-pl.y
            if dx*dx+dy*dy < 2.5 and trap.cooldown <= 0:
                if pl.points >= TRAP_COST:
                    pl.points -= TRAP_COST; trap.cooldown=TRAP_COOLDOWN
                    # ZAP all nearby enemies
                    zapped=0
                    for e in self.enemies:
                        if e.hp<=0: continue
                        ex=e.x-trap.x; ey=e.y-trap.y
                        if ex*ex+ey*ey < 9.0:
                            e.hp-=TRAP_DAMAGE; zapped+=1
                            if e.hp<=0: e.dead_t=1.2
                    self.notify(f'TRAP ZAP! {zapped} enemies shocked (-{TRAP_COST} pts)', 2.5)
                    sfx('trap'); return
                else:
                    self.notify(f'Need {TRAP_COST} pts for trap', 1.5); return

    def update_mystery_box(self, dt):
        if self.box_spinning:
            self.box_timer -= dt
            if self.box_timer <= 0:
                self.box_spinning = False
                pool = list(MYSTERY_BOX_POOL.keys())
                weights = [MYSTERY_BOX_POOL[w] for w in pool]
                total = sum(weights)
                r = _ENTROPY.rand() * total
                chosen = pool[0]
                for w,wt in zip(pool, weights):
                    r -= wt
                    if r <= 0: chosen=w; break
                pl = self.player
                pl.weapons_owned.add(chosen); pl.weapon=chosen
                wname=WEAPONS[chosen][0]
                atype=WEAPONS[chosen][6]
                if atype: pl.ammo[atype]=min(pl.ammo.get(atype,0)+60,300)
                self.notify(f'Mystery Box: {wname}!', 3.0); sfx('powerup')

    def _check_npc_proximity(self):
        pl = self.player
        for i,ent in enumerate(self.cart.get('entities',[])):
            if ent.get('type')!='npc': continue
            if i in self.npc_spoken: continue
            ex=ent.get('x',0)+0.5; ey=ent.get('y',0)+0.5
            dx=ex-pl.x; dy=ey-pl.y
            if dx*dx+dy*dy < 4.0:
                self.npc_spoken.add(i)
                lines = self.dialogue.get(str(i), [])
                for line in lines:
                    self.notify(f'NPC: {line}', 4.0)
                    speak(line)

    def exec_console(self, cmd):
        """Execute a FlowScript command from the dev console."""
        try:
            # Quick variable access: "var = value"
            if '=' in cmd and not cmd.strip().startswith('set'):
                parts = cmd.split('=', 1)
                k = parts[0].strip(); v = parts[1].strip()
                try: v2 = float(v) if '.' in v else int(v)
                except ValueError: v2 = v
                # Apply to game state
                if k == 'hp': self.player.hp = int(v2); self.player.max_hp=max(self.player.max_hp,int(v2))
                elif k == 'points': self.player.points = int(v2)
                elif k == 'wave': self._start_round(int(v2))
                elif k == 'ammo': self.player.ammo = {t:int(v2) for t in self.player.ammo}
                elif k == 'armor': self.player.armor = int(v2)
                self.flowscript.env[k] = v2
                self.console_output.append(f'{k} = {v2} .-')
                return
            # FlowScript
            out = self.flowscript.run(cmd)
            for line in out:
                self.console_output.append(line)
            if not out:
                self.console_output.append(f'> {cmd} .-')
        except Exception as ex:
            self.console_output.append(f'ERROR: {ex} .-')

# =============================================================================
# §10  PLAY MODE RENDERER  (tkinter canvas raycaster)
# =============================================================================
class PlayRenderer:
    def __init__(self, canvas):
        self.cv = canvas
        half = VIEW_H // 2
        self._wb = []
        for c in range(COLS):
            x1,x2=c*COL_W,(c+1)*COL_W
            bands=[canvas.create_rectangle(x1,0,x2,1,fill='#001a05',outline='',state='hidden') for _ in range(WALL_BANDS)]
            self._wb.append(bands)
        self._cr=[canvas.create_rectangle(c*COL_W,0,(c+1)*COL_W,half,fill='#02020e',outline='') for c in range(COLS)]
        self._fr=[canvas.create_rectangle(c*COL_W,half,(c+1)*COL_W,VIEW_H,fill='#0e0b04',outline='') for c in range(COLS)]
        self._spr=[canvas.create_rectangle(0,0,0,0,fill='#cc2200',outline='#ff4422') for _ in range(MAX_SPR)]
        cx,cy=VIEW_W//2,VIEW_H//2
        self._xh=canvas.create_line(cx-12,cy,cx+12,cy,fill='#00cc44',width=1)
        self._xv=canvas.create_line(cx,cy-9,cx,cy+9,fill='#00cc44',width=1)
        self._gun=canvas.create_text(VIEW_W//2,VIEW_H-55,text='',fill='#aaaaaa',font=('Courier',10,'bold'),anchor='center')
        self._notif=canvas.create_text(VIEW_W//2,28,text='',fill='#ffdd44',font=('Courier',12,'bold'),anchor='center')
        self._hurt=canvas.create_rectangle(0,0,VIEW_W,VIEW_H,fill='#bb0000',outline='',state='hidden')
        try: canvas.itemconfig(self._hurt,stipple='gray25')
        except: pass
        # Minimap
        self._mm_bg=canvas.create_rectangle(VIEW_W-105,4,VIEW_W-4,95,fill='#070707',outline='#333333')
        self._mm_pl=canvas.create_oval(0,0,4,4,fill='#00ff88',outline='')
        self._mm_dir=canvas.create_line(0,0,1,1,fill='#00ff88',width=1)
        # Box spin indicator
        self._box_label=canvas.create_text(VIEW_W//2,VIEW_H-20,text='',fill='#ffaa00',font=('Courier',10,'bold'),anchor='center')
        # Console overlay
        self._console_bg=canvas.create_rectangle(4,VIEW_H-200,VIEW_W-4,VIEW_H-4,fill='#000a00',outline='#00cc44',state='hidden')
        self._console_texts=[]
        for i in range(12):
            self._console_texts.append(canvas.create_text(10,VIEW_H-190+i*16,text='',fill='#00ff88',font=('Courier',9),anchor='w',state='hidden'))
        self._console_input=canvas.create_text(10,VIEW_H-10,text='',fill='#ffff00',font=('Courier',10,'bold'),anchor='w',state='hidden')

    def draw(self, gs):
        pl = gs.player
        cv = self.cv; half = VIEW_H//2
        zbuf = [0.0]*COLS

        for col in range(COLS):
            ra=pl.ang-FOV*.5+FOV*col/COLS
            dist,side,wrgb,tx,tile=cast_ray(lambda x,y: gs.get_tile(x,y), pl.x, pl.y, ra)
            zbuf[col]=dist
            bob=int(math.sin(pl.bob)*2) if not pl.in_vehicle else 0
            wh=min(int(VIEW_H/max(dist,.01)),VIEW_H)
            top=max((VIEW_H-wh)>>1,0)+bob; bot=min(top+wh,VIEW_H-1)
            x1,x2=col*COL_W,(col+1)*COL_W
            tid={'#':0,'M':1,'R':2,'D':3,'W':3,'T':2}.get(tile,0)
            ct=max(0.,min(1.,top/half if top>0 else 0.))
            cv.coords(self._cr[col],x1,0,x2,max(top,1))
            cv.itemconfig(self._cr[col],fill=_rgb(*_lerp3(CEIL_TOP,CEIL_BOT,ct)))
            ft=max(0.,min(1.,(VIEW_H-bot)/max(VIEW_H-half,1)))
            cv.coords(self._fr[col],x1,bot,x2,VIEW_H)
            cv.itemconfig(self._fr[col],fill=_rgb(*_lerp3(FLR_TOP,FLR_BOT,ft)))
            wb=self._wb[col]
            if top>=bot:
                for b in wb: cv.itemconfig(b,state='hidden'); continue
            bh=max(1,(bot-top)//WALL_BANDS)
            for b in range(WALL_BANDS):
                by1=top+b*bh; by2=top+(b+1)*bh if b<WALL_BANDS-1 else bot
                if by1>=by2: cv.itemconfig(wb[b],state='hidden'); continue
                ty_v=(b+.5)/WALL_BANDS; texel=get_texel(tid,tx,ty_v)
                color=_wall_color(dist,side,wrgb,texel,False)
                cv.coords(wb[b],x1,by1,x2,by2)
                cv.itemconfig(wb[b],fill=color,state='normal')

        # Sprites: enemies + vehicles + box
        sprites=[]
        for e in gs.enemies:
            dx,dy=e.x-pl.x,e.y-pl.y
            if e.hp>0:
                rgb=ENEMY_DEFS[e.kind][5]; col2=(220,50,50) if e.alert else rgb
                hp_frac=e.hp/e.max_hp
                sprites.append((dx*dx+dy*dy,dx,dy,_rgb(*[int(c*hp_frac+(255-255*hp_frac)*0.2) for c in col2]),'#ff4422',ENEMY_DEFS[e.kind][6]))
            elif e.dead_t>0:
                sprites.append((dx*dx+dy*dy,dx,dy,'#3a1508','#2a1005',.3))
        for veh in gs.vehicles:
            dx,dy=veh.x-pl.x,veh.y-pl.y
            vc=VEHICLE_DEFS[veh.kind]['color']
            sprites.append((dx*dx+dy*dy,dx,dy,vc,'#ffffff',VEHICLE_DEFS[veh.kind]['width']))
        # Mystery box
        bdx=gs.box_x-pl.x; bdy=gs.box_y-pl.y
        bcol='#ffdd00' if not gs.box_spinning else '#ff8800'
        sprites.append((bdx*bdx+bdy*bdy,bdx,bdy,bcol,'#ffffff',0.55))

        sprites.sort(reverse=True)
        for r in self._spr: cv.coords(r,0,0,0,0)
        for si,(d2,dx,dy,fill,out,sz) in enumerate(sprites):
            if si>=MAX_SPR: break
            dist2=math.sqrt(d2)
            if dist2<.35: continue
            ra2=(math.atan2(dy,dx)-pl.ang+math.pi)%TAU-math.pi
            if abs(ra2)>FOV*.6: continue
            sx2=int((ra2/FOV+.5)*COLS)
            if not(0<=sx2<COLS) or zbuf[sx2]<=dist2: continue
            spH=min(int(VIEW_H*sz/max(dist2,.01)),VIEW_H-2)
            spW=max(int(spH*COL_W//5),COL_W*2)
            pxc=sx2*COL_W+COL_W//2; ty2=max(half-spH//2,0); by2=min(half+spH//2,VIEW_H-2)
            cv.coords(self._spr[si],pxc-spW//2,ty2,pxc+spW//2,by2)
            cv.itemconfig(self._spr[si],fill=fill,outline=out)

        # Gun
        if not pl.in_vehicle:
            wname=WEAPONS.get(pl.weapon,WEAPONS[1])[0]
            cv.itemconfig(self._gun,text=GUN_FIRE.get(wname,'|*|') if pl.fire_t>0 else GUN_IDLE.get(wname,'| |'),
                          fill='#ff6622' if pl.fire_t>0 else '#999999')
        else:
            cv.itemconfig(self._gun,text=f'[ {pl.in_vehicle.kind} ]  WASD=drive  SPACE=brake  E=exit',fill='#88aaff')

        # Hurt flash
        cv.itemconfig(self._hurt,state='normal' if pl.hurt_t>0 else 'hidden')

        # Notifications
        notifs=gs.get_notifications()
        cv.itemconfig(self._notif,text=notifs[0] if notifs else '')

        # Box spinning
        cv.itemconfig(self._box_label,text='Mystery Box spinning...' if gs.box_spinning else '')

        # Minimap
        if gs.minimap_visible:
            cv.itemconfig(self._mm_bg,state='normal')
            cv.itemconfig(self._mm_pl,state='normal')
            cv.itemconfig(self._mm_dir,state='normal')
            MM=4; mmx=VIEW_W-103; mmy=6
            ppx=mmx+int(pl.x*MM); ppy=mmy+int(pl.y*MM)
            cv.coords(self._mm_pl,ppx-3,ppy-3,ppx+3,ppy+3)
            cv.coords(self._mm_dir,ppx,ppy,ppx+int(math.cos(pl.ang)*MM*2),ppy+int(math.sin(pl.ang)*MM*2))
        else:
            cv.itemconfig(self._mm_bg,state='hidden')
            cv.itemconfig(self._mm_pl,state='hidden')
            cv.itemconfig(self._mm_dir,state='hidden')

        # Console
        if gs.console_open:
            cv.itemconfig(self._console_bg,state='normal')
            cv.itemconfig(self._console_input,state='normal')
            lines=list(gs.console_output)[-11:]
            for i,txt in enumerate(self._console_texts):
                line_text=lines[i] if i<len(lines) else ''
                cv.itemconfig(txt,text=line_text,state='normal')
            cv.itemconfig(self._console_input,text='> '+gs.console_input)
        else:
            cv.itemconfig(self._console_bg,state='hidden')
            cv.itemconfig(self._console_input,state='hidden')
            for t in self._console_texts: cv.itemconfig(t,state='hidden')

# =============================================================================
# §11  PLAY MODE HUD  (tkinter Frame below canvas)
# =============================================================================
class PlayHUD:
    def __init__(self, frame):
        self.f = frame
        lf=('Courier',10,'bold')
        ls=('Courier',9)
        self.lbl_hp    = tk.Label(frame,text='HP: 100',fg='#00ff44',bg='#0a0a0a',font=lf)
        self.lbl_armor = tk.Label(frame,text='ARM: 0',fg='#4488ff',bg='#0a0a0a',font=lf)
        self.lbl_ammo  = tk.Label(frame,text='AMMO: 120',fg='#ffcc00',bg='#0a0a0a',font=lf)
        self.lbl_wave  = tk.Label(frame,text='WAVE 1',fg='#ff4444',bg='#0a0a0a',font=lf)
        self.lbl_pts   = tk.Label(frame,text='PTS: 500',fg='#ffaa00',bg='#0a0a0a',font=lf)
        self.lbl_perks = tk.Label(frame,text='',fg='#00ccff',bg='#0a0a0a',font=ls)
        self.lbl_alive = tk.Label(frame,text='',fg='#ff6666',bg='#0a0a0a',font=ls)
        self.lbl_kills = tk.Label(frame,text='KILLS: 0',fg='#cc44cc',bg='#0a0a0a',font=ls)
        for i,w in enumerate([self.lbl_hp,self.lbl_armor,self.lbl_ammo,self.lbl_wave,
                               self.lbl_pts,self.lbl_perks,self.lbl_alive,self.lbl_kills]):
            w.grid(row=0,column=i,padx=8,pady=2)

    def update(self, gs):
        pl=gs.player
        wdat=WEAPONS.get(pl.weapon, WEAPONS[1])
        atype=wdat[6]
        ammo_v=pl.ammo.get(atype,'-') if atype else '∞'
        pap_mark='✦' if pl.weapon in pl.pap_weapons else ''
        alive=[e for e in gs.enemies if e.hp>0]
        self.lbl_hp.config(text=f'HP: {pl.hp}/{pl.max_hp}',
                           fg='#ff4444' if pl.hp<30 else '#00ff44')
        self.lbl_armor.config(text=f'ARM: {pl.armor}')
        self.lbl_ammo.config(text=f'{wdat[0]}{pap_mark}: {ammo_v}')
        self.lbl_wave.config(text=f'WAVE {gs.round} [{gs.round_state.upper()[:3]}]')
        self.lbl_pts.config(text=f'PTS: {pl.points}')
        self.lbl_perks.config(text=' '.join(pl.perks) or 'no perks')
        self.lbl_alive.config(text=f'ALIVE: {len(alive)}  SPAWN: {len(gs.spawn_queue)}')
        self.lbl_kills.config(text=f'KILLS: {pl.kills}')

# =============================================================================
# §12  PLAY MODE WINDOW
# =============================================================================
class PlayModeWindow:
    def __init__(self, parent, cart, skill=1):
        self.win=tk.Toplevel(parent)
        self.win.title("DoomCraft — PLAY MODE")
        self.win.configure(bg='#000000')
        self.win.resizable(False,False)
        self.win.geometry(f"{VIEW_W}x{VIEW_H+HUD_H}")

        self.canvas=tk.Canvas(self.win,width=VIEW_W,height=VIEW_H,bg='#000000',
                              highlightthickness=0,cursor='none')
        self.canvas.pack()
        hf=tk.Frame(self.win,bg='#0a0a0a',height=HUD_H)
        hf.pack(fill='x'); hf.pack_propagate(False)

        self.gs=PlayGameState(cart, skill)
        self.renderer=PlayRenderer(self.canvas)
        self.hud=PlayHUD(hf)

        self.keys={}
        self.running=True; self.last_t=time.time()

        self.win.bind('<KeyPress>',   self._on_key_down)
        self.win.bind('<KeyRelease>', self._on_key_up)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self.win.focus_force()

        # Init TTS
        threading.Thread(target=init_tts, daemon=True).start()

        self._tick()

    def _on_key_down(self, ev):
        ks=ev.keysym
        self.keys[ks]=True
        gs=self.gs

        # Console toggle
        if ks=='grave':
            gs.console_open=not gs.console_open
            if gs.console_open: gs.console_input=''
            return

        if gs.console_open:
            if ks=='Return':
                if gs.console_input.strip():
                    gs.exec_console(gs.console_input.strip())
                gs.console_input=''
            elif ks=='BackSpace':
                gs.console_input=gs.console_input[:-1]
            elif len(ks)==1:
                gs.console_input+=ks
            elif ks=='space':
                gs.console_input+=' '
            return

        if ks in ('F','f'):
            gs.shoot()
        if ks in ('space',) and not gs.player.in_vehicle:
            gs.shoot()
        if ks in ('r','R'):
            gs.use_action()
        if ks=='e' or ks=='E':
            if gs.player.in_vehicle:
                self.keys['e_tap']=True
            else:
                gs._try_enter_vehicle()
        # Weapon select
        for i in range(1,6):
            if ks==str(i): gs.player.weapon=i if i in gs.player.weapons_owned else gs.player.weapon
        if ks=='Tab': gs.minimap_visible=not gs.minimap_visible
        if ks=='Escape': self._on_close()

    def _on_key_up(self, ev):
        self.keys[ev.keysym]=False

    def _tick(self):
        if not self.running: return
        now=time.time(); dt=min(now-self.last_t, 0.05); self.last_t=now
        gs=self.gs
        if not gs.console_open:
            gs.update(dt, self.keys)
        gs.update_mystery_box(dt)
        self.renderer.draw(gs)
        self.hud.update(gs)
        if gs.dead:
            self._show_game_over()
        else:
            self.win.after(16, self._tick)

    def _show_game_over(self):
        pl=self.gs.player
        tk.messagebox.showinfo('GAME OVER',
            f'You died on Wave {self.gs.round}!\n'
            f'Kills: {pl.kills}   Score: {pl.score}\n'
            f'Points: {pl.points}\n\nThe dot sings.  .-',
            parent=self.win)
        self._on_close()

    def _on_close(self):
        self.running=False
        stop_ambient()
        self.win.destroy()

# =============================================================================
# §13  PIXEL EDITOR (16×16 sprite editor)
# =============================================================================
class SpriteEditor(tk.Toplevel):
    PALETTE=['#000000','#ffffff','#ff0000','#00cc00','#0000ff','#ffff00',
             '#ff8800','#cc44cc','#44ccff','#888888','#cc8844','#224422',
             '#ff4444','#44ff44','#4444ff','transparent']

    def __init__(self, parent, on_save=None, name='', initial_b64=''):
        super().__init__(parent)
        self.title('Sprite Editor — 16×16')
        self.resizable(False,False)
        self.on_save=on_save; self.sprite_name=name
        self.SZ=20  # pixel cell size in editor
        self.pixels=['transparent']*256
        self.current_color='#ff0000'
        if initial_b64:
            self._load_b64(initial_b64)
        self._build_ui()

    def _build_ui(self):
        top=tk.Frame(self,bg='#111'); top.pack(side='top',fill='x')
        tk.Label(top,text='Sprite Name:',bg='#111',fg='white').pack(side='left',padx=4)
        self.name_var=tk.StringVar(value=self.sprite_name)
        tk.Entry(top,textvariable=self.name_var,width=16,bg='#222',fg='white').pack(side='left',padx=4)
        tk.Button(top,text='Save',command=self._save,bg='#224422',fg='#00ff44').pack(side='right',padx=4)
        tk.Button(top,text='Clear',command=self._clear,bg='#442222',fg='#ff6666').pack(side='right',padx=4)

        mid=tk.Frame(self,bg='#111'); mid.pack()
        self.cv=tk.Canvas(mid,width=16*self.SZ,height=16*self.SZ,bg='#222',cursor='crosshair')
        self.cv.pack(side='left',padx=4,pady=4)
        self.cv.bind('<Button-1>',self._paint)
        self.cv.bind('<B1-Motion>',self._paint)
        self.cv.bind('<Button-3>',self._pick_color)

        pal_frame=tk.Frame(mid,bg='#111'); pal_frame.pack(side='left',padx=4)
        tk.Label(pal_frame,text='Palette',bg='#111',fg='white',font=('Courier',9,'bold')).pack()
        pf2=tk.Frame(pal_frame,bg='#111'); pf2.pack()
        for i,c in enumerate(self.PALETTE):
            bc='#555555' if c=='transparent' else c
            btn=tk.Canvas(pf2,width=22,height=22,bg=bc,cursor='hand2',relief='raised',bd=2)
            btn.grid(row=i//2,column=i%2,padx=1,pady=1)
            btn.bind('<Button-1>',lambda e,col=c:setattr(self,'current_color',col))
        self._redraw()

    def _paint(self,ev):
        x=ev.x//self.SZ; y=ev.y//self.SZ
        if 0<=x<16 and 0<=y<16:
            self.pixels[y*16+x]=self.current_color; self._redraw()

    def _pick_color(self,ev):
        x=ev.x//self.SZ; y=ev.y//self.SZ
        if 0<=x<16 and 0<=y<16:
            self.current_color=self.pixels[y*16+x]

    def _redraw(self):
        self.cv.delete('all')
        for y in range(16):
            for x in range(16):
                c=self.pixels[y*16+x]
                fill='#111' if c=='transparent' else c
                x1=x*self.SZ; y1=y*self.SZ
                self.cv.create_rectangle(x1,y1,x1+self.SZ,y1+self.SZ,fill=fill,outline='#333')

    def _clear(self):
        self.pixels=['transparent']*256; self._redraw()

    def _save(self):
        name=self.name_var.get().strip() or 'sprite'
        # Encode as PPM → base64 (no PIL needed)
        header=f'P3\n16 16\n255\n'
        rows=[]
        for p in self.pixels:
            if p=='transparent': rows.append('0 0 0 ')
            else:
                r=int(p[1:3],16); g=int(p[3:5],16); b=int(p[5:7],16)
                rows.append(f'{r} {g} {b} ')
        ppm=(header+''.join(rows)).encode()
        b64=base64.b64encode(ppm).decode()
        if self.on_save: self.on_save(name, b64)
        self.destroy()

    def _load_b64(self, b64):
        try:
            data=base64.b64decode(b64).decode()
            lines=data.strip().split('\n')
            nums=[int(v) for line in lines[3:] for v in line.split()]
            for i in range(min(256,len(nums)//3)):
                r,g,b=nums[i*3],nums[i*3+1],nums[i*3+2]
                self.pixels[i]=f'#{r:02x}{g:02x}{b:02x}'
        except Exception: pass

# =============================================================================
# §14  EDIT MODE (Map Forge)
# =============================================================================
TILE_TYPES = [
    ('wall',    '#',  '#886644', 'Wall (solid)'),
    ('floor',   ' ',  '#333333', 'Floor (empty)'),
    ('door',    'D',  '#44aa44', 'Door'),
    ('window',  'W',  '#4466cc', 'Window'),
    ('trap',    'T',  '#cc8800', 'Elec Trap wall'),
]
ENTITY_TYPES = [
    ('player_start', 'P', '#00ff88', 'Player Start'),
    ('zombie',       'Z', '#ccaa88', 'Zombie spawn'),
    ('imp',          'I', '#cc5522', 'Imp spawn'),
    ('demon',        'N', '#cc66aa', 'Demon spawn'),
    ('health',       'h', '#44aaff', 'Health pack'),
    ('ammo',         '+', '#ffcc00', 'Ammo'),
    ('mystery_box',  'B', '#ffdd00', 'Mystery Box'),
    ('npc',          'C', '#aaffaa', 'NPC'),
    ('teleporter',   'T', '#ff88ff', 'Teleporter'),
    ('checkpoint',   'K', '#ffffff', 'Race Checkpoint'),
    ('wall_weapon',  'W', '#ff8800', 'Wall Weapon'),
    ('perk_machine', 'R', '#00ccff', 'Perk Machine'),
    ('CAR',          'V', '#cc8800', 'Vehicle: Car'),
    ('TANK',         'V', '#448844', 'Vehicle: Tank'),
    ('BIKE',         'V', '#cc3300', 'Vehicle: Bike'),
    ('electric_trap','E', '#ffee00', 'Electric Trap'),
]

CELL = 36   # pixels per grid cell in editor

class EditMode(tk.Toplevel):
    def __init__(self, parent, cart=None, on_save=None):
        super().__init__(parent)
        self.title('DoomCraft — EDIT MODE (Forge)')
        self.resizable(True, True)
        self.on_save = on_save
        self.cart = cart or {k:v for k,v in DEFAULT_CARTRIDGE.items()}
        self.cart.setdefault('grid',{})
        self.cart.setdefault('entities',[])
        self.cart.setdefault('wall_weapons',{})
        self.cart.setdefault('perks',{})
        self.cart.setdefault('sprites',{})
        self.cart.setdefault('dialogue',{})
        self.cart.setdefault('settings',DEFAULT_CARTRIDGE['settings'].copy())

        self.selected_tile = '#'
        self.selected_entity = None
        self.tool = 'tile'   # 'tile', 'entity', 'erase'
        self.cam_x = 0; self.cam_y = 0
        self.grid_w = self.cart.get('width', 20)
        self.grid_h = self.cart.get('height', 15)
        self.hover_x = self.hover_y = -1

        self._build_ui()
        self._redraw()

    def _build_ui(self):
        main = tk.Frame(self, bg='#111'); main.pack(fill='both', expand=True)

        # Left: toolbar
        toolbar = tk.Frame(main, bg='#1a1a1a', width=200)
        toolbar.pack(side='left', fill='y', padx=2)
        toolbar.pack_propagate(False)

        tk.Label(toolbar,text='── PALETTE ──',bg='#1a1a1a',fg='#00ff44',
                 font=('Courier',9,'bold')).pack(pady=(8,2))

        # Tile palette
        for sym,char,color,label in TILE_TYPES:
            def make_tile_cmd(c=char): return lambda: self._set_tile_tool(c)
            btn=tk.Button(toolbar,text=f'{char}  {label}',bg='#222',fg=color,
                          font=('Courier',9),anchor='w',command=make_tile_cmd())
            btn.pack(fill='x',padx=4,pady=1)

        tk.Label(toolbar,text='── ENTITIES ──',bg='#1a1a1a',fg='#ffaa00',
                 font=('Courier',9,'bold')).pack(pady=(8,2))

        for sym,char,color,label in ENTITY_TYPES:
            def make_ent_cmd(s=sym,c=char,col=color): return lambda: self._set_entity_tool(s,c,col)
            btn=tk.Button(toolbar,text=f'{char}  {label}',bg='#222',fg=color,
                          font=('Courier',9),anchor='w',command=make_ent_cmd())
            btn.pack(fill='x',padx=4,pady=1)

        tk.Label(toolbar,text='── TOOLS ──',bg='#1a1a1a',fg='#aaaaaa',
                 font=('Courier',9,'bold')).pack(pady=(8,2))

        tk.Button(toolbar,text='Eraser',bg='#442222',fg='#ff6666',
                  command=lambda:self._set_erase_tool()).pack(fill='x',padx=4,pady=1)
        tk.Button(toolbar,text='Settings',bg='#222244',fg='#8888ff',
                  command=self._open_settings).pack(fill='x',padx=4,pady=1)
        tk.Button(toolbar,text='Sprite Editor',bg='#224422',fg='#44ff88',
                  command=self._open_sprite_editor).pack(fill='x',padx=4,pady=1)
        tk.Button(toolbar,text='Dialogue Editor',bg='#222244',fg='#aaaaff',
                  command=self._open_dialogue_editor).pack(fill='x',padx=4,pady=1)
        tk.Button(toolbar,text='Map Size',bg='#222',fg='#aaaaaa',
                  command=self._resize_map).pack(fill='x',padx=4,pady=1)

        tk.Label(toolbar,text='── SAVE/LOAD ──',bg='#1a1a1a',fg='#ffff44',
                 font=('Courier',9,'bold')).pack(pady=(8,2))
        tk.Button(toolbar,text='Save Cartridge',bg='#224422',fg='#00ff88',
                  font=('Courier',10,'bold'),command=self._save_cart).pack(fill='x',padx=4,pady=2)
        tk.Button(toolbar,text='Load Cartridge',bg='#442200',fg='#ffaa44',
                  command=self._load_cart).pack(fill='x',padx=4,pady=2)

        # Status bar
        self.status_var=tk.StringVar(value='Tool: tile (#)  |  Left-click paint  Right-click erase')
        tk.Label(toolbar,textvariable=self.status_var,bg='#1a1a1a',fg='#666666',
                 font=('Courier',8),wraplength=190).pack(side='bottom',pady=4)

        # Right: canvas with scrollbars
        canvas_frame=tk.Frame(main,bg='#111'); canvas_frame.pack(side='left',fill='both',expand=True)
        self.hscroll=tk.Scrollbar(canvas_frame,orient='horizontal')
        self.vscroll=tk.Scrollbar(canvas_frame,orient='vertical')
        self.hscroll.pack(side='bottom',fill='x')
        self.vscroll.pack(side='right',fill='y')
        self.cv=tk.Canvas(canvas_frame,bg='#222',cursor='crosshair',
                          xscrollcommand=self.hscroll.set,yscrollcommand=self.vscroll.set)
        self.cv.pack(fill='both',expand=True)
        self.hscroll.config(command=self.cv.xview)
        self.vscroll.config(command=self.cv.yview)
        cw=self.grid_w*CELL+40; ch=self.grid_h*CELL+40
        self.cv.config(scrollregion=(0,0,cw,ch))

        self.cv.bind('<Button-1>',      self._on_click)
        self.cv.bind('<B1-Motion>',     self._on_drag)
        self.cv.bind('<Button-3>',      self._on_rclick)
        self.cv.bind('<B3-Motion>',     self._on_rdrag)
        self.cv.bind('<Motion>',        self._on_hover)
        self.cv.bind('<MouseWheel>',    self._on_scroll)

    def _set_tile_tool(self, char):
        self.tool='tile'; self.selected_tile=char; self.selected_entity=None
        self.status_var.set(f'Tool: tile ({char})  |  Left=paint  Right=erase')

    def _set_entity_tool(self, sym, char, color):
        self.tool='entity'; self.selected_entity=(sym,char,color)
        self.status_var.set(f'Tool: entity ({sym})  |  Left=place  Right=remove')

    def _set_erase_tool(self):
        self.tool='erase'
        self.status_var.set('Tool: eraser  |  Left=erase tile+entity')

    def _canvas_to_grid(self, cx, cy):
        x=int(self.cv.canvasx(cx)//CELL)
        y=int(self.cv.canvasy(cy)//CELL)
        return x,y

    def _on_click(self, ev):
        x,y=self._canvas_to_grid(ev.x,ev.y)
        if not (0<=x<self.grid_w and 0<=y<self.grid_h): return
        self._apply_tool(x,y); self._redraw()

    def _on_drag(self, ev):
        x,y=self._canvas_to_grid(ev.x,ev.y)
        if not (0<=x<self.grid_w and 0<=y<self.grid_h): return
        if self.tool != 'entity': self._apply_tool(x,y); self._redraw()

    def _on_rclick(self, ev):
        x,y=self._canvas_to_grid(ev.x,ev.y)
        if not (0<=x<self.grid_w and 0<=y<self.grid_h): return
        key=f'{x},{y}'
        self.cart['grid'].pop(key,None)
        self.cart['entities']=[e for e in self.cart['entities'] if not(e['x']==x and e['y']==y)]
        self.cart['wall_weapons'].pop(key,None)
        self.cart['perks'].pop(key,None)
        self._redraw()

    def _on_rdrag(self, ev): self._on_rclick(ev)

    def _on_hover(self, ev):
        x,y=self._canvas_to_grid(ev.x,ev.y)
        if (x,y)!=(self.hover_x,self.hover_y):
            self.hover_x,self.hover_y=x,y

    def _on_scroll(self, ev):
        if ev.state & 4: self.cv.xview_scroll(int(-ev.delta/120),'units')
        else:            self.cv.yview_scroll(int(-ev.delta/120),'units')

    def _apply_tool(self, x, y):
        key=f'{x},{y}'
        if self.tool=='tile':
            if self.selected_tile==' ':
                self.cart['grid'].pop(key,None)
            else:
                self.cart['grid'][key]=self.selected_tile
        elif self.tool=='entity':
            sym,char,color=self.selected_entity
            # Remove existing entity at this position
            self.cart['entities']=[e for e in self.cart['entities'] if not(e['x']==x and e['y']==y)]
            # Special handling
            if sym=='wall_weapon':
                wid_str=simpledialog.askinteger('Wall Weapon','Weapon ID (1=Pistol 2=Shotgun 3=Chaingun 4=Rocket)',
                                                 initialvalue=2, parent=self)
                if wid_str: self.cart['wall_weapons'][key]=wid_str
            elif sym=='perk_machine':
                pname=simpledialog.askstring('Perk Machine',
                    'Perk name:\nJUGGERNOG / SPEEDCOLA / DOUBLETAP / STAMINUP / MULEKICK',
                    initialvalue='JUGGERNOG', parent=self)
                if pname: self.cart['perks'][key]=pname.upper()
            else:
                props={}
                if sym in VEHICLE_DEFS: props['vehicle_kind']=sym
                self.cart['entities'].append({'type':sym,'x':x,'y':y,'rotation':0,'props':props})
        elif self.tool=='erase':
            key=f'{x},{y}'
            self.cart['grid'].pop(key,None)
            self.cart['entities']=[e for e in self.cart['entities'] if not(e['x']==x and e['y']==y)]
            self.cart['wall_weapons'].pop(key,None)
            self.cart['perks'].pop(key,None)

    def _redraw(self):
        self.cv.delete('all')
        # Draw cells
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                key=f'{x},{y}'
                tile=self.cart['grid'].get(key,' ')
                x1=x*CELL; y1=y*CELL; x2=x1+CELL; y2=y1+CELL
                # Color by tile
                if tile=='#': fill='#886644'; outline='#aa8866'
                elif tile=='D': fill='#2a6e2a'; outline='#44aa44'
                elif tile=='W': fill='#2a2a8e'; outline='#4466cc'
                elif tile=='T': fill='#664400'; outline='#cc8800'
                else: fill='#1a1a1a'; outline='#2a2a2a'
                self.cv.create_rectangle(x1,y1,x2,y2,fill=fill,outline=outline)
                # Check wall weapons
                if key in self.cart.get('wall_weapons',{}):
                    wid=self.cart['wall_weapons'][key]
                    self.cv.create_text(x1+CELL//2,y1+CELL//2,text=f'W{wid}',fill='#ff8800',font=('Courier',7,'bold'))
                if key in self.cart.get('perks',{}):
                    pname=self.cart['perks'][key]
                    self.cv.create_text(x1+CELL//2,y1+CELL//2,text=pname[:3],fill='#00ccff',font=('Courier',6,'bold'))

        # Draw entities
        ent_colors={'player_start':'#00ff88','zombie':'#ccaa88','imp':'#cc5522','demon':'#cc66aa',
                    'health':'#44aaff','ammo':'#ffcc00','mystery_box':'#ffdd00','npc':'#aaffaa',
                    'teleporter':'#ff88ff','checkpoint':'#ffffff','CAR':'#cc8800','TANK':'#448844',
                    'BIKE':'#cc3300','electric_trap':'#ffee00','perk_machine':'#00ccff','wall_weapon':'#ff8800'}
        ent_chars={'player_start':'P','zombie':'Z','imp':'I','demon':'N','health':'h','ammo':'+',
                   'mystery_box':'?','npc':'C','teleporter':'T','checkpoint':'K','CAR':'V',
                   'TANK':'V','BIKE':'V','electric_trap':'E','perk_machine':'R','wall_weapon':'W'}
        for ent in self.cart.get('entities',[]):
            ex,ey=ent['x'],ent['y']
            etype=ent.get('type','?')
            x1=ex*CELL+2; y1=ey*CELL+2; x2=x1+CELL-4; y2=y1+CELL-4
            col=ent_colors.get(etype,'#888888')
            self.cv.create_oval(x1,y1,x2,y2,fill=col,outline='#ffffff',width=1)
            char=ent_chars.get(etype,'?')
            self.cv.create_text(ex*CELL+CELL//2,ey*CELL+CELL//2,text=char,fill='#000000',font=('Courier',10,'bold'))

        # Grid coords every 5 cells
        for x in range(0,self.grid_w,5):
            self.cv.create_text(x*CELL+2,2,text=str(x),fill='#444444',font=('Courier',7),anchor='nw')
        for y in range(0,self.grid_h,5):
            self.cv.create_text(2,y*CELL+2,text=str(y),fill='#444444',font=('Courier',7),anchor='nw')

        # Hover highlight
        if 0<=self.hover_x<self.grid_w and 0<=self.hover_y<self.grid_h:
            hx=self.hover_x*CELL; hy=self.hover_y*CELL
            self.cv.create_rectangle(hx,hy,hx+CELL,hy+CELL,fill='',outline='#00ff88',width=2)

    def _open_settings(self):
        win=tk.Toplevel(self); win.title('Map Settings'); win.configure(bg='#111')
        settings=self.cart.setdefault('settings',DEFAULT_CARTRIDGE['settings'].copy())
        fields=[
            ('Map Name',          'name',           self.cart),
            ('Wave Base Enemies', 'wave_base',       settings),
            ('Wave Scale/Round',  'wave_scale',      settings),
            ('HP Scale/Round',    'health_scale',    settings),
            ('Player HP',         'player_hp',       settings),
            ('Power Active (0/1)','power_active',    settings),
        ]
        entries={}
        for i,(label,key,d) in enumerate(fields):
            tk.Label(win,text=label,bg='#111',fg='#aaaaaa',font=('Courier',10)).grid(row=i,column=0,padx=8,pady=4,sticky='w')
            var=tk.StringVar(value=str(d.get(key,'')))
            ent=tk.Entry(win,textvariable=var,bg='#222',fg='white',font=('Courier',10))
            ent.grid(row=i,column=1,padx=8,pady=4)
            entries[(key,id(d))]=(var,d,key)

        def save_settings():
            for (key,did),(var,d,k) in entries.items():
                val=var.get()
                try:
                    if '.' in val: d[k]=float(val)
                    elif val.lower() in ('true','1'): d[k]=True
                    elif val.lower() in ('false','0'): d[k]=False
                    else: d[k]=int(val)
                except ValueError: d[k]=val
            win.destroy()

        tk.Button(win,text='Save',command=save_settings,bg='#224422',fg='#00ff44',font=('Courier',10,'bold')).grid(row=len(fields),column=0,columnspan=2,pady=8)

    def _open_sprite_editor(self):
        sprites=self.cart.setdefault('sprites',{})
        name=simpledialog.askstring('Sprite Name','Enter sprite name:',parent=self) or 'sprite1'
        initial=sprites.get(name,'')
        def on_save(n,b64): sprites[n]=b64; self.status_var.set(f'Sprite "{n}" saved.')
        SpriteEditor(self, on_save=on_save, name=name, initial_b64=initial)

    def _open_dialogue_editor(self):
        entities_with_ids=[(i,e) for i,e in enumerate(self.cart.get('entities',[]))
                           if e.get('type')=='npc']
        if not entities_with_ids:
            messagebox.showinfo('Dialogue','No NPC entities placed on the map yet.',parent=self); return
        dialogue=self.cart.setdefault('dialogue',{})
        win=tk.Toplevel(self); win.title('TTS Dialogue Editor'); win.configure(bg='#111')
        for i,(eid,ent) in enumerate(entities_with_ids):
            tk.Label(win,text=f'NPC #{eid} at ({ent["x"]},{ent["y"]})',
                     bg='#111',fg='#aaffaa',font=('Courier',10,'bold')).grid(row=i*2,column=0,padx=8,pady=2,sticky='w')
            var=tk.StringVar(value='; '.join(dialogue.get(str(eid),[])))
            ent2=tk.Entry(win,textvariable=var,width=50,bg='#222',fg='white',font=('Courier',9))
            ent2.grid(row=i*2+1,column=0,padx=8,pady=2)
            def save_dlg(v=var,eid2=eid):
                lines=[l.strip() for l in v.get().split(';') if l.strip()]
                dialogue[str(eid2)]=lines
            win.bind('<FocusOut>',lambda e:save_dlg())
            ent2.bind('<Return>',lambda e,f=save_dlg:f())

        tk.Label(win,text='(Separate lines with semicolons. Lines are spoken via TTS in Play Mode.)',
                 bg='#111',fg='#666666',font=('Courier',8)).grid(row=len(entities_with_ids)*2,column=0,padx=8,pady=4)
        tk.Button(win,text='Done',command=win.destroy,bg='#224422',fg='#00ff44').grid(
            row=len(entities_with_ids)*2+1,column=0,pady=8)

    def _resize_map(self):
        w=simpledialog.askinteger('Map Width','Width (10-60):',initialvalue=self.grid_w,parent=self)
        h=simpledialog.askinteger('Map Height','Height (8-40):',initialvalue=self.grid_h,parent=self)
        if w and h:
            w=max(10,min(60,w)); h=max(8,min(40,h))
            self.grid_w=w; self.grid_h=h
            self.cart['width']=w; self.cart['height']=h
            cw=w*CELL+40; ch=h*CELL+40
            self.cv.config(scrollregion=(0,0,cw,ch))
            self._redraw()

    def _save_cart(self):
        path=filedialog.asksaveasfilename(parent=self,title='Save Cartridge',
                                          defaultextension='.json',
                                          filetypes=[('DoomCraft Cartridge','*.json')])
        if not path: return
        self.cart['width']=self.grid_w; self.cart['height']=self.grid_h
        save_cartridge(self.cart, path)
        sig=self.cart['seed_signature']
        messagebox.showinfo('Saved',f'Cartridge saved!\nSeed: {sig[:16]}...\nThe dot sings.  .-',parent=self)
        if self.on_save: self.on_save(self.cart, path)

    def _load_cart(self):
        path=filedialog.askopenfilename(parent=self,title='Load Cartridge',
                                         filetypes=[('DoomCraft Cartridge','*.json')])
        if not path: return
        try:
            self.cart=load_cartridge(path)
            self.grid_w=self.cart.get('width',20)
            self.grid_h=self.cart.get('height',15)
            cw=self.grid_w*CELL+40; ch=self.grid_h*CELL+40
            self.cv.config(scrollregion=(0,0,cw,ch))
            self._redraw()
            messagebox.showinfo('Loaded',f'Cartridge loaded: {self.cart.get("name","?")}',parent=self)
        except Exception as e:
            messagebox.showerror('Error',f'Load failed: {e}',parent=self)

# =============================================================================
# §15  LAUNCHER WINDOW  (main entry point)
# =============================================================================
LAUNCHER_ART = """\
██████╗  ██████╗  ██████╗ ███╗   ███╗ ██████╗██████╗  █████╗ ███████╗████████╗
██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝
██║  ██║██║   ██║██║   ██║██╔████╔██║██║     ██████╔╝███████║█████╗     ██║
██║  ██║██║   ██║██║   ██║██║╚██╔╝██║██║     ██╔══██╗██╔══██║██╔══╝     ██║
██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║╚██████╗██║  ██║██║  ██║██║        ██║
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝
            MOD SDK v1.0  ·  PURE PYTHON  ·  "The dot sings.  .-"
"""

class Launcher:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title('DoomCraft Mod SDK — Launcher')
        self.root.configure(bg='#000')
        self.root.resizable(False,False)
        self.active_cart=None
        self.active_cart_path=None
        self.skill=1
        self._build()

    def _build(self):
        root=self.root
        # ASCII art banner
        tk.Label(root,text=LAUNCHER_ART,bg='#000',fg='#00ff44',
                 font=('Courier',8,'bold'),justify='left').pack(padx=12,pady=(12,4))

        # Cartridge display
        self.cart_var=tk.StringVar(value='No cartridge loaded — start fresh or load one')
        tk.Label(root,textvariable=self.cart_var,bg='#000',fg='#888888',
                 font=('Courier',9)).pack(pady=2)

        # Skill selector
        skill_frame=tk.Frame(root,bg='#000'); skill_frame.pack(pady=4)
        tk.Label(skill_frame,text='SKILL LEVEL:',bg='#000',fg='#aaaaaa',font=('Courier',10,'bold')).pack(side='left',padx=4)
        self.skill_var=tk.IntVar(value=1)
        for i,(name,_,_) in SKILL_LEVELS.items():
            colors=['#44ff44','#ffcc00','#ff8800','#ff4444']
            tk.Radiobutton(skill_frame,text=name,variable=self.skill_var,value=i,
                           bg='#000',fg=colors[i],selectcolor='#111',
                           font=('Courier',10,'bold'),
                           command=lambda:setattr(self,'skill',self.skill_var.get())).pack(side='left',padx=6)

        # Cartridge buttons
        cart_frame=tk.Frame(root,bg='#000'); cart_frame.pack(pady=4)
        tk.Button(cart_frame,text='⟲ Load Cartridge',bg='#222244',fg='#8888ff',
                  font=('Courier',11),width=20,command=self._load_cart).pack(side='left',padx=6)
        tk.Button(cart_frame,text='New Cartridge',bg='#222',fg='#888888',
                  font=('Courier',11),width=16,command=self._new_cart).pack(side='left',padx=6)
        tk.Button(cart_frame,text='■ Start Menu',bg='#002211',fg='#00ff88',
                  font=('Courier',11,'bold'),width=14,command=self._open_start).pack(side='left',padx=6)

        # EDIT / PLAY
        btn_frame=tk.Frame(root,bg='#000'); btn_frame.pack(pady=16)
        tk.Button(btn_frame,
                  text='  ⚒  EDIT MODE\n     (Forge)',
                  bg='#1a1a3a',fg='#8888ff',
                  font=('Courier',14,'bold'),width=22,height=4,
                  relief='raised',bd=3,
                  command=self._launch_edit).pack(side='left',padx=12)
        tk.Button(btn_frame,
                  text='  ► PLAY MODE\n     LAUNCH',
                  bg='#1a3a1a',fg='#00ff44',
                  font=('Courier',14,'bold'),width=22,height=4,
                  relief='raised',bd=3,
                  command=self._launch_play).pack(side='left',padx=12)

        # FlowScript tester
        fs_frame=tk.Frame(root,bg='#000'); fs_frame.pack(fill='x',padx=12,pady=4)
        tk.Label(fs_frame,text='FlowScript Console:',bg='#000',fg='#00aa44',
                 font=('Courier',9,'bold')).pack(side='left')
        self.fs_var=tk.StringVar()
        fs_entry=tk.Entry(fs_frame,textvariable=self.fs_var,bg='#0a0a0a',fg='#00ff88',
                          font=('Courier',10),insertbackground='#00ff88',width=40)
        fs_entry.pack(side='left',padx=4)
        fs_entry.bind('<Return>',self._run_flowscript)
        tk.Button(fs_frame,text='Run .-',bg='#003300',fg='#00ff88',
                  font=('Courier',9),command=self._run_flowscript).pack(side='left',padx=2)

        self.fs_out=tk.Text(root,height=4,bg='#050a05',fg='#00ff88',
                            font=('Courier',9),state='disabled',bd=0,
                            highlightthickness=1,highlightbackground='#003300')
        self.fs_out.pack(fill='x',padx=12,pady=(0,4))

        # Bottom info
        tk.Label(root,text='RIP AND TEAR  ·  Left-click grid to paint  ·  ~ opens dev console in Play Mode',
                 bg='#000',fg='#333333',font=('Courier',8)).pack(pady=(0,8))

    def _new_cart(self):
        self.active_cart={k:(v.copy() if isinstance(v,dict) else v) for k,v in DEFAULT_CARTRIDGE.items()}
        self.active_cart['grid']={}
        self.active_cart['entities']=[]
        self.active_cart_path=None
        self.cart_var.set('New cartridge (unsaved)')

    def _load_cart(self):
        path=filedialog.askopenfilename(title='Load Cartridge',
                                         filetypes=[('DoomCraft Cartridge','*.json')])
        if not path: return
        try:
            self.active_cart=load_cartridge(path)
            self.active_cart_path=path
            self.cart_var.set(f'Loaded: {os.path.basename(path)}  [seed {self.active_cart["seed_signature"][:12]}...]')
        except Exception as e:
            messagebox.showerror('Error',f'Cannot load: {e}')

    def _launch_edit(self):
        if not self.active_cart: self._new_cart()
        def on_cart_save(cart, path):
            self.active_cart=cart; self.active_cart_path=path
            self.cart_var.set(f'Loaded: {os.path.basename(path)}  [seed {cart["seed_signature"][:12]}...]')
        EditMode(self.root, cart=self.active_cart, on_save=on_cart_save)

    def _launch_play(self):
        if not self.active_cart:
            result=messagebox.askyesno('No Cartridge',
                'No cartridge loaded.\nLaunch with the default demo map?')
            if result: self._make_demo_cart()
            else: return

        if auto_install_deps():
            skill=self.skill_var.get()
            PlayModeWindow(self.root, self.active_cart, skill=skill)
        else:
            messagebox.showerror('Dependency Error',
                'Could not install pygame/pyttsx3.\n'
                'Play Mode runs on the tkinter raycaster (no pygame required).\n'
                'Launching anyway...')
            skill=self.skill_var.get()
            PlayModeWindow(self.root, self.active_cart, skill=skill)

    def _make_demo_cart(self):
        """Generate a compact demo map so the user can jump in immediately."""
        cart={k:(v.copy() if isinstance(v,dict) else v) for k,v in DEFAULT_CARTRIDGE.items()}
        cart['name']='Demo — Nacht Der Untoten'
        cart['width']=18; cart['height']=14
        cart['grid']={}; cart['entities']=[]; cart['wall_weapons']={}; cart['perks']={}
        # Border walls
        for x in range(18):
            cart['grid'][f'{x},0']='#'
            cart['grid'][f'{x},13']='#'
        for y in range(14):
            cart['grid'][f'0,{y}']='#'
            cart['grid'][f'17,{y}']='#'
        # Inner rooms
        for x in range(5,13):
            cart['grid'][f'{x},5']='#'
            cart['grid'][f'{x},9']='#'
        for y in range(5,10):
            cart['grid'][f'5,{y}']='#'
            cart['grid'][f'12,{y}']='#'
        # Doors
        cart['grid']['8,5']='D'; cart['grid']['8,9']='D'
        cart['grid']['5,7']='D'; cart['grid']['12,7']='D'
        # Player start
        cart['entities'].append({'type':'player_start','x':2,'y':2,'rotation':0,'props':{}})
        # Perks
        cart['perks']['2,10']='JUGGERNOG'
        cart['perks']['14,2']='SPEEDCOLA'
        cart['perks']['14,10']='DOUBLETAP'
        # Wall weapons
        cart['wall_weapons']['1,5']='2'
        cart['wall_weapons']['1,9']='3'
        # Mystery box
        cart['entities'].append({'type':'mystery_box','x':9,'y':7,'rotation':0,'props':{}})
        # Electric traps
        cart['entities'].append({'type':'electric_trap','x':6,'y':7,'rotation':0,'props':{}})
        cart['entities'].append({'type':'electric_trap','x':11,'y':7,'rotation':0,'props':{}})
        # Vehicle
        cart['entities'].append({'type':'CAR','x':3,'y':10,'rotation':0,'props':{'vehicle_kind':'CAR'}})
        # NPC
        cart['entities'].append({'type':'npc','x':15,'y':2,'rotation':0,'props':{}})
        cart['dialogue']['4']=['Welcome, marine.','Survive the waves.','The dot sings.']
        # Power is off (Pack-a-Punch locked)
        cart['settings']['power_active']=False
        cart['settings']['wave_base']=6
        self.active_cart=cart
        self.active_cart_path=None
        cart['seed_signature']=cartridge_hash(cart)
        _ENTROPY.seed_from_hash(cart['seed_signature'])
        self.cart_var.set('Demo: Nacht Der Untoten [built-in]')

    def _run_flowscript(self, ev=None):
        code=self.fs_var.get().strip()
        if not code: return
        fs=FlowScript(tone_fn=play_tone)
        try:
            out=fs.run(code)
            self.fs_out.config(state='normal')
            self.fs_out.delete('1.0','end')
            self.fs_out.insert('end','\n'.join(out) if out else f'> {code} .-')
            self.fs_out.config(state='disabled')
        except Exception as e:
            self.fs_out.config(state='normal')
            self.fs_out.delete('1.0','end')
            self.fs_out.insert('end',f'ERROR: {e} .-')
            self.fs_out.config(state='disabled')


    def _open_start(self):
        StartMenu(self)
    def run(self):
        self.root.mainloop()

# =============================================================================
# §17  SFX GENERATOR  (waveform synth + ADSR, base64 WAV export to cartridge)
# =============================================================================
# // S_StartSound.  A tkinter UI around the existing _wav() audio primitive.
class SFXGenerator:
    WAVES = ('sine','square','saw','triangle','noise')
    def __init__(self, parent, cart=None):
        self.cart=cart
        self.win=tk.Toplevel(parent); self.win.title('SFX Generator'); self.win.configure(bg='#000')
        self.win.resizable(False,False)
        self.freq=tk.IntVar(value=440); self.dur=tk.DoubleVar(value=0.4)
        self.wave=tk.StringVar(value='square')
        self.atk=tk.DoubleVar(value=0.02); self.dec=tk.DoubleVar(value=0.08)
        self.sus=tk.DoubleVar(value=0.6);  self.rel=tk.DoubleVar(value=0.15)
        self.vol=tk.DoubleVar(value=0.3)
        self._last_wav=None
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='◊ SFX GENERATOR ◊',bg='#000',fg='#ff8800',
                 font=('Courier',13,'bold')).pack(pady=6)
        # Waveform radio
        wf=tk.Frame(w,bg='#000'); wf.pack(pady=2)
        tk.Label(wf,text='Waveform:',bg='#000',fg='#aaa',font=('Courier',10)).pack(side='left',padx=4)
        for wname in self.WAVES:
            tk.Radiobutton(wf,text=wname,variable=self.wave,value=wname,
                           bg='#000',fg='#ff8800',selectcolor='#111',
                           font=('Courier',9)).pack(side='left',padx=2)
        # Frequency / Duration / Volume
        self._slider(w,'Freq (Hz)',self.freq,40,2000,1)
        self._slider(w,'Duration (s)',self.dur,0.05,3.0,0.05)
        self._slider(w,'Volume',self.vol,0.0,1.0,0.01)
        # ADSR
        adsr=tk.LabelFrame(w,text=' ADSR Envelope ',bg='#000',fg='#ff8800',
                           font=('Courier',10,'bold'))
        adsr.pack(fill='x',padx=8,pady=6)
        self._slider(adsr,'Attack',self.atk,0.0,1.0,0.01)
        self._slider(adsr,'Decay',self.dec,0.0,1.0,0.01)
        self._slider(adsr,'Sustain',self.sus,0.0,1.0,0.01)
        self._slider(adsr,'Release',self.rel,0.0,1.0,0.01)
        # Buttons
        bf=tk.Frame(w,bg='#000'); bf.pack(pady=8)
        tk.Button(bf,text='▶ Preview',bg='#113311',fg='#00ff44',font=('Courier',10,'bold'),
                  width=12,command=self._preview).pack(side='left',padx=4)
        tk.Button(bf,text='💾 Save to Cartridge',bg='#331111',fg='#ff8844',font=('Courier',10,'bold'),
                  width=22,command=self._save_to_cart).pack(side='left',padx=4)
        tk.Button(bf,text='Close',bg='#222',fg='#aaa',font=('Courier',10),
                  width=8,command=self.win.destroy).pack(side='left',padx=4)
        # Status
        self.status=tk.Label(w,text='Tweak params → Preview → Save .-',
                             bg='#000',fg='#666',font=('Courier',9))
        self.status.pack(pady=(0,6))

    def _slider(self, parent, label, var, lo, hi, step):
        f=tk.Frame(parent,bg='#000'); f.pack(fill='x',padx=10,pady=1)
        tk.Label(f,text=f'{label}:',bg='#000',fg='#aaa',font=('Courier',9),
                 width=12,anchor='w').pack(side='left')
        tk.Scale(f,from_=lo,to=hi,resolution=step,orient='horizontal',
                 variable=var,bg='#111',fg='#ff8800',troughcolor='#222',
                 highlightthickness=0,length=260,font=('Courier',8),
                 showvalue=True).pack(side='left',fill='x',expand=True)

    def _synth(self):
        # // Generate raw samples using selected waveform with ADSR envelope.
        freq=self.freq.get(); dur=float(self.dur.get()); wave=self.wave.get()
        vol=float(self.vol.get())
        n=int(SR*dur)
        samps=[0.0]*n
        for i in range(n):
            t=i/SR; phase=(freq*t)%1.0
            if wave=='sine':     s=math.sin(TAU*phase)
            elif wave=='square': s=1.0 if phase<0.5 else -1.0
            elif wave=='saw':    s=2.0*phase-1.0
            elif wave=='triangle': s=4.0*abs(phase-0.5)-1.0
            elif wave=='noise':  s=_RNG.uniform(-1,1)
            else:                s=math.sin(TAU*phase)
            samps[i]=s*vol
        # ADSR envelope
        atk=max(1,int(self.atk.get()*SR))
        dec=max(1,int(self.dec.get()*SR))
        rel=max(1,int(self.rel.get()*SR))
        sus=max(0.0,min(1.0,float(self.sus.get())))
        for i in range(n):
            if i<atk: env=i/atk
            elif i<atk+dec:
                f=(i-atk)/dec; env=1.0-(1.0-sus)*f
            elif i>n-rel:
                f=(n-i)/rel; env=sus*f
            else: env=sus
            samps[i]*=env
        return _wav(samps)

    def _preview(self):
        self._last_wav=self._synth()
        try: _play_wav(self._last_wav)
        except Exception as e: self.status.config(text=f'Preview err: {e}')
        self.status.config(text=f'Previewed {len(self._last_wav)} bytes .-')

    def _save_to_cart(self):
        if self.cart is None:
            messagebox.showwarning('No cartridge','Load or create a cartridge first.'); return
        if not self._last_wav: self._last_wav=self._synth()
        name=simpledialog.askstring('SFX name','Name for this sound in the cartridge?',parent=self.win)
        if not name: return
        import base64
        self.cart.setdefault('sfx',{})[name]=base64.b64encode(self._last_wav).decode('ascii')
        self.status.config(text=f'Saved "{name}" to cartridge.sfx .-')


# =============================================================================
# §18  MUSIC GENERATOR  (procedural ambient drone + melody, GUI around _make_drone)
# =============================================================================
# // P_MusicSetup.  Wraps the existing _make_drone synth with user-facing controls.
class MusicGenerator:
    KEYS = {'C':65.41,'D':73.42,'E':82.41,'F':87.31,'G':98.00,'A':110.00,'B':123.47}
    def __init__(self, parent, cart=None):
        self.cart=cart
        self.win=tk.Toplevel(parent); self.win.title('Music Generator (Pyamby)')
        self.win.configure(bg='#000'); self.win.resizable(False,False)
        self.root_key=tk.StringVar(value='A')
        self.dur=tk.DoubleVar(value=8.0)
        self.seed=tk.IntVar(value=42)
        self.vol=tk.DoubleVar(value=0.15)
        self._last_wav=None
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='♪ MUSIC GENERATOR ♪',bg='#000',fg='#44aaff',
                 font=('Courier',13,'bold')).pack(pady=6)
        tk.Label(w,text='Procedural ambient drone (Pyamby-style).\nRoot note → base freq.  Seed → harmonic variations.',
                 bg='#000',fg='#666',font=('Courier',9),justify='left').pack(pady=2)
        # Key picker
        kf=tk.Frame(w,bg='#000'); kf.pack(pady=4)
        tk.Label(kf,text='Root key:',bg='#000',fg='#aaa',font=('Courier',10)).pack(side='left',padx=4)
        for k in self.KEYS:
            tk.Radiobutton(kf,text=k,variable=self.root_key,value=k,
                           bg='#000',fg='#44aaff',selectcolor='#111',
                           font=('Courier',9,'bold')).pack(side='left',padx=1)
        # Sliders
        self._slider(w,'Duration (s)',self.dur,2.0,30.0,0.5)
        self._slider(w,'Seed',self.seed,0,255,1)
        self._slider(w,'Volume',self.vol,0.0,0.3,0.005)
        # Buttons
        bf=tk.Frame(w,bg='#000'); bf.pack(pady=8)
        tk.Button(bf,text='▶ Preview',bg='#113311',fg='#00ff44',font=('Courier',10,'bold'),
                  width=12,command=self._preview).pack(side='left',padx=4)
        tk.Button(bf,text='💾 Save to Cartridge',bg='#111133',fg='#4488ff',font=('Courier',10,'bold'),
                  width=22,command=self._save_to_cart).pack(side='left',padx=4)
        tk.Button(bf,text='Close',bg='#222',fg='#aaa',font=('Courier',10),
                  width=8,command=self.win.destroy).pack(side='left',padx=4)
        self.status=tk.Label(w,text='Preview or save .-',
                             bg='#000',fg='#666',font=('Courier',9))
        self.status.pack(pady=(0,6))

    def _slider(self, parent, label, var, lo, hi, step):
        f=tk.Frame(parent,bg='#000'); f.pack(fill='x',padx=10,pady=1)
        tk.Label(f,text=f'{label}:',bg='#000',fg='#aaa',font=('Courier',9),
                 width=14,anchor='w').pack(side='left')
        tk.Scale(f,from_=lo,to=hi,resolution=step,orient='horizontal',
                 variable=var,bg='#111',fg='#44aaff',troughcolor='#222',
                 highlightthickness=0,length=260,font=('Courier',8)).pack(side='left',fill='x',expand=True)

    def _synth(self):
        base=self.KEYS[self.root_key.get()]
        return _make_drone(base, wave_seed=self.seed.get(),
                           dur=float(self.dur.get()), vol=float(self.vol.get()))

    def _preview(self):
        self._last_wav=self._synth()
        try: _play_wav(self._last_wav)
        except Exception as e: self.status.config(text=f'Preview err: {e}')
        self.status.config(text=f'Previewed {len(self._last_wav)} bytes .-')

    def _save_to_cart(self):
        if self.cart is None:
            messagebox.showwarning('No cartridge','Load or create a cartridge first.'); return
        if not self._last_wav: self._last_wav=self._synth()
        name=simpledialog.askstring('Track name','Name for this music track?',parent=self.win)
        if not name: return
        import base64
        self.cart.setdefault('music',{})[name]=base64.b64encode(self._last_wav).decode('ascii')
        self.status.config(text=f'Saved "{name}" to cartridge.music .-')


# =============================================================================
# §19  DIALOGUE & SCRIPTING EDITOR  (NPC lines + attached FlowScript, TTS test)
# =============================================================================
# // P_DialogTalk.  Edit per-entity dialogue lines and an optional FlowScript hook.
class DialogueEditor:
    def __init__(self, parent, cart=None):
        self.cart=cart
        self.win=tk.Toplevel(parent); self.win.title('Dialogue & Scripting Editor')
        self.win.configure(bg='#000'); self.win.geometry('720x520')
        self.current_id=None
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='✎  DIALOGUE & SCRIPTING  ✎',bg='#000',fg='#ffcc44',
                 font=('Courier',13,'bold')).pack(pady=4)
        # Two-pane: left = entity list, right = editor
        body=tk.Frame(w,bg='#000'); body.pack(fill='both',expand=True,padx=6,pady=4)
        left=tk.Frame(body,bg='#000'); left.pack(side='left',fill='y',padx=(0,6))
        tk.Label(left,text='NPC entities:',bg='#000',fg='#ffcc44',
                 font=('Courier',10,'bold')).pack(anchor='w')
        self.listbox=tk.Listbox(left,bg='#0a0a0a',fg='#ffcc44',font=('Courier',10),
                                selectbackground='#553300',width=22,height=20,bd=0,
                                highlightthickness=1,highlightbackground='#553300')
        self.listbox.pack(fill='y',expand=True)
        self.listbox.bind('<<ListboxSelect>>',self._on_select)
        tk.Button(left,text='Refresh',bg='#222',fg='#aaa',font=('Courier',9),
                  command=self._refresh).pack(fill='x',pady=2)

        right=tk.Frame(body,bg='#000'); right.pack(side='left',fill='both',expand=True)
        tk.Label(right,text='Dialogue lines (one per line):',bg='#000',fg='#aaa',
                 font=('Courier',10)).pack(anchor='w')
        self.dialog_txt=tk.Text(right,height=10,bg='#0a0a0a',fg='#ffcc44',
                                font=('Courier',10),bd=0,insertbackground='#ffcc44',
                                highlightthickness=1,highlightbackground='#553300')
        self.dialog_txt.pack(fill='x',pady=2)
        tk.Label(right,text='Attached FlowScript (runs on interact):',bg='#000',fg='#aaa',
                 font=('Courier',10)).pack(anchor='w',pady=(6,0))
        self.script_txt=tk.Text(right,height=8,bg='#0a0a0a',fg='#00ff88',
                                font=('Courier',10),bd=0,insertbackground='#00ff88',
                                highlightthickness=1,highlightbackground='#003300')
        self.script_txt.pack(fill='x',pady=2)
        # Action buttons
        bf=tk.Frame(right,bg='#000'); bf.pack(pady=6)
        tk.Button(bf,text='▶ Test TTS',bg='#332211',fg='#ffcc44',font=('Courier',10,'bold'),
                  width=12,command=self._test_tts).pack(side='left',padx=4)
        tk.Button(bf,text='▶ Test Script',bg='#113311',fg='#00ff44',font=('Courier',10,'bold'),
                  width=12,command=self._test_script).pack(side='left',padx=4)
        tk.Button(bf,text='💾 Save',bg='#111133',fg='#4488ff',font=('Courier',10,'bold'),
                  width=10,command=self._save).pack(side='left',padx=4)
        tk.Button(bf,text='Close',bg='#222',fg='#aaa',font=('Courier',10),
                  width=8,command=self.win.destroy).pack(side='left',padx=4)
        self.status=tk.Label(w,text='Select an NPC entity to edit its dialogue .-',
                             bg='#000',fg='#666',font=('Courier',9))
        self.status.pack(pady=2)
        self._refresh()

    def _refresh(self):
        self.listbox.delete(0,'end')
        if not self.cart: return
        for idx,ent in enumerate(self.cart.get('entities',[])):
            if ent.get('type')=='npc':
                label=f'#{idx} @({ent["x"]},{ent["y"]})'
                self.listbox.insert('end',label)

    def _on_select(self, ev=None):
        sel=self.listbox.curselection()
        if not sel or not self.cart: return
        label=self.listbox.get(sel[0])
        idx=int(label[1:label.index(' ')])
        self.current_id=idx
        dialogue=self.cart.get('dialogue',{}).get(str(idx),[])
        self.dialog_txt.delete('1.0','end'); self.dialog_txt.insert('1.0','\n'.join(dialogue))
        # FlowScript stored under scripts[str(idx)]
        script=self.cart.get('scripts',{}).get(str(idx),'')
        self.script_txt.delete('1.0','end'); self.script_txt.insert('1.0',script)
        self.status.config(text=f'Editing NPC #{idx} .-')

    def _test_tts(self):
        lines=self.dialog_txt.get('1.0','end').strip().splitlines()
        if not lines: self.status.config(text='No lines to speak .-'); return
        init_tts()
        for l in lines: speak(l)
        self.status.config(text=f'Spoke {len(lines)} lines .-')

    def _test_script(self):
        code=self.script_txt.get('1.0','end').strip()
        if not code: self.status.config(text='No script .-'); return
        fs=FlowScript(tone_fn=play_tone)
        try:
            out=fs.run(code)
            messagebox.showinfo('Script Output','\n'.join(out) if out else '(no output)',parent=self.win)
            self.status.config(text=f'Script ran: {len(out)} lines .-')
        except Exception as e:
            messagebox.showerror('Script Error',str(e),parent=self.win)

    def _save(self):
        if self.current_id is None or not self.cart:
            self.status.config(text='Nothing selected .-'); return
        lines=[l for l in self.dialog_txt.get('1.0','end').strip().splitlines() if l.strip()]
        script=self.script_txt.get('1.0','end').strip()
        self.cart.setdefault('dialogue',{})[str(self.current_id)]=lines
        self.cart.setdefault('scripts',{})[str(self.current_id)]=script
        self.status.config(text=f'Saved NPC #{self.current_id} .-')


# =============================================================================
# §20  CAMPAIGN SEQUENCER  (string cartridges together into .campaign files)
# =============================================================================
# // G_InitNew.  Ordered list of cartridges played in sequence.
class CampaignEditor:
    def __init__(self, parent):
        self.win=tk.Toplevel(parent); self.win.title('Campaign Sequencer')
        self.win.configure(bg='#000'); self.win.geometry('620x420')
        self.cart_paths=[]        # ordered list
        self.meta={'name':'Untitled Campaign','transitions':'linear'}
        self.campaign_path=None
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='⛛  CAMPAIGN SEQUENCER  ⛛',bg='#000',fg='#ff44cc',
                 font=('Courier',13,'bold')).pack(pady=4)
        body=tk.Frame(w,bg='#000'); body.pack(fill='both',expand=True,padx=8,pady=4)
        # List
        self.listbox=tk.Listbox(body,bg='#0a0a0a',fg='#ff44cc',font=('Courier',10),
                                selectbackground='#550033',bd=0,
                                highlightthickness=1,highlightbackground='#550033',
                                height=16,width=55)
        self.listbox.pack(side='left',fill='both',expand=True)
        ctl=tk.Frame(body,bg='#000'); ctl.pack(side='left',fill='y',padx=6)
        for lbl,cmd,color in [
            ('+ Add Cartridge', self._add, '#113311'),
            ('Remove',          self._remove,'#331111'),
            ('▲ Up',            self._move_up,'#1a1a1a'),
            ('▼ Down',          self._move_down,'#1a1a1a'),
            ('Name…',           self._rename,'#1a1a1a'),
            ('💾 Save',         self._save,'#111133'),
            ('⟲ Load',          self._load,'#111133'),
            ('Close',           self.win.destroy,'#222'),
        ]:
            tk.Button(ctl,text=lbl,bg=color,fg='#ccc',font=('Courier',10,'bold'),
                      width=16,command=cmd).pack(pady=2)
        self.status=tk.Label(w,text='Empty campaign.  Add cartridges to build .-',
                             bg='#000',fg='#666',font=('Courier',9))
        self.status.pack(pady=2)

    def _refresh(self):
        self.listbox.delete(0,'end')
        for i,p in enumerate(self.cart_paths):
            self.listbox.insert('end',f'{i+1:>2}. {os.path.basename(p)}')
        self.status.config(text=f'{self.meta["name"]}  —  {len(self.cart_paths)} levels .-')

    def _add(self):
        paths=filedialog.askopenfilenames(title='Add cartridges',
                                           filetypes=[('Cartridge','*.json')],parent=self.win)
        for p in paths: self.cart_paths.append(p)
        self._refresh()

    def _remove(self):
        sel=self.listbox.curselection()
        if not sel: return
        del self.cart_paths[sel[0]]; self._refresh()

    def _move_up(self):
        sel=self.listbox.curselection()
        if not sel or sel[0]==0: return
        i=sel[0]; self.cart_paths[i-1],self.cart_paths[i]=self.cart_paths[i],self.cart_paths[i-1]
        self._refresh(); self.listbox.selection_set(i-1)

    def _move_down(self):
        sel=self.listbox.curselection()
        if not sel or sel[0]>=len(self.cart_paths)-1: return
        i=sel[0]; self.cart_paths[i+1],self.cart_paths[i]=self.cart_paths[i],self.cart_paths[i+1]
        self._refresh(); self.listbox.selection_set(i+1)

    def _rename(self):
        name=simpledialog.askstring('Campaign name','Title:',parent=self.win,
                                     initialvalue=self.meta['name'])
        if name: self.meta['name']=name; self._refresh()

    def _save(self):
        path=filedialog.asksaveasfilename(title='Save Campaign',defaultextension='.campaign',
                                           filetypes=[('Campaign','*.campaign')],parent=self.win)
        if not path: return
        data={'meta':self.meta,'cartridges':self.cart_paths}
        with open(path,'w') as f: json.dump(data,f,indent=2)
        self.campaign_path=path
        self.status.config(text=f'Saved to {os.path.basename(path)} .-')

    def _load(self):
        path=filedialog.askopenfilename(title='Load Campaign',
                                         filetypes=[('Campaign','*.campaign')],parent=self.win)
        if not path: return
        try:
            with open(path) as f: data=json.load(f)
            self.meta=data.get('meta',{'name':'Loaded','transitions':'linear'})
            self.cart_paths=data.get('cartridges',[])
            self.campaign_path=path
            self._refresh()
        except Exception as e:
            messagebox.showerror('Load error',str(e),parent=self.win)


# =============================================================================
# §21  FILE MANAGER  (browse/rename/duplicate/delete cartridges)
# =============================================================================
# // M_LoadGame.  Cartridge organization UI.
class FileManager:
    def __init__(self, parent, on_load=None):
        self.on_load=on_load
        self.win=tk.Toplevel(parent); self.win.title('Cartridge File Manager')
        self.win.configure(bg='#000'); self.win.geometry('640x420')
        self.folder=os.path.expanduser('~')
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='📂  CARTRIDGE MANAGER  📂',bg='#000',fg='#88ccff',
                 font=('Courier',13,'bold')).pack(pady=4)
        top=tk.Frame(w,bg='#000'); top.pack(fill='x',padx=8)
        self.folder_var=tk.StringVar(value=self.folder)
        tk.Entry(top,textvariable=self.folder_var,bg='#0a0a0a',fg='#88ccff',
                 font=('Courier',10),bd=0,insertbackground='#88ccff').pack(side='left',fill='x',expand=True)
        tk.Button(top,text='Browse',bg='#111133',fg='#88ccff',font=('Courier',9),
                  command=self._pick_folder).pack(side='left',padx=2)
        tk.Button(top,text='Refresh',bg='#222',fg='#aaa',font=('Courier',9),
                  command=self._refresh).pack(side='left',padx=2)
        body=tk.Frame(w,bg='#000'); body.pack(fill='both',expand=True,padx=8,pady=4)
        self.listbox=tk.Listbox(body,bg='#0a0a0a',fg='#88ccff',font=('Courier',10),
                                selectbackground='#113355',bd=0,
                                highlightthickness=1,highlightbackground='#113355')
        self.listbox.pack(side='left',fill='both',expand=True)
        ctl=tk.Frame(body,bg='#000'); ctl.pack(side='left',fill='y',padx=6)
        for lbl,cmd,color in [
            ('▶ Load Selected', self._load_sel,'#113311'),
            ('Rename…',         self._rename,'#1a1a1a'),
            ('Duplicate',       self._dupe,'#1a1a1a'),
            ('Delete',          self._delete,'#331111'),
            ('Close',           self.win.destroy,'#222'),
        ]:
            tk.Button(ctl,text=lbl,bg=color,fg='#ccc',font=('Courier',10,'bold'),
                      width=16,command=cmd).pack(pady=2)
        self.status=tk.Label(w,text='Pick a folder containing cartridge .json files .-',
                             bg='#000',fg='#666',font=('Courier',9))
        self.status.pack(pady=2)
        self._refresh()

    def _pick_folder(self):
        path=filedialog.askdirectory(title='Cartridge folder',parent=self.win,
                                      initialdir=self.folder)
        if path:
            self.folder=path; self.folder_var.set(path); self._refresh()

    def _refresh(self):
        self.listbox.delete(0,'end')
        self.folder=self.folder_var.get()
        if not os.path.isdir(self.folder):
            self.status.config(text='Folder not found .-'); return
        try:
            files=sorted(f for f in os.listdir(self.folder) if f.endswith('.json'))
        except Exception as e:
            self.status.config(text=f'Err: {e} .-'); return
        for f in files:
            self.listbox.insert('end',f)
        self.status.config(text=f'{len(files)} cartridges in {self.folder} .-')

    def _selected_path(self):
        sel=self.listbox.curselection()
        if not sel: return None
        return os.path.join(self.folder, self.listbox.get(sel[0]))

    def _load_sel(self):
        p=self._selected_path()
        if not p: return
        try:
            cart=load_cartridge(p)
            if self.on_load: self.on_load(cart, p)
            self.status.config(text=f'Loaded {os.path.basename(p)} .-')
        except Exception as e:
            messagebox.showerror('Load error',str(e),parent=self.win)

    def _rename(self):
        p=self._selected_path()
        if not p: return
        old=os.path.basename(p)
        new=simpledialog.askstring('Rename',f'New name for "{old}":',parent=self.win,
                                    initialvalue=old)
        if not new or new==old: return
        if not new.endswith('.json'): new+='.json'
        try:
            os.rename(p, os.path.join(self.folder,new))
            self._refresh()
        except Exception as e:
            messagebox.showerror('Rename error',str(e),parent=self.win)

    def _dupe(self):
        p=self._selected_path()
        if not p: return
        base,ext=os.path.splitext(os.path.basename(p))
        new=os.path.join(self.folder,f'{base}_copy{ext}')
        i=1
        while os.path.exists(new):
            i+=1; new=os.path.join(self.folder,f'{base}_copy{i}{ext}')
        try:
            import shutil; shutil.copy2(p,new); self._refresh()
        except Exception as e:
            messagebox.showerror('Duplicate error',str(e),parent=self.win)

    def _delete(self):
        p=self._selected_path()
        if not p: return
        if not messagebox.askyesno('Delete',f'Delete "{os.path.basename(p)}" permanently?',
                                    parent=self.win): return
        try: os.remove(p); self._refresh()
        except Exception as e: messagebox.showerror('Delete error',str(e),parent=self.win)


# =============================================================================
# §22  SOLITAIRE  (embedded mini-game, Klondike)
# =============================================================================
# // G_SecondarySession.  A lightweight in-universe diversion.
class Solitaire:
    SUITS=('♠','♥','♦','♣'); RANKS=('A','2','3','4','5','6','7','8','9','10','J','Q','K')
    def __init__(self, parent):
        self.win=tk.Toplevel(parent); self.win.title('Klondike Solitaire')
        self.win.configure(bg='#063'); self.win.geometry('640x480')
        self._new_game()
        self._build_ui()
        self._draw()

    def _new_game(self):
        # // Deck = list of (rank, suit) tuples
        deck=[(r,s) for s in self.SUITS for r in self.RANKS]
        _RNG.shuffle(deck)
        self.tableau=[[] for _ in range(7)]
        self.foundations=[[] for _ in range(4)]
        self.stock=[]
        self.waste=[]
        # Deal tableau
        for i in range(7):
            for j in range(i,7):
                card=deck.pop()
                self.tableau[j].append((card[0],card[1],j==i))  # face-up only on top
        self.stock=[(c[0],c[1],False) for c in deck]
        self.selected=None

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='♠ ♥ KLONDIKE ♦ ♣',bg='#063',fg='#fff',
                 font=('Courier',13,'bold')).pack(pady=4)
        self.canvas=tk.Canvas(w,bg='#074',width=620,height=400,
                              highlightthickness=0)
        self.canvas.pack(padx=8)
        self.canvas.bind('<Button-1>',self._click)
        bar=tk.Frame(w,bg='#063'); bar.pack(fill='x',pady=4)
        tk.Button(bar,text='New Game',bg='#222',fg='#fff',font=('Courier',10),
                  command=lambda:(self._new_game(),self._draw())).pack(side='left',padx=4)
        tk.Button(bar,text='Close',bg='#222',fg='#fff',font=('Courier',10),
                  command=self.win.destroy).pack(side='left',padx=4)
        self.status=tk.Label(bar,text='Click stock to draw.  Click a card to select/move .-',
                             bg='#063',fg='#ddd',font=('Courier',9))
        self.status.pack(side='left',padx=12)

    def _card_color(self, suit):
        return '#e22' if suit in ('♥','♦') else '#111'

    def _draw(self):
        c=self.canvas; c.delete('all')
        CARD_W=72; CARD_H=96; GAP=8
        # Stock (top-left)
        x,y=10,10
        if self.stock:
            c.create_rectangle(x,y,x+CARD_W,y+CARD_H,fill='#228',outline='#fff',width=2,tags='stock')
            c.create_text(x+CARD_W/2,y+CARD_H/2,text=f'📦\n{len(self.stock)}',fill='#fff',
                          font=('Courier',10,'bold'),tags='stock')
        else:
            c.create_rectangle(x,y,x+CARD_W,y+CARD_H,fill='#062',outline='#444',width=1,tags='stock')
            c.create_text(x+CARD_W/2,y+CARD_H/2,text='↻',fill='#999',
                          font=('Courier',16,'bold'),tags='stock')
        # Waste
        x=10+CARD_W+GAP
        if self.waste:
            card=self.waste[-1]
            c.create_rectangle(x,y,x+CARD_W,y+CARD_H,fill='#fff',outline='#000',width=1,
                               tags=f'waste_{len(self.waste)-1}')
            c.create_text(x+CARD_W/2,y+CARD_H/2,text=f'{card[0]}\n{card[1]}',
                          fill=self._card_color(card[1]),font=('Courier',14,'bold'),
                          tags=f'waste_{len(self.waste)-1}')
        else:
            c.create_rectangle(x,y,x+CARD_W,y+CARD_H,fill='#063',outline='#444',width=1)
        # Foundations (top-right)
        for i in range(4):
            fx=10+(CARD_W+GAP)*(3+i); fy=10
            c.create_rectangle(fx,fy,fx+CARD_W,fy+CARD_H,fill='#074',outline='#ccc',width=1)
            if self.foundations[i]:
                card=self.foundations[i][-1]
                c.create_rectangle(fx,fy,fx+CARD_W,fy+CARD_H,fill='#fff',outline='#000',
                                   width=1,tags=f'found_{i}')
                c.create_text(fx+CARD_W/2,fy+CARD_H/2,text=f'{card[0]}\n{card[1]}',
                              fill=self._card_color(card[1]),font=('Courier',14,'bold'),
                              tags=f'found_{i}')
            else:
                c.create_text(fx+CARD_W/2,fy+CARD_H/2,text=self.SUITS[i],
                              fill='#555',font=('Courier',28,'bold'))
        # Tableau columns
        for i,col in enumerate(self.tableau):
            tx=10+(CARD_W+GAP)*i; ty=10+CARD_H+20
            if not col:
                c.create_rectangle(tx,ty,tx+CARD_W,ty+CARD_H,fill='#063',outline='#444',width=1,
                                   tags=f'tab_{i}_empty')
            for j,(rank,suit,face_up) in enumerate(col):
                cy=ty+j*22
                if face_up:
                    c.create_rectangle(tx,cy,tx+CARD_W,cy+CARD_H,fill='#fff',outline='#000',
                                       width=1,tags=f'tab_{i}_{j}')
                    c.create_text(tx+14,cy+14,text=rank,fill=self._card_color(suit),
                                  font=('Courier',11,'bold'),tags=f'tab_{i}_{j}')
                    c.create_text(tx+14,cy+28,text=suit,fill=self._card_color(suit),
                                  font=('Courier',11,'bold'),tags=f'tab_{i}_{j}')
                else:
                    c.create_rectangle(tx,cy,tx+CARD_W,cy+CARD_H,fill='#228',outline='#fff',
                                       width=1,tags=f'tab_{i}_{j}')
                    c.create_text(tx+CARD_W/2,cy+CARD_H/2,text='?',fill='#fff',
                                  font=('Courier',14,'bold'),tags=f'tab_{i}_{j}')
        # Highlight selection
        if self.selected:
            zone,idx,sub=self.selected
            if zone=='tab':
                tx=10+(CARD_W+GAP)*idx; ty=10+CARD_H+20+sub*22
                c.create_rectangle(tx-2,ty-2,tx+CARD_W+2,ty+CARD_H+2,outline='#ff0',width=3)
            elif zone=='waste':
                wx=10+CARD_W+GAP
                c.create_rectangle(wx-2,8,wx+CARD_W+2,10+CARD_H+2,outline='#ff0',width=3)

    def _rank_val(self, rank):
        return self.RANKS.index(rank)+1

    def _can_place_tab(self, card, col):
        if not col: return card[0]=='K'
        top=col[-1]
        if not top[2]: return False  # face-down top — impossible but safety
        top_red=top[1] in ('♥','♦'); card_red=card[1] in ('♥','♦')
        return (top_red!=card_red) and (self._rank_val(top[0])==self._rank_val(card[0])+1)

    def _can_place_found(self, card, idx):
        fnd=self.foundations[idx]
        if not fnd: return card[0]=='A'
        top=fnd[-1]
        return (top[1]==card[1]) and (self._rank_val(top[0])+1==self._rank_val(card[0]))

    def _click(self, ev):
        items=self.canvas.find_overlapping(ev.x,ev.y,ev.x,ev.y)
        if not items: return
        tags=[]
        for it in items: tags.extend(self.canvas.gettags(it))
        if 'stock' in tags:
            # Deal 1 from stock to waste, or recycle
            if self.stock:
                c=self.stock.pop(); self.waste.append((c[0],c[1],True))
            else:
                self.stock=[(c[0],c[1],False) for c in reversed(self.waste)]
                self.waste=[]
            self.selected=None; self._draw(); return
        # Try parse tab/waste/found tags
        target=None
        for t in tags:
            if t.startswith('tab_'):
                parts=t.split('_')
                if len(parts)==3:
                    target=('tab',int(parts[1]),int(parts[2])); break
                elif len(parts)==3 and parts[2]=='empty':
                    target=('tab',int(parts[1]),-1); break
            elif t.startswith('waste_'):
                target=('waste',0,int(t.split('_')[1])); break
            elif t.startswith('found_'):
                target=('found',int(t.split('_')[1]),0); break
        if target is None: return
        # Selection logic
        if self.selected is None:
            # Pick up (only if movable)
            zone,idx,sub=target
            if zone=='tab':
                if sub<len(self.tableau[idx]) and self.tableau[idx][sub][2]:
                    self.selected=target
            elif zone=='waste' and self.waste:
                self.selected=('waste',0,len(self.waste)-1)
            self._draw(); return
        # Drop
        src_zone,src_idx,src_sub=self.selected
        dst_zone,dst_idx,_=target
        if src_zone=='tab':
            cards=self.tableau[src_idx][src_sub:]
        elif src_zone=='waste':
            cards=[self.waste[-1]]
        else:
            self.selected=None; self._draw(); return
        moved=False
        if dst_zone=='tab':
            if self._can_place_tab(cards[0], self.tableau[dst_idx]):
                self.tableau[dst_idx].extend(cards)
                if src_zone=='tab': del self.tableau[src_idx][src_sub:]
                elif src_zone=='waste': self.waste.pop()
                moved=True
        elif dst_zone=='found' and len(cards)==1:
            if self._can_place_found(cards[0], dst_idx):
                self.foundations[dst_idx].append(cards[0])
                if src_zone=='tab': self.tableau[src_idx].pop()
                elif src_zone=='waste': self.waste.pop()
                moved=True
        if moved and src_zone=='tab' and self.tableau[src_idx]:
            # Flip last face-down
            top=self.tableau[src_idx][-1]
            if not top[2]:
                self.tableau[src_idx][-1]=(top[0],top[1],True)
        self.selected=None; self._draw()
        # Check win
        if all(len(f)==13 for f in self.foundations):
            self.status.config(text='🏆 YOU WIN .-')


# =============================================================================
# §23  IN-GAME TERMINAL  (physical entity: press E → hub with all creation tools)
# =============================================================================
# // P_UseSpecialLine.  When the player interacts with a terminal entity, a
#    Toplevel hub opens containing tabs for every creation tool.
class InGameTerminal:
    def __init__(self, parent, cart=None):
        self.cart=cart
        self.win=tk.Toplevel(parent); self.win.title('>_ DoomCraft Terminal')
        self.win.configure(bg='#000'); self.win.geometry('420x360')
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='┌─ DOOMCRAFT TERMINAL ─┐',bg='#000',fg='#00ff88',
                 font=('Courier',12,'bold')).pack(pady=6)
        tk.Label(w,text='> Select application .-',bg='#000',fg='#00aa44',
                 font=('Courier',10)).pack()
        grid=tk.Frame(w,bg='#000'); grid.pack(pady=10,padx=10,fill='both',expand=True)
        apps=[
            ('FlowScript',   lambda:FlowScriptConsole(self.win)),
            ('Sprite Editor',lambda:SpriteEditor(self.win, cart=self.cart) if self.cart else None),
            ('SFX Gen',      lambda:SFXGenerator(self.win, cart=self.cart)),
            ('Music Gen',    lambda:MusicGenerator(self.win, cart=self.cart)),
            ('Dialogue',     lambda:DialogueEditor(self.win, cart=self.cart)),
            ('Solitaire',    lambda:Solitaire(self.win)),
        ]
        for i,(name,cmd) in enumerate(apps):
            r,col=divmod(i,2)
            tk.Button(grid,text=name,bg='#001a00',fg='#00ff88',font=('Courier',11,'bold'),
                      width=18,height=2,relief='ridge',bd=2,
                      command=cmd).grid(row=r,column=col,padx=6,pady=6,sticky='nsew')
        tk.Button(w,text='[ Close Terminal ]',bg='#220000',fg='#ff4444',
                  font=('Courier',10,'bold'),command=self.win.destroy).pack(pady=6)


# =============================================================================
# §24  FLOWSCRIPT CONSOLE  (standalone multiline scripting window)
# =============================================================================
class FlowScriptConsole:
    def __init__(self, parent):
        self.win=tk.Toplevel(parent); self.win.title('FlowScript Console')
        self.win.configure(bg='#000'); self.win.geometry('560x420')
        self.fs=FlowScript(tone_fn=play_tone)
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='> FLOWSCRIPT CONSOLE .-',bg='#000',fg='#00ff88',
                 font=('Courier',12,'bold')).pack(pady=4)
        self.input=tk.Text(w,height=10,bg='#050a05',fg='#00ff88',
                           font=('Courier',10),bd=0,insertbackground='#00ff88',
                           highlightthickness=1,highlightbackground='#003300')
        self.input.pack(fill='both',expand=True,padx=8,pady=4)
        self.input.insert('1.0','# Example:\nset hp 100\nset pts 500\nprint Player hp: hp pts: pts\nrepeat 3 {\n    entropy roll 1 6\n    print Rolled roll\n}\n')
        bf=tk.Frame(w,bg='#000'); bf.pack(pady=4)
        tk.Button(bf,text='▶ Run',bg='#113311',fg='#00ff44',font=('Courier',10,'bold'),
                  width=10,command=self._run).pack(side='left',padx=4)
        tk.Button(bf,text='Clear Output',bg='#222',fg='#aaa',font=('Courier',10),
                  command=self._clear).pack(side='left',padx=4)
        tk.Button(bf,text='Close',bg='#222',fg='#aaa',font=('Courier',10),
                  command=self.win.destroy).pack(side='left',padx=4)
        self.output=tk.Text(w,height=10,bg='#050505',fg='#ffcc44',
                            font=('Courier',10),bd=0,state='disabled',
                            highlightthickness=1,highlightbackground='#333311')
        self.output.pack(fill='both',expand=True,padx=8,pady=4)

    def _run(self):
        code=self.input.get('1.0','end').strip()
        self.output.config(state='normal')
        try:
            out=self.fs.run(code)
            self.output.insert('end','\n'.join(out)+'\n────────────────────\n')
        except Exception as e:
            self.output.insert('end',f'ERROR: {e} .-\n────────────────────\n')
        self.output.see('end'); self.output.config(state='disabled')

    def _clear(self):
        self.output.config(state='normal'); self.output.delete('1.0','end')
        self.output.config(state='disabled')



# =============================================================================
# §25  START MENU  (hub for all standalone apps, accessible from Launcher)
# =============================================================================
class StartMenu:
    def __init__(self, launcher):
        self.launcher=launcher
        self.win=tk.Toplevel(launcher.root); self.win.title('Start Menu — All Apps')
        self.win.configure(bg='#000'); self.win.resizable(False,False)
        self._build_ui()

    def _build_ui(self):
        w=self.win
        tk.Label(w,text='■ START MENU ■',bg='#000',fg='#00ff88',
                 font=('Courier',14,'bold')).pack(pady=8)
        tk.Label(w,text='Launch any creation tool or standalone app .-',
                 bg='#000',fg='#666',font=('Courier',9)).pack(pady=(0,8))
        grid=tk.Frame(w,bg='#000'); grid.pack(padx=16,pady=4)
        # Rows of 3 apps
        apps=[
            ('FlowScript Console', '#003300','#00ff88', lambda:FlowScriptConsole(self.win)),
            ('Sprite Editor',      '#330033','#ff88ff', lambda:SpriteEditor(self.win, cart=self.launcher.active_cart)
                                                           if self.launcher.active_cart else
                                                           messagebox.showwarning('No cartridge','Load or create a cartridge first.')),
            ('SFX Generator',      '#332200','#ff8800', lambda:SFXGenerator(self.win, cart=self.launcher.active_cart)),
            ('Music Generator',    '#002233','#44aaff', lambda:MusicGenerator(self.win, cart=self.launcher.active_cart)),
            ('Dialogue Editor',    '#332211','#ffcc44', lambda:DialogueEditor(self.win, cart=self.launcher.active_cart)),
            ('Campaign Sequencer', '#330022','#ff44cc', lambda:CampaignEditor(self.win)),
            ('File Manager',       '#113355','#88ccff', lambda:FileManager(self.win, on_load=self._on_fm_load)),
            ('In-Game Terminal',   '#001a00','#00ff88', lambda:InGameTerminal(self.win, cart=self.launcher.active_cart)),
            ('Solitaire',          '#003322','#66ffaa', lambda:Solitaire(self.win)),
        ]
        for i,(name,bgc,fgc,cmd) in enumerate(apps):
            r,col=divmod(i,3)
            tk.Button(grid,text=name,bg=bgc,fg=fgc,font=('Courier',11,'bold'),
                      width=20,height=2,relief='ridge',bd=2,
                      command=cmd).grid(row=r,column=col,padx=6,pady=6)
        tk.Button(w,text='Close',bg='#222',fg='#aaa',font=('Courier',10),
                  command=self.win.destroy).pack(pady=(8,12))

    def _on_fm_load(self, cart, path):
        self.launcher.active_cart=cart
        self.launcher.active_cart_path=path
        self.launcher.cart_var.set(f'Loaded: {os.path.basename(path)}  [seed {cart["seed_signature"][:12]}...]')


# =============================================================================
# §16  ENTRY POINT
# =============================================================================
if __name__ == '__main__':
    # // R_Init: Init the renderer.  D_DoomMain.
    launcher = Launcher()
    launcher.run()
    # The dot sings.  .-
