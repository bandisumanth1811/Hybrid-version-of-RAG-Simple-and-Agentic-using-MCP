import os
import sys
import subprocess

def main():
    print("Starting Git Assist AI (Streamlit)...")
    
    # Get the absolute path to the streamlit app
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "ui", "streamlit_app.py")
    
    # Run streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
