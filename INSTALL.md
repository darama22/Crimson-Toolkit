# Installation Guide

## Automated Installation (Recommended)

```bash
git clone https://github.com/your-username/crimson-toolkit
cd crimson-toolkit
chmod +x install.sh
./install.sh
```

This will automatically:
1. Install Python dependencies
2. Install Ollama (local LLM runtime)
3. Download LLaMA 3.1 8B model (~4.7GB)
4. Verify installation

**Time:** ~10-15 minutes (depending on internet speed)

---

## Manual Installation

If you prefer manual setup or the automated installer fails:

### 1. Install Python Dependencies

```bash
pip install -r target-scout/requirements.txt
pip install -r phish-forge/requirements.txt
```

### 2. Install Ollama

**Linux/macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

### 3. Download LLM Model

```bash
ollama pull llama3.1:8b
```

### 4. Verify Installation

```bash
ollama list  # Should show llama3.1:8b
python target-scout/target-scout.py --help  # Should show help
```

---

## System Requirements

- **OS:** Linux (recommended), macOS, Windows
- **Python:** 3.8 or higher
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 10GB free space (for Ollama + model)
- **Internet:** Only for initial setup

---

## Troubleshooting

### "Ollama command not found"
```bash
# Add Ollama to PATH
export PATH=$PATH:/usr/local/bin
```

### "Model download failed"
```bash
# Try with explicit path
ollama pull llama3.1:8b
```

### "Permission denied" on install.sh
```bash
chmod +x install.sh
```

---

## Updating

To update the toolkit:

```bash
cd crimson-toolkit
git pull
./install.sh  # Re-run to update dependencies
```

---

## Uninstalling

To remove the toolkit:

```bash
# Remove Ollama
sudo systemctl stop ollama
sudo rm -rf /usr/local/bin/ollama ~/.ollama

# Remove repository
cd ..
rm -rf crimson-toolkit
```
