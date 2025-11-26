@echo off
echo ========================================
echo Git Push - Allow Secrets Workflow
echo ========================================
echo.

REM Step 1: Add and commit all files
echo [1/3] Adding and committing all files...
git add -A
git commit -m "Update project - include all files"
echo.

REM Step 2: Open secret bypass URLs
echo [2/3] Opening GitHub secret bypass URLs...
echo.
echo Please allow the secrets in your browser:
echo   1. Click "Allow secret" on both pages
echo   2. Come back to this window
echo.

start "" "https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE3s7dlLT8l3o7U1kIjqDvaZ"
timeout /t 2 /nobreak >nul
start "" "https://github.com/unsuns06/processor/security/secret-scanning/unblock-secret/35zrE0A9J0bKSOHWrEbnnnQrHrK"

echo Browser windows opened.
echo.
pause

REM Step 3: Push to GitHub
echo.
echo [3/3] Pushing to GitHub...
git push --force origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! All files pushed to GitHub
    echo ========================================
    echo Repository: https://github.com/unsuns06/processor
    echo.
) else (
    echo.
    echo ========================================
    echo Push failed!
    echo ========================================
    echo.
    echo If secrets are still blocked:
    echo   1. Make sure you clicked "Allow secret" on BOTH pages
    echo   2. Wait a few seconds and try again
    echo   3. Or run: git push --force origin main
    echo.
)

pause

