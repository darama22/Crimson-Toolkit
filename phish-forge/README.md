# PHISH-FORGE

**AI-Powered Phishing Campaign Generator for Red Team Operations**

Part of the CRIMSON Toolkit | **Status:** ✅ Functional

---

## 🎯 What It Does

PHISH-FORGE generates realistic phishing emails using **local AI (Ollama)** based on OSINT data from TARGET-SCOUT, then serves professional landing pages to capture credentials.

**Complete attack chain:**
1. Read company intelligence → 2. Generate AI email → 3. Serve fake login → 4. Capture credentials

---

## 🚀 Quick Start

### Prerequisites

**Install Ollama** (one-time setup):

```bash
# Automated (Linux/Kali)
chmod +x setup-ollama.sh
./setup-ollama.sh

# Manual: https://ollama.com/download
# Then: ollama pull llama3.1:8b
```

### Usage

```bash
# 1. Start Ollama
ollama serve &

# 2. Generate phishing email with AI
python phish-forge.py generate --intel ../target-scout/report.json

# 3. Start credential capture server
python capture-server.py

# 4. Target visits: http://localhost:8080
```

---

## ✨ Features

### 🤖 AI Email Generation
- **Ollama (default)**: Local LLaMA 3.1, no API keys, 100% offline
- Context-aware: Uses company tech stack, domains, employees
- Multiple templates: Jira, Office365, Generic IT alerts
- Realistic urgency and social engineering

### 🎣 Landing Pages
- Professional clones: Jira, Office365
- Real-time credential capture
- Auto-save to JSON
- Admin panel at `/admin`

### 📊 Credential Server
- Flask-based
- Cross-platform
- Live logging
- JSON export

---

## 📋 Requirements

- **Ollama** + **LLaMA 3.1 8B** (~4.7GB)
- Python 3.8+
- 8GB RAM minimum

---

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation & usage
- **[WORKFLOW.md](WORKFLOW.md)** - Complete attack workflow examples

---

## 🔧 LLM Options

| Provider | Cost | Setup | Privacy | Recommended |
|----------|------|-------|---------|-------------|
| **Ollama** | Free | Manual install | 100% local | ✅ Yes |
| Groq | Free | API key | Cloud | For demos |
| OpenAI | Paid | API key | Cloud | Max quality |

**Default:** Ollama (privacy-focused, no external dependencies)

---

## 🛡️ Legal Notice

**FOR AUTHORIZED RED TEAM TESTING ONLY**

This tool is designed for:
- Authorized penetration testing with written permission
- Security awareness training
- Simulated phishing exercises

**Unauthorized use is illegal.**

---

## 🎯 Tech Stack

- **LLM**: Ollama (LLaMA 3.1 8B)
- **Backend**: Python, Flask
- **Frontend**: HTML/CSS (Jira/Office365 clones)
- **Storage**: JSON

---

## 💡 Why This Tool Impresses

1. **No external dependencies** - 100% offline capable
2. **Real AI integration** - Not just templates
3. **Complete workflow** - Email → Page → Capture
4. **Professional quality** - Production-ready Red Team tool
5. **Privacy-first** - All data stays local

Perfect for security portfolios and Red Team demonstrations.
