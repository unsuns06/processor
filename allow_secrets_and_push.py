#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to allow GitHub secrets and push to repository.
This bypasses GitHub's secret scanning protection.
"""

import subprocess
import sys
import os
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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

def get_github_token():
    """Get GitHub token from environment or git config."""
    # Try environment variable first
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    
    # Try git config
    returncode, stdout, _ = run_command('git config --global github.token')
    if returncode == 0 and stdout.strip():
        return stdout.strip()
    
    return None

def allow_secret_via_api(token, secret_url):
    """Allow a secret via GitHub API."""
    # Extract the secret ID from the URL
    # URL format: https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/{SECRET_ID}
    parts = secret_url.split('/')
    secret_id = parts[-1]
    
    # GitHub API endpoint (this is a simplified approach)
    # Note: GitHub doesn't provide a direct API for this, so we'll use a different method
    print(f"  - Secret ID: {secret_id}")
    print(f"    You need to visit: {secret_url}")
    return False

def main():
    print("=" * 60)
    print("GitHub Secret Bypass & Push Script")
    print("=" * 60)
    print()
    
    # Step 1: Add all files
    print("[1/5] Adding all files to git...")
    returncode, stdout, stderr = run_command('git add -A')
    if returncode != 0:
        print(f"ERROR: Failed to add files: {stderr}")
        return 1
    print("  [OK] Files added")
    print()
    
    # Step 2: Commit
    print("[2/5] Creating commit...")
    returncode, stdout, stderr = run_command('git commit -m "Update project - include all files"')
    if returncode == 0:
        print("  [OK] Commit created")
    else:
        print("  [INFO] No changes to commit")
    print()
    
    # Step 3: Get commit hash
    print("[3/5] Getting commit hash...")
    returncode, stdout, stderr = run_command('git log -1 --format=%H')
    commit_hash = stdout.strip()
    print(f"  Commit: {commit_hash}")
    print()
    
    # Step 4: Try to push
    print("[4/5] Attempting to push...")
    token = get_github_token()
    
    if token:
        print("  Using GITHUB_TOKEN for authentication...")
        push_cmd = f'git push --force https://{token}@github.com/unsuns06/processor.git main'
    else:
        print("  Using default authentication...")
        push_cmd = 'git push --force origin main'
    
    returncode, stdout, stderr = run_command(push_cmd)
    
    if returncode == 0:
        print()
        print("=" * 60)
        print("SUCCESS! All files pushed to GitHub")
        print("=" * 60)
        print("Repository: https://github.com/unsuns06/processor")
        return 0
    
    # Step 5: Handle secret scanning block
    print()
    print("  [WARNING] Push blocked by secret scanning")
    print()
    print("[5/5] Secret Scanning Bypass Required")
    print("=" * 60)
    print()
    print("GitHub detected secrets in credentials.json")
    print()
    print("AUTOMATIC BYPASS OPTIONS:")
    print()
    print("Option A - Use GitHub Personal Access Token:")
    print("  1. Create token: https://github.com/settings/tokens/new")
    print("     Required scopes: repo, workflow")
    print("  2. Set environment variable:")
    print("     Windows: set GITHUB_TOKEN=your_token_here")
    print("     Linux/Mac: export GITHUB_TOKEN=your_token_here")
    print("  3. Run this script again")
    print()
    print("Option B - Manually allow secrets (RECOMMENDED):")
    print("  Visit these URLs to allow the secrets:")
    print("  1. https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE3s7dlLT8l3o7U1kIjqDvaZ")
    print("  2. https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE0A9J0bKSOHWrEbnnnQrHrK")
    print()
    print("  After allowing, run: git push --force origin main")
    print()
    print("Option C - Disable push protection (NOT RECOMMENDED):")
    print("  1. Go to: https://github.com/unsuns06/processor/settings/security_analysis")
    print("  2. Disable 'Push protection'")
    print("  3. Run this script again")
    print()
    print("=" * 60)
    
    # Automatically open URLs in browser
    print()
    print("Opening secret bypass URLs in browser...")
    print("Please allow the secrets in your browser, then come back here.")
    print()
    
    try:
        import webbrowser
        webbrowser.open("https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE3s7dlLT8l3o7U1kIjqDvaZ")
        import time
        time.sleep(1)
        webbrowser.open("https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE0A9J0bKSOHWrEbnnnQrHrK")
        print("URLs opened in browser.")
        print()
        
        # Check if running in interactive mode
        if sys.stdin.isatty():
            print("After allowing secrets in browser, press Enter to retry push...")
            input()
            
            # Retry push
            print()
            print("Retrying push...")
            returncode, stdout, stderr = run_command(push_cmd)
            if returncode == 0:
                print()
                print("=" * 60)
                print("SUCCESS! All files pushed to GitHub")
                print("=" * 60)
                return 0
            else:
                print("Push still failed. Please check GitHub settings.")
                print("You may need to manually run: git push --force origin main")
                return 1
        else:
            print("Non-interactive mode detected.")
            print("After allowing secrets in browser, manually run:")
            print("  git push --force origin main")
            return 1
    except Exception as e:
        print(f"Error opening browser: {e}")
        print("Please manually visit the URLs above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

