import os
import re
import uuid
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MasterFileRenamer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Master File Renamer")
        self.geometry("700x550")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.search_pattern = ctk.StringVar(value=r"SK_?755_Sirenenrelief")
        self.replace_str = ctk.StringVar(value="SK_755_Siren_Relief")
        self.gui_queue = queue.Queue()
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Allow tabview to grow
        
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
            text="Master File Renamer", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Unified Sequential Renaming & Dynamic Regex Replacing Utility", 
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
        
        # Shared Folder Selection Frame
        self.path_frame = ctk.CTkFrame(self.main_frame)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="Root Directory (Target Folder)", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 2))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Select a folder to scan..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(15, 10), pady=(0, 15))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=100, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e", padx=(0, 15), pady=(0, 15))
        
        # Tab View
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Add tabs
        self.tab_seq = self.tabview.add("Smart Sequential Rename")
        self.tab_regex = self.tabview.add("Dynamic Regex Replace")
        
        # Setup Tab 1: Sequential Rename
        self.setup_sequential_tab()
        
        # Setup Tab 2: Regex Replace
        self.setup_regex_tab()
        
        # Trace folder path updates to scan extensions
        self.target_path.trace_add("write", lambda *args: self.scan_for_extensions())
        
        # Start GUI queue consumer
        self.process_queue()

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def setup_sequential_tab(self):
        self.tab_seq.grid_columnconfigure(0, weight=1)
        
        lbl = ctk.CTkLabel(
            self.tab_seq, 
            text="Select File Type to rename:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(15, 5))
        
        self.combo_ext = ctk.CTkOptionMenu(
            self.tab_seq,
            values=["(No folder selected)"]
        )
        self.combo_ext.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 15))
        
        # Status & Progress Frame inside Tab
        self.seq_status = ctk.CTkLabel(
            self.tab_seq, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.seq_status.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 5))
        
        self.seq_progress = ctk.CTkProgressBar(self.tab_seq)
        self.seq_progress.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 15))
        self.seq_progress.set(0.0)
        
        self.seq_btn = ctk.CTkButton(
            self.tab_seq, 
            text="Start Smart Rename", 
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            command=self.start_sequential_thread,
            state="disabled"
        )
        self.seq_btn.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

    def setup_regex_tab(self):
        self.tab_regex.grid_columnconfigure(0, weight=1)
        
        lbl_search = ctk.CTkLabel(
            self.tab_regex, 
            text="Search Pattern (Regex):", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_search.grid(row=0, column=0, sticky="w", padx=10, pady=(15, 2))
        
        search_ent = ctk.CTkEntry(self.tab_regex, textvariable=self.search_pattern)
        search_ent.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        lbl_tip = ctk.CTkLabel(
            self.tab_regex, 
            text="Tip: 'SK_?755' matches both SK755 and SK_755", 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="gray"
        )
        lbl_tip.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))
        
        lbl_replace = ctk.CTkLabel(
            self.tab_regex, 
            text="Replace with:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_replace.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 2))
        
        replace_ent = ctk.CTkEntry(self.tab_regex, textvariable=self.replace_str)
        replace_ent.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 15))
        
        self.regex_status = ctk.CTkLabel(
            self.tab_regex, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.regex_status.grid(row=5, column=0, sticky="w", padx=10, pady=(0, 5))
        
        self.regex_btn = ctk.CTkButton(
            self.tab_regex, 
            text="Start Regex Rename", 
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            command=self.start_regex_thread
        )
        self.regex_btn.grid(row=6, column=0, sticky="ew", padx=10, pady=10)

    def scan_for_extensions(self):
        folder = self.target_path.get()
        if not folder or not os.path.isdir(folder):
            self.combo_ext.configure(values=["(No folder selected)"])
            self.combo_ext.set("(No folder selected)")
            self.seq_btn.configure(state="disabled")
            return
        
        try:
            extensions = set()
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    ext = os.path.splitext(f)[1].lower()
                    if ext: extensions.add(ext)
            
            available = sorted(list(extensions))
            if available:
                self.combo_ext.configure(values=available)
                self.combo_ext.set(available[0])
                self.seq_btn.configure(state="normal")
                self.seq_status.configure(text=f"Status: Found {len(available)} file types.")
            else:
                self.combo_ext.configure(values=["No extensions found"])
                self.combo_ext.set("No extensions found")
                self.seq_btn.configure(state="disabled")
                self.seq_status.configure(text="Status: No files with extensions found.")
        except Exception as e:
            self.combo_ext.configure(values=["Error reading directory"])
            self.combo_ext.set("Error reading directory")
            self.seq_btn.configure(state="disabled")
            self.seq_status.configure(text=f"Status: Scan error: {e}")

    def start_sequential_thread(self):
        folder = self.target_path.get()
        ext = self.combo_ext.get()
        if not folder or not ext or ext not in self.combo_ext.cget("values"):
            return
            
        if messagebox.askyesno("Confirm Sequential Rename", f"This will sequentially rename all {ext} files in '{os.path.basename(folder)}'. Proceed?"):
            self.seq_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process_sequential, args=(folder, ext), daemon=True).start()

    def start_regex_thread(self):
        folder = self.target_path.get()
        pattern = self.search_pattern.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid root folder selected.")
            return
        if not pattern:
            messagebox.showerror("Error", "Search pattern cannot be empty.")
            return
            
        if messagebox.askyesno("Confirm Regex Rename", "Regex renaming is highly powerful and permanent. Proceed?"):
            self.regex_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process_regex, args=(folder, pattern), daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                tab = msg.get("tab")
                
                status_lbl = self.seq_status if tab == "seq" else self.regex_status
                progress_bar = self.seq_progress if tab == "seq" else None
                
                if action == "update_status":
                    status_lbl.configure(text=msg["text"])
                elif action == "update_progress":
                    if progress_bar: progress_bar.set(msg["value"])
                elif action == "success":
                    messagebox.showinfo("Success", msg["message"])
                    self.reset_ui(tab)
                    # Trigger a rescan of extensions after sequential renaming finishes
                    if tab == "seq":
                        self.scan_for_extensions()
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.reset_ui(tab)
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def reset_ui(self, tab):
        if tab == "seq":
            self.seq_btn.configure(state="normal")
            self.seq_progress.set(0.0)
            self.seq_status.configure(text="Status: Ready")
        else:
            self.regex_btn.configure(state="normal")
            self.regex_status.configure(text="Status: Ready")
        self.browse_btn.configure(state="normal")

    def process_sequential(self, folder, ext):
        base_name = os.path.basename(os.path.normpath(folder)) + "_"
        try:
            files = sorted([f for f in os.listdir(folder) 
                            if f.lower().endswith(ext) and os.path.isfile(os.path.join(folder, f))])
            
            file_count = len(files)
            if file_count == 0:
                self.gui_queue.put({"action": "error", "tab": "seq", "message": "No files found to rename."})
                return

            padding_length = len(str(file_count))
            
            # Phase 1: Isolation
            temp_files = []
            for index, filename in enumerate(files, 1):
                old_path = os.path.join(folder, filename)
                temp_name = f"atomic_{uuid.uuid4().hex}.tmp"
                temp_path = os.path.join(folder, temp_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "tab": "seq",
                    "text": f"Status: Isolating namespace ({index}/{file_count})"
                })
                
                os.rename(old_path, temp_path)
                temp_files.append(temp_path)
                self.gui_queue.put({"action": "update_progress", "tab": "seq", "value": (index / file_count) * 0.5})

            # Phase 2: Reconstruction
            total = 0
            for index, temp_path in enumerate(temp_files, 1):
                num = str(index).zfill(padding_length)
                new_name = f"{base_name}{num}{ext}"
                new_path = os.path.join(folder, new_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "tab": "seq",
                    "text": f"Status: Reconstructing {new_name}"
                })
                
                os.rename(temp_path, new_path)
                total += 1
                self.gui_queue.put({"action": "update_progress", "tab": "seq", "value": 0.5 + ((index / file_count) * 0.5)})

            self.gui_queue.put({
                "action": "success", 
                "tab": "seq",
                "message": f"Successfully renamed {total} files.\nFormat: {base_name}{'0'*padding_length}{ext}"
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "seq", "message": f"Error: {e}"})

    def process_regex(self, folder, pattern):
        new_txt = self.replace_str.get()
        count = 0
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Bottom-up walk is required for directories
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files + dirs:
                    if regex.search(name):
                        new_name = regex.sub(new_txt, name)
                        old_path = os.path.join(root, name)
                        new_path = os.path.join(root, new_name)
                        
                        if old_path != new_path:
                            os.rename(old_path, new_path)
                            count += 1
                            self.gui_queue.put({
                                "action": "update_status", 
                                "tab": "regex",
                                "text": f"Status: Renamed {count} items (Last: {new_name})"
                            })
                            
            self.gui_queue.put({
                "action": "success", 
                "tab": "regex",
                "message": f"Successfully renamed {count} folders/files using regex."
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "regex", "message": f"Error: {e}"})

if __name__ == "__main__":
    app = MasterFileRenamer()
    app.mainloop()