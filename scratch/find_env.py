import os

def main():
    start_dir = os.path.abspath("c:/Users/gabri/Documents/anki_helper")
    current = start_dir
    print(f"Searching for .env starting from: {current}")
    
    # Go up to root
    for i in range(5):
        env_path = os.path.join(current, ".env")
        print(f"Checking: {env_path}")
        if os.path.exists(env_path):
            print(f"FOUND .env at: {env_path}")
            # print first line or check if it has key
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if "GOOGLE_API_KEY" in line:
                        print("  -> Contains GOOGLE_API_KEY")
            return
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
        
    print("No .env file found in target path or its parents.")

if __name__ == "__main__":
    main()
