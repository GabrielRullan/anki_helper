import zipfile
import zstandard
import os
import shutil

backup_path = r"C:\Users\gabri\AppData\Roaming\Anki2\Gabriel\backups\backup-2026-08-09-22.34.28.colpkg"
extract_dir = r"c:\Users\gabri\Documents\anki_helper\scratch\backup_aug09"

os.makedirs(extract_dir, exist_ok=True)

print(f"Testing unpacking {backup_path}...")

# Check if it's zip or zstd
is_zip = False
try:
    with zipfile.ZipFile(backup_path, 'r') as zf:
        zf.extractall(extract_dir)
        print("Successfully extracted as ZIP archive!")
        is_zip = True
except Exception as e:
    print("Not a standard zip file:", e)

if not is_zip:
    print("Trying zstandard decompression...")
    try:
        dctx = zstandard.ZstdDecompressor()
        tar_path = os.path.join(extract_dir, "backup.tar")
        with open(backup_path, 'rb') as ifh, open(tar_path, 'wb') as ofh:
            dctx.copy_stream(ifh, ofh)
        print("Decompressed zstd stream into tar archive!")
        import tarfile
        with tarfile.open(tar_path) as tf:
            tf.extractall(extract_dir)
            print("Successfully extracted tar contents!")
    except Exception as e:
        print("Failed zstd/tar decompression:", e)

print("Contents of extracted dir:", os.listdir(extract_dir))
