import os
import uuid
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SmartFileRenamer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Smart File Renamer")
        self.geometry("600x480")
        self.resizable(True, True)
        
        self.folder_path = ctk.StringVar()
        self.available_extensions = []
        self.gui_queue = queue.Queue()
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header Section Frame (Title + Dark Mode Switch)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        # Left side of header: Title and Subtitle
        self.title_col = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_col.grid(row=0, column=0, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.title_col, 
            text="Smart File Renamer", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Collision-Free Sequential File Renaming Utility", 
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
        
        # 1. Folder Selection Frame
        self.path_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="1. Select Folder", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.folder_path, 
            placeholder_text="Browse to folder containing files to rename..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=100, 
            command=self.select_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e")
        
        # 2. Extension Selection Frame
        self.ext_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ext_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.ext_frame.grid_columnconfigure(0, weight=1)
        
        self.ext_label = ctk.CTkLabel(
            self.ext_frame, 
            text="2. Select File Type to rename", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.ext_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.combo_ext = ctk.CTkOptionMenu(
            self.ext_frame,
            values=["(No folder scanned)"]
        )
        self.combo_ext.grid(row=1, column=0, sticky="ew")
        
        # Status & Progress Frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, padx=20, pady=15, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_status = ctk.CTkLabel(
            self.status_frame, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_status.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self.status_frame)
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0.0)
        
        # Start Action Button
        self.btn_run = ctk.CTkButton(
            self.main_frame, 
            text="Start Smart Rename", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_thread,
            state="disabled"
        )
        self.btn_run.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Start GUI queue consumer
        self.process_queue()

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
            
        self.folder_path.set(folder)
        
        # Scan for extensions
        extensions = set()
        try:
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    ext = os.path.splitext(f)[1].lower()
                    if ext: extensions.add(ext)
            
            self.available_extensions = sorted(list(extensions))
            
            if self.available_extensions:
                self.combo_ext.configure(values=self.available_extensions)
                self.combo_ext.set(self.available_extensions[0])
                self.btn_run.configure(state="normal")
                self.lbl_status.configure(text=f"Status: Found {len(self.available_extensions)} file types.")
            else:
                self.combo_ext.configure(values=["No extensions found"])
                self.combo_ext.set("No extensions found")
                self.btn_run.configure(state="disabled")
                self.lbl_status.configure(text="Status: No files with extensions found.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not scan folder: {e}")

    def start_thread(self):
        selected_ext = self.combo_ext.get()
        if not selected_ext or selected_ext not in self.available_extensions:
            return
            
        if messagebox.askyesno("Confirm", f"This will rename all {selected_ext} files sequentially in this folder. Proceed?"):
            self.btn_run.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process, args=(selected_ext,), daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                if action == "update_status":
                    self.lbl_status.configure(text=msg["text"])
                elif action == "update_progress":
                    self.progress.set(msg["value"])
                elif action == "success":
                    messagebox.showinfo("Success", msg["message"])
                    self.reset_ui()
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.reset_ui()
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def reset_ui(self):
        self.btn_run.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.progress.set(0.0)
        self.lbl_status.configure(text="Status: Ready")

    def process(self, selected_ext):
        folder = self.folder_path.get()
        base_name = os.path.basename(os.path.normpath(folder)) + "_"
        
        try:
            files = sorted([f for f in os.listdir(folder) 
                            if f.lower().endswith(selected_ext) and os.path.isfile(os.path.join(folder, f))])
            
            file_count = len(files)
            if file_count == 0:
                self.gui_queue.put({"action": "error", "message": "No files found to rename."})
                return

            padding_length = len(str(file_count))
            
            # Phase 1: Isolation (rename to unique temp filenames to avoid WinError 183 collision)
            temp_files = []
            for index, filename in enumerate(files, 1):
                old_path = os.path.join(folder, filename)
                temp_name = f"atomic_{uuid.uuid4().hex}.tmp"
                temp_path = os.path.join(folder, temp_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "text": f"Status: Isolating namespace ({index}/{file_count})"
                })
                
                os.rename(old_path, temp_path)
                temp_files.append(temp_path)
                
                self.gui_queue.put({
                    "action": "update_progress", 
                    "value": (index / file_count) * 0.5
                })

            # Phase 2: Reconstruction (rename from temp files to final names)
            total = 0
            for index, temp_path in enumerate(temp_files, 1):
                num = str(index).zfill(padding_length)
                new_name = f"{base_name}{num}{selected_ext}"
                new_path = os.path.join(folder, new_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "text": f"Status: Reconstructing {new_name}"
                })
                
                os.rename(temp_path, new_path)
                total += 1
                
                self.gui_queue.put({
                    "action": "update_progress", 
                    "value": 0.5 + ((index / file_count) * 0.5)
                })

            self.gui_queue.put({
                "action": "success", 
                "message": f"Successfully renamed {total} files.\nFormat: {base_name}{'0'*padding_length}{selected_ext}"
            })
            
        except Exception as e:
            self.gui_queue.put({"action": "error", "message": f"Error: {e}"})

if __name__ == "__main__":
    app = SmartFileRenamer()
    app.mainloop()