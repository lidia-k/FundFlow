#!/bin/bash
set -e

echo "🚀 Setting up FundFlow development environment..."

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is required but not installed."
        exit 1
    fi
}

echo "📋 Checking required tools..."
check_command docker
check_command docker-compose
check_command node
check_command python3

echo "✅ All required tools found!"

# Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# Set up backend
echo "🐍 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Set up frontend
echo "⚛️ Setting up frontend..."
cd frontend
npm install
cd ..

# Create environment file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/{uploads,results,templates} logs

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

# Build initial Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start developing:"
echo "  make dev          # Start with Docker"
echo "  make dev-local    # Start locally"
echo ""
echo "Other useful commands:"
echo "  make help         # Show all available commands"
echo "  make test         # Run tests"
echo "  make lint         # Run linters"
echo ""