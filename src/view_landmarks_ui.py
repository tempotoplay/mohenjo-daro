import tkinter as tk
from tkinter import ttk
import os
from landmark_lib import LandmarkRegistry, Landmark

# Constants
SCALE_PIXELS_PER_METER = 2.0  # Zoom level
PADDING = 50

class LandmarkViewerApp:
    def __init__(self, root, registry):
        self.root = root
        self.root.title("Mohenjo-daro Landmark Viewer")
        self.root.geometry("1000x800")
        
        self.registry = registry
        self.selected_item = None
        self.view_scale = 1.0 # Dynamic zoom capable
        self.offset_x = 0
        self.offset_y = 0

        # Colors
        self.colors = {
            'Citadel': '#E57373',      
            'Lower City': '#81C784',   
            'Natural': '#64B5F6',      
            'Default': '#B0BEC5'      
        }
        
        self.setup_ui()
        self.calculate_bounds()
        self.draw_map()

    def setup_ui(self):
        # Paned Window (Split View)
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel: List
        self.left_frame = ttk.Frame(self.paned, width=300)
        self.paned.add(self.left_frame, weight=1)
        
        ttk.Label(self.left_frame, text="Landmarks").pack(pady=5)
        
        self.tree = ttk.Treeview(self.left_frame, columns=('Region'), show='tree headings')
        self.tree.heading('Region', text='Region')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_list_select)
        
        # Populate List
        regions = {}
        for lm in self.registry.landmarks.values():
            if lm.region not in regions:
                regions[lm.region] = self.tree.insert('', tk.END, text=lm.region, open=True)
            
            self.tree.insert(regions[lm.region], tk.END, iid=lm.id, text=lm.name, values=(lm.region,))

        # Right Panel: Canvas
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=3)
        
        self.canvas = tk.Canvas(self.right_frame, bg="#F5F5F5")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Mouse interactions
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<MouseWheel>', self.on_zoom)

    def calculate_bounds(self):
        lms = list(self.registry.landmarks.values())
        if not lms: 
            return
            
        self.min_x = min(lm.abs_x - max(lm.dimensions.width, lm.dimensions.diameter)/2 for lm in lms)
        self.max_x = max(lm.abs_x + max(lm.dimensions.width, lm.dimensions.diameter)/2 for lm in lms)
        self.min_y = min(lm.abs_y - max(lm.dimensions.length, lm.dimensions.diameter)/2 for lm in lms)
        self.max_y = max(lm.abs_y + max(lm.dimensions.length, lm.dimensions.diameter)/2 for lm in lms)
        
        self.world_w = self.max_x - self.min_x
        self.world_h = self.max_y - self.min_y
        
        # Initial fit
        # We want to fit world_w * s < canvas_w
        # Lets just start with 1:2
        self.view_scale = 1.5

    def world_to_screen(self, wx, wy):
        # Center world 0,0 is arbitrary.
        # Let's map min_x, min_y to PADDING, max_y (since Y flip)
        
        sx = (wx - self.min_x) * self.view_scale + PADDING + self.offset_x
        sy = (self.max_y - wy) * self.view_scale + PADDING + self.offset_y
        return sx, sy

    def draw_map(self):
        self.canvas.delete("all")
        
        for lm in self.registry.landmarks.values():
            cx, cy = self.world_to_screen(lm.abs_x, lm.abs_y)
            color = self.colors.get(lm.region, self.colors['Default'])
            
            # Highlight selection
            outline = "black"
            width = 1
            if self.selected_item == lm.id:
                outline = "red"
                width = 3
                
            tag = lm.id
            
            if lm.shape == 'CIRCLE':
                r = (lm.dimensions.diameter / 2) * self.view_scale
                self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline=outline, width=width, tags=(tag, "landmark"))
                
            elif lm.shape == 'CURVE' and 'river' in lm.id:
                 w = lm.dimensions.width * self.view_scale
                 l = lm.dimensions.length * self.view_scale
                 self.canvas.create_rectangle(cx-w/2, cy-l/2, cx+w/2, cy+l/2, fill=color, outline=outline, width=width, stipple="gray50", tags=(tag, "landmark"))

            elif lm.shape == 'RECT_COMPLEX' and 'bath' in lm.id:
                w = lm.dimensions.width * self.view_scale
                l = lm.dimensions.length * self.view_scale
                self.canvas.create_rectangle(cx-w/2, cy-l/2, cx+w/2, cy+l/2, fill=color, outline=outline, width=width, tags=(tag, "landmark"))
                
                # Pool
                pw = lm.dimensions.pool_w * self.view_scale
                pl = lm.dimensions.pool_l * self.view_scale
                self.canvas.create_rectangle(cx-pw/2, cy-pl/2, cx+pw/2, cy+pl/2, fill="#4DD0E1", tags=(tag, "landmark"))

            else:
                 w = lm.dimensions.width * self.view_scale
                 l = lm.dimensions.length * self.view_scale
                 self.canvas.create_rectangle(cx-w/2, cy-l/2, cx+w/2, cy+l/2, fill=color, outline=outline, width=width, tags=(tag, "landmark"))

            # Label (only if zoomed in enough or selected)
            if self.view_scale > 1.0 or self.selected_item == lm.id:
                self.canvas.create_text(cx, cy, text=lm.name, font=("Arial", 10), fill="black")

    def on_list_select(self, event):
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            # Check if it's a landmark (not a region folder)
            if item_id in self.registry.landmarks:
                self.selected_item = item_id
                self.draw_map()
                
                # Auto center (optional)
                lm = self.registry.landmarks[item_id]
                # TODO: Implement auto-pan to selection

    def on_canvas_click(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        
        # Simple hit detection
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if tags and len(tags) > 0:
            lid = tags[0]
            if lid in self.registry.landmarks:
                self.selected_item = lid
                # Select in tree
                try:
                    self.tree.see(lid)
                    self.tree.selection_set(lid)
                except:
                    pass
                self.draw_map()

    def on_canvas_drag(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.draw_map()
        
    def on_zoom(self, event):
        # Windows/Mac difference in delta
        if event.delta > 0:
            self.view_scale *= 1.1
        else:
            self.view_scale *= 0.9
        self.draw_map()

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'landmarks.yaml')
    
    registry = LandmarkRegistry(data_path)
    
    root = tk.Tk()
    app = LandmarkViewerApp(root, registry)
    root.mainloop()

if __name__ == "__main__":
    main()
