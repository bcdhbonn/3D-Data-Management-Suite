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
        
        self.title("Master File Renamer | Adjust Filenames")
        self.geometry("850x750")
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
            text="File Manager & Renamer", 
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Tool for sequential numbering and replacing name patterns", 
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
        
        # Shared Folder Selection Frame
        self.path_frame = ctk.CTkFrame(self.main_frame)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="1. Select Target Folder (Directory containing files to rename)", 
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
        
        # Tab View
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Enlarge tab button text
        try:
            self.tabview._segmented_button.configure(font=ctk.CTkFont(size=14, weight="bold"))
        except Exception:
            pass
            
        # Add tabs
        self.tab_seq = self.tabview.add("Sequential Numbering")
        self.tab_regex = self.tabview.add("Search & Replace (Patterns)")
        
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
        self.tab_seq.grid_rowconfigure(5, weight=1) # Allow preview textbox to expand
        
        info_lbl = ctk.CTkLabel(
            self.tab_seq,
            text="This tool sequentially renames all files of a selected type.\nThe new name is based on the folder name followed by a counter (e.g., Excavation_01.jpg, Excavation_02.jpg).",
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="gray",
            justify="left"
        )
        info_lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        
        lbl = ctk.CTkLabel(
            self.tab_seq, 
            text="Select file type (e.g., .jpg for images, .obj for 3D models):", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl.grid(row=1, column=0, sticky="w", padx=15, pady=(10, 2))
        
        self.combo_ext = ctk.CTkOptionMenu(
            self.tab_seq,
            values=["(No folder scanned)"],
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=14)
        )
        self.combo_ext.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Action Buttons row
        btn_frame = ctk.CTkFrame(self.tab_seq, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.seq_preview_btn = ctk.CTkButton(
            btn_frame,
            text="Show Preview (Recommended)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="transparent",
            border_color=self.combo_ext.cget("button_color"),
            border_width=1,
            hover_color="#0d1f3d",
            command=self.generate_sequential_preview
        )
        self.seq_preview_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.seq_btn = ctk.CTkButton(
            btn_frame, 
            text="Start Renaming", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_sequential_thread,
            state="disabled"
        )
        self.seq_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Status Label
        self.seq_status = ctk.CTkLabel(
            self.tab_seq, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.seq_status.grid(row=4, column=0, sticky="w", padx=15, pady=(5, 2))
        
        # Preview Text Box
        self.seq_preview = ctk.CTkTextbox(
            self.tab_seq,
            font=("Consolas", 13),
            activate_scrollbars=True
        )
        self.seq_preview.grid(row=5, column=0, sticky="nsew", padx=15, pady=5)
        self.seq_preview.insert(ctk.END, "Sequential renaming preview will appear here...\n")
        self.seq_preview.configure(state="disabled")
        
        self.seq_progress = ctk.CTkProgressBar(self.tab_seq)
        self.seq_progress.grid(row=6, column=0, sticky="ew", padx=15, pady=(10, 15))
        self.seq_progress.set(0.0)

    def setup_regex_tab(self):
        self.tab_regex.grid_columnconfigure(0, weight=1)
        self.tab_regex.grid_rowconfigure(4, weight=1) # Allow preview textbox to expand
        
        info_lbl = ctk.CTkLabel(
            self.tab_regex,
            text="This tool searches for specific terms or patterns in file and folder names and replaces them.\nIt is ideal for correcting naming errors or removing unwanted suffixes.",
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="gray",
            justify="left"
        )
        info_lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        
        # Inputs Layout Frame
        inputs_frame = ctk.CTkFrame(self.tab_regex, fg_color="transparent")
        inputs_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        inputs_frame.grid_columnconfigure(0, weight=1)
        
        lbl_search = ctk.CTkLabel(
            inputs_frame, 
            text="Search term or pattern (case-insensitive):", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_search.grid(row=0, column=0, sticky="w", pady=(5, 2))
        
        search_ent = ctk.CTkEntry(inputs_frame, textvariable=self.search_pattern, font=("Helvetica", 14))
        search_ent.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        
        lbl_tip = ctk.CTkLabel(
            inputs_frame, 
            text="Tips for search patterns:\n• Find_?755     -> finds both 'Find755' and 'Find_755' (the '?' makes the underscore optional)\n• _highpoly     -> searches exactly for this term (e.g. to delete it)", 
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="gray",
            justify="left"
        )
        lbl_tip.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        lbl_replace = ctk.CTkLabel(
            inputs_frame, 
            text="Replace with (leave empty to delete the search term):", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        lbl_replace.grid(row=3, column=0, sticky="w", pady=(5, 2))
        
        replace_ent = ctk.CTkEntry(inputs_frame, textvariable=self.replace_str, font=("Helvetica", 14))
        replace_ent.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        
        # Action Buttons row
        btn_frame = ctk.CTkFrame(self.tab_regex, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.regex_preview_btn = ctk.CTkButton(
            btn_frame,
            text="Show Preview (Recommended)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            fg_color="transparent",
            border_color=self.combo_ext.cget("button_color"),
            border_width=1,
            hover_color="#0d1f3d",
            command=self.generate_regex_preview
        )
        self.regex_preview_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.regex_btn = ctk.CTkButton(
            btn_frame, 
            text="Start Renaming", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_regex_thread
        )
        self.regex_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        self.regex_status = ctk.CTkLabel(
            self.tab_regex, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.regex_status.grid(row=3, column=0, sticky="w", padx=15, pady=(5, 2))
        
        # Preview Text Box
        self.regex_preview = ctk.CTkTextbox(
            self.tab_regex,
            font=("Consolas", 13),
            activate_scrollbars=True
        )
        self.regex_preview.grid(row=4, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.regex_preview.insert(ctk.END, "Search & replace preview will appear here...\n")
        self.regex_preview.configure(state="disabled")

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
                self.seq_status.configure(text=f"Status: Scan successful. Found {len(available)} file types.")
            else:
                self.combo_ext.configure(values=["No compatible files found"])
                self.combo_ext.set("No compatible files found")
                self.seq_btn.configure(state="disabled")
                self.seq_status.configure(text="Status: No files to rename found.")
        except Exception as e:
            self.combo_ext.configure(values=["Error scanning"])
            self.combo_ext.set("Error scanning")
            self.seq_btn.configure(state="disabled")
            self.seq_status.configure(text=f"Status: Scan error: {e}")

    def generate_sequential_preview(self):
        folder = self.target_path.get()
        ext = self.combo_ext.get()
        
        self.seq_preview.configure(state="normal")
        self.seq_preview.delete("1.0", ctk.END)
        
        if not folder or not os.path.isdir(folder):
            self.seq_preview.insert(ctk.END, "Error: Select a valid target folder first.\n")
            self.seq_preview.configure(state="disabled")
            return
            
        if not ext or ext not in self.combo_ext.cget("values") or ext.startswith("("):
            self.seq_preview.insert(ctk.END, "Error: No files found to rename or folder not scanned.\n")
            self.seq_preview.configure(state="disabled")
            return
            
        base_name = os.path.basename(os.path.normpath(folder)) + "_"
        
        try:
            files = sorted([f for f in os.listdir(folder) 
                            if f.lower().endswith(ext) and os.path.isfile(os.path.join(folder, f))])
            
            file_count = len(files)
            if file_count == 0:
                self.seq_preview.insert(ctk.END, f"No files ending with '{ext}' found in directory.\n")
                self.seq_preview.configure(state="disabled")
                return

            padding_length = len(str(file_count))
            
            self.seq_preview.insert(ctk.END, f"[PREVIEW] Sequential Renaming for '{ext}' files:\n")
            self.seq_preview.insert(ctk.END, f"New Base Name: {base_name}\n")
            self.seq_preview.insert(ctk.END, f"Total files: {file_count} | Digits: {padding_length}\n")
            self.seq_preview.insert(ctk.END, "="*75 + "\n")
            self.seq_preview.insert(ctk.END, f"{'OLD FILENAME':<34} --> {'NEW FILENAME':<34}\n")
            self.seq_preview.insert(ctk.END, "-"*75 + "\n")
            
            # Preview first 15 files
            preview_limit = 15
            for index, filename in enumerate(files, 1):
                if index > preview_limit:
                    self.seq_preview.insert(ctk.END, f"... and {file_count - preview_limit} more files.\n")
                    break
                num = str(index).zfill(padding_length)
                new_name = f"{base_name}{num}{ext}"
                self.seq_preview.insert(ctk.END, f"{filename[:33]:<34} --> {new_name[:33]:<34}\n")
                
        except Exception as e:
            self.seq_preview.insert(ctk.END, f"Error generating preview: {e}\n")
            
        self.seq_preview.configure(state="disabled")

    def generate_regex_preview(self):
        folder = self.target_path.get()
        pattern = self.search_pattern.get()
        new_txt = self.replace_str.get()
        
        self.regex_preview.configure(state="normal")
        self.regex_preview.delete("1.0", ctk.END)
        
        if not folder or not os.path.isdir(folder):
            self.regex_preview.insert(ctk.END, "Error: Select a valid target folder first.\n")
            self.regex_preview.configure(state="disabled")
            return
            
        if not pattern:
            self.regex_preview.insert(ctk.END, "Error: Search pattern cannot be empty.\n")
            self.regex_preview.configure(state="disabled")
            return
            
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            matches = []
            # Bottom-up walk matching production logic
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files + dirs:
                    if regex.search(name):
                        new_name = regex.sub(new_txt, name)
                        if name != new_name:
                            matches.append((name, new_name))
            
            match_count = len(matches)
            if match_count == 0:
                self.regex_preview.insert(ctk.END, f"No files or folders matched the pattern '{pattern}'.\n")
                self.regex_preview.configure(state="disabled")
                return

            self.regex_preview.insert(ctk.END, f"[PREVIEW] Search & Replace matches:\n")
            self.regex_preview.insert(ctk.END, f"Search for: '{pattern}'  -->  Replace with: '{new_txt}'\n")
            self.regex_preview.insert(ctk.END, f"Found {match_count} matching elements.\n")
            self.regex_preview.insert(ctk.END, "="*75 + "\n")
            self.regex_preview.insert(ctk.END, f"{'CURRENT NAME':<34} --> {'PROPOSED':<34}\n")
            self.regex_preview.insert(ctk.END, "-"*75 + "\n")
            
            # Preview first 15 files/folders
            preview_limit = 15
            for index, (old_name, new_name) in enumerate(matches, 1):
                if index > preview_limit:
                    self.regex_preview.insert(ctk.END, f"... and {match_count - preview_limit} more elements.\n")
                    break
                self.regex_preview.insert(ctk.END, f"{old_name[:33]:<34} --> {new_name[:33]:<34}\n")
                
        except Exception as e:
            self.regex_preview.insert(ctk.END, f"Error generating preview (Invalid pattern?): {e}\n")
            
        self.regex_preview.configure(state="disabled")

    def start_sequential_thread(self):
        folder = self.target_path.get()
        ext = self.combo_ext.get()
        if not folder or not ext or ext not in self.combo_ext.cget("values"):
            return
            
        if messagebox.askyesno("Confirm Sequential Rename", f"Do you really want to sequentially rename all {ext} files in '{os.path.basename(folder)}'?\n\nThis will permanently change the files on disk."):
            self.seq_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process_sequential, args=(folder, ext), daemon=True).start()

    def start_regex_thread(self):
        folder = self.target_path.get()
        pattern = self.search_pattern.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Invalid target folder selected.")
            return
        if not pattern:
            messagebox.showerror("Error", "Search pattern cannot be empty.")
            return
            
        if messagebox.askyesno("Confirm Search & Replace", "Search & Replace can make extensive changes to files and folders. Please ensure you have a backup of your data.\n\nProceed?"):
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
                    "text": f"Status: Securing names... ({index}/{file_count})"
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
                    "text": f"Status: Writing file names... {new_name}"
                })
                
                os.rename(temp_path, new_path)
                total += 1
                self.gui_queue.put({"action": "update_progress", "tab": "seq", "value": 0.5 + ((index / file_count) * 0.5)})

            self.gui_queue.put({
                "action": "success", 
                "tab": "seq",
                "message": f"Successfully renamed {total} files!\n\nFormat: {base_name}{'0'*padding_length}{ext}"
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "seq", "message": f"An error occurred: {e}"})

    def process_regex(self, folder, pattern):
        new_txt = self.replace_str.get()
        count = 0
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Bottom-up walk is required for directory renaming
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
                                "text": f"Status: Renamed: {count} objects (Last: {new_name})"
                            })
                            
            self.gui_queue.put({
                "action": "success", 
                "tab": "regex",
                "message": f"Successfully renamed {count} files/folders."
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "regex", "message": f"An error occurred: {e}"})

if __name__ == "__main__":
    app = MasterFileRenamer()
    app.mainloop()