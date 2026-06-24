import os

def main():
    docs_dir = "c:/Users/gabri/Documents"
    print(f"Scanning {docs_dir} for .env files...")
    
    found = []
    for root, dirs, files in os.walk(docs_dir):
        # Ignore common large folders
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
