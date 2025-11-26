@echo off
setlocal enabledelayedexpansion

REM Configuration - Edit these lines
set REMOTE_URL=https://github.com/unsuns06/processor.git
set BRANCH=main

echo ========================================
echo Git Quick Push Script
echo ========================================
echo.

REM Initialize git if needed
if not exist ".git" (
    echo Initializing git repository...
    git init
    git branch -M %BRANCH%
    git remote add origin %REMOTE_URL%
    echo Repository initialized.
    echo.
)

REM Add and commit
echo Adding all files...
git add .

echo Creating commit...
git commit -m "Update project - %date% %time%"

REM Push
echo Pushing to %REMOTE_URL% (branch: %BRANCH%)...
git push -u origin %BRANCH%

if errorlevel 1 (
    echo.
    echo Push failed. Trying with --force flag...
    git push --force origin %BRANCH%
    if errorlevel 1 (
        echo.
        echo ERROR: Push still failed. Please check:
        echo 1. Your GitHub credentials
        echo 2. Repository URL is correct
        echo 3. You have write access to the repository
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Push completed successfully!
echo ========================================
pause

