#!/bin/bash
set -e

# Crimson Toolkit Installer for Kali Linux / Debian
# Auto-handles venv to bypass PEP 668 restrictions

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Crimson Toolkit Installer${NC}"
echo -e "${BLUE}[*] Detected OS: $(uname -s)${NC}"

# 1. Install system dependencies
echo -e "\n${BLUE}[*] Checking system dependencies...${NC}"
if [ -x "$(command -v apt)" ]; then
    echo "Installing python3-venv, nmap, golang..."
    sudo apt update -qq
    sudo apt install -y python3-venv nmap golang-go
else
    echo -e "${RED}[!] apt not found. Make sure you have python3-venv, nmap, and go installed.${NC}"
fi

# 2. Setup Virtual Environment
echo -e "\n${BLUE}[*] Setting up Python Virtual Environment (to bypass PEP 668)...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}[+] venv created.${NC}"
else
    echo -e "${GREEN}[+] venv already exists.${NC}"
fi

# 3. Install Python Dependencies inside venv
echo -e "\n${BLUE}[*] Installing Python requirements...${NC}"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Optional: Setup Ollama
echo -e "\n${BLUE}[?] Do you want to install/setup Ollama for AI features? (High RAM usage) [y/N]${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    if ! [ -x "$(command -v ollama)" ]; then
        curl https://ollama.ai/install.sh | sh
    fi
    echo -e "${BLUE}[*] Pulling llama3.1:8b model...${NC}"
    ollama pull llama3.1:8b
fi

# 5. Create Launchers
echo -e "\n${BLUE}[*] Creating universal launcher 'crimson'...${NC}"
cat <<EOF > crimson
#!/bin/bash
# Launcher that uses the local venv automatically
BASE_DIR="\$(dirname "\$(realpath "\$0")")"
VENV_PYTHON="\$BASE_DIR/venv/bin/python"

if [ "\$#" -lt 1 ]; then
    echo "Usage: ./crimson <tool-directory>/<tool-script.py> [args]"
    echo "Example: ./crimson target-scout/target-scout.py --company Test"
    exit 1
fi

TOOL=\$1
shift
\$VENV_PYTHON \$TOOL "\$@"
EOF

chmod +x crimson
chmod +x install.sh

echo -e "\n${GREEN}╔═════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           INSTALLATION COMPLETE! (Recuerda actualizar)          ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════════════════════════════════╝${NC}"
echo -e "\nUsage examples:"
echo -e "  1. Use the launcher (Recommended):"
echo -e "     ${BLUE}./crimson target-scout/target-scout.py --help${NC}"
echo -e "     ${BLUE}./crimson c2-chameleon/c2-chameleon.py${NC}"
echo -e "\n  2. Or activate venv manually:"
echo -e "     ${BLUE}source venv/bin/activate${NC}"
echo -e "     ${BLUE}python target-scout/target-scout.py${NC}"
