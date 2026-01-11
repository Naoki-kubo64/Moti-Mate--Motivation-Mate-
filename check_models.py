
import google.generativeai as genai
import os

api_key = None
if os.path.exists("api_key.txt"):
    with open("api_key.txt", "r") as f:
        api_key = f.read().strip()

if not api_key:
    print("No API key found in api_key.txt")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    with open("models.txt", "w") as f:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
    print("Models written to models.txt")
except Exception as e:
    print(f"Error listing models: {e}")
