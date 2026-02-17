#!/bin/bash

# CampusHire.AI Backend Setup Script
# This script sets up the Python environment and installs all dependencies

set -e  # Exit on error

echo "🚀 Setting up CampusHire.AI Backend..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv backend/venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source backend/venv/bin/activate || source backend/venv/Scripts/activate  # Windows fallback

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install Python dependencies
echo ""
echo "📥 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Download spaCy English model
echo ""
echo "📚 Downloading spaCy English language model..."
python3 -m spacy download en_core_web_sm || echo "⚠️  Warning: Could not download spaCy model. Run 'python -m spacy download en_core_web_sm' manually."

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p backend/data/sample_resumes
mkdir -p backend/data
echo "✓ Directories created"

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create a .env file in the project root with:"
    echo "   GEMINI_API_KEY=your_gemini_api_key_here"
    echo "   DEBUG=True"
    echo ""
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
else
    echo "✓ .env file found"
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To start the backend server:"
echo "  1. Activate virtual environment: source backend/venv/bin/activate (or backend\\venv\\Scripts\\activate on Windows)"
echo "  2. Navigate to backend directory: cd backend"
echo "  3. Run: uvicorn main:app --reload"
echo ""
