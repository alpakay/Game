import pygame as game
import random
import math
import time as t
import button as b
import os

def draw_text(screen, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def paused():
    paused = True
    while paused:
        for event in game.event.get():
            if event.type == game.KEYUP:
                if event.key == game.K_SPACE:
                    paused = False
                if event.key == game.K_ESCAPE:
                    game.quit()
            if event.type == game.MOUSEBUTTONDOWN:
                paused = False
            if event.type == game.QUIT:
                game.quit()
                quit()

class Weapon(game.sprite.Sprite):
    def __init__(self, weapon_id):
        self.weapon_id = weapon_id
        self.richocet = None
        self.radius = None
        self.timer = None
        if weapon_id == 1:
            self.damage = 5
            self.attack_speed = 0.9
            self.richocet = 1
            self.timer = 1
        if weapon_id == 2:
            self.damage = 40
            self.attack_speed = 0.33
            self.radius = 80
    def level_up(self, player):
        if self.weapon_id == 1:
            player.damage += 7
            player.attack_speed += 0.12
            self.damage += 5
            self.attack_speed += 0.12
            self.timer += 1
            if self.timer % 5 == 0:
                self.richocet += 1
                player.richocet = self.richocet
        if self.weapon_id == 2:
            player.damage += 20
            player.attack_speed += 0.07
            self.damage += 20
            self.radius += 5
            self.attack_speed += 0.07

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
        self.proj_speed = 300
        self.attack_speed = weapon.attack_speed
        self.level = 1
        self.xp = 0
        self.isAlive = True
        self.health = 1000
        self.damage = weapon.damage
        self.speed = 100
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
    
    def level_up(self, secenek, max_xp):
        if self.xp >= max_xp:
            self.level += 1
            self.xp -= max_xp
            self.weapon.level_up(self)
        



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


def main():
    game.init()
    game.mixer.init()
    shot_sound = game.mixer.Sound("Shot.ogg")
    bomb_sound = game.mixer.Sound("bomb.ogg")
    game.mixer.music.load("music.ogg")
    game.mixer.music.play()
    screen = game.display.set_mode((1920, 1080), game.FULLSCREEN)
    game.display.set_caption("Escape Red")
    timer = game.time.Clock()
    game.mouse.set_visible(False)
    font = game.font.SysFont('Bauhaus 93', 60)
    font2 = game.font.SysFont('Bauhaus 93', 15)
    
    running = True
    leveled_up = False
    evolved = False
    spawnable = True
    
    attack_speed_image = game.image.load("attack_button.png").convert_alpha()
    speed_image = game.image.load("speed_button.png").convert_alpha()
    damage_image = game.image.load("damage_button.png").convert_alpha()
    enemy_image = game.image.load("enemy.png").convert_alpha()
    umut_image = game.image.load("umut.png").convert_alpha()
    mami_image = game.image.load("mami.png").convert_alpha()
    kaan_image = game.image.load("kaan.png").convert_alpha()
    eren_image = game.image.load("eren.png").convert_alpha()

    attack_speed_button = b.Button(0, 715, attack_speed_image, 0.1)
    damage_button = b.Button(0, 765, damage_image, 0.1)
    speed_button = b.Button(0, 815, speed_image, 0.1)
    
    health = 10
    spawn_speed = 0.5 
    tick_clock = 0
    white = (255, 255, 255)
    max_xp = 100
    dt = 0
    score = 0
    speed = 10
    temp = 0
    temp_clock = None
    temp_clock2 = 0
    temp_clock3 = 0
    temp_clock4 = 0
    temp_clock5 = 0
    temp_clock6 = 0
    temp_clock7 = 0
    temp_clock8 = 0
    temp_clock9 = 0
    temp_clock10 = 0
    temp2 = 499
    temp3 = 99
    i = 0
    enemy_list = []
    boss_list = []
    particle_list = []
    explosion_list = []
    
    weapon = Weapon(2)
    player = Player(screen, weapon)
    
    while running:
        for event in game.event.get():
            if event.type == game.QUIT:
                running = False
            if event.type == game.KEYDOWN:
                if event.key == game.K_ESCAPE:
                    running = False
                if event.key == game.K_RCTRL:
                    temp = player.attack_speed
                    player.attack_speed = 10
                if event.key == game.K_i:
                    spawn_speed = 100
            
            if event.type == game.KEYUP:
                if event.key == game.K_SPACE:
                    paused()
                if event.key == game.K_RCTRL:
                    player.attack_speed = temp
        screen.fill("gray")
        if player.health < 1:
            player.isAlive = False
        if player.isAlive == False:
            running = False 
        
        if player.xp >= max_xp:
            leveled_up = True
            temp_clock = tick_clock + 100
            player.proj_speed += 10
        if attack_speed_button.draw(screen):
            player.level_up(1, max_xp)
        elif damage_button.draw(screen):
            player.level_up(2, max_xp)
        elif speed_button.draw(screen):
            player.level_up(3, max_xp)
        else:
            player.level_up(4, max_xp)
        if temp_clock == tick_clock:
            evolved = False
            leveled_up = False
        if evolved == True and tick_clock < temp_clock:
            draw_text(screen, "Evolved!", font2, white, player.player_position.x-28, player.player_position.y-40)
        elif leveled_up == True and tick_clock < temp_clock:
            draw_text(screen, "Level Up!", font2, white, player.player_position.x-28, player.player_position.y-40)
        if player.level % 5 == 0 and temp != player.level:
            temp = player.level
            max_xp += 50
            if weapon.weapon_id == 1:
                evolved = True
                temp_clock = tick_clock + 100
        
        game.draw.circle(screen, "green", player.player_position, 20)
        game.draw.rect(screen, "red", game.Rect(player.player_position.x - 20, player.player_position.y - 30, (player.health / 1000 * 40), 5))
         
        for enemy in enemy_list:
            if enemy in boss_list:
                continue
            game.draw.circle(screen, "black", enemy.position, 20)
            game.draw.rect(screen, "red", game.Rect(enemy.position.x - 20, enemy.position.y - 30, (enemy.health / enemy.maxhealth * 40), 5))
        
        if i == 360:
            i = 0
        i += 10
        for boss in boss_list:
            pos4 = boss.position.copy()
            if boss.id == 30:
                pos4.x -= 70
                pos4.y -= 70
                screen.blit(enemy_image, pos4, None, 0)
            if boss.id == 31:
                pos4.x -= 150
                pos4.y -= 150
                screen.blit(umut_image, pos4, None, 0)
            if boss.id == 32:
                pos4.x -= 20
                pos4.y -= 20
                screen.blit(mami_image, pos4, None, 0)
            if boss.id == 33:
                pos4.x -= 60
                pos4.y -= 60
                screen.blit(kaan_image, pos4, None, 0)
            if boss.id == 34:
                pos4.x -= 60
                pos4.y -= 60
                new = game.transform.rotate(eren_image, i)
                screen.blit(new, pos4, None, 0)
                
            game.draw.rect(screen, "red", game.Rect(boss.position.x - 20, boss.position.y - 30, (boss.health / boss.maxhealth * 40), 5))
        
        for particle in particle_list:
            if weapon.weapon_id == 1:
                polygon_points = [(particle.particle_position.x + 1, particle.particle_position.y + 1), (particle.particle_position.x + 2, particle.particle_position.y), (particle.particle_position.x + 1, particle.particle_position.y - 2), (particle.particle_position.x - 1, particle.particle_position.y - 2), (particle.particle_position.x - 2, particle.particle_position.y)]
                game.draw.polygon(screen, "blue", polygon_points, 10)
            elif weapon.weapon_id == 2:
                game.draw.circle(screen, "red", particle.particle_position, 10)
            particle.move(dt)
        
        for explosion in explosion_list:
            game.draw.circle(screen, "orange", explosion.pos, explosion.radius)
            explosion.radius += 1
            if explosion.radius == 30:
                explosion_list.remove(explosion)
        
        draw_text(screen, str(score), font, white, screen.get_width() / 2 - 25, 20)
        draw_text(screen, str(f"Level: {player.level}"), font2, white, 20, 10)
        draw_text(screen, str(f"XP: {player.xp:.{0}f}"), font2, white, screen.get_width() - 85, 10)
        draw_text(screen, str(f"{player.attack_speed:.{1}f}"), font2, white, 60, 745)
        draw_text(screen, str(player.damage), font2, white, 60, 795)
        draw_text(screen, str(player.speed), font2, white, 60, 845)

        for enemy in enemy_list:
            for particle in particle_list:
                if (particle.particle_position.x < enemy.position.x + 20
                and particle.particle_position.x + 10 > enemy.position.x
                and particle.particle_position.y < enemy.position.y + 20
                and particle.particle_position.y + 10 > enemy.position.y):
                    if particle.lastHit == enemy:
                        continue
                    particle.lastHit = enemy
                    if weapon.weapon_id == 1:
                        particle.speed = particle.speed * 2
                        if particle.speed > 500:
                            particle.speed = 500
                        enemy.health -= player.damage
                        if enemy.health <= 0:
                            if enemy in boss_list:
                                boss_list.remove(enemy)
                                if enemy.health / 10 > 100:
                                            player.xp += 100
                                else:
                                    player.xp += enemy.health / 10
                                score += 20
                            enemy.health = 0
                            if enemy in enemy_list:
                                enemy_list.remove(enemy)
                            player.xp += 10
                            score += 1
                        particle.timer += 1
                        if particle.timer == particle.richocet:
                            particle_list.remove(particle)
                        else:
                            if particle.change_direction(enemy_list, enemy) is False:
                                particle_list.remove(particle)
                       
                    
                    elif weapon.weapon_id == 2:
                        bomb_sound.play()
                        enemy.health -= player.damage
                        if enemy.health <= 0:
                            if enemy in boss_list:
                                boss_list.remove(enemy)
                                if enemy.health / 10 > 100:
                                            player.xp += 100
                                else:
                                    player.xp += enemy.health / 10
                                score += 20
                            enemy.health = 0
                            enemy_list.remove(enemy)
                            player.xp += 10
                            score += 1
                        particle_list.remove(particle)
                        explosion_list.append(Explosion(particle.particle_position, 10))
                        for enemy1 in enemy_list:
                            if (particle.particle_position.x - weapon.radius < enemy1.position.x
                            and particle.particle_position.x + weapon.radius > enemy1.position.x
                            and particle.particle_position.y + weapon.radius > enemy1.position.y
                            and particle.particle_position.y - weapon.radius < enemy1.position.y):
                                enemy1.health -= player.damage
                                if enemy1.health <= 0:
                                    if enemy1 in boss_list:
                                        boss_list.remove(enemy1)
                                        if enemy1.health / 10 > 100:
                                            player.xp += 100
                                        else:
                                            player.xp += enemy1.health / 10
                                        score += 20
                                    enemy_list.remove(enemy1)
                                    player.xp += 10
                                    score += 1

                                
                        


            if (player.player_position.x < enemy.position.x + enemy.size
                and player.player_position.x + 20 > enemy.position.x
                and player.player_position.y < enemy.position.y + enemy.size
                and player.player_position.y + 20 > enemy.position.y
            ):
                player.health -= enemy.damage * dt * 100
            if enemy.id == 33:
                enemy.kaan_move(dt)
            else:
                enemy.enemy_move(player, dt)

        
        keys = game.key.get_pressed()
        if keys[game.K_w]:
            player.player_position.y -= player.speed*dt
        if keys[game.K_s]:
            player.player_position.y += player.speed*dt
        if keys[game.K_d]:
            player.player_position.x += player.speed*dt
        if keys[game.K_a]:
            player.player_position.x -= player.speed*dt 
        
        spawn_rate = 100 / spawn_speed
        try:
            mod = tick_clock % spawn_rate
        except ZeroDivisionError:
            mod = 0
        if mod < 1 and tick_clock != 0:
            enemy = Enemy(screen, health, speed, 20, 1)
            enemy_list.append(enemy)
           
        rate = 100 / player.attack_speed
        try:
            mod = tick_clock % rate
        except ZeroDivisionError:
            mod = 0
        if mod < 1 and enemy_list.count != 0:
            cls_enemy = player.closest_enemy(enemy_list)
            if cls_enemy != None:
                shot_sound.play()
                particle_list.append(Particle(player.player_position, cls_enemy.position, player))
            
        game.display.flip()

        dt = timer.tick(100) / 1000
        if dt > 0.9:
            dt = 0.9
        tick_clock +=1
        
        if tick_clock % 2000 == 0 and tick_clock != 0:
            spawn_speed += 0.5
            speed += 20
        if tick_clock % 6000 == 0 and tick_clock != 0:
            health += 30
        #onur spawn
        if score > 70:
            for boss in boss_list:
                if boss.id == 30:
                    spawnable = False
                    break
                else:
                    spawnable = True
            if spawnable:
                boss = Enemy(screen, 7000, speed + 10, 100, 30)
                boss_list.append(boss)
                enemy_list.append(boss)
        #umut spawn
        if score > 1000:
            for boss in boss_list:
                if boss.id == 31:
                    spawnable = False
                    break
                else:
                    spawnable = True
            if spawnable:
                boss = Enemy(screen, 15000, speed + 25, 200, 31)
                boss_list.append(boss)
                enemy_list.append(boss)
        #mami spawn
        if score > 200 and tick_clock > temp_clock2:
            boss_sayac = 0
            for boss in boss_list:
                if boss.id == 32:
                    boss_sayac += 1
            if boss_sayac < 10:
                speed2 = speed*2
                if speed2 < 150:
                    speed2 = 150
                boss = Enemy(screen, health*2, speed2, 5, 32)
                boss_list.append(boss)
                enemy_list.append(boss)
                temp_clock2 = tick_clock + 100
        #kaan spawn
        if score > 400 and tick_clock > temp_clock3:
            boss_sayac = 0
            for boss in boss_list:
                if boss.id == 33:
                    boss_sayac += 1
            if boss_sayac < 5:
                speed3 = speed*3
                if speed3 < 225:
                    speed3 = 225
                boss = Enemy(screen, health, speed3, 40, 33)
                boss_list.append(boss)
                enemy_list.append(boss)
                temp_clock3 = tick_clock + 500
        #eren spawn
        if score > 2000 and tick_clock > temp_clock6:
            if score == 1200:
                spawn_speed = 10
            boss_sayac = 0
            for boss in boss_list:
                if boss.id == 34:
                    boss_sayac += 1
            if boss_sayac < 3:
                boss = Enemy(screen, health, speed*3, 40, 34)
                boss_list.append(boss)
                enemy_list.append(boss)
                temp_clock6 = tick_clock + 200
         
        if score > temp2 and score != 0 and temp_clock4 < tick_clock:
            speed += 40
            spawn_speed += 10
            temp_clock4 = tick_clock + 100
            temp2 += 2000
        if score > temp3 and score != 0 and temp_clock5 < tick_clock:
            player.speed += 10
            temp_clock5 = tick_clock + 100
            temp3 += 100

    over = True
    while over:
        screen.fill("gray")
        draw_text(screen, "Game Over", font, "red", screen.get_width() / 2 - 150, screen.get_height() / 2 - 40)
        draw_text(screen, str(f"Score: {score}"), font, "red", screen.get_width() / 2 - 150, screen.get_height() / 2 + 40 )
        game.display.flip()
        #print("Game Over")
        for event in game.event.get():
            if event.type == game.QUIT:
                over = False
            if event.type == game.KEYDOWN:
                if event.key == game.K_SPACE:
                    main()
                if event.key == game.K_ESCAPE:
                    over = False
        with open("HighScore.txt", "w") as dosyaW:
            with open("HighScore.txt", "r") as dosyaR:
                veri = dosyaR.read()
                if veri:
                    if score > int(veri):
                        dosyaW.write(f"{score}")
                else:
                    dosyaW.write(f"{score}")
        dosyaW.close()
        dosyaR.close()
    game.quit()



main()