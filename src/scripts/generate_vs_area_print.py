import os
import sys
import random
from PIL import Image, ImageDraw

# Add project root to path to import mohenjo package
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "src"))

from mohenjo.registry import LandmarkRegistry, ProceduralFeature
from mohenjo.generators import generate_rich_zone, generate_poor_zone, generate_street_network

# Constants
SCALE_RATIO = 4000
DPI = 600
CM_TO_INCH = 1 / 2.54

# Laser Grayscale Values
LEVEL_GROUND = 50       # Low burn (Gray)
LEVEL_STREET = 20       # Medium burn (Dark Gray)
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
    y2 = y1 + h_px
    draw_obj.rectangle([x1, y1, x2, y2], fill=color)

def save_features(registry, new_features):
    # Filter out old VS features
    # Heuristic: parent_id starts with 'lower_vs_' or ID starts with 'vs_proc_'
    # Safe bet: usage of parent_id matching zone IDs
    
    vs_zone_ids = [lm.id for lm in registry.landmarks.values() if "vs_zone" in lm.id]
    
    # Keep others
    preserved_features = [f for f in registry.procedural_features 
                         if f.parent_id not in vs_zone_ids]
    
    # Add new
    preserved_features.extend(new_features)
    
    # Save
    procedural_path = os.path.join(os.path.dirname(__file__), "../..", "src/data/procedural.yaml")
    registry.save_procedural(procedural_path, preserved_features)
    print(f"Saved {len(new_features)} VS features to {procedural_path}")

def generate_vs_area_print():
    base_dir = os.path.join(os.path.dirname(__file__), "../..")
    landmarks_path = os.path.join(base_dir, "src/data/landmarks.yaml")
    procedural_path = os.path.join(base_dir, "src/data/procedural.yaml")
    output_dir = os.path.join(base_dir, "outputs/samples")
    
    registry = LandmarkRegistry(landmarks_path, procedural_path)
    
    vs_area_id = "lower_vs_area"
    vs_area = registry.landmarks.get(vs_area_id)
    if not vs_area:
        print(f"Error: {vs_area_id} not found.")
        return

    # Canvas
    model_w_m = vs_area.dimensions.width
    model_l_m = vs_area.dimensions.length
    padding_m = 10
    total_w_m = model_w_m + (padding_m * 2)
    total_l_m = model_l_m + (padding_m * 2)
    
    img_w = meters_to_pixels(total_w_m)
    img_h = meters_to_pixels(total_l_m)
    
    img = Image.new('L', (img_w, img_h), LEVEL_GROUND)
    draw = ImageDraw.Draw(img)
    
    center_x_px = img_w // 2
    center_y_px = img_h // 2
    
    vs_center_global_x = vs_area.abs_x
    vs_center_global_y = vs_area.abs_y
    
    def world_to_img(x, y):
        rel_x = x - vs_center_global_x
        rel_y = y - vs_center_global_y
        px = center_x_px + meters_to_pixels(rel_x)
        py = center_y_px - meters_to_pixels(rel_y)
        return int(px), int(py)

    # 1. Procedural Zones Generation
    print("Generating Procedural Housing for VS Area...")
    
    # Identify Zones - Look for VS zones
    zones = [lm for lm in registry.landmarks.values() if "vs_zone" in lm.id]
    
    # Identify Obstacles (Streets, specific landmarks)
    obstacles = []
    print("Identifying Obstacles for Collision Detection...")
    for lm in registry.landmarks.values():
        if "street" in lm.id or "lane" in lm.id or "house" in lm.id or "workshop" in lm.id:
            if "zone" in lm.id: continue 
            
            w = lm.dimensions.width
            l = lm.dimensions.length
            min_x = lm.abs_x - w/2
            max_x = lm.abs_x + w/2
            min_y = lm.abs_y - l/2
            max_y = lm.abs_y + l/2
            obstacles.append((min_x, max_x, min_y, max_y, lm.id))

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

    new_features = []
    
    for zone in zones:
        print(f"  - Processing Zone: {zone.name} ({zone.id})")
        
        zone_tl_x_global = zone.abs_x - zone.dimensions.width / 2
        zone_tl_y_global = zone.abs_y + zone.dimensions.length / 2 
        
        # 1. No Streets for now (Matches HR style)
        streets = []
        # if "mixed_north" in zone.id:
        #    streets = generate_street_network(zone.dimensions.width, zone.dimensions.length, "RICH")
        # elif "residential_south" in zone.id:
        #    streets = generate_street_network(zone.dimensions.width, zone.dimensions.length, "POOR")
            
        print(f"    - Generated {len(streets)} street segments (Allocated but empty).")
        
        # Add streets to local obstacles list for this zone's houses
        # And persist them
        for i, s in enumerate(streets):
            global_points = []
            for (lx, ly) in s.points:
                gx = zone_tl_x_global + lx
                gy = zone_tl_y_global - ly
                global_points.append((gx, gy))
                
            # Render Street
            pixel_points = []
            for (gx, gy) in global_points:
                px, py = world_to_img(gx, gy)
                pixel_points.append((px, py))
            draw.polygon(pixel_points, fill=LEVEL_STREET)
            
            # Add to obstacles (Simple Bounding Box for now)
            xs = [p[0] for p in global_points]
            ys = [p[1] for p in global_points]
            obstacles.append((min(xs), max(xs), min(ys), max(ys), "proc_street"))
            
            # Persist
            pf = ProceduralFeature(
                id=f"{zone.id}_street_{i}",
                parent_id=zone.id,
                shape="POLYGON",
                geometry={'points': global_points},
                description=f"Tertiary Street in {zone.name}"
            )
            new_features.append(pf)

        # 2. Generate Houses
        houses = []
        if "mixed_north" in zone.id:
            # Fit one more row: Balanced approach.
            # House 14m, Gap 3m = Stride 17m.
            # 230 / 17 = 13.5 columns. Fits 13 cols comfortably.
            houses = generate_rich_zone(zone.dimensions.width, zone.dimensions.length, house_size=14.0, gap=3.0)
        elif "residential_south" in zone.id:
            houses = generate_poor_zone(zone.dimensions.width, zone.dimensions.length)
            
        print(f"    - Generating {len(houses)} shapes (pre-collision)...")
        
        valid_houses = []
        valid_houses = []
        
        is_rich_zone = "mixed_north" in zone.id # Or identify by generator type
        
        if is_rich_zone:
            # RICH ZONE: Houses come in pairs (Wall, Courtyard)
            # Validation Logic: Check Wall. If Wall is valid, keep BOTH. If Wall fails, discard BOTH.
            # This prevents orphaned courtyards.
            num_houses = len(houses)
            # Ensure even number just in case
            if num_houses % 2 != 0:
                 print(f"Warning: Rich zone houses count {num_houses} is not even!")
            
            for i in range(0, num_houses, 2):
                if i + 1 >= num_houses: break
                
                wall_house = houses[i]
                court_house = houses[i+1]
                
                # Global points for Wall
                wall_points = []
                for (lx, ly) in wall_house.points:
                    gx = zone_tl_x_global + lx
                    gy = zone_tl_y_global - ly
                    wall_points.append((gx, gy))
                
                # Check Collision on WALL only
                if not check_collision(wall_points, obstacles):
                    # Wall is valid -> Keep Pair
                    
                    # 1. Add Wall
                    valid_houses.append((wall_house, wall_points))
                    pf_wall = ProceduralFeature(
                        id=f"{zone.id}_house_{i}",
                        parent_id=zone.id,
                        shape="POLYGON",
                        geometry={'points': wall_points},
                        description=f"Procedural House in {zone.name} ({wall_house.category})"
                    )
                    new_features.append(pf_wall)
                    
                    # 2. Add Courtyard
                    court_points = []
                    for (lx, ly) in court_house.points:
                        gx = zone_tl_x_global + lx
                        gy = zone_tl_y_global - ly
                        court_points.append((gx, gy))
                        
                    valid_houses.append((court_house, court_points))
                    pf_court = ProceduralFeature(
                        id=f"{zone.id}_house_{i+1}",
                        parent_id=zone.id,
                        shape="POLYGON",
                        geometry={'points': court_points},
                        description=f"Procedural House in {zone.name} ({court_house.category})"
                    )
                    new_features.append(pf_court)
                    
        else:
            # POOR ZONE: Houses are individual (or collision check per item is fine)
            for i, h in enumerate(houses):
                global_points = []
                for (lx, ly) in h.points:
                    gx = zone_tl_x_global + lx
                    gy = zone_tl_y_global - ly
                    global_points.append((gx, gy))
                
                if not check_collision(global_points, obstacles):
                    valid_houses.append((h, global_points))
                    
                    # Create ProceduralFeature
                    pf = ProceduralFeature(
                        id=f"{zone.id}_house_{i}",
                        parent_id=zone.id,
                        shape="POLYGON",
                        geometry={'points': global_points},
                        description=f"Procedural House in {zone.name} ({h.category})"
                    )
                    new_features.append(pf)
        
        print(f"    - Valid shapes after collision check: {len(valid_houses)}")

        for (h, global_points) in valid_houses:
            pixel_points = []
            for (gx, gy) in global_points:
                px, py = world_to_img(gx, gy)
                pixel_points.append((px, py))
            
            if h.category == "COURTYARD":
                color = LEVEL_GROUND 
            else:
                color = LEVEL_BUILDING
                
            draw.polygon(pixel_points, fill=color)

    # Save to procedural.yaml
    save_features(registry, new_features)

    # --- PERSISTENCE LOGIC START ---
    # Convert valid houses to ProceduralFeatures
    # We need to construct ProceduralFeature objects
    # and save them to procedural.yaml
    
    # from mohenjo.registry import ProceduralFeature # Moved to top
    
    new_features = []
    
    # VS Streets (if we generated them? Wait, collision check used obstacle list, did we generate streets?)
    # In generate_hr_area_print we didn't actually generate procedural streets in VS area yet?
    # Ah, the HR script had generate_street_network. The VS clone I made (generate_vs_area_print.py)
    # COPIED the structure but I didn't verify if I copied the street generation call.
    # Looking at my previous write_to_file for generate_vs_area_print.py...
    # I see: "1. Procedural Zones Generation", then "Identify Zones", then loop over zones.
    # I did NOT include generate_street_network in the VS script loop yet!
    # I should probably add that if I want streets. 
    # But for now, let's persist what we have (Houses).
    
    # We have valid_houses list from the loop. But wait, loop is per zone.
    # We need to collect ALL features across zones.
    
    all_vs_features = []
    
    # I need to refactor the loop to collect features instead of just drawing.
    # Let's do a quick re-traversal or refill?
    # Better: Identify generated items and add to list.
    pass # placeholder
    
    # Refactoring the generation loop to collect features:
    generated_features = []
    
    # Clear existing VS features to ensure idempotency
    # We'll filter them out from registry.procedural_features when saving
    
    # ... (Re-implementing the loop logic to create ProceduralFeature objects) ...
    # Wait, I can't easily inject mid-stream without rewriting the function.
    # I will append the persistence logic at the end, but I need the data.
    # I will rewrite the generation block to store data in `generated_features` AND draw.

    # Actually, simpler to just modify the loop above in a subsequent Edit.
    # For now let's just add the import and the save function skeleton.
    



    # 2. Explicit Landmarks (Overlay on top)
    print("Drawing Explicit Landmarks...")
    half_w = model_w_m / 2
    half_l = model_l_m / 2
    min_x = vs_center_global_x - half_w
    max_x = vs_center_global_x + half_w
    min_y = vs_center_global_y - half_l
    max_y = vs_center_global_y + half_l

    for lm_id, lm in registry.landmarks.items():
        if lm.id == vs_area_id or "zone" in lm.shape.lower(): 
            continue 
        
        if (lm.abs_x >= min_x and lm.abs_x <= max_x and 
            lm.abs_y >= min_y and lm.abs_y <= max_y):
            
            print(f"  - Drawing {lm.name}")
            
            w = lm.dimensions.width
            l = lm.dimensions.length
            
            # Always clear ground first
            draw_rect(draw, w+2, l+2, lm.abs_x, lm.abs_y, center_x_px, center_y_px, vs_center_global_x, vs_center_global_y, LEVEL_GROUND) 
            
            if "street" in lm.id or "lane" in lm.id:
                 pass # Just cleared path
            else:
                 draw_rect(draw, w, l, lm.abs_x, lm.abs_y, center_x_px, center_y_px, vs_center_global_x, vs_center_global_y, LEVEL_BUILDING)
            
    # Save Full Reference
    os.makedirs(output_dir, exist_ok=True)
    full_out = os.path.join(output_dir, "vs_area_print_full.png")
    img.save(full_out)
    print(f"Saved Full Reference: {full_out}")

if __name__ == "__main__":
    generate_vs_area_print()
