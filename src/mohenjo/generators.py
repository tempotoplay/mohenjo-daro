import random
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class House:
    points: List[Tuple[float, float]]
    category: str # "RICH" or "POOR"

def get_wobbly_rect_points(x, y, w, h, wobble=0.2):
    """Returns list of 4 points for a rect with slight wobble."""
    # Wobble relative to size? Or fixed? 
    # Use small wobble for realism in meters (e.g. 0.2m)
    p1 = (x + random.uniform(-wobble, wobble), y + random.uniform(-wobble, wobble))
    p2 = (x + w + random.uniform(-wobble, wobble), y + random.uniform(-wobble, wobble))
    p3 = (x + w + random.uniform(-wobble, wobble), y + h + random.uniform(-wobble, wobble))
    p4 = (x + random.uniform(-wobble, wobble), y + h + random.uniform(-wobble, wobble))
    return [p1, p2, p3, p4]

def generate_rich_zone(width_m: float, length_m: float, seed: int = 42) -> List[House]:
    random.seed(seed)
    houses = []
    
    house_size = 15.0
    gap = 4.0
    
    for y in range(0, int(length_m - house_size), int(house_size + gap)):
        for x in range(0, int(width_m - house_size), int(house_size + gap)):
            
            # Base rect coords
            # Add wobble logic here or just return rect?
            # Let's return wobbly polygons directly.
            
            wall = house_size * 0.25
            # Rotation 0-3: U-shapes (Open on one side)
            # Rotation 4:   O-shape (Fully enclosed)
            shape_type = random.choice([0, 1, 2, 3, 4]) 
            
            # 1. Main Block
            main_poly = get_wobbly_rect_points(x, y, house_size, house_size, wobble=0.3)
            houses.append(House(points=main_poly, category="RICH_WALL"))
            
            # 2. Courtyard (Eraser)
            cx, cy, cw, ch = 0, 0, 0, 0
            
            # Dimensions for Enclosed (O-Shape)
            if shape_type == 4:
                # Centered courtyard
                cx = x + wall
                cy = y + wall
                cw = house_size - 2*wall
                ch = house_size - 2*wall
            
            # Dimensions for Open (U-Shape)
            elif shape_type == 0:   # Top Open
                cx, cy, cw, ch = x+wall, y, house_size-2*wall, house_size-wall
            elif shape_type == 1: # Right Open
                cx, cy, cw, ch = x+wall, y+wall, house_size-wall, house_size-2*wall
            elif shape_type == 2: # Bottom Open
                cx, cy, cw, ch = x+wall, y+wall, house_size-2*wall, house_size-wall
            elif shape_type == 3: # Left Open
                cx, cy, cw, ch = x, y+wall, house_size-wall, house_size-2*wall
            
            court_poly = get_wobbly_rect_points(cx, cy, cw, ch, wobble=0.1)
            houses.append(House(points=court_poly, category="COURTYARD"))
            
    return houses

def generate_poor_zone(width_m: float, length_m: float, seed: int = 42) -> List[House]:
    random.seed(seed)
    houses = []
    
    house_w = 5.0
    house_h = 6.0
    gap = 1.0
    
    current_y = 0
    while current_y < length_m - house_h:
        current_x = 0
        while current_x < width_m - house_w:
            
            # Logic: Skipping (20%)
            if random.random() < 0.2:
                current_x += house_w + gap
                continue
                
            # Logic: Coalescing (Merging) (30%)
            w_actual = house_w
            h_actual = house_h
            if random.random() < 0.3 and (current_x + (house_w*2) + gap < width_m):
                w_actual = (house_w * 2) + gap + random.uniform(-0.5, 0.5)
                h_actual = house_h + random.uniform(-0.5, 0.5)
            else:
                 w_actual += random.uniform(-0.5, 0.5)
                 h_actual += random.uniform(-0.5, 0.5)

            # Draw
            if current_x + w_actual < width_m:
                 poly = get_wobbly_rect_points(current_x, current_y, w_actual, h_actual, wobble=0.2)
                 houses.append(House(points=poly, category="POOR"))
            
            current_x += w_actual + gap
        current_y += house_h + gap
        
    return houses
