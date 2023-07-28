import pygame
from pygame.locals import MOUSEWHEEL
import requests
import os

# api: https://airlabs.co/docs/flights

pygame.init()  # init pygame

WINDOW_SIZE = (365 * 2, 365 * 2)

window = pygame.display.set_mode(WINDOW_SIZE)
map_surf = pygame.surface.Surface(WINDOW_SIZE)
font = pygame.font.Font(None, 32)
font_planes = pygame.font.Font(None, 15)
running = True
translate = False
background_surf = pygame.transform.scale(pygame.image.load('sprites/texas.png'), WINDOW_SIZE)
cam_zoom = 1
temp_pos = (0, 0)
temp_surf = pygame.surface.Surface(WINDOW_SIZE)
print(background_surf.get_width(), background_surf.get_height())


def grid_conversion(coordinates: (int, int)):  # convert pixel coordinates to longitude and latitude
    lat_sub = 36.5 - 26
    long_sub = 106.6 - 93.5

    x_ratio = coordinates[0] / background_surf.get_width()
    y_ratio = coordinates[1] / background_surf.get_height()
    return -(y_ratio * lat_sub) + 36.5, (x_ratio * long_sub) - 106.6


def reverse_grid_conversion(coordinates: (int, int)):  # convert longitude and latitude to pixel coordinates
    #  first int is the latitude 2nd is the longitude
    lat_sub = 36.5 - 26
    long_sub = 106.6 - 93.5
    return round(((coordinates[1] + 106.6) / long_sub) * background_surf.get_width()), round(
        ((-(coordinates[0] - 36.5)) / lat_sub) * background_surf.get_height())


airport_positions = [
    ['DFW', reverse_grid_conversion((32.8998, -97.0403))],  # DFW (Dallas Fort Worth Airport)
    ['SAT', reverse_grid_conversion((29.5227, -98.4698))]  # SAT (San Antonio Airport)
]

#  Corner pos is 36.5, -106.6 (N W)
#  Other Corner pos is 26, -93.5 (N W)

#  26, -106  (S W)
#  36.5 -93.5 (N E)

#  bounding-box: 26,-106,36.5,-93.5


airports = []
texts = []
for airport in airport_positions:  # load airports
    new_airport_surf = pygame.transform.scale_by(pygame.image.load('sprites/airport.png'), 4)
    airports.append(new_airport_surf)

    airport_text = font.render(airport[0], False, (0, 0, 0))
    texts.append(airport_text)


class Plane(pygame.sprite.Sprite):
    def __init__(self, lat, long, direction, call_sign):
        super().__init__()

        coord = reverse_grid_conversion((lat, long))
        self.pos_x = coord[0]
        self.pos_y = coord[1]
        self.image = pygame.transform.rotate(pygame.image.load('sprites/plane.png'), direction)
        self.call_sign = call_sign
        self.rect = self.image.get_rect()
        self.rect.x = self.pos_x
        self.rect.y = self.pos_y
        self.text = None
        self.text_pos = None

    def update(self, t):
        pygame.transform.scale_by(self.image, cam_zoom)

        if t:
            print(temp_pos)
            self.rect.x = temp_pos[0] + self.pos_x
            self.rect.y = temp_pos[1] + self.pos_y

        if self.rect.collidepoint(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]):
            text_pos = self.pos_x + 5, self.pos_y
            self.text = font_planes.render(self.call_sign, False, (0, 0, 0))
            self.text_pos = text_pos
        else:
            self.text = None
            self.text_pos = None


def load_planes():
    planes_list = []
    req = requests.get(f'https://airlabs.co/api/v9/flights?api_key={os.getenv("apikey")}&bbox=26,-106,36.5,-93.5')
    req_data = req.json()
    for plane_ in req_data['response']:
        if 'reg_number' in plane_.keys():
            planes_list.append(Plane(plane_['lat'], plane_['lng'], plane_['dir'], plane_['reg_number']))
        else:
            planes_list.append(Plane(plane_['lat'], plane_['lng'], plane_['dir'], plane_['flag']))
    return planes_list
    # return [Plane(29.334942, -98.207540, 0, 'hi')]


planes = load_planes()

clock = pygame.Clock()
pygame.time.set_timer(pygame.USEREVENT, 5000)
while running:
    translate = False
    for event in pygame.event.get():  # https://www.pygame.org/docs/
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.USEREVENT:
            # planes = load_planes()
            pygame.time.set_timer(pygame.USEREVENT, 10000)

        if event.type == MOUSEWHEEL:
            if event.y > 0:
                cam_zoom += .1
            else:
                cam_zoom -= .1
            translate_pos_x = -((temp_surf.get_width() / window.get_width()) * pygame.mouse.get_pos()[0])
            translate_pos_y = -((temp_surf.get_width() / window.get_height()) * pygame.mouse.get_pos()[1])
            translate = True
            temp_pos = pygame.mouse.get_pos()[0] + translate_pos_x, pygame.mouse.get_pos()[1] + translate_pos_y

    map_surf.fill('white')
    map_surf.blit(background_surf, (0, 0))
    for airport in range(len(airports)):
        map_surf.blit(airports[airport], airport_positions[airport][1])

    for plane in planes:
        map_surf.blit(plane.image, (plane.pos_x, plane.pos_y))
        plane.update(translate)

        if plane.text_pos is not None:
            map_surf.blit(plane.text, plane.text_pos)

    for text in range(len(texts)):
        pos = list(airport_positions[text][1])
        pos[0] += 30  # offset
        pos[1] += 5
        # noinspection PyTypeChecker
        map_surf.blit(texts[text], tuple(pos))
    temp_surf = pygame.transform.scale_by(map_surf, cam_zoom)
    window.fill('white')
    window.blit(temp_surf, temp_pos)
    pygame.display.flip()  # update display

    clock.tick(60)
