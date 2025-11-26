#!/usr/bin/env python3
"""
Retry push until successful - waits for user to allow secrets
"""

import subprocess
import time
import sys

def try_push():
    """Try to push to GitHub."""
    result = subprocess.run(
        'git push --force origin main',
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr

def main():
    print("=" * 70)
    print("Waiting for GitHub secret approval...")
    print("=" * 70)
    print()
    print("Please allow the secrets in your browser:")
    print("  1. https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE3s7dlLT8l3o7U1kIjqDvaZ")
    print("  2. https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE0A9J0bKSOHWrEbnnnQrHrK")
    print()
    print("This script will automatically retry the push every 5 seconds...")
    print("Press Ctrl+C to stop")
    print()
    
    attempt = 1
    while True:
        print(f"Attempt {attempt}: Trying to push...", end=" ", flush=True)
        
        success, error = try_push()
        
        if success:
            print("SUCCESS!")
            print()
            print("=" * 70)
            print("All files successfully pushed to GitHub!")
            print("=" * 70)
            print("Repository: https://github.com/unsuns06/processor")
            return 0
        else:
            if "secret" in error.lower() or "GH013" in error:
                print("Still blocked by secret scanning")
            else:
                print("Failed with different error:")
                print(error)
                return 1
        
        attempt += 1
        print("Waiting 5 seconds before retry...")
        print()
        time.sleep(5)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("Stopped by user. You can manually push with:")
        print("  git push --force origin main")
        sys.exit(1)

