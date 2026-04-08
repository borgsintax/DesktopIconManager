import customtkinter as ctk
import os
import sys
import glob
import subprocess
from tkinter import messagebox
from icon_manager import IconManager

# Set theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class DesktopManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.manager = IconManager()
        
        # Check for silent/startup mode
        if len(sys.argv) > 1 and "--silent" in sys.argv:
            self.run_silent_backup()
            sys.exit()

        # Window setup
        self.title("Desktop Icon Manager")
        self.geometry("600x500")
        self.resizable(False, False)

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)
        self.grid_rowconfigure(4, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="Desktop Icon Manager", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Actions Frame
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.actions_frame.grid_columnconfigure((0, 1), weight=1)

        self.backup_btn = ctk.CTkButton(self.actions_frame, text="Backup Posizioni Ora", command=self.backup_now)
        self.backup_btn.grid(row=0, column=0, padx=10, pady=10)

        self.reg_backup_btn = ctk.CTkButton(self.actions_frame, text="Backup Registro (Extra)", command=self.backup_registry, fg_color="gray")
        self.reg_backup_btn.grid(row=0, column=1, padx=10, pady=10)

        # Restore Section
        self.restore_label = ctk.CTkLabel(self, text="Ripristina Backup:", font=ctk.CTkFont(size=16, weight="bold"))
        self.restore_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.backups_listbox = ctk.CTkScrollableFrame(self, height=200)
        self.backups_listbox.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        self.refresh_backups_list()

        # Settings Section
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.startup_var = ctk.BooleanVar(value=self.check_startup_status())
        self.startup_switch = ctk.CTkSwitch(self.settings_frame, text="Esegui Backup all'Avvio di Windows", 
                                          variable=self.startup_var, command=self.toggle_startup)
        self.startup_switch.pack(padx=20, pady=10)

    def run_silent_backup(self):
        try:
            self.manager.save_icons()
        except Exception as e:
            # In silent mode, we might want to log to a file instead of showing error
            with open("error_log.txt", "a") as f:
                f.write(f"Backup failed: {e}\n")

    def backup_now(self):
        try:
            filename = self.manager.save_icons()
            if filename:
                messagebox.showinfo("Successo", f"Backup creato: {os.path.basename(filename)}")
                self.refresh_backups_list()
            else:
                messagebox.showerror("Errore", "Impossibile salvare le icone.")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def backup_registry(self):
        try:
            filename = self.manager.export_registry()
            if filename:
                messagebox.showinfo("Successo", f"Registro esportato: {os.path.basename(filename)}")
            else:
                messagebox.showerror("Errore", "Impossibile esportare il registro.")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def refresh_backups_list(self):
        # Clear existing
        for widget in self.backups_listbox.winfo_children():
            widget.destroy()

        # Find json files
        files = glob.glob(os.path.join(self.manager.backup_dir, "icons_*.json"))
        files.sort(reverse=True)

        for f in files:
            basename = os.path.basename(f)
            # Format: icons_YYYY-MM-DD_HH-MM-SS.json
            display_name = basename.replace("icons_", "").replace(".json", "").replace("_", " ")
            
            row_frame = ctk.CTkFrame(self.backups_listbox)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            label = ctk.CTkLabel(row_frame, text=display_name)
            label.pack(side="left", padx=10)
            
            restore_btn = ctk.CTkButton(row_frame, text="Ripristina", width=80, 
                                      command=lambda f=f: self.restore_backup(f))
            restore_btn.pack(side="right", padx=10, pady=5)

    def restore_backup(self, filename):
        try:
            success = self.manager.restore_icons(filename)
            if success:
                messagebox.showinfo("Successo", "Icone ripristinate!")
            else:
                messagebox.showerror("Errore", "Impossibile ripristinare alcune icone.")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def check_startup_status(self):
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        link_path = os.path.join(startup_path, 'DIM.lnk')
        return os.path.exists(link_path)

    def toggle_startup(self):
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        link_path = os.path.join(startup_path, 'DIM.lnk')
        
        if self.startup_var.get():
            # Create shortcut
            target = sys.executable
            # We need to run the script. If packaged as exe, it's different.
            # Assuming running as python script for now.
            # Arguments: script path + --silent
            
            script_path = os.path.abspath(__file__)
            
            # Use VBScript to create shortcut because python doesn't have built-in way without extra deps
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{link_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target}"
            oLink.Arguments = "{script_path} --silent"
            oLink.WorkingDirectory = "{os.path.dirname(script_path)}"
            oLink.Save
            """
            
            vbs_file = os.path.join(os.environ['TEMP'], "create_shortcut.vbs")
            with open(vbs_file, "w") as f:
                f.write(vbs_script)
            
            subprocess.run(["cscript", "//Nologo", vbs_file], check=True)
            os.remove(vbs_file)
            
        else:
            # Remove shortcut
            if os.path.exists(link_path):
                os.remove(link_path)

if __name__ == "__main__":
    app = DesktopManagerApp()
    app.mainloop()
