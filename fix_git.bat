@echo off
echo Fixing Git repository and pushing to GitHub...

REM Configure Git
git config --global user.name "Lnrchaos"
git config --global user.email "lnrchaos@example.com"

REM Remove any existing remote
git remote remove origin 2>nul

REM Add the correct remote
git remote add origin https://github.com/Lnrchaos/Aegis.git

REM Add all files
git add .

REM Create commit
git commit -m "Initial commit: Aegis cybersecurity programming language"

REM Check what branch we're on
git branch

REM Try to push to main
git push -u origin main

REM If main fails, try master
if errorlevel 1 (
    echo Trying master branch...
    git checkout -b master
    git push -u origin master
)

echo Done! Check your GitHub repository.
pause
