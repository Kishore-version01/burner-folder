import os
import sys
import time
import shutil
import stat
import tempfile
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Paste the key printed by encrypt_setup.py here:
FERNET_KEY = b"UF_V4VFQckboj7m1iqv_0Lk1EE9ASLbiygtELEyMqxc="

# Countdown duration in seconds before the decrypted temp folder self-destructs:
COUNTDOWN_SECONDS = 60
# ==============================================================================


def open_folder_in_explorer(folder_path: Path):
    """Opens the specified folder in the native OS file explorer."""
    system_name = sys.platform
    print(f"[ACTION] Opening folder in OS file explorer ({system_name})...")
    try:
        if system_name.startswith("win"):
            # Windows Explorer
            os.startfile(folder_path)  # or subprocess.Popen(["explorer", str(folder_path)])
        elif system_name == "darwin":
            # macOS
            subprocess.Popen(["open", str(folder_path)])
        else:
            # Linux and other Unix variants
            subprocess.Popen(["xdg-open", str(folder_path)])
        print("[SUCCESS] File explorer launched.")
    except Exception as e:
        print(f"[WARNING] Could not open file explorer automatically: {e}")
        print(f"[INFO] You can inspect the folder manually at: {folder_path}")


def handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to handle read-only or locked files on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def main():
    print("=" * 65)
    print(" BURNER FOLDER - LAUNCHER")
    print("=" * 65)

    # Validate Fernet key
    if not FERNET_KEY or FERNET_KEY == b"PASTE_KEY_HERE":
        print("[ERROR] No valid Fernet key configured!")
        print("[ACTION REQUIRED] Run 'python encrypt_setup.py' first, then copy the")
        print("                 generated key and paste it into FERNET_KEY in launcher.py.")
        sys.exit(1)

    try:
        fernet = Fernet(FERNET_KEY)
    except Exception as e:
        print(f"[ERROR] Invalid Fernet key format: {e}")
        sys.exit(1)

    # Locate payload directory
    base_dir = Path(__file__).resolve().parent
    payload_dir = base_dir / "payload"

    print(f"[INFO] Looking for payload directory: {payload_dir}")
    if not payload_dir.exists() or not payload_dir.is_dir():
        print(f"[ERROR] Payload folder does not exist: {payload_dir}")
        print("Please run encrypt_setup.py to generate the payload folder.")
        sys.exit(1)

    enc_files = list(payload_dir.glob("*.enc"))
    if not enc_files:
        print(f"[ERROR] No *.enc files found in {payload_dir}.")
        sys.exit(1)

    print(f"[INFO] Found {len(enc_files)} encrypted file(s) in payload/.")

    # Step 1 & 2: Create temp directory and decrypt files
    temp_dir = Path(tempfile.mkdtemp(prefix="burner_access_"))
    print(f"[TEMP] Created ephemeral destination folder: {temp_dir}")

    try:
        print("[DECRYPT] Decrypting payload files into temp directory...")
        for enc_file in enc_files:
            original_filename = enc_file.stem  # strips the .enc extension
            target_path = temp_dir / original_filename

            with open(enc_file, "rb") as f:
                cipher_data = f.read()

            try:
                decrypted_data = fernet.decrypt(cipher_data)
            except InvalidToken:
                print(f"[ERROR] Failed to decrypt {enc_file.name}. Invalid key or corrupted file!")
                raise

            with open(target_path, "wb") as f:
                f.write(decrypted_data)

            print(f"  [OK] Decrypted {enc_file.name} -> {target_path.name}")

        # Step 3: Open temp folder in OS file explorer
        open_folder_in_explorer(temp_dir)

        # Step 4: Live countdown in console
        print(f"\n[TIMER] Ephemeral access window is now active!")
        print(f"[TIMER] Folder will be permanently wiped in {COUNTDOWN_SECONDS} seconds.")
        print("[TIMER] Press Ctrl+C at any time to self-destruct immediately.\n")

        for remaining in range(COUNTDOWN_SECONDS, 0, -1):
            sys.stdout.write(f"\r==> Time remaining: {remaining:3d}s [Files accessible in temp folder] ")
            sys.stdout.flush()
            time.sleep(1)

        print("\n\n[TIMER] Countdown reached 0. Initiating self-destruction sequence...")

    except KeyboardInterrupt:
        print("\n\n[USER ABORT] Interrupt received. Initiating early self-destruction...")
    finally:
        # Step 5: Delete ONLY the temp folder
        print(f"[CLEANUP] Deleting temporary folder: {temp_dir}")
        # Give OS processes a short moment to release handles if Explorer was browsing
        time.sleep(0.5)

        for attempt in range(5):
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, onexc=handle_remove_readonly if sys.version_info >= (3, 12) else None)
                break
            except Exception as e:
                time.sleep(0.5)

        if temp_dir.exists():
            # If still exists, try ignore_errors=True
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Verify deletion
        if not temp_dir.exists():
            print("[SUCCESS] Temporary decrypted files were completely destroyed from disk.")
        else:
            print("[WARNING] Could not verify complete removal of temp folder (file may be locked by another application).")

        # Step 6: Confirmation of untouched files
        print(f"[STATUS] launcher.py: Untouched ({Path(__file__).name})")
        print(f"[STATUS] payload/: Intact with {len(list(payload_dir.glob('*.enc')))} ciphertext file(s).")
        print("=" * 65)
        print(" BURNER CYCLE COMPLETE - ACCESS TERMINATED")
        print("=" * 65)


if __name__ == "__main__":
    main()
