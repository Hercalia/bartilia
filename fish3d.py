import pygame
from pygame import image, transform, RESIZABLE
import random
import math
import os
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 1300
screen_height = screen_width * 600 // 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("3D Boid Simulator")
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)

def project_3d_to_2d(x, y, z, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z):
    # Translate the point based on the camera position
    x -= camera_x
    y -= camera_y
    z -= camera_z

    # Rotate around the Z axis
    cos_z = math.cos(camera_angle_z)
    sin_z = math.sin(camera_angle_z)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z

    # Rotate around the Y axis
    cos_y = math.cos(camera_angle_y)
    sin_y = math.sin(camera_angle_y)
    x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y

    # Rotate around the X axis
    cos_x = math.cos(camera_angle_x)
    sin_x = math.sin(camera_angle_x)
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

    # Avoid division by zero
    epsilon = 0.000001
    factor = fov / (viewer_distance + z + epsilon)
    x = x * factor + screen_width / 2
    y = -y * factor + screen_height / 2
    return x, y, z

def clip_line_to_near_plane(start, end, near_plane_z=0):
    sx, sy, sz = start
    ex, ey, ez = end

    if sz >= near_plane_z and ez >= near_plane_z:
        return start, end
    if sz < near_plane_z and ez < near_plane_z:
        return None

    t = (near_plane_z - sz) / (ez - sz)
    ix = sx + t * (ex - sx)
    iy = sy + t * (ey - sy)
    iz = near_plane_z

    if sz < near_plane_z:
        return (ix, iy, iz), end
    else:
        return start, (ix, iy, iz)

def draw_3d_box(screen, x,y,z,screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y,camera_angle_z, box_width, box_height, box_depth,color=LIGHT_BLUE):
    # Define the 3D coordinates of the box corners
    corners = [
        (x, y, z),
        (box_width, y, z),
        (box_width, box_height, z),
        (x, box_height, z),
        (x, y, box_depth),
        (box_width, y, box_depth),
        (box_width, box_height, box_depth),
        (x, box_height, box_depth)
    ]
    # for i in range(1, box_width-x+50, 5):
    #     t = i+x
    #     corners.append((t, y, z))
    #     corners.append((t, y, box_depth))
    # Project the 3D coordinates to 2D screen coordinates
    projected_corners = [project_3d_to_2d(x, y, z, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y,camera_angle_z) for x, y, z in corners]

    # Draw lines between the projected 2D points to form the edges of the 3D box
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Front face
        (4, 5), (5, 6), (6, 7), (7, 4),  # Back face
        (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
    ]
        # Add edges to fill the bottom face
    # for i in range(1, len(corners)//2-len(edges)):
    #     edges.append((8 + 2 * (i - 1), 9 + 2 * (i - 1)))
    for edge in edges:
        start, end = edge
        clipped_line = clip_line_to_near_plane(projected_corners[start], projected_corners[end])
        if clipped_line:
            (sx, sy, sz), (ex, ey, ez) = clipped_line
            if sz > 0 and ez > 0:  # Ensure both points are in front of the camera
                pygame.draw.line(screen, color, (sx, sy), (ex, ey), 3)
def draw_cube(screen, x, y, z, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z, box_width, box_height, box_depth, color=LIGHT_BLUE):
    corners = [
        (x, y, z),
        (x + box_width, y, z),
        (x + box_width, y + box_height, z),
        (x, y + box_height, z),
        (x, y, z + box_depth),
        (x + box_width, y, z + box_depth),
        (x + box_width, y + box_height, z + box_depth),
        (x, y + box_height, z + box_depth)
    ]

    projected_corners = [project_3d_to_2d(x, y, z, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z) for x, y, z in corners]

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Front face
        (4, 5), (5, 6), (6, 7), (7, 4),  # Back face
        (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
    ]

    for edge in edges:
        start, end = edge
        clipped_line = clip_line_to_near_plane(projected_corners[start], projected_corners[end])
        if clipped_line:
            (sx, sy, sz), (ex, ey, ez) = clipped_line
            if sz > 0 and ez > 0:  # Ensure both points are in front of the camera
                pygame.draw.line(screen, color, (sx, sy), (ex, ey), 3)
    


class Boid:
    def __init__(self, screen_width, screen_height, screen_depth, separation_resolve=0.01, alignment_resolve=0.01, cohesion_resolve=0.01, top_speed=5, fishima=None, x=None, y=None, z=None, fish_type='fish', width=36, height=16,margin=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen_depth = screen_depth
        self.position = [x, y, z]
        self.velocity = [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]
        self.max_speed = top_speed
        self.min_speed =top_speed
        self.speed = random.uniform(self.min_speed, self.max_speed)
        self.separation_resolve = separation_resolve
        self.alignment_resolve = alignment_resolve
        self.cohesion_resolve = cohesion_resolve
        self.image = transform.scale(image.load(fishima), (width, height))
        self.imageflip = transform.flip(self.image, True, False)
        self.width = width
        self.height = height
        self.collisiontomouse = False
        self.fish_type = fish_type
        self.prev_x, self.prev_y, self.prev_z = 0, 0, 0
        self.margin = margin
    def distance(self, other):
        if isinstance(other, Boid):
            return math.sqrt((self.position[0] - other.position[0]) ** 2 + (self.position[1] - other.position[1]) ** 2 + (self.position[2] - other.position[2]) ** 2)
        elif isinstance(other, tuple) and len(other) == 3:
            return math.sqrt((self.position[0] - other[0]) ** 2 + (self.position[1] - other[1]) ** 2 + (self.position[2] - other[2]) ** 2)

    def update_position(self,delta):
        if self.collisiontomouse:
            self.collisiontomouse = False
        self.position[0] += self.velocity[0] * self.speed*delta
        self.position[1] += self.velocity[1] * self.speed*delta
        self.position[2] += self.velocity[2] * self.speed*delta
        self.check_bounds()
        self.limit_speed()

    def check_bounds(self):
        margin = self.margin
        turn_factor = 1

        if self.position[0] < margin:
            self.velocity[0] += turn_factor
        elif self.position[0] > self.screen_width - margin:
            self.velocity[0] -= turn_factor

        if self.position[1] < margin:
            self.velocity[1] += turn_factor
        elif self.position[1] > self.screen_height - margin:
            self.velocity[1] -= turn_factor

        if self.position[2] < margin:
            self.velocity[2] += turn_factor
        elif self.position[2] > self.screen_depth - margin:
            self.velocity[2] -= turn_factor

    # def move_random_direction(self):
    #     self.velocity = [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]

    def draw(self, screen, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z):
        x, y, z = project_3d_to_2d(self.position[0], self.position[1], self.position[2], self.screen_width, self.screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z)
        if 0 <= x <= self.screen_width and 0 <= y <= self.screen_height and z > 0:
            new_image = self.image
            if x < self.prev_x:
                new_image = self.imageflip
            # new_image = transform.rotate(new_image, math.degrees(math.atan2(x-self.prev_x, -x-self.prev_y)) + 180)
            dist = math.sqrt((self.position[0] - camera_x) ** 2 + (self.position[1] - camera_y) ** 2 + (self.position[2] - camera_z) ** 2)
            scale_factor = max(0.001, min(1000.0, 500 / dist))  # Adjust the scale factor as needed
            new_width = int(self.width * scale_factor)
            new_height = int(self.height * scale_factor)
            new_image = transform.scale(new_image, (new_width, new_height))
            # Calculate the end point of the direction line
            direction_length = 10  # Length of the direction line
            end_x = self.position[0] + self.velocity[0] * direction_length
            end_y = self.position[1] + self.velocity[1] * direction_length
            end_z = self.position[2] + self.velocity[2] * direction_length
            end_x, end_y, _ = project_3d_to_2d(end_x, end_y, end_z, self.screen_width, self.screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z)

            # Draw the direction line
            pygame.draw.line(screen, LIGHT_BLUE, (x, y), (end_x, end_y), 2)
            pygame.draw.circle(screen, WHITE, (int(end_x), int(end_y)),1000/math.sqrt((self.position[0] - camera_x) ** 2 + (self.position[1] - camera_y) ** 2 + (self.position[2] - camera_z) ** 2))
            screen.blit(new_image, (x-self.width//2, y-self.height//2))
        self.prev_x, self.prev_y, self.prev_z = x, y, z

    def apply_separation(self, boids, separation_distance):
        move_x, move_y, move_z = 0, 0, 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < separation_distance:
                move_x += self.position[0] - other_boid.position[0]
                move_y += self.position[1] - other_boid.position[1]
                move_z += self.position[2] - other_boid.position[2]
        self.velocity[0] += move_x * self.separation_resolve
        self.velocity[1] += move_y * self.separation_resolve
        self.velocity[2] += move_z * self.separation_resolve

    def apply_alignment(self, boids, alignment_distance):
        avg_velocity_x, avg_velocity_y, avg_velocity_z = 0, 0, 0
        count = 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < alignment_distance and other_boid.fish_type == self.fish_type:
                avg_velocity_x += other_boid.velocity[0]
                avg_velocity_y += other_boid.velocity[1]
                avg_velocity_z += other_boid.velocity[2]
                count += 1
        if count > 0:
            avg_velocity_x /= count
            avg_velocity_y /= count
            avg_velocity_z /= count
            self.velocity[0] += (avg_velocity_x - self.velocity[0]) * self.alignment_resolve
            self.velocity[1] += (avg_velocity_y - self.velocity[1]) * self.alignment_resolve
            self.velocity[2] += (avg_velocity_z - self.velocity[2]) * self.alignment_resolve

    def apply_cohesion(self, boids, cohesion_distance):
        avg_position_x, avg_position_y, avg_position_z = 0, 0, 0
        count = 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < cohesion_distance and other_boid.fish_type == self.fish_type:
                avg_position_x += other_boid.position[0]
                avg_position_y += other_boid.position[1]
                avg_position_z += other_boid.position[2]
                count += 1
        if count > 0:
            avg_position_x /= count
            avg_position_y /= count
            avg_position_z /= count
            self.velocity[0] += (avg_position_x - self.position[0]) * self.cohesion_resolve
            self.velocity[1] += (avg_position_y - self.position[1]) * self.cohesion_resolve
            self.velocity[2] += (avg_position_z - self.position[2]) * self.cohesion_resolve

    def apply_mouse_repulsion(self, mouse_pos, repulsion_distance, repulsion_strength):
        distance_to_mouse = math.sqrt((self.position[0] - mouse_pos[0]) ** 2 + (self.position[1] - mouse_pos[1]) ** 2 + (self.position[2] - mouse_pos[2]) ** 2)
        if distance_to_mouse < repulsion_distance:
            anglex, angley = self.calculate_angle(mouse_pos)
            move_x = math.cos((anglex))*10000/(distance_to_mouse+1)
            move_y = math.sin((anglex))*10000/(distance_to_mouse+1)
            move_z = math.sin((angley))*10000/(distance_to_mouse+1)
            self.velocity[0] += move_x * repulsion_strength
            self.velocity[1] += move_y * repulsion_strength
            self.velocity[2] += move_z * repulsion_strength

    def limit_speed(self):
        speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2 + self.velocity[2] ** 2)
        if speed > self.max_speed:
            self.velocity[0] = (self.velocity[0] / speed) * self.max_speed
            self.velocity[1] = (self.velocity[1] / speed) * self.max_speed
            self.velocity[2] = (self.velocity[2] / speed) * self.max_speed
    def check_collision_with_mouse(self, mouse_pos, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z):
        x, y, _ = project_3d_to_2d(self.position[0], self.position[1], self.position[2], screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z)
        mouse_x, mouse_y = mouse_pos
        # Use the fish's hitbox for collision detection
        boid_rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        # Create a small hitbox for the mouse
        mouse_hitbox_size = 50  # Size of the mouse hitbox
        mouse_rect = pygame.Rect(mouse_x - mouse_hitbox_size // 2, mouse_y - mouse_hitbox_size // 2, mouse_hitbox_size, mouse_hitbox_size)
        return boid_rect.colliderect(mouse_rect)
    def calculate_angle(self,target_position):
        dx = target_position[0] - self.position[0]
        dy = target_position[1] - self.position[1]
        dz = target_position[2] - self.position[2]
        anglex = math.degrees(math.atan2(dy, dx)) + 180
        angley = math.degrees(math.atan2(dz, dx)) + 180
        return anglex, angley
    def push(self, camera_x, camera_y, camera_z):
        anglex, angley = self.calculate_angle((camera_x, camera_y, camera_z))
        self.velocity[0] += math.cos(math.radians(anglex))
        self.velocity[1] += math.sin(math.radians(anglex))
        self.velocity[2] += math.sin(math.radians(angley))
    
        
class CollisionMouse:
    def __init__(self, boids, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y,camera_angle_z,replusion_distance, repulsion_strength,rangeattack):
        self.boids = boids
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fov = fov
        self.viewer_distance = viewer_distance
        self.camera_x = camera_x
        self.camera_y = camera_y
        self.camera_z = camera_z
        self.camera_angle_x = camera_angle_x
        self.camera_angle_y = camera_angle_y
        self.camera_angle_z = camera_angle_z
        self.repulsion_distance = replusion_distance
        self.repulsion_strength = repulsion_strength
        self.rangeattack = rangeattack

    def check_collisions(self, mouse_pos):
            for boid in self.boids:
                if boid.check_collision_with_mouse(mouse_pos, self.screen_width, self.screen_height, self.fov, self.viewer_distance, self.camera_x, self.camera_y, self.camera_z, self.camera_angle_x, self.camera_angle_y, self.camera_angle_z):
                    if boid.distance((self.camera_x,self.camera_y,self.camera_z)) < self.rangeattack:
                        print("Collision detected with boid at position:", boid.position)
                        boid.push(self.camera_x,self.camera_y,self.camera_z)
                        boid.collisiontomouse = True
                        # boid.apply_mouse_repulsion((boid.position[0],boid.position[1],boid.position[2]), self.repulsion_distance, self.repulsion_strength)
                        # boid.move_random_direction()
                    else:
                        print("too far",boid.distance((self.camera_x,self.camera_y,self.camera_z)))




# Main loop
def shake(value):
    return math.radians(random.uniform(-1, 1))*value
soliox = []
def add_hitbox(x1, x2,y1,y2,z1,z2):
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    z_min, z_max = min(z1, z2), max(z1, z2)
    soliox.append((x_min, x_max, y_min, y_max, z_min, z_max))

def check_forsolid(x,y,z,xd,yd,zd,chamber=100):
    if y < chamber:
        return True
    for hitbox in soliox:
        x_min, x_max, y_min, y_max, z_min, z_max = hitbox
        if (x - xd <= x_max and x + xd >= x_min and
            y - yd <= y_max and y + yd >= y_min and
            z - zd <= z_max and z + zd >= z_min):
            return True
    return False
def stair(x,y,z,length,xd,yd,zd):
    for i in range(length):
        add_hitbox(i*xd+x, i*xd+x+100, i*yd+y, i*yd+y+100, i*zd+z, i*zd+z+100)
balllist = []
class Ball:
    def __init__(self, x, y, z, radius, color, screen_width, screen_height, screen_depth,chamber=100,xd=0,yd=0,zd=0):
        self.position = [x, y, z]
        self.velocity = [xd, yd, zd]
        self.radius = radius
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen_depth = screen_depth
        self.gravity = 1
        self.chamber = chamber
        self.image = image.load(os.path.join('assets', 'SaleuoA.png'))
        self.time = 0
        self.collison = 0

    def update(self, delta):
        self.velocity[1] -= self.gravity * delta
        self.position[0] += self.velocity[0] * delta
        if check_forsolid(self.position[0],self.position[1],self.position[2],self.radius,self.radius,self.radius,chamber=self.chamber):
            self.position[0] -= self.velocity[0] * delta
            self.velocity[0] = -0.6 * self.velocity[0]
            self.collison += 1
        self.position[1] += self.velocity[1] * delta
        if check_forsolid(self.position[0],self.position[1],self.position[2],self.radius,self.radius,self.radius,chamber=self.chamber):
            self.position[1] -= self.velocity[1] * delta
            self.velocity[1] = -0.6 * self.velocity[1]
            self.collison += 1
        self.position[2] += self.velocity[2] * delta
        if check_forsolid(self.position[0],self.position[1],self.position[2],self.radius,self.radius,self.radius,chamber=self.chamber):
            self.position[2] -= self.velocity[2] * delta
            self.velocity[2] = -0.6 * self.velocity[2]
            self.collison += 1

        self.velocity[0] *= 0.98
        self.velocity[1] *= 0.98
        self.velocity[2] *= 0.98
        self.time += 1
        if self.time > 600 or self.collison > 8:
            balllist.remove(self)
    def distance(self, other):
        if isinstance(other, tuple):
            return math.sqrt((self.position[0] - other[0]) ** 2 + (self.position[1] - other[1]) ** 2 + (self.position[2] - other[2]) ** 2)
        else:
            return math.sqrt((self.position[0] - other.position[0]) ** 2 + (self.position[1] - other.position[1]) ** 2 + (self.position[2] - other.position[2]) ** 2)
    def draw(self, screen, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z):
        # x, y, z = project_3d_to_2d(self.position[0], self.position[1], self.position[2], self.screen_width, self.screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z)
        # if z > 0:  # Ensure the ball is in front of the camera
        #     scale_factor = max(0.0001, min(800.0, 100 / z))  # Adjust the scale factor as needed
        #     scaled_image = transform.scale(self.image, (int(self.radius * 2 * scale_factor), int(self.radius * 2 * scale_factor)))
        #     screen.blit(scaled_image, (x - self.radius * scale_factor, y - self.radius * scale_factor))
        draw_cube(screen, self.position[0], self.position[1], self.position[2], self.screen_width, self.screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z, self.radius * 2, self.radius * 2, self.radius * 2, self.color)
        draw_cube(screen, self.position[0]+self.radius/2, self.position[1]+self.radius/2, self.position[2]+self.radius/2, self.screen_width, self.screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y, camera_angle_z, self.radius, self.radius, self.radius, self.color)

def main():
    global screen
    clock = pygame.time.Clock()
    separation_distance = 35
    alignment_distance = 50
    cohesion_distance = 65
    separation_resolve = 0.04
    alignment_resolve = 0.02
    cohesion_resolve = 0.02
    # separation_resolve = 0
    # alignment_resolve = 0
    # cohesion_resolve = 0
    repulsion_distance = 175
    repulsion_strength = 0.05
    top_speed = 3
    rangeattack = 50000
    screen_depth = 1000
    player_speed = 10
    player_speedx = 0
    player_speedy = 0
    player_speedz = 0
    phi = 1 + math.sqrt(5) / 2
    player_height = 160
    eye_height = player_height*0.8
    wipth=player_height/phi/math.sqrt(2)
    player_width = wipth
    player_depth = wipth
    fov = 512
    volume = player_height*player_width*player_depth/1000000
    print(volume)
    viewer_distance = 2  # Adjusted viewer distance
    camera_x, camera_y, camera_z = screen_width / 2, screen_height / 2, screen_depth/2  # Initial camera position
    player_x, player_y, player_z = screen_width / 2, 5000+player_height*2, screen_depth/2  # Initial player position
    camera_angle_x = 0
    camera_angle_y = 0
    camera_angle_z = 0
    camera_speed = 0.1  # Speed of camera movement
    smoving_speed = 24/8
    moving_speed = smoving_speed
    fishima = os.path.join('assets', 'fish.png')
    salmonela = os.path.join('assets', 'salmon.png')
    tunala = os.path.join('assets', 'rainbow_fish.png')
    background = os.path.join('assets', 'water.png')
    background = image.load(background)
    background = transform.scale(background, (screen_width, screen_height))
    boids = []
    new_camera_angle_x = camera_angle_x
    new_camera_angle_y = camera_angle_y
    new_camera_angle_z = camera_angle_z
    shaking = 0
    isshaking = False
    t0 = time.time()
    t1 = time.time()
    delta = 0
    setfps = 600
    fps = 60
    chamber = 100
    buff = False
    shake_level = 0
    gravity = 1
    for i in range(20):
        randomwidth = random.uniform(36, 36)
        randomheight = int(randomwidth * 16 / 36)
        boids.append(Boid(screen_width, screen_height, screen_depth, separation_resolve, alignment_resolve, cohesion_resolve, top_speed, fishima, random.uniform(0, screen_width), random.uniform(0, screen_height), random.uniform(0, screen_depth), fish_type='cod', width=randomwidth, height=randomheight,margin=chamber))
        randomwidth = random.uniform(45, 72)
        randomheight = int(randomwidth * 16 / 45)
        boids.append(Boid(screen_width, screen_height, screen_depth, separation_resolve, alignment_resolve, cohesion_resolve, top_speed, salmonela, random.uniform(0, screen_width), random.uniform(0, screen_height), random.uniform(0, screen_depth), fish_type='salmon', width=randomwidth, height=randomheight,margin=chamber))
        randomwidth = random.uniform(14, 72)
        randomheight = int(randomwidth * 16 / 14)
        boids.append(Boid(screen_width, screen_height, screen_depth, separation_resolve, alignment_resolve, cohesion_resolve, top_speed, tunala, random.uniform(0, screen_width), random.uniform(0, screen_height), random.uniform(0, screen_depth), fish_type='rainbow', width=randomwidth, height=randomheight,margin=chamber))
    xv = 0
    yv = 0
    zv = 0
    pxv = 0
    pyv = 0
    pzv = 0
    # for i in range(10):
    #     xv = random.randint(-10000, 10000)
    #     yv = random.randint(-10000, 10000)
    #     zv = random.randint(-10000, 10000)
        
    #     dx = random.randint(-1000, 1000) - xv
    #     dy = random.randint(-1000, 1000) - yv
    #     dz = random.randint(-1000, 1000) - zv
        
    #     anglex = math.degrees(math.atan2(dy, dx)) + 180
    #     angley = math.degrees(math.atan2(dz, dx)) + 180
    #     angle_y_sin = math.sin(math.radians(angley))
    #     angle_y_cos = math.cos(math.radians(angley))
    #     angle_x_sin = math.sin(math.radians(anglex))
    #     angle_x_cos = math.cos(math.radians(anglex))
        
    #     xv += 1*(-angle_y_sin*angle_x_cos)
    #     yv += 1*(-angle_x_sin)
    #     zv += 1*(angle_y_cos*angle_x_cos)
        
    #     add_hitbox(xv, xv + 100, yv, yv + 100, zv, zv + 100)
        
    #     pxv = xv
    #     pyv = yv
    #     pzv = zv
    # stair(100,100,100,100,10,10,0)
    # stair(100,100,200,100,10,10,0)
    # stair(100,100,300,100,10,10,0)
    # stair(100,200,0,100,10,10,0)
    # stair(100,200,400,100,10,10,0)
    running = True
    height_fall = 0
    collision_mouse = CollisionMouse(boids, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, camera_angle_x, camera_angle_y,camera_angle_z,repulsion_distance, repulsion_strength,rangeattack)
    player_slowtime = 0
    # for _ in range(10):  # Add 10 more balls
        # balllist.append(Ball(
        #     random.uniform(0, screen_width),
        #     random.uniform(0, screen_height),
        #     random.uniform(0, screen_depth),
        #     random.uniform(10, 30),  # Random radius between 10 and 30
        #     WHITE,
        #     screen_width,
        #     screen_height,
        #     screen_depth,
        #     chamber=chamber
        # ))
    firerate = 0
    canrun = False
    falling = 99
    while running:
        t0 = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        delta = 1#(t0*fps - t1*fps)
        mouse_pos = pygame.mouse.get_rel()
        camera_angle_y += mouse_pos[0]/100
        camera_angle_x -= mouse_pos[1]/100
        mousepressed = pygame.mouse.get_pressed()
        keypressed = pygame.key.get_pressed()
        if mousepressed[0]:
            for boid in boids:
                boid.apply_mouse_repulsion((camera_x,camera_y,camera_z), repulsion_distance, repulsion_strength)
        if player_slowtime < 1:
            if keypressed[pygame.K_b]:
                buff = True
                moving_speed = smoving_speed*2*player_height/180
            else:
                buff = False 
                moving_speed = smoving_speed*player_height/180
        else:
            player_slowtime -= 1
            moving_speed = smoving_speed*player_height/180/20
        if keypressed[pygame.K_w]:
            player_speedz += math.cos(camera_angle_y) * moving_speed
            player_speedx += math.sin(camera_angle_y) * moving_speed
            shaking = 2
            shake_level = 1
        if keypressed[pygame.K_s]:
            player_speedz -= math.cos(camera_angle_y) * moving_speed
            player_speedx -= math.sin(camera_angle_y) * moving_speed
            shaking = 2
            shake_level = 1
        if keypressed[pygame.K_a]:
            player_speedx -= math.cos(camera_angle_y) * moving_speed
            player_speedz += math.sin(camera_angle_y) * moving_speed
        if keypressed[pygame.K_d]:
            player_speedx += math.cos(camera_angle_y) * moving_speed
            player_speedz -= math.sin(camera_angle_y) * moving_speed
        # if keypressed[pygame.K_LEFT]:
        #     camera_angle_y -= camera_speed
        # if keypressed[pygame.K_RIGHT]:
        #     camera_angle_y += camera_speed
        # if keypressed[pygame.K_UP]:
        #     camera_angle_x += camera_speed
        # if keypressed[pygame.K_DOWN]:
        #     camera_angle_x -= camera_speed
        if keypressed[pygame.K_q]:
            player_speedy += 10
        if keypressed[pygame.K_e]:
            player_speedy -= 10
        if keypressed[pygame.K_z]:
            fov = 1522
        else:
            fov = 512
        if firerate > 0:
            firerate -= 1
        if keypressed[pygame.K_c] and firerate < 1:
            camera_angle_y_sin = math.sin((-camera_angle_y))
            camera_angle_y_cos = math.cos((-camera_angle_y))
            camera_angle_x_sin = math.sin((-camera_angle_x))
            camera_angle_x_cos = math.cos((-camera_angle_x))
            balllist.append(Ball(
            player_x-player_width/2,
            player_y+eye_height,
            player_z-player_depth/2,
            random.uniform(45, 45),  # Random radius between 10 and 30
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
            screen_width,
            screen_height,
            screen_depth,
            chamber=chamber,
            xd = 100*(-camera_angle_y_sin*camera_angle_x_cos),
            yd = 100*(-camera_angle_x_sin),
            zd = 100*(camera_angle_y_cos*camera_angle_x_cos)
        ))
            firerate = 3
        # if keypressed[pygame.K_SPACE]:
        #     mouse_pos = pygame.mouse.get_pos()
        #     collision_mouse.check_collisions(mouse_pos)
        if keypressed[pygame.K_r]:
            shaking = 60
            shake_level = random.uniform(1.1, 6.5)
        if keypressed[pygame.K_t]:
            chamber += 10
        if keypressed[pygame.K_y]:
            chamber -= 10
        if keypressed[pygame.K_SPACE] and falling < 3:
            if buff:
                player_speedy = 40#*player_height/160
            else:
                player_speedy = 25#*player_height/160
        

        screen.fill(BLUE)
        screen.blit(background, (0, 0))
        if shaking > 0:
            shakex = shake(shake_level)
            shakey = shake(shake_level)
            shakez = shake(shake_level)
            new_camera_angle_z += shakez
            new_camera_angle_x += shakex
            new_camera_angle_y += shakey
            new_camera_angle_x +=(camera_angle_x-new_camera_angle_x)*0.2
            new_camera_angle_y +=(camera_angle_y-new_camera_angle_y)*0.2
            new_camera_angle_z +=(camera_angle_z-new_camera_angle_z)*0.2
            shakex*=0.8
            shakey*=0.8
            shakez*=0.8
            shaking -= 1
        else:
            new_camera_angle_z +=(camera_angle_z-new_camera_angle_z)*0.2
            new_camera_angle_x +=(camera_angle_x-new_camera_angle_x)*0.2
            new_camera_angle_y +=(camera_angle_y-new_camera_angle_y)*0.2
            shake_level *= 0.9
            if shake_level>0.1:
                shaking = 1
        player_speedy -=gravity*delta#*volume
        player_x += player_speedx*delta
        falling += 1
        if check_forsolid(player_x,player_y,player_z,player_width,player_height,player_depth,chamber=chamber):
            player_y+=10
            if check_forsolid(player_x,player_y,player_z,player_width,player_height,player_depth,chamber=chamber):
                player_y-=10
                player_x -= player_speedx*delta
                player_speedx = -0.3*player_speedx
                print("collisionx")
            player_speedx*=0.95
        player_y += player_speedy*delta
        if check_forsolid(player_x,player_y,player_z,player_width,player_height,player_depth,chamber=chamber):
            player_y -= player_speedy*delta
            canrun = True
            if player_speedy < 0:
                on_ground = True
                player_speedx *= 0.8
                player_speedz *= 0.8
            if player_speedy < 0:
                if player_speedy < -3:
                    height_fall = player_speedy*delta
                    # if height_fall < -80:
                    #     player_slowtime = 1500
                player_speedy = -0.3*player_speedy
            else:
                player_speedy = 0
                on_ground = False
                canrun = False
            if canrun:
                if on_ground:
                    falling = 0
                    player_speedy *= 0.8
        player_z += player_speedz*delta
        if check_forsolid(player_x,player_y,player_z,player_width,player_height,player_depth,chamber=chamber):
            player_y+=10
            if check_forsolid(player_x,player_y,player_z,player_width,player_height,player_depth,chamber=chamber):
                player_y-=10
                player_z -= player_speedz*delta
                player_speedz = -0.3*player_speedz
                print("collisionz")
            player_speedz*=0.95
        camera_x = player_x
        camera_y = player_y+eye_height
        camera_z = player_z
        player_speedx*=0.9
        # player_speedy*=0.98
        player_speedz*=0.9
        px,py,pz = project_3d_to_2d(player_x, player_y, player_z, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, new_camera_angle_z)
        # if player_x < player_width+chamber:
        #     player_x = player_width+chamber
        # if player_x > screen_width-player_width-chamber:
        #     player_x = screen_width-player_width-chamber
        # if player_y < -chamber:
        #     player_y = -chamber
        # if player_y > screen_height-player_height-chamber:
        #     player_y = screen_height-player_height-chamber
        # if player_z < player_depth+chamber:
        #     player_z = player_depth+chamber
        # if player_z > screen_depth-player_depth-chamber:
        #     player_z = screen_depth-player_depth-chamber
        

        # Draw the 3D bounding box
        draw_3d_box(screen, 0,0,0,screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, new_camera_angle_z,screen_width, screen_height, screen_depth)
        draw_3d_box(screen, chamber,chamber,chamber,screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, new_camera_angle_z,screen_width-chamber, screen_height-chamber, screen_depth-chamber)
        for hitbox in soliox:
            x_min, x_max, y_min, y_max, z_min, z_max = hitbox
            draw_cube(screen, x_min, y_min, z_min, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, new_camera_angle_z, x_max-x_min, y_max-y_min, z_max-z_min,(255,255,255))
        plywitx = player_x+player_width/2
        plywity = player_y+player_height
        plywitz = player_z+player_depth/2

        draw_cube(screen, plywitx, plywity, plywitz, screen_width, screen_height, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, new_camera_angle_z, player_x-player_width/2-plywitx, player_y-plywity, player_z-player_depth/2-plywitz,(255,0,0))

        boids.sort(key=lambda boid: -boid.distance((camera_x, camera_y, camera_z)))

        for boid in boids:
            boid.apply_separation(boids, separation_distance)
            boid.apply_alignment(boids, alignment_distance)
            boid.apply_cohesion(boids, cohesion_distance)
            boid.apply_mouse_repulsion((0, 0, 0), 75, 0.005)
            boid.update_position(delta)
            boid.draw(screen, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, camera_angle_z)
            boid.margin = chamber
        for ball in balllist:
            ball.update(delta)
            ball.draw(screen, fov, viewer_distance, camera_x, camera_y, camera_z, new_camera_angle_x, new_camera_angle_y, camera_angle_z)
        pygame.display.flip()
        clock.tick(setfps)
        t1 = t0

    pygame.quit()

if __name__ == "__main__":
    main()