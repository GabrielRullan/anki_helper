import os

def main():
    print("Checking environment variables...")
    for key in ["GOOGLE_API_KEY", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION"]:
        val = os.environ.get(key)
        if val:
            # Mask the API key for security
            masked = val[:6] + "..." + val[-4:] if len(val) > 10 else "exists (short)"
            print(f"  - {key}: {masked}")
        else:
            print(f"  - {key}: NOT SET")

if __name__ == "__main__":
    main()
