import PyInstaller.__main__
import os
import shutil

# Clean previous build
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

print("Starting build process...")

# PyInstaller command arguments
args = [
    'main.py',
    '--name=MotivationMate',
    '--noconsole',
    '--onefile',
    '--add-data=assets;assets',
    '--icon=assets/icon.ico',
    '--clean',
    '--uac-admin' # Request admin might be needed for some toast notifications, but optional. Let's stick to standard first.
]

# Run PyInstaller
PyInstaller.__main__.run(args)

print("Build complete.")

# Copy README to dist
if os.path.exists("dist/MotivationMate.exe"):
    shutil.copy("README_DIST.txt", "dist/README.txt")
    print("README copied.")
    
    # Create Zip
    print("Creating zip archive...")
    shutil.make_archive("MotivationMate_v3", 'zip', "dist")
    print("Zip created: MotivationMate_v3.zip")
else:
    print("Error: Executable not found.")
