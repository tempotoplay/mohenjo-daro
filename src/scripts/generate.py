import os
import sys
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Add src/
from mohenjo.registry import LandmarkRegistry, ProceduralFeature

def generate_citadel_bastions(registry: LandmarkRegistry) -> list[ProceduralFeature]:
    features = []
    
    # Get Citadel Walls
    walls = registry.landmarks.get('citadel_walls')
    if not walls:
        print("Citadel Walls not found.")
        return []
    
    width_m = walls.dimensions.width
    length_m = walls.dimensions.length
    cx = walls.abs_x
    cy = walls.abs_y
    
    bastion_w = 12.0 # 12 meters wide
    bastion_l = 12.0 # 12 meters deep (Square)
    interval = 30.0 # Spacing
    
    x_start = cx - width_m/2
    x_end = cx + width_m/2
    y_start = cy - length_m/2
    y_end = cy + length_m/2
    
    # helper to add wall segment
    def add_wall_segment(x, y, w, h, side):
        features.append(ProceduralFeature(
            id=f"wall_{side}_{len(features)}",
            parent_id="citadel_walls",
            shape="RECT",
            geometry={'x': x, 'y': y, 'w': w, 'h': h},
            description=f"Citadel Wall Segment {side}"
        ))

    # Determine positions along X axis
    x_positions = []
    curr = x_start
    while curr <= x_end + 0.1:
        x_positions.append(curr)
        curr += interval
    
    # Top Edge
    for i, x_pos in enumerate(x_positions):
        features.append(ProceduralFeature(
            id=f"bastion_top_{i}", parent_id="citadel_walls", shape="RECT",
            geometry={'x': x_pos, 'y': y_start, 'w': bastion_w, 'h': bastion_l},
            description="Citadel Bastion"
        ))
        if i < len(x_positions) - 1:
            next_x = x_positions[i+1]
            gap_center_x = (x_pos + next_x) / 2
            gap_w = interval - bastion_w + 0.5
            add_wall_segment(gap_center_x, y_start, gap_w, 6.0, "top")

    # Bottom Edge
    for i, x_pos in enumerate(x_positions):
        features.append(ProceduralFeature(
            id=f"bastion_bottom_{i}", parent_id="citadel_walls", shape="RECT",
            geometry={'x': x_pos, 'y': y_end, 'w': bastion_w, 'h': bastion_l},
            description="Citadel Bastion"
        ))
        if i < len(x_positions) - 1:
            next_x = x_positions[i+1]
            gap_center_x = (x_pos + next_x) / 2
            gap_w = interval - bastion_w + 0.5
            add_wall_segment(gap_center_x, y_end, gap_w, 6.0, "bottom")

    # Left & Right Edge
    y_positions = []
    curr_y = y_start + interval
    while curr_y <= y_end - interval + 0.1:
        y_positions.append(curr_y)
        curr_y += interval
        
    for i, y_pos in enumerate(y_positions):
        # Left
        features.append(ProceduralFeature(
            id=f"bastion_left_{i}", parent_id="citadel_walls", shape="RECT",
            geometry={'x': x_start, 'y': y_pos, 'w': bastion_w, 'h': bastion_l},
            description="Citadel Bastion"
        ))
        if i < len(y_positions) - 1:
            next_y = y_positions[i+1]
            gap_center_y = (y_pos + next_y) / 2
            gap_h = interval - bastion_l + 0.5
            add_wall_segment(x_start, gap_center_y, 6.0, gap_h, "left")
            
        # Right
        features.append(ProceduralFeature(
            id=f"bastion_right_{i}", parent_id="citadel_walls", shape="RECT",
            geometry={'x': x_end, 'y': y_pos, 'w': bastion_w, 'h': bastion_l},
            description="Citadel Bastion"
        ))
        if i < len(y_positions) - 1:
            next_y = y_positions[i+1]
            gap_center_y = (y_pos + next_y) / 2
            gap_h = interval - bastion_l + 0.5
            add_wall_segment(x_end, gap_center_y, 6.0, gap_h, "right")

    # Connect corners (gaps between corner bastion and first side bastion)
    if y_positions:
        first_y = y_positions[0]
        last_y = y_positions[-1]
        
        # Left Top
        gap_center = (y_start + first_y) / 2
        gap_h = (first_y - y_start) - bastion_l + 0.5
        add_wall_segment(x_start, gap_center, 6.0, gap_h, "left_corner_top")
        
        # Left Bottom
        gap_center = (last_y + y_end) / 2
        gap_h = (y_end - last_y) - bastion_l + 0.5
        add_wall_segment(x_start, gap_center, 6.0, gap_h, "left_corner_bottom")
        
        # Right Top
        add_wall_segment(x_end, (y_start + first_y)/2, 6.0, gap_h, "right_corner_top")
        # Right Bottom
        add_wall_segment(x_end, (y_end + last_y)/2, 6.0, gap_h, "right_corner_bottom")

    return features

def generate_citadel_interior(registry: LandmarkRegistry) -> list[ProceduralFeature]:
    features = []
    
    walls = registry.landmarks.get('citadel_walls')
    if not walls: return []
    
    # Citadel Bounds
    c_x, c_y = walls.abs_x, walls.abs_y
    c_w, c_l = walls.dimensions.width, walls.dimensions.length
    
    # Internal usage area (exclude walls themselves)
    wall_thickness = 12.0
    min_x = c_x - (c_w/2) + wall_thickness
    max_x = c_x + (c_w/2) - wall_thickness
    min_y = c_y - (c_l/2) + wall_thickness
    max_y = c_y + (c_l/2) - wall_thickness
    
    # Get Exclusion Zones (Existing Landmarks in Citadel)
    # We add a buffer of 5m
    padding = 5.0
    exclusion_zones = []
    for lm in registry.landmarks.values():
        if lm.region == 'Citadel' and lm.id != 'citadel_walls':
            exclusion_zones.append(lm.get_bounds(padding=padding))
            
    def check_collision(x, y, w, h):
        b_min_x = x - w/2
        b_max_x = x + w/2
        b_min_y = y - h/2
        b_max_y = y + h/2
        
        # Check against Walls
        if b_min_x < min_x or b_max_x > max_x or b_min_y < min_y or b_max_y > max_y:
            return True
            
        # Check against Exclusion Zones
        for ex in exclusion_zones:
            if (b_max_x < ex[0] or b_min_x > ex[2] or 
                b_max_y < ex[1] or b_min_y > ex[3]):
                continue # No collision
            else:
                return True # Collided
        return False

    # Block Generation Strategy
    import random
    random.seed(42) # Deterministic seed
    
    # Grid of potential blocks
    block_size = 15.0 # Updated to 15m to match test sample
    street_width = 4.0
    step = block_size + street_width
    
    # Start top-left
    current_x = min_x + block_size/2
    
    count = 0
    while current_x <= max_x:
        current_y = min_y + block_size/2
        while current_y <= max_y:
            
            # Try to place a block
            if not check_collision(current_x, current_y, block_size, block_size):
                
                # Pick Type: 40% O-Shape (Courtyard), 40% U-Shape, 20% Solid
                roll = random.random()
                
                if roll < 0.2:
                    # Solid
                    features.append(ProceduralFeature(
                        id=f"cit_bldg_{count}", parent_id="citadel_walls", shape="RECT",
                        geometry={'x': current_x, 'y': current_y, 'w': block_size, 'h': block_size},
                        description="Citadel Building Block Solid"
                    ))
                elif roll < 0.6:
                    # O-Shape (Courtyard)
                    features.append(ProceduralFeature(
                        id=f"cit_bldg_{count}_main", parent_id="citadel_walls", shape="RECT",
                        geometry={'x': current_x, 'y': current_y, 'w': block_size, 'h': block_size},
                        description="Citadel Building Block O-Type"
                    ))
                    # Inner Courtyard
                    features.append(ProceduralFeature(
                        id=f"cit_bldg_{count}_court", parent_id="citadel_walls", shape="RECT",
                        geometry={'x': current_x, 'y': current_y, 'w': 5.0, 'h': 5.0},
                        description="Citadel Building Courtyard"
                    ))
                else:
                    # U-Shape
                    rotation = random.choice(['N', 'S', 'E', 'W'])
                    parts = []
                    if rotation == 'N': # Open Top
                        parts = [
                            {'dx': -4.0, 'dy': 0.0, 'w': 4.0, 'h': 12.0},
                            {'dx': 4.0, 'dy': 0.0, 'w': 4.0, 'h': 12.0},
                            {'dx': 0.0, 'dy': 4.0, 'w': 4.0, 'h': 4.0}
                        ]
                    elif rotation == 'S': # Open Bottom
                        parts = [
                            {'dx': -4.0, 'dy': 0.0, 'w': 4.0, 'h': 12.0},
                            {'dx': 4.0, 'dy': 0.0, 'w': 4.0, 'h': 12.0},
                            {'dx': 0.0, 'dy': -4.0, 'w': 4.0, 'h': 4.0}
                        ]
                    elif rotation == 'W': # Open Left
                        parts = [
                            {'dx': 0.0, 'dy': -4.0, 'w': 12.0, 'h': 4.0},
                            {'dx': 0.0, 'dy': 4.0, 'w': 12.0, 'h': 4.0},
                            {'dx': 4.0, 'dy': 0.0, 'w': 4.0, 'h': 4.0}
                        ]
                    elif rotation == 'E': # Open Right
                        parts = [
                            {'dx': 0.0, 'dy': -4.0, 'w': 12.0, 'h': 4.0},
                            {'dx': 0.0, 'dy': 4.0, 'w': 12.0, 'h': 4.0},
                            {'dx': -4.0, 'dy': 0.0, 'w': 4.0, 'h': 4.0}
                        ]
                    
                    for idx, p in enumerate(parts):
                        features.append(ProceduralFeature(
                            id=f"cit_bldg_{count}_u_{idx}", parent_id="citadel_walls", shape="RECT",
                            geometry={'x': current_x + p['dx'], 'y': current_y + p['dy'], 
                                    'w': p['w'], 'h': p['h']},
                            description=f"Citadel Building Block U-Type {rotation}"
                        ))
                
                count += 1
                
            current_y += step
        current_x += step
        
    return features

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Scripts are in src/scripts, data is in src/data
    data_path = os.path.join(base_dir, '..', 'data', 'landmarks.yaml')
    output_path = os.path.join(base_dir, '..', 'data', 'procedural.yaml')
    
    registry = LandmarkRegistry(data_path)
    
    all_features = []
    
    print("Generating Citadel Bastions...")
    bastions = generate_citadel_bastions(registry)
    all_features.extend(bastions)
    
    print("Generating Citadel Interior...")
    interior = generate_citadel_interior(registry)
    all_features.extend(interior)
    
    print(f"Total features: {len(all_features)}")
    print(f"Saving to {output_path}...")
    registry.save_procedural(output_path, all_features)
    print("Done.")

if __name__ == "__main__":
    main()
