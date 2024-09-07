from math import*
import pygame
from colorsys import hsv_to_rgb
from pygame import *
import random
import os
import time

class PerlinNoise:
    def __init__(self, permutation=None, seed=None, randomize=False):
        if permutation:
            self.PERMUTATION = permutation
        else:
            self.PERMUTATION = []
            for i in range(256):
                self.PERMUTATION.append((i))
            if seed is not None:
                random.seed(seed)
                random.shuffle(self.PERMUTATION)
            elif randomize:
                random.shuffle(self.PERMUTATION)

        self.p = [0] * 512
        for i in range(512):
            self.p[i] = self.PERMUTATION[i % 256]
    def noise(self, x, y, z):
        X = floor(x) & 255
        Y = floor(y) & 255
        Z = floor(z) & 255
        x -= floor(x)
        y -= floor(y)
        z -= floor(z)
        u = PerlinNoise.fade(x)
        v = PerlinNoise.fade(y)
        w = PerlinNoise.fade(z)
        A = self.p[X] + Y
        AA = self.p[A] + Z
        AB = self.p[A + 1] + Z
        B = self.p[X + 1] + Y
        BA = self.p[B] + Z
        BB = self.p[B + 1] + Z

        return PerlinNoise.lerp(w, PerlinNoise.lerp(v, PerlinNoise.lerp(u, PerlinNoise.grad(self.p[AA], x, y, z),
                                                                       PerlinNoise.grad(self.p[BA], x - 1, y, z)),
                                                    PerlinNoise.lerp(u, PerlinNoise.grad(self.p[AB], x, y - 1, z),
                                                                     PerlinNoise.grad(self.p[BB], x - 1, y - 1, z))),
                                PerlinNoise.lerp(v, PerlinNoise.lerp(u, PerlinNoise.grad(self.p[AA + 1], x, y, z - 1),
                                                                     PerlinNoise.grad(self.p[BA + 1], x - 1, y, z - 1)),
                                                 PerlinNoise.lerp(u, PerlinNoise.grad(self.p[AB + 1], x, y - 1, z - 1),
                                                                  PerlinNoise.grad(self.p[BB + 1], x - 1, y - 1, z - 1))))

    @staticmethod
    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def lerp(t, a, b):
        return a + t * (b - a)

    @staticmethod
    def grad(hash, x, y, z):
        h = hash & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else z)
        return ((u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v))

    def octave_noise(self, x, y, z, octaves, persistence):
        total = 0
        frequency = 1
        amplitude = 1
        max_value = 0  # Used for normalizing result to [0, 1]

        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency, z * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return total / max_value
class GameSprite(sprite.Sprite):
    def __init__(self, x, y, speedx, speedy, window_width, window_height,ima,width,height,offdirection=0,timesetdamage=1500):
        super().__init__()
        self.x = x
        self.y = y
        self.spedx = speedx
        self.speedx = self.spedx
        self.spedy = speedy
        self.speedy = self.spedy
        self.win_width = window_width
        self.win_height = window_height
        self.offdirection = offdirection
        self.image = transform.scale(image.load(ima),(width,height))
        self.damagetime = 0
        self.timesetdamage = timesetdamage
        self.width = width
        self.height = height
    def border(self):
        if self.x<0:
            self.x=0
            border = True
        if self.x>win_width:
            self.x = win_width
            border = True
        if self.y<0:
            self.y = 0
            border = True
        if self.y > win_height:
            self.y = win_height
            border = True
    def checkborder(self):
        if self.x<0:
            return True
        if self.x>win_width:
            return True
        if self.y<0:
            return True
        if self.y > win_height:
            return True
class Player(GameSprite):
    
    def move(self, dx, dy, noise, mapwidth, mapheight):
        new_x = self.x + dx * self.speedx*self.win_width/win_width
        new_y = self.y + dy * self.speedy *self.win_height/win_height

        # Scale the player's position to the size of the noise map
        noise_map_x = int(new_x * mapwidth / self.win_width)
        noise_map_y = int(new_y * mapheight / self.win_height)

        # Clamp the player's position to the bounds of the noise map
        noise_map_x = max(0, min(noise_map_x, mapwidth - 1))
        noise_map_y = max(0, min(noise_map_y, mapheight - 1))

        # Check the height at the new position
        height = (noise[noise_map_x][noise_map_y] + 1) * 127.5
        collisionwithenemy = False
        for enemy in enemies:
            if self.check_collision(enemy):
                collisionwithenemy = True
        if height >= 127-16 and not collisionwithenemy:  # Only move if the height is 127 or higher
            self.x = new_x
            self.y = new_y
        elif height >= 127-32:
            dx = new_x - self.x
            dy = new_y - self.y
            self.x += dx*height/127
            self.y += dy*height/127
        else:
            dx = new_x - self.x
            dy = new_y - self.y
            self.x += dx*0.1
            self.y += dy*0.1
                # Check for collisions with enemies


    def draw(self, surface):
        screen.blit(self.image, (self.x-8, self.y-8))

    def resize(self, new_width, new_height):
        self.x = self.x * new_width / self.win_width
        self.y = self.y * new_height / self.win_height
        self.window_width = new_width
        self.window_height = new_height
        self.speedx = self.spedx * new_width / self.win_width
        self.speedy = self.spedy * new_height / self.win_height

    def check_collision(self, treasure):
        player_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        treasure_rect = pygame.Rect(treasure.x - treasure.width//2, treasure.y - treasure.height//2, treasure.width, treasure.height)
        return player_rect.colliderect(treasure_rect)

class Enemy(GameSprite):
    def move(self, dx, dy, noise, mapwidth, mapheight):
        new_x = self.x + dx * self.speedx*self.win_width/win_width
        new_y = self.y + dy * self.speedy *self.win_height/win_height

        # Scale the player's position to the size of the noise map
        noise_map_x = int(new_x * mapwidth / self.win_width)
        noise_map_y = int(new_y * mapheight / self.win_height)

        # Clamp the player's position to the bounds of the noise map
        noise_map_x = max(0, min(noise_map_x, mapwidth - 1))
        noise_map_y = max(0, min(noise_map_y, mapheight - 1))

        # Check the height at the new position
        height = (noise[noise_map_x][noise_map_y] + 1) * 127.5
        if height >= 127-16:  # Only move if the height is 127 or higher
            self.x = new_x
            self.y = new_y
        elif height >= 127-32:
            dx = new_x - self.x
            dy = new_y - self.y
            self.x += dx*height/255
            self.y += dy*height/255
        else:
            dx = new_x - self.x
            dy = new_y - self.y
            self.x += dx*0.1
            self.y += dy*0.1

    def draw(self, surface):
        screen.blit(self.image, (self.x-8, self.y-8))

    def resize(self, new_width, new_height):
        self.x = self.x * new_width / self.win_width
        self.y = self.y * new_height / self.win_height
        self.window_width = new_width
        self.window_height = new_height
        self.speedx = self.spedx * new_width / self.win_width
        self.speedy = self.spedy * new_height / self.win_height

    def check_collision(self, player):
        monster_rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        player_rect = pygame.Rect(player.x - player.width//2, player.y - player.height//2, player.width, player.height)
        return monster_rect.colliderect(player_rect)

class Treasure:
    def __init__(self, x, y, visible_slices,ima,width,height):
        self.x = x
        self.y = y
        self.visible_slices = visible_slices
        self.image = transform.scale(image.load(ima),(width,height))
        self.width = width
        self.height = height

    def draw(self, surface, current_slice):
        if current_slice in self.visible_slices:
            screen.blit(self.image, (self.x-self.width//2, self.y-self.height//2))

def find_land_position(noise, mapwidth, mapheight, win_width, win_height):
    while True:
        x = random.randint(0, mapwidth - 1)
        y = random.randint(0, mapheight - 1)
        height = (noise[x][y] + 1) * 127.5
        if height >= 127:  # Ensure it's on land
            return x * win_width / mapwidth, y * win_height / mapheight

# Example usage with Pygame
#Todo
if __name__ == "__main__":
    setblocksx = 256
    setblocksy = 256
    setblocksz = 16
    win_width, win_height = 1024,1024
    mapwidth, mapheight = (256), (256)
    layers =16# Ensure this is greater than or equal to the number of slices you want to sample
    scalex = 0.032 / (mapwidth / setblocksx)
    scaley = 0.032 / (mapheight / setblocksy)
    scalez = 0.032 / (layers / setblocksz)
    octaves = 4
    persistence = 0.5
    lacunarity = 2

    # Example permutations and seed
    permutation = None  # Replace with a list of 256 integers if needed
    seed = random.randint(1,1000000000)  # Replace with an integer if needed
    print("seed", seed)
    # seed = None
    randomize = False  # Set to True for random permutation

    perlin_noise = PerlinNoise(permutation=permutation, seed=seed, randomize=randomize)
    noise = [[[0] * mapheight for _ in range(mapwidth)] for _ in range(layers)]  # Initialize with the correct number of layers
    # print("permutation", perlin_noise.PERMUTATION)
    fe = 0
    starttimer = time.time()
    for z in range(layers):
        for x in range(mapwidth):
            for y in range(mapheight):
                noise[z][x][y] = perlin_noise.octave_noise(x * scalex, y * scaley, z * scalez, octaves, persistence)
            fe += 1
            if x % 128 == 0:
                print(fe/(layers*mapwidth)*100,"%")
    print("Time taken:", time.time() - starttimer)

    pygame.init()
    screen = pygame.display.set_mode((win_width, win_height), RESIZABLE)
    
    # Use os.path.join for cross-platform compatibility
    icon = pygame.image.load(os.path.join('assets', 'Kingsion.png'))
    icon = pygame.transform.scale(icon, (128, 128))
    biplayerima = os.path.join('assets', 'Player.png')
    treasureimage = (os.path.join('assets', 'goldbar.png'))
    enemy_image = os.path.join('assets', 'SaleuoA.png')
    enemy_2image = os.path.join('assets', 'SaleuoV.png')
    enemy_3image = os.path.join('assets', 'SaleuoX.png')
    
    pygame.display.set_icon(icon)
    pygame.display.set_caption("Portrichy Newin")

    noise_surface = pygame.Surface((mapwidth, mapheight))

    show_noise = 3  # Variable to track the current mode
    snow_noise = 0
    current_slice = 0  # Start with the first slice
    player_x, player_y = find_land_position(noise[current_slice], mapwidth, mapheight, win_width, win_height)
    player = Player(player_x, player_y, 3, 3, win_width, win_height,biplayerima,16,16)  # Initialize player on land
    # Create a list of enemies
    num_enemies = 60  # Number of enemies you want to add
    enemies = []
    separation_distance = 25  # Minimum distance between enemies
    def caculate_distance(x1, y1, x2, y2):
        distance = sqrt((x2-x1) ** 2 +(y2-y1) ** 2)
        return distance
    for _ in range(num_enemies):
        while True:
            enemy_x, enemy_y = find_land_position(noise[current_slice], mapwidth, mapheight, win_width, win_height)
            if random.randint(1, 16) == 1:
                new_enemy = Enemy(enemy_x, enemy_y, 4, 4, win_width, win_height, enemy_3image, 16, 16,75)
            elif random.randint(1, 8) == 1:
                new_enemy = Enemy(enemy_x, enemy_y, 3, 3, win_width, win_height, enemy_2image, 16, 16,150)
            else:
                new_enemy = Enemy(enemy_x, enemy_y, 2, 2, win_width, win_height, enemy_image, 16, 16,300)
            
            # Check if the new enemy is too close to existing enemies
            too_close = False
            for enemy in enemies:
                if caculate_distance(new_enemy.x, new_enemy.y, enemy.x, enemy.y) < 1 or caculate_distance(new_enemy.x, new_enemy.y, player.x, player.y) < 120:
                    too_close = True
                    break
            
            if not too_close:
                enemies.append(new_enemy)
                break
    # Spawn treasure on specific slices
    num_slices = 1  # Number of slices where the treasure will be visible
    if num_slices > layers:
        num_slices = layers // 2
        if num_slices < 1:
            num_slices = 1
    treasure_slices = random.sample(range(layers), k=num_slices)  # Make the treasure visible in `num_slices` random slices
    print("Treasure slices:", treasure_slices)
    treasure_x, treasure_y = None, None
    while True:
        tx = random.randint(0, mapwidth - 1)
        ty = random.randint(0, mapheight - 1)
        if all((noise[slice_index][tx][ty] + 1) * 127.5 >= 127 for slice_index in treasure_slices):  # Ensure it's on land in all slices
            treasure_x, treasure_y = tx, ty
            break
    treasure = Treasure(treasure_x * win_width / mapwidth, treasure_y * win_height / mapheight, treasure_slices,treasureimage,16,16)

    def hsb_to_rgbo(h, s, b):
        r, g, b = hsv_to_rgb(h, s, b)
        return int(r * 255), int(g * 255), int(b * 255)

    def generate_1d_noise(length, scale, octaves, persistence):
            perlin_noise = PerlinNoise()
            noise = [perlin_noise.octave_noise(x * scale, 0, 0, octaves, persistence) for x in range(length)]
            return noise

    ice_noise = generate_1d_noise(mapwidth, 0.12, 8, 0.5)
    def caculate_direction(x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        angle = atan2(dy, dx)  # Angle in radians
        angle_degrees = degrees(angle)  # Convert to degrees
        return angle_degrees
    def update_noise_surface():
        for x in range(mapwidth):
            for y in range(mapheight):
                value = int((noise[current_slice][x][y] + 1) * 127.5)  # Normalize to [0, 255]
                if show_noise == 0:
                    h = 1 - (value % 255 / 255)  # Hue
                    s = 1.0
                    b = 1
                    color = hsb_to_rgbo(h, s, b)
                    red = color[0]
                    green = color[1]
                    blue = color[2]
                    if red > 255:
                        red = 255
                    if green > 255:
                        green = 255
                    if blue > 255:
                        blue = 255
                    color = (red, green, blue)
                elif show_noise == 1:
                    value = value / 255
                    if value < 0.25:
                        color = (0, 0, 64)  # Very deep water
                    elif value < 0.35:
                        color = (0, 0, 128)  # Deep water
                    elif value < 0.45:
                        color = (0, 0, 192)  # Medium water
                    elif value < 0.5:
                        color = (0, 0, 255)  # Shallow water
                    elif value < 0.55:
                        color = (210, 180, 140)  # Beach
                    elif value < 0.65:
                        color = (34, 139, 34)  # Grass
                    elif value < 0.69:
                        color = (25, 105, 25)  # Forest
                    elif value < 0.73:
                        color = (17, 74, 17)  # Dark forest
                    elif value < 0.75:
                        color = (139, 69, 19)  # Hills
                    elif value < 0.81:
                        color = (112, 128, 144)  # Hills
                    else:
                        color = (176, 224, 230)  # Mountains
                elif show_noise == 2:
                    if value <51:
                        color = (value,0,0)
                    elif value<102:
                        color = (value,value/2,0)
                    elif value<127:
                        color = (value,value*3/4,0)
                    elif value<153:
                        color = (value,value,0)
                    elif value<204:
                        color = (0,value,0)
                    else:
                        color = (0,value,value)
                else:
                    colorratered = 134/255
                    colorrategreen = 239/255
                    colorrateblue = 134/255
                    if value >127:
                        if value > 255:
                            value = 255
                        color = ((int(value*colorratered),int(value*colorrategreen),int(value*colorrateblue)))
                    else:
                        colorratered = 100/255
                        colorrategreen = 100/255
                        colorrateblue = 255/255
                        color = ((int(value*colorratered),int(value*colorrategreen),int(value*colorrateblue)))
                if snow_noise == 1:
                    ice_threshold_top = mapheight * 0.1 + ice_noise[x] * 10  # Adjust the threshold with noise
                    ice_threshold_bottom = mapheight * 0.9 - ice_noise[x] * 10  # Adjust the threshold with noise
                    if y < ice_threshold_top or y > ice_threshold_bottom:  # Ice regions with curved borders
                        if value > 127:
                            value+40
                            if value > 255:
                                value = 255
                            color = (value, value, value)  # White color for snow
                        else:
                            value += 30
                            color = (int(value * 220 / 255), int(value * 228 / 255), int(value * 235 / 255))  # Light blue color for ice
                noise_surface.set_at((x, y), color)
    # def save_slice_image(slice_index):
    #     global current_slice
    #     current_slice = slice_index
    #     update_noise_surface()
    #     if not os.path.exists('slices'):
    #         os.makedirs('slices')
    #     pygame.image.save(noise_surface, os.path.join('slices', f"slice_{slice_index}.png"))
    # # Save images for all slices
    # for slice_index in range(layers):
    #     save_slice_image(slice_index)

    # Start the Pygame window after generating images
    update_noise_surface()
    running = True
    scalexs = 0
    scaleys = 0
    pygame.font.init()
    font1 = pygame.font.SysFont("San-Serif",80)
    font2 = pygame.font.SysFont("San-Serif",36)
    screenupt = False
    startupt = True
    clock = pygame.time.Clock()
    slicetest = True
    timechia =0 
    win = False
    botmode = False
    gold = 0
    waitforgold = 150
    timestart = time.time()
    maxhp = 100
    hp = maxhp
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # show_noise +=1
                    # show_noise = show_noise%4
                    # update_noise_surface()
                    screenupt = not screenupt
                    pausete = font1.render("Game Paused",True,(255,255,255))
                    texrect = pausete.get_rect(center=(win_width // 2, win_height // 2))
                    screen.blit(pausete,texrect)
                if event.key == pygame.K_b:
                    botmode = not botmode
                if event.key == pygame.K_c:
                    snow_noise +=1
                    snow_noise = snow_noise%2
                    update_noise_surface()
                if event.key == pygame.K_f:
                    slicetest = not slicetest
                if event.key == pygame.K_UP:
                    scaleys += 100
                if event.key == pygame.K_DOWN:
                    scaleys -= 100
                if event.key == pygame.K_LEFT:
                    scalexs -= 100
                if event.key == pygame.K_RIGHT:
                    scalexs += 100
            elif event.type == pygame.VIDEORESIZE:
                win_width, win_height = event.w, event.h
                screen = pygame.display.set_mode((win_width, win_height), RESIZABLE)
                player.resize(win_width, win_height)
        if screenupt or startupt:
            keys = pygame.key.get_pressed()
            mouseclick = pygame.mouse.get_pressed()
            if keys[pygame.K_q]:
                current_slice = (current_slice - 1)
                if current_slice < 0:
                    current_slice = 0
                update_noise_surface()
            if keys[pygame.K_e]:
                current_slice = (current_slice + 1)
                if current_slice >= layers:
                    current_slice = layers - 1
                update_noise_surface()
            if not botmode:
                if keys[pygame.K_w]:
                    player.move(0, -1, noise[current_slice], mapwidth, mapheight)
                if keys[pygame.K_s]:
                    player.move(0, 1, noise[current_slice], mapwidth, mapheight)
                if keys[pygame.K_a]:
                    player.move(-1, 0, noise[current_slice], mapwidth, mapheight)
                if keys[pygame.K_d]:
                    player.move(1, 0, noise[current_slice], mapwidth, mapheight)
                if mouseclick[0]:
                    mousepos = pygame.mouse.get_pos()
                    player_x, player_y = player.x, player.y
                    anlia=caculate_direction(player_x,player_y,mousepos[0],mousepos[1])
                    trianlia = caculate_direction(player_x,player_y,treasure_x,treasure_y)
                    dx = cos(radians(anlia))
                    dy = sin(radians(anlia))
                    player.move(dx, dy, noise[current_slice], mapwidth, mapheight)
            else:
                player_x, player_y = player.x, player.y
                nearest_enemy = None
                min_distance = float(100)
                
                # Find the nearest enemy
                for enemy in enemies:
                    distance = caculate_distance(player_x, player_y, enemy.x, enemy.y)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_enemy = enemy
                percentia = 0.5
                if nearest_enemy:
                    # Calculate the direction away from the nearest enemy
                    enemy_x, enemy_y = nearest_enemy.x, nearest_enemy.y
                    direction = caculate_direction(player_x, player_y, enemy_x, enemy_y)
                    if timechia>0:
                        timechia -= 1
                    if random.randint(1, 10) == 1 and timechia == 0 or player.checkborder():
                        player.offdirection = (random.randint(0, 1)-0.5)*2*180
                        timechia = 150
                    dx = cos(radians(direction+player.offdirection))
                    dy = sin(radians(direction+player.offdirection))
                    player.move(dx*(1-percentia), dy*(1-percentia), noise[current_slice], mapwidth, mapheight)
                # Test moving in DIRECTTEST directions and check which one is nearest to the treasure
                best_direction = None
                min_treasure_distance = float('inf')
                DIRECTTEST = 32
                for i in range(DIRECTTEST):
                    dx = sin(radians(i * 360 / DIRECTTEST))
                    dy = cos(radians(i * 360 / DIRECTTEST))
                    new_x = player.x + dx * 10
                    new_y = player.y + dy * 10
                    treasure_distance = caculate_distance(new_x, new_y, treasure.x, treasure.y)
                    if treasure_distance < min_treasure_distance:
                        min_treasure_distance = treasure_distance
                        best_direction = (dx, dy)
                
                if best_direction:
                    player.move(best_direction[0]*percentia, best_direction[1]*percentia, noise[current_slice], mapwidth, mapheight)

            scaled_surface = pygame.transform.scale(noise_surface, (win_width + scalexs, win_height + scaleys))
            screen.fill((0, 0, 0))
            screen.blit(scaled_surface, (-scalexs / 2, -scaleys / 2))
            if slicetest:
                slicetest = font2.render("slices:"+str(current_slice)+"|gold:"+str(gold)+"|Hp:"+str(hp),True,(255,255,255))
                screen.blit(slicetest,(0,0))
            # Update and draw each enemy
            for enemy in enemies:
                # Apply separation force
                if timechia > 0:
                    timechia -= 1
                if random.randint(1, 10) == 1 and timechia == 0:
                    enemy.offdirection = random.randint(-1, 1)*60
                    timechia = 150
                canmove = True
                nearest_enemy = None
                min_distance = float('inf')
                for other_enemy in enemies:
                    if other_enemy != enemy:
                        distance = caculate_distance(enemy.x, enemy.y, other_enemy.x, other_enemy.y)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_enemy = other_enemy

                # Define the minimum separation distance
                separation_distance = 25  # Adjust this value as needed

                if nearest_enemy and min_distance < separation_distance:
                    repel_direction = caculate_direction(nearest_enemy.x, nearest_enemy.y, enemy.x, enemy.y)
                    repel_dx = cos(radians(repel_direction))
                    repel_dy = sin(radians(repel_direction))
                    enemy.move(repel_dx, repel_dy, noise[current_slice], mapwidth, mapheight)
                    canmove = False

                medist = caculate_distance(enemy.x, enemy.y, player.x, player.y)
                if medist < 700:
                    enemy.draw(screen)
                else:
                    pygame.draw.rect(screen, (255, 0, 0), (enemy.x - 8, enemy.y - 8, 16, 16))
                tedist = caculate_distance(enemy.x, enemy.y, treasure.x, treasure.y)
                if tedist<35:
                    repel_direction = caculate_direction(treasure_x, treasure_y, enemy.x, enemy.y)
                    repel_dx = cos(radians(repel_direction))
                    repel_dy = sin(radians(repel_direction))
                    enemy.move(-repel_dx, -repel_dy, noise[current_slice], mapwidth, mapheight)
                # Move the enemy towards the player
                if canmove:
                    direction = caculate_direction(enemy.x, enemy.y, player.x, player.y)
                    dx = cos(radians(direction + enemy.offdirection))
                    dy = sin(radians(direction + enemy.offdirection))
                    enemy.move(dx, dy, noise[current_slice], mapwidth, mapheight)
                
                # Check for collision with the player
                if enemy.damagetime > 0:
                    enemy.damagetime -= 1
                if enemy.check_collision(player):
                    # text_score = font1.render("Game Over", True, (255, 0, 0))
                    # text_rect = text_score.get_rect(center=(win_width // 2, win_height // 2))
                    # screen.blit(text_score, text_rect)
                    # pygame.display.flip()
                    # time.sleep(2)
                    # running = False
                    player.move(dx,dy, noise[current_slice], mapwidth, mapheight)
                    if enemy.damagetime == 0:
                        hp -= 1
                        enemy.damagetime = 150
                    # pass
                if hp <= 0:
                    text_score = font1.render("Game Over", True, (255, 0, 0))
                    text_rect = text_score.get_rect(center=(win_width // 2, win_height // 2))
                    screen.blit(text_score, text_rect)
                    pygame.display.flip()
                    win = True
                enemy.border()
            lidist = caculate_distance(player.x, player.y, treasure.x, treasure.y)
            player.draw(screen)
            if lidist < 500:
                treasure.draw(screen, current_slice)
            else:
                pygame.draw.circle(screen,(127,127,127),(int(treasure.x),int(treasure.y)),8)
            player.border()
            # Check for collision with treasure
            if waitforgold > 0:
                waitforgold -= 1
            if current_slice in treasure_slices and player.check_collision(treasure) and waitforgold == 0:
                # text_score = font1.render("You win",True,(255,255,255))
                # text_rect = text_score.get_rect(center=(win_width // 2, win_height // 2))
                # screen.blit(text_score,text_rect)
                # screenupt = False
                # win = True
                gold+=1
                hp+=10
                waitforgold = 150
            if hp > maxhp:
                hp = maxhp
            if gold >=100:
                currentime = time.time()
                text_score = font1.render("You win|Time:"+str(currentime-timestart),True,(255,255,255))
                text_rect = text_score.get_rect(center=(win_width // 2, win_height // 2))
                screen.blit(text_score,text_rect)
                screenupt = False
                win = True
            clock.tick(150)
            startupt = False
        else:
            if not win:
                pausete = font1.render("Game Paused",True,(255,255,255))
                texrect = pausete.get_rect(center=(win_width // 2, win_height // 2))
                screen.blit(pausete,texrect)
        pygame.display.flip()
        # Exit the game loop if the game is over
        if win:
            time.sleep(2)  # Optional: Add a delay to show the game over message
            running = False
    pygame.quit()
#make app: pyinstaller --onefile --windowed --icon=app_icon.ico --add-data "assets;assets" Seleportria.py | time:78.39497184753418
#make app: pyinstaller --onefile --windowed --icon=app_icon.ico --add-data "assets;assets" shoter_game.py
#690 lines of code