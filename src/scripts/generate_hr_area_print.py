import os
import sys
import random
from PIL import Image, ImageDraw

# Add project root to path to import mohenjo package
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "src"))

from mohenjo.registry import LandmarkRegistry
from mohenjo.generators import generate_rich_zone, generate_poor_zone

# Constants
SCALE_RATIO = 4000
DPI = 600
CM_TO_INCH = 1 / 2.54

# Laser Grayscale Values
LEVEL_GROUND = 50       # Low burn (Gray)
LEVEL_STREET = 20       # Medium burn (Dark Gray)
LEVEL_BUILDING = 255    # No burn (White) - Highest point

# Housing Constants
RICH_HOUSE_SIZE_M = 15
POOR_HOUSE_W_M = 5
POOR_HOUSE_H_M = 6
RICH_GAP_M = 2  # Generous gap
POOR_GAP_M = 1  # Tight gap

def meters_to_pixels(meters):
    return int(meters * (100 / SCALE_RATIO) * CM_TO_INCH * DPI)

def draw_wobbly_rect(draw, x1, y1, x2, y2, color, wobble=1):
    """Draws a rectangle with slightly perturbed corners."""
    p1 = (x1 + random.randint(-wobble, wobble), y1 + random.randint(-wobble, wobble))
    p2 = (x2 + random.randint(-wobble, wobble), y1 + random.randint(-wobble, wobble))
    p3 = (x2 + random.randint(-wobble, wobble), y2 + random.randint(-wobble, wobble))
    p4 = (x1 + random.randint(-wobble, wobble), y2 + random.randint(-wobble, wobble))
    draw.polygon([p1, p2, p3, p4], fill=color)

# --- RICH HOUSING GENERATORS ---
def gen_rich_house(draw, x, y, size_px, color, ground_color):
    draw_wobbly_rect(draw, x, y, x+size_px, y+size_px, color)
    wall = int(size_px * 0.25)
    rotation = random.choice([0, 1, 2, 3]) 
    # Courtyard logic (U-shape)
    if rotation == 0:   # Top Open
        draw_wobbly_rect(draw, x+wall, y, x+size_px-wall, y+size_px-wall, ground_color, wobble=0)
    elif rotation == 1: # Right Open
        draw_wobbly_rect(draw, x+wall, y+wall, x+size_px, y+size_px-wall, ground_color, wobble=0)
    elif rotation == 2: # Bottom Open
        draw_wobbly_rect(draw, x+wall, y+wall, x+size_px-wall, y+size_px, ground_color, wobble=0)
    elif rotation == 3: # Left Open
        draw_wobbly_rect(draw, x, y+wall, x+size_px-wall, y+size_px-wall, ground_color, wobble=0)

# --- POOR HOUSING GENERATORS ---
def gen_poor_block(draw, x1, y1, x2, y2, house_w_px, house_h_px, gap_px, color):
    # Denser packing
    current_y = y1
    while current_y < y2 - house_h_px:
        current_x = x1
        while current_x < x2 - house_w_px:
            
            # Logic: Skipping (20%)
            if random.random() < 0.2:
                current_x += house_w_px + gap_px
                continue
                
            # Logic: Coalescing (Merging) (30%)
            w_actual = house_w_px
            h_actual = house_h_px
            if random.random() < 0.3 and (current_x + (house_w_px*2) + gap_px < x2):
                w_actual = (house_w_px * 2) + gap_px + random.randint(-1, 2)
                h_actual = house_h_px + random.randint(-1, 2)
            else:
                 w_actual += random.randint(-1, 2) # Slight variation
                 h_actual += random.randint(-1, 2)

            # Draw
            if current_x + w_actual < x2 and current_y + h_actual < y2:
                 draw_wobbly_rect(draw, current_x, current_y, current_x + w_actual, current_y + h_actual, color, wobble=1)
            
            current_x += w_actual + gap_px
        current_y += house_h_px + gap_px

def generate_hr_area_print():
    base_dir = os.path.join(os.path.dirname(__file__), "../..")
    landmarks_path = os.path.join(base_dir, "src/data/landmarks.yaml")
    procedural_path = os.path.join(base_dir, "src/data/procedural.yaml")
    output_dir = os.path.join(base_dir, "outputs/samples")
    
    registry = LandmarkRegistry(landmarks_path, procedural_path)
    
    hr_area_id = "lower_hr_area"
    hr_area = registry.landmarks.get(hr_area_id)
    if not hr_area:
        print(f"Error: {hr_area_id} not found.")
        return

    # Canvas
    model_w_m = hr_area.dimensions.width
    model_l_m = hr_area.dimensions.length
    padding_m = 10
    total_w_m = model_w_m + (padding_m * 2)
    total_l_m = model_l_m + (padding_m * 2)
    
    img_w = meters_to_pixels(total_w_m)
    img_h = meters_to_pixels(total_l_m)
    
    img = Image.new('L', (img_w, img_h), LEVEL_GROUND)
    draw = ImageDraw.Draw(img)
    
    center_x_px = img_w // 2
    center_y_px = img_h // 2
    
    hr_center_global_x = hr_area.abs_x
    hr_center_global_y = hr_area.abs_y
    
    def world_to_img(x, y):
        rel_x = x - hr_center_global_x
        rel_y = y - hr_center_global_y
        px = center_x_px + meters_to_pixels(rel_x)
        py = center_y_px - meters_to_pixels(rel_y)
        return int(px), int(py)

    def draw_rect(draw_obj, w_m, h_m, x_m, y_m, color):
        w_px = meters_to_pixels(w_m)
        h_px = meters_to_pixels(h_m) 
        cx, cy = world_to_img(x_m, y_m)
        x1 = cx - (w_px // 2)
        y1 = cy - (h_px // 2)
        x2 = x1 + w_px
        y2 = y1 + h_px
        draw_obj.rectangle([x1, y1, x2, y2], fill=color)

    # 1. Procedural Zones Generation
    print("Generating Procedural Housing...")
    
    # Identify Zones
    zones = [lm for lm in registry.landmarks.values() if lm.region == "Lower City" and "zone" in lm.shape.lower()]
    
    rich_h_size_px = meters_to_pixels(RICH_HOUSE_SIZE_M)
    poor_h_w_px = meters_to_pixels(POOR_HOUSE_W_M)
    poor_h_h_px = meters_to_pixels(POOR_HOUSE_H_M)
    rich_gap_px = meters_to_pixels(RICH_GAP_M)
    poor_gap_px = meters_to_pixels(POOR_GAP_M)

    from mohenjo.generators import generate_rich_zone, generate_poor_zone

    # [Collision Detection Preparation]
    # Identify Obstacles (Streets, specific landmarks)
    obstacles = []
    print("Identifying Obstacles for Collision Detection...")
    for lm in registry.landmarks.values():
        # Heuristic: Streets/Lanes are obstacles. Existing explicit houses are obstacles.
        if "street" in lm.id or "lane" in lm.id or "house" in lm.id:
            if "zone" in lm.id: continue # Zones are not obstacles to themselves
            
            # Simple Bounding Box Collision
            # Calculate Global Bounds in METERS
            w = lm.dimensions.width
            l = lm.dimensions.length
            min_x = lm.abs_x - w/2
            max_x = lm.abs_x + w/2
            min_y = lm.abs_y - l/2
            max_y = lm.abs_y + l/2
            obstacles.append((min_x, max_x, min_y, max_y, lm.id))
            print(f"  - Obstacle: {lm.id} [{min_x}, {max_x}, {min_y}, {max_y}]")

    def check_collision(poly_points_global, obstacles):
        # Naive: Check if any point is inside an obstacle? 
        # Better: Check bounding box overlap first.
        # Poly points: [(x,y), ...]
        p_xs = [p[0] for p in poly_points_global]
        p_ys = [p[1] for p in poly_points_global]
        p_min_x, p_max_x = min(p_xs), max(p_xs)
        p_min_y, p_max_y = min(p_ys), max(p_ys)
        
        for (o_min_x, o_max_x, o_min_y, o_max_y, oid) in obstacles:
            # Check rect overlap
            if (p_min_x < o_max_x and p_max_x > o_min_x and
                p_min_y < o_max_y and p_max_y > o_min_y):
                return True
        return False

    for zone in zones:
        print(f"  - Processing Zone: {zone.name} ({zone.id})")
        print(f"    - Dimensions: {zone.dimensions.width}m x {zone.dimensions.length}m")
        print(f"    - Absolute Loc: ({zone.abs_x}, {zone.abs_y})")
        
        # Get Pixel Bounds of the zone
        w_px = meters_to_pixels(zone.dimensions.width)
        l_px = meters_to_pixels(zone.dimensions.length)
        cx, cy = world_to_img(zone.abs_x, zone.abs_y)
        
        # Zone Bounds (Top Left)
        z_x1 = cx - w_px//2
        z_y1 = cy - l_px//2
        # z_x2, z_y2 not strictly needed for generator call, but useful context
        
        print(f"    - Canvas Top-Left: ({z_x1}, {z_y1})")

        # Generator returns houses in LOCAL coordinates (0 to width/length in meters)
        # We need to transform them to IMAGE coordinates:
        # Image X = z_x1 + meters_to_pixels(local_x)
        # Image Y = z_y1 + meters_to_pixels(local_y)
        
        houses = []
        if "rich" in zone.id:
            houses = generate_rich_zone(zone.dimensions.width, zone.dimensions.length)
        elif "poor" in zone.id:
            houses = generate_poor_zone(zone.dimensions.width, zone.dimensions.length)
            
        print(f"    - Generating {len(houses)} shapes (pre-collision)...")
        
        valid_houses = []
        for h in houses:
            # Transform points to GLOBAL meters to check collision
            # Zone Top-Left (global)
            # zone.abs_x is center. width is w. Top-left X = center - w/2.
            # Local X grows RIGHT. Global X grows RIGHT.
            # Local Y grows DOWN. Global Y grows UP. ((Wait, standard cartesian))
            
            # Re-verify Generators Coordinate System
            # Generators: y in range(0, length). 0 is "Top".
            # Global: Y grows UP. 
            # So Local Y=0 corresponds to Global Y_Max (Top edge of zone).
            # Global Y = (Zone_Center_Y + Length/2) - Local_Y
            
            zone_tl_x_global = zone.abs_x - zone.dimensions.width / 2
            zone_tl_y_global = zone.abs_y + zone.dimensions.length / 2 
            
            global_points = []
            for (lx, ly) in h.points:
                gx = zone_tl_x_global + lx
                gy = zone_tl_y_global - ly
                global_points.append((gx, gy))
            
            if not check_collision(global_points, obstacles):
                valid_houses.append((h, global_points))
        
        print(f"    - Valid shapes after collision check: {len(valid_houses)}")

        for (h, global_points) in valid_houses:
            # Transform global points to Canvas Pixels
            pixel_points = []
            for (gx, gy) in global_points:
                # world_to_img takes global coordinates
                px, py = world_to_img(gx, gy)
                pixel_points.append((px, py))
            
            # Determine color
            if h.category == "COURTYARD":
                color = LEVEL_GROUND
            else:
                color = LEVEL_BUILDING
                
            draw.polygon(pixel_points, fill=color)


    # 2. explicit Landmarks (Overlay on top)
    print("Drawing Explicit Landmarks...")
    half_w = model_w_m / 2
    half_l = model_l_m / 2
    min_x = hr_center_global_x - half_w
    max_x = hr_center_global_x + half_w
    min_y = hr_center_global_y - half_l
    max_y = hr_center_global_y + half_l

    for lm_id, lm in registry.landmarks.items():
        if lm.id == hr_area_id or "zone" in lm.shape.lower(): 
            continue 
        
        if (lm.abs_x >= min_x and lm.abs_x <= max_x and 
            lm.abs_y >= min_y and lm.abs_y <= max_y):
            
            print(f"  - Drawing {lm.name}")
            
            w = lm.dimensions.width
            l = lm.dimensions.length
            
            # Check type
            is_street = "street" in lm.id or "lane" in lm.id
            
            # Always clear the ground first (Essential for gaps/streets to ensure they cut through)
            # For streets/lanes, this IS the drawing (creating a gap).
            # For buildings, this creates a clean foundation.
            draw_rect(draw, w+2, l+2, lm.abs_x, lm.abs_y, LEVEL_GROUND) 
            
            if is_street:
                 # If it's a street, optionally burn deeper? 
                 # User asked for "gaps". LEVEL_GROUND is the gap between houses.
                 # If we want distinct streets, use LEVEL_STREET (20).
                 # Let's use LEVEL_STREET to distinguish "Designated Street" from "Random Ground".
                 # But if "gap" simply means "not a house", LEVEL_GROUND is safer.
                 # Current Collision Detection keeps houses out. 
                 # This 'draw' just enforces the gap over any potential bleed.
                 # Let's stick to cleaning to Ground.
                 pass
            else:
                 # It's a building/structure
                 draw_rect(draw, w, l, lm.abs_x, lm.abs_y, LEVEL_BUILDING)
            
    # Save Full Reference
    os.makedirs(output_dir, exist_ok=True)
    full_out = os.path.join(output_dir, "hr_area_print_full.png")
    img.save(full_out)
    print(f"Saved Full Reference: {full_out}")

    # 3. Tiling Logic (Same as before)
    # ...
    # Re-using previous tiling logic code block
    overlap_cm = 0.5 
    overlap_px = int(overlap_cm * CM_TO_INCH * DPI)
    split_x_px = img_w // 2
    
    tile1 = img.crop((0, 0, split_x_px + overlap_px, img_h))
    tile2 = img.crop((split_x_px - overlap_px, 0, img_w, img_h))
    
    t1_out = os.path.join(output_dir, "hr_area_print_tile_1.png")
    t2_out = os.path.join(output_dir, "hr_area_print_tile_2.png")
    
    tile1.save(t1_out)
    tile2.save(t2_out)
    print(f"Saved Tile 1: {t1_out}")
    print(f"Saved Tile 2: {t2_out}")

if __name__ == "__main__":
    generate_hr_area_print()
