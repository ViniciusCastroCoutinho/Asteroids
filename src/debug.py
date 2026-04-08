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
        self.i = 1
        pg.init()
        if C.RANDOM_SEED is not None:
            random.seed(C.RANDOM_SEED)
        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroids (Debug)")
        self.clock = pg.time.Clock()
        self.scene = Scene("play")
        self.font = pg.font.SysFont("consolas", 20)
        self.big = pg.font.SysFont("consolas", 48)
        self.world = World()

    def run(self):
        while True:
            self.screen.fill(C.BLACK)

            dt = self.clock.tick(C.FPS) / 1000.0
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)
                if e.type == pg.KEYDOWN:
                    # ESC: encerra o jogo nas cenas menu/play; volta ao menu no game over
                    if e.key == pg.K_ESCAPE:
                        if self.scene.name == "game_over":
                            self.scene = Scene("menu")
                        else:
                            pg.quit()
                            sys.exit(0)
                    elif self.scene.name == "play":
                        if e.key == pg.K_SPACE:
                            self.world.try_fire()
                        if e.key == pg.K_LSHIFT:
                            self.world.hyperspace()
                    elif self.scene.name == "menu":
                        self.world = World()
                        self.scene = Scene("play")
                    elif self.scene.name == "game_over":
                        if e.key in (pg.K_RETURN, pg.K_SPACE):
                            self.world = World()
                            self.go_fade = 0.0
                            self.scene = Scene("play")

            keys = pg.key.get_pressed()

            if self.scene.name == "menu":
                pass
                # self.draw_menu()
            elif self.scene.name == "play":
                self.world.update(dt, keys)
                self.world.draw(self.screen, self.font)
                # Verifica se o mundo sinalizou fim de jogo
                if self.world.game_over:
                    self.final_score = self.world.score
                    self.go_fade = 0.0
                    self.scene = Scene("game_over")
            elif self.scene.name == "game_over":
                self.go_fade += dt
                # self.draw_game_over()

            test_pos = Vec(C.WIDTH // 2 - 110, C.HEIGHT // 2 - 20)

            # pw = sprites.PowerUp(test_pos, "SHOTGUN")
            # utils.draw_image(self.screen, pw.pos, image=pw.image)
            #
            if self.i:
                self.world.spawn_power_up(test_pos, "SHOTGUN")
                self.i = 0

            # print(list(self.world.power_ups.sprites())[0].pos)
            # print(list(self.world.power_ups.sprites())[0].rect.top)
            # print(list(self.world.power_ups.sprites())[0].rect.left)

            pg.display.flip()
