import os
import re
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Set theme and appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class DynamicReplacer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Dynamic Regex Replacer")
        self.geometry("650x550")
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
            text="Dynamic Regex Replacer", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Recursive Bottom-Up Regex Search & Replace Renamer", 
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
            text="1. Select Root Folder", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Select a root folder..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Browse", 
            width=100, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e")
        
        # 2. Search Pattern Frame
        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.search_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_label = ctk.CTkLabel(
            self.search_frame, 
            text="2. Search Pattern (Regular Expression)", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.search_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.search_entry = ctk.CTkEntry(self.search_frame, textvariable=self.search_pattern)
        self.search_entry.grid(row=1, column=0, sticky="ew")
        
        self.tip_label = ctk.CTkLabel(
            self.search_frame, 
            text="Tip: 'SK_?755' finds both SK755 and SK_755", 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="gray"
        )
        self.tip_label.grid(row=2, column=0, sticky="w", pady=(2, 0))
        
        # 3. Replace Pattern Frame
        self.replace_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.replace_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.replace_frame.grid_columnconfigure(0, weight=1)
        
        self.replace_label = ctk.CTkLabel(
            self.replace_frame, 
            text="3. Replace with", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.replace_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.replace_entry = ctk.CTkEntry(self.replace_frame, textvariable=self.replace_str)
        self.replace_entry.grid(row=1, column=0, sticky="ew")
        
        # Status Label Frame
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Status: Ready", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Start Action Button
        self.start_btn = ctk.CTkButton(
            self.main_frame, 
            text="Start Dynamic Rename", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_thread
        )
        self.start_btn.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Start GUI queue consumer
        self.process_queue()

    def toggle_theme(self):
        new_theme = self.switch_var.get()
        ctk.set_appearance_mode(new_theme)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def start_thread(self):
        if not self.target_path.get() or not os.path.exists(self.target_path.get()):
            messagebox.showerror("Error", "Invalid root folder path selected.")
            return
            
        if not self.search_pattern.get():
            messagebox.showerror("Error", "Please enter a valid search pattern.")
            return
            
        if messagebox.askyesno("Confirm", "Regex renaming is highly powerful and permanent. Are you sure you have backups and wish to proceed?"):
            self.start_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")
                if action == "update_status":
                    self.status_label.configure(text=msg["text"])
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
        self.start_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.status_label.configure(text="Status: Ready")

    def process(self):
        root_dir = self.target_path.get()
        pattern = self.search_pattern.get()
        new_txt = self.replace_str.get()
        count = 0
        
        try:
            # Compile regex to validate early
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Bottom-up is required so directory changes do not break subsequent walks
            for root, dirs, files in os.walk(root_dir, topdown=False):
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
                                "text": f"Status: Renamed {count} items (Last: {new_name})"
                            })
                            
            self.gui_queue.put({
                "action": "success", 
                "message": f"Successfully renamed {count} folders and files."
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "message": f"Error: {e}"})

if __name__ == "__main__":
    app = DynamicReplacer()
    app.mainloop()