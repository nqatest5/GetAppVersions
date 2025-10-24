import tkinter as tk
import os
import subprocess
import pandas as pd
import tempfile

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
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def adb_connect_device():
    try:
        output = run_adb_command("devices")
        if output:
            print(f"{output}")
        else:
            print("No devices found.")
    except Exception as e:
        print(f"Could not connect to device: {e}")


def get_package_versions():
    final_csv_file = "packages.csv"
    only_third_party_checked = checkbox_var.get()
    # Step 1: Get list of packages and save to a temporary file
    try:
        if only_third_party_checked:
            output = run_adb_command("shell pm list packages -3")
        else:
            output = run_adb_command("shell pm list packages")

        if output is None:
            print("Failed to retrieve package list.")
            return

        # Parse package names
        packages = [line.replace("package:", "").strip() for line in output.splitlines() if
                    line.startswith("package:") and line.strip()]

        if not packages:
            print("No packages found.")
            return

        # Create DataFrame for package names
        df = pd.DataFrame({"package_name": packages})

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            df.to_csv(temp_file.name, index=False)
            temp_file_path = temp_file.name
            print(f"Saved {len(packages)} package names to temporary file")

        # Step 2: Read temporary file and add versions
        df = pd.read_csv(temp_file_path)
        versions = []

        for package_name in df["package_name"]:
            try:
                # Run dumpsys command and filter for versionName
                dumpsys_output = run_adb_command(f"shell dumpsys package {package_name}")
                version = "N/A"
                if dumpsys_output:
                    # Look for versionName in the output
                    for line in dumpsys_output.splitlines():
                        if "versionName" in line:
                            try:
                                # Extract version after "versionName="
                                version = line.split("versionName=")[-1].strip()
                                break
                            except IndexError:
                                version = "N/A"
                versions.append(version)
                print(f"Got version {version} for {package_name}")
            except Exception as e:
                print(f"Error getting version for {package_name}: {e}")
                versions.append("Error")

        # Add versions to DataFrame
        df["versionName"] = versions

        # Save to final CSV
        df.to_csv(final_csv_file, index=False)
        print(f"\nSaved final output with {len(packages)} packages and versions to {final_csv_file}\n")

        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
            print("Cleaned up temporary file")
        except Exception as e:
            print(f"Error cleaning up temporary file: {e}")

    except Exception as e:
        print(f"Could not get versions: {e}")


root = tk.Tk()
root.title("Get App Versions")
root.geometry("300x140")
root.resizable(True, True)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill='both')

start_button = tk.Button(frame, text="Get App Versions", command=get_package_versions, width=30)
start_button.pack(pady=3)

connect_button = tk.Button(frame, text="Connect Device", command=adb_connect_device, width=30)
connect_button.pack(pady=3)

checkbox_var = tk.BooleanVar()
only_third_party = tk.Checkbutton(frame, text="Only 3rd party apps?", variable=checkbox_var)
only_third_party.pack(pady=0)

root.mainloop()