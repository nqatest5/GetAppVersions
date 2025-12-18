import tkinter as tk
from tkinter import ttk
import subprocess
import csv
from google_play_scraper import app
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
        # Start progress bar
        pb['mode'] = 'determinate'
        pb['value'] = 0
        root.update_idletasks()

        output = run_adb_command("shell pm list packages -3")

        if output is None:
            print("Failed to retrieve package list.")
            pb['value'] = 0
            return

        packages = [line.replace("package:", "").strip() for line in output.splitlines() if
                    line.startswith("package:") and line.strip()]

        if not packages:
            print("No packages found.")
            pb['value'] = 0
            return

        total_packages = len(packages)

        # Open CSV file for writing
        with open(final_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            header = ["package_name", "versionName", "App Name"]
            writer.writerow(header)

            for index, package_name in enumerate(packages, 1):
                # Get version name
                version = ""
                try:
                    dumpsys_output = run_adb_command(f"shell dumpsys package {package_name} | grep 'versionName'")
                    if dumpsys_output:
                        version = dumpsys_output[12:]
                    print(f"Got version {version} for {package_name}")
                except Exception as e:
                    print(f"Error getting version for {package_name}: {e}")

                app_title = ""
                try:
                    app_title = get_app_title(package_name)
                except Exception as e:
                    print(f"Could not find {package_name} app name on play store")

                # Write row to CSV
                row = [package_name, version, app_title]
                writer.writerow(row)

                # Update progress bar
                progress_value = (index / total_packages) * 100
                pb['value'] = progress_value
                root.update_idletasks()

        # Task complete, set progress bar to 100%
        pb['value'] = 100
        root.update_idletasks()
        print(f"\nSaved final output with {len(packages)} packages and versions to {final_csv_file}\n")

    except Exception as e:
        print(f"Could not get versions: {e}")
    finally:
        # Reset progress bar after a delay
        root.after(1000, lambda: pb.configure(value=0))


def start_task(pb, root, start_btn):
    # Disable button during task
    start_btn.config(state='disabled')

    def task_wrapper():
        try:
            get_package_versions(pb, root)
        finally:
            # Re-enable button when done
            root.after(0, lambda: start_btn.config(state='normal'))

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

start_button = ttk.Button(frame, text="Get App Versions", width=30, style='Accent.TButton')
start_button.grid(row=0, column=0, pady=2)

connect_button = ttk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.grid(row=3, column=0, pady=2)

test_var = tk.StringVar(value="Sanity Test")
sanity_test_box = ttk.Radiobutton(frame, text="Sanity Test", variable=test_var, style='ToggleButton', width=30,
                                  value="Sanity Test")
sanity_test_box.grid(row=1, column=0, pady=2)

full_test_box = ttk.Radiobutton(frame, text="Full Test", variable=test_var, style='ToggleButton', width=30,
                                value="Full Test")
full_test_box.grid(row=2, column=0, pady=2)

progressbar = ttk.Progressbar(
    frame,
    orient='horizontal',
    length=200,
    mode='determinate',  # Changed to determinate
    maximum=100
)
progressbar.grid(row=4, column=0, pady=2)

# Configure button command after it's created
start_button.config(command=lambda: start_task(progressbar, root, start_button))

# Handle window close
root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))

root.mainloop()