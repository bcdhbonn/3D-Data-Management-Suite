import os
import trimesh
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MeshAnalyzer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("3D Mesh Analyzer")
        self.geometry("650x500")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.gui_queue = queue.Queue()
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Allow console textbox to grow
        
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
            text="3D Mesh Analyzer", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Geometric Metadata Extractor for OBJ, STL, GLB & PLY", 
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
        
        # 1. Path Selection Frame
        self.path_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="Select Folder with 3D Files", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Select a folder to scan..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=100, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e")
        
        # Log Output / Console Frame
        self.console_frame = ctk.CTkFrame(self.main_frame)
        self.console_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(self.console_frame, font=("Consolas", 10), activate_scrollbars=True)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.log_text.configure(state="disabled")
        
        # 3. Action / Start Button Frame
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        
        self.start_btn = ctk.CTkButton(
            self.action_frame, 
            text="Analyze Geometry", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_thread
        )
        self.start_btn.grid(row=0, column=0, sticky="ew")
        
        # Start the GUI queue consumer
        self.process_queue()

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def log(self, msg):
        self.gui_queue.put({"action": "log", "text": msg})

    def start_thread(self):
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self.process, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                if action == "log":
                    self.log_text.configure(state="normal")
                    self.log_text.insert(ctk.END, msg["text"] + "\n")
                    self.log_text.see(ctk.END)
                    self.log_text.configure(state="disabled")
                elif action == "success":
                    messagebox.showinfo("Done", msg["message"])
                    self.start_btn.configure(state="normal")
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.start_btn.configure(state="normal")
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def process(self):
        folder = self.target_path.get()
        if not folder or not os.path.exists(folder):
            self.gui_queue.put({"action": "error", "message": "Invalid directory selected"})
            return
            
        files = []
        for r, _, fs in os.walk(folder):
            for f in fs:
                if f.lower().endswith(('.obj', '.stl', '.glb', '.ply')):
                    files.append(os.path.join(r, f))
                    
        if not files:
            self.log("No compatible 3D model files found (.obj, .stl, .glb, .ply).")
            self.gui_queue.put({"action": "success", "message": "No 3D files found to analyze."})
            return
            
        for f_path in files:
            filename = os.path.basename(f_path)
            self.log(f"Processing: {filename}...")
            try:
                # Optimized loading for large OBJ/models without heavy validation
                m_data = trimesh.load(f_path, force='mesh', validate=False, process=False)
                if isinstance(m_data, trimesh.Scene):
                    v = sum(len(g.vertices) for g in m_data.geometry.values())
                    f = sum(len(g.faces) for g in m_data.geometry.values())
                else:
                    v, f = len(m_data.vertices), len(m_data.faces)
                self.log(f" > Vertices: {v:,} | Faces: {f:,}")
                del m_data
            except Exception as e:
                self.log(f" > Error processing {filename}: {e}")
                
        self.gui_queue.put({"action": "success", "message": "Analysis complete."})

if __name__ == "__main__":
    app = MeshAnalyzer()
    app.mainloop()