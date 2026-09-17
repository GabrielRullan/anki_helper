import os
import glob

backup_dir = r"C:\Users\gabri\AppData\Roaming\Anki2\Gabriel\backups"
print(f"Checking backup dir: {backup_dir}")

if os.path.exists(backup_dir):
    files = os.listdir(backup_dir)
    print(f"Total backup files found: {len(files)}")
    for f in sorted(files, reverse=True)[:30]:
        fp = os.path.join(backup_dir, f)
        size = os.path.getsize(fp) / (1024*1024)
        print(f"  {f} ({size:.2f} MB)")
else:
    print("Backup directory does not exist!")
