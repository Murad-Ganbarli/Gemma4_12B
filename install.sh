#!/bin/bash
set -e

# Output Colors
BLUE="\033[94m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

echo -e "${BLUE}[INSTALLER] Starting setup for Local LLM Chat (Apple Silicon)...${RESET}"

# 1. Verify macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}[ERROR] This application and its GPU optimizations are designed exclusively for macOS.${RESET}"
    exit 1
fi

# 2. Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[ERROR] requirements.txt not found in this directory.${RESET}"
    exit 1
fi

# 3. Verify Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed.${RESET}"
    echo -e "Please install Python 3 via Homebrew: ${YELLOW}brew install python${RESET} or download it from python.org."
    exit 1
fi

# 4. Check for Xcode Command Line Tools (required to compile Metal shaders)
if ! xcode-select -p &> /dev/null; then
    echo -e "${YELLOW}[WARNING] Xcode Command Line Tools are missing. Installing now...${RESET}"
    xcode-select --install
    echo -e "${YELLOW}[INFO] Please complete the pop-up installer on your screen, then run this install script again once finished.${RESET}"
    exit 0
fi

# 5. Create Virtual Environment
if [ -d ".venv" ]; then
    echo -e "${BLUE}[INSTALLER] Virtual environment (.venv) already exists. Skipping creation...${RESET}"
else
    echo -e "${BLUE}[INSTALLER] Creating clean virtual environment (.venv)...${RESET}"
    python3 -m venv .venv
fi

# 6. Activate Environment
echo -e "${BLUE}[INSTALLER] Activating environment...${RESET}"
source .venv/bin/activate

# 7. Upgrade Core Packaging Tools
echo -e "${BLUE}[INSTALLER] Upgrading pip, setuptools, and wheel...${RESET}"
pip install --upgrade pip setuptools wheel

# 8. Install requirements with Apple Metal compilation
echo -e "${BLUE}[INSTALLER] Installing dependencies from requirements.txt with Apple Metal compilation...${RESET}"
CMAKE_ARGS="-GGML_METAL=on" pip install -r requirements.txt --no-cache-dir

echo -e "${GREEN}[SUCCESS] Setup complete!${RESET}"
echo -e "${BLUE}------------------------------------------------------------${RESET}"
echo -e "${BLUE}To run your server:${RESET}"
echo -e "  1. Activate the environment:  ${GREEN}source .venv/bin/activate${RESET}"
echo -e "  2. Launch the script:         ${GREEN}python run.py${RESET}"
echo -e "${BLUE}------------------------------------------------------------${RESET}"