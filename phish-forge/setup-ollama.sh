#!/bin/bash
# PHISH-FORGE Setup Script for Linux/Kali
# Installs Ollama and downloads the LLaMA 3.1 8B model

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║   PHISH-FORGE Setup - Ollama Installation            ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "[!] Please don't run as root. Ollama should be installed for your user."
    exit 1
fi

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "[+] Ollama is already installed"
    ollama --version
else
    echo "[*] Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    if [ $? -eq 0 ]; then
        echo "[+] Ollama installed successfully"
    else
        echo "[-] Ollama installation failed. Visit: https://ollama.com"
        exit 1
    fi
fi

# Start Ollama service
echo ""
echo "[*] Starting Ollama service..."
ollama serve > /dev/null 2>&1 &
sleep 3

# Check if llama3.1:8b is already downloaded
if ollama list | grep -q "llama3.1:8b"; then
    echo "[+] LLaMA 3.1 8B model already downloaded"
else
    echo "[*] Downloading LLaMA 3.1 8B model (this may take a few minutes)..."
    echo "[*] Model size: ~4.7GB"
    ollama pull llama3.1:8b
    
    if [ $? -eq 0 ]; then
        echo "[+] Model downloaded successfully"
    else
        echo "[-] Model download failed"
        exit 1
    fi
fi

# Install Python dependencies
echo ""
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║   ✅ SETUP COMPLETE                                   ║"
echo "║                                                       ║"
echo "║   Ollama is running on: http://localhost:11434        ║"
echo "║   Model: llama3.1:8b                                  ║"
echo "║                                                       ║"
echo "║   Test it:                                            ║"
echo "║   $ python phish-forge.py generate --intel data.json  ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
