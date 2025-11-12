import tkinter as tk
import os
import subprocess
import csv
from google_play_scraper import app

def run_adb_command(command):
    try:
        result = subprocess.run(
            ['adb'] + command.split(),
            capture_output=True,
            text=True,
            check=True
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

def get_package_versions():
    final_csv_file = "packages.csv"
    only_third_party_checked = checkbox_var.get()
    try:
        if only_third_party_checked:
            output = run_adb_command("shell pm list packages -3")
        else:
            output = run_adb_command("shell pm list packages")

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
            if play_scraper_checkbox_var.get():
                header.append("App Name")
            writer.writerow(header)

            for package_name in packages:
                # Get version name
                version =""
                try:
                    dumpsys_output = run_adb_command(f"shell dumpsys package {package_name} | grep 'versionName'")
                    if dumpsys_output:
                        version = dumpsys_output[12:]
                    print(f"Got version {version} for {package_name}")
                except Exception as e:
                    print(f"Error getting version for {package_name}: {e}")

                # Get app name (if checkbox is checked)
                if play_scraper_checkbox_var.get():
                    try:
                        app_title = get_app_title(package_name)
                    except Exception as e:
                        print(f"Could not find {package_name} app name on play store")

                # Write row to CSV
                row = [package_name, version]
                if play_scraper_checkbox_var.get():
                    row.append(app_title)
                writer.writerow(row)

        print(f"\nSaved final output with {len(packages)} packages and versions to {final_csv_file}\n")

    except Exception as e:
        print(f"Could not get versions: {e}")

root = tk.Tk()
root.title("Get App Versions")
root.geometry("300x180")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

start_button = tk.Button(frame, text="Get App Versions", command=get_package_versions, width=30)
start_button.pack(pady=3)

connect_button = tk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.pack(pady=3)

checkbox_var = tk.BooleanVar()
only_third_party = tk.Checkbutton(frame, text="Only 3rd party apps?", variable=checkbox_var)
only_third_party.pack(pady=0)

play_scraper_checkbox_var = tk.BooleanVar()
get_app_name_checkbox = tk.Checkbutton(frame, text="Get app name?", variable=play_scraper_checkbox_var)
get_app_name_checkbox.pack(pady=0)

root.mainloop()