import yaml
import os
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Dimensions:
    width: float
    length: float
    pool_w: float = 0
    pool_l: float = 0
    diameter: float = 0
    grid_rows: int = 0
    grid_cols: int = 0
    courtyard_w: float = 0
    courtyard_l: float = 0

@dataclass
class ProceduralFeature:
    id: str
    parent_id: str
    shape: str # RECT, POLYGON
    geometry: Dict # {x, y, w, h} or {points: [(x,y), ...]}
    description: str = ""

@dataclass
class Landmark:
    id: str
    name: str
    region: str
    description: str
    dimensions: Dimensions
    height_m: float
    shape: str
    location: Dict
    
    # Calculated absolute position (Center)
    abs_x: float = 0.0
    abs_y: float = 0.0

    def get_bounds(self, padding: float = 0.0) -> Tuple[float, float, float, float]:
        """Returns (min_x, min_y, max_x, max_y) including padding."""
        half_w = (self.dimensions.width / 2) + padding
        half_l = (self.dimensions.length / 2) + padding
        return (
            self.abs_x - half_w,
            self.abs_y - half_l,
            self.abs_x + half_w,
            self.abs_y + half_l
        )

class LandmarkRegistry:
    def __init__(self, yaml_path: str, procedural_path: Optional[str] = None):
        self.landmarks: Dict[str, Landmark] = {}
        self.procedural_features: List[ProceduralFeature] = []
        self.load_landmarks(yaml_path)
        self.resolve_coordinates()
        if procedural_path:
            self.load_procedural(procedural_path)

    def load_landmarks(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Registry not found at {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        for item in data.get('landmarks', []):
            dims_data = item.get('dimensions_m', {})
            dims = Dimensions(
                width=dims_data.get('width', 0),
                length=dims_data.get('length', 0),
                pool_w=dims_data.get('pool_w', 0),
                pool_l=dims_data.get('pool_l', 0),
                diameter=dims_data.get('diameter', 0),
                grid_rows=dims_data.get('grid_rows', 0),
                grid_cols=dims_data.get('grid_cols', 0),
                courtyard_w=dims_data.get('courtyard_w', 0),
                courtyard_l=dims_data.get('courtyard_l', 0)
            )
            
            lm = Landmark(
                id=item['id'],
                name=item['name'],
                region=item.get('region', 'Unknown'),
                description=item.get('description', ''),
                dimensions=dims,
                height_m=item.get('height_m', 0),
                shape=item['shape'],
                location=item.get('location', {})
            )
            self.landmarks[lm.id] = lm
            
    def load_procedural(self, path: str):
        if not os.path.exists(path):
            return
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data: return
            
        for item in data.get('features', []):
            pf = ProceduralFeature(
                id=item['id'],
                parent_id=item['parent_id'],
                shape=item['shape'],
                geometry=item['geometry'],
                description=item.get('description', '')
            )
            self.procedural_features.append(pf)

    def save_procedural(self, path: str, features: List[ProceduralFeature]):
        data = {'features': []}
        for f in features:
            # Convert geometry tuples to lists (safe_yaml compatibility)
            def convert_tuples(obj):
                if isinstance(obj, tuple):
                    return list(obj)
                if isinstance(obj, list):
                    return [convert_tuples(i) for i in obj]
                if isinstance(obj, dict):
                    return {k: convert_tuples(v) for k, v in obj.items()}
                return obj

            safe_geometry = convert_tuples(f.geometry)

            data['features'].append({
                'id': f.id,
                'parent_id': f.parent_id,
                'shape': f.shape,
                'geometry': safe_geometry,
                'description': f.description
            })
            
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def resolve_coordinates(self):
        # First pass: Get absolute coordinates
        # Second pass: Resolve relative coordinates
        # Simple dependency resolution loop
        resolved = set()
        
        # Mark absolute ones as resolved
        for lm in self.landmarks.values():
            if 'grid_x' in lm.location:
                lm.abs_x = float(lm.location['grid_x'])
                lm.abs_y = float(lm.location['grid_y'])
                resolved.add(lm.id)
                
        # Resolve relatives
        # Warning: simplified, assumes no cycles and depth < 10
        for _ in range(5): 
            for lm in self.landmarks.values():
                if lm.id in resolved:
                    continue
                
                rel_to = lm.location.get('relative_to')
                if rel_to and rel_to in resolved:
                    parent = self.landmarks[rel_to]
                    direction = lm.location.get('direction', 'NORTH')
                    
                    # Use explicit offset if provided, else default gap
                    offset_x = lm.location.get('offset_x', 0)
                    offset_y = lm.location.get('offset_y', 0)
                    gap = 20 # Default gap in meters if no offset is used implicitly (logic below)
                    
                    # If offsets are provided, they might be additive to the direction logic or replacement.
                    # Let's treat them as adjustments to the standard directional placement if present.
                    # Or simpler:
                    # If direction is set, place next to it.
                    # offset_x/y serve as fine-tuning "shift".
                    
                    base_x = parent.abs_x
                    base_y = parent.abs_y
                    
                    if direction == 'WEST':
                        dist = (parent.dimensions.width / 2) + (lm.dimensions.width / 2) + gap
                        base_x -= dist
                    elif direction == 'EAST':
                        # Use diameter if valid, else width
                        p_size = parent.dimensions.width / 2 
                        self_size = (lm.dimensions.diameter / 2) if lm.dimensions.diameter else (lm.dimensions.width / 2)
                        dist = p_size + self_size + gap
                        base_x += dist
                    elif direction == 'NORTH':
                        dist = (parent.dimensions.length / 2) + (lm.dimensions.length / 2) + gap
                        base_y += dist
                    elif direction == 'SOUTH':
                        dist = (parent.dimensions.length / 2) + (lm.dimensions.length / 2) + gap
                        base_y -= dist
                        
                    # Apply manual offsets
                    # Only apply 'gap' if offset is NOT specified? 
                    # The YAML used offset_x: 20 INSTEAD of relying on default gap?
                    # "offset_x: 20 # Gap between bath and college"
                    # My previous logic hardcoded gap=20.
                    # So base logic + offset should be fine.
                    # Actually, if I say "offset_x: 20", I probably mean "shift 20m East" 
                    # OR "gap is 20m".
                    # Let's interpret offset_x/y as ADDITIONAL shift from the calculated center.
                    
                    if offset_x: base_x += (offset_x - gap) if direction in ['EAST', 'WEST'] else offset_x
                    if offset_y: base_y += (offset_y - gap) if direction in ['NORTH', 'SOUTH'] else offset_y

                    # Re-simplify:
                    # If I put offset_x: 70 for Stupa (EAST of Bath), I want it 70m away, not 20+70.
                    # Current logic: base position uses gap=20.
                    # If I accept offset key to OVERRIDE gap?
                    # Let's try to interpret "offset_x" as "The specific distance to shift in X".
                    # But direction gives a sign.
                    
                    # Let's stick to: Calculate standard directional position (with gap=20), then ADD offset_x/y.
                    # If user puts offset_x: 20, they add 20m.
                    # In YAML I wrote `offset_x: 20 # Gap between bath and college`.
                    # Since gap=20 is default, adding 20 would make it 40.
                    # I'll rely on the default gap for "College" (since 20 is default).
                    # For Stupa, I put `offset_x: 70`. That would be 20+70 = 90. That's fine.
                    
                    lm.abs_x = base_x
                    lm.abs_y = base_y
                        
                    resolved.add(lm.id)
