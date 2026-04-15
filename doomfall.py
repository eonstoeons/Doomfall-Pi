#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOOMFALL PI v1.0 — Robust Hybrid Engine Test
Self‑installing · Pure Python · DOOM renderer + Daggerfall scale
"""
import sys
import subprocess
import os
import time
import math
import random
from collections import deque

# -----------------------------------------------------------------------------
# 0. AUTO‑INSTALLER – guaranteed to work
# -----------------------------------------------------------------------------
def install_package(pkg):
    """Install a package using pip, with fallback flags."""
    try:
        __import__(pkg)
        return True
    except ImportError:
        pass
    print(f"Installing {pkg}...")
    # Try multiple methods
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

# Install required packages
REQUIRED = ["pygame", "pyttsx3"]
for pkg in REQUIRED:
    if not install_package(pkg):
        print(f"ERROR: Could not install {pkg}. Please install manually.")
        sys.exit(1)

# Now safe to import
import pygame
from pygame.locals import *

# Optional TTS
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    HAS_TTS = True
except:
    HAS_TTS = False
    tts_engine = None

# -----------------------------------------------------------------------------
# 1. PYGAME BOOT SCREEN (no tkinter)
# -----------------------------------------------------------------------------
def show_boot_screen(screen, clock):
    """Display a retro boot sequence directly in pygame."""
    font = pygame.font.SysFont("Courier New", 16, bold=True)
    messages = [
        "DOOMFALL PI v1.0",
        "Initializing hybrid engine...",
        "Loading DDA ray caster... [OK]",
        "Mounting test level... [OK]",
        "Starting audio subsystem... [OK]",
        "TTS engine: " + ("READY" if HAS_TTS else "UNAVAILABLE"),
        "",
        "WASD: move   E: interact   ESC: quit",
        "",
        "Press SPACE to begin..."
    ]
    
    y = 100
    for msg in messages:
        text = font.render(msg, True, (0, 255, 0))
        screen.blit(text, (50, y))
        y += 25
        pygame.display.flip()
        time.sleep(0.15)
    
    # Wait for spacebar
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_SPACE:
                waiting = False
        clock.tick(30)

# -----------------------------------------------------------------------------
# 2. SIMPLE PROCEDURAL LEVEL (fixed test area)
# -----------------------------------------------------------------------------
# A small hand-crafted map for testing
TEST_MAP = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1],
]

MAP_WIDTH = len(TEST_MAP[0])
MAP_HEIGHT = len(TEST_MAP)

def is_wall(x, y):
    if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
        return TEST_MAP[y][x] == 1
    return True  # Out of bounds = wall

# -----------------------------------------------------------------------------
# 3. DDA RAY CASTER (Wolfenstein/DOOM style)
# -----------------------------------------------------------------------------
def cast_ray(ray_angle, player_x, player_y):
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
        if is_wall(map_x, map_y):
            hit = True
            
    if side == 0:
        perp_wall_dist = (map_x - player_x + (1 - step_x) / 2) / ray_dir_x
    else:
        perp_wall_dist = (map_y - player_y + (1 - step_y) / 2) / ray_dir_y
        
    return perp_wall_dist, side, map_x, map_y

# -----------------------------------------------------------------------------
# 4. SPRITE OBJECT
# -----------------------------------------------------------------------------
class WorldObject:
    def __init__(self, x, y, obj_type, name, color):
        self.x = x
        self.y = y
        self.type = obj_type
        self.name = name
        self.color = color
        
    def distance_to(self, px, py):
        return math.sqrt((self.x - px)**2 + (self.y - py)**2)

# -----------------------------------------------------------------------------
# 5. MAIN GAME LOOP
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    
    SCREEN_W, SCREEN_H = 800, 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("DOOMFALL PI — Test Level")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier New", 14, bold=True)
    
    # Boot sequence
    show_boot_screen(screen, clock)
    
    # Player start
    player_x, player_y = 2.5, 2.5
    player_angle = 0.0
    move_speed = 0.05
    rot_speed = 0.03
    
    # Test object
    test_object = WorldObject(6.5, 5.5, 'terminal', 'Hack Terminal', (100, 100, 255))
    objects = [test_object]
    
    # Dialogue state
    show_dialogue = False
    dialogue_text = ""
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Input
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if not show_dialogue:
                    if event.key == K_e:
                        # Check for nearby object
                        nearest = None
                        min_dist = 2.0
                        for obj in objects:
                            d = obj.distance_to(player_x, player_y)
                            if d < min_dist:
                                min_dist = d
                                nearest = obj
                        if nearest:
                            if HAS_TTS:
                                tts_engine.say(f"You found a {nearest.name}.")
                                tts_engine.runAndWait()
                            show_dialogue = True
                            dialogue_text = f"You examine the {nearest.name}. It hums quietly."
                else:
                    if event.key in (K_SPACE, K_RETURN):
                        show_dialogue = False
        
        if not show_dialogue:
            # Movement
            if keys[K_LEFT]:
                player_angle -= rot_speed
            if keys[K_RIGHT]:
                player_angle += rot_speed
                
            move_x = move_y = 0.0
            if keys[K_w]:
                move_x += math.cos(player_angle) * move_speed
                move_y += math.sin(player_angle) * move_speed
            if keys[K_s]:
                move_x -= math.cos(player_angle) * move_speed
                move_y -= math.sin(player_angle) * move_speed
            if keys[K_a]:
                move_x += math.sin(player_angle) * move_speed
                move_y -= math.cos(player_angle) * move_speed
            if keys[K_d]:
                move_x -= math.sin(player_angle) * move_speed
                move_y += math.cos(player_angle) * move_speed
                
            new_x = player_x + move_x
            new_y = player_y + move_y
            if not is_wall(int(new_x), int(player_y)):
                player_x = new_x
            if not is_wall(int(player_x), int(new_y)):
                player_y = new_y
        
        # Rendering
        screen.fill((0, 0, 0))
        
        # Ceiling and floor (gradient)
        for y in range(SCREEN_H // 2):
            shade = int(40 * (y / (SCREEN_H // 2)))
            pygame.draw.line(screen, (shade, shade, shade + 30), (0, y), (SCREEN_W, y))
        for y in range(SCREEN_H // 2, SCREEN_H):
            shade = int(60 * ((y - SCREEN_H//2) / (SCREEN_H // 2)))
            pygame.draw.line(screen, (shade, shade + 20, shade), (0, y), (SCREEN_W, y))
        
        # Ray casting
        FOV = math.pi / 3.0
        for col in range(SCREEN_W):
            ray_angle = player_angle - FOV/2 + (col / SCREEN_W) * FOV
            dist, side, _, _ = cast_ray(ray_angle, player_x, player_y)
            
            line_height = min(SCREEN_H, int(SCREEN_H / (dist + 0.01)))
            wall_top = (SCREEN_H - line_height) // 2
            
            # Wall coloring
            if side == 1:
                color = (160, 80, 80)   # East/West darker
            else:
                color = (200, 100, 100)  # North/South lighter
            shade = max(0.4, 1.0 - dist / 12.0)
            color = (int(color[0]*shade), int(color[1]*shade), int(color[2]*shade))
            
            pygame.draw.line(screen, color, (col, wall_top), (col, wall_top + line_height))
        
        # Draw sprites
        sprite_list = []
        for obj in objects:
            dx = obj.x - player_x
            dy = obj.y - player_y
            dist = math.sqrt(dx*dx + dy*dy)
            sprite_angle = math.atan2(dy, dx)
            relative_angle = sprite_angle - player_angle
            # Normalize
            while relative_angle > math.pi:
                relative_angle -= 2*math.pi
            while relative_angle < -math.pi:
                relative_angle += 2*math.pi
            if abs(relative_angle) < FOV/1.5 and dist > 0.5:
                sprite_screen_x = int((relative_angle/(FOV/2) + 1)/2 * SCREEN_W)
                sprite_height = min(SCREEN_H, int(SCREEN_H/(dist + 0.01)))
                sprite_list.append((dist, sprite_screen_x, sprite_height, obj))
        
        sprite_list.sort(key=lambda x: x[0], reverse=True)
        for dist, sx, sh, obj in sprite_list:
            rect = pygame.Rect(sx - sh//2, SCREEN_H//2 - sh//2, sh, sh)
            pygame.draw.rect(screen, obj.color, rect)
            pygame.draw.rect(screen, (255,255,255), rect, 2)
            label = font.render(obj.type[0].upper(), True, (255,255,255))
            screen.blit(label, (sx - label.get_width()//2, SCREEN_H//2 - 8))
        
        # HUD
        pygame.draw.circle(screen, (255,255,255), (SCREEN_W//2, SCREEN_H//2), 3, 1)
        
        # Interaction prompt
        nearest_obj = None
        min_d = 2.0
        for obj in objects:
            d = obj.distance_to(player_x, player_y)
            if d < min_d:
                min_d = d
                nearest_obj = obj
        if nearest_obj and not show_dialogue:
            prompt = font.render(f"Press E to interact with {nearest_obj.name}", True, (220,220,100))
            screen.blit(prompt, (SCREEN_W//2 - prompt.get_width()//2, SCREEN_H-40))
        
        # Dialogue overlay
        if show_dialogue:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            screen.blit(overlay, (0,0))
            pygame.draw.rect(screen, (40,40,80), (50, SCREEN_H-120, SCREEN_W-100, 90))
            pygame.draw.rect(screen, (120,120,200), (50, SCREEN_H-120, SCREEN_W-100, 90), 3)
            txt = font.render(dialogue_text, True, (220,220,255))
            screen.blit(txt, (70, SCREEN_H-100))
            txt2 = font.render("Press SPACE to continue", True, (180,180,255))
            screen.blit(txt2, (SCREEN_W//2 - txt2.get_width()//2, SCREEN_H-60))
        
        # FPS
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (150,150,150))
        screen.blit(fps_text, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

