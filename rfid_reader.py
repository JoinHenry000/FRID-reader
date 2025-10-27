# rfid_reader.py
"""
RFID Reader GUI for Windows (reads from COM port)
- Designed to parse tag lines like: E2000017221101441890A1B3
- Shows COM port, status, Start/Stop, Clear, tag list and unique count
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading, time
import serial, serial.tools.list_ports

class RFIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Reader — Windows")
        self.root.geometry("520x480")
        self.ser = None
        self.reading = False
        self.tags = set()
        self.create_widgets()
        self.refresh_ports()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill='both', expand=True)

        top = ttk.Frame(frm)
        top.pack(fill='x', pady=4)

        ttk.Label(top, text="COM Port:").pack(side='left')
        self.port_cb = ttk.Combobox(top, values=[], width=14, state='readonly')
        self.port_cb.pack(side='left', padx=(6,8))
        self.port_cb.set('COM5')

        ttk.Label(top, text="Baud:").pack(side='left')
        self.baud_cb = ttk.Combobox(top, values=['9600','115200','19200','38400'], width=8, state='readonly')
        self.baud_cb.set('9600')
        self.baud_cb.pack(side='left', padx=(6,8))

        self.refresh_btn = ttk.Button(top, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.pack(side='left', padx=4)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(fill='x', pady=8)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.toggle_start)
        self.start_btn.pack(side='left', padx=6)

        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_tags)
        self.clear_btn.pack(side='left', padx=6)

        self.status_lbl = ttk.Label(frm, text="Status: Idle")
        self.status_lbl.pack(fill='x', pady=(6,8))

        count_frame = ttk.Frame(frm)
        count_frame.pack(fill='x')
        ttk.Label(count_frame, text="Total unique tags:").pack(side='left')
        self.count_var = tk.StringVar(value="0")
        self.count_lbl = ttk.Label(count_frame, textvariable=self.count_var, font=('Segoe UI', 11, 'bold'))
        self.count_lbl.pack(side='left', padx=(6,0))

        # Scrolled list of tags
        self.text = scrolledtext.ScrolledText(frm, wrap='none', height=18)
        self.text.pack(fill='both', expand=True, pady=(8,0))

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        if port_list:
            self.port_cb['values'] = port_list
            # if COM5 exists keep it, else set first
            if 'COM5' in port_list:
                self.port_cb.set('COM5')
            else:
                self.port_cb.set(port_list[0])
        else:
            self.port_cb['values'] = []
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
                # Expect tag like: E2000017221101441890A1B3
                token = s.split()[0]
                # sanitize token: keep alnum only
                token = ''.join(ch for ch in token if ch.isalnum()).upper()
                if token and token not in self.tags:
                    self.tags.add(token)
                    self.root.after(0, self.append_tag, token)
            except Exception as e:
                print("Read error:", e)
                self.root.after(0, lambda: self.status_lbl.config(text=f"Status: Read error: {e}"))
                break
        self.reading = False

    def append_tag(self, tag):
        self.text.insert('end', tag + "\n")
        self.text.see('end')
        self.count_var.set(str(len(self.tags)))

    def clear_tags(self):
        self.tags.clear()
        self.text.delete('1.0', 'end')
        self.count_var.set("0")

    def on_close(self):
        self.stop_reading()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = RFIDApp(root)
    root.protocol('WM_DELETE_WINDOW', app.on_close)
    root.mainloop()
