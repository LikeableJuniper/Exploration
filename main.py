import pygame as pg
import math
import random
from perlin import PerlinNoiseFactory
import ctypes
from vectors import Vector


random.seed(seed := random.randint(0, 1_000_000))
print(f"Seed: {seed}")
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

pg.init()
pg.font.init()
mainFont = pg.font.SysFont("Arial Black", 20)
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
fieldSize = [250, 250]
noiseFactory = PerlinNoiseFactory(2)
waterThreshold = -0.5
colors = [(0, 0, 175), (0, 100, 255), (0, 150, 50), (0, 100, 25), (100, 100, 100), (250, 250, 250)]
terrainSharpness = 7.5


class Cell:
    def __init__(self, x, y, cellType, color, image=None, building=None, unit=None):
        self.pos = x, y
        self.cellType = cellType
        self.color = color
        self.image = image
        self.building = building
        self.unit = unit
    
    def __repr__(self):
        return f"Cell with building {self.image}"
    
    def render(self, rect, zoom, screen):
        if (0 <= rect[0] <= screensize[0] and 0 <= rect[1] <= screensize[1]) or (0 <= rect[0]+rect[2] <= screensize[0] and 0 <= rect[1]+rect[3] <= screensize[1]) or (0 <= rect[0]+rect[2] <= screensize[0] and 0 <= rect[1] <= screensize[1] or (0 <= rect[0] <= screensize[0] and 0 <= rect[1]+rect[3] <= screensize[1])):
            pg.draw.rect(screen, self.color, rect)
            if self.image:
                pg.draw.rect(screen, (255, 0, 0), rect)
            if zoom >= renderZoom:
                pg.draw.rect(screen, (0, 0, 0), rect, 1) # Only drawing outlines when zoomed close makes game appear prettier when zoomed out
                if self.image:
                    screen.blit(pg.transform.scale(self.image, rect[2:4]), rect[0:2])


def generateTerrain(size) -> list[list[Cell]]:
    field = [[None for _ in range(size[1])] for _ in range(size[0])]
    noiseSize = size[0]/terrainSharpness, size[1]/terrainSharpness
    negativeDeepWater = (1-waterThreshold)/5
    maxPositive = (1+waterThreshold)
    for x in range(size[0]):
        for y in range(size[1]):
            noise = noiseFactory(x/noiseSize[0], y/noiseSize[1])+waterThreshold
            if noise < -negativeDeepWater:
                color = colors[0]
            elif noise < 0:
                color = colors[1]
            elif noise < maxPositive/4:
                color = colors[2]
            elif noise < maxPositive/2:
                color = colors[3]
            elif noise < 3 * maxPositive/4:
                color = colors[4]
            else:
                color = colors[5]
            field[x][y] = Cell(x, y, colors.index(color), color)
    return field


def distance(pos1, pos2):
    return math.sqrt(sum([(pos2[i]-pos1[i])**2 for i in range(len(pos1))]))


def pickRandomPos(field: list[list[Cell]], allowWater=False, allowBuilding=False, allowUnit=False):
    size = len(field)-1, len(field[0])-1
    while True:
        val = field[(x := random.randint(0, size[0]))][(y := random.randint(0, size[1]))]
        if not allowWater and val.cellType < 2:
            continue
        if not allowBuilding and val.building:
            continue
        if not allowUnit and val.unit:
            continue
        break
    return x, y



images = {
    "capital": pg.image.load("Images/capital.png").convert_alpha(),
    "city": pg.image.load("Images/city.png").convert_alpha()
    }

field = generateTerrain(fieldSize)
cellSize = 75
scrollSpeed = cellSize
zoomSpeed = 1.125
offset = Vector(0, 0)
zoom = 1
renderZoom = 1/zoomSpeed**10
spawnX, spawnY = pickRandomPos(field)

field[spawnX][spawnY].building = "capital"
field[spawnX][spawnY].image = images["capital"]
print(spawnX, spawnY)

playing = True

while playing:
    screen.fill((50, 50, 50))

    currentSize = zoom * cellSize

    # Additional ySub and xSub variables to counter incorrect cell display as good as possible (still not perfect)
    ySub = 0
    for y, row in enumerate(field):
        xSub = 0
        ySub += (yVal := offset[1]+y*currentSize) - math.floor(yVal)
        for x, elem in enumerate(row):
            xSub += (xVal := offset[0] + x*currentSize) - math.floor(xVal)
            rect = [xVal - xSub, yVal - ySub] + [currentSize]*2
            elem.render(rect, zoom, screen)
    
    screen.blit(mainFont.render(f"Zoom: {round(zoom, 2)}", False, (255, 100, 0)), [10, 10])
    
    pg.display.update()

    for event in pg.event.get():

        if event.type == pg.MOUSEWHEEL:
            mousePos = Vector(pg.mouse.get_pos())
            if event.y < 0:
                zoom /= zoomSpeed
                offset = mousePos + ((offset-mousePos) / zoomSpeed)
            elif event.y > 0:
                zoom *= zoomSpeed
                offset = mousePos + ((offset-mousePos) * zoomSpeed)
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                offset[0] += scrollSpeed
            if event.key == pg.K_RIGHT:
                offset[0] -= scrollSpeed
            if event.key == pg.K_UP:
                offset[1] += scrollSpeed
            if event.key == pg.K_DOWN:
                offset[1] -= scrollSpeed
        
        if pg.mouse.get_pressed()[0]: # Purposefully not using "event.type == pg.MOUSEBUTTONDOWN" because that also detecs scroll wheel as click
            if zoom >= renderZoom:
                x, y = int((-offset[0]+event.pos[0]) // currentSize), int((-offset[1]+event.pos[1]) // currentSize)
                print(field[x][y])

        
        if event.type == pg.QUIT:
            pg.quit()
            playing = False
            break
