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

def generate_rich_zone(width_m: float, length_m: float, seed: int = 42, house_size: float = 15.0, gap: float = 4.0) -> List[House]:
    random.seed(seed)
    houses = []
    
    # house_size and gap passed as args (defaults 15.0, 4.0)
    
    for y in range(0, int(length_m - house_size), int(house_size + gap)):
        for x in range(0, int(width_m - house_size), int(house_size + gap)):
            
            # Base rect coords
            # Add wobble logic here or just return rect?
            # Let's return wobbly polygons directly.
            
            wall = house_size * 0.25
            # Rotation 0-3: U-shapes (Open on one side)
            # Rotation 4:   O-shape (Fully enclosed)
            # Rotation 5:   Solid Block (No Courtyard)
            shape_type = random.choice([0, 1, 2, 3, 4, 4, 0, 1, 5, 5]) # Weighted: 20% Solid, 20% O-Shape, Rest U-Shape
            
            # 1. Main Block
            main_poly = get_wobbly_rect_points(x, y, house_size, house_size, wobble=0.3)
            houses.append(House(points=main_poly, category="RICH_WALL"))
            
            # 2. Courtyard (Eraser or Filler)
            if shape_type == 5:
                # Solid Block: Add a dummy filler to maintain Pair structure
                # Tiny rect inside main block (safe)
                dummy_poly = get_wobbly_rect_points(x + house_size/2, y + house_size/2, 0.1, 0.1, wobble=0.0)
                houses.append(House(points=dummy_poly, category="RICH_SOLID_FILLER"))

            else:
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

@dataclass
class Street:
    points: List[Tuple[float, float]] # Polygon (likely a rect)
    category: str # "TERTIARY_STREET"

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

def generate_street_network(width_m: float, length_m: float, style: str, seed: int = 42) -> List[Street]:
    """Generates a network of secondary streets (polygons) to serve as obstacles."""
    random.seed(seed)
    streets = []
    
    if style == "RICH":
        # Regular Grid
        block_size = 45.0 # Large blocks for rich
        street_width = 3.0
        
        # Horizontal Streets
        y = block_size
        while y < length_m - block_size:
            poly = get_wobbly_rect_points(0, y, width_m, street_width, wobble=0.5)
            streets.append(Street(points=poly, category="TERTIARY_STREET"))
            y += block_size + street_width
            
        # Vertical Streets
        x = block_size
        while x < width_m - block_size:
            poly = get_wobbly_rect_points(x, 0, street_width, length_m, wobble=0.5)
            streets.append(Street(points=poly, category="TERTIARY_STREET"))
            x += block_size + street_width
            
    elif style == "POOR":
        # Organic / Chaotic
        # Random cuts through the block to break it up.
        num_streets = int((width_m * length_m) / 1200) # Density heuristic
        street_width = 2.5
        
        for _ in range(num_streets):
            # Random Start/End
            if random.random() < 0.5:
                # Vertical-ish
                start_x = random.uniform(0, width_m)
                end_x = start_x + random.uniform(-10, 10)
                
                # Make a rect
                poly = get_wobbly_rect_points(start_x, 0, street_width, length_m, wobble=1.0)
                streets.append(Street(points=poly, category="TERTIARY_STREET"))
            else:
                # Horizontal-ish
                start_y = random.uniform(0, length_m)
                end_y = start_y + random.uniform(-10, 10)
                
                poly = get_wobbly_rect_points(0, start_y, width_m, street_width, wobble=1.0)
                streets.append(Street(points=poly, category="TERTIARY_STREET"))
                
    return streets

def generate_industrial_zone(width_m: float, length_m: float, seed: int = 42) -> List[House]:
    """Generates large, spaced-out industrial buildings."""
    random.seed(seed)
    buildings = []
    
    # Large buildings, Big gaps
    # Variable sizes
    
    # Try a simple packing or loose grid
    x = 0
    y = 0
    row_height = 0
    
    gap = 8.0
    
    current_y = 5.0
    while current_y < length_m - 10:
        current_x = 5.0
        row_h = 0
        while current_x < width_m - 10:
            
            w = random.uniform(12.0, 20.0)
            h = random.uniform(10.0, 18.0)
            
            if current_x + w > width_m:
                 break
                 
            poly = get_wobbly_rect_points(current_x, current_y, w, h, wobble=0.2)
            buildings.append(House(points=poly, category="INDUSTRIAL"))
            
            row_h = max(row_h, h)
            current_x += w + gap
            
        current_y += row_h + gap
        
    return buildings
