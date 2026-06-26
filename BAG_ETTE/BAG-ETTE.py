import os
import yaml
import bagit
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
from datetime import datetime

class BagEtte(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("BAG-ETTE")
        self.geometry("900x800")
        self.resizable(True, True)
        
        # Sci-Fi Retro Terminal Styling
        self.bg_color = "#001100"
        self.fg_color = "#33ff33"
        self.configure(fg_color=self.bg_color)
        
        self.target_path = ctk.StringVar()
        self.metadata_file = ctk.StringVar()
        self.in_place = ctk.BooleanVar(value=False)
        self.do_zip = ctk.BooleanVar(value=True)
        self.available_keys = {}
        self.full_metadata = {}
        self.gui_queue = queue.Queue()
        
        # Configure layout grids
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container frame
        self.main_frame = ctk.CTkFrame(
            self, 
            corner_radius=15, 
            fg_color="#001800",
            border_color=self.fg_color,
            border_width=1
        )
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Allow scrollable frame to grow
        
        # Header
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="> BAG-ETTE V1",
            font=ctk.CTkFont(family="Courier", size=24, weight="bold"),
            text_color=self.fg_color
        )
        self.header_label.grid(row=0, column=0, pady=20, sticky="n")
        
        # Inputs Frame
        self.inputs_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.inputs_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.inputs_frame.grid_columnconfigure(1, weight=1)
        
        self.create_simple_row(0, "SRC_DIR:", self.target_path, "BROWSE", lambda: self.target_path.set(filedialog.askdirectory()))
        self.create_simple_row(1, "YAML_MD :", self.metadata_file, "LOAD", self.load_metadata_fields)
        
        # Ingredients / Selection Frame
        self.selection_label = ctk.CTkLabel(
            self.main_frame,
            text="SELECT_INGREDIENTS:",
            font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
            text_color=self.fg_color
        )
        self.selection_label.grid(row=2, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            height=150,
            fg_color="#000800",
            scrollbar_button_color="#004400",
            scrollbar_button_hover_color="#006600",
            border_color=self.fg_color,
            border_width=1
        )
        self.scrollable_frame.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Options & Run Row
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure(2, weight=1)
        
        self.cb_inplace = ctk.CTkCheckBox(
            self.options_frame,
            text="[IN_PLACE]",
            variable=self.in_place,
            text_color=self.fg_color,
            fg_color="#002200",
            check_color=self.fg_color,
            hover_color="#003300",
            font=ctk.CTkFont(family="Courier", size=12)
        )
        self.cb_inplace.grid(row=0, column=0, padx=(0, 20), sticky="w")
        
        self.cb_zip = ctk.CTkCheckBox(
            self.options_frame,
            text="[ZIP_WRAP]",
            variable=self.do_zip,
            text_color=self.fg_color,
            fg_color="#002200",
            check_color=self.fg_color,
            hover_color="#003300",
            font=ctk.CTkFont(family="Courier", size=12)
        )
        self.cb_zip.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        self.start_btn = ctk.CTkButton(
            self.options_frame,
            text="[ BAKE BAG-ETTE ]",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color=self.fg_color,
            fg_color="#002200",
            hover_color="#004400",
            border_color=self.fg_color,
            border_width=1,
            height=35,
            command=self.start_thread
        )
        self.start_btn.grid(row=0, column=3, sticky="e")
        
        # Log & Progress Frame
        self.log_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.log_frame.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_widget = ctk.CTkTextbox(
            self.log_frame, 
            height=150, 
            font=("Courier", 10), 
            text_color=self.fg_color, 
            fg_color="#000500",
            border_color=self.fg_color,
            border_width=1,
            activate_scrollbars=True
        )
        self.log_widget.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.log_widget.configure(state="disabled")
        
        self.progress = ctk.CTkProgressBar(
            self.log_frame,
            progress_color=self.fg_color,
            fg_color="#002200"
        )
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0.0)
        
        self.process_queue()

    def toggle_theme(self):
        pass

    def create_simple_row(self, row_idx, label_txt, var, btn_txt, cmd):
        lbl = ctk.CTkLabel(
            self.inputs_frame, 
            text=label_txt, 
            font=ctk.CTkFont(family="Courier", size=12),
            text_color=self.fg_color,
            width=80,
            anchor="w"
        )
        lbl.grid(row=row_idx, column=0, padx=(0, 10), pady=5, sticky="w")
        
        ent = ctk.CTkEntry(
            self.inputs_frame,
            textvariable=var,
            font=("Courier", 11),
            text_color=self.fg_color,
            fg_color="#002200",
            border_color=self.fg_color,
            border_width=1,
            insert_color=self.fg_color
        )
        ent.grid(row=row_idx, column=1, padx=(0, 10), pady=5, sticky="ew")
        
        btn = ctk.CTkButton(
            self.inputs_frame,
            text=btn_txt,
            font=ctk.CTkFont(family="Courier", size=11, weight="bold"),
            text_color=self.fg_color,
            fg_color="#002200",
            hover_color="#004400",
            border_color=self.fg_color,
            border_width=1,
            width=80,
            command=cmd
        )
        btn.grid(row=row_idx, column=2, pady=5, sticky="e")

    def load_metadata_fields(self):
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
                    text_color=self.fg_color,
                    fg_color="#002200",
                    check_color=self.fg_color,
                    hover_color="#003300",
                    font=ctk.CTkFont(family="Courier", size=11)
                )
                cb.grid(row=i//2, column=i%2, sticky="w", padx=20, pady=5)
            self.log(f"METADATA LOADED: {len(self.full_metadata)} FIELDS FOUND.")
        except Exception as e:
            self.log(f"PARSE_ERROR: {e}")

    def log(self, msg):
        self.gui_queue.put({"action": "log", "text": msg})

    def start_thread(self):
        if not self.target_path.get() or not os.path.exists(self.target_path.get()):
            messagebox.showwarning("INPUT MISSING", "Please select a valid source directory.")
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
                    messagebox.showinfo("DONE", msg["message"])
                    self.start_btn.configure(state="normal")
                    self.progress.set(0.0)
                elif action == "error":
                    messagebox.showerror("ERROR", msg["message"])
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
                self.log("KNEADING DOUGH (COPYING FILES)...")
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

            self.log("BAKING (GENERATING BAGIT)...")
            self.gui_queue.put({"action": "progress", "value": 0.6})
            bagit.make_bag(work_dir, bag_info, checksums=['sha256'])
            self.gui_queue.put({"action": "progress", "value": 0.8})
            
            if self.do_zip.get():
                self.log("WRAPPING IN ZIP...")
                shutil.make_archive(work_dir, 'zip', work_dir)
                if not self.in_place.get(): shutil.rmtree(work_dir)
            
            self.gui_queue.put({"action": "progress", "value": 1.0})
            self.log("SUCCESS. BAG-ETTE READY.")
            self.gui_queue.put({"action": "success", "message": "BAG-ETTE creation successful."})
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.gui_queue.put({"action": "error", "message": f"Archive failed: {e}"})

if __name__ == "__main__":
    app = BagEtte()
    app.mainloop()