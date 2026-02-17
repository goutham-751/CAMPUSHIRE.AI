@echo off
REM CampusHire.AI Backend Setup Script for Windows
REM This script sets up the Python environment and installs all dependencies

echo 🚀 Setting up CampusHire.AI Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

echo ✓ Python version:
python --version

REM Create virtual environment if it doesn't exist
if not exist "backend\venv" (
    echo.
    echo 📦 Creating virtual environment...
    python -m venv backend\venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo.
echo 🔌 Activating virtual environment...
call backend\venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install Python dependencies
echo.
echo 📥 Installing Python dependencies...
cd backend
pip install -r requirements.txt
cd ..

REM Download spaCy English model
echo.
echo 📚 Downloading spaCy English language model...
python -m spacy download en_core_web_sm
if errorlevel 1 (
    echo ⚠️  Warning: Could not download spaCy model. Run 'python -m spacy download en_core_web_sm' manually.
)

REM Create necessary directories
echo.
echo 📁 Creating necessary directories...
if not exist "backend\data\sample_resumes" mkdir backend\data\sample_resumes
if not exist "backend\data" mkdir backend\data
echo ✓ Directories created

REM Check for .env file
echo.
if not exist ".env" (
    echo ⚠️  Warning: .env file not found!
    echo    Please create a .env file in the project root with:
    echo    GEMINI_API_KEY=your_gemini_api_key_here
    echo    DEBUG=True
    echo.
    echo    Get your API key from: https://makersuite.google.com/app/apikey
) else (
    echo ✓ .env file found
)

echo.
echo ✅ Backend setup complete!
echo.
echo To start the backend server:
echo   1. Activate virtual environment: backend\venv\Scripts\activate
echo   2. Navigate to backend directory: cd backend
echo   3. Run: uvicorn main:app --reload
echo.

pause
