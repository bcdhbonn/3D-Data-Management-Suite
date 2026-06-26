import os
import re
import uuid
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue

# Setzt das allgemeine Design und den Farbstil fest
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MasterFileRenamer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Master File Renamer | Dateinamen anpassen")
        self.geometry("750x700")
        self.resizable(True, True)
        
        self.target_path = ctk.StringVar()
        self.search_pattern = ctk.StringVar(value=r"SK_?755_Sirenenrelief")
        self.replace_str = ctk.StringVar(value="SK_755_Siren_Relief")
        self.gui_queue = queue.Queue()
        
        # Grid-Layout des Hauptfensters konfigurieren
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Haupt-Container-Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Erlaubt der Tab-Ansicht sich auszudehnen
        
        # Kopfbereich Frame (Titel, Untertitel und Design-Schalter)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        # Linke Seite des Kopfbereichs: Titel und Erklärung
        self.title_col = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_col.grid(row=0, column=0, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.title_col, 
            text="Dateimanager & Renamer", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_col, 
            text="Werkzeug zum fortlaufenden Nummerieren und Ersetzen von Namensmustern", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Rechte Seite des Kopfbereichs: Hell/Dunkel-Design umschalten
        initial_mode = ctk.get_appearance_mode()
        self.switch_var = ctk.StringVar(value=initial_mode)
        
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Dunkler Modus",
            command=self.toggle_theme,
            variable=self.switch_var,
            onvalue="Dark",
            offvalue="Light"
        )
        self.theme_switch.grid(row=0, column=1, sticky="e", pady=5)
        
        # Gemeinsamer Bereich: Zielordner auswählen
        self.path_frame = ctk.CTkFrame(self.main_frame)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="1. Zielordner auswählen (Verzeichnis mit den umzubenennenden Dateien)", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 2))
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.target_path, 
            placeholder_text="Klicke auf Durchsuchen, um einen Ordner zu wählen..."
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=(15, 10), pady=(0, 15))
        
        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Durchsuchen", 
            width=100, 
            command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=1, sticky="e", padx=(0, 15), pady=(0, 15))
        
        # Reiter-Navigation (Tabs) für die beiden Werkzeuge
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Tabs hinzufügen
        self.tab_seq = self.tabview.add("Fortlaufende Nummerierung")
        self.tab_regex = self.tabview.add("Suchen & Ersetzen (Muster)")
        
        # Tab 1 konfigurieren: Fortlaufende Nummerierung
        self.setup_sequential_tab()
        
        # Tab 2 konfigurieren: Suchen & Ersetzen
        self.setup_regex_tab()
        
        # Überwacht Änderungen am Ordnerpfad, um die Dateitypen-Liste direkt zu aktualisieren
        self.target_path.trace_add("write", lambda *args: self.scan_for_extensions())
        
        # Startet die thread-sichere Benutzeroberflächen-Aktualisierung
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
        self.tab_seq.grid_rowconfigure(5, weight=1) # Erlaubt der Vorschau-Box sich auszudehnen
        
        info_lbl = ctk.CTkLabel(
            self.tab_seq,
            text="Dieses Werkzeug benennt alle Dateien eines Typs fortlaufend um.\nDer neue Name entspricht dem Ordnernamen gefolgt von einer fortlaufenden Nummer (z. B. Grabung_01.jpg, Grabung_02.jpg).",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray",
            justify="left"
        )
        info_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        lbl = ctk.CTkLabel(
            self.tab_seq, 
            text="Dateityp auswählen (z. B. .jpg für Bilder, .obj für 3D-Modelle):", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl.grid(row=1, column=0, sticky="w", padx=10, pady=(10, 2))
        
        self.combo_ext = ctk.CTkOptionMenu(
            self.tab_seq,
            values=["(Kein Ordner gescannt)"]
        )
        self.combo_ext.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Buttons für Aktionen
        btn_frame = ctk.CTkFrame(self.tab_seq, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.seq_preview_btn = ctk.CTkButton(
            btn_frame,
            text="Änderungen anzeigen (Vorschau)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            border_color=self.combo_ext.cget("button_color"),
            border_width=1,
            hover_color="#0d1f3d",
            command=self.generate_sequential_preview
        )
        self.seq_preview_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.seq_btn = ctk.CTkButton(
            btn_frame, 
            text="Umbenennung starten", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_sequential_thread,
            state="disabled"
        )
        self.seq_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Statusanzeige
        self.seq_status = ctk.CTkLabel(
            self.tab_seq, 
            text="Status: Bereit", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.seq_status.grid(row=4, column=0, sticky="w", padx=10, pady=(5, 2))
        
        # Vorschau Text-Box
        self.seq_preview = ctk.CTkTextbox(
            self.tab_seq,
            font=("Consolas", 10),
            activate_scrollbars=True
        )
        self.seq_preview.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        self.seq_preview.insert(ctk.END, "Die Vorschau für die Nummerierung wird hier angezeigt...\n")
        self.seq_preview.configure(state="disabled")
        
        self.seq_progress = ctk.CTkProgressBar(self.tab_seq)
        self.seq_progress.grid(row=6, column=0, sticky="ew", padx=10, pady=(10, 15))
        self.seq_progress.set(0.0)

    def setup_regex_tab(self):
        self.tab_regex.grid_columnconfigure(0, weight=1)
        self.tab_regex.grid_rowconfigure(4, weight=1) # Erlaubt der Vorschau-Box sich auszudehnen
        
        info_lbl = ctk.CTkLabel(
            self.tab_regex,
            text="Dieses Werkzeug sucht nach bestimmten Begriffen oder Mustern in Datei- und Ordnernamen und ersetzt diese.\nEs eignet sich hervorragend, um Namensfehler oder unerwünschte Namenszusätze zu korrigieren.",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray",
            justify="left"
        )
        info_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Eingabe-Felder in einem inneren Frame gruppiert
        inputs_frame = ctk.CTkFrame(self.tab_regex, fg_color="transparent")
        inputs_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        inputs_frame.grid_columnconfigure(0, weight=1)
        
        lbl_search = ctk.CTkLabel(
            inputs_frame, 
            text="Gesuchter Begriff oder Suchmuster (Groß-/Kleinschreibung ignoriert):", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_search.grid(row=0, column=0, sticky="w", pady=(5, 2))
        
        search_ent = ctk.CTkEntry(inputs_frame, textvariable=self.search_pattern)
        search_ent.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        
        lbl_tip = ctk.CTkLabel(
            inputs_frame, 
            text="Tipps für Muster:\n• Grabung_?755   -> findet sowohl 'Grabung755' als auch 'Grabung_755' (das '?' macht den Strich optional)\n• _highpoly       -> sucht genau diesen Begriff, um ihn z. B. zu entfernen", 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="gray",
            justify="left"
        )
        lbl_tip.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        lbl_replace = ctk.CTkLabel(
            inputs_frame, 
            text="Ersetzen durch (feld leerlassen, um den gesuchten Begriff zu löschen):", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_replace.grid(row=3, column=0, sticky="w", pady=(5, 2))
        
        replace_ent = ctk.CTkEntry(inputs_frame, textvariable=self.replace_str)
        replace_ent.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        
        # Buttons für Aktionen
        btn_frame = ctk.CTkFrame(self.tab_regex, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.regex_preview_btn = ctk.CTkButton(
            btn_frame,
            text="Änderungen anzeigen (Vorschau)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            border_color=self.combo_ext.cget("button_color"),
            border_width=1,
            hover_color="#0d1f3d",
            command=self.generate_regex_preview
        )
        self.regex_preview_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.regex_btn = ctk.CTkButton(
            btn_frame, 
            text="Umbenennung starten", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_regex_thread
        )
        self.regex_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        self.regex_status = ctk.CTkLabel(
            self.tab_regex, 
            text="Status: Bereit", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.regex_status.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 2))
        
        # Vorschau Text-Box
        self.regex_preview = ctk.CTkTextbox(
            self.tab_regex,
            font=("Consolas", 10),
            activate_scrollbars=True
        )
        self.regex_preview.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 15))
        self.regex_preview.insert(ctk.END, "Die Vorschau für die Begriff-Ersetzung wird hier angezeigt...\n")
        self.regex_preview.configure(state="disabled")

    def scan_for_extensions(self):
        folder = self.target_path.get()
        if not folder or not os.path.isdir(folder):
            self.combo_ext.configure(values=["(Kein Ordner ausgewählt)"])
            self.combo_ext.set("(Kein Ordner ausgewählt)")
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
                self.seq_status.configure(text=f"Status: Scannen erfolgreich. {len(available)} Dateitypen gefunden.")
            else:
                self.combo_ext.configure(values=["Keine Dateien im Ordner gefunden"])
                self.combo_ext.set("Keine Dateien im Ordner gefunden")
                self.seq_btn.configure(state="disabled")
                self.seq_status.configure(text="Status: Keine umzubenennenden Dateien vorhanden.")
        except Exception as e:
            self.combo_ext.configure(values=["Fehler beim Auslesen"])
            self.combo_ext.set("Fehler beim Auslesen")
            self.seq_btn.configure(state="disabled")
            self.seq_status.configure(text=f"Status: Fehler beim Scannen: {e}")

    def generate_sequential_preview(self):
        folder = self.target_path.get()
        ext = self.combo_ext.get()
        
        self.seq_preview.configure(state="normal")
        self.seq_preview.delete("1.0", ctk.END)
        
        if not folder or not os.path.isdir(folder):
            self.seq_preview.insert(ctk.END, "Fehler: Bitte wähle zuerst einen gültigen Ordner aus.\n")
            self.seq_preview.configure(state="disabled")
            return
            
        if not ext or ext not in self.combo_ext.cget("values") or ext.startswith("("):
            self.seq_preview.insert(ctk.END, "Fehler: Keine Dateien gefunden oder ungültiger Dateityp.\n")
            self.seq_preview.configure(state="disabled")
            return
            
        base_name = os.path.basename(os.path.normpath(folder)) + "_"
        
        try:
            files = sorted([f for f in os.listdir(folder) 
                            if f.lower().endswith(ext) and os.path.isfile(os.path.join(folder, f))])
            
            file_count = len(files)
            if file_count == 0:
                self.seq_preview.insert(ctk.END, f"Keine Dateien mit der Endung '{ext}' im Ordner gefunden.\n")
                self.seq_preview.configure(state="disabled")
                return

            padding_length = len(str(file_count))
            
            self.seq_preview.insert(ctk.END, f"[VORSCHAU] Fortlaufende Nummerierung für '{ext}'-Dateien:\n")
            self.seq_preview.insert(ctk.END, f"Neuer Basis-Name: {base_name}\n")
            self.seq_preview.insert(ctk.END, f"Gesamtanzahl: {file_count} Dateien | Stellenanzahl: {padding_length} Stellen.\n")
            self.seq_preview.insert(ctk.END, "="*70 + "\n")
            self.seq_preview.insert(ctk.END, f"{'ALTER DATEINAME':<32} --> {'NEUER DATEINAME':<32}\n")
            self.seq_preview.insert(ctk.END, "-"*70 + "\n")
            
            # Erste 15 Dateien anzeigen
            preview_limit = 15
            for index, filename in enumerate(files, 1):
                if index > preview_limit:
                    self.seq_preview.insert(ctk.END, f"... und {file_count - preview_limit} weitere Dateien.\n")
                    break
                num = str(index).zfill(padding_length)
                new_name = f"{base_name}{num}{ext}"
                self.seq_preview.insert(ctk.END, f"{filename[:31]:<32} --> {new_name[:31]:<32}\n")
                
        except Exception as e:
            self.seq_preview.insert(ctk.END, f"Fehler beim Erstellen der Vorschau: {e}\n")
            
        self.seq_preview.configure(state="disabled")

    def generate_regex_preview(self):
        folder = self.target_path.get()
        pattern = self.search_pattern.get()
        new_txt = self.replace_str.get()
        
        self.regex_preview.configure(state="normal")
        self.regex_preview.delete("1.0", ctk.END)
        
        if not folder or not os.path.isdir(folder):
            self.regex_preview.insert(ctk.END, "Fehler: Bitte wähle zuerst einen gültigen Ordner aus.\n")
            self.regex_preview.configure(state="disabled")
            return
            
        if not pattern:
            self.regex_preview.insert(ctk.END, "Fehler: Das Suchfeld darf nicht leer sein.\n")
            self.regex_preview.configure(state="disabled")
            return
            
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            matches = []
            # Bottom-Up-Suche (genau wie bei der echten Durchführung)
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files + dirs:
                    if regex.search(name):
                        new_name = regex.sub(new_txt, name)
                        if name != new_name:
                            matches.append((name, new_name))
            
            match_count = len(matches)
            if match_count == 0:
                self.regex_preview.insert(ctk.END, f"Keine Ordner oder Dateien gefunden, die auf das Muster '{pattern}' passen.\n")
                self.regex_preview.configure(state="disabled")
                return

            self.regex_preview.insert(ctk.END, f"[VORSCHAU] Suchen & Ersetzen Trefferliste:\n")
            self.regex_preview.insert(ctk.END, f"Suche nach: '{pattern}'  -->  Ersetzen durch: '{new_txt}'\n")
            self.regex_preview.insert(ctk.END, f"Gefunden: {match_count} passende Elemente.\n")
            self.regex_preview.insert(ctk.END, "="*70 + "\n")
            self.regex_preview.insert(ctk.END, f"{'AKTUELLER NAME':<32} --> {'VORSCHLAG':<32}\n")
            self.regex_preview.insert(ctk.END, "-"*70 + "\n")
            
            # Erste 15 Treffer anzeigen
            preview_limit = 15
            for index, (old_name, new_name) in enumerate(matches, 1):
                if index > preview_limit:
                    self.regex_preview.insert(ctk.END, f"... und {match_count - preview_limit} weitere Elemente.\n")
                    break
                self.regex_preview.insert(ctk.END, f"{old_name[:31]:<32} --> {new_name[:31]:<32}\n")
                
        except Exception as e:
            self.regex_preview.insert(ctk.END, f"Fehler beim Erstellen der Vorschau (Muster fehlerhaft?): {e}\n")
            
        self.regex_preview.configure(state="disabled")

    def start_sequential_thread(self):
        folder = self.target_path.get()
        ext = self.combo_ext.get()
        if not folder or not ext or ext not in self.combo_ext.cget("values"):
            return
            
        if messagebox.askyesno("Bestätigung", f"Möchtest du wirklich alle {ext}-Dateien im Ordner '{os.path.basename(folder)}' fortlaufend umbenennen?\n\nDies ändert die Dateien permanent."):
            self.seq_btn.configure(state="disabled")
            self.browse_btn.configure(state="disabled")
            threading.Thread(target=self.process_sequential, args=(folder, ext), daemon=True).start()

    def start_regex_thread(self):
        folder = self.target_path.get()
        pattern = self.search_pattern.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Fehler", "Ungültiger Zielordner ausgewählt.")
            return
        if not pattern:
            messagebox.showerror("Fehler", "Das Suchmuster darf nicht leer sein.")
            return
            
        if messagebox.askyesno("Bestätigung", "Suchen & Ersetzen kann weitreichende Änderungen an Dateien und Ordnern vornehmen. Bitte erstelle vorab ein Backup.\n\nFortfahren?"):
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
                    messagebox.showinfo("Erfolg", msg["message"])
                    self.reset_ui(tab)
                    self.scan_for_extensions()
                elif action == "error":
                    messagebox.showerror("Fehler", msg["message"])
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
            self.seq_status.configure(text="Status: Bereit")
        else:
            self.regex_btn.configure(state="normal")
            self.regex_status.configure(text="Status: Bereit")
        self.browse_btn.configure(state="normal")

    def process_sequential(self, folder, ext):
        base_name = os.path.basename(os.path.normpath(folder)) + "_"
        try:
            files = sorted([f for f in os.listdir(folder) 
                            if f.lower().endswith(ext) and os.path.isfile(os.path.join(folder, f))])
            
            file_count = len(files)
            if file_count == 0:
                self.gui_queue.put({"action": "error", "tab": "seq", "message": "Keine Dateien zum Umbenennen gefunden."})
                return

            padding_length = len(str(file_count))
            
            # Phase 1: Isolation (Namensräume sichern)
            temp_files = []
            for index, filename in enumerate(files, 1):
                old_path = os.path.join(folder, filename)
                temp_name = f"atomic_{uuid.uuid4().hex}.tmp"
                temp_path = os.path.join(folder, temp_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "tab": "seq",
                    "text": f"Status: Sichere Namensraum... ({index}/{file_count})"
                })
                
                os.rename(old_path, temp_path)
                temp_files.append(temp_path)
                self.gui_queue.put({"action": "update_progress", "tab": "seq", "value": (index / file_count) * 0.5})

            # Phase 2: Reconstruction (Echtes Umbenennen)
            total = 0
            for index, temp_path in enumerate(temp_files, 1):
                num = str(index).zfill(padding_length)
                new_name = f"{base_name}{num}{ext}"
                new_path = os.path.join(folder, new_name)
                
                self.gui_queue.put({
                    "action": "update_status", 
                    "tab": "seq",
                    "text": f"Status: Schreibe Dateiname... {new_name}"
                })
                
                os.rename(temp_path, new_path)
                total += 1
                self.gui_queue.put({"action": "update_progress", "tab": "seq", "value": 0.5 + ((index / file_count) * 0.5)})

            self.gui_queue.put({
                "action": "success", 
                "tab": "seq",
                "message": f"Erfolgreich {total} Dateien umbenannt!\n\nFormat: {base_name}{'0'*padding_length}{ext}"
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "seq", "message": f"Fehler aufgetreten: {e}"})

    def process_regex(self, folder, pattern):
        new_txt = self.replace_str.get()
        count = 0
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Bottom-Up-Walk ist zwingend nötig für Ordnerstrukturen
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
                                "text": f"Status: Umbenannt: {count} Objekte (Zuletzt: {new_name})"
                            })
                            
            self.gui_queue.put({
                "action": "success", 
                "tab": "regex",
                "message": f"Erfolgreich {count} Dateien/Ordner mittels Suchmuster umbenannt."
            })
        except Exception as e:
            self.gui_queue.put({"action": "error", "tab": "regex", "message": f"Fehler aufgetreten: {e}"})

if __name__ == "__main__":
    app = MasterFileRenamer()
    app.mainloop()