import tkinter as tk
from tkinter import ttk
import subprocess
import csv
import json
import os
import threading
import atexit
import signal
import sys

# Global variables for cleanup
active_threads = []
active_processes = []


def cleanup():
    """Clean up all threads and subprocesses"""
    print("Cleaning up...")

    # Terminate any active subprocesses
    for proc in active_processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass

    # Note: threads can't be forcefully killed in Python
    # They'll terminate when the main program exits
    print("Cleanup complete")


def load_package_config():
    """Load package configuration from JSON file"""
    config_file = "package_config.json"

    # Create default config if it doesn't exist
    if not os.path.exists(config_file):
        default_config = {
            "Sanity Test": {
                "Average": {
                    "com.android.phone": "Phone",
                    "com.android.chrome": "Chrome",
                    "com.google.android.apps.maps": "Google Maps"
                },
                "Post": {
                    "com.android.settings": "Settings",
                    "com.android.camera2": "Camera",
                    "com.google.android.gm": "Gmail"
                }
            },
            "Full Test": {
                "Average": {
                    "com.android.phone": "Phone",
                    "com.android.chrome": "Chrome",
                    "com.google.android.apps.maps": "Google Maps",
                    "com.android.settings": "Settings",
                    "com.android.camera2": "Camera"
                },
                "Post": {
                    "com.google.android.gm": "Gmail",
                    "com.google.android.youtube": "YouTube",
                    "com.android.contacts": "Contacts",
                    "com.android.messaging": "Messages",
                    "com.google.android.apps.photos": "Google Photos"
                }
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        print(f"Created default config file: {config_file}")

    # Load the config
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_adb_command(command):
    try:
        proc = subprocess.Popen(
            ['adb'] + command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=0x08000000  # Windows: no cmd window
        )
        active_processes.append(proc)
        stdout, stderr = proc.communicate()
        active_processes.remove(proc)

        if proc.returncode != 0:
            print(f"Error executing command: {stderr}")
            return None

        return stdout.strip()
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def adb_connect_device():
    try:
        output = run_adb_command("devices")
        if output:
            print("Device connected")
        else:
            print("No devices found.")
    except Exception as e:
        print(f"Could not connect to device: {e}")


def get_app_version(package_name):
    """Get version for a specific package"""
    try:
        dumpsys_output = run_adb_command(f"shell dumpsys package {package_name}")
        if dumpsys_output:
            # Search for versionName in the output
            for line in dumpsys_output.splitlines():
                if 'versionName=' in line:
                    version = line.split('versionName=')[1].strip()
                    return version
        return "Not Found"
    except Exception as e:
        print(f"Error getting version for {package_name}: {e}")
        return "Error"


def get_package_versions(pb, root, test_type):
    final_csv_file = "packages.csv"
    try:
        # Load package configuration
        config = load_package_config()

        if test_type not in config:
            print(f"Test type '{test_type}' not found in configuration.")
            return

        test_sections = config[test_type]

        # Start progress bar
        pb['mode'] = 'determinate'
        pb['value'] = 0
        root.update_idletasks()

        # Calculate total packages across all sections
        total_packages = sum(len(packages) for packages in test_sections.values())

        if total_packages == 0:
            print("No packages configured for this test type.")
            pb['value'] = 0
            return

        # Open CSV file for writing
        with open(final_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            current_index = 0

            # Process each section (Average, Post, etc.)
            for section_name, packages_dict in test_sections.items():
                # Write section header
                writer.writerow([f"=== {test_type} - {section_name} ==="])
                writer.writerow([])  # Empty row for spacing

                # Write column headers for this section
                writer.writerow(["Package Name", "Version"])

                # Process packages in this section
                for package_name, app_name in packages_dict.items():
                    current_index += 1

                    # Get version name
                    version = get_app_version(package_name)
                    print(f"[{section_name}] Got version {version} for {package_name} ({app_name})")

                    # Write row to CSV
                    row = [package_name, f"{app_name} version: {version}"]
                    writer.writerow(row)

                    # Update progress bar
                    progress_value = (current_index / total_packages) * 100
                    pb['value'] = progress_value
                    root.update_idletasks()

                # Add empty rows between sections
                writer.writerow([])
                writer.writerow([])

        # Task complete, set progress bar to 100%
        pb['value'] = 100
        root.update_idletasks()
        print(
            f"\nSaved output with {total_packages} packages across {len(test_sections)} sections to {final_csv_file}\n")

    except Exception as e:
        print(f"Could not get versions: {e}")
    finally:
        # Reset progress bar after a delay
        root.after(1000, lambda: pb.configure(value=0))


def start_task(pb, root, start_btn, test_var):
    # Get selected test type
    test_type = test_var.get()

    # Disable button during task
    start_btn.config(state='disabled')
    connect_button.config(state='disabled')
    sanity_test_box.config(state='disabled')
    full_test_box.config(state='disabled')

    def task_wrapper():
        try:
            get_package_versions(pb, root, test_type)
        finally:
            # Re-enable button when done
            root.after(0, lambda: start_btn.config(state='normal'))
            root.after(0, lambda: connect_button.config(state='normal'))
            root.after(0, lambda: sanity_test_box.config(state='normal'))
            root.after(0, lambda: full_test_box.config(state='normal'))

    # Start the task in a new thread
    thread = threading.Thread(target=task_wrapper, daemon=True)
    active_threads.append(thread)
    thread.start()


def on_closing(root):
    """Handle window close event"""
    cleanup()
    root.destroy()
    sys.exit(0)


# Register cleanup handlers
atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda sig, frame: cleanup() or sys.exit(0))
signal.signal(signal.SIGTERM, lambda sig, frame: cleanup() or sys.exit(0))

root = tk.Tk()
root.title("Get App Versions")
root.geometry("275x180")
root.resizable(False, False)
root.tk.call('source', 'forest-light.tcl')
ttk.Style().theme_use('forest-light')

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

test_var = tk.StringVar(value="Sanity Test")

start_button = ttk.Button(frame, text="Get App Versions", width=30, style='Accent.TButton')
start_button.grid(row=0, column=0, pady=2)

sanity_test_box = ttk.Radiobutton(frame, text="Sanity Test", variable=test_var, style='ToggleButton', width=30,
                                  value="Sanity Test")
sanity_test_box.grid(row=1, column=0, pady=2)

full_test_box = ttk.Radiobutton(frame, text="Full Test", variable=test_var, style='ToggleButton', width=30,
                                value="Full Test")
full_test_box.grid(row=2, column=0, pady=2)

connect_button = ttk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.grid(row=3, column=0, pady=2)

progressbar = ttk.Progressbar(
    frame,
    orient='horizontal',
    length=200,
    mode='determinate',
    maximum=100
)
progressbar.grid(row=4, column=0, pady=2)

# Configure button command after it's created
start_button.config(command=lambda: start_task(progressbar, root, start_button, test_var))

# Handle window close
root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))

root.mainloop()