import pygame
from pygame import image, transform
import random
import math
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 1300
screen_height = screen_width * 600 // 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Boid Simulator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)

class Water:
    def __init__(self, width, height, num_points):
        self.width = width
        self.height = height
        self.num_points = num_points
        self.points = [(random.randint(0, width), random.randint(0, height)) for _ in range(num_points)]
        self.texture = self.generate_voronoi_texture()

    def generate_voronoi_texture(self):
        texture = pygame.Surface((self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                closest_point = min(self.points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
                distance_to_closest = math.sqrt((closest_point[0] - x) ** 2 + (closest_point[1] - y) ** 2)
                brightness = min(255, int(distance_to_closest / 2))  # Adjust the divisor to control brightness scaling
                brightness *= 4  # Amplify the brightness
                if brightness > 160:
                    brightness = 160
                color = (brightness, brightness, 255)  # Blue with varying brightness
                texture.set_at((x, y), color)
        return texture

    def draw(self, screen):
        screen.blit(self.texture, (0, 0))

class Boid:
    def __init__(self, screen_width, screen_height, separation_resolve=0.01, alignment_resolve=0.01, cohesion_resolve=0.01, top_speed=5, fishima=None, x=None, y=None, fish_type='fish'):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.position = [x, y]
        self.velocity = [random.uniform(-1, 1), random.uniform(-1, 1)]
        self.max_speed = top_speed
        self.min_speed = 1
        self.speed_x = random.uniform(self.min_speed, self.max_speed)
        self.speed_y = random.uniform(self.min_speed, self.max_speed)
        self.separation_resolve = separation_resolve
        self.alignment_resolve = alignment_resolve
        self.cohesion_resolve = cohesion_resolve
        self.image = transform.scale(image.load(fishima), (36, 16))
        self.fish_type = fish_type  # Add fish type attribute

    def distance(self, other_boid):
        return math.sqrt((self.position[0] - other_boid.position[0]) ** 2 + (self.position[1] - other_boid.position[1]) ** 2)

    def update_position(self):
        self.position[0] += self.velocity[0] * self.speed_x
        self.position[1] += self.velocity[1] * self.speed_y
        self.check_bounds()
        self.limit_speed()

    def check_bounds(self):
        margin = 50  # Distance from the edge to start turning
        turn_factor = 1  # How strongly to turn back

        if self.position[0] < margin:
            self.velocity[0] += turn_factor
        elif self.position[0] > self.screen_width - margin:
            self.velocity[0] -= turn_factor

        if self.position[1] < margin:
            self.velocity[1] += turn_factor
        elif self.position[1] > self.screen_height - margin:
            self.velocity[1] -= turn_factor

    def move_random_direction(self):
        self.velocity = [random.uniform(-1, 1), random.uniform(-1, 1)]

    def draw(self, screen):
        if self.velocity[0] < 0:
            self.newimage = transform.flip(self.image, True, False)
        else:
            self.newimage = transform.rotate(self.image, 0)
        screen.blit(self.newimage, (self.position[0], self.position[1]))

    def apply_separation(self, boids, separation_distance):
        move_x, move_y = 0, 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < separation_distance:
                move_x += self.position[0] - other_boid.position[0]
                move_y += self.position[1] - other_boid.position[1]
        self.velocity[0] += move_x * self.separation_resolve  # Apply a smaller fraction for smoother separation
        self.velocity[1] += move_y * self.separation_resolve  # Apply a smaller fraction for smoother separation

    def apply_alignment(self, boids, alignment_distance):
        avg_velocity_x, avg_velocity_y = 0, 0
        count = 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < alignment_distance and other_boid.fish_type == self.fish_type:
                avg_velocity_x += other_boid.velocity[0]
                avg_velocity_y += other_boid.velocity[1]
                count += 1
        if count > 0:
            avg_velocity_x /= count
            avg_velocity_y /= count
            self.velocity[0] += (avg_velocity_x - self.velocity[0]) * self.alignment_resolve
            self.velocity[1] += (avg_velocity_y - self.velocity[1]) * self.alignment_resolve

    def apply_cohesion(self, boids, cohesion_distance):
        avg_position_x, avg_position_y = 0, 0
        count = 0
        for other_boid in boids:
            if other_boid != self and self.distance(other_boid) < cohesion_distance and other_boid.fish_type == self.fish_type:
                avg_position_x += other_boid.position[0]
                avg_position_y += other_boid.position[1]
                count += 1
        if count > 0:
            avg_position_x /= count
            avg_position_y /= count
            self.velocity[0] += (avg_position_x - self.position[0]) * self.cohesion_resolve
            self.velocity[1] += (avg_position_y - self.position[1]) * self.cohesion_resolve
    def apply_mouse_repulsion(self, mouse_pos, repulsion_distance, repulsion_strength):
        distance_to_mouse = math.sqrt((self.position[0] - mouse_pos[0]) ** 2 + (self.position[1] - mouse_pos[1]) ** 2)
        if distance_to_mouse < repulsion_distance:
            move_x = self.position[0] - mouse_pos[0]
            move_y = self.position[1] - mouse_pos[1]
            self.velocity[0] += move_x * repulsion_strength
            self.velocity[1] += move_y * repulsion_strength
    def limit_speed(self):
        speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        if speed > self.max_speed:
            self.velocity[0] = (self.velocity[0] / speed) * self.max_speed
            self.velocity[1] = (self.velocity[1] / speed) * self.max_speed

# Main loop
def main():
    clock = pygame.time.Clock()
    separation_distance = 45
    alignment_distance = 60
    cohesion_distance = 75
    separation_resolve = 0.05
    alignment_resolve = 0.1
    cohesion_resolve = 0.01
    repulsion_distance = 75
    repulsion_strength = 0.05
    top_speed = 3.5
    fishima = os.path.join('assets', 'fish.png')
    salmonela = os.path.join('assets', 'salmon.png')
    water = Water(400, 300, 60)
    water = transform.scale(water.texture, (screen_width, screen_height))
    boids = [Boid(screen_width, screen_height, separation_resolve, alignment_resolve, cohesion_resolve, top_speed, fishima, random.uniform(0, screen_width), random.uniform(0, screen_height), fish_type='cod') for _ in range(24)]
    for i in range(24):
        boids.append(Boid(screen_width, screen_height, separation_resolve, alignment_resolve, cohesion_resolve, top_speed, salmonela, random.uniform(0, screen_width), random.uniform(0, screen_height), fish_type='salmon'))
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_pos = pygame.mouse.get_pos()
        mousepressed = pygame.mouse.get_pressed()
        if mousepressed[0]:
            for boid in boids:
                boid.apply_mouse_repulsion(mouse_pos, repulsion_distance, repulsion_strength)

        screen.fill(BLACK)
        screen.blit(water, (0, 0))

        for boid in boids:
            boid.apply_separation(boids, separation_distance)
            boid.apply_alignment(boids, alignment_distance)
            boid.apply_cohesion(boids, cohesion_distance)
            boid.update_position()
            boid.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()