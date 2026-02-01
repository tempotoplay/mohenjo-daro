import argparse
import os
import math
from typing import List, Dict, Optional
from landmark_lib import LandmarkRegistry

# Constants
SCALE_PIXELS_PER_METER = 2.0  # 1 meter = 2 pixels in SVG
PADDING = 100  # Padding around the map in generated SVG

class LandmarkRenderer:
    def __init__(self, registry: LandmarkRegistry):
        self.registry = registry
        self.colors = {
            'Citadel': '#E57373',      # Red-ish
            'Lower City': '#81C784',   # Green-ish
            'Natural': '#64B5F6',      # Blue
            'Site': 'none',            # Transparent
            'Default': '#B0BEC5'       # Grey
        }

    def render(self, output_path: str, target_id: Optional[str] = None, region: Optional[str] = None):
        if target_id:
            to_render = [self.registry.landmarks[target_id]]
        elif region:
            to_render = [lm for lm in self.registry.landmarks.values() if lm.region == region]
        else:
            to_render = list(self.registry.landmarks.values())
            
        if not to_render:
            print(f"No landmarks to render (Target ID: {target_id}, Region: {region}).")
            return

        # Calculate bounding box
        min_x = min(lm.abs_x - (lm.dimensions.width/2 + lm.dimensions.diameter/2) for lm in to_render)
        max_x = max(lm.abs_x + (lm.dimensions.width/2 + lm.dimensions.diameter/2) for lm in to_render)
        min_y = min(lm.abs_y - (lm.dimensions.length/2 + lm.dimensions.diameter/2) for lm in to_render)
        max_y = max(lm.abs_y + (lm.dimensions.length/2 + lm.dimensions.diameter/2) for lm in to_render)

        # SVG ViewBox logic
        # Map World (min_x, min_y) -> SVG (PADDING, height-PADDING)
        # World Y is Up+, SVG Y is Down+
        
        width_m = max_x - min_x
        height_m = max_y - min_y
        
        # Ensure minimum size to avoid divide by zero or tiny SVGs
        if width_m < 1: width_m = 100
        if height_m < 1: height_m = 100
        
        svg_w = width_m * SCALE_PIXELS_PER_METER + (PADDING * 2)
        svg_h = height_m * SCALE_PIXELS_PER_METER + (PADDING * 2)
        
        # Transform functions
        def world_to_svg(wx, wy):
            sx = (wx - min_x) * SCALE_PIXELS_PER_METER + PADDING
            # Flip Y: Max Y in world is PADDING top in SVG
            sy = (max_y - wy) * SCALE_PIXELS_PER_METER + PADDING
            return sx, sy

        svg_lines = []
        svg_lines.append(f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">')
        svg_lines.append(f'<rect width="100%" height="100%" fill="#F5F5F5" />')
        
        # Grid lines (optional, every 100m)
        
        # Sort by area (large first) so big things like walls don't cover small things
        # Exception: Site boundaries should be drawn? Actually if transparent they can be anywhere, 
        # but if we want labels on top, maybe order matters. 
        # Let's keep large first but handle transparency.
        to_render.sort(key=lambda x: x.dimensions.width * x.dimensions.length if x.shape != 'CIRCLE' else 3.14 * (x.dimensions.diameter/2)**2, reverse=True)
        
        labels = []

        for lm in to_render:
            cx, cy = world_to_svg(lm.abs_x, lm.abs_y)
            color = self.colors.get(lm.region, self.colors['Default'])
            
            svg_lines.append(f'<!-- {lm.name} ({lm.id}) -->')

            # Common styling for Site
            stroke_args = 'stroke="black" stroke-width="2"'
            if lm.region == 'Site':
                stroke_args = 'stroke="#9E9E9E" stroke-width="2" stroke-dasharray="10,5" fill="none"'
                color = "none" # Ensure fill is none
            
            if lm.shape == 'CIRCLE':
                r = (lm.dimensions.diameter / 2) * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" {stroke_args} opacity="0.8">')
                svg_lines.append(f'<title>{lm.name}</title>')
                svg_lines.append('</circle>')
                
            elif lm.shape == 'CURVE' and 'river' in lm.id:
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" opacity="0.6" />')
                
            elif lm.shape == 'RECT_COMPLEX' and 'bath' in lm.id:
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="black" />')
                
                pw = lm.dimensions.pool_w * SCALE_PIXELS_PER_METER
                pl = lm.dimensions.pool_l * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<rect x="{cx - pw/2}" y="{cy - pl/2}" width="{pw}" height="{pl}" fill="#4DD0E1" stroke="black" />')
            
            elif lm.id == 'citadel_walls':
                 w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                 l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                 # Main Platform
                 svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="#5D4037" stroke-width="3" opacity="0.5" />')
                 
                 # Bastions (Procedural)
                 bastion_w = 5 * SCALE_PIXELS_PER_METER
                 bastion_l = 5 * SCALE_PIXELS_PER_METER
                 interval = 30 * SCALE_PIXELS_PER_METER
                 
                 # Calculate corners
                 x_start = cx - w/2
                 x_end = cx + w/2
                 y_start = cy - l/2
                 y_end = cy + l/2
                 
                 bastions = []
                 # Top & Bottom edges
                 current_x = x_start
                 while current_x <= x_end:
                     bastions.append((current_x - bastion_w/2, y_start - bastion_l/2)) # Top
                     bastions.append((current_x - bastion_w/2, y_end - bastion_l/2))   # Bottom
                     current_x += interval
                     
                 # Left & Right edges
                 current_y = y_start
                 while current_y <= y_end:
                    bastions.append((x_start - bastion_w/2, current_y - bastion_l/2)) # Left
                    bastions.append((x_end - bastion_w/2, current_y - bastion_l/2))   # Right
                    current_y += interval
                    
                 for bx, by in bastions:
                     svg_lines.append(f'<rect x="{bx}" y="{by}" width="{bastion_w}" height="{bastion_l}" fill="#5D4037" stroke="none" opacity="0.8" />')

            elif lm.shape == 'LINE':
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="#424242" />')

            elif lm.shape == 'RECT_BORDER':
                 # Transparent boundary (dashed)
                 w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                 l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                 svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-dasharray="10,5" />')

            else:
                # Generic Rect (Filled)
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                
                # If site boundary is used without RECT_BORDER shape (legacy check)
                if lm.region == 'Site':
                     svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-dasharray="10,5" />')
                else:
                     svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="black" stroke-width="2" />')

            # Label
            # Store label for later rendering to avoid overlaps
            label_width = len(lm.name) * 7 # Approx width
            label_height = 14
            labels.append({
                'text': lm.name,
                'x': cx,
                'y': cy,
                'w': label_width,
                'h': label_height,
                'id': lm.id
            })

        # Render labels with naive collision avoidance
        placed_labels = []
        for label in labels:
            lx, ly = label['x'], label['y']
            lw, lh = label['w'], label['h']
            
            # Simple "move down" strategy
            max_attempts = 10
            for _ in range(max_attempts):
                collision = False
                # Define current box (centered on lx, ly)
                l_min_x = lx - lw/2
                l_max_x = lx + lw/2
                l_min_y = ly - lh/2
                l_max_y = ly + lh/2
                
                for pl in placed_labels:
                    p_min_x = pl['x'] - pl['w']/2 - 2 # buffer
                    p_max_x = pl['x'] + pl['w']/2 + 2
                    p_min_y = pl['y'] - pl['h']/2 - 2
                    p_max_y = pl['y'] + pl['h']/2 + 2
                    
                    if (l_min_x < p_max_x and l_max_x > p_min_x and
                        l_min_y < p_max_y and l_max_y > p_min_y):
                        collision = True
                        break
                
                if collision:
                    ly += lh # Move down
                else:
                    break
            
            placed_labels.append({'x': lx, 'y': ly, 'w': lw, 'h': lh})
            svg_lines.append(f'<text x="{lx}" y="{ly}" font-family="Arial" font-size="12" text-anchor="middle" fill="black" stroke="white" stroke-width="0.5" paint-order="stroke">{label["text"]}</text>')

        svg_lines.append('</svg>')
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(svg_lines))
        print(f"Generated map at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="VerifyMohenjo-daro Landmarks")
    parser.add_argument('--all', action='store_true', help="Render all landmarks")
    parser.add_argument('--id', type=str, help="Render specific landmark by ID")
    parser.add_argument('--region', type=str, help="Render landmarks by Region")
    parser.add_argument('--output', type=str, default='landmark_map.svg', help="Output SVG file")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'landmarks.yaml')
    
    registry = LandmarkRegistry(data_path)
    renderer = LandmarkRenderer(registry)
    
    if args.id:
        if args.id not in registry.landmarks:
            print(f"Error: Landmark ID '{args.id}' not found.")
            return
        renderer.render(args.output, target_id=args.id)
    elif args.region:
        renderer.render(args.output, region=args.region)
    else:
        renderer.render(args.output)

if __name__ == "__main__":
    main()
