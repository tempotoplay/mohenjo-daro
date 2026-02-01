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

class LandmarkRegistry:
    def __init__(self, yaml_path: str):
        self.landmarks: Dict[str, Landmark] = {}
        self.load_landmarks(yaml_path)
        self.resolve_coordinates()

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
                diameter=dims_data.get('diameter', 0)
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
                    gap = 20 # Arbitrary gap in meters
                    
                    # Calculate position based on direction and sizes
                    # Assuming X=East+, Y=North+ (Standard Graph)
                    # Note: SVG Y is down, will handle in render
                    
                    if direction == 'WEST':
                        # To the left of parent
                        dist = (parent.dimensions.width / 2) + (lm.dimensions.width / 2) + gap
                        lm.abs_x = parent.abs_x - dist
                        lm.abs_y = parent.abs_y
                    elif direction == 'EAST':
                        dist = (parent.dimensions.width / 2) + (lm.dimensions.diameter / 2 if lm.dimensions.diameter else lm.dimensions.width / 2) + gap
                        lm.abs_x = parent.abs_x + dist
                        lm.abs_y = parent.abs_y
                    elif direction == 'NORTH':
                        dist = (parent.dimensions.length / 2) + (lm.dimensions.length / 2) + gap
                        lm.abs_x = parent.abs_x
                        lm.abs_y = parent.abs_y + dist
                    elif direction == 'SOUTH':
                        dist = (parent.dimensions.length / 2) + (lm.dimensions.length / 2) + gap
                        lm.abs_x = parent.abs_x
                        lm.abs_y = parent.abs_y - dist
                        
                    resolved.add(lm.id)
