# SPACE DODGE REMASTERED

import pygame 
import random
import sys
pygame.init()
pygame.mixer.init()

Width, Height = 1120, 700
window = pygame.display.set_mode((Width, Height), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Space Dodge Remastered")
clock = pygame.time.Clock()
WIN_TIME = 233000
paused = False
in_menu = True


def main_menu():
    menu_font = pygame.font.SysFont("Arial", 48, bold=True)
    title_text = menu_font.render("Space Dodge Remastered", True, (255, 255, 255))
    sub_font = pygame.font.SysFont("Arial", 28)

    blink = True
    blink_timer = 0
    blink_interval = 500 
    escape_hold_start = None

    while True:
        dt = clock.tick(60)  
        blink_timer += dt
        if blink_timer >= blink_interval:
            blink = not blink
            blink_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                music_start_time = pygame.time.get_ticks()
                return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            if escape_hold_start is None:
                escape_hold_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - escape_hold_start >= 1000:
                pygame.quit()
                sys.exit()
        else:
            escape_hold_start = None

        window.blit(background_img, (0, 0))

        window.blit(title_text, (Width // 2 - title_text.get_width() // 2, Height // 2 - 50))

        if blink:
            start_text = sub_font.render("Press SPACE to play", True, (255, 255, 255))
            quit_text = sub_font.render("Hold ESC to quit", True, (255, 255, 255))
            window.blit(start_text, (Width // 2 - start_text.get_width() // 2, Height // 2 + 30))
            window.blit(quit_text, (Width // 2 - quit_text.get_width() // 2, Height // 2 + 70))

        pygame.display.update()




# Asset loading ~
original_player_img = pygame.image.load(r"Assets/sprites/ship.png")
player_img = pygame.transform.scale(original_player_img, (70, 80))
original_missile_img = pygame.image.load(r"Assets/sprites/missile.png")
background_img = pygame.image.load(r"Assets/sprites/background.png")
explosion_img_original = pygame.image.load(r"Assets/sprites/explosion.png")
boom_sound = pygame.mixer.Sound(r"Assets/sfx/boom3.wav")
original_heart_img = pygame.image.load(r"Assets/sprites/heart.png")
heart_img = pygame.transform.scale(original_heart_img, (30, 30)) 
death_sound = pygame.mixer.Sound(r"Assets/sfx/Heartbreak.mp3")
main_theme = pygame.mixer.Sound(r"Assets/sfx/Theme.wav")
zap = pygame.mixer.Sound(r"Assets/sfx/zap.mp3")
burn_sound = pygame.mixer.Sound(r"Assets/sfx/boom5.wav")
laser_damage = pygame.image.load(r"Assets/sprites/laser_damage.png")



# Player settings ~
player_width, player_height = player_img.get_width(), player_img.get_height()
player_x = Width // 2 - player_width // 2
player_y = Height - player_height - 20
vel = 6.5

# loop stuff ~
run = True
background_img = pygame.transform.scale(background_img, (Width, Height +10))
lives = 15
game_over = False
death_sound_played = False
death_time = 0
music_played = False
lasers = []

# For scrolling background ~
bg_y1 = 0
bg_y2 = -Height 
bg_scroll_speed = 2.5

# Missile control ~
missile_width = 50
missile_height = 70
missiles = []
missile_speed = 7
missile_spawn_delay = 2000  
missiles_per_cycle = 3
missile_timer = 0
missile_img_scaled = pygame.transform.scale(original_missile_img, (missile_width, missile_height))
explosion_img = pygame.transform.scale(explosion_img_original, (player_width, player_height))
missile_img = pygame.transform.rotate(missile_img_scaled, 180)
exploding = False
explosion_timer = 0
explosion_duration = 200


# Mask for ppc ~
player_mask = pygame.mask.from_surface(player_img)
missile_mask = pygame.mask.from_surface(missile_img)

class LaserSegment:
    def __init__(self, rect, appear_delay, fade_in_duration, hold_duration, fade_out_duration):
        self.rect = pygame.Rect(rect)
        self.appear_delay = appear_delay
        self.fade_in_duration = fade_in_duration
        self.hold_duration = hold_duration
        self.fade_out_duration = fade_out_duration

        self.alpha = 0
        self.visible = False
        self.disappeared = False
        self.start_time = None

    def update(self, global_time):
        if self.start_time is None and global_time >= self.appear_delay:
            self.start_time = global_time

        if self.start_time is not None:
            elapsed = global_time - self.start_time
            total_life = self.fade_in_duration + self.hold_duration + self.fade_out_duration

            if elapsed < self.fade_in_duration:
                self.alpha = int(255 * (elapsed / self.fade_in_duration))
            elif elapsed < self.fade_in_duration + self.hold_duration:
                self.alpha = 255
            elif elapsed < total_life:
                out_elapsed = elapsed - self.fade_in_duration - self.hold_duration
                self.alpha = int(255 * (1 - (out_elapsed / self.fade_out_duration)))
            else:
                self.alpha = 0
                self.disappeared = True

    def draw(self, surface, color=(255, 255, 255)):
        if self.alpha > 0:
            surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            surf.fill((*color, self.alpha))
            surface.blit(surf, self.rect.topleft)




class Laser:
    def __init__(self, direction, position, warning_time=1600, fire_duration=600, thickness=120, segment_size=7):
        self.direction = direction
        self.position = position
        self.warning_time = warning_time
        self.fire_duration = fire_duration
        self.state = "warning"
        self.start_time = pygame.time.get_ticks()

        self.thickness = thickness
        self.segment_size = segment_size
        self.segments = []

        self.fade_started = False
        self.opacity = 60
        self.warning_blink_interval = 300
        self.zap_played = False
        self.warning_x = position
        self.warning_y = position


    def start_firing(self):
        self.state = "firing"
        self.start_time = pygame.time.get_ticks()
        if not self.zap_played:
            zap.play()
            self.zap_played = True

        self.segments = []
        delay_offset = 50  
        fade_in_duration = 150
        hold_duration = 350
        fade_out_duration = 200

        if self.direction == "vertical":
            count = self.thickness // self.segment_size
            center_index = count // 2
            for i in range(count):
                x = self.position - self.thickness // 2 + i * self.segment_size
                y = 0
                dist = abs(i - center_index)
                appear_delay = dist * delay_offset
                self.segments.append(
                    LaserSegment(
                        rect=(x, y, self.segment_size, Height),
                        appear_delay=appear_delay,                                                                                                             
                        fade_in_duration=fade_in_duration,
                        hold_duration=hold_duration,
                        fade_out_duration=fade_out_duration
                    )
                )
        else:
            count = self.thickness // self.segment_size
            center_index = count // 2
            for i in range(count):
                y = self.position - self.thickness // 2 + i * self.segment_size
                x = 0
                dist = abs(i - center_index)
                appear_delay = dist * delay_offset
                self.segments.append(
                    LaserSegment(
                        rect=(x, y, Width, self.segment_size),
                        appear_delay=appear_delay,
                        fade_in_duration=fade_in_duration,
                        hold_duration=hold_duration,
                        fade_out_duration=fade_out_duration
                    )
                )


    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time

        if self.state == "warning":
            if elapsed >= self.warning_time:
                self.start_firing()

        elif self.state == "firing":
            for seg in self.segments:
                seg.update(elapsed)
            if all(seg.disappeared for seg in self.segments):
                self.state = "done"

    def draw(self, surface):
        if self.state == "done":
            return

        if self.state == "warning":
            blink = (pygame.time.get_ticks() // self.warning_blink_interval) % 2 == 0
            if blink:
                if self.direction == "vertical":
                    strip = pygame.Surface((self.thickness, Height), pygame.SRCALPHA)
                    strip.fill((255, 255, 255, self.opacity))
                    surface.blit(strip, (self.warning_x - self.thickness // 2, 0))
                else:
                    strip = pygame.Surface((Width, self.thickness), pygame.SRCALPHA)
                    strip.fill((255, 255, 255, self.opacity))
                    surface.blit(strip, (0, self.warning_y - self.thickness // 2))

                font = pygame.font.SysFont("Arial", 40, bold=True)
                ex_mark = font.render("!", True, (255, 0, 0))
                if self.direction == "vertical":
                    x = self.warning_x - ex_mark.get_width() // 2
                    y = Height // 2 - ex_mark.get_height() // 2
                else:
                    x = Width // 2 - ex_mark.get_width() // 2
                    y = self.warning_y - ex_mark.get_height() // 2
                surface.blit(ex_mark, (x, y))

        elif self.state == "firing":
            for seg in self.segments:
                seg.draw(surface)


current_time = 0
laser_schedule = [] 
spawned_lasers = set()
invincibility_duration = 1000  
last_hit_time = 0  
win = False
for _ in range(117300, 128000, 900):
                    laser_schedule.append(_)

dummy_val = 0
percent = 0
pause_time_factor = 0
missile_type = ""
game_state_variables = [player_x, player_y, player_mask, missile_timer, missiles, missiles_per_cycle, lasers, spawned_lasers, lives, dummy_val, death_sound_played, death_time, music_played, missile_type, missile_spawn_delay, missile_speed, missile_img, background_img, bg_y1, bg_y2, bg_scroll_speed, exploding, explosion_timer, vel, last_hit_time, win, current_time, percent, pause_time_factor]

def game_loop(player_x, player_y, player_mask, missile_timer, missiles, missiles_per_cycle, lasers, spawned_lasers, lives, dummy_val, death_sound_played, death_time, music_played, missile_type, missile_spawn_delay, missile_speed, missile_img, background_img, bg_y1, bg_y2, bg_scroll_speed, exploding, explosion_timer, vel, last_hit_time, win, current_time, percent, pause_time_factor):
    '''global player_x, player_y, player_mask, missile_timer, missiles, lasers, spawned_lasers
    global lives, game_over, death_sound_played, death_time, music_played
    global missile_type, missile_spawn_delay, missile_speed, missile_img
    global background_img, bg_y1, bg_y2, bg_scroll_speed
    global exploding, explosion_timer, vel, last_hit_time, win, current_time
    global paused

    player_x = Width // 2 - player_width // 2
    player_y = Height - player_height - 20
    missile_timer = 0
    missiles = []
    lasers = []
    spawned_lasers = set()
    lives = 15
    game_over = False
    death_sound_played = False
    death_time = 0
    music_played = False
    missile_type = "top"
    missile_spawn_delay = 2000
    missile_speed = 7
    bg_y1 = 0
    bg_y2 = -Height 
    bg_scroll_speed = 2.5
    exploding = False
    explosion_timer = 0
    vel = 6.5
    last_hit_time = 0
    win = False
    run = True
    clock2 = pygame.time.Clock()
    WIN_TIME = 233000
    font = pygame.font.SysFont("Arial", 40, bold=True)
    current_time = 0'''
    global game_state_variables, paused, game_over
    clock2 = pygame.time.Clock()
    music_start_time = 0 
    run = True
    font = pygame.font.SysFont("Arial", 40, bold = True)
    reinitialise_count = 0
    #pause_time_factor = 0


    while run:
        # The clock for framerates ~
        clock2.tick(120)

        # Setting the QUIT instance ~
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                reinitialise_count = 0
                pause_time = current_time
                game_state_variables = [player_x, player_y, player_mask, missile_timer, missiles, missiles_per_cycle, lasers, spawned_lasers, lives, game_over, death_sound_played, death_time, music_played, missile_type, missile_spawn_delay, missile_speed, missile_img, background_img, bg_y1, bg_y2, bg_scroll_speed, exploding, explosion_timer, vel, last_hit_time, win, current_time, percent, pause_time_factor]
                paused = True
                run = False
                pygame.mixer.pause()
                break

 
        if not game_over:
            # Music timeee ~
            if not music_played:
                main_theme.play()
                music_start_time = pygame.time.get_ticks() 
                music_played = True
            #print("PAUSE TIME FACTOR = ", pause_time_factor)
            current_time = pygame.time.get_ticks() - music_start_time - pause_time_factor
            '''if reinitialise_count < 1:
                pause_time_factor = 0
                reinitialise_count += 1'''


            # Movement init ~
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x - vel > 0:
                player_x -= vel
            if keys[pygame.K_RIGHT] and player_x + vel + player_width < Width:
                player_x += vel
            if keys[pygame.K_UP] and player_y - vel > 0:
                player_y -= vel
            if keys[pygame.K_DOWN] and player_y + vel + player_height < Height:
                player_y += vel
            if keys[pygame.K_a] and player_x - vel > 0:
                player_x -= vel
            if keys[pygame.K_d] and player_x + vel + player_width < Width:
                player_x += vel
            if keys[pygame.K_w] and player_y - vel > 0:
                player_y -= vel
            if keys[pygame.K_s] and player_y + vel + player_height < Height:
                player_y += vel



            # BG ~
            window.fill((0, 0, 0))
            bg_y1 += bg_scroll_speed
            bg_y2 += bg_scroll_speed
            if bg_y1 >= Height:
                bg_y1 = -Height
            if bg_y2 >= Height:
                bg_y2 = -Height
            window.blit(background_img, (0, bg_y1))
            window.blit(background_img, (0, bg_y2))



            # Missile time :D
            missile_timer += clock2.get_time()
            should_spawn_missiles = not (60000 <= current_time < 61900)
            if missile_timer >= missile_spawn_delay and should_spawn_missiles:
                for i in range(missiles_per_cycle):
                    if missile_type == "top":
                        angle = 180
                        missile_img = pygame.transform.rotate(missile_img_scaled, 180)
                        x = random.randint(0, Width - missile_width)
                        y = -missile_height
                        vx, vy = 0, missile_speed

                    elif missile_type == "left":
                        angle = -90
                        missile_img = pygame.transform.rotate(missile_img_scaled, -90)
                        x = -missile_width
                        y = random.randint(0, Height - missile_height)
                        vx, vy = missile_speed, 0

                    elif missile_type == "right":
                        angle = 90
                        missile_img = pygame.transform.rotate(missile_img_scaled, 90)
                        x = Width
                        y = random.randint(0, Height - missile_height)
                        vx, vy = -missile_speed, 0

                    elif missile_type == "bottom":
                        angle = 360
                        missile_img = pygame.transform.rotate(missile_img_scaled, 360)
                        x = random.randint(0, Width - missile_width)
                        y = Height
                        vx, vy = 0, -missile_speed

                    elif missile_type == "diag_tl":
                        angle = -135
                        missile_img = pygame.transform.rotate(missile_img_scaled, -135)
                        x = -missile_width
                        y = -missile_height
                        vx, vy = missile_speed - 2, missile_speed - 2

                    elif missile_type == "diag_tr":
                        angle = 135
                        missile_img = pygame.transform.rotate(missile_img_scaled, 135)
                        x = Width
                        y = -missile_height
                        vx, vy = -(missile_speed - 2), missile_speed - 2


                    rotated_img = pygame.transform.rotate(missile_img_scaled, angle)
                    missiles.append({
                        "rect": pygame.Rect(x, y, rotated_img.get_width(), rotated_img.get_height()),
                        "vel": (vx, vy),
                        "type": missile_type,
                        "img": rotated_img,
                        "mask": pygame.mask.from_surface(rotated_img)
                    })

                missile_timer = 0


            if (not game_over) and (current_time < 233000):
                for missile in missiles[:]:
                    missile["rect"].x += missile["vel"][0]
                    missile["rect"].y += missile["vel"][1]

                    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
                    missile_rect = missile["rect"]
                    offset = (missile_rect.x - player_rect.x, missile_rect.y - player_rect.y)

                    if missile["mask"].overlap(player_mask, offset) and not exploding:
                        exploding = True
                        explosion_timer = pygame.time.get_ticks()
                        if lives > 1:
                            boom_sound.play()
                        lives -= 1
                        if lives > 0:
                            missiles.remove(missile)
                        break

                    if (missile_rect.y > Height or missile_rect.y < -missile_height or
                        missile_rect.x > Width or missile_rect.x < -missile_width):
                        missiles.remove(missile)

            for missile in missiles:
                window.blit(missile["img"], (missile["rect"].x, missile["rect"].y))



            # Drawing lives ~
            for i in range(lives):
                window.blit(heart_img, (Width - (i + 1) * 40 - 10, 10))


            # Drawing the charr onto screen ~
            if exploding:
                if lives < 1:
                    window.blit(player_img, (player_x, player_y))
                else:
                    window.blit(explosion_img, (player_x, player_y))
                vel = 0
                if pygame.time.get_ticks() - explosion_timer >= explosion_duration:
                    if lives < 1:
                        vel = 0
                    else:
                        vel = 6.5
                    exploding = False  
            else:
                window.blit(player_img, (player_x, player_y))



            for laser in lasers[:]:
                laser.update()
                laser.draw(window)
                if laser.state == "done":
                    lasers.remove(laser)
                if laser.state == "firing":
                    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
                    current_time2 = pygame.time.get_ticks()
                    
                    if current_time2 - last_hit_time >= invincibility_duration:
                        for seg in laser.segments:
                            if seg.alpha > 0 and seg.rect.colliderect(player_rect):
                                last_hit_time = current_time2
                                exploding = True
                                explosion_timer = current_time2
                                if lives > 1:
                                    burn_sound.play()
                                lives -= 2
                                break


            if lives <= 0 and not game_over:
                game_over = True
                vel = 0
                bg_scroll_speed = 0
                missile_spawn_delay = float('inf')
                missile_speed = 0
                death_time = pygame.time.get_ticks()
                main_theme.stop()
                if not death_sound_played:
                    death_sound.play()
                    death_sound_played = True
                game_state_variables = [player_x, player_y, player_mask, missile_timer, missiles, missiles_per_cycle, lasers, spawned_lasers, lives, game_over, death_sound_played, death_time, music_played, missile_type, missile_spawn_delay, missile_speed, missile_img, background_img, bg_y1, bg_y2, bg_scroll_speed, exploding, explosion_timer, vel, last_hit_time, win, current_time, percent, pause_time_factor]

                pygame.time.wait(1500)
                break

                

            # Missile audio synk ~
            if current_time < 15000:
                missiles_per_cycle = 3
                missile_speed = 7
                missile_spawn_delay = 2000
                missile_type = "top"
            elif 15000 <= current_time < 30000:
                missiles_per_cycle = 3
                missile_speed = 7
                missile_spawn_delay = 1700
            elif 30000 <= current_time < 43500:
                scale = (current_time - 30000) / 10000 
                missile_spawn_delay = int(2000 - scale * (2000 - 700)) 
            elif 43500 <= current_time < 61900:
                missile_spawn_delay = 300
                missile_speed = 10
                missiles_per_cycle = 4
                bg_scroll_speed = 3.5
            elif 61900 <= current_time <= 95900:
                missile_type = random.choice(["top", "left", "right", "bottom", "diag_tl", "diag_tr"])
                missile_speed = 7
                missiles_per_cycle = 3
                missile_spawn_delay = 700
                bg_scroll_speed = 2.5
            elif 95900 <= current_time < 104000:
                missile_type = "top"
                missile_speed = 7
                missiles_per_cycle = 3
            elif 104000 <= current_time < 106500:
                missile_type = "left"
                missile_speed = 7
                missiles_per_cycle = 3
            elif 106500 <= current_time < 108000:
                missile_type = "right"
                missile_speed = 7
                missiles_per_cycle = 3
            elif 108000 <= current_time < 110000:
                missile_type = "bottom"
                missile_speed = 7
                missiles_per_cycle = 3
            elif 110000 <= current_time < 112300:
                missile_type = random.choice(["diag_tl", "diag_tr"])
                missiles_per_cycle = 2
                missile_speed = 7    
            elif 112300 <= current_time < 125000:
                missiles_per_cycle = 0
                laser_schedule.append(112300)
            elif 128000 <= current_time < 137500:
                missile_type = random.choice(["top", "left", "right", "bottom", "diag_tl", "diag_tr"])
                missile_speed = 8
                missiles_per_cycle = 3
                missile_spawn_delay = 500
            elif 137500 <= current_time < 145900:
                missile_type = "top"
                missile_speed = 7
                missiles_per_cycle = 3
                missile_spawn_delay = 700
            elif 145900 <= current_time < 155900:
                missile_type = "top"
                missile_speed = 10
                missiles_per_cycle = 4
                missile_spawn_delay = 500
                bg_scroll_speed = 4
            elif 155900 <= current_time < 165000:
                missile_type = random.choice(["top", "left", "right", "bottom", "diag_tl", "diag_tr"])
                missile_speed = 8
                missiles_per_cycle = 4
                missile_spawn_delay = 500
                bg_scroll_speed = 3
            elif 165000 <= current_time < 187700:
                missile_type = random.choice(["top", "left", "right", "bottom", "diag_tl", "diag_tr"])
                missile_speed = 8
                missiles_per_cycle = 4
                missile_spawn_delay = 500
                if current_time % 2000 < 100 and len(lasers) < 1:
                    direction = random.choice(["horizontal", "vertical"])
                    pos = player_y if direction == "horizontal" else player_x
                    lasers.append(Laser(direction, pos))
            elif 187700 <= current_time < 192000:
                missiles_per_cycle = 0
            elif 192000 <= current_time < 200000:
                missile_type = "top"
                missiles_per_cycle = 3
                missile_speed = 7
                missile_spawn_delay = 600
            elif 200000 <= current_time < 209500:
                missiles_per_cycle = 0
                time_since_phase_start = current_time - 200000
                if time_since_phase_start < 5000:
                    if (pygame.time.get_ticks() // 300) % 2 == 0:
                        font = pygame.font.SysFont("Arial", 40, bold=True)
                        for x in range(0, Width, 40):
                            ex_mark = font.render("!", True, (255, 0, 0))
                            window.blit(ex_mark, (x, 20))
                elif 5000 <= time_since_phase_start < 7000:
                    font = pygame.font.SysFont("Arial", 50, bold=True)
                    warning_text = font.render("⚠ WARNING: FINAL WAVE INCOMING ⚠", True, (255, 100, 100))
                    window.blit(warning_text, (
                        Width // 2 - warning_text.get_width() // 2,
                        Height // 2 - warning_text.get_height() // 2)
                    )
                elif 7000 <= time_since_phase_start < 9000:
                    font = pygame.font.SysFont("Arial", 60, bold=True)
                    luck_text = font.render("GOOD LUCK", True, (255, 255, 0))
                    window.blit(luck_text, (
                        Width // 2 - luck_text.get_width() // 2,
                        Height // 2 - luck_text.get_height() // 2)
                    )
            elif 209500 <= current_time < 216000:
                missile_type = "top"
                missiles_per_cycle = 5
                missile_speed = 12
                missile_spawn_delay = 400
                bg_scroll_speed = 6
                if current_time % 1500 < 100 and len(lasers) < 1:
                    direction = random.choice(["horizontal", "vertical"])
                    pos = random.randint(100, Height - 100) if direction == "horizontal" else random.randint(100, Width - 100)
                    lasers.append(Laser(direction, pos))
            elif 216000 <= current_time < 225900:
                missile_type = random.choice(["top", "left", "right", "bottom", "diag_tl", "diag_tr"])
                missile_speed = 10
                missiles_per_cycle = 4
                missile_spawn_delay = 400
                if current_time % 2000 < 100 and len(lasers) < 1:
                    direction = random.choice(["horizontal", "vertical"])
                    pos = random.randint(100, Height - 100) if direction == "horizontal" else random.randint(100, Width - 100)
                    lasers.append(Laser(direction, pos))
            elif 225900 <= current_time < 233000:
                missiles_per_cycle = 0
            elif 233000 < current_time:
                win = True 
                


            for spawn_time in laser_schedule:
                if current_time >= spawn_time and spawn_time not in spawned_lasers:
                    direction = random.choice(["horizontal", "vertical"])
                    pos = random.randint(100, Height - 100) if direction == "horizontal" else random.randint(100, Width - 100)
                    lasers.append(Laser(direction, pos))
                    spawned_lasers.add(spawn_time)

            # Percentage display
            percent = min(100, int((current_time / WIN_TIME) * 100))
            percent_text = font.render(f"{percent}%", True, (255, 255, 255))
            window.blit(percent_text, (10, 10))  


                
        if win:
            break
            
        pygame.display.update()

def draw_win_screen():
    window.fill((0, 0, 0))  
    font_big = pygame.font.SysFont("consolas", 60)
    font_small = pygame.font.SysFont("consolas", 30)

    win_text = font_big.render("MISSION COMPLETE!", True, (255, 255, 0))
    info_text = font_small.render("Hold down SPACE to play again", True, (200, 200, 200))

    window.blit(win_text, (Width // 2 - win_text.get_width() // 2, Height // 2 - 80))
    window.blit(info_text, (Width // 2 - info_text.get_width() // 2, Height // 2 + 10))

def draw_game_over_screen(percent):
    global current_time, WIN_TIME
    window.blit(background_img, (0, 0))

    font_big = pygame.font.SysFont("Arial", 60, bold=True)
    font_small = pygame.font.SysFont("Arial", 30)

    game_over_text = font_big.render("GAME OVER", True, (255, 50, 50))
    retry_text = font_small.render("Hold down SPACE to try again", True, (200, 200, 200))

    # Final survival percentage
    final_percent = percent
    percent_text = font_small.render(f"Progress : {final_percent}%", True, (255, 255, 255))

    window.blit(game_over_text, (
        Width // 2 - game_over_text.get_width() // 2,
        Height // 2 - game_over_text.get_height() // 2 - 40
    ))

    window.blit(percent_text, (
        Width // 2 - percent_text.get_width() // 2,
        Height // 2 + 10
    ))

    if (pygame.time.get_ticks() // 500) % 2 == 0:
        window.blit(retry_text, (
            Width // 2 - retry_text.get_width() // 2,
            Height // 2 + 60
        ))



# __main__
main_game_run = True
while main_game_run:
    if in_menu:
        main_menu()
        in_menu = False
    else:
        game_loop(*game_state_variables)
        
    while game_over or win:
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if game_over:
            draw_game_over_screen(game_state_variables[-2])  
            for event in pygame.event.get():
                if keys[pygame.K_SPACE]:
                    in_menu = True
                    game_state_variables[0] = Width // 2 - player_width // 2
                    game_state_variables[1] = Height - player_height - 20
                    game_state_variables[3] = 0
                    game_state_variables[4] = []
                    game_state_variables[6] = []
                    game_state_variables[7] = set()
                    game_state_variables[8] = 15
                    game_state_variables[9] = False
                    game_state_variables[10] = False
                    game_state_variables[11] = 0
                    game_state_variables[12] = False
                    game_state_variables[13] = "top"
                    game_state_variables[14] = 2000
                    game_state_variables[15] = 7
                    game_state_variables[18] = 0
                    game_state_variables[19] = -Height 
                    game_state_variables[20] = 2.5
                    game_state_variables[21] = False
                    game_state_variables[22] = 0
                    game_state_variables[23] = 6.5
                    game_state_variables[24] = 0
                    game_state_variables[25] = False
                    game_state_variables[26] = 0
                    game_state_variables[27] = 0
                    game_state_variables[28] = 0 
                    game_over = False
                    break

        elif win:
            draw_win_screen()
            for event in pygame.event.get():
                if keys[pygame.K_SPACE]:
                    in_menu = True
                    game_state_variables[0] = Width // 2 - player_width // 2
                    game_state_variables[1] = Height - player_height - 20
                    game_state_variables[3] = 0
                    game_state_variables[4] = []
                    game_state_variables[6] = []
                    game_state_variables[7] = set()
                    game_state_variables[8] = 15
                    game_state_variables[9] = False
                    game_state_variables[10] = False
                    game_state_variables[11] = 0
                    game_state_variables[12] = False
                    game_state_variables[13] = "top"
                    game_state_variables[14] = 2000
                    game_state_variables[15] = 7
                    game_state_variables[18] = 0
                    game_state_variables[19] = -Height 
                    game_state_variables[20] = 2.5
                    game_state_variables[21] = False
                    game_state_variables[22] = 0
                    game_state_variables[23] = 6.5
                    game_state_variables[24] = 0
                    game_state_variables[25] = False
                    game_state_variables[26] = 0
                    game_state_variables[27] = 0
                    game_state_variables[28] = 0 
                    game_over = False
                    break


        pygame.display.update()
        clock.tick(60)

#game_state_variables = [player_x, player_y, player_mask, missile_timer, missiles, missiles_per_cycle, lasers, spawned_lasers, lives, game_over, death_sound_played, death_time, music_played, missile_type, missile_spawn_delay, missile_speed, missile_img, background_img, bg_y1, bg_y2, bg_scroll_speed, exploding, explosion_timer, vel, last_hit_time, win, current_time, percent, pause_time_factor]

    while paused:
        pause_loop = True
        pause_clock = pygame.time.Clock()
        escape_hold_start = None
        while pause_loop:
            pause_clock.tick(60)

            pause_time = pygame.time.get_ticks() 

            #print(pause_time)

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    paused = False
                    pause_loop = False
                    pygame.mixer.unpause()
                    game_state_variables[-1] = pause_time - game_state_variables[-3]

                    break

            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                if escape_hold_start is None:
                    escape_hold_start = pygame.time.get_ticks()
                elif pygame.time.get_ticks() - escape_hold_start >= 1000:
                    pygame.quit()
                    sys.exit()
            else:
                escape_hold_start = None

            font_big = pygame.font.SysFont("consolas", 60)
            font_small = pygame.font.SysFont("consolas", 30)

            win_text = font_big.render("Game Paused", True, (255, 255, 0))
            info_text = font_small.render("Press SPACE to resume", True, (200, 200, 200))
            quit_text = font_small.render("Hold ESC to quit", True, (200, 200, 200))

            window.blit(win_text, (Width // 2 - win_text.get_width() // 2, Height // 2 - 80))
            window.blit(info_text, (Width // 2 - info_text.get_width() // 2, Height // 2 + 10))
            window.blit(quit_text, (Width // 2 - quit_text.get_width() // 2, Height // 2 + 50))

            pygame.display.update()

        paused = False
