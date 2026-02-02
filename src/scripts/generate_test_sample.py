import os
from PIL import Image, ImageDraw
import random

# Constants
SCALE_RATIO = 4000  # 1:4000 (Updated from 5533)
DPI = 600           # High resolution for small details
CM_TO_INCH = 1 / 2.54
SAMPLE_W_CM = 8     # 8cm Width
SAMPLE_H_CM = 2     # 2cm Height

# Calculate pixel dimensions
IMG_W = int(SAMPLE_W_CM * CM_TO_INCH * DPI)
IMG_H = int(SAMPLE_H_CM * CM_TO_INCH * DPI)
PIXELS_PER_METER = (100 / SCALE_RATIO) * CM_TO_INCH * DPI

print(f"Image Size: {IMG_W}x{IMG_H} px")
print(f"Pixels per Real Meter: {PIXELS_PER_METER:.2f} px/m")

# Street Widths (Meters)
WIDTH_MAIN_ST = 10
WIDTH_SEC_ST = 5
WIDTH_ALLEY = 2.5

# Houses (Meters)
RICH_HOUSE_SIZE = 15 # Base size 15m x 15m
POOR_HOUSE_W = 5 
POOR_HOUSE_H = 6

# Colors (Grayscale 0-255)
# Mode: ORIGINAL (3-Level)
LEVEL_GROUND_ORIG = 50
LEVEL_STREET_ORIG = 20
LEVEL_BUILDING_ORIG = 255

# Mode: BLOCK (2-Level: Surface vs Street)
LEVEL_SURFACE_BLOCK = 255
LEVEL_STREET_BLOCK = 0

def draw_wobbly_rect(draw, x1, y1, x2, y2, color, wobble=1):
    """Draws a rectangle with slightly perturbed corners."""
    p1 = (x1 + random.randint(-wobble, wobble), y1 + random.randint(-wobble, wobble))
    p2 = (x2 + random.randint(-wobble, wobble), y1 + random.randint(-wobble, wobble))
    p3 = (x2 + random.randint(-wobble, wobble), y2 + random.randint(-wobble, wobble))
    p4 = (x1 + random.randint(-wobble, wobble), y2 + random.randint(-wobble, wobble))
    draw.polygon([p1, p2, p3, p4], fill=color)

# --- RICH HOUSING ---

def draw_u_shape(draw, x, y, size, color, ground_color):
    """Draws U-shaped house with Random Rotation"""
    draw_wobbly_rect(draw, x, y, x+size, y+size, color)
    
    wall = int(size * 0.25)
    rotation = random.choice([0, 1, 2, 3]) # 0=TopOpen, 1=RightOpen, 2=BotOpen, 3=LeftOpen
    
    if rotation == 0:   # Top Open
        draw_wobbly_rect(draw, x+wall, y, x+size-wall, y+size-wall, ground_color, wobble=0)
    elif rotation == 1: # Right Open
        draw_wobbly_rect(draw, x+wall, y+wall, x+size, y+size-wall, ground_color, wobble=0)
    elif rotation == 2: # Bottom Open
        draw_wobbly_rect(draw, x+wall, y+wall, x+size-wall, y+size, ground_color, wobble=0)
    elif rotation == 3: # Left Open
        draw_wobbly_rect(draw, x, y+wall, x+size-wall, y+size-wall, ground_color, wobble=0)

def draw_l_shape(draw, x, y, size, color, ground_color):
    """Draws L-shaped house with Random Rotation"""
    draw_wobbly_rect(draw, x, y, x+size, y+size, color)
    
    wall = int(size * 0.35)
    rotation = random.choice([0, 1, 2, 3]) # Corner cutouts
    
    # We "cut out" one quadrant to make an L
    if rotation == 0:   # Top Right Cut
        draw_wobbly_rect(draw, x+wall, y, x+size, y+size-wall, ground_color, wobble=0)
    elif rotation == 1: # Bottom Right Cut
        draw_wobbly_rect(draw, x+wall, y+wall, x+size, y+size, ground_color, wobble=0)
    elif rotation == 2: # Bottom Left Cut
        draw_wobbly_rect(draw, x, y+wall, x+size-wall, y+size, ground_color, wobble=0)
    elif rotation == 3: # Top Left Cut
        draw_wobbly_rect(draw, x, y, x+size-wall, y+size-wall, ground_color, wobble=0)

def draw_8_shape(draw, x, y, size, color, ground_color):
    """Draws 8-shaped house (Two courtyards)"""
    draw_wobbly_rect(draw, x, y, x+size, y+size, color)
    hole_w = int(size * 0.35)
    hole_h = int(size * 0.20)
    # Vertical orientation of holes
    draw_wobbly_rect(draw, x + (size-hole_w)//2, y + size//5, x + (size-hole_w)//2 + hole_w, y + size//5 + hole_h, ground_color, wobble=0)
    draw_wobbly_rect(draw, x + (size-hole_w)//2, y + int(size*0.6), x + (size-hole_w)//2 + hole_w, y + int(size*0.6) + hole_h, ground_color, wobble=0)

def draw_square_shape(draw, x, y, size, color, ground_color):
    """Draws O-shaped house (Thicker walls)"""
    draw_wobbly_rect(draw, x, y, x+size, y+size, color)
    # Wall is thicker (30-40%)
    wall = random.randint(int(size*0.30), int(size*0.40))
    draw_wobbly_rect(draw, x+wall, y+wall, x+size-wall, y+size-wall, ground_color, wobble=0)

def draw_z_shape(draw, x, y, size, color, ground_color):
    """Draws Z-shaped house"""
    # Simply draw horizontal bars? Or filled rect with side geometric cutouts?
    # Strategy: Draw full rect, cut out Top-Left and Bottom-Right quadrants (but partial)
    draw_wobbly_rect(draw, x, y, x+size, y+size, color)
    
    cut_size = int(size * 0.4)
    # Cut Top Left
    draw_wobbly_rect(draw, x, y, x+cut_size, y+cut_size, ground_color, wobble=0)
    # Cut Bottom Right
    draw_wobbly_rect(draw, x+size-cut_size, y+size-cut_size, x+size, y+size, ground_color, wobble=0)
    # Optional: Randomly flip to S-shape
    if random.choice([True, False]):
        # Restore what we cut and cut the other corners? 
        # Easier to just re-draw S-shape if needed, but Z is fine for variety.
        pass

# --- LAYOUT ---

def get_layout():
    """Calculates street and block positions."""
    main_w_px = int(WIDTH_MAIN_ST * PIXELS_PER_METER)
    sec_w_px = int(WIDTH_SEC_ST * PIXELS_PER_METER)
    alley_w_px = int(WIDTH_ALLEY * PIXELS_PER_METER)
    
    main_x = IMG_W // 2
    # Adjust secondary streets for new height (2cm total)
    sec_y1 = IMG_H // 3
    sec_y2 = (IMG_H // 3) * 2
    
    # Streets
    streets_rects = [
        (main_x - main_w_px//2, 0, main_x + main_w_px//2, IMG_H),
        (0, sec_y1 - sec_w_px//2, IMG_W, sec_y1 + sec_w_px//2),
        (0, sec_y2 - sec_w_px//2, IMG_W, sec_y2 + sec_w_px//2)
    ]
    
    # Alleys (More density)
    # Add vertical alleys in each column
    c1_center = main_x // 2
    c2_center = main_x + (IMG_W - main_x) // 2
    streets_rects.append((c1_center - alley_w_px//2, 0, c1_center + alley_w_px//2, IMG_H))
    streets_rects.append((c2_center - alley_w_px//2, 0, c2_center + alley_w_px//2, IMG_H))

    blocks = []
    
    # Barriers
    barriers_x = sorted([0, c1_center - alley_w_px//2, c1_center + alley_w_px//2, 
                         main_x - main_w_px//2, main_x + main_w_px//2, 
                         c2_center - alley_w_px//2, c2_center + alley_w_px//2,
                         IMG_W])
    barriers_y = sorted([0, sec_y1 - sec_w_px//2, sec_y1 + sec_w_px//2, 
                         sec_y2 - sec_w_px//2, sec_y2 + sec_w_px//2, IMG_H])
    
    for i in range(len(barriers_x) - 1):
        for j in range(len(barriers_y) - 1):
            x1, x2 = barriers_x[i], barriers_x[i+1]
            y1, y2 = barriers_y[j], barriers_y[j+1]
            if (x2 - x1) < alley_w_px or (y2 - y1) < alley_w_px:
                continue 
            blocks.append((x1, y1, x2, y2))
            
    return main_x, streets_rects, blocks

def draw_raster_sample(filename, mode="ORIGINAL"):
    if mode == "BLOCK":
        bg_color = LEVEL_SURFACE_BLOCK
        street_color = LEVEL_STREET_BLOCK
        building_color = LEVEL_SURFACE_BLOCK
        ground_fill = LEVEL_SURFACE_BLOCK 
    else:
        bg_color = LEVEL_GROUND_ORIG
        street_color = LEVEL_STREET_ORIG
        building_color = LEVEL_BUILDING_ORIG
        ground_fill = LEVEL_GROUND_ORIG 

    img = Image.new('L', (IMG_W, IMG_H), bg_color)
    draw = ImageDraw.Draw(img)
    
    main_x, streets_rects, blocks = get_layout()

    # Draw Streets
    for r in streets_rects:
        draw.rectangle(r, fill=street_color)

    if mode == "ORIGINAL":
        rich_shapes = [draw_u_shape, draw_l_shape, draw_8_shape, draw_square_shape, draw_z_shape]
        
        for (bx1, by1, bx2, by2) in blocks:
            # Right side = Rich
            is_rich = (bx1 > main_x)
            
            if is_rich:
                house_size = int(RICH_HOUSE_SIZE * PIXELS_PER_METER)
                gap = int(2 * PIXELS_PER_METER)
                
                for y in range(by1 + gap, by2 - house_size, house_size + gap):
                    for x in range(bx1 + gap, bx2 - house_size, house_size + gap):
                        shape_func = random.choice(rich_shapes) # Random shape logic
                        shape_func(draw, x, y, house_size, building_color, ground_fill)
                        
            else:
                # Poor houses
                house_w = int(POOR_HOUSE_W * PIXELS_PER_METER)
                house_h = int(POOR_HOUSE_H * PIXELS_PER_METER)
                gap = int(1 * PIXELS_PER_METER) + 1
                
                current_y = by1 + gap
                while current_y < by2 - house_h:
                    current_x = bx1 + gap
                    while current_x < bx2 - house_w:
                        
                        # LOGIC: Skipping (20% chance)
                        if random.random() < 0.2:
                            current_x += house_w + gap
                            continue
                            
                        # LOGIC: Coalescing (Merging) (30% chance)
                        # Check if we have space to draw a double-wide
                        is_merged = False
                        if random.random() < 0.3 and (current_x + (house_w*2) + gap < bx2):
                            w_actual = (house_w * 2) + gap + random.randint(-1, 2)
                            h_actual = house_h + random.randint(-1, 2)
                            is_merged = True
                        else:
                            w_actual = house_w + random.randint(-1, 2)
                            h_actual = house_h + random.randint(-1, 2)
                        
                        if current_x + w_actual < bx2 and current_y + h_actual < by2:
                            draw_wobbly_rect(draw, current_x, current_y, current_x + w_actual, current_y + h_actual, building_color, wobble=1)
                        
                        current_x += w_actual + gap
                    current_y += house_h + gap

    img.save(filename)
    print(f"Saved {mode} sample to {filename}")

def generate_svg_sample(filename):
    main_x, streets_rects, blocks = get_layout()
    w_mm = SAMPLE_W_CM * 10
    h_mm = SAMPLE_H_CM * 10
    svg_content = [
        f'<svg width="{w_mm}mm" height="{h_mm}mm" viewBox="0 0 {IMG_W} {IMG_H}" xmlns="http://www.w3.org/2000/svg">',
        '<!-- Streets (Black Fill) -->',
        '<g id="streets" fill="black" stroke="none">'
    ]
    for (x1, y1, x2, y2) in streets_rects:
         svg_content.append(f'  <rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" />')
    svg_content.append('</g>')
    svg_content.append('</svg>')
    with open(filename, 'w') as f:
        f.write('\n'.join(svg_content))
    print(f"Saved SVG sample to {filename}")

if __name__ == "__main__":
    os.makedirs("outputs/samples", exist_ok=True)
    draw_raster_sample("outputs/samples/mohenjo_test_sample.png", mode="ORIGINAL")
    draw_raster_sample("outputs/samples/mohenjo_test_sample_block.png", mode="BLOCK")
    generate_svg_sample("outputs/samples/mohenjo_test_sample.svg")
