import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
import threading
from time import sleep
import json
import os
import sys
import time
import subprocess

# --- Stdout redirector for capturing print statements ---
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Auto-scroll to the end
        self.text_widget.update()

    def flush(self):
        pass

def run_adb_command(command):
    try:
        result = subprocess.run(
            ['adb'] + command.split(),  # Split command into a list
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Stderr: {e.stderr}")
    return None

def adb_connect_device():
    try:
        output = run_adb_command(
            f"devices"
        )
        print(f"{output}")
    except Exception:
        print("Could not connect to device")

def get_package_versions():
    try:
        output = run_adb_command(
            f"shell pm list packages"
        )
        #print(f"{output}")
        process = subprocess.Popen(output, stdout=subprocess.PIPE, text=True, bufsize=1)
        for line in process.stdout:
            try:
                line.replace('package:', '').strip()
                print(f"{output}")
            except Exception:
                print("Error lol")

    except subprocess.CalledProcessError as e:
        print(f"Could not get versions: {e}")


root = tk.Tk()
root.title("Get App Versions")
root.geometry("600x600")  # Increased height to accommodate more buttons
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

start_button = tk.Button(frame, text="Get App Versions", command=get_package_versions, width=30)
start_button.pack(pady=3)

connect_button = tk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.pack(pady=3)

# --- Log Area for Terminal Messages ---
log_frame = tk.Frame(frame)
log_frame.pack(fill='both', expand=True)

log_label = tk.Label(log_frame, text="Log Output:", font=('Helvetica', 10))
log_label.pack(anchor='w')

log_text = tk.Text(log_frame, height=10, width=50, font=('Helvetica', 9), wrap='word')
log_text.pack(side='left', fill='both', expand=True)

scrollbar = tk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
scrollbar.pack(side='right', fill='y')
log_text.config(yscrollcommand=scrollbar.set)

# Redirect print statements to the log_text widget
sys.stdout = StdoutRedirector(log_text)

root.mainloop()