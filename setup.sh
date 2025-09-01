#!/bin/bash
# Setup script for Local Coding Agent (LCA)

echo "=== Local Coding Agent Setup ==="
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo
echo "Creating virtual environment..."
python3 -m venv venv || {
    echo "❌ Failed to create virtual environment"
    echo "   You may need to install: sudo apt install python3-venv"
    exit 1
}

# Activate virtual environment
echo "✓ Virtual environment created"
echo
echo "To complete setup:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo
echo "2. Install dependencies:"
echo "   pip install -e ."
echo
echo "3. Copy and configure .env file:"
echo "   cp .env.example .env"
echo "   # Edit .env and add your LLM_API_KEY"
echo
echo "4. Test the installation:"
echo "   lca --help"
echo
echo "5. Start using LCA:"
echo "   lca whoami    # Check configuration"
echo "   lca analyze   # Analyze your project"
echo "   lca ask \"How do I implement a REST API?\""
echo
echo "For more information, see README.md"