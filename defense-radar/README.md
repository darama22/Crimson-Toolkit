# DEFENSE-RADAR

Network Defense Detection Scanner - Part of CRIMSON Toolkit

## Features
- 🔍 Network port scanning (nmap integration)
- 🛡️ Defense technology fingerprinting (EDR, Firewall, WAF, IDS/IPS)
- 🧠 AI-powered tactical recommendations
- 📊 Professional reporting
- 🎯 Attack vector suggestions

## Usage

### Basic scan
```bash
python defense-radar.py 192.168.1.1
```

### Scan with AI tactical advice
```bash
python defense-radar.py example.com
```

## Detected Technologies
- Firewalls (Host-based, Network)
- EDR/Antivirus (Windows Defender, etc.)
- Web Application Firewalls (WAF)
- Intrusion Detection/Prevention Systems (IDS/IPS)

## Requirements
- Python 3.8+
- nmap (system package)
- ollama (for AI features)
- rich library

## Installation
```bash
# Install Python dependencies
pip install ollama rich

# Install nmap
# Linux: sudo apt install nmap
# Windows: choco install nmap
# macOS: brew install nmap
```

## AI Tactical Advisor
When Ollama is available, DEFENSE-RADAR uses AI to:
- Analyze detected defenses
- Suggest primary/secondary attack vectors
- Recommend evasion techniques
- Provide tactical guidance

## Legal Notice
For authorized security assessments only. Unauthorized scanning is illegal.
