from PIL import Image
import os

if os.path.exists("assets/neutral.png"):
    img = Image.open("assets/neutral.png")
    img.save("assets/icon.ico", format='ICO', sizes=[(64, 64)])
    print("Icon.ico created.")
