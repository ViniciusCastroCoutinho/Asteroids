import random
import sys
from dataclasses import dataclass

import pygame as pg

import config as C
from systems import World

Vec = pg.math.Vector2


@dataclass
class Scene:
    name: str


class GameDebug:
    def __init__(self):
        pg.init()
        if C.RANDOM_SEED is not None:
            random.seed(C.RANDOM_SEED)
        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroids (Debug)")
        self.clock = pg.time.Clock()
        self.world = World()

    def run(self):
        while True:
            self.screen.fill(C.BLACK)

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)

            # testing goes here
            # utils.draw_image(self.screen, Vec(C.WIDTH // 2 - 110, C.HEIGHT // 2 - 20), image_path=EnumPowerUps["SHOTGUN"])

            pg.display.flip()
