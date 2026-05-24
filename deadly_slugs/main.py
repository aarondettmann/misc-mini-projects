from pathlib import Path
import math
import os
import random
import sys

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from slugs import Slug


class GC:
    """
    Game constants
    """

    class Size:
        # Total window size
        X = 800
        Y = 500
        BBOX = math.sqrt(X**2 + Y**2)

        TOP_BAR_Y = 30
        WIN_HEIGHT_Y = Y - TOP_BAR_Y

    class Path:
        img = Path(r'media/img/')

    # Other constants
    FPS = 40
    CLOCK = pg.time.Clock()


class C:
    """
    Colors
    """

    black = pg.Color(0, 0, 0)
    white = pg.Color(255, 255, 255)

    green = (2, 137, 0)
    light_gray = pg.Color(100, 100, 100)
    lighter_gray = pg.Color(150, 150, 150)
    orange = pg.Color(255, 116, 0)
    pale_green = pg.Color(160, 191, 151)
    sort_of_red = (213, 78, 78)
    sort_of_blue = pg.Color(100, 151, 177)
    teal = pg.Color(0, 76, 76)
    underwater_blue = pg.Color(0, 85, 130)

    @classmethod
    def gray_scale(cls, weight):
        return cls.light_gray.lerp(cls.lighter_gray, min(weight, 1))


# Game parameters
N_SLUGS = 25
N_GRAS = 10
VELOCITY = 30  # [px/s]
DT = 1/GC.FPS  # [s]
DT_FADE_DEAD_TRAIL = 3
DT_MAX_HIT = 2
LEN_SLIME_TRAIL = math.ceil(0.3*GC.Size.BBOX)  # Path only saved once per pixel length
SLUG_SPAWN_POS = [
    [GC.Size.X*0.25, GC.Size.Y*0.25],
    [GC.Size.X*0.75, GC.Size.Y*0.25],
    [GC.Size.X*0.25, GC.Size.Y*0.75],
    [GC.Size.X*0.75, GC.Size.Y*0.75],
]
RADIUS_SLUG = 8
RADIUS_PLAYER = 10
PLAYER_LIVES = 3

VELOCITY_PLAYER = 5  # [px/DT]


class SlugSprite(pg.sprite.Sprite):
    """
    Slug object
    """

    def __init__(self):
        # Instantiate actual slug
        self.slug = Slug(*self.slug_init_pos(), VELOCITY)

        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(os.path.join(GC.Path.img, "slug_posX.png"))

        self.rect = self.image.get_rect()
        self.rect.inflate_ip(-0.1*self.rect.width, -0.1*self.rect.height)
        self.rect.center = (self.x, self.y)

        # self.image = pg.Surface((self.rect.width, self.rect.height))
        # self.image.fill(C.black)

    @property
    def x(self):
        return self.slug.x

    @property
    def y(self):
        return self.slug.y

    @property
    def has_left_window(self):
        return self.x < 0 or self.x > GC.Size.X or self.y < GC.Size.TOP_BAR_Y or self.y > GC.Size.Y

    def slug_init_pos(self):
        return random.choice(SLUG_SPAWN_POS)

    def move(self, dt):
        self.slug.move(dt)
        self.rect.center = (self.slug.x, self.slug.y)
        x, y = self.slug._heading()
        if x > 0:
            self.image = pg.image.load(os.path.join(GC.Path.img, "slug_posX.png"))
        else:
            self.image = pg.image.load(os.path.join(GC.Path.img, "slug_negX.png"))

        if self.has_left_window:
            self.slug.declare_dead()

        if self.slug.dt_dead > DT_FADE_DEAD_TRAIL:
            self.kill()

    def update(self, dt):
        self.move(dt)


class AliveSlugs(pg.sprite.Group):

    def __init__(self, *slugs):
        pg.sprite.Group.__init__(self, slugs)

    def pop_recently_died(self):
        dead_slugs = []
        for slug in self:
            if slug.slug.dead:
                dead_slugs.append(slug)
                slug.kill()
        return dead_slugs


class DeadSlugs(pg.sprite.Group):

    def __init__(self, *slugs):
        pg.sprite.Group.__init__(self, slugs)


class Player(pg.sprite.Sprite):
    """
    Player object
    """

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((1.5*RADIUS_PLAYER, 1.5*RADIUS_PLAYER))
        self.image.fill(C.black)
        self.rect = self.image.get_rect()

        self.rect.x = GC.Size.X*0.5
        self.rect.y = GC.Size.Y*0.5

        self.dt_hit = 0

        self.lives = PLAYER_LIVES

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, x):
        self.rect.x = x

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, y):
        self.rect.y = y

    def update(self, dt, hit):
        if hit or self.dt_hit:
            if self.dt_hit == 0:
                self.lives -= 1

            self.dt_hit += dt

        # Reset dt_hit
        if (self.dt_hit > DT_MAX_HIT) or (not hit and self.dt_hit > 0):
            self.dt_hit = 0


class GrassSprite(pg.sprite.Sprite):
    """
    Grass object
    """

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(os.path.join(GC.Path.img, "grass01.png"))
        ar_img = self.image.get_width()/self.image.get_height()
        self.image = pg.transform.scale(self.image, (math.ceil(0.05*GC.Size.X), math.ceil(0.05*GC.Size.X/ar_img)))

        self.rect = self.image.get_rect()
        self.rect.center = (random.random()*GC.Size.X, GC.Size.TOP_BAR_Y + random.random()*GC.Size.WIN_HEIGHT_Y)


class BoulderSprite(pg.sprite.Sprite):
    """
    Boulder object
    """

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(os.path.join(GC.Path.img, "boulder01.png"))
        ar_img = self.image.get_width()/self.image.get_height()
        self.image = pg.transform.scale(self.image, (math.ceil(0.1*GC.Size.X), math.ceil(0.1*GC.Size.X/ar_img)))

        self.rect = self.image.get_rect()


class AllBoulders(pg.sprite.Group):

    def __init__(self):
        pg.sprite.Group.__init__(self)

        for pos in SLUG_SPAWN_POS:
            boulder = BoulderSprite()
            boulder.rect.center = pos
            self.add(boulder)



class AllGrass(pg.sprite.Group):
    def __init__(self, grass):
        pg.sprite.Group.__init__(self, grass)


def init_surface():
    pg.init()
    pg.display.set_caption("Deadly Slugs")
    surface = pg.display.set_mode((GC.Size.X, GC.Size.Y))
    # surface = pg.display.set_mode((0, 0))

    # TODO
    # pg.display.set_icon()

    surface.fill(C.pale_green)
    pg.display.flip()
    return surface


def main():
    surface = init_surface()
    font = pg.font.SysFont('bitstreamverasans', 18)

    # Player
    player = Player()

    # Slugs
    slugs = AliveSlugs([SlugSprite() for _ in range(N_SLUGS)])
    dead_slugs = DeadSlugs([])
    n_slugs_survived = 0

    # Grass
    all_grass = AllGrass([GrassSprite() for _ in range(N_GRAS)])

    # Boulders
    all_boulders = AllBoulders()

    running = True
    while running:
        level = n_slugs_survived // 100 + 1
        surface.fill(C.pale_green)

        all_grass.draw(surface)

        dead_slugs.update(dt=DT)
        slugs.update(dt=DT)
        dead_slugs.add(slugs.pop_recently_died())

        # # Collision: Slug --- Gras
        # collisions = pg.sprite.groupcollide(slugs, all_grass, False, True, collided=pg.sprite.collide_rect)
        # for coll in collisions:
        #     coll.slug.speed_factor = min(coll.slug.speed_factor*1.3, 2.5)

        # Respawn missing slugs
        n_missing_slugs = max(N_SLUGS - len(slugs), 0)
        slugs.add([SlugSprite() for _ in range(n_missing_slugs)])

        # # Respawn missing grass
        # n_missing_grass = max(N_GRAS - len(all_grass), 0)
        # all_grass.add([GrassSprite() for _ in range(n_missing_grass)])

        # Slime trail
        # for slug in slugs:
        #     if len(slug.slug.path) > 1:
        #         pg.draw.lines(surface, C.light_gray, False, slug.slug.path[-LEN_SLIME_TRAIL:], width=10)
        # for slug in dead_slugs:
        #     if len(slug.slug.path) > 1:
        #         pg.draw.lines(surface, C.gray_scale(slug.slug.dt_dead/DT_FADE_DEAD_TRAIL), False, slug.slug.path[-LEN_SLIME_TRAIL:], width=10)

        slugs.draw(surface)
        all_boulders.draw(surface)

        pg.draw.circle(surface, C.green, (player.x, player.y), 15)

        # COLLISIONS --- PLAYER vs SLUG
        all_slugs = pg.sprite.Group(slugs)
        collisions = pg.sprite.spritecollide(player, all_slugs, False, collided=pg.sprite.collide_rect)
        player.update(dt=DT, hit=bool(collisions))
        if collisions:
            pg.draw.circle(surface, C.orange, (player.x, player.y), 15)

        if pg.key.get_pressed()[pg.K_LEFT]:
            player.x = max(0, player.x - VELOCITY_PLAYER)
        elif pg.key.get_pressed()[pg.K_RIGHT]:
            player.x = min(GC.Size.X, player.x + VELOCITY_PLAYER)
        elif pg.key.get_pressed()[pg.K_UP]:
            player.y = max(GC.Size.TOP_BAR_Y, player.y - VELOCITY_PLAYER)
        elif pg.key.get_pressed()[pg.K_DOWN]:
            player.y = min(GC.Size.Y, player.y + VELOCITY_PLAYER)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

        # Top window
        pg.draw.rect(surface, C.sort_of_blue, pg.Rect(0, 0, GC.Size.X, GC.Size.TOP_BAR_Y))
        pg.draw.line(surface, C.white, (0, GC.Size.TOP_BAR_Y), (GC.Size.X, GC.Size.TOP_BAR_Y), width=2)
        txt_n_slugs = font.render(f"Lives: {player.lives} | Level {level}", False, C.white)
        surface.blit(txt_n_slugs, (5, GC.Size.TOP_BAR_Y*0.1))

        if player.lives < 1:
            running = False

        pg.display.flip()
        GC.CLOCK.tick(GC.FPS)

    # Game over
    txt_n_slugs = font.render(f"Game Over", False, C.white)
    rect = txt_n_slugs.get_rect().inflate(20, 20)
    rect.center = (GC.Size.X/2, GC.Size.Y/2)

    pg.draw.rect(surface, C.sort_of_red, rect, border_radius=10)
    pg.draw.rect(surface, C.white, rect.copy(), width=3, border_radius=10)
    txt = surface.blit(txt_n_slugs, (rect.x + 10, rect.y + 10))
    pg.display.flip()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()


if __name__ == "__main__":
    main()
