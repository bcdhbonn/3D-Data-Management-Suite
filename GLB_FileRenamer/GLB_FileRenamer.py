import os
import struct
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
import shutil

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GLBMasterManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("GLB Master Manager | Align Internal Names")
        self.geometry("850x700")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.create_backups = ctk.BooleanVar(value=True)
        self.select_all_var = ctk.BooleanVar(value=True)
        self.found_files = []  # list of dicts: {"path", "filename", "internal", "chk_var", "widgets"}
        self.gui_queue = queue.Queue()
        self.is_scanning = False
        self.is_patching = False
        
        # Configure layout grids on root window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Allow files container/list to grow
        
        # Header Section Frame (Title + Dark Mode Switch)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        # Left side of header: Title and Subtitle
        self.title_col = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_col.grid(row=0, column=0, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.title_col, 
            text="GLB Master Manager", 
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Align Internal glTF Metadata Names with Disk Filenames", 
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Right side of header: Toggle Switch for Dark Mode
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
            text="1. Select Target Folder containing GLB files", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 2))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Choose a folder path...",
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
        
        self.patch_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Patch Internal Names", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_patch_thread,
            state="disabled",
            width=180
        )
        self.patch_btn.grid(row=0, column=1, padx=(0, 15), sticky="w")
        
        self.backup_cb = ctk.CTkCheckBox(
            self.controls_frame,
            text="Create backups (.glb.bak)",
            variable=self.create_backups,
            font=ctk.CTkFont(size=14)
        )
        self.backup_cb.grid(row=0, column=2, sticky="e", pady=5)
        
        # Files container frame
        self.files_container = ctk.CTkFrame(self.main_frame)
        self.files_container.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.files_container.grid_columnconfigure(0, weight=1)
        self.files_container.grid_rowconfigure(1, weight=1) # Scroll frame expands
        
        # Files Header Frame
        self.files_header_frame = ctk.CTkFrame(self.files_container, height=40, fg_color="transparent")
        self.files_header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 5))
        self.files_header_frame.grid_columnconfigure(0, weight=0, minsize=50)
        self.files_header_frame.grid_columnconfigure(1, weight=3)
        self.files_header_frame.grid_columnconfigure(2, weight=4)
        
        self.select_all_cb = ctk.CTkCheckBox(
            self.files_header_frame, 
            text="", 
            variable=self.select_all_var, 
            command=self.toggle_select_all,
            width=20
        )
        self.select_all_cb.grid(row=0, column=0, sticky="w", padx=(5, 0))
        
        self.hdr_file = ctk.CTkLabel(self.files_header_frame, text="Filename", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.hdr_file.grid(row=0, column=1, sticky="w", padx=5)
        
        self.hdr_internal = ctk.CTkLabel(self.files_header_frame, text="Internal Mesh Names", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.hdr_internal.grid(row=0, column=2, sticky="w", padx=5)
        
        # Scrollable Frame for file list
        self.scroll_frame = ctk.CTkScrollableFrame(self.files_container, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=0, minsize=50)
        self.scroll_frame.grid_columnconfigure(1, weight=3)
        self.scroll_frame.grid_columnconfigure(2, weight=4)
        
        # Display initial placeholder
        self.lbl_placeholder = ctk.CTkLabel(
            self.scroll_frame, 
            text="No folder scanned yet. Choose a folder and click 'Scan Folder'.", 
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="gray"
        )
        self.lbl_placeholder.grid(row=0, column=0, columnspan=3, pady=30, sticky="ew")
        
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

    def get_internal_names(self, filepath):
        """Extracts the internal mesh names from the GLB JSON chunk."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read(20000) # Read chunk for performance
            if len(data) < 20 or data[:4] != b'glTF': return "Not a valid GLB"
            
            # GLB Header: Magic (4), Version (4), Total Length (4), JSON Length (4), JSON Type (4)
            json_len = struct.unpack('<I', data[12:16])[0]
            if json_len == 0 or (20 + json_len) > len(data):
                # Fallback: Read more if chunk was too small
                with open(filepath, 'rb') as f:
                    data = f.read(20 + json_len)
            
            json_content = data[20:20+json_len].decode('utf-8', errors='ignore')
            json_data = json.loads(json_content)
            
            names = []
            if 'meshes' in json_data:
                for m in json_data['meshes']:
                    names.append(m.get('name', 'unnamed'))
            return ", ".join(names) if names else "No mesh names found"
        except Exception:
            return "Error reading metadata"

    def start_scan_thread(self):
        folder = self.target_path.get()
        if not folder or not os.path.isdir(folder):
            # If path entry is empty, run browser dialog
            folder = filedialog.askdirectory()
            if not folder: return
            self.target_path.set(folder)
            
        self.scan_btn.configure(state="disabled")
        self.patch_btn.configure(state="disabled")
        self.is_scanning = True
        self.progress_label.configure(text="Status: Scanning...")
        self.progress.set(0.0)
        
        # Clear scroll frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.found_files = []
        
        threading.Thread(target=self.scan_folder_worker, args=(folder,), daemon=True).start()

    def scan_folder_worker(self, path):
        try:
            glb_files = []
            for root, _, files in os.walk(path):
                for f in files:
                    if f.lower().endswith('.glb'):
                        glb_files.append(os.path.join(root, f))
            
            total_files = len(glb_files)
            if total_files == 0:
                self.gui_queue.put({"action": "scan_complete", "count": 0})
                return
                
            for i, full_path in enumerate(glb_files):
                filename = os.path.basename(full_path)
                internal = self.get_internal_names(full_path)
                
                # Push file to main GUI thread
                self.gui_queue.put({
                    "action": "add_file",
                    "path": full_path,
                    "filename": filename,
                    "internal": internal,
                    "progress": (i + 1) / total_files
                })
            
            self.gui_queue.put({"action": "scan_complete", "count": total_files})
        except Exception as e:
            self.gui_queue.put({"action": "error", "message": f"Scan failed: {e}"})

    def add_file_row(self, full_path, filename, internal):
        row_idx = len(self.found_files)
        chk_var = ctk.BooleanVar(value=True)
        
        # Individual Checkbox
        chk = ctk.CTkCheckBox(
            self.scroll_frame, 
            text="", 
            variable=chk_var, 
            command=self.update_select_all_state,
            width=20
        )
        chk.grid(row=row_idx, column=0, sticky="w", padx=(5, 0), pady=5)
        
        # Filename Label
        lbl_file = ctk.CTkLabel(
            self.scroll_frame, 
            text=filename, 
            anchor="w", 
            font=ctk.CTkFont(size=13)
        )
        lbl_file.grid(row=row_idx, column=1, sticky="w", padx=5, pady=5)
        
        # Internal name label
        lbl_internal = ctk.CTkLabel(
            self.scroll_frame, 
            text=internal, 
            anchor="w", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        lbl_internal.grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        
        self.found_files.append({
            "path": full_path,
            "filename": filename,
            "internal": internal,
            "chk_var": chk_var,
            "widgets": [chk, lbl_file, lbl_internal]
        })

    def scan_complete(self, count):
        self.is_scanning = False
        self.scan_btn.configure(state="normal")
        self.progress.set(1.0)
        
        if count > 0:
            self.patch_btn.configure(state="normal")
            self.progress_label.configure(text=f"Status: Found {count} GLB files.")
            self.select_all_var.set(True)
        else:
            self.patch_btn.configure(state="disabled")
            self.progress_label.configure(text="Status: No GLB files found.")
            
            # Show empty label placeholder in scrollframe
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame, 
                text="No GLB files found in the directory.", 
                font=ctk.CTkFont(size=14, slant="italic"),
                text_color="gray"
            )
            lbl_empty.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

    def patch_glb(self, filepath):
        """Overwrites internal name fields with the current filename."""
        new_name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            # Create backup if requested
            if self.create_backups.get():
                backup_path = filepath + ".bak"
                shutil.copy2(filepath, backup_path)
                
            with open(filepath, 'rb') as f:
                header = f.read(12)
                if len(header) < 12 or header[:4] != b'glTF':
                    raise ValueError("Not a valid GLB file (invalid header)")
                total_len = struct.unpack('<I', header[8:12])[0]
                data = f.read()
            
            # Extract JSON chunk
            json_len = struct.unpack('<I', data[0:4])[0]
            json_data = json.loads(data[8:8+json_len].decode('utf-8'))

            # Global name update in all relevant standard categories
            for cat in ['meshes', 'nodes', 'materials', 'animations', 'skins']:
                if cat in json_data:
                    for item in json_data[cat]:
                        item['name'] = new_name

            # Pack JSON back to bytes
            new_json = json.dumps(json_data, separators=(',', ':')).encode('utf-8')
            # Chunk must be aligned to 4 bytes
            while len(new_json) % 4 != 0: new_json += b' '
            
            new_json_len = len(new_json)
            # Find the start of the BIN chunk (Binary data)
            bin_start = 8 + json_len
            bin_data = data[bin_start:]
            
            # Reconstruct the GLB
            new_total_len = 12 + 8 + new_json_len + len(bin_data)
            
            output = b'glTF' + struct.pack('<I', 2) + struct.pack('<I', new_total_len)
            output += struct.pack('<I', new_json_len) + b'JSON' + new_json + bin_data

            with open(filepath, 'wb') as f:
                f.write(output)
            return True
        except Exception as e:
            print(f"Error patching {filepath}: {e}")
            return False

    def start_patch_thread(self):
        selected_files = [item for item in self.found_files if item["chk_var"].get()]
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select at least one GLB file to patch.")
            return
            
        confirm_msg = "This will modify the internal metadata names of the selected GLB files.\n"
        if self.create_backups.get():
            confirm_msg += "Safety backups (.glb.bak) will be created."
        else:
            confirm_msg += "WARNING: No backups will be created!"
            
        if not messagebox.askyesno("Safety Check", f"{confirm_msg}\n\nDo you want to proceed?"):
            return
            
        self.patch_btn.configure(state="disabled")
        self.scan_btn.configure(state="disabled")
        self.is_patching = True
        
        threading.Thread(target=self.patch_all_worker, args=(selected_files,), daemon=True).start()

    def patch_all_worker(self, selected_files):
        success_count = 0
        total_files = len(selected_files)
        
        for i, item in enumerate(selected_files):
            filepath = item["path"]
            filename = item["filename"]
            self.gui_queue.put({"action": "update_status", "text": f"Patching: {filename}"})
            
            if self.patch_glb(filepath):
                success_count += 1
                new_internal = os.path.splitext(filename)[0]
                self.gui_queue.put({
                    "action": "update_row_internal", 
                    "path": filepath, 
                    "text": new_internal
                })
            else:
                self.gui_queue.put({
                    "action": "update_row_internal", 
                    "path": filepath, 
                    "text": "Patching Error"
                })
                
            self.gui_queue.put({"action": "update_progress", "value": (i + 1) / total_files})
            
        self.gui_queue.put({
            "action": "patch_complete", 
            "message": f"Successfully patched {success_count} of {total_files} GLB files."
        })

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                
                if action == "add_file":
                    self.add_file_row(msg["path"], msg["filename"], msg["internal"])
                    self.progress.set(msg["progress"])
                    
                elif action == "scan_complete":
                    self.scan_complete(msg["count"])
                    
                elif action == "update_status":
                    self.progress_label.configure(text=msg["text"])
                    
                elif action == "update_progress":
                    self.progress.set(msg["value"])
                    
                elif action == "update_row_internal":
                    for item in self.found_files:
                        if item["path"] == msg["path"]:
                            item["widgets"][2].configure(text=msg["text"])
                            
                elif action == "patch_complete":
                    self.is_patching = False
                    self.scan_btn.configure(state="normal")
                    self.patch_btn.configure(state="normal")
                    self.progress.set(0.0)
                    self.progress_label.configure(text="Status: Ready")
                    messagebox.showinfo("Finished", msg["message"])
                    
                elif action == "error":
                    self.is_scanning = False
                    self.is_patching = False
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
    app = GLBMasterManager()
    app.mainloop()