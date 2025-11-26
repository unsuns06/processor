#!/usr/bin/env python3
"""
Check HuggingFace Space status and provide git commands to fix issues
"""

import subprocess
import os
from pathlib import Path

def run_git_command(command):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_huggingface_status():
    """Check the current status of the HuggingFace deployment"""
    print("=" * 60)
    print("🔍 HuggingFace Space Status Check")
    print("=" * 60)
    print()

    # Check if we're in a git repository
    success, output, error = run_git_command("git status")
    if not success:
        print("❌ Not in a git repository!")
        print("   Make sure you're in the correct directory")
        return

    print("✅ Git repository found")
    print()

    # Check git status
    success, output, error = run_git_command("git status --porcelain")
    has_changes = len(output) > 0

    print("📊 Git Status:")
    if has_changes:
        print(f"   📝 Has uncommitted changes: {len(output)} files")
        print("   Files with changes:")
        for line in output.split('\n'):
            if line.strip():
                status = line[:2]
                filename = line[3:]
                if status == '??':
                    print(f"     🆕 {filename} (new file)")
                elif status.startswith('M'):
                    print(f"     📝 {filename} (modified)")
                elif status.startswith('D'):
                    print(f"     🗑️  {filename} (deleted)")
        print()
        print("🔧 To fix: Commit these changes")
        print("   git add .")
        print("   git commit -m 'Update Google Drive integration'")
        print("   git push")
    else:
        print("   ✅ Working directory clean (all changes committed)")

    print()

    # Check what files are tracked vs untracked
    print("📋 File Tracking Status:")

    important_files = [
        'credentials.json',
        'settings.yaml',
        'client_secrets.json',
        'app.py',
        'requirements.txt'
    ]

    for filename in important_files:
        # Check if file exists locally
        if Path(filename).exists():
            # Check if tracked by git
            success, output, error = run_git_command(f"git ls-files --error-unmatch {filename}")
            is_tracked = success and filename in output

            success, output, error = run_git_command(f"git status --porcelain {filename}")
            has_local_changes = filename in output

            if is_tracked:
                if has_local_changes:
                    print(f"   ✅ {filename} (tracked, has local changes)")
                else:
                    print(f"   ✅ {filename} (tracked, no changes)")
            else:
                print(f"   ❌ {filename} (NOT tracked by git)")
                print(f"      Run: git add -f {filename}")
        else:
            print(f"   ❌ {filename} (file not found locally)")

    print()

    # Check recent commits
    print("📜 Recent Commits:")
    success, output, error = run_git_command("git log --oneline -5")
    if success:
        for line in output.split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print(f"   ❌ Error getting git log: {error}")

    print()

    # Check current branch
    success, output, error = run_git_command("git branch")
    if success:
        print(f"📍 Current branch: {output.replace('*', '').strip()}")

    print()

    # Provide recommendations
    print("=" * 60)
    print("🔧 RECOMMENDATIONS:")
    print("=" * 60)

    if has_changes:
        print("1. 📝 Commit your changes:")
        print("   git add .")
        print("   git commit -m 'Add Google Drive authentication files'")
        print("   git push")
        print()

    print("2. 🔄 Force rebuild the space:")
    print("   - Go to your HuggingFace space settings")
    print("   - Look for 'Rebuild space' or 'Restart space' option")
    print("   - Or push a small change to trigger automatic rebuild")
    print()

    print("3. ⏳ Wait 2-3 minutes for rebuild to complete")
    print()

    print("4. 🔍 Verify the fix:")
    print("   Visit: https://your-space.hf.space/debug")
    print("   Should show credentials.json in 'files.important_files'")
    print()
    print("5. ✅ Final test:")
    print("   Visit: https://your-space.hf.space/check_gdrive")
    print("   Should show: 'status': 'success'")

if __name__ == "__main__":
    check_huggingface_status()

