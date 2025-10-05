#!/bin/bash

echo "🔧 Installing system dependencies..."

# Update package list
sudo apt-get update

# Install make, python, and pip
sudo apt-get install -y make python3 python3-pip

echo "✅ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Run: make setup"
echo "  2. Run: source <(make env)"
echo "  3. Start coding! 🚀"
