#!/bin/bash

# CampusHire.AI Frontend Setup Script
# This script sets up the frontend environment and installs dependencies

set -e  # Exit on error

echo "🚀 Setting up CampusHire.AI Frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node --version)
echo "✓ Node.js version: $NODE_VERSION"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✓ npm version: $(npm --version)"

# Navigate to frontend directory
cd frontend

# Install dependencies
echo ""
echo "📥 Installing frontend dependencies..."
npm install

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found in frontend directory!"
    echo "   Creating .env file with default values..."
    echo "VITE_API_URL=http://127.0.0.1:8000" > .env
    echo "✓ .env file created"
else
    echo "✓ .env file found"
fi

cd ..

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "To start the frontend development server:"
echo "  1. Navigate to frontend directory: cd frontend"
echo "  2. Run: npm run dev"
echo ""
