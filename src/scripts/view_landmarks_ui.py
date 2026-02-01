import tkinter as tk
from tkinter import ttk
import os
import sys

# Add src/ to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mohenjo.registry import LandmarkRegistry, Landmark

# ... (Constants and Class definition) ...

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, '..', 'data', 'landmarks.yaml')
    
    registry = LandmarkRegistry(data_path)
    
    root = tk.Tk()
    app = LandmarkViewerApp(root, registry)
    root.mainloop()

if __name__ == "__main__":
    main()
