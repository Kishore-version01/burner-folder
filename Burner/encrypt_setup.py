import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

def main():
    print("=" * 65)
    print(" BURNER FOLDER - SETUP & ENCRYPTION TOOL")
    print("=" * 65)

    # Determine base directory (where this script resides)
    base_dir = Path(__file__).resolve().parent
    payload_dir = base_dir / "payload"

    # Determine source directory
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1]).resolve()
    else:
        # Default fallback sample directory next to Burner or prompt
        source_dir = base_dir.parent / "test_source_files"

    print(f"[INFO] Source folder: {source_dir}")

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[ERROR] Source folder does not exist: {source_dir}")
        print("Usage: python encrypt_setup.py <path_to_source_folder>")
        sys.exit(1)

    # 1. Generate Fernet key ONCE
    key = Fernet.generate_key()
    fernet = Fernet(key)

    # Print the key clearly - do not auto-save it anywhere
    print("\n" + "#" * 65)
    print(" IMPORTANT: SAVE THIS FERNET KEY")
    print(" Copy and paste this key into 'launcher.py' by hand:")
    print(f"\n  FERNET_KEY = b\"{key.decode()}\"\n")
    print("#" * 65 + "\n")

    # 2. Ensure payload directory exists
    payload_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Target payload folder: {payload_dir}")

    # 3. Encrypt every file in source folder into payload/<name>.enc
    files_to_encrypt = [f for f in source_dir.iterdir() if f.is_file()]

    if not files_to_encrypt:
        print("[WARNING] No files found in source folder to encrypt.")
        return

    print(f"[INFO] Encrypting {len(files_to_encrypt)} file(s)...")

    for file_path in files_to_encrypt:
        # Read source file (read-only)
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Encrypt contents
        encrypted_data = fernet.encrypt(file_data)

        # Write to payload/<name>.enc
        enc_filename = f"{file_path.name}.enc"
        dest_path = payload_dir / enc_filename

        with open(dest_path, "wb") as f:
            f.write(encrypted_data)

        print(f"  [ENCRYPTED] {file_path.name} -> payload/{enc_filename}")

    print("\n[SUCCESS] Encryption complete.")
    print("[INFO] Original source files were left untouched.")
    print("[INFO] launcher.py was not modified. Remember to paste the key into launcher.py manually.")

if __name__ == "__main__":
    main()
