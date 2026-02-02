import argparse
import os
import sys
import math
from typing import List, Dict, Optional

# Add src/ to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mohenjo.registry import LandmarkRegistry
from mohenjo.generators import generate_rich_zone, generate_poor_zone

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

    def render(self, output_path: str, target_id: Optional[str] = None, region: Optional[str] = None, custom_list: Optional[List] = None):
        if custom_list:
            to_render = custom_list
        elif target_id:
            to_render = [self.registry.landmarks[target_id]]
        elif region:
            to_render = [lm for lm in self.registry.landmarks.values() if lm.region == region]
        else:
            to_render = list(self.registry.landmarks.values())
            
        if not to_render:
            print(f"No landmarks to render (Target ID: {target_id}, Region: {region}).")
            return

        # Calculate bounding box
        if not to_render:
            print("To Render List is Empty!")
            return

        min_x = min(lm.abs_x - (lm.dimensions.width/2 + lm.dimensions.diameter/2) for lm in to_render)
        max_x = max(lm.abs_x + (lm.dimensions.width/2 + lm.dimensions.diameter/2) for lm in to_render)
        min_y = min(lm.abs_y - (lm.dimensions.length/2 + lm.dimensions.diameter/2) for lm in to_render)
        max_y = max(lm.abs_y + (lm.dimensions.length/2 + lm.dimensions.diameter/2) for lm in to_render)

        print(f"DEBUG: Rendering {len(to_render)} landmarks.")
        print(f"DEBUG: World Bounds: X[{min_x:.1f}, {max_x:.1f}] Y[{min_y:.1f}, {max_y:.1f}]")
        # print(f"DEBUG: IDs: {[lm.id for lm in to_render]}") 

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
                
            elif lm.shape == 'OVAL':
                rx = (lm.dimensions.width / 2) * SCALE_PIXELS_PER_METER
                ry = (lm.dimensions.length / 2) * SCALE_PIXELS_PER_METER
                svg_lines.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}" stroke="black" opacity="0.8" />')
                svg_lines.append(f'<title>{lm.name}</title>')

            elif lm.shape == 'RECT_COMPLEX':
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                
                # Base rect
                svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="black" />')
                
                if 'bath' in lm.id:
                    pw = lm.dimensions.pool_w * SCALE_PIXELS_PER_METER
                    pl = lm.dimensions.pool_l * SCALE_PIXELS_PER_METER
                    svg_lines.append(f'<rect x="{cx - pw/2}" y="{cy - pl/2}" width="{pw}" height="{pl}" fill="#4DD0E1" stroke="black" />')
                elif 'college' in lm.id:
                    # Courtyard
                    cw = getattr(lm.dimensions, 'courtyard_w', 10) * SCALE_PIXELS_PER_METER
                    cl = getattr(lm.dimensions, 'courtyard_l', 10) * SCALE_PIXELS_PER_METER
                    svg_lines.append(f'<rect x="{cx - cw/2}" y="{cy - cl/2}" width="{cw}" height="{cl}" fill="#F5F5F5" stroke="black" opacity="0.7" />')

            elif lm.id == 'citadel_walls':
                 w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                 l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                 # Main Platform (Base) - Walls are now separate segments
                 svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="none" opacity="0.3" />')
                 
                 # Bastions now rendered via procedural features

            elif lm.shape == 'RECT_GRID' or lm.shape == 'SQUARE_GRID':
                w = lm.dimensions.width * SCALE_PIXELS_PER_METER
                l = lm.dimensions.length * SCALE_PIXELS_PER_METER
                
                # Base background
                svg_lines.append(f'<rect x="{cx - w/2}" y="{cy - l/2}" width="{w}" height="{l}" fill="{color}" stroke="black" />')
                
                # Draw grid if specified
                rows = getattr(lm.dimensions, 'grid_rows', 0)
                cols = getattr(lm.dimensions, 'grid_cols', 0)
                
                if rows > 0 and cols > 0:
                    cell_w = w / cols
                    cell_h = l / rows
                    
                    for r in range(rows):
                        for c in range(cols):
                            cell_x = (cx - w/2) + c * cell_w
                            cell_y = (cy - l/2) + r * cell_h
                            # Small gap to show grid
                            gap = 1
                            svg_lines.append(f'<rect x="{cell_x + gap}" y="{cell_y + gap}" width="{cell_w - gap*2}" height="{cell_h - gap*2}" fill="none" stroke="black" stroke-width="0.5" opacity="0.5" />')

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

        # Render Procedural Features (Bastions etc)
        # Assuming we filter these by region/parent if needed, but for now allow all if parent is rendered?
        # Or just render all loaded features if we are in relevant region.
        # Let's check parent_id against to_render IDs.
        rendered_ids = set(lm.id for lm in to_render)
        
        for pf in self.registry.procedural_features:
            if pf.parent_id not in rendered_ids:
                continue
                
            if pf.shape == 'RECT':
                # Geometry is in METERS, need to convert to SVG pixels
                # geometry={'x': current_x, 'y': y_start, 'w': bastion_w, 'h': bastion_l}
                
                # Careful: pf.geometry['x'] is world X.
                # world_to_svg handles the flip and scale.
                
                px, py = world_to_svg(pf.geometry['x'], pf.geometry['y'])
                
                # Height/Width in pixels
                pw = pf.geometry['w'] * SCALE_PIXELS_PER_METER
                pl = pf.geometry['h'] * SCALE_PIXELS_PER_METER
                
                # Let's assume X/Y is center for simplicity in world_to_svg
                
                fill_color = "#8D6E63" # Distinct Brown/Red
                stroke_color = "black"
                stroke_width = "1"
                opacity = "1.0"
                
                if "Courtyard" in pf.description:
                    fill_color = "#E0E0E0" # darker grey to stand out from background
                    stroke_color = "none"
                    opacity = "1.0"
                elif "Building" in pf.description:
                     fill_color = "#EF5350" # Brighter Red
                
                svg_lines.append(f'<rect x="{px - pw/2}" y="{py - pl/2}" width="{pw}" height="{pl}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity}" />')

        # [Collision Detection Preparation]
        # Identify Obstacles (Streets, specific landmarks)
        obstacles = []
        # print("Identifying Obstacles for Collision Detection...")
        for lm in self.registry.landmarks.values():
            if "street" in lm.id or "lane" in lm.id or "house" in lm.id:
                if "zone" in lm.id: continue
                
                w = lm.dimensions.width
                l = lm.dimensions.length
                obs_min_x = lm.abs_x - w/2
                obs_max_x = lm.abs_x + w/2
                obs_min_y = lm.abs_y - l/2
                obs_max_y = lm.abs_y + l/2
                obstacles.append((obs_min_x, obs_max_x, obs_min_y, obs_max_y))

        def check_collision(poly_points_global, obstacles):
            p_xs = [p[0] for p in poly_points_global]
            p_ys = [p[1] for p in poly_points_global]
            p_min_x, p_max_x = min(p_xs), max(p_xs)
            p_min_y, p_max_y = min(p_ys), max(p_ys)
            
            for (o_min_x, o_max_x, o_min_y, o_max_y) in obstacles:
                if (p_min_x < o_max_x and p_max_x > o_min_x and
                    p_min_y < o_max_y and p_max_y > o_min_y):
                    return True
            return False

        # Identify rendered zones
        for lm in to_render:
             if "zone" in lm.shape.lower():
                 # Generate houses
                 houses = []
                 if "rich" in lm.id:
                     houses = generate_rich_zone(lm.dimensions.width, lm.dimensions.length)
                 elif "poor" in lm.id:
                     houses = generate_poor_zone(lm.dimensions.width, lm.dimensions.length)
                 
                 zone_w_m = lm.dimensions.width
                 zone_l_m = lm.dimensions.length
                 
                 # Calculate World Top-Left
                 world_tl_x = lm.abs_x - zone_w_m / 2
                 world_tl_y = lm.abs_y + zone_l_m / 2 # Max Y
                 
                 # Iterate houses
                 for h in houses:
                     # Calculate Global Points in Meters
                     global_points = []
                     for (hx, hy) in h.points:
                         wx = world_tl_x + hx
                         wy = world_tl_y - hy
                         global_points.append((wx, wy))
                     
                     # Collision Check
                     if check_collision(global_points, obstacles):
                         continue

                     poly_points = []
                     for (wx, wy) in global_points:
                         sx, sy = world_to_svg(wx, wy)
                         poly_points.append(f"{sx},{sy}")
                     
                     points_str = " ".join(poly_points)
                     
                     # Styling
                     fill = "#BCAAA4" # Light Brown
                     stroke = "none"
                     if h.category == "RICH_WALL":
                         fill = "#8D6E63"
                     elif h.category == "COURTYARD":
                         fill = "#F5F5F5" # Same as ground
                         stroke = "#5D4037"
                         stroke_width = "0.5"
                     elif h.category == "POOR":
                         fill = "#A1887F"
                         stroke = "black"
                         stroke_width = "0.5"
                         
                     svg_lines.append(f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" />')

        svg_lines.append('</svg>')
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(svg_lines))
        print(f"Generated map at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="VerifyMohenjo-daro Landmarks")
    parser.add_argument('--all', action='store_true', help="Render all landmarks")
    parser.add_argument('--id', type=str, help="Render specific landmark by ID")
    parser.add_argument('--region', type=str, help="Render landmarks by Region")
    parser.add_argument('--match', type=str, help="Render landmarks containing string in ID")
    
    # Default output should be relative to where script is run, but let's make it go to outputs/ if CWD is root
    # Ideally, just default='outputs/landmark_map.svg' if running from root.
    parser.add_argument('--output', type=str, default='outputs/landmark_map.svg', help="Output SVG file")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Scripts in src/scripts, data in src/data
    data_path = os.path.join(base_dir, '..', 'data', 'landmarks.yaml')
    procedural_path = os.path.join(base_dir, '..', 'data', 'procedural.yaml')
    
    registry = LandmarkRegistry(data_path, procedural_path)
    renderer = LandmarkRenderer(registry)
    
    if args.id:
        if args.id not in registry.landmarks:
            print(f"Error: Landmark ID '{args.id}' not found.")
            return
        renderer.render(args.output, target_id=args.id)
    elif args.match:
        # Custom matching logic
        to_render = [lm for lm in registry.landmarks.values() if args.match in lm.id]
        if not to_render:
            print(f"No landmarks matched '{args.match}'")
            return
        renderer.render(args.output, custom_list=to_render)
    elif args.region:
        renderer.render(args.output, region=args.region)
    else:
        renderer.render(args.output)

if __name__ == "__main__":
    main()
