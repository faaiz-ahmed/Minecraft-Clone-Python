from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random
import os

app = Ursina()

WORLD_SIZE = 20
INVENTORY_SIZE = 9
FLAT_RADIUS = 8

def load_texture_safe(path):
    if os.path.exists(path):
        return load_texture(path)
    print(f"Warning: Texture '{path}' not found.")
    return color.white

textures = {
    'grass': load_texture_safe("asset/grass.png"),
    'dirt': load_texture_safe("asset/dirt.png"),
    'stone': load_texture_safe("asset/stone.png"),
    'brick': load_texture_safe("asset/brick.png"),
    'plank': load_texture_safe("asset/plank.png"),
    'wood': load_texture_safe("asset/wood.png"),
    'birch': load_texture_safe("asset/birch.png"),
    'stonebrick': load_texture_safe("asset/stonebrick.png"),
    'wall': load_texture_safe("asset/wall.png"),
    'sky': load_texture_safe("asset/sky.png"),
}

inventory = [
    ('grass', textures['grass']),
    ('dirt', textures['dirt']),
    ('stone', textures['stone']),
    ('brick', textures['brick']),
    ('plank', textures['plank']),
    ('wood', textures['wood']),
    ('birch', textures['birch']),
    ('stonebrick', textures['stonebrick']),
    ('wall', textures['wall']),
]

selected_block = 0
block_count = 0
game_started = False
world_blocks = {}

Entity(model='sphere', texture=textures['sky'], scale=400, double_sided=True)
DirectionalLight(color=color.white, rotation=(50, -30, 0))
AmbientLight(color=color.rgb(90, 90, 90))

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_name='grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=textures[block_name],
            color=color.white,
            highlight_color=color.rgb(210, 210, 210),
            scale=1,
        )
        self.block_name = block_name
        self._alive = True       # prevents crash when fast-clicking
        global block_count
        block_count += 1
        world_blocks[tuple(position)] = self

    def input(self, key):
        if not game_started or not self.hovered or not self._alive:
            return
        global block_count

        if key == 'left mouse down':
            self._alive = False
            world_blocks.pop(tuple(self.position), None)
            destroy(self)
            block_count -= 1
            update_block_counter()

        elif key == 'right mouse down':
            new_pos = self.position + mouse.normal
            npt     = tuple(new_pos)
            if npt not in world_blocks:
                Voxel(position=new_pos, block_name=inventory[selected_block][0])
                update_block_counter()

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera,            # attached to camera = always visible in view
            model='cube',
            texture=inventory[0][1],
            scale=(0.15, 0.15, 0.4),
            position=(0.45, -0.35, 0.6),
            rotation=(30, -15, 0),
            color=color.white,
        )

    def update_texture(self):
        self.texture = inventory[selected_block][1]

def get_height(x, z):
    dist = math.sqrt(x * x + z * z)
    if dist < FLAT_RADIUS:
        return 1
    transition = min(1.0, (dist - FLAT_RADIUS) / 10.0)
    raw = (
        3.0 * math.sin(x * 0.18) * math.cos(z * 0.18)
      + 2.0 * math.sin(x * 0.35 + z * 0.25)
      + 1.0 * math.cos(x * 0.55 - z * 0.45)
      + random.uniform(-0.4, 0.4)
    )
    hill_height = max(1, min(int(raw) + 4, 8))
    return int(1 + (hill_height - 1) * transition)

def generate_terrain():
    random.seed(42)
    for z in range(-WORLD_SIZE, WORLD_SIZE):
        for x in range(-WORLD_SIZE, WORLD_SIZE):
            height = get_height(x, z)
            for y in range(height + 1):
                if y == height:
                    bname = 'grass'
                elif y >= height - 3:
                    bname = 'dirt'
                else:
                    bname = 'stone'
                Voxel(position=(x, y, z), block_name=bname)

hud = {}

def create_hud():
    slot_width = 1.6 / INVENTORY_SIZE
    slots = []

    hud['inv_bar'] = Entity(
        parent=camera.ui, model='quad',
        color=color.rgba(0, 0, 0, 0.6),
        scale=(0.88, 0.11), position=(0, -0.42)
    )

    for i in range(INVENTORY_SIZE):
        xp = -0.8 + slot_width * i + slot_width / 2
        slots.append((
            Entity(parent=camera.ui, model='quad',
                   color=color.rgba(0.23, 0.23, 0.23, 0.8),
                   scale=(slot_width * 0.88, 0.082), position=(xp, -0.42)),
            Entity(parent=camera.ui, model='quad',
                   texture=inventory[i][1],
                   scale=(slot_width * 0.64, 0.062), position=(xp, -0.42)),
            Text(str(i + 1), parent=camera.ui,
                 position=(xp, -0.375),
                 scale=0.38, color=color.light_gray, origin=(0, 0))
        ))

    hud['inventory_slots'] = slots

    hud['selection'] = Entity(
        parent=camera.ui, model='quad',
        color=color.rgba(1, 1, 1, 0.35),
        scale=(slot_width * 0.94, 0.096),
        position=(-0.8 + slot_width / 2, -0.42)
    )

    # Crosshair — two thin lines
    hud['ch_h'] = Entity(parent=camera.ui, model='quad',
        color=color.rgba(1, 1, 1, 0.85), scale=(0.022, 0.003))
    hud['ch_v'] = Entity(parent=camera.ui, model='quad',
        color=color.rgba(1, 1, 1, 0.85), scale=(0.003, 0.022))

    # Top-left info — just text, no box backgrounds
    hud['block_counter'] = Text(
        f'Blocks: {block_count}', parent=camera.ui,
        position=(-0.85, 0.46), scale=0.55,
        color=color.white, origin=(-0.5, 0)
    )
    hud['current_block'] = Text(
        f'[ {inventory[0][0]} ]', parent=camera.ui,
        position=(-0.85, 0.40), scale=0.55,
        color=color.yellow, origin=(-0.5, 0)
    )

    # Bottom controls hint
    hud['controls'] = Text(
        'LMB Break  |  RMB Place  |  1-9 Select  |  F Fly  |  ESC Menu',
        parent=camera.ui, position=(0, -0.475),
        color=color.rgba(1, 1, 1, 0.5), scale=0.40, origin=(0, 0)
    )

def _set_hud(state):
    for k, v in hud.items():
        if k == 'inventory_slots':
            for slot in v:
                for e in slot:
                    e.enabled = state
        else:
            v.enabled = state

def update_block_counter():
    if 'block_counter' in hud:
        hud['block_counter'].text = f'Blocks: {block_count}'

def update_selection():
    slot_width = 1.6 / INVENTORY_SIZE
    hud['selection'].position = (
        -0.8 + slot_width * selected_block + slot_width / 2, -0.42
    )
    hud['current_block'].text = f'[ {inventory[selected_block][0]} ]'
    hand.update_texture()

def start_game():
    global game_started
    game_started   = True
    menu.enabled   = False
    mouse.locked   = True
    player.enabled = True
    hand.enabled   = True
    for e in terrain_entities:
        e.enabled = True
    _set_hud(True)
    update_block_counter()

def show_menu():
    global game_started
    game_started = False
    menu.enabled = True
    mouse.locked = False
    player.enabled = False
    hand.enabled = False
    _set_hud(False)

def input(key):
    global selected_block
    if key == 'escape':
        show_menu()
        return
    if not game_started:
        return
    for i in range(1, 10):
        if key == str(i) and i - 1 < INVENTORY_SIZE:
            selected_block = i - 1
            update_selection()
    if key == 'f':
        if player.gravity == 1:
            player.gravity = 0
            player.speed = 10
        else:
            player.gravity = 1
            player.speed = 5

menu = Entity(parent=camera.ui)

Entity(parent=menu, model='quad',
       color=color.rgba(0, 0, 0, 0.88), scale=(4, 3))

Entity(parent=menu, model='quad',
       color=color.rgba(0.07, 0.07, 0.07, 0.97),
       scale=(0.52, 0.72), position=(0, 0.04))

Entity(parent=menu, model='quad',
       color=color.rgba(0.25, 0.75, 0.25, 1),
       scale=(0.52, 0.012), position=(0, 0.40))

Text(parent=menu, text='MINECRAFT',
     scale=3.8, y=0.32,
     color=color.rgba(0.45, 1, 0.32, 1), origin=(0, 0))
Text(parent=menu, text='CLONE',
     scale=2.0, y=0.21,
     color=color.rgba(0.65, 1, 0.55, 0.85), origin=(0, 0))

Entity(parent=menu, model='quad',
       color=color.rgba(1, 1, 1, 0.10),
       scale=(0.40, 0.003), position=(0, 0.14))

Button(parent=menu, text='PLAY',
       scale=(0.36, 0.088), y=0.07,
       color=color.rgba(0.12, 0.52, 0.12, 1),
       highlight_color=color.rgba(0.18, 0.72, 0.18, 1),
       on_click=start_game)

Button(parent=menu, text='QUIT',
       scale=(0.36, 0.088), y=-0.07,
       color=color.rgba(0.52, 0.08, 0.08, 1),
       highlight_color=color.rgba(0.72, 0.12, 0.12, 1),
       on_click=application.quit)

Text(parent=menu,
     text='WASD Move  |  Space Jump  |  F Fly\n1-9 Select Block  |  ESC Menu',
     scale=0.46, y=-0.22,
     color=color.rgba(0.55, 0.55, 0.55, 0.85), origin=(0, 0))

print("Generating terrain...")
generate_terrain()
terrain_entities = [e for e in scene.entities if isinstance(e, Voxel)]
print(f"Generated {len(terrain_entities)} blocks")

for e in terrain_entities:
    e.enabled = False

player = FirstPersonController(
    position=(0, 4, 0),
    speed=5,
    jump_height=2.5,
    mouse_sensitivity=Vec2(40, 40),
)
player.enabled = False

hand = Hand()
hand.enabled = False

create_hud()
_set_hud(False)

menu.enabled = True
mouse.locked = False

print("Ready! Click PLAY to start.")
app.run()
