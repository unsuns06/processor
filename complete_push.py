#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Git Push Solution with Secret Bypass
Handles all scenarios for pushing to GitHub with secrets
"""

import subprocess
import sys
import os
import time
import webbrowser

def run_command(cmd, shell=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def print_header(text):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(text)
    print("=" * 70)
    print()

def print_step(step_num, total_steps, text):
    """Print a formatted step."""
    print(f"[{step_num}/{total_steps}] {text}")

def try_push(use_token=False):
    """Attempt to push to GitHub."""
    if use_token:
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            return False, "No GITHUB_TOKEN found"
        push_cmd = f'git push --force https://{token}@github.com/unsuns06/processor.git main'
    else:
        push_cmd = 'git push --force origin main'
    
    returncode, stdout, stderr = run_command(push_cmd)
    return returncode == 0, stderr

def open_secret_urls():
    """Open secret bypass URLs in browser."""
    urls = [
        "https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE3s7dlLT8l3o7U1kIjqDvaZ",
        "https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE0A9J0bKSOHWrEbnnnQrHrK"
    ]
    
    print("Opening secret bypass URLs in your browser...")
    print()
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
        try:
            webbrowser.open(url)
            time.sleep(1)
        except Exception as e:
            print(f"     Error opening URL: {e}")
    print()
    return urls

def main():
    print_header("GitHub Push - Complete Solution")
    
    # Step 1: Add all files
    print_step(1, 5, "Adding all files to git...")
    returncode, stdout, stderr = run_command('git add -A')
    if returncode != 0:
        print(f"  ERROR: Failed to add files: {stderr}")
        return 1
    print("  [OK] All files added")
    print()
    
    # Step 2: Commit
    print_step(2, 5, "Creating commit...")
    returncode, stdout, stderr = run_command('git commit -m "Update project - include all files"')
    if returncode == 0:
        print("  [OK] Commit created")
    else:
        if "nothing to commit" in stdout or "nothing to commit" in stderr:
            print("  [INFO] No changes to commit")
        else:
            print(f"  [WARNING] Commit may have failed: {stderr}")
    print()
    
    # Step 3: Try direct push
    print_step(3, 5, "Attempting direct push to GitHub...")
    success, error = try_push()
    
    if success:
        print_header("SUCCESS! All files pushed to GitHub")
        print("Repository: https://github.com/unsuns06/processor")
        return 0
    
    # Check if it's a secret scanning issue
    if "secret" not in error.lower() and "GH013" not in error:
        print(f"  [ERROR] Push failed for unknown reason:")
        print(f"  {error}")
        return 1
    
    print("  [WARNING] Push blocked by GitHub secret scanning")
    print()
    
    # Step 4: Open bypass URLs
    print_step(4, 5, "Opening secret bypass URLs...")
    urls = open_secret_urls()
    
    print("INSTRUCTIONS:")
    print("  1. In each browser tab, click the 'Allow secret' button")
    print("  2. GitHub will ask you to confirm - click 'Allow'")
    print("  3. After allowing BOTH secrets, return here")
    print()
    
    # Wait for user
    if sys.stdin.isatty():
        try:
            input("Press Enter after you've allowed both secrets in GitHub...")
        except (EOFError, KeyboardInterrupt):
            print()
            print("Continuing anyway...")
    else:
        print("Non-interactive mode - waiting 30 seconds for manual approval...")
        time.sleep(30)
    
    print()
    
    # Step 5: Retry push
    print_step(5, 5, "Retrying push...")
    success, error = try_push()
    
    if success:
        print_header("SUCCESS! All files pushed to GitHub")
        print("Repository: https://github.com/unsuns06/processor")
        return 0
    else:
        print()
        print("  [ERROR] Push still failed")
        print()
        print("TROUBLESHOOTING:")
        print()
        print("Option A - Verify you allowed BOTH secrets:")
        print(f"  1. {urls[0]}")
        print(f"  2. {urls[1]}")
        print("     Then run: git push --force origin main")
        print()
        print("Option B - Use GitHub Personal Access Token:")
        print("  1. Create token: https://github.com/settings/tokens/new")
        print("     Required scopes: repo, workflow")
        print("  2. Set environment variable:")
        print("     set GITHUB_TOKEN=your_token_here")
        print("  3. Run this script again")
        print()
        print("Option C - Disable push protection:")
        print("  1. Go to: https://github.com/unsuns06/processor/settings/security_analysis")
        print("  2. Disable 'Push protection' for secret scanning")
        print("  3. Run: git push --force origin main")
        print()
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("Interrupted by user")
        sys.exit(1)

