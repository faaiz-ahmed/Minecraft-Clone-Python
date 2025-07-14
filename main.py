from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random
import os

app = Ursina()

WORLD_SIZE = 20
INVENTORY_SIZE = 9
CHUNK_SIZE = 8

# Load textures safely with warning
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
    'sky': load_texture_safe("asset/sky.png")
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
    ('wall', textures['wall'])
]

selected_block = 0
block_count = 0
game_started = False
world_blocks = {}  # Store block positions for better management

# Improved lighting
sky = Entity(model='sphere', texture=textures['sky'], scale=300, double_sided=True)
sun = DirectionalLight(color=color.white, rotation=(45, -45, 45))
ambient_light = AmbientLight(color=color.gray)

# Voxel block class with optimizations
class Voxel(Button):
    def __init__(self, position=(0,0,0), texture=textures['grass']):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=color.white,
            highlight_color=color.light_gray,
            scale=1
        )
        global block_count
        block_count += 1
        world_blocks[tuple(position)] = self

    def input(self, key):
        if not game_started:
            return
        
        global block_count
        if self.hovered:
            if key == 'left mouse down':
                pos = tuple(self.position)
                if pos in world_blocks:
                    del world_blocks[pos]
                destroy(self)
                block_count -= 1
                update_block_counter()
                
            elif key == 'right mouse down':
                new_pos = self.position + mouse.normal
                new_pos_tuple = tuple(new_pos)
                
                # Check if position is already occupied
                if new_pos_tuple not in world_blocks:
                    Voxel(position=new_pos, texture=inventory[selected_block][1])
                    update_block_counter()

# Player hand model with better positioning
class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera,
            model='cube',
            texture=inventory[selected_block][1],
            scale=(0.15, 0.25, 0.6),
            position=(0.5, -0.5, 0.7),
            color=color.white,
            rotation=(10, -10, 0)
        )
        
    def update_texture(self):
        self.texture = inventory[selected_block][1]

# Improved terrain generation with noise
def generate_terrain():
    random.seed(42)  # Consistent world generation
    
    for z in range(-WORLD_SIZE, WORLD_SIZE):
        for x in range(-WORLD_SIZE, WORLD_SIZE):
            # More natural height generation
            height = int(3 * math.sin(x * 0.2) + 2 * math.cos(z * 0.25) + 
                        1.5 * math.sin(x * 0.1 + z * 0.1) + 
                        random.uniform(-0.5, 0.5))
            height = max(0, min(height, 6))
            
            # Generate layers
            for y in range(height + 1):
                if y == height and height > 0:
                    # Grass on top
                    block_type = textures['grass']
                elif y >= height - 2 and height > 2:
                    # Dirt layer
                    block_type = textures['dirt']
                else:
                    # Stone base
                    block_type = textures['stone']
                
                Voxel(position=(x, y, z), texture=block_type)

# Enhanced inventory UI
def create_inventory_ui():
    slot_width = 1.6 / INVENTORY_SIZE
    slots = []
    
    for i in range(INVENTORY_SIZE):
        x_pos = -0.8 + slot_width * i + slot_width / 2
        
        # Slot background with border
        slot_bg = Entity(
            parent=camera.ui, 
            model='quad', 
            color=color.rgb(60, 60, 60), 
            scale=(slot_width * 0.9, 0.08), 
            position=(x_pos, -0.42)
        )
        
        # Item preview
        block_preview = Entity(
            parent=camera.ui, 
            model='quad', 
            texture=inventory[i][1], 
            scale=(slot_width * 0.65, 0.06), 
            position=(x_pos, -0.42)
        )
        
        # Slot number
        slot_number = Text(
            str(i + 1), 
            parent=camera.ui, 
            position=(x_pos, -0.37), 
            scale=0.4, 
            color=color.white,
            origin=(0, 0)
        )
        
        slots.append((slot_bg, block_preview, slot_number))
    
    # Selection indicator
    selection = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.rgba(255, 255, 255, 0.4),
        scale=(slot_width * 0.95, 0.09), 
        position=(-0.8 + slot_width * selected_block + slot_width/2, -0.42)
    )
    
    return slots, selection

# Enhanced HUD
def create_hud():
    # Crosshair with better visibility
    crosshair = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.white, 
        scale=0.01,
        position=(0, 0, -0.1)
    )
    
    # Block counter with background
    counter_bg = Entity(
        parent=camera.ui,
        model='quad',
        color=color.rgba(0, 0, 0, 0.5),
        scale=(0.25, 0.06),
        position=(-0.75, 0.44)
    )
    
    block_counter = Text(
        f'Blocks: {block_count}', 
        position=(-0.75, 0.44), 
        color=color.white, 
        scale=0.6,
        origin=(0, 0)
    )
    
    # Current block display
    current_bg = Entity(
        parent=camera.ui,
        model='quad',
        color=color.rgba(0, 0, 0, 0.5),
        scale=(0.3, 0.06),
        position=(-0.75, -0.48)
    )
    
    current_block = Text(
        f'Block: {inventory[selected_block][0]}', 
        position=(-0.75, -0.48), 
        color=color.white, 
        scale=0.6,
        origin=(0, 0)
    )
    
    # Controls help
    controls = Text(
        'Left Click: Break | Right Click: Place | 1-9: Select | F: Fly | ESC: Menu',
        position=(0, 0.47), 
        color=color.white, 
        scale=0.45,
        origin=(0, 0)
    )
    
    # Inventory bar background
    inventory_bar = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.rgba(0, 0, 0, 0.6), 
        scale=(0.85, 0.11), 
        position=(0, -0.42)
    )
    
    inventory_slots, selection_indicator = create_inventory_ui()
    
    return {
        'crosshair': crosshair,
        'counter_bg': counter_bg,
        'block_counter': block_counter,
        'current_bg': current_bg,
        'current_block': current_block,
        'controls': controls,
        'inventory_bar': inventory_bar,
        'inventory_slots': inventory_slots,
        'selection_indicator': selection_indicator
    }

def update_block_counter():
    hud['block_counter'].text = f'Blocks: {block_count}'

def update_selection():
    slot_width = 1.6 / INVENTORY_SIZE
    hud['selection_indicator'].position = (-0.8 + slot_width * selected_block + slot_width / 2, -0.42)
    hud['current_block'].text = f'Block: {inventory[selected_block][0]}'
    hand.update_texture()

def show_menu():
    global game_started
    game_started = False
    menu.enabled = True
    mouse.locked = False
    
    # Disable game elements
    player.enabled = False
    hand.enabled = False
    
    for key in hud:
        if key == 'inventory_slots':
            for slot_elements in hud[key]:
                for element in slot_elements:
                    element.enabled = False
        else:
            hud[key].enabled = False

# Enhanced input handler
def input(key):
    global selected_block
    
    if key == 'escape':
        show_menu()
        return
    
    if not game_started:
        return

    # Number keys for inventory selection
    for i in range(1, 10):
        if key == str(i) and i-1 < INVENTORY_SIZE:
            selected_block = i - 1
            update_selection()

    # Flight toggle
    if key == 'f':
        if player.gravity == 1:
            player.gravity = 0
            player.speed = 8
        else:
            player.gravity = 1
            player.speed = 5

# Main menu functions
def start_game():
    global game_started
    game_started = True
    menu.enabled = False
    mouse.locked = True
    
    # Enable game elements
    player.enabled = True
    hand.enabled = True
    
    for e in terrain_entities:
        e.enabled = True
    
    for key in hud:
        if key == 'inventory_slots':
            for slot_elements in hud[key]:
                for element in slot_elements:
                    element.enabled = True
        else:
            hud[key].enabled = True

def quit_game():
    application.quit()

# Create improved main menu
menu = Entity(parent=camera.ui)
menu_bg = Entity(parent=menu, model='quad', color=color.rgba(0, 0, 0, 0.8), scale=(4, 3))

title = Text(
    parent=menu, 
    text='Minecraft Alpha Clone', 
    scale=2.5, 
    y=0.7,
    color=color.white
)

subtitle = Text(
    parent=menu,
    text='Enhanced Edition',
    scale=1,
    y=0.5,
    color=color.light_gray
)

play_btn = Button(
    parent=menu, 
    text='Play', 
    scale=(0.4, 0.12), 
    y=0.1, 
    color=color.azure,
    highlight_color=color.light_gray,
    on_click=start_game
)

quit_btn = Button(
    parent=menu, 
    text='Quit', 
    scale=(0.4, 0.12), 
    y=-0.1, 
    color=color.red,
    highlight_color=color.light_gray,
    on_click=quit_game
)

# Generate terrain but keep it disabled initially
print("Generating terrain...")
generate_terrain()
terrain_entities = [e for e in scene.entities if isinstance(e, Voxel)]
print(f"Generated {len(terrain_entities)} blocks")

# Disable terrain initially
for e in terrain_entities:
    e.enabled = False

# Create player and disable until game starts
player = FirstPersonController(
    position=(0, 8, 0), 
    speed=5, 
    jump_height=2.5, 
    mouse_sensitivity=Vec2(40, 40)
)
player.enabled = False

hand = Hand()
hand.enabled = False

hud = create_hud()

# Disable all HUD elements initially
for key in hud:
    if key == 'inventory_slots':
        for slot_elements in hud[key]:
            for element in slot_elements:
                element.enabled = False
    else:
        hud[key].enabled = False

# Make sure menu is enabled and mouse is not locked
menu.enabled = True
mouse.locked = False

print("Game ready! Click Play to start.")

app.run()