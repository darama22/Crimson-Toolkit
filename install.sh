#!/bin/bash
set -e

# Crimson Toolkit Installer for Kali Linux / Debian
# Auto-handles venv AND creates global commands AND sets up AI

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[*] Crimson Toolkit Installer${NC}"
echo -e "${BLUE}[*] Detected OS: $(uname -s)${NC}"

# 1. System Dependencies
echo -e "\n${BLUE}[*] Checking system dependencies...${NC}"
if [ -x "$(command -v apt)" ]; then
    echo "Installing python3-venv, nmap, golang..."
    sudo apt update -qq
    sudo apt install -y python3-venv nmap golang-go curl
else
    echo -e "${RED}[!] apt not found. Make sure system deps are installed.${NC}"
fi

# 2. Setup Venv
echo -e "\n${BLUE}[*] Setting up Python Virtual Environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}[+] venv created.${NC}"
else
    echo -e "${GREEN}[+] venv exists.${NC}"
fi

# 3. Install Python Deps
echo -e "\n${BLUE}[*] Installing Python requirements...${NC}"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Global Shortcuts Setup
echo -e "\n${BLUE}[*] Installing global commands (requires sudo)...${NC}"
INSTALL_DIR=$(pwd)
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"

# Function to create global wrapper
create_shortcut() {
    TOOL_NAME=$1
    SCRIPT_PATH=$2
    
    echo "Creating command: $TOOL_NAME"
    
    # Create wrapper script content
    cat <<EOF > "$TOOL_NAME.tmp"
#!/bin/bash
cd "$INSTALL_DIR"
exec "$VENV_PYTHON" "$SCRIPT_PATH" "\$@"
EOF
    
    # Move to /usr/local/bin
    sudo mv "$TOOL_NAME.tmp" "/usr/local/bin/$TOOL_NAME"
    sudo chmod +x "/usr/local/bin/$TOOL_NAME"
}

# Create shortcuts for all tools
create_shortcut "target-scout" "target-scout/target-scout.py"
create_shortcut "phish-forge" "phish-forge/phish-forge.py"
create_shortcut "payload-chef" "payload-chef/payload-chef.py"
create_shortcut "c2-chameleon" "c2-chameleon/c2-chameleon.py"
create_shortcut "vuln-oracle" "vuln-oracle/vuln-oracle.py"
create_shortcut "defense-radar" "defense-radar/defense-radar.py"

echo -e "${GREEN}[+] Shortcuts installed in /usr/local/bin${NC}"

# 5. AI Model Setup (AUTO)
echo -e "\n${BLUE}[*] Configuring AI Engine (Ollama)...${NC}"

# Check if Ollama is installed
if ! [ -x "$(command -v ollama)" ]; then
    echo "Ollama not found. Installing..."
    curl https://ollama.ai/install.sh | sh
else
    echo -e "${GREEN}[+] Ollama is installed.${NC}"
fi

# Check if Ollama service is running, if not start it temporarily
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5 # Wait for it to start
fi

# Pull the model automatically
echo -e "${BLUE}[*] Downloading AI Model (llama3.1:8b)... This might take a while.${NC}"
ollama pull llama3.1:8b

echo -e "${GREEN}[+] AI Model ready.${NC}"

echo -e "\n${GREEN}╔═════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           INSTALLATION COMPLETE! AI ENGINE READY                ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════════════════════════════════╝${NC}"
echo -e "\nNow you can run tools from ANYWHERE:"
echo -e "  $ target-scout --company Test"
echo -e "  $ phish-forge generate --template instagram"
