from PIL import Image
import os

if os.path.exists("assets/neutral.png"):
    img = Image.open("assets/neutral.png")
    # Resize to 64x64 for tray icon
    img = img.resize((64, 64), Image.Resampling.LANCZOS)
    img.save("assets/icon.png")
    print("Icon created.")
else:
    print("assets/neutral.png not found.")
