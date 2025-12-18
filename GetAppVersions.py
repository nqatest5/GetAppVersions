import tkinter as tk
from tkinter import ttk
import subprocess
import csv
from google_play_scraper import app
import threading

def run_adb_command(command):
    try:
        result = subprocess.run(
            ['adb'] + command.split(),
            capture_output=True,
            text=True,
            check=True,
            creationflags=0x08000000  # Tells Windows to run process without creating cmd window
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def adb_connect_device():
    try:
        output = run_adb_command("devices")
        if output:
            print("done")
        else:
            print("No devices found.")
    except Exception as e:
        print(f"Could not connect to device: {e}")

def get_app_title(app_id):
    try:
        result = app(app_id)
        if result and 'title' in result:
            return result['title']
    except Exception as e:
        print(f"Error scraping app with ID {app_id}: {e}")
        return ""

def get_package_versions(pb, root):
    final_csv_file = "packages.csv"
    try:
        output = run_adb_command("shell pm list packages -3")

        if output is None:
            print("Failed to retrieve package list.")
            return

        packages = [line.replace("package:", "").strip() for line in output.splitlines() if
                    line.startswith("package:") and line.strip()]
        
        if not packages:
            print("No packages found.")
            return

        # Open CSV file for writing
        with open(final_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            header = ["package_name", "versionName"]
            header.append("App Name")
            writer.writerow(header)

            for package_name in packages:
                # Get version name
                version =""
                try:
                    dumpsys_output = run_adb_command(f"shell dumpsys package {package_name} | grep 'versionName'")
                    for i in range(101):
                        pb['value'] = i
                        root.update_idletasks()  # Update the GUI
                    if dumpsys_output:
                        version = dumpsys_output[12:]
                    print(f"Got version {version} for {package_name}")
                except Exception as e:
                    print(f"Error getting version for {package_name}: {e}")

                try:
                    app_title = get_app_title(package_name)
                except Exception as e:
                    print(f"Could not find {package_name} app name on play store")

                # Write row to CSV
                row = [package_name, version]
                row.append(app_title)
                writer.writerow(row)
                # Task complete, stop the progress bar
        pb['value'] = 100
        print(f"\nSaved final output with {len(packages)} packages and versions to {final_csv_file}\n")

    except Exception as e:
        print(f"Could not get versions: {e}")

def start_task(pb, root):
    # Start the task in a new thread
    thread = threading.Thread(target=get_package_versions, args=(pb, root))
    thread.start()

root = tk.Tk()
root.title("Get App Versions")
root.geometry("275x180")
root.resizable(False, False)
root.tk.call('source', 'forest-light.tcl')
ttk.Style().theme_use('forest-light')

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

start_button = ttk.Button(frame, text="Get App Versions", command=lambda: start_task(progressbar,root), width=30, style='Accent.TButton')
start_button.grid(row=0, column=0, pady=2)

connect_button = ttk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.grid(row=3, column=0, pady=2)

test_var = tk.StringVar(value="Sanity Test")
sanity_test_box = ttk.Radiobutton(frame, text="Sanity Test", variable=test_var, style='ToggleButton', width=30, value="Sanity Test")
sanity_test_box.grid(row=1, column=0, pady=2)

full_test_box = ttk.Radiobutton(frame, text="Full Test", variable=test_var, style='ToggleButton', width=30, value="Full Test")
full_test_box.grid(row=2, column=0, pady=2)

progressbar = ttk.Progressbar(
    frame,
    orient='horizontal',
    length=200,
    mode='indeterminate',
    maximum=100 # Maximum value is 100
)
progressbar.grid(row=4, column=0, pady=2)

root.mainloop()