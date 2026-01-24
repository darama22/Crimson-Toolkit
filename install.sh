#!/bin/bash
#
# CRIMSON Toolkit - Automated Installer
# Installs all dependencies including Ollama and LLaMA 3.1 model
#
# Usage:
#   git clone https://github.com/your-repo/crimson-toolkit
#   cd crimson-toolkit
#   chmod +x install.sh
#   ./install.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}"
cat << "EOF"
 ██████╗██████╗ ██╗███╗   ███╗███████╗ ██████╗ ███╗   ██╗
██╔════╝██╔══██╗██║████╗ ████║██╔════╝██╔═══██╗████╗  ██║
██║     ██████╔╝██║██╔████╔██║███████╗██║   ██║██╔██╗ ██║
██║     ██╔══██╗██║██║╚██╔╝██║╚════██║██║   ██║██║╚██╗██║
╚██████╗██║  ██║██║██║ ╚═╝ ██║███████║╚██████╔╝██║ ╚████║
 ╚═════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
                                                           
         AI-Powered Red Team Toolkit - Installer
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}[!] Please don't run as root${NC}"
    exit 1
fi

echo -e "${BLUE}[*] Starting automated installation...${NC}\n"

# ============================================
# Step 1: Install Python dependencies
# ============================================
echo -e "${YELLOW}[1/4] Installing Python dependencies...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[-] Python 3 is not installed. Please install Python 3.8+${NC}"
    exit 1
fi

echo -e "${BLUE}[*] Installing TARGET-SCOUT dependencies...${NC}"
pip install -q -r target-scout/requirements.txt

echo -e "${BLUE}[*] Installing PHISH-FORGE dependencies...${NC}"
pip install -q -r phish-forge/requirements.txt

echo -e "${GREEN}[+] Python dependencies installed${NC}\n"

# ============================================
# Step 2: Install Ollama
# ============================================
echo -e "${YELLOW}[2/4] Installing Ollama (local LLM runtime)...${NC}"

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}[+] Ollama is already installed${NC}"
    ollama --version
else
    echo -e "${BLUE}[*] Downloading and installing Ollama...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Ollama installed successfully${NC}"
    else
        echo -e "${RED}[-] Ollama installation failed${NC}"
        echo -e "${YELLOW}[!] Please install manually from: https://ollama.com${NC}"
        exit 1
    fi
fi

echo ""

# ============================================
# Step 3: Start Ollama and download model
# ============================================
echo -e "${YELLOW}[3/4] Setting up LLaMA 3.1 model...${NC}"

# Start Ollama in background
echo -e "${BLUE}[*] Starting Ollama service...${NC}"
ollama serve > /dev/null 2>&1 &
sleep 3

# Check if model is already downloaded
if ollama list | grep -q "llama3.1:8b"; then
    echo -e "${GREEN}[+] LLaMA 3.1 8B model already downloaded${NC}"
else
    echo -e "${BLUE}[*] Downloading LLaMA 3.1 8B model...${NC}"
    echo -e "${BLUE}[*] This is a one-time download (~4.7GB, may take 5-10 minutes)${NC}"
    echo -e "${BLUE}[*] Please be patient...${NC}\n"
    
    ollama pull llama3.1:8b
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Model downloaded successfully${NC}"
    else
        echo -e "${RED}[-] Model download failed${NC}"
        exit 1
    fi
fi

echo ""

# ============================================
# Step 4: Verify installation
# ============================================
echo -e "${YELLOW}[4/4] Verifying installation...${NC}"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}[+] Ollama service is running${NC}"
else
    echo -e "${YELLOW}[!] Ollama service not accessible (this is OK, will start when needed)${NC}"
fi

# Check if tools are ready
if [ -f "target-scout/target-scout.py" ] && [ -f "phish-forge/phish-forge.py" ]; then
    echo -e "${GREEN}[+] All tools are ready${NC}"
else
    echo -e "${RED}[-] Some tools are missing${NC}"
fi

echo ""

# ============================================
# Installation Complete
# ============================================
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                   INSTALLATION COMPLETE                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}The CRIMSON Toolkit is now ready to use!${NC}\n"

echo -e "${YELLOW}📚 Quick Start:${NC}"
echo ""
echo -e "  ${GREEN}1. Start Ollama (run once after reboot):${NC}"
echo -e "     ollama serve &"
echo ""
echo -e "  ${GREEN}2. Scan a target:${NC}"
echo -e "     cd target-scout"
echo -e "     python target-scout.py --company \"TechCorp\" --output intel.json"
echo ""
echo -e "  ${GREEN}3. Generate phishing email:${NC}"
echo -e "     cd ../phish-forge"
echo -e "     python phish-forge.py generate --intel ../target-scout/intel.json"
echo ""
echo -e "  ${GREEN}4. Start credential capture server:${NC}"
echo -e "     python capture-server.py"
echo ""

echo -e "${YELLOW}📖 Documentation:${NC}"
echo -e "  • Main README: ${BLUE}./README.md${NC}"
echo -e "  • TARGET-SCOUT: ${BLUE}./target-scout/README.md${NC}"
echo -e "  • PHISH-FORGE: ${BLUE}./phish-forge/README.md${NC}"
echo ""

echo -e "${YELLOW}⚠️  Legal Notice:${NC}"
echo -e "  This toolkit is for ${RED}AUTHORIZED TESTING ONLY${NC}"
echo -e "  Unauthorized use is illegal"
echo ""

echo -e "${GREEN}Happy hacking! 🚀${NC}\n"
