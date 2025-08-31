import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import serial.tools.list_ports
import subprocess
import threading
import queue
import sys
import os
import re
import json

from datetime import datetime

class ESP32_Multi_Flasher(tk.Tk):
    """
    A standalone GUI tool for flashing multiple binary files to Espressif chips
    using esptool, featuring profiles, chip selection, and an erase function.
    """
    def __init__(self):
        super().__init__()
        self.title("ESP-Forge")
        self.geometry("800x680")
        self.minsize(700, 550)

        # --- Member Variables ---
        self.output_queue = queue.Queue()
        self.file_entries = []
        self.serial_port = tk.StringVar()
        self.chip_type = tk.StringVar(value="esp32")
        self.flash_baud_rate = tk.StringVar(value="921600")
        self.available_ports = []

        self.setup_style()
        self.setup_ui()
        self.refresh_ports()
        self.after(100, self.process_queue)

    def setup_style(self):
        """Configures a modern dark theme for the application."""
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.BG_COLOR = "#2E2E2E"
        self.FG_COLOR = "#EAEAEA"
        self.ENTRY_BG = "#3C3C3C"
        self.ACCENT_COLOR = "#007ACC"
        self.BUTTON_BG = "#4A4A4A"
        self.ERROR_COLOR = "#CF6679"

        self.configure(background=self.BG_COLOR)
        self.style.configure('.', background=self.BG_COLOR, foreground=self.FG_COLOR, fieldbackground=self.ENTRY_BG, borderwidth=0)
        self.style.configure('TFrame', background=self.BG_COLOR)
        self.style.configure('TLabel', background=self.BG_COLOR, foreground=self.FG_COLOR, font=('Segoe UI', 10))
        self.style.configure('TButton', background=self.BUTTON_BG, foreground=self.FG_COLOR, font=('Segoe UI', 10, 'bold'), borderwidth=1, focusthickness=3, focuscolor='none')
        self.style.map('TButton', background=[('active', self.ACCENT_COLOR)])
        self.style.configure('TEntry', fieldbackground=self.ENTRY_BG, foreground=self.FG_COLOR, insertcolor=self.FG_COLOR)
        self.style.configure('TLabelFrame', background=self.BG_COLOR, borderwidth=1)
        self.style.configure('TLabelFrame.Label', background=self.BG_COLOR, foreground=self.FG_COLOR, font=('Segoe UI', 11, 'bold'))
        self.style.configure('Horizontal.TProgressbar', troughcolor=self.ENTRY_BG, background=self.ACCENT_COLOR, borderwidth=0)
        self.style.configure('Error.Horizontal.TProgressbar', background=self.ERROR_COLOR)
        self.style.configure('TCheckbutton', indicatorbackground=self.ENTRY_BG, indicatorforeground=self.ACCENT_COLOR)


    def setup_ui(self):
        """Sets up the main user interface."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # --- File Selection Area ---
        files_frame = ttk.LabelFrame(main_frame, text="Binary Files and Addresses", padding=10)
        files_frame.grid(row=0, column=0, sticky="ew", pady=5)
        files_frame.columnconfigure(0, weight=1)

        profile_frame = ttk.Frame(files_frame)
        profile_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        ttk.Button(profile_frame, text="Load Profile", command=self.load_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(profile_frame, text="Save Profile", command=self.save_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(profile_frame, text="Clear All", command=lambda: self.clear_all(True)).pack(side=tk.LEFT, padx=2)

        for i in range(8):
            path_var, addr_var = tk.StringVar(), tk.StringVar()
            entry = ttk.Entry(files_frame, textvariable=path_var, state="readonly")
            entry.grid(row=i+1, column=0, sticky="ew", padx=(0, 5), pady=2)
            browse_button = ttk.Button(files_frame, text="...", width=3, command=lambda v=path_var: self.browse_file(v))
            browse_button.grid(row=i+1, column=1, padx=5, pady=2)
            addr_entry = ttk.Entry(files_frame, textvariable=addr_var, width=12, font=('Consolas', 10))
            addr_entry.grid(row=i+1, column=2, padx=5, pady=2)
            self.file_entries.append({"path_var": path_var, "addr_var": addr_var})
        self.clear_all(set_defaults=True)

        # --- Log Widget ---
        log_frame = ttk.LabelFrame(main_frame, text="Output", padding=(10, 5))
        log_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        log_frame.columnconfigure(0, weight=1); log_frame.rowconfigure(0, weight=1)
        
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", font=('Consolas', 10),
                                                    background=self.ENTRY_BG, foreground=self.FG_COLOR, borderwidth=0)
        self.log_widget.grid(row=0, column=0, sticky="nsew")
        self.log_widget.tag_config("INFO", foreground="#EAEAEA")
        self.log_widget.tag_config("ERROR", foreground=self.ERROR_COLOR)
        self.log_widget.tag_config("SUCCESS", foreground="#6BCB77")

        # --- Control Bar ---
        control_frame = ttk.Frame(main_frame, padding=(0, 10))
        control_frame.grid(row=2, column=0, sticky="ew")
        self.flash_button = ttk.Button(control_frame, text="⚡ Flash Files", command=self.start_flash_thread)
        self.flash_button.pack(side=tk.LEFT, padx=(0, 5), ipady=5)
        self.erase_button = ttk.Button(control_frame, text="🗑️ Erase Flash", command=self.start_erase_thread)
        self.erase_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.chip_info_button = ttk.Button(control_frame, text="ℹ️ Get Chip Info", command=self.start_chip_info_thread)
        self.chip_info_button.pack(side=tk.LEFT, padx=5, ipady=5)
        self.progress_bar = ttk.Progressbar(control_frame, orient='horizontal', mode='determinate', style='Horizontal.TProgressbar')
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)

        # --- Hardware Config Bar ---
        hw_frame = ttk.LabelFrame(main_frame, text="Hardware Configuration", padding=10)
        hw_frame.grid(row=3, column=0, sticky="ew", pady=(5,0))
        ttk.Label(hw_frame, text="Chip:").pack(side=tk.LEFT, padx=(0,5))
        ttk.OptionMenu(hw_frame, self.chip_type, self.chip_type.get(), "esp32", "esp32s2", "esp32s3", "esp32c3", "esp8266").pack(side=tk.LEFT, padx=(0,15))
        ttk.Label(hw_frame, text="Baud:").pack(side=tk.LEFT, padx=(0,5))
        ttk.OptionMenu(hw_frame, self.flash_baud_rate, self.flash_baud_rate.get(), "115200", "230400", "460800", "921600").pack(side=tk.LEFT, padx=(0,15))
        ttk.Label(hw_frame, text="Port:").pack(side=tk.LEFT, padx=(0,5))
        self.port_menu = ttk.OptionMenu(hw_frame, self.serial_port, "No ports")
        self.port_menu.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(hw_frame, text="⟳", width=3, command=self.refresh_ports).pack(side=tk.LEFT, padx=5)
        self.monitor_button = ttk.Button(hw_frame, text="Serial Monitor", command=self.open_serial_monitor)
        self.monitor_button.pack(side=tk.LEFT, padx=5, ipady=2)

    def browse_file(self, path_var):
        filepath = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
        if filepath: path_var.set(filepath)

    def refresh_ports(self):
        self.available_ports = [port.device for port in serial.tools.list_ports.comports()]
        menu = self.port_menu["menu"]
        menu.delete(0, "end")
        if self.available_ports:
            for port in self.available_ports:
                menu.add_command(label=port, command=lambda value=port: self.serial_port.set(value))
            if not self.serial_port.get() or self.serial_port.get() not in self.available_ports:
                self.serial_port.set(self.available_ports[0])
        else:
            self.serial_port.set("No ports found")
    
    def clear_all(self, set_defaults=False):
        for entry in self.file_entries:
            entry['path_var'].set(""), entry['addr_var'].set("")
        if set_defaults:
            self.file_entries[0]['addr_var'].set("0x1000"), self.file_entries[1]['addr_var'].set("0x8000")
            self.file_entries[2]['addr_var'].set("0xe000"), self.file_entries[3]['addr_var'].set("0x10000")

    def save_profile(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Flasher Profiles", "*.json")], title="Save Flashing Profile")
        if not filepath: return
        files_data = [{"path": e['path_var'].get(), "addr": e['addr_var'].get()} for e in self.file_entries if e['path_var'].get() and e['addr_var'].get()]
        profile = {"chip": self.chip_type.get(), "baud": self.flash_baud_rate.get(), "files": files_data}
        try:
            with open(filepath, 'w') as f: json.dump(profile, f, indent=4)
            self.log_message("Profile saved successfully.\n", "SUCCESS")
        except Exception as e: messagebox.showerror("Error Saving Profile", f"An error occurred: {e}", parent=self)

    def load_profile(self):
        filepath = filedialog.askopenfilename(filetypes=[("Flasher Profiles", "*.json")], title="Load Flashing Profile")
        if not filepath: return
        try:
            with open(filepath, 'r') as f: profile = json.load(f)
            self.clear_all()
            self.chip_type.set(profile.get("chip", "esp32"))
            self.flash_baud_rate.set(profile.get("baud", "921600"))
            for i, file_info in enumerate(profile.get("files", [])):
                if i < len(self.file_entries):
                    self.file_entries[i]['path_var'].set(file_info.get("path", "")), self.file_entries[i]['addr_var'].set(file_info.get("addr", ""))
            self.log_message("Profile loaded successfully.\n", "SUCCESS")
        except Exception as e: messagebox.showerror("Error Loading Profile", f"Could not read or parse profile file:\n{e}", parent=self)

    def set_ui_state(self, state):
        for button in [self.flash_button, self.erase_button, self.monitor_button, self.chip_info_button]:
            button.config(state=state)
    
    def common_pre_task_checks(self):
        port = self.serial_port.get()
        if not port or "No ports" in port:
            messagebox.showerror("Error", "Please select a valid serial port.", parent=self)
            return None
        self.log_widget.config(state="normal"); self.log_widget.delete('1.0', tk.END); self.log_widget.config(state="disabled")
        self.progress_bar.config(style='Horizontal.TProgressbar'); self.progress_bar['value'] = 0
        self.set_ui_state("disabled")
        return port

    def start_flash_thread(self):
        port = self.common_pre_task_checks()
        if not port: return
        flash_args = []
        for entry in self.file_entries:
            path, addr = entry['path_var'].get(), entry['addr_var'].get()
            if path and addr:
                if not os.path.exists(path):
                    messagebox.showerror("Error", f"File not found:\n{path}", parent=self)
                    self.set_ui_state("normal"); return
                flash_args.extend([addr, path])
        if not flash_args:
            messagebox.showerror("Error", "No files selected to flash.", parent=self)
            self.set_ui_state("normal"); return
        threading.Thread(target=self.execute_flash, args=(port, flash_args), daemon=True).start()

    def start_erase_thread(self):
        port = self.common_pre_task_checks()
        if not port: return
        if messagebox.askyesno("Confirm Erase", "This will ERASE ALL DATA on the chip. Are you sure?"):
            threading.Thread(target=self.execute_erase, args=(port,), daemon=True).start()
        else:
            self.set_ui_state("normal")

    def start_chip_info_thread(self):
        port = self.common_pre_task_checks()
        if not port: return
        threading.Thread(target=self.execute_get_chip_info, args=(port,), daemon=True).start()
        
    def execute_flash(self, port, flash_args):
        self.output_queue.put(("Starting multi-file flash...\n", "INFO"))
        command = [sys.executable, "-m", "esptool", "--chip", self.chip_type.get(), "--port", port, "--baud", self.flash_baud_rate.get(),
                   "--before", "default_reset", "--after", "hard_reset", "write_flash", "-z", "--flash_mode", 
                   "dio", "--flash_freq", "80m", "--flash_size", "detect", *flash_args]
        self.run_esptool_command(command)

    def execute_erase(self, port):
        self.output_queue.put(("Starting flash erase...\n", "INFO"))
        command = [sys.executable, "-m", "esptool", "--chip", self.chip_type.get(), "--port", port, "erase_flash"]
        self.run_esptool_command(command)
        
    def execute_get_chip_info(self, port):
        self.output_queue.put(("Getting chip info...\n", "INFO"))
        command = [sys.executable, "-m", "esptool", "--chip", self.chip_type.get(), "--port", port, "chip_id"]
        self.run_esptool_command(command)

    def run_esptool_command(self, command):
        task_success = False
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for line in iter(process.stdout.readline, ''):
                self.output_queue.put((line, "INFO"))
            process.wait()
            if process.returncode == 0:
                self.output_queue.put(("\nOperation completed successfully!", "SUCCESS")); task_success = True
            else:
                 self.output_queue.put((f"\nOperation failed with error code: {process.returncode}", "ERROR"))
        except FileNotFoundError: self.output_queue.put(("\nERROR: 'esptool' not found. Is it installed? (pip install esptool)", "ERROR"))
        except Exception as e: self.output_queue.put((f"\nAn unexpected error occurred: {e}", "ERROR"))
        finally: self.output_queue.put(lambda: self.on_task_complete(task_success))
    
    def on_task_complete(self, success):
        self.set_ui_state("normal")
        if success: self.progress_bar['value'] = 100
        else:
            self.progress_bar.config(style='Error.Horizontal.TProgressbar')
            if self.progress_bar['value'] == 0: self.progress_bar['value'] = 100

    def process_queue(self):
        try:
            while True:
                item = self.output_queue.get_nowait()
                if callable(item): item()
                else:
                    message, tag = item
                    self.log_message(message, tag, end='')
                    if "write_flash" in message:
                        match = re.search(r'\((\d{1,3}) %\)', message)
                        if match: self.progress_bar['value'] = int(match.group(1))
        except queue.Empty: pass
        finally: self.after(100, self.process_queue)
            
    def log_message(self, message, tag, end='\n'):
        self.log_widget.config(state="normal")
        self.log_widget.insert(tk.END, message + end, (tag,))
        self.log_widget.see(tk.END)
        self.log_widget.config(state="disabled")

    def open_serial_monitor(self):
        port = self.serial_port.get()
        if not port or "No ports" in port:
            messagebox.showerror("Error", "Please select a valid serial port first.", parent=self)
            return
        SerialMonitor(self, port)

class SerialMonitor(tk.Toplevel):
    def __init__(self, parent, port):
        super().__init__(parent)
        self.title(f"Serial Monitor - {port}"), self.geometry("700x500")
        self.port, self.serial_connection, self.read_thread = port, None, None
        self.stop_thread, self.serial_queue = threading.Event(), queue.Queue()
        self.timestamps_enabled = tk.BooleanVar(value=True)
        self.autoscroll_enabled = tk.BooleanVar(value=True)
        
        self.style = parent.style
        self.configure(background=self.style.lookup('TFrame', 'background'))
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(0, weight=1), main_frame.columnconfigure(0, weight=1)

        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state="disabled", font=('Consolas', 10),
                                                    background=self.style.lookup('TEntry', 'fieldbackground'),
                                                    foreground=self.style.lookup('TEntry', 'foreground'), borderwidth=0)
        self.text_area.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.text_area.tag_config("SUCCESS", foreground="#6BCB77"), self.text_area.tag_config("ERROR", foreground="#CF6679"), self.text_area.tag_config("INFO", foreground="#EAEAEA")

        entry_frame = ttk.Frame(main_frame)
        entry_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10,0))
        entry_frame.columnconfigure(0, weight=1)
        self.entry_var = tk.StringVar()
        entry = ttk.Entry(entry_frame, textvariable=self.entry_var)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", self.send_data)
        self.baud_rate = tk.StringVar(value="115200")
        ttk.OptionMenu(entry_frame, self.baud_rate, self.baud_rate.get(), "9600", "57600", "74880", "115200", "230400", "460800", "921600").grid(row=0, column=1, padx=5)
        ttk.Button(entry_frame, text="Send", command=self.send_data).grid(row=0, column=2, padx=5, ipady=2)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5,0))
        ttk.Checkbutton(controls_frame, text="Timestamps", variable=self.timestamps_enabled).pack(side=tk.LEFT)
        ttk.Checkbutton(controls_frame, text="Auto-scroll", variable=self.autoscroll_enabled).pack(side=tk.LEFT, padx=10)
        ttk.Button(controls_frame, text="Save Log", command=self.save_log).pack(side=tk.RIGHT, padx=2)
        ttk.Button(controls_frame, text="Clear", command=self.clear_output).pack(side=tk.RIGHT, padx=2)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.process_serial_queue)
        self.connect_serial()
        
    def connect_serial(self):
        try:
            baud = int(self.baud_rate.get())
            self.serial_connection = serial.Serial(self.port, baud, timeout=1)
            self.stop_thread.clear()
            self.read_thread = threading.Thread(target=self.read_from_port, daemon=True)
            self.read_thread.start()
            self.log_to_monitor(f"Connected to {self.port} at {baud} baud.\n", "SUCCESS")
        except (serial.SerialException, ValueError) as e:
            self.log_to_monitor(f"Error: {e}\n", "ERROR")
            messagebox.showerror("Connection Error", str(e), parent=self)

    def read_from_port(self):
        """Reads complete lines from the serial port."""
        while not self.stop_thread.is_set():
            try:
                # Read a full line from the serial port. This blocks until a newline
                # is received or the timeout (set during connection) occurs.
                line = self.serial_connection.readline()
                if line:
                    # Queue the complete line for processing by the UI thread.
                    self.serial_queue.put(line.decode('utf-8', errors='replace'))
            except serial.SerialException:
                # Handle cases where the device is disconnected.
                self.serial_queue.put(("ERROR: Device disconnected.\n", "ERROR"))
                break
    
    def send_data(self, event=None):
        data = self.entry_var.get()
        if data and self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write((data + '\n').encode('utf-8'))
            self.entry_var.set("")

    def process_serial_queue(self):
        try:
            while True:
                item = self.serial_queue.get_nowait()
                if isinstance(item, tuple): message, tag = item
                else: message, tag = item, "INFO"
                self.log_to_monitor(message, tag)
        except queue.Empty: pass
        finally:
            if not self.stop_thread.is_set(): self.after(100, self.process_serial_queue)

    def log_to_monitor(self, message, tag):
        """Logs a message to the text area, adding a timestamp and ensuring clean newlines."""
        self.text_area.config(state="normal")
        timestamp = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] " if self.timestamps_enabled.get() else ""
        # message from readline() might contain '\r\n'. We strip it to avoid extra blank lines
        # and then add our own consistent newline.
        cleaned_message = message.strip()
        if cleaned_message: # Avoid printing empty lines that only contain a timestamp
            self.text_area.insert(tk.END, f"{timestamp}{cleaned_message}\n", (tag,))
        
        if self.autoscroll_enabled.get(): self.text_area.see(tk.END)
        self.text_area.config(state="disabled")

    def save_log(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], title="Save Serial Log")
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get('1.0', tk.END))
        except Exception as e: messagebox.showerror("Save Error", f"Failed to save log: {e}", parent=self)

    def clear_output(self):
        self.text_area.config(state="normal"); self.text_area.delete('1.0', tk.END); self.text_area.config(state="disabled")

    def on_closing(self):
        self.stop_thread.set()
        if self.read_thread: self.read_thread.join(timeout=1)
        if self.serial_connection and self.serial_connection.is_open: self.serial_connection.close()
        self.destroy()

if __name__ == "__main__":
    try:
        import serial
    except ImportError:
        messagebox.showerror("Dependency Error", "PySerial is not installed.\nPlease run: pip install pyserial")
        sys.exit(1)
    app = ESP32_Multi_Flasher()
    app.mainloop()


