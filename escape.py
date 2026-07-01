import pygame as game
import random
import math
import os

# --- UI CLASSES ---
class Button:
    def __init__(self, x, y, width, height, text, font, bg_color, text_color, hover_color, image=None):
        self.rect = game.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color
        self.image = image
        if image:
            self.image = game.transform.scale(image, (width, height))
        self.is_hovered = False

    def draw(self, surface):
        action = False
        pos = game.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(pos)
        
        if self.is_hovered and game.mouse.get_pressed()[0] == 1:
            action = True
            
        color = self.hover_color if self.is_hovered else self.bg_color
        
        if self.image:
            surface.blit(self.image, self.rect)
            if self.is_hovered:
                overlay = game.Surface((self.rect.width, self.rect.height), game.SRCALPHA)
                overlay.fill((255, 255, 255, 50))
                surface.blit(overlay, self.rect)
        else:
            game.draw.rect(surface, color, self.rect, border_radius=10)
            game.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=10)
        
        if self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            # outline
            outline_surf = self.font.render(self.text, True, (0,0,0))
            surface.blit(outline_surf, (text_rect.x+2, text_rect.y+2))
            surface.blit(text_surf, text_rect)
            
        return action

class Slider:
    def __init__(self, x, y, w, h, initial_val, min_val, max_val):
        self.rect = game.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.grabbed = False

    def draw(self, surface):
        pos = game.mouse.get_pos()
        click = game.mouse.get_pressed()[0]
        
        if self.rect.collidepoint(pos) and click:
            self.grabbed = True
        if not click:
            self.grabbed = False
            
        if self.grabbed:
            rel_x = max(self.rect.x, min(pos[0], self.rect.x + self.rect.width))
            percent = (rel_x - self.rect.x) / self.rect.width
            self.val = self.min_val + percent * (self.max_val - self.min_val)

        game.draw.rect(surface, (100, 100, 100), self.rect, border_radius=self.rect.height//2)
        fill_w = int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        if fill_w > 0:
            fill_rect = game.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            game.draw.rect(surface, (0, 200, 0), fill_rect, border_radius=self.rect.height//2)
        game.draw.circle(surface, (255, 255, 255), (self.rect.x + fill_w, self.rect.y + self.rect.height//2), self.rect.height)

        return self.val

def draw_text(screen, text, font, text_col, x, y, center=False):
    img = font.render(text, True, text_col)
    if center:
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)
    else:
        screen.blit(img, (x, y))

# --- GAME CLASSES ---
class Weapon(game.sprite.Sprite):
    def __init__(self, weapon_id):
        self.weapon_id = weapon_id
        self.richocet = None
        self.radius = None
        self.timer = None
        if weapon_id == 1:
            self.damage = 35  # Guclendirildi
            self.attack_speed = 3.0 # Guclendirildi (saniyede 3 atis)
            self.richocet = 2
            self.timer = 1
        if weapon_id == 2:
            self.damage = 100 # Guclendirildi
            self.attack_speed = 1.5 # Guclendirildi
            self.radius = 120

class Explosion(game.sprite.Sprite):
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = 0

class Particle(game.sprite.Sprite):
    def __init__(self, start_pos, enemy_pos, player):
        self.speed = player.proj_speed
        self.dif_x = enemy_pos.x - start_pos.x
        self.dif_y = enemy_pos.y - start_pos.y
        self.particle_position = start_pos.copy()
        self.richocet = player.richocet
        self.timer = 0
        self.lastHit = None

    def move(self, dt):
        try:
            temp = self.speed / (abs(self.dif_x) + abs(self.dif_y))
        except ZeroDivisionError:
            temp = self.speed
        self.particle_position.y += temp * self.dif_y * dt
        self.particle_position.x += temp * self.dif_x * dt

    def change_direction(self, enemy_list, e):
        enemy = self.closest_enemy(enemy_list, e)
        if enemy == None:
            return False
        enemy_pos = enemy.position
        self.dif_x = enemy_pos.x - self.particle_position.x
        self.dif_y = enemy_pos.y - self.particle_position.y
        return True
    
    def closest_enemy(self, enemy_list, e):
        closest_distance = 100000
        return_enemy = None
        for enemy in enemy_list:
            temp = math.sqrt((self.particle_position.x - enemy.position.x)**2 + (self.particle_position.y - enemy.position.y)**2)
            if temp < closest_distance and enemy != e:
                closest_distance = temp
                return_enemy = enemy
        return return_enemy

class Player(game.sprite.Sprite):
    def __init__(self, screen, weapon):
        game.sprite.Sprite.__init__(self)
        self.weapon = weapon
        self.richocet = weapon.richocet
        self.proj_speed = 600
        self.attack_speed = weapon.attack_speed
        self.level = 1
        self.xp = 0
        self.isAlive = True
        self.max_health = 1000
        self.health = 1000
        self.damage = weapon.damage
        self.speed = 250
        self.player_position = game.Vector2(screen.get_width() / 2, screen.get_height() / 2)

    def closest_enemy(self, enemy_list):
        closest_distance = 100000
        return_enemy = None
        for enemy in enemy_list:
            temp = math.sqrt((self.player_position.x - enemy.position.x)**2 + (self.player_position.y - enemy.position.y)**2)
            if temp < closest_distance:
                closest_distance = temp
                return_enemy = enemy
        return return_enemy
    
    def level_up_stat(self, choice):
        # 1: Attack Speed, 2: Damage, 3: Movement Speed, 4: Heal/Max Health
        if choice == 1:
            self.attack_speed += 0.5
            self.weapon.attack_speed += 0.5
        elif choice == 2:
            self.damage += 20
            self.weapon.damage += 20
        elif choice == 3:
            self.speed += 30
        elif choice == 4:
            self.max_health += 300
            self.health = self.max_health
        self.level += 1
        
        # Weapon evolutions
        if self.weapon.weapon_id == 1:
            self.weapon.timer += 1
            if self.weapon.timer % 3 == 0:
                self.weapon.richocet += 1
                self.richocet = self.weapon.richocet
        if self.weapon.weapon_id == 2:
            self.weapon.radius += 10

class Enemy(game.sprite.Sprite):
    def __init__(self, screen, health, speed, size, id):
        game.sprite.Sprite.__init__(self)
        self.size = size 
        self.id = id
        self.health = health
        self.damage = 1
        self.speed = speed
        self.maxhealth = health
        r = random.randint(1 ,4)
        self.height = screen.get_height()
        self.width = screen.get_width()
        if r == 1:
            self.position = game.Vector2(-10, random.randint(0, self.height))
            if id == 33:
                self.dir_x = 1
                self.dir_y = 0
        if r == 2:
            self.position = game.Vector2(self.width + 10, random.randint(0, self.height))
            if id == 33:
                self.dir_x = -1
                self.dir_y = 0
        if r == 3:
            self.position = game.Vector2(random.randint(0, self.width), -10)
            if id == 33:
                self.dir_x = 0
                self.dir_y = 1
        if r == 4:
            self.position = game.Vector2(random.randint(0, self.width), self.height + 10)
            self.dir_x = 0
            self.dir_y = -1
        
    def enemy_move(self, player, dt):
        dif_x = player.player_position.x - self.position.x
        dif_y = player.player_position.y - self.position.y
        try:
            temp = self.speed / (abs(dif_x) + abs(dif_y))
        except ZeroDivisionError:
            temp = 0
        self.position.y += temp * dif_y * dt
        self.position.x += temp * dif_x * dt
    
    def kaan_move(self, dt):
        self.position.x += dt * self.dir_x * self.speed
        self.position.y += dt * self.dir_y * self.speed
        if self.position.x < -20 or self.position.x > self.width + 20 or self.position.y < -20 or self.position.y > self.height + 20:
            self.dir_x *= -1
            self.dir_y *= -1

# --- STATE CONSTANTS ---
STATE_WEAPON_SELECT = 0
STATE_PLAYING = 1
STATE_LEVEL_UP = 2
STATE_PAUSED = 3
STATE_GAME_OVER = 4

def reset_game():
    return (
        100, 0, 20, 70, 1000, 0, 0, 0, 0, 0, 
        [], [], [], [], {"onur":False, "umut":False}, 
        STATE_WEAPON_SELECT, None
    )

def main():
    game.init()
    game.mixer.init()
    
    shot_sound = game.mixer.Sound("assets/audio/Shot.ogg")
    bomb_sound = game.mixer.Sound("assets/audio/bomb.ogg")
    game.mixer.music.load("assets/audio/music.ogg")
    game.mixer.music.play(-1)
    
    music_vol = 0.5
    sfx_vol = 0.5
    game.mixer.music.set_volume(music_vol)
    shot_sound.set_volume(sfx_vol)
    bomb_sound.set_volume(sfx_vol)

    # 2K ekran sorununu cozmek icin yerel cozunurlukte tam ekran (0,0)
    screen = game.display.set_mode((0, 0), game.FULLSCREEN)
    sw = screen.get_width()
    sh = screen.get_height()
    game.display.set_caption("Escape From Friends")
    timer = game.time.Clock()
    game.mouse.set_visible(True)
    
    font_large = game.font.SysFont('arial', 80, bold=True)
    font = game.font.SysFont('arial', 60, bold=True)
    font2 = game.font.SysFont('arial', 30, bold=True)
    font3 = game.font.SysFont('arial', 22, bold=True) # Istatistikler icin daha kucuk font
    
    # Boss images
    enemy_image = game.image.load("assets/images/enemy.png").convert_alpha()
    umut_image = game.image.load("assets/images/umut.png").convert_alpha()
    mami_image = game.image.load("assets/images/mami.png").convert_alpha()
    kaan_image = game.image.load("assets/images/kaan.png").convert_alpha()
    eren_image = game.image.load("assets/images/eren.png").convert_alpha()

    white = (255, 255, 255)
    running = True
    
    (max_xp, score, enemy_health, enemy_speed, spawn_interval, 
     last_spawn_time, last_shot_time, last_mami_spawn, last_kaan_spawn, 
     last_eren_spawn, enemy_list, boss_list, particle_list, explosion_list, 
     boss_spawn_flags, state, player) = reset_game()

    # Ortali UI Elements
    btn_weapon_1 = Button(sw//2 - 380, sh//2 - 100, 350, 200, "Sektirgeç", font, (50,50,200), white, (100,100,255))
    btn_weapon_2 = Button(sw//2 + 30, sh//2 - 100, 350, 200, "Patlangaç", font, (200,50,50), white, (255,100,100))
    
    # Seviye Atlama butonlarini ortalama
    btn_lvl_atk_spd = Button(sw//2 - 380, sh//2 - 100, 220, 200, "Saldırı Hızı", font2, (50,50,50), white, (100,100,100))
    btn_lvl_dmg = Button(sw//2 - 110, sh//2 - 100, 220, 200, "Hasar", font2, (50,50,50), white, (100,100,100))
    btn_lvl_spd = Button(sw//2 + 160, sh//2 - 100, 220, 200, "Hareket Hızı", font2, (50,50,50), white, (100,100,100))
    btn_lvl_heal = Button(sw//2 - 200, sh//2 + 150, 400, 100, "İyileş & Maks Can", font2, (50,150,50), white, (100,200,100))
    
    btn_resume = Button(sw//2 - 200, sh//2 + 50, 400, 80, "Devam Et", font, (50,150,50), white, (100,200,100))
    btn_restart = Button(sw//2 - 250, sh//2 + 150, 500, 80, "Yeniden Başlat", font, (200,150,50), white, (255,200,100))
    btn_quit = Button(sw//2 - 200, sh//2 + 250, 400, 80, "Çıkış", font, (200,50,50), white, (255,100,100))
    slider_music = Slider(sw//2 - 150, sh//2 - 150, 300, 20, music_vol, 0.0, 1.0)
    slider_sfx = Slider(sw//2 - 150, sh//2 - 50, 300, 20, sfx_vol, 0.0, 1.0)
    
    mouse_was_pressed = False
    dt = 0
    i_rot = 0
    
    while running:
        current_time = game.time.get_ticks()
        mouse_pressed = game.mouse.get_pressed()[0] == 1
        mouse_clicked = mouse_pressed and not mouse_was_pressed
        mouse_was_pressed = mouse_pressed
        
        for event in game.event.get():
            if event.type == game.QUIT:
                running = False
            if event.type == game.KEYDOWN:
                if event.key == game.K_ESCAPE:
                    if state == STATE_PLAYING:
                        state = STATE_PAUSED
                    elif state == STATE_PAUSED:
                        state = STATE_PLAYING
                
        screen.fill((30, 30, 40)) # Arka plani biraz koyulastirdik
        
        if state == STATE_WEAPON_SELECT:
            draw_text(screen, "Escape From Friends", font_large, white, sw//2, 200, center=True)
            draw_text(screen, "Silahını Seç", font, (200,200,200), sw//2, 300, center=True)
            
            if btn_weapon_1.draw(screen) and mouse_clicked:
                weapon = Weapon(1)
                player = Player(screen, weapon)
                state = STATE_PLAYING
                game.mouse.set_visible(False)
            if btn_weapon_2.draw(screen) and mouse_clicked:
                weapon = Weapon(2)
                player = Player(screen, weapon)
                state = STATE_PLAYING
                game.mouse.set_visible(False)
                
        elif state == STATE_PLAYING:
            if player.health <= 0:
                state = STATE_GAME_OVER
                game.mouse.set_visible(True)
                continue
                
            if player.xp >= max_xp:
                state = STATE_LEVEL_UP
                game.mouse.set_visible(True)
                continue

            keys = game.key.get_pressed()
            if keys[game.K_w]: player.player_position.y -= player.speed * dt
            if keys[game.K_s]: player.player_position.y += player.speed * dt
            if keys[game.K_d]: player.player_position.x += player.speed * dt
            if keys[game.K_a]: player.player_position.x -= player.speed * dt 
            
            player.player_position.x = max(0, min(sw, player.player_position.x))
            player.player_position.y = max(0, min(sh, player.player_position.y))
            
            # Difficulty & Spawns (Daha dengeli artacak)
            spawn_interval = max(100, 1000 - int(score * 2.0))
            enemy_speed = 70 + (score * 0.1)
            enemy_health = 20 + (score * 0.8)

            if current_time - last_spawn_time > spawn_interval:
                spawns = random.randint(2, 4) if spawn_interval < 200 else 1
                for _ in range(spawns):
                    enemy = Enemy(screen, enemy_health, enemy_speed, 20, 1)
                    enemy_list.append(enemy)
                last_spawn_time = current_time

            # Boss Logic (Gelmeleri daha erken ve netlestirildi)
            if score >= 50 and not boss_spawn_flags["onur"]:
                boss = Enemy(screen, 3000, enemy_speed + 10, 100, 30)
                boss_list.append(boss); enemy_list.append(boss)
                boss_spawn_flags["onur"] = True
            
            if score >= 100:
                if current_time - last_mami_spawn > 3000:
                    if sum(1 for b in boss_list if b.id == 32) < 5:
                        b_speed = max(150, enemy_speed * 1.5)
                        boss = Enemy(screen, enemy_health * 3, b_speed, 5, 32)
                        boss_list.append(boss); enemy_list.append(boss)
                        last_mami_spawn = current_time
                        
            if score >= 200:
                if current_time - last_kaan_spawn > 5000:
                    if sum(1 for b in boss_list if b.id == 33) < 3:
                        b_speed = max(225, enemy_speed * 2)
                        boss = Enemy(screen, enemy_health * 2, b_speed, 40, 33)
                        boss_list.append(boss); enemy_list.append(boss)
                        last_kaan_spawn = current_time
                        
            if score >= 300:
                if current_time - last_eren_spawn > 6000:
                    if sum(1 for b in boss_list if b.id == 34) < 2:
                        b_speed = enemy_speed * 2
                        boss = Enemy(screen, enemy_health * 5, b_speed, 40, 34)
                        boss_list.append(boss); enemy_list.append(boss)
                        last_eren_spawn = current_time
                        
            if score >= 500 and not boss_spawn_flags["umut"]:
                boss = Enemy(screen, 10000, enemy_speed + 20, 200, 31)
                boss_list.append(boss); enemy_list.append(boss)
                boss_spawn_flags["umut"] = True
                
            fire_rate_ms = max(50, int(1000 / player.attack_speed))
            if current_time - last_shot_time > fire_rate_ms and len(enemy_list) > 0:
                cls_enemy = player.closest_enemy(enemy_list)
                if cls_enemy:
                    shot_sound.play()
                    particle_list.append(Particle(player.player_position, cls_enemy.position, player))
                    last_shot_time = current_time

            for enemy in enemy_list:
                if enemy.id == 33:
                    enemy.kaan_move(dt)
                else:
                    enemy.enemy_move(player, dt)
                    
                if (player.player_position.x < enemy.position.x + enemy.size
                    and player.player_position.x + 20 > enemy.position.x
                    and player.player_position.y < enemy.position.y + enemy.size
                    and player.player_position.y + 20 > enemy.position.y):
                    player.health -= enemy.damage * dt * 100

            for particle in particle_list:
                particle.move(dt)

            for explosion in explosion_list:
                explosion.radius += 200 * dt
                if explosion.radius >= 150:
                    explosion_list.remove(explosion)

            particles_to_remove = []
            for particle in particle_list:
                hit = False
                for enemy in enemy_list:
                    if (particle.particle_position.x < enemy.position.x + 20
                        and particle.particle_position.x + 10 > enemy.position.x
                        and particle.particle_position.y < enemy.position.y + 20
                        and particle.particle_position.y + 10 > enemy.position.y):
                        
                        if particle.lastHit == enemy:
                            continue
                        particle.lastHit = enemy
                        hit = True
                        
                        if weapon.weapon_id == 1:
                            particle.speed = min(800, particle.speed * 2)
                            enemy.health -= player.damage
                            
                            particle.timer += 1
                            if particle.timer >= particle.richocet or not particle.change_direction(enemy_list, enemy):
                                particles_to_remove.append(particle)
                                
                        elif weapon.weapon_id == 2:
                            bomb_sound.play()
                            enemy.health -= player.damage
                            particles_to_remove.append(particle)
                            explosion_list.append(Explosion(particle.particle_position, 10))
                            
                            for enemy1 in enemy_list:
                                dist = math.sqrt((particle.particle_position.x - enemy1.position.x)**2 + (particle.particle_position.y - enemy1.position.y)**2)
                                if dist <= weapon.radius:
                                    enemy1.health -= player.damage
                        break
                
                if not hit and (particle.particle_position.x < 0 or particle.particle_position.x > sw or
                                particle.particle_position.y < 0 or particle.particle_position.y > sh):
                    particles_to_remove.append(particle)

            for p in set(particles_to_remove):
                if p in particle_list:
                    particle_list.remove(p)

            enemies_to_remove = []
            for enemy in enemy_list:
                if enemy.health <= 0:
                    enemies_to_remove.append(enemy)
                    if enemy in boss_list:
                        boss_list.remove(enemy)
                        player.xp += max(30, enemy.maxhealth / 10)
                        score += 20
                    else:
                        player.xp += 10
                        score += 1
            for e in enemies_to_remove:
                if e in enemy_list:
                    enemy_list.remove(e)

            # Draw Grid
            for x in range(0, sw, 100):
                game.draw.line(screen, (50,50,60), (x,0), (x,sh))
            for y in range(0, sh, 100):
                game.draw.line(screen, (50,50,60), (0,y), (sw,y))

            # Draw Player
            game.draw.circle(screen, (0, 200, 0), player.player_position, 20)
            
            # Draw Enemies
            i_rot = (i_rot + 100 * dt) % 360
            for enemy in enemy_list:
                if enemy in boss_list:
                    pos4 = enemy.position.copy()
                    if enemy.id == 30:
                        pos4.x -= 70; pos4.y -= 70
                        screen.blit(enemy_image, pos4)
                    elif enemy.id == 31:
                        pos4.x -= 150; pos4.y -= 150
                        screen.blit(umut_image, pos4)
                    elif enemy.id == 32:
                        pos4.x -= 20; pos4.y -= 20
                        screen.blit(mami_image, pos4)
                    elif enemy.id == 33:
                        pos4.x -= 60; pos4.y -= 60
                        screen.blit(kaan_image, pos4)
                    elif enemy.id == 34:
                        pos4.x -= 60; pos4.y -= 60
                        new = game.transform.rotate(eren_image, i_rot)
                        screen.blit(new, pos4)
                    game.draw.rect(screen, "red", game.Rect(enemy.position.x - 20, enemy.position.y - 30, (enemy.health / enemy.maxhealth * 40), 5))
                else:
                    game.draw.circle(screen, "black", enemy.position, 15)
                    game.draw.rect(screen, "red", game.Rect(enemy.position.x - 15, enemy.position.y - 20, (enemy.health / enemy.maxhealth * 30), 4))

            # Draw Particles
            for particle in particle_list:
                if weapon.weapon_id == 1:
                    polygon_points = [(particle.particle_position.x + 5, particle.particle_position.y), 
                                      (particle.particle_position.x, particle.particle_position.y + 5), 
                                      (particle.particle_position.x - 5, particle.particle_position.y), 
                                      (particle.particle_position.x, particle.particle_position.y - 5)]
                    game.draw.polygon(screen, "cyan", polygon_points)
                elif weapon.weapon_id == 2:
                    game.draw.circle(screen, "red", particle.particle_position, 8)

            for explosion in explosion_list:
                alpha = max(0, 255 - int(explosion.radius * 1.5))
                surf = game.Surface((explosion.radius*2, explosion.radius*2), game.SRCALPHA)
                game.draw.circle(surf, (255, 165, 0, alpha), (explosion.radius, explosion.radius), explosion.radius)
                screen.blit(surf, (explosion.pos.x - explosion.radius, explosion.pos.y - explosion.radius))

            # HUD
            game.draw.rect(screen, (50, 50, 50), (20, 20, 300, 30), border_radius=15)
            hp_ratio = max(0, player.health / player.max_health)
            if hp_ratio > 0:
                game.draw.rect(screen, (200, 50, 50), (20, 20, 300 * hp_ratio, 30), border_radius=15)
            draw_text(screen, f"Can: {int(player.health)}/{int(player.max_health)}", font2, white, 170, 35, center=True)
            
            draw_text(screen, f"Skor: {score}", font, white, sw//2, 40, center=True)
            draw_text(screen, f"Seviye: {player.level}", font, white, sw - 150, 40, center=True)
            stats_text = f"Hasar: {int(player.damage)} | Hız: {int(player.speed)} | Saldırı Hızı: {player.attack_speed:.2f}"
            draw_text(screen, stats_text, font3, (200,200,200), sw - 200, 80, center=True)
            
            game.draw.rect(screen, (50, 50, 50), (100, sh - 40, sw - 200, 20), border_radius=10)
            xp_ratio = min(1.0, player.xp / max_xp)
            if xp_ratio > 0:
                game.draw.rect(screen, (50, 200, 255), (100, sh - 40, (sw - 200) * xp_ratio, 20), border_radius=10)
            draw_text(screen, f"XP: {int(player.xp)}/{int(max_xp)}", font2, white, sw//2, sh - 30, center=True)

        elif state == STATE_LEVEL_UP:
            overlay = game.Surface((sw, sh), game.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0,0))
            
            draw_text(screen, "SEVİYE ATLADIN!", font_large, (255,215,0), sw//2, sh//2 - 250, center=True)
            draw_text(screen, "Bir geliştirme seç:", font, white, sw//2, sh//2 - 170, center=True)
            
            if btn_lvl_atk_spd.draw(screen) and mouse_clicked:
                player.level_up_stat(1)
                player.xp -= max_xp
                max_xp += 50
                state = STATE_PLAYING
                game.mouse.set_visible(False)
            if btn_lvl_dmg.draw(screen) and mouse_clicked:
                player.level_up_stat(2)
                player.xp -= max_xp
                max_xp += 50
                state = STATE_PLAYING
                game.mouse.set_visible(False)
            if btn_lvl_spd.draw(screen) and mouse_clicked:
                player.level_up_stat(3)
                player.xp -= max_xp
                max_xp += 50
                state = STATE_PLAYING
                game.mouse.set_visible(False)
            if btn_lvl_heal.draw(screen) and mouse_clicked:
                player.level_up_stat(4)
                player.xp -= max_xp
                max_xp += 50
                state = STATE_PLAYING
                game.mouse.set_visible(False)

        elif state == STATE_PAUSED:
            overlay = game.Surface((sw, sh), game.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0,0))
            game.mouse.set_visible(True)
            
            draw_text(screen, "DURAKLATILDI", font_large, white, sw//2, sh//2 - 250, center=True)
            draw_text(screen, "Müzik Sesi", font2, white, sw//2, sh//2 - 170, center=True)
            draw_text(screen, "Efekt Sesi", font2, white, sw//2, sh//2 - 70, center=True)
            
            new_music_vol = slider_music.draw(screen)
            if new_music_vol != music_vol:
                music_vol = new_music_vol
                game.mixer.music.set_volume(music_vol)
                
            new_sfx_vol = slider_sfx.draw(screen)
            if new_sfx_vol != sfx_vol:
                sfx_vol = new_sfx_vol
                shot_sound.set_volume(sfx_vol)
                bomb_sound.set_volume(sfx_vol)
                
            if btn_resume.draw(screen) and mouse_clicked:
                state = STATE_PLAYING
                game.mouse.set_visible(False)
            
            if btn_restart.draw(screen) and mouse_clicked:
                (max_xp, score, enemy_health, enemy_speed, spawn_interval, 
                 last_spawn_time, last_shot_time, last_mami_spawn, last_kaan_spawn, 
                 last_eren_spawn, enemy_list, boss_list, particle_list, explosion_list, 
                 boss_spawn_flags, state, player) = reset_game()
                 
            if btn_quit.draw(screen) and mouse_clicked:
                running = False

        elif state == STATE_GAME_OVER:
            overlay = game.Surface((sw, sh), game.SRCALPHA)
            overlay.fill((50, 0, 0, 10))
            screen.blit(overlay, (0,0))
            
            draw_text(screen, "OYUN BİTTİ", font_large, (255, 50, 50), sw//2, sh//2 - 50, center=True)
            draw_text(screen, f"Toplam Skor: {score}", font, white, sw//2, sh//2 + 50, center=True)
            draw_text(screen, "Yeniden başlamak için BOŞLUK, çıkmak için ESC", font2, (200,200,200), sw//2, sh//2 + 120, center=True)
            
            keys = game.key.get_pressed()
            if keys[game.K_SPACE]:
                try:
                    with open("HighScore.txt", "r") as f:
                        hs = int(f.read() or 0)
                except FileNotFoundError:
                    hs = 0
                if score > hs:
                    with open("HighScore.txt", "w") as f:
                        f.write(str(score))
                
                (max_xp, score, enemy_health, enemy_speed, spawn_interval, 
                 last_spawn_time, last_shot_time, last_mami_spawn, last_kaan_spawn, 
                 last_eren_spawn, enemy_list, boss_list, particle_list, explosion_list, 
                 boss_spawn_flags, state, player) = reset_game()
                 
            if keys[game.K_ESCAPE]:
                running = False
                
        game.display.flip()
        dt = timer.tick(120) / 1000.0

    game.quit()

if __name__ == "__main__":
    main()