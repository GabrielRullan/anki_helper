import os

def main():
    appdata_dir = "C:/Users/gabri/.gemini/antigravity-ide"
    print(f"Scanning AppData: {appdata_dir}")
    for root, dirs, files in os.walk(appdata_dir):
        for file in files:
            if file == ".env" or file.endswith(".env"):
                print(f"FOUND: {os.path.join(root, file)}")

if __name__ == "__main__":
    main()
