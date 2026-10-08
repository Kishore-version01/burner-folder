import os
import sys
import argparse
from pathlib import Path
from cryptography.fernet import Fernet

LAUNCHER_TEMPLATE = '''import os
import sys
import time
import shutil
import stat
import tempfile
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

# ==============================================================================
# CONFIGURATION (Configured by Burner Creator)
# ==============================================================================
FERNET_KEY = __FERNET_KEY__
COUNTDOWN_SECONDS = __COUNTDOWN_SECONDS__
BURN_AFTER_READING = __BURN_AFTER_READING__
# ==============================================================================


def open_folder_in_explorer(folder_path: Path):
    """Opens the specified folder in the native OS file explorer."""
    system_name = sys.platform
    print(f"[ACTION] Opening folder in OS file explorer ({system_name})...")
    try:
        if system_name.startswith("win"):
            os.startfile(folder_path)
        elif system_name == "darwin":
            subprocess.Popen(["open", str(folder_path)])
        else:
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

    if not FERNET_KEY:
        print("[ERROR] No valid Fernet key configured!")
        sys.exit(1)

    try:
        fernet = Fernet(FERNET_KEY)
    except Exception as e:
        print(f"[ERROR] Invalid Fernet key format: {e}")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent
    payload_dir = base_dir / "payload"

    print(f"[INFO] Looking for payload directory: {payload_dir}")
    if not payload_dir.exists() or not payload_dir.is_dir():
        print(f"[ERROR] Payload folder does not exist: {payload_dir}")
        sys.exit(1)

    enc_files = list(payload_dir.glob("*.enc"))
    if not enc_files:
        print(f"[ERROR] No *.enc files found in {payload_dir}.")
        sys.exit(1)

    print(f"[INFO] Found {len(enc_files)} encrypted file(s) in payload/.")

    # Create ephemeral destination folder under OS temp dir
    temp_dir = Path(tempfile.mkdtemp(prefix="burner_access_"))
    print(f"[TEMP] Created ephemeral destination folder: {temp_dir}")

    try:
        print("[DECRYPT] Decrypting payload files into temp directory...")
        for enc_file in enc_files:
            original_filename = enc_file.stem
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

        open_folder_in_explorer(temp_dir)

        print()
        print("[TIMER] Ephemeral access window is now active!")
        print(f"[TIMER] Files will be permanently deleted in {COUNTDOWN_SECONDS} seconds.")
        if BURN_AFTER_READING:
            print("[NOTICE] SELF-DESTRUCT ACTIVE: Entire folder will be permanently vaporized.")
        print("[TIMER] Press Ctrl+C at any time to self-destruct immediately.")
        print()

        for remaining in range(COUNTDOWN_SECONDS, 0, -1):
            sys.stdout.write(f"\r==> Time remaining: {remaining:3d}s [Files active in temp folder] ")
            sys.stdout.flush()
            time.sleep(1)

        print()
        print()
        print("[TIMER] Countdown reached 0. Initiating self-destruction sequence...")

    except KeyboardInterrupt:
        print()
        print()
        print("[USER ABORT] Interrupt received. Initiating early self-destruction...")
    finally:
        print(f"[CLEANUP] Deleting temporary decrypted folder: {temp_dir}")
        time.sleep(0.5)

        for _ in range(5):
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, onexc=handle_remove_readonly if sys.version_info >= (3, 12) else None)
                break
            except Exception:
                time.sleep(0.5)

        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

        if not temp_dir.exists():
            print("[SUCCESS] Temporary decrypted files were destroyed from disk.")
        else:
            print("[WARNING] Could not verify complete removal of temp folder.")

        if BURN_AFTER_READING:
            print()
            print("#" * 65)
            print(" [SELF-DESTRUCT] EXECUTING ONE-TIME PERMANENT BURN")
            print("#" * 65)
            # 1. Delete encrypted payload files
            shutil.rmtree(payload_dir, ignore_errors=True)
            print("  [OK] Payload directory wiped.")

            # 2. Overwrite launcher.py to eradicate the key from disk immediately
            try:
                with open(__file__, "w", encoding="utf-8") as f:
                    f.write("# BURNED: This folder has expired and all files and keys have been permanently destroyed.\\n")
                print("  [OK] Cryptographic key permanently erased.")
            except Exception:
                pass

            # 3. Schedule parent folder deletion after Python exits
            print("  [OK] Purging folder structure from disk...")
            os.chdir(tempfile.gettempdir())
            if sys.platform.startswith("win"):
                subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 2 > nul & rmdir /s /q "{base_dir}"', shell=True)
            else:
                subprocess.Popen(f'sleep 1 && rm -rf "{base_dir}"', shell=True)

            print("=" * 65)
            print(" BURN COMPLETE - FOLDER PERMANENTLY VAPORIZED")
            print("=" * 65)
        else:
            print(f"[STATUS] launcher.py: Untouched ({Path(__file__).name})")
            print(f"[STATUS] payload/: Intact with {len(list(payload_dir.glob('*.enc')))} ciphertext file(s).")
            print("=" * 65)
            print(" BURNER CYCLE COMPLETE - ACCESS TERMINATED")
            print("=" * 65)


if __name__ == "__main__":
    main()
'''


def create_burner_package(source_path: Path, output_path: Path, countdown_seconds: int, burn_after_reading: bool = True):
    """Packages source files into a standalone Burner Folder."""
    print("\n" + "=" * 65)
    print(" CREATING BURNER FOLDER PACKAGE")
    print("=" * 65)
    print(f"Source Folder     : {source_path}")
    print(f"Destination Folder: {output_path}")
    print(f"Countdown Window  : {countdown_seconds} seconds")
    print(f"Self-Destruct Mode: {'PERMANENT BURN (Wipes files & keys, leaves folder)' if burn_after_reading else 'SAFE (Keep payload)'}")
    print("=" * 65)

    payload_dir = output_path / "payload"
    payload_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate unique Fernet key
    key = Fernet.generate_key()
    fernet = Fernet(key)

    # 2. Encrypt source files
    files = [f for f in source_path.iterdir() if f.is_file()]
    if not files:
        print(f"[ERROR] No files found in source folder: {source_path}")
        sys.exit(1)

    print(f"\n[1/3] Encrypting {len(files)} file(s) into payload/...")
    for file_path in files:
        with open(file_path, "rb") as f:
            content = f.read()

        encrypted = fernet.encrypt(content)
        dest_file = payload_dir / f"{file_path.name}.enc"
        with open(dest_file, "wb") as f:
            f.write(encrypted)
        print(f"  [OK] Encrypted: {file_path.name} -> payload/{dest_file.name}")

    # 3. Create pre-configured launcher.py
    print(f"\n[2/3] Generating launcher.py configured with key and timer...")
    template_path = Path(__file__).resolve().parent / "launcher_template.py"
    if template_path.exists():
        raw_template = template_path.read_text(encoding="utf-8")
    else:
        raw_template = LAUNCHER_TEMPLATE

    launcher_code = raw_template.replace(
        "__FERNET_KEY__", repr(key)
    ).replace(
        "__COUNTDOWN_SECONDS__", str(countdown_seconds)
    ).replace(
        "__BURN_AFTER_READING__", str(burn_after_reading)
    )
    launcher_file = output_path / "launcher.py"
    with open(launcher_file, "w", encoding="utf-8") as f:
        f.write(launcher_code)
    print(f"  [OK] Created: {launcher_file.name}")

    print("\n[3/3] Finalizing...")
    print("\n" + "#" * 65)
    print(" [SUCCESS] BURNER FOLDER CREATED SUCCESSFULLY!")
    print("#" * 65)
    print(f"Folder location: {output_path}")
    print(f"Total files    : {len(files)}")
    print(f"Access timer   : {countdown_seconds}s")
    print(f"Self-destruct  : {'ENABLED (one-time burn)' if burn_after_reading else 'DISABLED'}")
    print("\nTo run or distribute this burner folder:")
    print(f"  cd \"{output_path}\"")
    print("  python launcher.py")
    print("#" * 65 + "\n")


def interactive_wizard():
    print("=" * 65)
    print(" BURNER FOLDER CREATION WIZARD")
    print("=" * 65)
    print("This wizard will package any folder into a self-destructing Burner folder.")
    print("Original files will remain untouched.\n")

    # 1. Ask for source folder
    while True:
        raw_source = input("Enter path to source folder to burn: ").strip().strip('"').strip("'")
        if not raw_source:
            print("Please enter a valid directory path.")
            continue
        source_path = Path(raw_source).resolve()
        if not source_path.exists() or not source_path.is_dir():
            print(f"Directory not found: {source_path}. Please try again.")
            continue
        files = [f for f in source_path.iterdir() if f.is_file()]
        if not files:
            print(f"No files found in '{source_path}'. Please select a folder with files.")
            continue
        print(f"-> Found {len(files)} file(s) in source directory.\n")
        break

    # 2. Ask for destination folder
    default_out_name = f"Burner_{source_path.name}"
    default_out_path = source_path.parent / default_out_name
    raw_output = input(f"Enter destination path for Burner folder [default: {default_out_name}]: ").strip().strip('"').strip("'")
    if not raw_output:
        output_path = default_out_path
    else:
        output_path = Path(raw_output).resolve()

    if output_path.exists():
        confirm = input(f"Warning: '{output_path}' already exists. Overwrite contents? (y/n) [default: y]: ").strip().lower()
        if confirm and not confirm.startswith('y'):
            print("Aborted.")
            sys.exit(0)

    # 3. Ask for countdown duration
    while True:
        raw_timer = input("Enter countdown timer in seconds [default: 60]: ").strip()
        if not raw_timer:
            countdown_seconds = 60
            break
        try:
            countdown_seconds = int(raw_timer)
            if countdown_seconds <= 0:
                print("Timer must be greater than 0.")
                continue
            break
        except ValueError:
            print("Please enter a valid whole number of seconds.")

    # 4. Ask for self-destruct mode
    raw_burn = input("Permanently burn payload files & key after viewing? (y/n) [default: y]: ").strip().lower()
    burn_after_reading = not raw_burn.startswith('n')

    create_burner_package(source_path, output_path, countdown_seconds, burn_after_reading)


def main():
    parser = argparse.ArgumentParser(description="Create a standalone self-destructing Burner Folder.")
    parser.add_argument("--source", "-s", type=str, help="Source folder containing files to burn.")
    parser.add_argument("--output", "-o", type=str, help="Output destination for the burner folder.")
    parser.add_argument("--timer", "-t", type=int, default=60, help="Countdown timer in seconds (default: 60).")
    parser.add_argument("--safe", action="store_true", help="Safe mode: keep payload and launcher on disk after timer.")

    args = parser.parse_args()

    burn_after_reading = not args.safe

    if args.source:
        source_path = Path(args.source).resolve()
        if not source_path.exists() or not source_path.is_dir():
            print(f"[ERROR] Source folder does not exist: {source_path}")
            sys.exit(1)

        if args.output:
            output_path = Path(args.output).resolve()
        else:
            output_path = source_path.parent / f"Burner_{source_path.name}"

        create_burner_package(source_path, output_path, args.timer, burn_after_reading)
    else:
        # Launch interactive CLI wizard
        interactive_wizard()


if __name__ == "__main__":
    main()
