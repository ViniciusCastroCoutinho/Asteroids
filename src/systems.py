# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
import random
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, Ship, UFO, PowerUp, EnumPowerUps
from utils import Vec, rand_edge_pos, rand_unit_vec, draw_image


class World:
    """Initialize the world state, entity groups, timers, and player progress."""

    def __init__(self):
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.power_ups = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group(self.ship)

        self.score = 0
        self.lives = C.START_LIVES
        self.wave = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.game_over = False  # Sinaliza fim de jogo para a cena principal

    def start_wave(self):
        """Spawn a new asteroid wave with difficulty based on the current round."""
        self.wave += 1
        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel = Vec(math.cos(ang), math.sin(ang)) * speed
            special_chance = random.randint(1, 100)
            if (
                special_chance <= C.TOUGH_AST_CHANCE
                and special_chance <= C.EXPLOSIVE_AST_CHANCE
            ):
                choice = random.choice(["tough", "explosive"])
                self.spawn_asteroid(pos, vel, "L", type=choice)
            elif special_chance <= C.TOUGH_AST_CHANCE:
                self.spawn_asteroid(pos, vel, "L", type="tough")
            elif special_chance <= C.EXPLOSIVE_AST_CHANCE:
                self.spawn_asteroid(pos, vel, "L", type="explosive")
            else:
                self.spawn_asteroid(pos, vel, "L")

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str, type: str = "normal"):
        """Create an asteroid and register it in the world groups."""
        a = Asteroid(pos, vel, size, type)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_ufo(self):
        """Spawn a single UFO at a screen edge and send it across the playfield."""
        if self.ufos:
            return
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def ufo_try_fire(self):
        """Let every active UFO attempt to fire at the ship."""
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def try_fire(self):
        """Fire a player bullet when the bullet cap allows it."""
        if len(self.bullets) >= C.MAX_BULLETS:
            return
        bullets = self.ship.fire()
        if bullets:
            for b in bullets:
                self.bullets.add(b)
                self.all_sprites.add(b)

    def spawn_power_up(self, pos: Vec, power_up: str):
        pw_up = PowerUp(pos, power_up)
        self.power_ups.add(pw_up)
        self.all_sprites.add(pw_up)

    def hyperspace(self):
        """Trigger the ship hyperspace action and apply its score penalty."""
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    def update(self, dt: float, keys):
        """Update the world simulation, timers, enemy behavior, and progression."""
        self.ship.control(keys, dt)
        self.all_sprites.update(dt)
        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5
        if self.ufos:
            self.ufo_try_fire()
        else:
            self.ufo_timer -= dt
        if not self.ufos and self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        self.handle_collisions()

        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    def handle_collisions(self):
        """Resolve collisions between bullets, asteroids, UFOs, and the ship."""
        # asteroid is hit
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in hits.items():
            self.split_asteroid(ast)

        ufo_hits = pg.sprite.groupcollide(
            self.asteroids,
            self.ufo_bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in ufo_hits.items():
            self.split_asteroid(ast)

        # ship is hit
        if self.ship.invuln <= 0 and self.safe <= 0:
            for ast in self.asteroids:
                if (ast.pos - self.ship.pos).length() < (ast.r + self.ship.r):
                    self.ship_die()
                    break
            for ufo in self.ufos:
                if (ufo.pos - self.ship.pos).length() < (ufo.r + self.ship.r):
                    self.ship_die()
                    break
            for bullet in self.ufo_bullets:
                if (bullet.pos - self.ship.pos).length() < (bullet.r + self.ship.r):
                    bullet.kill()
                    self.ship_die()
                    break

        # power ups
        for pw in self.power_ups:
            if pg.sprite.collide_rect(pw, self.ship):
                pw.kill()
                self.ship.powerup = pw.type
                self.ship.powerup_duration = C.POWERUP_DURATION
                break

        # ufo is hit
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.score += score
                    ufo.kill()
                    b.kill()
                    if not ufo.small:
                        self.spawn_power_up(ufo.pos, "SHOTGUN")

    def split_asteroid(self, ast: Asteroid):
        """Destroy/Damage an asteroid, award score, and spawn its smaller fragments."""
        self.score += C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.hp -= 1
        if ast.hp == 0:
            ast.kill()
            if ast.type != "explosive":
                for s in split:
                    dirv = rand_unit_vec()
                    speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
                    self.spawn_asteroid(pos, dirv * speed, s)

            # explosive asteroid
            else:
                for other_ast in self.asteroids:
                    if (other_ast.pos - ast.pos).length() <= C.EXPLOSIVE_AST_RANGE:
                        self.split_asteroid(other_ast)
                for ufo in self.ufos:
                    if (ufo.pos - ast.pos).length() <= C.EXPLOSIVE_AST_RANGE:
                        score = (
                            C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                        )
                        self.score += score
                        ufo.kill()
                        if not ufo.small:
                            self.spawn_power_up(ufo.pos, "SHOTGUN")
                if (self.ship.pos - ast.pos).length() <= C.EXPLOSIVE_AST_RANGE:
                    if self.ship.invuln <= 0 and self.safe <= 0:
                        self.ship_die()

    def ship_die(self):
        """Remove uma vida; sinaliza game over ou reposiciona a nave."""
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True  # Game.run() detecta e muda de cena
            return
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        """Draw all world entities and the current HUD information."""
        for spr in self.all_sprites:
            spr.draw(surf)

        if self.ship.powerup:
            image_rect = draw_image(
                surf,
                (C.WIDTH - (C.WIDTH / 10), 5),
                EnumPowerUps[self.ship.powerup].value,
            ).get_rect()
            image_rect.topleft = (C.WIDTH - (C.WIDTH / 10), 5)
            pg.draw.rect(surf, C.WHITE, image_rect, width=1)

        pg.draw.line(surf, (60, 60, 60), (0, 60), (C.WIDTH, 60), width=1)
        txt = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))
