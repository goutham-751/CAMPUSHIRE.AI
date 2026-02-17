@echo off
REM CampusHire.AI Frontend Setup Script for Windows
REM This script sets up the frontend environment and installs dependencies

echo 🚀 Setting up CampusHire.AI Frontend...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16 or higher.
    exit /b 1
)

echo ✓ Node.js version:
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed. Please install npm.
    exit /b 1
)

echo ✓ npm version:
npm --version

REM Navigate to frontend directory
cd frontend

REM Install dependencies
echo.
echo 📥 Installing frontend dependencies...
call npm install

REM Check for .env file
echo.
if not exist ".env" (
    echo ⚠️  Warning: .env file not found in frontend directory!
    echo    Creating .env file with default values...
    echo VITE_API_URL=http://127.0.0.1:8000 > .env
    echo ✓ .env file created
) else (
    echo ✓ .env file found
)

cd ..

echo.
echo ✅ Frontend setup complete!
echo.
echo To start the frontend development server:
echo   1. Navigate to frontend directory: cd frontend
echo   2. Run: npm run dev
echo.

pause
