import os
from PIL import Image
import io

def save_uploaded_file(uploaded_file):
    try:
        if not os.path.exists("temp"):
            os.makedirs("temp")
        file_path = os.path.join("temp", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        return None

def cleanup_temp_files():
    if os.path.exists("temp"):
        for file in os.listdir("temp"):
            os.remove(os.path.join("temp", file))
