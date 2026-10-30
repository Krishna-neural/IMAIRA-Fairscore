#!/usr/bin/env bash
# ======================================================================
#  IMAIRA FairScore — One-Click Launcher for macOS and Linux
# ======================================================================

set -e

echo "======================================================================"
echo " IMAIRA FairScore — Starting Setup & Server"
echo "======================================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not found! Please install Python 3.10+."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[2/3] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Run pre-flight checks
python3 check_setup.py

echo ""
echo "[3/3] Starting IMAIRA FairScore server on http://localhost:8002..."
echo "(Press Ctrl+C to stop the server)"
echo ""

python3 -m api.main
