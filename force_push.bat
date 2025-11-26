@echo off
echo ========================================
echo Git Force Push Script
echo ========================================
echo.

REM Check if .git directory exists
if not exist ".git" (
    echo Initializing new git repository...
    git init
    if errorlevel 1 (
        echo ERROR: Failed to initialize git repository
        pause
        exit /b 1
    )
    echo Git repository initialized successfully.
    echo.
)

REM Check if remote 'origin' exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo Setting up remote repository...
    set /p remote_url="Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): "
    git remote add origin !remote_url!
    if errorlevel 1 (
        echo ERROR: Failed to add remote repository
        pause
        exit /b 1
    )
    echo Remote 'origin' added successfully.
    echo.
) else (
    echo Remote repository already configured.
    echo.
)

REM Check git status
echo Checking repository status...
git status
echo.

REM Add all files
echo Adding all files to git...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files
    pause
    exit /b 1
)
echo Files added successfully.
echo.

REM Create commit
echo Creating a new commit...
git commit -m "Update project"
if errorlevel 1 (
    echo Note: No changes to commit or commit failed
    echo Continuing with push anyway...
)
echo.

REM Get current branch name
for /f "delims=" %%i in ('git branch --show-current') do set branch=%%i
if "%branch%"=="" (
    set branch=main
    echo Renaming default branch to 'main'...
    git branch -M main
)

echo Current branch: %branch%
echo.

REM Confirm force push
echo WARNING: You are about to FORCE PUSH to the remote repository!
echo This will overwrite remote history. Make sure this is what you want.
echo.
set /p confirm="Type 'yes' to continue with force push: "
if not "%confirm%"=="yes" (
    echo Force push cancelled.
    pause
    exit /b 0
)

REM Force push
echo Force pushing to remote repository (branch: %branch%)...
git push --force origin %branch%
if errorlevel 1 (
    echo.
    echo ERROR: Push failed. This could be due to:
    echo - Authentication issues (you may need to enter credentials)
    echo - Network connectivity problems
    echo - Remote repository permissions
    echo.
    echo Try running: git push --force origin %branch%
    echo Or set up authentication with: git config credential.helper store
    pause
    exit /b 1
)

echo.
echo ========================================
echo Push completed successfully!
echo ========================================
pause
