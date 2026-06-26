import os
import hashlib
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GroupedRecursiveHasher(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Hash-Brownie")
        self.geometry("650x480")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.algo_var = ctk.StringVar(value="SHA-256")
        self.algorithms = ["SHA-256", "SHA-512", "MD5"]
        
        # Thread-safe communication queue
        self.gui_queue = queue.Queue()
        
        # Files to exclude from reports
        self.ignored_filenames = {".ds_store", "thumbs.db", "desktop.ini"}
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1) # Let progress/status take up excess space
        
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
            text="Hash-Brownie", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Recursive Data Integrity & Cryptographic Checksum Utility", 
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
        self.path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="1. Root Directory", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Select a root folder to scan..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=100, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e")
        
        # 2. Options Frame (Algorithm only)
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure(0, weight=1)
        
        self.algo_label = ctk.CTkLabel(
            self.options_frame, 
            text="2. Cryptographic Algorithm", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.algo_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.algo_menu = ctk.CTkOptionMenu(
            self.options_frame, 
            variable=self.algo_var, 
            values=self.algorithms
        )
        self.algo_menu.grid(row=1, column=0, sticky="ew")
        
        # 3. Status and Progress Frame
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        self.progress_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.progress.set(0.0)
        
        # New buttons: Open Report & Open Folder (disabled until a report is created)
        self.open_report_btn = ctk.CTkButton(
            self.progress_frame, 
            text="Open Report", 
            state="disabled", 
            command=self.open_report
        )
        self.open_report_btn.grid(row=2, column=0, padx=(0, 5), pady=(10, 0), sticky="ew")
        
        self.open_folder_btn = ctk.CTkButton(
            self.progress_frame, 
            text="Open Folder", 
            state="disabled", 
            command=self.open_folder
        )
        self.open_folder_btn.grid(row=2, column=1, padx=(5, 0), pady=(10, 0), sticky="ew")
        
        # 4. Action Button
        self.start_btn = ctk.CTkButton(
            self.main_frame, 
            text="Generate Integrity Report", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_thread
        )
        self.start_btn.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Start the GUI queue consumer
        self.process_queue()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def open_report(self):
        if hasattr(self, 'last_report_path') and os.path.exists(self.last_report_path):
            os.startfile(self.last_report_path)

    def open_folder(self):
        if hasattr(self, 'last_target_path') and os.path.exists(self.last_target_path):
            os.startfile(self.last_target_path)

    def get_file_info(self, file_path, algo):
        hash_func = getattr(hashlib, algo.lower().replace("-", ""))()
        try:
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(65536), b''):
                    hash_func.update(block)
            timestamp = os.path.getmtime(file_path)
            date_str = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M:%S')
            return date_str, hash_func.hexdigest()
        except Exception:
            return "N/A", "Error accessing file"

    def start_thread(self):
        # 1. Disable the buttons synchronously in the UI thread to prevent double clicks
        self.start_btn.configure(state="disabled")
        self.open_report_btn.configure(state="disabled")
        self.open_folder_btn.configure(state="disabled")
        
        # 2. Spawn the hashing worker thread
        thread = threading.Thread(target=self.process)
        thread.daemon = True
        thread.start()

    def process_queue(self):
        """Polls the queue for pending UI updates (runs on the main thread)."""
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                
                if action == "update_status":
                    self.progress_label.configure(text=msg["text"])
                elif action == "update_progress":
                    self.progress.set(msg["value"])
                elif action == "success":
                    self.last_report_path = msg["report_path"]
                    self.last_target_path = msg["target_path"]
                    messagebox.showinfo("Success", msg["message"])
                    self.reset_ui()
                    self.open_report_btn.configure(state="normal")
                    self.open_folder_btn.configure(state="normal")
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.reset_ui()
                elif action == "info":
                    messagebox.showinfo("Info", msg["message"])
                    self.reset_ui()
                
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Re-schedule check every 100ms
            self.after(100, self.process_queue)

    def reset_ui(self):
        self.start_btn.configure(state="normal")
        self.progress_label.configure(text="Status: Ready")
        self.progress.set(0.0)

    def process(self):
        root_folder = self.target_path.get()
        algo = self.algo_var.get()
        
        if not root_folder or not os.path.exists(root_folder):
            self.gui_queue.put({"action": "error", "message": "Invalid directory selected"})
            return

        folder_name = os.path.basename(os.path.normpath(root_folder))
        report_filename = f"{folder_name}_hashes.md"
        output_file = os.path.join(root_folder, report_filename)
        
        try:
            structure = {}
            total_files = 0
            
            # Recursively traverse directory
            for root_dir, dirs, files in os.walk(root_folder):
                valid_files = []
                for f in files:
                    # Ignore the report itself and common system metadata
                    if f.lower() == report_filename.lower():
                        continue
                    if f.lower() in self.ignored_filenames:
                        continue
                    valid_files.append(f)

                if not valid_files:
                    continue
                
                # Normalize relative path to forward slashes for Markdown cross-platform compatibility
                rel_path = os.path.relpath(root_dir, root_folder)
                normalized_path = rel_path.replace(os.sep, '/')
                
                structure[normalized_path] = sorted(valid_files)
                total_files += len(valid_files)

            if total_files == 0:
                self.gui_queue.put({"action": "info", "message": "No files found to hash."})
                return

            processed_count = 0
            lines = [
                f"# Integrity Report: {folder_name}", 
                f"Generated on: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", 
                f"Algorithm: {algo}", 
                ""
            ]

            sorted_paths = sorted(structure.keys(), key=lambda x: (x != ".", x))

            for rel_path in sorted_paths:
                display_path = "Root" if rel_path == "." else rel_path
                lines.append(f"### Folder: {display_path}")
                lines.append(f"| Filename | Last Modified | {algo} Checksum |")
                lines.append(f"|---|---|---|")

                for file in structure[rel_path]:
                    # Reconstruct correct OS path for file reading
                    os_rel_path = rel_path.replace('/', os.sep)
                    full_path = os.path.join(root_folder, os_rel_path, file)
                    
                    self.gui_queue.put({"action": "update_status", "text": f"Hashing: {file}"})
                    
                    date, checksum = self.get_file_info(full_path, algo)
                    lines.append(f"| {file} | {date} | {checksum} |")
                    
                    processed_count += 1
                    # CustomTkinter progress bar uses 0.0 to 1.0
                    self.gui_queue.put({"action": "update_progress", "value": processed_count / total_files})

                lines.append("\n")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            self.gui_queue.put({
                "action": "success", 
                "message": f"Report created: {report_filename}",
                "report_path": output_file,
                "target_path": root_folder
            })
            
        except Exception as e:
            self.gui_queue.put({"action": "error", "message": str(e)})

if __name__ == "__main__":
    app = GroupedRecursiveHasher()
    app.mainloop()