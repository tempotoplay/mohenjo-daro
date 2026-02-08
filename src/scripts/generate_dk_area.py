import os
import sys
import random
from PIL import Image, ImageDraw

# Add project root to path to import mohenjo package
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "src"))

from mohenjo.registry import LandmarkRegistry, ProceduralFeature
from mohenjo.generators import generate_rich_zone, generate_street_network

# Constants
SCALE_RATIO = 4000
DPI = 600
CM_TO_INCH = 1 / 2.54

# Laser Grayscale Values
LEVEL_GROUND = 50       # Low burn (Gray)
LEVEL_STREET = 0        # Deep burn (Black)
LEVEL_BUILDING = 255    # No burn (White) - Highest point

def meters_to_pixels(meters):
    return int(meters * (100 / SCALE_RATIO) * CM_TO_INCH * DPI)

def draw_rect(draw_obj, w_m, h_m, x_m, y_m, center_x_px, center_y_px, area_center_x, area_center_y, color):
    w_px = meters_to_pixels(w_m)
    h_px = meters_to_pixels(h_m) 
    
    # World to Img
    rel_x = x_m - area_center_x
    rel_y = y_m - area_center_y
    cx = center_x_px + meters_to_pixels(rel_x)
    cy = center_y_px - meters_to_pixels(rel_y)
    
    x1 = cx - (w_px // 2)
    y1 = cy - (h_px // 2)
    x2 = x1 + w_px
    y2 = y1 + h_px
    draw_obj.rectangle([x1, y1, x2, y2], fill=color)

def check_collision(poly_points_global, obstacles):
    p_xs = [p[0] for p in poly_points_global]
    p_ys = [p[1] for p in poly_points_global]
    p_min_x, p_max_x = min(p_xs), max(p_xs)
    p_min_y, p_max_y = min(p_ys), max(p_ys)
    
    for (o_min_x, o_max_x, o_min_y, o_max_y, oid) in obstacles:
        if (p_min_x < o_max_x and p_max_x > o_min_x and
            p_min_y < o_max_y and p_max_y > o_min_y):
            return True
    return False

def save_features(registry, new_features):
    # Filter out old DK features
    # Heuristic: parent_id starts with 'lower_dk_' or ID starts with 'dk_'
    
    dk_zone_ids = [lm.id for lm in registry.landmarks.values() if "dk_area" in lm.id or "dk_zone" in lm.id]
    
    # Keep others (non-DK)
    preserved_features = [f for f in registry.procedural_features 
                         if f.parent_id not in dk_zone_ids and not f.id.startswith("dk_")]
    
    # Add new
    preserved_features.extend(new_features)
    
    # Save
    procedural_path = os.path.join(os.path.dirname(__file__), "../..", "src/data/procedural.yaml")
    registry.save_procedural(procedural_path, preserved_features)
    print(f"Saved {len(new_features)} DK features to {procedural_path}")

def generate_dk_area():
    base_dir = os.path.join(os.path.dirname(__file__), "../..")
    landmarks_path = os.path.join(base_dir, "src/data/landmarks.yaml")
    procedural_path = os.path.join(base_dir, "src/data/procedural.yaml")
    output_dir = os.path.join(base_dir, "outputs/samples")
    
    registry = LandmarkRegistry(landmarks_path, procedural_path)
    
    dk_area_id = "lower_dk_area"
    dk_area = registry.landmarks.get(dk_area_id)
    if not dk_area:
        print(f"Error: {dk_area_id} not found.")
        return

    # Canvas Setup
    model_w_m = dk_area.dimensions.width
    model_l_m = dk_area.dimensions.length
    padding_m = 10
    total_w_m = model_w_m + (padding_m * 2)
    total_l_m = model_l_m + (padding_m * 2)
    
    img_w = meters_to_pixels(total_w_m)
    img_h = meters_to_pixels(total_l_m)
    
    img = Image.new('L', (img_w, img_h), LEVEL_GROUND)
    draw = ImageDraw.Draw(img)
    
    center_x_px = img_w // 2
    center_y_px = img_h // 2
    
    dk_center_global_x = dk_area.abs_x
    dk_center_global_y = dk_area.abs_y
    
    def world_to_img(x, y):
        rel_x = x - dk_center_global_x
        rel_y = y - dk_center_global_y
        px = center_x_px + meters_to_pixels(rel_x)
        py = center_y_px - meters_to_pixels(rel_y)
        return int(px), int(py)

    print("Generating Procedural Features for DK Area...")
    
    # 1. Identify Obstacles (Explicit Landmarks in/near DK)
    obstacles = []
    print("Identifying Obstacles for Collision Detection...")
    
    # Define DK bounds (approx)
    dk_min_x = dk_area.abs_x - model_w_m/2
    dk_max_x = dk_area.abs_x + model_w_m/2
    dk_min_y = dk_area.abs_y - model_l_m/2
    dk_max_y = dk_area.abs_y + model_l_m/2
    
    for lm in registry.landmarks.values():
        # Skip the DK area itself, zones, and large boundaries
        if (lm.id == dk_area_id or 
            "zone" in lm.shape.lower() or 
            lm.shape == "RECT_BORDER" or 
            "boundary" in lm.id): 
            continue 
        
        # Overlap check
        w = lm.dimensions.width
        l = lm.dimensions.length
        min_x = lm.abs_x - w/2
        max_x = lm.abs_x + w/2
        min_y = lm.abs_y - l/2
        max_y = lm.abs_y + l/2
        
        # If intersects DK Area
        if (min_x < dk_max_x and max_x > dk_min_x and
            min_y < dk_max_y and max_y > dk_min_y):
            
            obstacles.append((min_x, max_x, min_y, max_y, lm.id))
            
            # Draw obstacles on visual
            # Check if it is a street
            color = LEVEL_BUILDING
            if "street" in lm.id or "lane" in lm.id:
                color = LEVEL_STREET
                
            draw_rect(draw, w, l, lm.abs_x, lm.abs_y, center_x_px, center_y_px, dk_center_global_x, dk_center_global_y, color)

    new_features = []
    
    # 2. Generate Streets (Priority)
    print("  - Generating Street Network (Grid)...")
    streets = generate_street_network(model_w_m, model_l_m, "RICH")
    
    dk_tl_x_global = dk_area.abs_x - model_w_m / 2
    dk_tl_y_global = dk_area.abs_y + model_l_m / 2 
    
    street_count = 0
    for i, s in enumerate(streets):
        global_points = []
        for (lx, ly) in s.points:
            gx = dk_tl_x_global + lx
            gy = dk_tl_y_global - ly
            global_points.append((gx, gy))
            
        # Draw Street
        pixel_points = []
        for (gx, gy) in global_points:
            px, py = world_to_img(gx, gy)
            pixel_points.append((px, py))
        draw.polygon(pixel_points, fill=LEVEL_STREET)
        
        # Add to obstacles
        xs = [p[0] for p in global_points]
        ys = [p[1] for p in global_points]
        obstacles.append((min(xs), max(xs), min(ys), max(ys), "proc_street"))
        
        # Persist
        pf = ProceduralFeature(
            id=f"dk_street_{i}",
            parent_id=dk_area_id,
            shape="POLYGON",
            geometry={'points': global_points},
            description=f"Street in {dk_area.name}"
        )
        new_features.append(pf)
        street_count += 1
        
    print(f"    - Generated {street_count} street segments.")
    
    # 3. Generate Houses (Fill)
    print("  - Generating Housing...")
    
    # Use RICH zone parameters: House=12m, Gap=2m
    houses = generate_rich_zone(model_w_m, model_l_m, house_size=12.0, gap=2.0)
    
    valid_houses_count = 0
    
    # Iterate in pairs for Rich Zone consistency
    num_houses = len(houses)
    for i in range(0, num_houses, 2):
        if i + 1 >= num_houses: break
        
        wall_house = houses[i]
        court_house = houses[i+1]
        
        # Global points for Wall
        wall_points = []
        for (lx, ly) in wall_house.points:
            gx = dk_tl_x_global + lx
            gy = dk_tl_y_global - ly
            wall_points.append((gx, gy))
        
        # Check Collision on WALL
        if not check_collision(wall_points, obstacles):
            # Wall is valid -> Keep Pair
            
            # 1. Add Wall
            pf_wall = ProceduralFeature(
                id=f"dk_house_{i}",
                parent_id=dk_area_id,
                shape="POLYGON",
                geometry={'points': wall_points},
                description=f"Procedural House in DK ({wall_house.category})"
            )
            new_features.append(pf_wall)
            
            # Visual
            pixel_points = []
            for (gx, gy) in wall_points:
                px, py = world_to_img(gx, gy)
                pixel_points.append((px, py))
            draw.polygon(pixel_points, fill=LEVEL_BUILDING)
            
            # 2. Add Courtyard
            court_points = []
            for (lx, ly) in court_house.points:
                gx = dk_tl_x_global + lx
                gy = dk_tl_y_global - ly
                court_points.append((gx, gy))
                
            pf_court = ProceduralFeature(
                id=f"dk_house_{i+1}",
                parent_id=dk_area_id,
                shape="POLYGON",
                geometry={'points': court_points},
                description=f"Procedural House in DK ({court_house.category})"
            )
            new_features.append(pf_court)
            
            # Visual (Courtyard is ground level/color)
            pixel_points = []
            for (gx, gy) in court_points:
                px, py = world_to_img(gx, gy)
                pixel_points.append((px, py))
            draw.polygon(pixel_points, fill=LEVEL_GROUND) # Or fill with court color if distinct
            
            valid_houses_count += 2
            
    print(f"    - Valid houses placed: {valid_houses_count}")

    # Save to procedural.yaml
    save_features(registry, new_features)
    
    # Save Image
    os.makedirs(output_dir, exist_ok=True)
    full_out = os.path.join(output_dir, "dk_area_print_full.png")
    img.save(full_out)
    print(f"Saved Full Reference: {full_out}")

    # 3. Tiling Logic
    overlap_cm = 0.5 
    overlap_px = int(overlap_cm * CM_TO_INCH * DPI)
    split_x_px = img_w // 2
    
    # Tile 1 (Left + Overlap)
    tile1 = img.crop((0, 0, split_x_px + overlap_px, img_h))
    t1_out = os.path.join(output_dir, "dk_area_print_tile_1.png")
    tile1.save(t1_out)
    print(f"Saved Tile 1: {t1_out}")
    
    # Tile 2 (Right + Overlap)
    tile2 = img.crop((split_x_px - overlap_px, 0, img_w, img_h))
    t2_out = os.path.join(output_dir, "dk_area_print_tile_2.png")
    tile2.save(t2_out)
    print(f"Saved Tile 2: {t2_out}")

if __name__ == "__main__":
    generate_dk_area()
