# rfid_reader.py
"""
RFID Reader — Dark mode UI
- Reads RFID tags from a COM port (e.g., COM5)
- Shows COM port, connection status, Start/Stop, Clear
- Displays unique tag list and total count
- Dark theme (suitable for Windows)
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import threading, time
import serial, serial.tools.list_ports

# ----- Color scheme (dark) -----
BG = "#121212"
PANEL = "#1e1e1e"
FG = "#e6e6e6"
ACCENT = "#4CAF50"
BTN_BG = "#2b2b2b"
BTN_ACTIVE = "#3a3a3a"
ENTRY_BG = "#222222"

class DarkStyle:
    @staticmethod
    def apply(root):
        root.configure(bg=BG)
        style = ttk.Style()
        # Use default theme then customize
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=FG)
        style.configure('TButton', background=BTN_BG, foreground=FG, relief='flat')
        style.map('TButton',
                  background=[('active', BTN_ACTIVE)],
                  foreground=[('disabled', '#888')])
        style.configure('TCombobox', fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=FG)
        style.configure('TEntry', fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=FG)

class RFIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Reader — Dark")
        self.root.geometry("560x520")
        self.root.resizable(False, False)

        DarkStyle.apply(self.root)

        self.ser = None
        self.reading = False
        self.tags = set()
        self.worker = None

        self._build_ui()
        self.refresh_ports()

    def _build_ui(self):
        pad = 10
        main = ttk.Frame(self.root, padding=pad)
        main.pack(fill='both', expand=True)

        # Top row: Port / Baud / Refresh
        top = ttk.Frame(main)
        top.pack(fill='x', pady=(0,8))

        ttk.Label(top, text="COM Port:").pack(side='left')
        self.port_cb = ttk.Combobox(top, values=[], width=14, state='readonly')
        self.port_cb.pack(side='left', padx=(6,10))
        self.port_cb.set('COM5')

        ttk.Label(top, text="Baud:").pack(side='left')
        self.baud_cb = ttk.Combobox(top, values=['9600','115200','19200','38400'], width=10, state='readonly')
        self.baud_cb.pack(side='left', padx=(6,10))
        self.baud_cb.set('9600')

        self.refresh_btn = ttk.Button(top, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.pack(side='left')

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill='x', pady=(6,8))

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.toggle_start)
        self.start_btn.pack(side='left', padx=(0,8))

        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_tags)
        self.clear_btn.pack(side='left', padx=(0,8))

        # Status label
        self.status_lbl = ttk.Label(main, text="Status: Idle")
        self.status_lbl.pack(fill='x', pady=(6,6))

        # Count
        count_frame = ttk.Frame(main)
        count_frame.pack(fill='x', pady=(0,8))
        ttk.Label(count_frame, text="Total unique tags:").pack(side='left')
        self.count_var = tk.StringVar(value="0")
        self.count_lbl = ttk.Label(count_frame, textvariable=self.count_var, font=('Segoe UI', 11, 'bold'))
        self.count_lbl.pack(side='left', padx=(8,0))

        # Tag list (ScrolledText with dark background)
        box_frame = ttk.Frame(main)
        box_frame.pack(fill='both', expand=True)

        self.text = scrolledtext.ScrolledText(box_frame, wrap='none', height=18, bg=PANEL, fg=FG, insertbackground=FG)
        self.text.pack(fill='both', expand=True)
        # Make scrolledtext read-only except programmatic inserts
        self.text.configure(state='disabled')

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        names = [p.device for p in ports]
        self.port_cb['values'] = names
        if names:
            if 'COM5' in names:
                self.port_cb.set('COM5')
            else:
                self.port_cb.set(names[0])
        else:
            # leave COM5 as default if none found
            self.port_cb.set('COM5')

    def toggle_start(self):
        if self.reading:
            self.stop_reading()
        else:
            self.start_reading()

    def start_reading(self):
        port = self.port_cb.get()
        if not port:
            messagebox.showwarning("Choose port", "Please select a COM port first.")
            return
        try:
            baud = int(self.baud_cb.get())
        except:
            baud = 9600
        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
        except Exception as e:
            messagebox.showerror("Serial error", f"Cannot open port {port}:\n{e}")
            return

        self.reading = True
        self.start_btn.config(text="Stop")
        self.status_lbl.config(text=f"Status: Connected to {port} @ {baud}")
        self.worker = threading.Thread(target=self.read_loop, daemon=True)
        self.worker.start()

    def stop_reading(self):
        self.reading = False
        self.start_btn.config(text="Start")
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except:
            pass
        self.status_lbl.config(text="Status: Disconnected")

    def read_loop(self):
        while self.reading:
            try:
                line = self.ser.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                if isinstance(line, bytes):
                    s = line.decode('utf-8', errors='ignore').strip()
                else:
                    s = str(line).strip()
                if not s:
                    continue
                token = s.split()[0]
                token = ''.join(ch for ch in token if ch.isalnum()).upper()
                if token and token not in self.tags:
                    self.tags.add(token)
                    self.root.after(0, self.append_tag, token)
            except Exception as e:
                # show error in status but keep app responsive
                self.root.after(0, lambda: self.status_lbl.config(text=f"Status: Read error: {e}"))
                break
        self.reading = False

    def append_tag(self, tag):
        # enable, insert, disable to keep read-only
        self.text.configure(state='normal')
        self.text.insert('end', tag + "\n")
        self.text.see('end')
        self.text.configure(state='disabled')
        self.count_var.set(str(len(self.tags)))

    def clear_tags(self):
        self.tags.clear()
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.configure(state='disabled')
        self.count_var.set("0")

    def on_close(self):
        self.stop_reading()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
