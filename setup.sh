#!/bin/bash
# Setup script for Batch Print Hot Folder

echo "========================================"
echo "Batch Print Hot Folder - Setup"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi
echo ""

# Create config from example if it doesn't exist
if [ ! -f "config.json" ]; then
    echo "Creating config.json from example..."
    cp config.example.json config.json
    echo "✓ Created config.json"
    echo ""
    echo "⚠ IMPORTANT: Please edit config.json to configure your hot folders and printers"
    echo ""
else
    echo "✓ config.json already exists"
    echo ""
fi

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json to configure your hot folders"
echo "2. Run the service with: ./run.sh or python3 batch_print.py"
echo ""
echo "For help finding printer names:"
echo "  Windows: wmic printer get name"
echo "  macOS/Linux: lpstat -p | awk '{print \$2}'"
echo ""
