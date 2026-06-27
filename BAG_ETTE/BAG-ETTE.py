import os
import yaml
import bagit
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
from datetime import datetime

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BagEtte(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("BAG-ETTE | Archival Packaging Utility")
        self.geometry("900x750")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.metadata_file = ctk.StringVar()
        self.in_place = ctk.BooleanVar(value=False)
        self.do_zip = ctk.BooleanVar(value=True)
        self.available_keys = {}
        self.full_metadata = {}
        self.gui_queue = queue.Queue()
        
        # Configure layout grids on root window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Allow scrollable frame to grow
        
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
            text="BAG-ETTE", 
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Standardized Archival BagIt Packager", 
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
        self.theme_switch.grid(row=0, column=1, sticky="e", padx=10)
        if initial_mode == "Dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
            
        # Inputs Frame
        self.inputs_frame = ctk.CTkFrame(self.main_frame)
        self.inputs_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.inputs_frame.grid_columnconfigure(1, weight=1)
        
        self.create_simple_row(0, "Source Dir:", self.target_path, "Browse", lambda: self.target_path.set(filedialog.askdirectory()))
        self.create_simple_row(1, "Metadata YAML:", self.metadata_file, "Load File", self.load_metadata_fields)
        
        # Selection Frame Label
        self.selection_label = ctk.CTkLabel(
            self.main_frame,
            text="Select Metadata Fields to Include:",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.selection_label.grid(row=2, column=0, padx=25, pady=(15, 5), sticky="w")
        
        # Scrollable Frame for fields
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, height=150)
        self.scrollable_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Options & Run Row
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        self.options_frame.grid_columnconfigure(2, weight=1)
        
        self.cb_inplace = ctk.CTkCheckBox(
            self.options_frame,
            text="In-Place Packaging",
            variable=self.in_place,
            font=ctk.CTkFont(size=13)
        )
        self.cb_inplace.grid(row=0, column=0, padx=(10, 20), sticky="w")
        
        self.cb_zip = ctk.CTkCheckBox(
            self.options_frame,
            text="Wrap in ZIP Archive",
            variable=self.do_zip,
            font=ctk.CTkFont(size=13)
        )
        self.cb_zip.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        self.start_btn = ctk.CTkButton(
            self.options_frame,
            text="Bake Bag-It Package",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_thread,
            width=180
        )
        self.start_btn.grid(row=0, column=3, sticky="e", padx=(0, 10))
        
        # Log & Progress Frame
        self.log_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.log_frame.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_widget = ctk.CTkTextbox(
            self.log_frame, 
            height=150, 
            font=("Consolas", 11) if os.name == 'nt' else ("Courier", 11),
            activate_scrollbars=True
        )
        self.log_widget.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.log_widget.configure(state="disabled")
        
        self.progress = ctk.CTkProgressBar(self.log_frame)
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0.0)
        
        self.process_queue()

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def create_simple_row(self, row_idx, label_txt, var, btn_txt, cmd):
        lbl = ctk.CTkLabel(
            self.inputs_frame, 
            text=label_txt, 
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            anchor="w"
        )
        lbl.grid(row=row_idx, column=0, padx=15, pady=10, sticky="w")
        
        ent = ctk.CTkEntry(
            self.inputs_frame,
            textvariable=var,
            font=ctk.CTkFont(size=13)
        )
        ent.grid(row=row_idx, column=1, padx=(0, 15), pady=10, sticky="ew")
        
        btn = ctk.CTkButton(
            self.inputs_frame,
            text=btn_txt,
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
            command=cmd
        )
        btn.grid(row=row_idx, column=2, padx=(0, 15), pady=10, sticky="e")

    def load_metadata_fields(self, path=None):
        if not path:
            path = filedialog.askopenfilename(filetypes=[("MD/YAML", "*.md *.yaml")])
        if not path: return
        self.metadata_file.set(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content.split('---')[1]) if '---' in content else yaml.safe_load(content)
                self.full_metadata = data if data else {}
            
            for w in self.scrollable_frame.winfo_children(): w.destroy()
            self.available_keys = {}
            for i, key in enumerate(self.full_metadata.keys()):
                var = ctk.BooleanVar(value=True)
                self.available_keys[key] = var
                cb = ctk.CTkCheckBox(
                    self.scrollable_frame,
                    text=key,
                    variable=var,
                    font=ctk.CTkFont(size=13)
                )
                cb.grid(row=i//2, column=i%2, sticky="w", padx=20, pady=8)
            self.log(f"Metadata file loaded: {len(self.full_metadata)} fields found.")
        except Exception as e:
            self.log(f"YAML Parse Error: {e}")

    def log(self, msg):
        self.gui_queue.put({"action": "log", "text": msg})

    def start_thread(self):
        if not self.target_path.get() or not os.path.exists(self.target_path.get()):
            messagebox.showwarning("Input Missing", "Please select a valid source directory.")
            return
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self.process, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                if action == "log":
                    self.log_widget.configure(state="normal")
                    self.log_widget.insert("end", f"{datetime.now().strftime('%H:%M:%S')} | {msg['text']}\n")
                    self.log_widget.see("end")
                    self.log_widget.configure(state="disabled")
                elif action == "progress":
                    self.progress.set(msg["value"])
                elif action == "success":
                    messagebox.showinfo("Baking Done", msg["message"])
                    self.start_btn.configure(state="normal")
                    self.progress.set(0.0)
                elif action == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.start_btn.configure(state="normal")
                    self.progress.set(0.0)
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def process(self):
        src = self.target_path.get()
        work_dir = src if self.in_place.get() else f"{src.rstrip('/\\\\')}_Archive"
        try:
            if not self.in_place.get():
                self.log("Kneading dough (copying files to archive)...")
                if os.path.exists(work_dir): shutil.rmtree(work_dir)
                os.makedirs(work_dir)
                all_f = [os.path.join(r, file) for r, d, fs in os.walk(src) for file in fs]
                for i, fp in enumerate(all_f):
                    rel = os.path.relpath(fp, src); dest = os.path.join(work_dir, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copy2(fp, dest)
                    self.gui_queue.put({"action": "progress", "value": (i / len(all_f)) * 0.4})

            # Metadata Logic
            bag_info = {'Bagging-Date': datetime.now().strftime('%Y-%m-%d')}
            for k, var in self.available_keys.items():
                if var.get():
                    val = self.full_metadata[k]
                    if k == 'author' and isinstance(val, list):
                        names = [" ".join([p for p in [a.get('first_name'), a.get('last_name')] if p]) for a in val]
                        bag_info['Contact-Name'] = ", ".join([n for n in names if n])
                    elif k == 'titel_en':
                        bag_info['External-Description'] = str(val)
                    elif k == 'Inventory Number':
                        bag_info['External-Identifier'] = str(val)
                    else:
                        bag_info[k] = ", ".join([str(x) for x in val]) if isinstance(val, list) else str(val)

            self.log("Baking (generating BagIt structure)...")
            self.gui_queue.put({"action": "progress", "value": 0.6})
            bagit.make_bag(work_dir, bag_info, checksums=['sha256'])
            self.gui_queue.put({"action": "progress", "value": 0.8})
            
            if self.do_zip.get():
                self.log("Wrapping in ZIP...")
                shutil.make_archive(work_dir, 'zip', work_dir)
                if not self.in_place.get(): shutil.rmtree(work_dir)
            
            self.gui_queue.put({"action": "progress", "value": 1.0})
            self.log("Success! BAG-ETTE is ready.")
            self.gui_queue.put({"action": "success", "message": "BAG-ETTE archival package creation successful."})
        except Exception as e:
            self.log(f"Error: {e}")
            self.gui_queue.put({"action": "error", "message": f"Archive packing failed: {e}"})

if __name__ == "__main__":
    app = BagEtte()
    app.mainloop()