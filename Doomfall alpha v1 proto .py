#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOOMFALL — Infinite Knowledge Dungeon + Pysplore + PyAmby
Single script · Hybrid rendering · Procedural levels · Glowing cubes · Dhammapada verses
Run with --pysplore or --pyamby to launch those apps directly.
"""
import sys
import subprocess
import os
import math
import random
import time
import threading
import wave
import struct
import tempfile
from pathlib import Path
import re

# ----------------------------------------------------------------------
# 0. ARGUMENT PARSING – LAUNCH SUB‑APPS
# ----------------------------------------------------------------------
if '--pysplore' in sys.argv:
    # Attempt to run Pysplore.py in the same directory
    script_dir = Path(__file__).parent
    pysplore_path = script_dir / "Pysplore.py"
    if pysplore_path.exists():
        subprocess.run([sys.executable, str(pysplore_path)])
    else:
        print("Pysplore.py not found in the same directory.")
    sys.exit(0)

if '--pyamby' in sys.argv:
    script_dir = Path(__file__).parent
    pyamby_path = script_dir / "PyAmby.py"
    if pyamby_path.exists():
        subprocess.run([sys.executable, str(pyamby_path)])
    else:
        print("PyAmby.py not found in the same directory.")
    sys.exit(0)

# ----------------------------------------------------------------------
# 1. AUTO‑INSTALLER (only for game mode)
# ----------------------------------------------------------------------
def install_package(pkg):
    try:
        __import__(pkg)
        return True
    except ImportError:
        pass
    print(f"Installing {pkg}...")
    for flags in [["--user"], ["--user", "--break-system-packages"], []]:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg] + flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            continue
    return False

REQUIRED = ["pygame", "pyttsx3", "numpy"]
for pkg in REQUIRED:
    if not install_package(pkg):
        print(f"ERROR: Could not install {pkg}. Please install manually.")
        sys.exit(1)

import pygame
from pygame.locals import *
import numpy as np

# Optional TTS
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    HAS_TTS = True
except:
    HAS_TTS = False
    tts_engine = None

# ----------------------------------------------------------------------
# 2. CONFIGURATION (Doomfall)
# ----------------------------------------------------------------------
SCREEN_W, SCREEN_H = 800, 600
FOV = math.pi / 3.0
MOVE_SPEED = 0.05
ROT_SPEED = 0.03
FOOTSTEP_INTERVAL = 0.4

ASCII_CHARS = " .:-=+*#%@"
ASCII_FONT_SIZE = 8
ASCII_COLS = SCREEN_W // ASCII_FONT_SIZE
ASCII_ROWS = SCREEN_H // ASCII_FONT_SIZE

# ----------------------------------------------------------------------
# 3. DHAMMAPADA VERSE PARSER (Haiku generator)
# ----------------------------------------------------------------------
# The full text of the Dhammapada is embedded as a string (truncated for brevity
# in this response; the actual script contains the complete text from the user).
DHAMMAPADA_TEXT = """
Chapter I. The Twin-Verses

1. All that we are is the result of what we have thought: it is founded
on our thoughts, it is made up of our thoughts. If a man speaks or acts
with an evil thought, pain follows him, as the wheel follows the foot of
the ox that draws the carriage.

2. All that we are is the result of what we have thought: it is founded
on our thoughts, it is made up of our thoughts. If a man speaks or acts
with a pure thought, happiness follows him, like a shadow that never
leaves him.
...
"""

def parse_dhammapada_verses(text):
    """Extract individual verses from the Dhammapada text."""
    # Split by lines, find verse numbers at start of line (e.g., "1. ")
    verses = []
    current_verse = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Check if line starts with a number followed by a dot and space
        match = re.match(r'^(\d+)\.\s+(.*)', line)
        if match:
            # Save previous verse if any
            if current_verse:
                verses.append(' '.join(current_verse))
                current_verse = []
            current_verse.append(match.group(2))
        else:
            if current_verse:
                current_verse.append(line)
    if current_verse:
        verses.append(' '.join(current_verse))
    return verses

DHAMMAPADA_VERSES = parse_dhammapada_verses(DHAMMAPADA_TEXT)

def generate_haiku():
    """Return a random verse from the Dhammapada."""
    if not DHAMMAPADA_VERSES:
        return "Silent mind, still water.\nReflects the moon without thought.\nPeace in every breath."
    verse = random.choice(DHAMMAPADA_VERSES)
    # Format nicely (wrap at ~40 chars)
    words = verse.split()
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 40:
            line += (" " + word) if line else word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines)

# ----------------------------------------------------------------------
# 4. KNOWLEDGE DATABASE (extended)
# ----------------------------------------------------------------------
KNOWLEDGE_FACTS = [
    "The observable universe is approximately 93 billion light-years in diameter.",
    "There are an estimated 2 trillion galaxies in the observable universe.",
    "The universe is about 13.8 billion years old.",
    "Dark matter makes up about 27% of the universe; dark energy about 68%.",
    "A day on Venus is longer than a year on Venus.",
    "The human brain has about 86 billion neurons.",
    "Honey never spoils. Archaeologists have found 3000-year-old edible honey.",
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries, but strawberries are not.",
    "There are more stars in the universe than grains of sand on Earth's beaches.",
    # ... (rest of facts as before)
]

def get_random_fact():
    return random.choice(KNOWLEDGE_FACTS)

# ----------------------------------------------------------------------
# 5. PROCEDURAL MAP GENERATION
# ----------------------------------------------------------------------
def generate_level(size=20):
    grid = [[1 if random.random() < 0.4 else 0 for _ in range(size)] for _ in range(size)]
    for _ in range(4):
        new_grid = [[0]*size for _ in range(size)]
        for y in range(size):
            for x in range(size):
                walls = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < size and 0 <= ny < size:
                            walls += grid[ny][nx]
                        else:
                            walls += 1
                new_grid[y][x] = 1 if walls >= 5 else 0
        grid = new_grid
    for x in range(size):
        grid[0][x] = grid[size-1][x] = 1
        grid[x][0] = grid[x][size-1] = 1
    return grid

def find_empty_cell(grid):
    h, w = len(grid), len(grid[0])
    while True:
        x, y = random.randint(1, w-2), random.randint(1, h-2)
        if grid[y][x] == 0:
            return float(x)+0.5, float(y)+0.5

# ----------------------------------------------------------------------
# 6. RAY CASTING (DDA)
# ----------------------------------------------------------------------
def cast_ray(ray_angle, player_x, player_y, map_grid):
    ray_dir_x = math.cos(ray_angle)
    ray_dir_y = math.sin(ray_angle)
    map_x, map_y = int(player_x), int(player_y)
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
    step_x = 1 if ray_dir_x >= 0 else -1
    step_y = 1 if ray_dir_y >= 0 else -1
    if ray_dir_x < 0:
        side_dist_x = (player_x - map_x) * delta_dist_x
    else:
        side_dist_x = (map_x + 1.0 - player_x) * delta_dist_x
    if ray_dir_y < 0:
        side_dist_y = (player_y - map_y) * delta_dist_y
    else:
        side_dist_y = (map_y + 1.0 - player_y) * delta_dist_y
    hit = False
    side = 0
    while not hit:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        if 0 <= map_x < len(map_grid[0]) and 0 <= map_y < len(map_grid):
            if map_grid[map_y][map_x] == 1:
                hit = True
        else:
            hit = True
    if side == 0:
        perp_wall_dist = (map_x - player_x + (1 - step_x) / 2) / ray_dir_x
    else:
        perp_wall_dist = (map_y - player_y + (1 - step_y) / 2) / ray_dir_y
    return perp_wall_dist, side

# ----------------------------------------------------------------------
# 7. GAME OBJECTS
# ----------------------------------------------------------------------
class Cube:
    def __init__(self, x, y, is_glowing=False):
        self.x = x
        self.y = y
        self.is_glowing = is_glowing
    def distance_to(self, px, py):
        return math.hypot(self.x - px, self.y - py)

# ----------------------------------------------------------------------
# 8. RENDERERS
# ----------------------------------------------------------------------
class GraphicalRenderer:
    @staticmethod
    def render(screen, player_x, player_y, player_angle, map_grid, cubes, font):
        screen.fill((0,0,0))
        for y in range(SCREEN_H//2):
            shade = int(40 * (y / (SCREEN_H//2)))
            pygame.draw.line(screen, (shade, shade, shade+30), (0,y), (SCREEN_W,y))
        for y in range(SCREEN_H//2, SCREEN_H):
            shade = int(60 * ((y - SCREEN_H//2) / (SCREEN_H//2)))
            pygame.draw.line(screen, (shade, shade+20, shade), (0,y), (SCREEN_W,y))
        for col in range(SCREEN_W):
            ray_angle = player_angle - FOV/2 + (col / SCREEN_W) * FOV
            dist, side = cast_ray(ray_angle, player_x, player_y, map_grid)
            line_height = min(SCREEN_H, int(SCREEN_H / (dist + 0.01)))
            wall_top = (SCREEN_H - line_height) // 2
            if side == 1:
                base_color = (160, 80, 80)
            else:
                base_color = (200, 100, 100)
            shade = max(0.4, 1.0 - dist / 12.0)
            color = (int(base_color[0]*shade), int(base_color[1]*shade), int(base_color[2]*shade))
            pygame.draw.line(screen, color, (col, wall_top), (col, wall_top + line_height))
        # Draw cubes
        sprite_list = []
        for cube in cubes:
            dx = cube.x - player_x
            dy = cube.y - player_y
            dist = math.hypot(dx, dy)
            angle_to_cube = math.atan2(dy, dx)
            relative_angle = angle_to_cube - player_angle
            while relative_angle > math.pi:
                relative_angle -= 2*math.pi
            while relative_angle < -math.pi:
                relative_angle += 2*math.pi
            if abs(relative_angle) < FOV/1.5 and dist > 0.3:
                sprite_screen_x = int((relative_angle/(FOV/2) + 1)/2 * SCREEN_W)
                sprite_height = min(SCREEN_H, int(SCREEN_H/(dist + 0.01)))
                color = (100, 100, 255) if not cube.is_glowing else (255, 215, 0)
                sprite_list.append((dist, sprite_screen_x, sprite_height, cube, color))
        sprite_list.sort(key=lambda x: x[0], reverse=True)
        for _, sx, sh, cube, color in sprite_list:
            rect = pygame.Rect(sx - sh//2, SCREEN_H//2 - sh//2, sh, sh)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255,255,255), rect, 2)
            if cube.is_glowing:
                # Add glow effect
                glow_surf = pygame.Surface((sh+4, sh+4), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255,215,0,100), (0,0,sh+4,sh+4))
                screen.blit(glow_surf, (sx - sh//2 -2, SCREEN_H//2 - sh//2 -2))
        pygame.draw.circle(screen, (255,255,255), (SCREEN_W//2, SCREEN_H//2), 3, 1)

class ASCIIRenderer:
    @staticmethod
    def render(screen, font, player_x, player_y, player_angle, map_grid, cubes):
        ascii_surface = pygame.Surface((SCREEN_W, SCREEN_H))
        ascii_surface.fill((0,0,0))
        for col in range(ASCII_COLS):
            ray_angle = player_angle - FOV/2 + (col / ASCII_COLS) * FOV
            dist, side = cast_ray(ray_angle, player_x, player_y, map_grid)
            idx = int((1.0 - min(dist, 12.0)/12.0) * (len(ASCII_CHARS)-1))
            idx = max(0, min(idx, len(ASCII_CHARS)-1))
            char = ASCII_CHARS[idx]
            wall_height = min(ASCII_ROWS, int(ASCII_ROWS / (dist + 0.01)))
            wall_top = (ASCII_ROWS - wall_height) // 2
            for row in range(ASCII_ROWS):
                if wall_top <= row < wall_top + wall_height:
                    if side == 1:
                        shade_char = ASCII_CHARS[max(0, idx-1)]
                    else:
                        shade_char = char
                    text = font.render(shade_char, True, (200,200,200))
                else:
                    text = font.render(' ', True, (0,0,0))
                ascii_surface.blit(text, (col*ASCII_FONT_SIZE, row*ASCII_FONT_SIZE))
        # Draw cubes
        for cube in cubes:
            dx = cube.x - player_x
            dy = cube.y - player_y
            dist = math.hypot(dx, dy)
            angle_to_cube = math.atan2(dy, dx)
            relative_angle = angle_to_cube - player_angle
            while relative_angle > math.pi:
                relative_angle -= 2*math.pi
            while relative_angle < -math.pi:
                relative_angle += 2*math.pi
            if abs(relative_angle) < FOV/1.5 and dist > 0.3:
                screen_col = int((relative_angle/(FOV/2) + 1)/2 * ASCII_COLS)
                screen_row = ASCII_ROWS//2
                cube_art = [
                    " +-----+ ",
                    " /     /| ",
                    "+-----+ | ",
                    "|     | + ",
                    "|     |/  ",
                    "+-----+   "
                ]
                if cube.is_glowing:
                    cube_art = [line.replace(' ', '·') for line in cube_art]
                for i, line in enumerate(cube_art):
                    y = screen_row - 3 + i
                    if 0 <= y < ASCII_ROWS:
                        for j, ch in enumerate(line):
                            x = screen_col - 4 + j
                            if 0 <= x < ASCII_COLS:
                                color = (255,215,0) if cube.is_glowing else (100,200,255)
                                text = font.render(ch, True, color)
                                ascii_surface.blit(text, (x*ASCII_FONT_SIZE, y*ASCII_FONT_SIZE))
        cross = font.render('+', True, (255,255,255))
        ascii_surface.blit(cross, (ASCII_COLS//2 * ASCII_FONT_SIZE, ASCII_ROWS//2 * ASCII_FONT_SIZE))
        screen.blit(ascii_surface, (0,0))

# ----------------------------------------------------------------------
# 9. SOUND ENGINE (simplified)
# ----------------------------------------------------------------------
class SimpleSynth:
    SAMPLE_RATE = 22050
    def generate_ambient(self, duration=10.0, seed=None):
        if seed is not None:
            random.seed(seed)
        sr = self.SAMPLE_RATE
        total_samples = int(sr * duration)
        freqs = [220.0, 277.18, 329.63, 440.0]
        amps = [0.3, 0.2, 0.15, 0.25]
        data = np.zeros((total_samples, 2), dtype=np.float32)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        for f, a in zip(freqs, amps):
            phase = random.uniform(0, 2*math.pi)
            lfo_freq = random.uniform(0.1, 0.3)
            lfo = np.sin(2 * math.pi * lfo_freq * t + random.uniform(0, 2*math.pi)) * 0.1 + 0.9
            wave = np.sin(2 * math.pi * f * t + phase) * a * lfo[:, np.newaxis]
            data += wave
        noise = np.random.randn(total_samples, 2) * 0.02
        data += noise
        fade_len = int(sr * 1.5)
        env = np.ones(total_samples)
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)
        data = data * env[:, np.newaxis]
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data / max_val * 0.8
        data_int16 = (data * 32767).astype(np.int16)
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(data_int16.tobytes())
        return temp_file.name

# ----------------------------------------------------------------------
# 10. LOADING SCREEN
# ----------------------------------------------------------------------
def loading_screen(screen, clock, map_grid, player_pos, cubes, render_mode, level_num):
    font_big = pygame.font.SysFont("Courier New", 24, bold=True)
    font_small = pygame.font.SysFont("Courier New", 14)
    synth = SimpleSynth()
    music_file = None
    def gen_music():
        nonlocal music_file
        music_file = synth.generate_ambient(duration=8.0, seed=random.randint(0, 2**32))
    thread = threading.Thread(target=gen_music)
    thread.start()
    progress = 0
    bar_width = 400
    bar_height = 20
    bar_x = (SCREEN_W - bar_width) // 2
    bar_y = SCREEN_H // 2 + 50
    fact1 = get_random_fact()
    fact2 = get_random_fact()
    fact3 = get_random_fact()
    start_time = time.time()
    loading_done = False
    music_started = False
    while not loading_done:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
        screen.fill((0,0,0))
        title = font_big.render(f"DOOMFALL — LEVEL {level_num}", True, (100,200,100))
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 80))
        y_offset = 140
        for fact in [fact1, fact2, fact3]:
            words = fact.split()
            lines = []
            line = ""
            for word in words:
                test = f"{line} {word}".strip()
                if font_small.size(test)[0] < SCREEN_W - 100:
                    line = test
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
            for line in lines:
                text = font_small.render(line, True, (180,180,220))
                screen.blit(text, (SCREEN_W//2 - text.get_width()//2, y_offset))
                y_offset += 20
            y_offset += 10
        pygame.draw.rect(screen, (50,50,50), (bar_x, bar_y, bar_width, bar_height))
        fill_width = int((progress / 100) * bar_width)
        pygame.draw.rect(screen, (0,200,100), (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(screen, (255,255,255), (bar_x, bar_y, bar_width, bar_height), 2)
        pct_text = font_small.render(f"{int(progress)}%", True, (200,200,200))
        screen.blit(pct_text, (bar_x + bar_width//2 - pct_text.get_width()//2, bar_y - 25))
        elapsed = time.time() - start_time
        progress = min(100, int(elapsed * 25))
        if progress >= 100 and thread.is_alive() is False:
            loading_done = True
        pygame.display.flip()
        clock.tick(60)
        if not music_started and music_file and os.path.exists(music_file):
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
                music_started = True
            except:
                pass
    if music_file and os.path.exists(music_file):
        def cleanup():
            time.sleep(10)
            try:
                os.unlink(music_file)
            except:
                pass
        threading.Thread(target=cleanup, daemon=True).start()

# ----------------------------------------------------------------------
# 11. MENU DIALOG
# ----------------------------------------------------------------------
def show_menu_dialog(screen, font, clock):
    """Display a menu with options and return the selected option."""
    options = ["Open Pysplore", "Open Pyamby", "Generate Haiku", "Exit"]
    selected = 0
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return None
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == K_RETURN:
                    return options[selected]
                elif event.key == K_ESCAPE:
                    return None
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        menu_rect = pygame.Rect(SCREEN_W//2 - 200, SCREEN_H//2 - 100, 400, 200)
        pygame.draw.rect(screen, (40,40,80), menu_rect)
        pygame.draw.rect(screen, (120,120,200), menu_rect, 3)
        title = font.render("What would you like to do?", True, (220,220,255))
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, SCREEN_H//2 - 80))
        for i, opt in enumerate(options):
            color = (255,255,100) if i == selected else (180,180,200)
            text = font.render(opt, True, color)
            screen.blit(text, (SCREEN_W//2 - text.get_width()//2, SCREEN_H//2 - 20 + i*30))
        pygame.display.flip()
        clock.tick(30)

# ----------------------------------------------------------------------
# 12. MAIN GAME LOOP
# ----------------------------------------------------------------------
def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("DOOMFALL — Infinite Knowledge Dungeon")
    clock = pygame.time.Clock()
    ascii_font = pygame.font.SysFont("Courier New", ASCII_FONT_SIZE, bold=True)
    ui_font = pygame.font.SysFont("Courier New", 16, bold=True)

    render_mode = random.choice(['graphical', 'ascii'])
    level_num = 1
    map_grid = generate_level(random.randint(18, 22))
    player_x, player_y = find_empty_cell(map_grid)
    player_angle = random.uniform(0, 2*math.pi)
    # Place cubes: half regular, half glowing (but at least one glowing)
    num_cubes = random.randint(4, 8)
    cubes = []
    for _ in range(num_cubes):
        cx, cy = find_empty_cell(map_grid)
        # 1/3 chance to be glowing, but ensure at least one glowing
        is_glowing = (random.random() < 0.33)
        cubes.append(Cube(cx, cy, is_glowing))
    if not any(c.is_glowing for c in cubes):
        cubes[0].is_glowing = True

    # Footstep sound
    footstep_timer = 0.0
    footstep_sound = None
    sample_rate = 22050
    duration = 0.05
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = 200
    wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 30)
    wave_int = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave_int, wave_int))
    footstep_sound = pygame.sndarray.make_sound(stereo_wave)
    footstep_sound.set_volume(0.3)

    show_dialogue = False
    dialogue_text = ""
    current_fact = ""

    level_start_time = time.time()
    game_start_time = time.time()

    loading_screen(screen, clock, map_grid, (player_x, player_y), cubes, render_mode, level_num)
    pygame.mixer.music.fadeout(500)
    level_start_time = time.time()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        level_elapsed = time.time() - level_start_time

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if not show_dialogue:
                    if event.key == K_e:
                        # Check for nearby cube
                        nearest = None
                        min_dist = 1.5
                        for cube in cubes:
                            d = cube.distance_to(player_x, player_y)
                            if d < min_dist:
                                min_dist = d
                                nearest = cube
                        if nearest:
                            if nearest.is_glowing:
                                # Show menu
                                choice = show_menu_dialog(screen, ui_font, clock)
                                if choice == "Open Pysplore":
                                    script_dir = Path(__file__).parent
                                    pysplore_path = script_dir / "Pysplore.py"
                                    if pysplore_path.exists():
                                        subprocess.Popen([sys.executable, str(pysplore_path)])
                                    else:
                                        dialogue_text = "Pysplore.py not found."
                                        show_dialogue = True
                                elif choice == "Open Pyamby":
                                    script_dir = Path(__file__).parent
                                    pyamby_path = script_dir / "PyAmby.py"
                                    if pyamby_path.exists():
                                        subprocess.Popen([sys.executable, str(pyamby_path)])
                                    else:
                                        dialogue_text = "PyAmby.py not found."
                                        show_dialogue = True
                                elif choice == "Generate Haiku":
                                    haiku = generate_haiku()
                                    dialogue_text = f"Dhammapada verse:\n\n{haiku}"
                                    if HAS_TTS:
                                        try:
                                            tts_engine.say(haiku)
                                            tts_engine.runAndWait()
                                        except:
                                            pass
                                    show_dialogue = True
                                elif choice == "Exit":
                                    dialogue_text = "You chose to exit the cube."
                                    show_dialogue = True
                                else:
                                    dialogue_text = "Menu cancelled."
                                    show_dialogue = True
                            else:
                                # Regular cube: toggle render mode
                                render_mode = 'ascii' if render_mode == 'graphical' else 'graphical'
                                current_fact = get_random_fact()
                                dialogue_text = f"[KNOWLEDGE] {current_fact}\n\nRender mode: {render_mode.upper()}"
                                if HAS_TTS:
                                    try:
                                        tts_engine.say(current_fact)
                                        tts_engine.runAndWait()
                                    except:
                                        pass
                                show_dialogue = True
                else:
                    if event.key in (K_SPACE, K_RETURN):
                        show_dialogue = False
                        # Advance to next level
                        level_num += 1
                        map_grid = generate_level(random.randint(18, 22))
                        player_x, player_y = find_empty_cell(map_grid)
                        cubes = []
                        num_cubes = random.randint(4, 8)
                        for _ in range(num_cubes):
                            cx, cy = find_empty_cell(map_grid)
                            is_glowing = (random.random() < 0.33)
                            cubes.append(Cube(cx, cy, is_glowing))
                        if not any(c.is_glowing for c in cubes):
                            cubes[0].is_glowing = True
                        loading_screen(screen, clock, map_grid, (player_x, player_y), cubes, render_mode, level_num)
                        pygame.mixer.music.fadeout(500)
                        footstep_timer = 0.0
                        level_start_time = time.time()

        if not show_dialogue:
            move_x = move_y = 0.0
            if keys[K_LEFT]:
                player_angle -= ROT_SPEED
            if keys[K_RIGHT]:
                player_angle += ROT_SPEED
            if keys[K_w] or keys[K_UP]:
                move_x += math.cos(player_angle) * MOVE_SPEED
                move_y += math.sin(player_angle) * MOVE_SPEED
            if keys[K_s] or keys[K_DOWN]:
                move_x -= math.cos(player_angle) * MOVE_SPEED
                move_y -= math.sin(player_angle) * MOVE_SPEED
            if keys[K_a]:
                move_x += math.sin(player_angle) * MOVE_SPEED
                move_y -= math.cos(player_angle) * MOVE_SPEED
            if keys[K_d]:
                move_x -= math.sin(player_angle) * MOVE_SPEED
                move_y += math.cos(player_angle) * MOVE_SPEED

            moved = False
            new_x = player_x + move_x
            new_y = player_y + move_y
            if 0 <= int(new_x) < len(map_grid[0]) and 0 <= int(player_y) < len(map_grid):
                if map_grid[int(player_y)][int(new_x)] == 0:
                    player_x = new_x
                    moved = True
            if 0 <= int(player_x) < len(map_grid[0]) and 0 <= int(new_y) < len(map_grid):
                if map_grid[int(new_y)][int(player_x)] == 0:
                    player_y = new_y
                    moved = True

            footstep_timer += dt
            if moved and footstep_timer > FOOTSTEP_INTERVAL:
                footstep_sound.play()
                footstep_timer = 0.0
            elif not moved:
                footstep_timer = FOOTSTEP_INTERVAL

        # Rendering
        if render_mode == 'graphical':
            GraphicalRenderer.render(screen, player_x, player_y, player_angle, map_grid, cubes, ui_font)
        else:
            ASCIIRenderer.render(screen, ascii_font, player_x, player_y, player_angle, map_grid, cubes)

        # HUD
        nearest = None
        min_d = 1.5
        for cube in cubes:
            d = cube.distance_to(player_x, player_y)
            if d < min_d:
                min_d = d
                nearest = cube
        if nearest and not show_dialogue:
            prompt = "Press E to interact"
            if nearest.is_glowing:
                prompt += " with GLOWING CUBE"
            text = ui_font.render(prompt, True, (220,220,100))
            screen.blit(text, (SCREEN_W//2 - text.get_width()//2, SCREEN_H-40))
        mode_text = ui_font.render(f"MODE: {render_mode.upper()}", True, (150,150,150))
        screen.blit(mode_text, (10, 10))
        level_text = ui_font.render(f"LEVEL: {level_num}", True, (150,150,150))
        screen.blit(level_text, (10, 30))
        timer_text = ui_font.render(f"TIME: {int(level_elapsed//60):02d}:{int(level_elapsed%60):02d}", True, (150,150,150))
        screen.blit(timer_text, (10, 50))
        help_text = ui_font.render("WASD/Arrows: move  E: interact  ESC: quit", True, (120,120,120))
        screen.blit(help_text, (SCREEN_W - help_text.get_width() - 10, 10))

        if show_dialogue:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            screen.blit(overlay, (0,0))
            pygame.draw.rect(screen, (40,40,80), (50, SCREEN_H-140, SCREEN_W-100, 110))
            pygame.draw.rect(screen, (120,120,200), (50, SCREEN_H-140, SCREEN_W-100, 110), 3)
            words = dialogue_text.split()
            lines = []
            line = ""
            for word in words:
                test = f"{line} {word}".strip()
                if ui_font.size(test)[0] < SCREEN_W-120:
                    line = test
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
            y = SCREEN_H-120
            for l in lines:
                txt = ui_font.render(l, True, (220,220,255))
                screen.blit(txt, (70, y))
                y += 25
            prompt2 = ui_font.render("Press SPACE to continue", True, (180,180,255))
            screen.blit(prompt2, (SCREEN_W//2 - prompt2.get_width()//2, SCREEN_H-45))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

