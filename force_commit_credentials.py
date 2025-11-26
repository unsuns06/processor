#!/usr/bin/env python3
"""
Force commit Google Drive credentials and push to HuggingFace
"""

import subprocess
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and show output"""
    print(f"🔄 {description}")
    print(f"   Command: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"   ⚠️  Warning: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def force_commit_credentials():
    """Force commit the Google Drive credentials"""
    print("=" * 60)
    print("🚀 Force Commit Google Drive Credentials")
    print("=" * 60)
    print()

    # Check if files exist locally
    required_files = ['credentials.json', 'settings.yaml', 'client_secrets.json']

    print("📋 Checking required files:")
    for filename in required_files:
        if Path(filename).exists():
            size = Path(filename).stat().st_size
            print(f"   ✅ {filename} ({size} bytes)")
        else:
            print(f"   ❌ {filename} (missing!)")
            return False

    print()

    # Check git status
    success = run_command("git status --porcelain", "Checking git status...")
    if not success:
        return False

    # Add files (force for credentials.json since it was in .gitignore)
    files_to_add = required_files + ['app.py', 'requirements.txt']
    for filename in files_to_add:
        if Path(filename).exists():
            success = run_command(f"git add -f {filename}", f"Adding {filename}...")
            if not success:
                return False

    print()

    # Check if there are changes to commit
    success, output, error = run_command("git status --porcelain", "Checking for changes to commit...")
    if not output.strip():
        print("ℹ️  No changes to commit")
        return True

    print()

    # Commit the changes
    success = run_command(
        'git commit -m "Add Google Drive authentication files and integration"',
        "Committing changes..."
    )
    if not success:
        return False

    print()

    # Push to remote
    success = run_command("git push", "Pushing to remote...")
    if not success:
        return False

    print()
    print("=" * 60)
    print("✅ SUCCESS! Files committed and pushed!")
    print("=" * 60)
    print()
    print("📤 Next steps:")
    print("   1. Wait 1-2 minutes for HuggingFace to process")
    print("   2. Force rebuild the space if needed:")
    print("      - Go to space settings")
    print("      - Click 'Rebuild space' or 'Restart space'")
    print()
    print("   3. Check if it works:")
    print("      Visit: https://your-space.hf.space/debug")
    print("      Should show credentials.json in file listing")
    print()
    print("   4. Final test:")
    print("      Visit: https://your-space.hf.space/check_gdrive")

    return True

if __name__ == "__main__":
    success = force_commit_credentials()
    if not success:
        print()
        print("❌ Failed to commit credentials")
        print("   Check the errors above and try again")
        exit(1)

