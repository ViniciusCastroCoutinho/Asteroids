# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the interactive game entities and their local behaviors.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos, draw_image
from enum import Enum
import os

current_directory = dir_path = os.path.dirname(os.path.realpath(__file__))
resources = os.path.join(current_directory, "resources")


class EnumPowerUps(Enum):
    """File paths for power up images"""

    SHOTGUN = os.path.join(resources, "Shotgun.png")
    ONE_UP = os.path.join(resources, "One_Up.png")

    @classmethod
    def _missing_(cls, value):
        # If not valid value, return MISSING
        MISSING = os.path.join(resources, "Missing.png")
        for member in cls:
            if member.value == value:
                return member
        return MISSING


class Bullet(pg.sprite.Sprite):
    """Initialize a player bullet with position, velocity, and lifetime"""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BULLET_TTL  # time to live
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """
        Move the bullet, wrap it on screen, and expire it over time.
        :param dt: time passed
        """
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
            return

        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the bullet on the target surface"""
        draw_circle(surf, self.pos, self.r)


class UfoBullet(pg.sprite.Sprite):
    """Initialize a UFO bullet with position, velocity, and lifetime"""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.UFO_BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """Move the UFO bullet, wrap it on screen, and expire it over time"""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the UFO bullet on the target surface"""
        draw_circle(surf, self.pos, self.r)


class Asteroid(pg.sprite.Sprite):
    """Initialize an asteroid with its position, velocity, and size profile"""

    def __init__(self, pos: Vec, vel: Vec, size: str, type: str = "normal"):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.size = size
        self.type = type
        if self.type == "tough":
            self.hp = 3
        else:
            self.hp = 1
        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        """Build an irregular polygon outline based on the asteroid size"""
        steps = 12 if self.size == "L" else 10 if self.size == "M" else 8
        pts = []
        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(0.75, 1.2)
            r = self.r * jitter
            v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            pts.append(v * r)
        return pts

    def update(self, dt: float):
        """Move the asteroid and wrap it across the screen"""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the asteroid outline on the target surface"""
        pts = [(self.pos + p) for p in self.poly]
        if self.hp == 3:
            pg.draw.polygon(surf, C.BRIGHT_RED, pts, width=0)
        elif self.hp == 2:
            pg.draw.polygon(surf, C.DARK_RED, pts, width=0)

        if self.type == "explosive":
            pg.draw.polygon(surf, C.EXPLOSIVE, pts, width=0)

        pg.draw.polygon(surf, C.WHITE, pts, width=1)


class Ship(pg.sprite.Sprite):
    """Initialize the player ship and its gameplay state"""

    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.alive = True
        self.r = C.SHIP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

        self.powerup = ""  # Default = ""
        self.powerup_duration = 0

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        """Apply rotation, thrust, and friction from the current input state"""
        if keys[pg.K_LEFT]:
            self.angle -= C.SHIP_TURN_SPEED * dt
        if keys[pg.K_RIGHT]:
            self.angle += C.SHIP_TURN_SPEED * dt
        if keys[pg.K_UP]:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt
        self.vel *= C.SHIP_FRICTION

    def fire(self) -> list[Bullet] | None:
        """
        Spawn a player bullet when the fire cooldown allows it.
        Returns a tuple containing a Bullet object and a powerup string
        """
        if self.cool > 0:
            return None
        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE

        if self.powerup == "SHOTGUN":
            dirv2 = angle_to_vec(self.angle + C.SHOTGUN_ANGLE)
            pos2 = self.pos + dirv2 * (self.r + 6)
            vel2 = self.vel + dirv2 * C.SHIP_BULLET_SPEED

            dirv3 = angle_to_vec(self.angle - C.SHOTGUN_ANGLE)
            pos3 = self.pos + dirv3 * (self.r + 6)
            vel3 = self.vel + dirv3 * C.SHIP_BULLET_SPEED

            return [Bullet(pos, vel), Bullet(pos2, vel2), Bullet(pos3, vel3)]
        else:
            return [Bullet(pos, vel)]

    def hyperspace(self):
        """Teleport the ship to a random location and reset its momentum"""
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    def update(self, dt: float):
        """Advance cooldowns, move the ship, and wrap it on screen"""
        if self.cool > 0:
            self.cool -= dt
        if self.invuln > 0:
            self.invuln -= dt
        if self.powerup_duration > 0:
            self.powerup_duration -= dt

        if self.powerup_duration <= 0:
            self.powerup = ""

        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the ship and its temporary invulnerability indicator"""
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + 140)
        right = angle_to_vec(self.angle - 140)
        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * 0.9
        p3 = self.pos + right * self.r * 0.9
        draw_poly(surf, [p1, p2, p3])
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)
        # pg.draw.rect(surf, C.WHITE, self.rect, width=1)


class UFO(pg.sprite.Sprite):
    """Initialize a UFO enemy with its size profile and movement state"""

    def __init__(self, pos: Vec, small: bool):
        super().__init__()
        self.pos = Vec(pos)
        self.small = small
        profile = C.UFO_SMALL if small else C.UFO_BIG
        self.r = profile["r"]
        self.aim = profile["aim"]
        self.speed = C.UFO_SPEED
        self.cool = C.UFO_FIRE_EVERY
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.dir = Vec(1, 0) if uniform(0, 1) < 0.5 else Vec(-1, 0)

    def update(self, dt: float):
        """Move the UFO, advance its fire cooldown, and remove it off screen"""
        self.pos += self.dir * self.speed * dt
        self.cool -= dt
        if self.pos.x < -self.r * 2 or self.pos.x > C.WIDTH + self.r * 2:
            self.kill()
        self.rect.center = self.pos

    def fire_at(self, target_pos: Vec) -> UfoBullet | None:
        """Fire a bullet toward the ship with accuracy based on the UFO type"""
        if self.cool > 0:
            return None
        aim_vec = Vec(target_pos) - self.pos
        if aim_vec.length_squared() == 0:
            aim_vec = self.dir.normalize()
        else:
            aim_vec = aim_vec.normalize()
        max_error = (1.0 - self.aim) * 60.0
        shot_dir = aim_vec.rotate(uniform(-max_error, max_error))
        self.cool = C.UFO_FIRE_EVERY
        spawn_pos = self.pos + shot_dir * (self.r + 6)
        vel = shot_dir * C.UFO_BULLET_SPEED
        return UfoBullet(spawn_pos, vel)

    def draw(self, surf: pg.Surface):
        """Draw the UFO body on the target surface"""
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.WHITE, rect, width=1)
        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)


class Hunter(pg.sprite.Sprite):
    """Enemy ship that actively chases the player using steering behaviors."""

    def __init__(self, pos: Vec, target: Ship):
        super().__init__()
        self.target = target
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)

        # Reusing UFO Small radius for collision consistency
        self.r = C.UFO_SMALL["r"]
        self.speed = C.HUNTER_SPEED
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """Calculate direction to player and adjust velocity."""
        if not self.target.alive:
            return

        # 1. Get direction vector towards the player
        aim_vec = self.target.pos - self.pos

        if aim_vec.length_squared() > 0:
            aim_vec = aim_vec.normalize()

        # 2. Apply acceleration towards the player using agility factor
        acceleration = aim_vec * self.speed * dt * C.HUNTER_AGILITY
        self.vel += acceleration

        # 3. Apply friction to prevent infinite orbiting
        self.vel *= 0.98

        # 4. Cap maximum speed
        if self.vel.length() > self.speed:
            self.vel.scale_to_length(self.speed)

        # 5. Update position and wrap around screen
        self.pos += self.vel
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.BRIGHT_RED, rect, width=1)

        # Cockpit/Cup
        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)


class PowerUp(pg.sprite.Sprite):
    """Initialize a Powerup"""

    def __init__(self, pos: Vec, power_up_type: str):
        super().__init__()
        self.pos = Vec(pos)
        self.type = power_up_type
        self.image = pg.image.load(EnumPowerUps[self.type].value).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos.x, self.pos.y
        self.idle_time = 1
        self.state = "down"  # just for idle animation

    def update(self, dt: float):
        """Animate the power up"""
        if self.idle_time > 0:
            self.idle_time -= dt

        else:
            if self.state == "down":
                self.pos.y -= 5
                self.state = "up"

            elif self.state == "up":
                self.pos.y += 5
                self.state = "down"

            self.idle_time = 1

            self.pos = wrap_pos(self.pos)
            self.rect.topleft = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the power up on the target surface"""
        draw_image(surf, self.pos, self.image)
        # pg.draw.rect(surf, C.WHITE, self.rect, width=1)
