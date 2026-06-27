import os
import trimesh
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
import json
import struct
from collections import Counter
import numpy as np

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_file_size_str(filepath):
    """Calculates disk file size and formats it into human-readable units (B, KB, MB)."""
    try:
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    except Exception:
        return "N/A"

def check_is_manifold(mesh):
    """Checks if a trimesh geometry is manifold using fast numpy operations (no edge shared by more than two faces)."""
    try:
        counts = np.bincount(mesh.edges_unique_inverse)
        if np.any(counts > 2):
            return "No"
        return "Yes"
    except Exception:
        return "Unknown"

def get_model_metadata(filepath):
    """Detects texture map names and creator software from GLB or OBJ models."""
    ext = os.path.splitext(filepath)[1].lower()
    maps = []
    generator = "Unknown"
    
    if ext == '.glb':
        try:
            with open(filepath, 'rb') as f:
                data = f.read(25000) # Read slightly larger chunk to capture asset details
            if len(data) >= 20 and data[:4] == b'glTF':
                json_len = struct.unpack('<I', data[12:16])[0]
                if json_len > 0:
                    if 20 + json_len > len(data):
                        with open(filepath, 'rb') as f:
                            data = f.read(20 + json_len)
                    json_content = data[20:20+json_len].decode('utf-8', errors='ignore')
                    json_data = json.loads(json_content)
                    
                    # Extract generator software
                    if 'asset' in json_data:
                        generator = json_data['asset'].get('generator', 'Unknown')
                    
                    for img in json_data.get('images', []):
                        name = img.get('name')
                        uri = img.get('uri')
                        mime = img.get('mimeType', '')
                        if name:
                            maps.append(name)
                        elif uri:
                            maps.append(os.path.basename(uri))
                        elif mime:
                            ext_map = mime.split('/')[-1]
                            maps.append(f"embedded.{ext_map}")
                        else:
                            maps.append("embedded_image")
        except Exception as e:
            print(f"Error reading GLB metadata: {e}")
            
    elif ext == '.obj':
        # Check for associated material (.mtl) file
        mtl_path = os.path.splitext(filepath)[0] + ".mtl"
        if os.path.isfile(mtl_path):
            try:
                with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        # Extract creator comment if present at the top of the MTL file
                        if line.startswith('#'):
                            comment = line[1:].strip()
                            if any(word in comment.lower() for word in ['blender', 'substance', 'alias', 'max', 'maya', 'zbrush', '3d', 'exporter', 'rhino']):
                                generator = comment
                        elif line.startswith(('map_Kd', 'map_Bump', 'map_Ks', 'map_d', 'bump', 'map_Ka', 'map_Ns')):
                            parts = line.split()
                            if len(parts) > 1:
                                tex_name = parts[-1]
                                maps.append(os.path.basename(tex_name))
            except Exception as e:
                print(f"Error reading MTL file: {e}")
                
    # Format texture maps with a separate line for each map
    maps_str = "\n".join(dict.fromkeys(maps)) if maps else "None"
    return maps_str, generator

def fast_scan_obj(filepath):
    """Parses vertex/face counts and bounding box dimensions from OBJ text files without loading the mesh."""
    v_count = 0
    f_count = 0
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    has_coords = False
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if len(line) < 3:
                    continue
                c = line[0]
                if c == 'v':
                    if line[1] == ' ':
                        v_count += 1
                        try:
                            parts = line.split()
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            if x < min_x: min_x = x
                            if x > max_x: max_x = x
                            if y < min_y: min_y = y
                            if y > max_y: max_y = y
                            if z < min_z: min_z = z
                            if z > max_z: max_z = z
                            has_coords = True
                        except Exception:
                            pass
                elif c == 'f':
                    if line[1] == ' ':
                        f_count += 1
    except Exception:
        pass
        
    if has_coords:
        dx = max_x - min_x
        dy = max_y - min_y
        dz = max_z - min_z
        bounds_str = f"{dx:.2f} × {dy:.2f} × {dz:.2f}"
    else:
        bounds_str = "Skipped (Large)"
        
    return v_count, f_count, bounds_str

def fast_parse_ply_header(filepath):
    """Fast-parses vertex and face counts from PLY header text without loading the body."""
    v_count = 0
    f_count = 0
    try:
        with open(filepath, 'rb') as f:
            # Read first 4096 bytes which is more than enough for a PLY header
            header_bytes = f.read(4096)
            header_text = header_bytes.decode('utf-8', errors='ignore')
            lines = header_text.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith('element vertex'):
                    v_count = int(line.split()[-1])
                elif line.startswith('element face'):
                    f_count = int(line.split()[-1])
                elif line == 'end_header':
                    break
    except Exception:
        pass
    return v_count, f_count

def fast_parse_stl_count(filepath):
    """Fast-parses face and vertex counts from binary STL file triangle count buffer."""
    try:
        with open(filepath, 'rb') as f:
            f.seek(80)
            count_bytes = f.read(4)
            if len(count_bytes) == 4:
                num_triangles = struct.unpack('<I', count_bytes)[0]
                return num_triangles * 3, num_triangles
    except Exception:
        pass
    return 0, 0


class MeshAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("3D Mesh Analyzer | Extract Geometry Metadata")
        self.geometry("1400x700")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.select_all_var = ctk.BooleanVar(value=True)
        self.found_files = []  # list of dicts: {"path", "filename", "format", "chk_var", "widgets", "vertices", "faces", "watertight", "manifold", "size", "bounds", "maps", "creator"}
        self.gui_queue = queue.Queue()
        self.is_scanning = False
        self.is_analyzing = False
        
        # Configure layout grids on root window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Allow files frame/list to grow
        
        # Header Section Frame (Title + Dark Mode Switch)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        # Title and Subtitle
        self.title_col = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_col.grid(row=0, column=0, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.title_col, 
            text="3D Mesh Analyzer", 
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Geometric Metadata Extractor for OBJ, STL, GLB & PLY", 
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Toggle Switch for Dark Mode
        initial_mode = ctk.get_appearance_mode()
        self.switch_var = ctk.StringVar(value=initial_mode)
        
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            variable=self.switch_var,
            onvalue="Dark",
            offvalue="Light",
            font=ctk.CTkFont(size=14)
        )
        self.theme_switch.grid(row=0, column=1, sticky="e", pady=5)
        
        # Path Selection Frame
        self.path_frame = ctk.CTkFrame(self.main_frame)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="1. Select Target Folder containing 3D models", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 2))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Choose a folder path containing 3D files...",
            font=("Helvetica", 14)
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(15, 10), pady=(0, 15))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=120, 
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e", padx=(0, 15), pady=(0, 15))
        
        # Controls Frame (Buttons)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=0)
        self.controls_frame.grid_columnconfigure(1, weight=0)
        self.controls_frame.grid_columnconfigure(2, weight=1)
        
        self.scan_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Scan Folder", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_scan_thread,
            width=150
        )
        self.scan_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.analyze_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Analyze Geometry", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_analysis_thread,
            state="disabled",
            width=180
        )
        self.analyze_btn.grid(row=0, column=1, sticky="w")
        
        # Files container frame
        self.files_container = ctk.CTkFrame(self.main_frame)
        self.files_container.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.files_container.grid_columnconfigure(0, weight=1)
        self.files_container.grid_rowconfigure(0, weight=1) # Scroll frame expands
        
        # Scrollable Frame for file list
        self.scroll_frame = ctk.CTkScrollableFrame(self.files_container, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure strict columns configuration directly on scroll frame to ensure alignment
        self.scroll_frame.grid_columnconfigure(0, weight=0, minsize=40)  # Checkbox
        self.scroll_frame.grid_columnconfigure(1, weight=0, minsize=200) # Filename
        self.scroll_frame.grid_columnconfigure(2, weight=0, minsize=55)  # Format
        self.scroll_frame.grid_columnconfigure(3, weight=0, minsize=75)  # Vertices
        self.scroll_frame.grid_columnconfigure(4, weight=0, minsize=75)  # Faces
        self.scroll_frame.grid_columnconfigure(5, weight=0, minsize=75)  # Watertight
        self.scroll_frame.grid_columnconfigure(6, weight=0, minsize=75)  # Manifold
        self.scroll_frame.grid_columnconfigure(7, weight=0, minsize=75)  # Size
        self.scroll_frame.grid_columnconfigure(8, weight=0, minsize=220) # Bounding Box (increased)
        self.scroll_frame.grid_columnconfigure(9, weight=0, minsize=400) # Texture Maps (increased)
        
        # Create initial headers and placeholder
        self.create_headers()
        self.show_placeholder()
        
        # Status & Progress Frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            self.status_frame, 
            text="Status: Idle", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.progress_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self.status_frame)
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0.0)
        
        # Start GUI queue consumer
        self.process_queue()

    def create_headers(self):
        """Creates the headers directly inside the scrollable frame for perfect vertical alignment."""
        self.select_all_cb = ctk.CTkCheckBox(
            self.scroll_frame, 
            text="", 
            variable=self.select_all_var, 
            command=self.toggle_select_all,
            width=20
        )
        self.select_all_cb.grid(row=0, column=0, sticky="w", padx=(10, 10), pady=10)
        
        headers = [
            ("Filename", 200, 1),
            ("Format", 55, 2),
            ("Vertices", 75, 3),
            ("Faces", 75, 4),
            ("Watertight", 75, 5),
            ("Manifold", 75, 6),
            ("Size", 75, 7),
            ("Bounding Box", 220, 8),
            ("Texture Maps", 400, 9)
        ]
        for text, w, col in headers:
            lbl = ctk.CTkLabel(self.scroll_frame, text=text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w", width=w)
            lbl.grid(row=0, column=col, sticky="w", padx=5, pady=10)

    def show_placeholder(self):
        self.lbl_placeholder = ctk.CTkLabel(
            self.scroll_frame, 
            text="No folder scanned yet. Choose a folder and click 'Scan Folder'.", 
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="gray"
        )
        self.lbl_placeholder.grid(row=1, column=0, columnspan=10, pady=30, sticky="ew")

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def toggle_select_all(self):
        val = self.select_all_var.get()
        for item in self.found_files:
            item["chk_var"].set(val)

    def update_select_all_state(self):
        if not self.found_files:
            self.select_all_var.set(False)
            return
        all_checked = all(item["chk_var"].get() for item in self.found_files)
        self.select_all_var.set(all_checked)

    def start_scan_thread(self):
        folder = self.target_path.get()
        if not folder or not os.path.isdir(folder):
            # If path entry is empty, run browser dialog
            folder = filedialog.askdirectory()
            if not folder: return
            self.target_path.set(folder)
            
        self.scan_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.is_scanning = True
        self.progress_label.configure(text="Status: Scanning...")
        self.progress.set(0.0)
        
        # Clear scroll frame and rebuild headers
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.create_headers()
        self.found_files = []
        
        threading.Thread(target=self.scan_folder_worker, args=(folder,), daemon=True).start()

    def scan_folder_worker(self, path):
        try:
            compat_files = []
            for root, _, files in os.walk(path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ('.obj', '.stl', '.glb', '.ply'):
                        compat_files.append(os.path.join(root, f))
            
            total_files = len(compat_files)
            if total_files == 0:
                self.gui_queue.put({"action": "scan_complete", "count": 0})
                return
                
            for i, full_path in enumerate(compat_files):
                filename = os.path.basename(full_path)
                ext = os.path.splitext(filename)[1].upper().replace('.', '')
                
                # Push file to main GUI thread
                self.gui_queue.put({
                    "action": "add_file",
                    "path": full_path,
                    "filename": filename,
                    "format": ext,
                    "progress": (i + 1) / total_files
                })
            
            self.gui_queue.put({"action": "scan_complete", "count": total_files})
        except Exception as e:
            self.gui_queue.put({"action": "error", "message": f"Scan failed: {e}"})

    def add_file_row(self, full_path, filename, fmt):
        # row_idx is len(found_files) + 1 because headers row is at index 0
        row_idx = len(self.found_files) + 1
        chk_var = ctk.BooleanVar(value=True)
        
        # Individual Checkbox
        chk = ctk.CTkCheckBox(
            self.scroll_frame, 
            text="", 
            variable=chk_var, 
            command=self.update_select_all_state,
            width=20
        )
        chk.grid(row=row_idx, column=0, sticky="nw", padx=(10, 10), pady=5)
        
        # Truncate filename display to 30 characters to keep columns perfectly aligned
        display_name = filename
        if len(display_name) > 30:
            display_name = display_name[:17] + "..." + display_name[-10:]
            
        # Labels configured with strict widths matching header sizes
        lbl_file = ctk.CTkLabel(self.scroll_frame, text=display_name, anchor="w", font=ctk.CTkFont(size=13), width=200)
        lbl_file.grid(row=row_idx, column=1, sticky="nw", padx=5, pady=5)
        
        lbl_format = ctk.CTkLabel(self.scroll_frame, text=fmt, anchor="w", font=ctk.CTkFont(size=13, weight="bold"), width=55)
        lbl_format.grid(row=row_idx, column=2, sticky="nw", padx=5, pady=5)
        
        lbl_vertices = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=75)
        lbl_vertices.grid(row=row_idx, column=3, sticky="nw", padx=5, pady=5)
        
        lbl_faces = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=75)
        lbl_faces.grid(row=row_idx, column=4, sticky="nw", padx=5, pady=5)
        
        lbl_watertight = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=75)
        lbl_watertight.grid(row=row_idx, column=5, sticky="nw", padx=5, pady=5)
        
        lbl_manifold = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=75)
        lbl_manifold.grid(row=row_idx, column=6, sticky="nw", padx=5, pady=5)
        
        lbl_size = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=75)
        lbl_size.grid(row=row_idx, column=7, sticky="nw", padx=5, pady=5)
        
        lbl_bounds = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=220)
        lbl_bounds.grid(row=row_idx, column=8, sticky="nw", padx=5, pady=5)
        
        # Multi-line labels for Texture maps (newline-separated, no wrapping, 400px width)
        lbl_maps = ctk.CTkLabel(self.scroll_frame, text="Pending...", anchor="w", font=ctk.CTkFont(size=12), text_color="gray", width=400, justify="left")
        lbl_maps.grid(row=row_idx, column=9, sticky="nw", padx=5, pady=5)
        
        self.found_files.append({
            "path": full_path,
            "filename": filename,
            "format": fmt,
            "chk_var": chk_var,
            "widgets": [chk, lbl_file, lbl_format, lbl_vertices, lbl_faces, lbl_watertight, lbl_manifold, lbl_size, lbl_bounds, lbl_maps],
            "vertices": None,
            "faces": None,
            "watertight": None,
            "manifold": None,
            "size": None,
            "bounds": None,
            "maps": None,
            "creator": "Unknown"
        })

    def scan_complete(self, count):
        self.is_scanning = False
        self.scan_btn.configure(state="normal")
        self.progress.set(1.0)
        
        if count > 0:
            self.analyze_btn.configure(state="normal")
            self.progress_label.configure(text=f"Status: Found {count} 3D files. Ready to analyze.")
            self.select_all_var.set(True)
        else:
            self.analyze_btn.configure(state="disabled")
            self.progress_label.configure(text="Status: No 3D files found.")
            
            # Show empty label placeholder in scrollframe
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame, 
                text="No compatible 3D model files found (.obj, .stl, .glb, .ply).", 
                font=ctk.CTkFont(size=14, slant="italic"),
                text_color="gray"
            )
            lbl_empty.grid(row=1, column=0, columnspan=10, pady=20, sticky="ew")

    def start_analysis_thread(self):
        selected_files = [item for item in self.found_files if item["chk_var"].get()]
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select at least one file to analyze.")
            return
            
        self.scan_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.is_analyzing = True
        self.progress_label.configure(text="Status: Starting geometric analysis...")
        self.progress.set(0.0)
        
        # Reset selected rows labels to "Analyzing..."
        for item in selected_files:
            for i in range(3, 10):
                item["widgets"][i].configure(text="Analyzing...", text_color="#3b82f6") # Blue indicator
                
        threading.Thread(target=self.analysis_worker, args=(selected_files,), daemon=True).start()

    def write_automatic_report(self, folder, report_rows, report_filename):
        """Writes the Markdown report file with 2-column HTML tables automatically in the target directory."""
        if not folder or not os.path.isdir(folder) or not report_rows:
            return None
        md_path = os.path.join(folder, report_filename)
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# 3D Mesh Analysis Report: {os.path.splitext(report_filename)[0].replace('_report', '')}\n\n")
                for r in report_rows:
                    f.write(f"## Model: {r['Filename']}\n\n")
                    f.write('<table border="0" cellpadding="4" cellspacing="0">\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td width="220"><b>Format</b></td>\n')
                    f.write(f'    <td>{r["Format"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Vertices</b></td>\n')
                    f.write(f'    <td>{r["Vertices"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Faces</b></td>\n')
                    f.write(f'    <td>{r["Faces"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Watertight</b></td>\n')
                    f.write(f'    <td>{r["Watertight"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Manifold</b></td>\n')
                    f.write(f'    <td>{r["Manifold"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>File Size</b></td>\n')
                    f.write(f'    <td>{r["File Size"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Bounding Box (X × Y × Z)</b></td>\n')
                    f.write(f'    <td>{r["Bounding Box (X x Y x Z)"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Texture Maps</b></td>\n')
                    # Clean texture maps newlines to HTML breaks inside table cell
                    maps_md = r["Texture Maps"].replace("\n", "<br>")
                    f.write(f'    <td>{maps_md}</td>\n')
                    f.write('  </tr>\n')
                    f.write('  <tr valign="top">\n')
                    f.write('    <td><b>Creator Software</b></td>\n')
                    f.write(f'    <td>{r["Creator Software"]}</td>\n')
                    f.write('  </tr>\n')
                    f.write('</table>\n\n')
            return md_path
        except Exception as e:
            print(f"Error writing auto Markdown report: {e}")
            return None

    def analysis_worker(self, selected_files):
        total = len(selected_files)
        
        for i, item in enumerate(selected_files):
            filepath = item["path"]
            filename = item["filename"]
            self.gui_queue.put({"action": "update_status", "text": f"Analyzing geometry: {filename}"})
            
            # 1. Fetch file size
            size_str = get_file_size_str(filepath)
            item["size"] = size_str
            
            # 2. Discover texture maps and creator software (non-blocking, fast check)
            maps_str, generator = get_model_metadata(filepath)
            item["maps"] = maps_str
            item["creator"] = generator
            
            # 3. Inspect trimesh geometry properties
            try:
                try:
                    fsize = os.path.getsize(filepath)
                    is_large = fsize > 25 * 1024 * 1024
                except Exception:
                    is_large = False
                    fsize = 0

                ext_lower = os.path.splitext(filepath)[1].lower()
                m_data = None
                
                if is_large and ext_lower in ('.obj', '.ply', '.stl'):
                    # FAST PATH: Parse metadata directly and skip trimesh load
                    self.gui_queue.put({"action": "update_status", "text": f"Scanning large model: {filename} (fast mode...)"})
                    if ext_lower == '.obj':
                        v, f, bounds_str = fast_scan_obj(filepath)
                    elif ext_lower == '.ply':
                        v, f = fast_parse_ply_header(filepath)
                        bounds_str = "Skipped (Large)"
                    elif ext_lower == '.stl':
                        v, f = fast_parse_stl_count(filepath)
                        bounds_str = "Skipped (Large)"
                    else:
                        v, f, bounds_str = 0, 0, "Skipped (Large)"
                    is_watertight = "Skipped (Large)"
                    is_manifold = "Skipped (Large)"
                else:
                    # SLOW PATH: Load via trimesh
                    if fsize > 10 * 1024 * 1024:
                        self.gui_queue.put({"action": "update_status", "text": f"Loading model: {filename} (please wait...)"})
                        
                    load_kwargs = {"force": "mesh", "validate": False, "process": False}
                    if ext_lower == ".obj":
                        load_kwargs["split_object"] = False
                        load_kwargs["skip_materials"] = True
                    m_data = trimesh.load(filepath, **load_kwargs)
                    
                    # Check for scene vs single mesh structures
                    if isinstance(m_data, trimesh.Scene):
                        v = sum(len(g.vertices) for g in m_data.geometry.values())
                        f = sum(len(g.faces) for g in m_data.geometry.values())
                        if v > 500000 or f > 500000:
                            is_watertight = "Skipped (Large)"
                            is_manifold = "Skipped (Large)"
                        else:
                            is_watertight = "Yes" if all(g.is_watertight for g in m_data.geometry.values()) else "No"
                            is_manifold = "Yes" if all(check_is_manifold(g) == "Yes" for g in m_data.geometry.values()) else "No"
                        
                        bounds = m_data.bounds
                        if bounds is not None:
                            dx, dy, dz = bounds[1] - bounds[0]
                            bounds_str = f"{dx:.2f} × {dy:.2f} × {dz:.2f}"
                        else:
                            bounds_str = "N/A"
                    else:
                        v = len(m_data.vertices)
                        f = len(m_data.faces)
                        if v > 500000 or f > 500000:
                            is_watertight = "Skipped (Large)"
                            is_manifold = "Skipped (Large)"
                        else:
                            is_watertight = "Yes" if m_data.is_watertight else "No"
                            is_manifold = check_is_manifold(m_data)
                        
                        dx, dy, dz = m_data.extents
                        bounds_str = f"{dx:.2f} × {dy:.2f} × {dz:.2f}"
                
                # Store statistics in dict
                item["vertices"] = v
                item["faces"] = f
                item["watertight"] = is_watertight
                item["manifold"] = is_manifold
                item["bounds"] = bounds_str
                
                # Push updates to main GUI thread
                self.gui_queue.put({
                    "action": "update_row_success",
                    "path": filepath,
                    "vertices": f"{v:,}" if isinstance(v, int) else str(v),
                    "faces": f"{f:,}" if isinstance(f, int) else str(f),
                    "watertight": is_watertight,
                    "manifold": is_manifold,
                    "size": size_str,
                    "bounds": bounds_str,
                    "maps": maps_str
                })
                
                # Clean up memory context
                if m_data is not None:
                    del m_data
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                item["vertices"] = "Error"
                item["faces"] = "Error"
                item["watertight"] = "Error"
                item["manifold"] = "Error"
                item["bounds"] = "Error"
                
                self.gui_queue.put({
                    "action": "update_row_error",
                    "path": filepath,
                    "error_text": "Error",
                    "size": size_str,
                    "maps": maps_str
                })
                
            self.gui_queue.put({"action": "update_progress", "value": (i + 1) / total})
            
        # Create the automatic Markdown statistics report in the target folder
        folder = self.target_path.get()
        report_rows = []
        for item in self.found_files:
            report_rows.append({
                "Filename": item["filename"],
                "Path": item["path"],
                "Format": item["format"],
                "Vertices": f"{item['vertices']:,}" if isinstance(item["vertices"], int) else (item["vertices"] if item["vertices"] is not None else "Not Analyzed"),
                "Faces": f"{item['faces']:,}" if isinstance(item["faces"], int) else (item["faces"] if item["faces"] is not None else "Not Analyzed"),
                "Watertight": item["watertight"] if item["watertight"] is not None else "Not Analyzed",
                "Manifold": item["manifold"] if item["manifold"] is not None else "Not Analyzed",
                "File Size": item["size"] if item["size"] is not None else "Not Analyzed",
                "Bounding Box (X x Y x Z)": item["bounds"] if item["bounds"] is not None else "Not Analyzed",
                "Texture Maps": item["maps"] if item["maps"] is not None else "Not Analyzed",
                "Creator Software": item["creator"] if item["creator"] is not None else "Unknown"
            })
            
        selected_items = [item for item in self.found_files if item["vertices"] is not None]
        if len(selected_items) == 1:
            obj_name = os.path.splitext(selected_items[0]["filename"])[0]
        else:
            obj_name = os.path.basename(folder)
            if not obj_name:
                obj_name = "mesh_statistics"
        report_filename = f"{obj_name}_report.md"
        auto_report_path = self.write_automatic_report(folder, report_rows, report_filename)
        
        self.gui_queue.put({
            "action": "analysis_complete", 
            "count": total,
            "auto_report": auto_report_path
        })

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                
                if action == "add_file":
                    self.add_file_row(msg["path"], msg["filename"], msg["format"])
                    self.progress.set(msg["progress"])
                    
                elif action == "scan_complete":
                    self.scan_complete(msg["count"])
                    
                elif action == "update_status":
                    self.progress_label.configure(text=msg["text"])
                    
                elif action == "update_progress":
                    self.progress.set(msg["value"])
                    
                elif action == "update_row_success":
                    for item in self.found_files:
                        if item["path"] == msg["path"]:
                            item["widgets"][3].configure(text=msg["vertices"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][4].configure(text=msg["faces"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][5].configure(text=msg["watertight"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][6].configure(text=msg["manifold"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][7].configure(text=msg["size"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][8].configure(text=msg["bounds"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][9].configure(text=msg["maps"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            
                elif action == "update_row_error":
                    for item in self.found_files:
                        if item["path"] == msg["path"]:
                            for i in range(3, 7):
                                item["widgets"][i].configure(text=msg["error_text"], text_color="#ef4444") # Red error text
                            item["widgets"][7].configure(text=msg["size"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                            item["widgets"][8].configure(text=msg["error_text"], text_color="#ef4444")
                            item["widgets"][9].configure(text=msg["maps"], text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
                                
                elif action == "analysis_complete":
                    self.is_analyzing = False
                    self.scan_btn.configure(state="normal")
                    self.analyze_btn.configure(state="normal")
                    self.progress.set(0.0)
                    self.progress_label.configure(text="Status: Ready")
                    
                    finish_msg = f"Successfully analyzed {msg['count']} 3D model files."
                    if msg["auto_report"]:
                        finish_msg += f"\n\nAutomatic Markdown report saved to:\n{os.path.basename(msg['auto_report'])}"
                    messagebox.showinfo("Analysis Done", finish_msg)
                    
                elif action == "error":
                    self.is_scanning = False
                    self.is_analyzing = False
                    self.scan_btn.configure(state="normal")
                    self.progress.set(0.0)
                    self.progress_label.configure(text="Status: Error")
                    messagebox.showerror("Error", msg["message"])
                    
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

if __name__ == "__main__":
    app = MeshAnalyzer()
    app.mainloop()