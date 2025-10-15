#!/bin/bash
# Environment setup script

echo "Setting up Redactopii environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r Redactopii/requirements.txt

# Install Octopii dependencies if needed
if [ -f "Octopii/requirements.txt" ]; then
    pip install -r Octopii/requirements.txt
fi

echo "Environment setup complete!"
echo "Activate with: source venv/bin/activate"