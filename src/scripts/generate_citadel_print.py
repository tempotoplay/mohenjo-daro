import os
import sys
from PIL import Image, ImageDraw

# Add project root to path to import mohenjo package
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "src"))

from mohenjo.registry import LandmarkRegistry

# Constants matches generate_test_sample.py
SCALE_RATIO = 4000 # Updated to 1:4000
DPI = 600
CM_TO_INCH = 1 / 2.54

# Laser Grayscale Values
LEVEL_GROUND = 50       # Low burn (Gray)
LEVEL_STREET = 20       # Medium burn (Dark Gray)
LEVEL_BUILDING = 255    # No burn (White) - Highest point

def meters_to_pixels(meters):
    return int(meters * (100 / SCALE_RATIO) * CM_TO_INCH * DPI)

def generate_citadel_print():
    # Paths
    base_dir = os.path.join(os.path.dirname(__file__), "../..")
    landmarks_path = os.path.join(base_dir, "src/data/landmarks.yaml")
    procedural_path = os.path.join(base_dir, "src/data/procedural.yaml")
    output_path = os.path.join(base_dir, "outputs/samples/citadel_print.png")

    # Load Registry
    registry = LandmarkRegistry(landmarks_path, procedural_path)
    
    # Get Citadel Walls for canvas sizing
    citadel = registry.landmarks.get("citadel_walls")
    if not citadel:
        print("Error: citadel_walls not found in landmarks.")
        return

    # Canvas Dimensions
    # User requested fit to 6x10 cm Area.
    # At 1:4000, model is ~4.6cm x ~9.2cm.
    
    TARGET_W_CM = 6.0
    TARGET_L_CM = 10.0
    
    target_w_m = (TARGET_W_CM / 100) * SCALE_RATIO
    target_l_m = (TARGET_L_CM / 100) * SCALE_RATIO
    
    # Calculate Padding to center
    model_w_m = citadel.dimensions.width
    model_l_m = citadel.dimensions.length
    
    pad_w_m = max(0, (target_w_m - model_w_m) / 2)
    pad_l_m = max(0, (target_l_m - model_l_m) / 2)
    
    # Apply padding
    total_w_m = model_w_m + (pad_w_m * 2)
    total_l_m = model_l_m + (pad_l_m * 2)
    
    img_w = meters_to_pixels(total_w_m)
    img_h = meters_to_pixels(total_l_m)
    
    print(f"Canvas: {total_w_m:.1f}m x {total_l_m:.1f}m")
    print(f"Padding X: {pad_w_m:.1f}m, Padding Y: {pad_l_m:.1f}m")
    print(f"Image: {img_w}x{img_h} px")
    print(f"Scale: 1:{SCALE_RATIO} @ {DPI} DPI")

    # Create Image
    img = Image.new('L', (img_w, img_h), LEVEL_GROUND)
    draw = ImageDraw.Draw(img)
    
    # Coordinate System
    # Center of Image corresponds to Citadel Origin (0,0)
    center_x_px = img_w // 2
    center_y_px = img_h // 2
    
    def world_to_img(x, y):
        # Image X increases Right (+X)
        # Image Y increases Down (-Y)
        px = center_x_px + meters_to_pixels(x)
        py = center_y_px - meters_to_pixels(y) 
        return px, py

    def draw_rect(draw_obj, w_m, h_m, x_m, y_m, color):
        # x_m, y_m are CENTER of the rect
        w_px = meters_to_pixels(w_m)
        h_px = meters_to_pixels(h_m)
        
        cx, cy = world_to_img(x_m, y_m)
        
        # Top Left
        x1 = cx - (w_px // 2)
        y1 = cy - (h_px // 2)
        x2 = x1 + w_px
        y2 = y1 + h_px
        
        draw_obj.rectangle([x1, y1, x2, y2], fill=color)

    def draw_ellipse(draw_obj, w_m, l_m, x_m, y_m, color):
        w_px = meters_to_pixels(w_m)
        l_px = meters_to_pixels(l_m)
        
        cx, cy = world_to_img(x_m, y_m)
        
        x1 = cx - (w_px // 2)
        y1 = cy - (l_px // 2)
        x2 = x1 + w_px
        y2 = y1 + l_px
        
        draw_obj.ellipse([x1, y1, x2, y2], fill=color)

    # 1. Draw "Explicit" Landmarks from landmarks.yaml
    # These include Great Bath, Granary, Stupa, etc.
    print("Drawing Explicit Landmarks...")
    for lm_id, lm in registry.landmarks.items():
        if lm.region == "Citadel" and lm.id != "citadel_walls":
            print(f"  - Drawing {lm.name} ({lm.shape})")
            
            # Determine Color
            color = LEVEL_BUILDING
            if "pool" in lm.description.lower() or "tank" in lm.description.lower():
                color = LEVEL_GROUND # Emulate depth for pool?
            elif lm.id == "citadel_divinity_street":
                 color = LEVEL_STREET

            # Draw based on shape
            w = lm.dimensions.width
            l = lm.dimensions.length
            
            if lm.shape in ["CIRCLE", "OVAL"]:
                if lm.dimensions.diameter > 0:
                    w = lm.dimensions.diameter
                    l = lm.dimensions.diameter
                draw_ellipse(draw, w, l, lm.abs_x, lm.abs_y, color)
            
            elif lm.shape in ["RECT_COMPLEX", "RECT_GRID", "SQUARE_GRID", "LINE", "RECT_BORDER"]:
                if lm.id == "citadel_great_bath":
                     # Draw base block
                     draw_rect(draw, w, l, lm.abs_x, lm.abs_y, LEVEL_BUILDING)
                     # Draw Pool (Rough center approximation)
                     if lm.dimensions.pool_w > 0:
                         draw_rect(draw, lm.dimensions.pool_w, lm.dimensions.pool_l, lm.abs_x, lm.abs_y, LEVEL_GROUND)
                else:
                    draw_rect(draw, w, l, lm.abs_x, lm.abs_y, color)



    # 2. Draw Procedural Features (Walls, Bastions, etc.)
    # Draw these AFTER landmarks (or concurrent? Usually overlapping is fine if they are consistent)
    # Actually, walls (Procedural) should probably be ON TOP if they are the defining perimeter?
    # Or landmarks ON TOP of walls?
    # Let's draw procedural features now.
    print(f"Drawing {len(registry.procedural_features)} Procedural Features...")
    for pf in registry.procedural_features:
        if pf.parent_id == "citadel_walls": # Only draw Citadel stuff
            bg_color = LEVEL_BUILDING
            if "Courtyard" in pf.description or "pool" in pf.description.lower():
                bg_color = LEVEL_GROUND
            
            # Geometry: x, y, w, h
            geo = pf.geometry
            draw_rect(draw, geo['w'], geo['h'], geo['x'], geo['y'], bg_color)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Saved to {output_path}")
    
    # Calculat phys size
    w_cm = img_w / DPI * 2.54
    h_cm = img_h / DPI * 2.54
    print(f"Physical Size: {w_cm:.2f} cm x {h_cm:.2f} cm")

if __name__ == "__main__":
    generate_citadel_print()
