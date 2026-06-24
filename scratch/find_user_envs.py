import os

def main():
    home_dir = "c:/Users/gabri"
    print(f"Scanning {home_dir} for .env files...")
    
    found = []
    # Only scan a few folders to avoid scanning the entire AppData
    target_subfolders = [
        "Documents",
        "Desktop",
        "Downloads",
        "Dropbox",
        "OneDrive",
        ".gemini",
        "anki_helper"
    ]
    
    for folder in target_subfolders:
        path = os.path.join(home_dir, folder)
        if not os.path.exists(path):
            continue
        print(f"Scanning subfolder: {path}...")
        for root, dirs, files in os.walk(path):
            if ".git" in dirs:
                dirs.remove(".git")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            for file in files:
                if file == ".env" or file.endswith(".env"):
                    full_path = os.path.join(root, file)
                    found.append(full_path)
                    
    print(f"Found {len(found)} .env files:")
    for path in found:
        print(f" - {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "GOOGLE_API_KEY" in content:
                    print("    -> Contains GOOGLE_API_KEY!")
        except Exception as e:
            print(f"    -> Could not read: {e}")

if __name__ == "__main__":
    main()
