import os
import struct
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GLBMasterManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("GLB Internal Patcher")
        self.geometry("750x600")
        self.resizable(True, True)
        
        self.found_files = []
        self.gui_queue = queue.Queue()
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Allow log to grow
        
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
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Align Internal glTF Metadata Names with Disk Filenames", 
            font=ctk.CTkFont(size=12),
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
            offvalue="Light"
        )
        self.theme_switch.grid(row=0, column=1, sticky="e", pady=5)
        
        # Controls Frame (Buttons)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=0)
        self.controls_frame.grid_columnconfigure(1, weight=0)
        self.controls_frame.grid_columnconfigure(2, weight=1)
        
        self.scan_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Scan Folder", 
            command=self.scan_folder,
            width=150
        )
        self.scan_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.patch_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Patch Internal Names", 
            command=self.start_patch_thread,
            state="disabled",
            width=180
        )
        self.patch_btn.grid(row=0, column=1, padx=0, sticky="w")
        
        # Output Text Console
        self.console_frame = ctk.CTkFrame(self.main_frame)
        self.console_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.txt_output = ctk.CTkTextbox(self.console_frame, font=("Consolas", 10), activate_scrollbars=True)
        self.txt_output.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.txt_output.configure(state="disabled")
        
        # Status & Progress Frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            self.status_frame, 
            text="Status: Idle", 
            font=ctk.CTkFont(size=12),
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

    def get_internal_names(self, filepath):
        """Extracts the internal mesh names from the GLB JSON chunk."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read(20000) # Read chunk for performance
            if data[:4] != b'glTF': return "Not a valid GLB"
            
            # GLB Header: Magic (4), Version (4), Total Length (4), JSON Length (4), JSON Type (4)
            json_len = struct.unpack('<I', data[12:16])[0]
            json_content = data[20:20+json_len].decode('utf-8', errors='ignore')
            json_data = json.loads(json_content)
            
            names = []
            if 'meshes' in json_data:
                for m in json_data['meshes']:
                    names.append(m.get('name', 'unnamed'))
            return ", ".join(names) if names else "No mesh names found"
        except Exception:
            return "Error reading metadata"

    def scan_folder(self):
        path = filedialog.askdirectory()
        if not path: return
        
        self.found_files = []
        
        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", ctk.END)
        self.txt_output.insert(ctk.END, f"{'FILENAME':<40} | {'INTERNAL MESH NAME':<30}\n")
        self.txt_output.insert(ctk.END, "="*80 + "\n")
        
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith('.glb'):
                    full_path = os.path.join(root, f)
                    internal = self.get_internal_names(full_path)
                    self.found_files.append(full_path)
                    self.txt_output.insert(ctk.END, f"{f[:39]:<40} | {internal[:29]:<30}\n")
                    
        self.txt_output.configure(state="disabled")
        
        if self.found_files:
            self.patch_btn.configure(state="normal")
            self.progress_label.configure(text=f"Status: Found {len(self.found_files)} GLB files.")
        else:
            self.patch_btn.configure(state="disabled")
            self.progress_label.configure(text="Status: Scan complete. No GLB files found.")
            messagebox.showwarning("Empty", "No GLB files found in this directory.")

    def patch_glb(self, filepath):
        """Overwrites internal name fields with the current filename."""
        new_name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, 'rb') as f:
                header = f.read(12)
                total_len = struct.unpack('<I', header[8:12])[0]
                data = f.read()
            
            # Extract JSON chunk
            json_len = struct.unpack('<I', data[0:4])[0]
            json_data = json.loads(data[8:8+json_len].decode('utf-8'))

            # Global name update in all relevant categories
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
        if not messagebox.askyesno("Safety Check", "This will modify internal metadata. Do you have a backup?"):
            return
        self.patch_btn.configure(state="disabled")
        self.scan_btn.configure(state="disabled")
        threading.Thread(target=self.patch_all, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                if action == "update_status":
                    self.progress_label.configure(text=msg["text"])
                elif action == "update_progress":
                    self.progress.set(msg["value"])
                elif action == "success":
                    messagebox.showinfo("Finished", msg["message"])
                    self.scan_btn.configure(state="normal")
                    self.progress.set(0.0)
                    self.progress_label.configure(text="Status: Ready")
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.scan_btn.configure(state="normal")
                    self.progress.set(0.0)
                    self.progress_label.configure(text="Status: Ready")
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def patch_all(self):
        success_count = 0
        total_files = len(self.found_files)
        
        for i, path in enumerate(self.found_files):
            filename = os.path.basename(path)
            self.gui_queue.put({"action": "update_status", "text": f"Patching: {filename}"})
            
            if self.patch_glb(path):
                success_count += 1
                
            self.gui_queue.put({"action": "update_progress", "value": (i + 1) / total_files})
            
        self.gui_queue.put({
            "action": "success", 
            "message": f"Successfully patched {success_count} of {total_files} files internally."
        })

if __name__ == "__main__":
    app = GLBMasterManager()
    app.mainloop()