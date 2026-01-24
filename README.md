# Crimson Toolkit

**Professional Red Team AI Suite** - Complete offensive security toolkit with integrated AI capabilities.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

**Crimson Toolkit** is a comprehensive suite of 6 integrated security tools designed for Red Team operations and penetration testing. Each tool features AI-powered capabilities through integration with local LLMs (Ollama) and provides professional command-line interfaces.

**Legal Notice:** This toolkit is for authorized security assessments only. Unauthorized use is prohibited.

---

## Tools

### 1. Target Scout (OSINT Reconnaissance)
Automated intelligence gathering and target profiling.

**Key Features:**
*   **LinkedIn Enumeration:** Scrapes and identifies employee profiles associated with the target company.
*   **Email Discovery:** Integrates with Hunter.io to find valid email addresses patterns.
*   **Domain Scanning:** Enumerates subdomains and maps the digital footprint.
*   **Social Profiling:** aggregated search across social media platforms.
*   **Smart Reporting:** Generates comprehensive JSON executive summaries.

**Terminal Preview:**
```console
$ python target-scout.py --company "TechCorp"
╔═══════════════════════════════════════════════════════════╗
║                      TARGET-SCOUT v1.0                    ║
║               Automated OSINT & Reconnaissance            ║
╚═══════════════════════════════════════════════════════════╝
[*] Target: TechCorp
[+] Scanning domain...
[+] Enumerating employees (LinkedIn)...
[+] Discovery: 12 emails found
[+] Report generated: TechCorp_profile.json
```

### 2. Phish Forge (AI-Powered Phishing)
Create realistic phishing campaigns with AI-generated content.

**Key Features:**
*   **44 Pre-built Templates:** Includes clones of Instagram, Google, Microsoft, PayPal, and more.
*   **AI Content Engine:** Uses Ollama to generate context-aware, personalized phishing emails that bypass spam filters.
*   **Credential Capture:** Built-in web server to capture and log submitted credentials (for testing purposes).
*   **Web Dashboard:** Professional interface to manage campaigns and view captured data.

**Terminal Preview:**
```console
$ python phish-forge.py generate --template instagram
[+] AI Engine: Generating personalized phishing email...
[+] Template: Instagram Login
[+] Server: Started on port 8080
[+] URL: http://localhost:8080/instagram/login.php
```

### 3. Payload Chef (Polymorphic Malware Generator)
Generate evasive payloads with advanced anti-detection features.

**Key Features:**
*   **Polymorphic Engine:** Generates unique code signatures for every payload to evade static analysis.
*   **AMSI Bypass:** Implements memory patching techniques to disable Antimalware Scan Interface.
*   **Sandbox Detection:** Checks CPU cores, RAM size, and timing to detect if running in a virtual analysis environment.
*   **Parent Process Spoofing:** Masquerades the payload under legitimate system processes (e.g., explorer.exe).
*   **Go Compilation:** Compiles payloads into standalone executables (.exe).

**Terminal Preview:**
```console
$ python payload-chef.py create --type reverse-shell
[+] Evasion Level: High
[+] Obfuscation: Applied (Polymorphic)
[+] AMSI Bypass: Injected
[+] Compiling Go binary...
[+] Success: output/payload_x64.exe generated
```

### 4. C2 Chameleon (Command & Control)
Manage compromised agents with tactical assistance.

**Key Features:**
*   **Auto-Channel Switching:** Automatically rotates communication protocols (TCP → HTTPS → DNS) if a connection fails or is blocked.
*   **AI Tactical Advisor:** Analyzes session logs in real-time and suggests commands or evasion strategies.
*   **Multi-Protocol Listeners:** Supports simultaneous listeners on different ports/protocols.
*   **TUI Dashboard:** Professional terminal user interface built with the Rich library.

**Terminal Preview:**
```console
╭───────────────────────────────────────────────────────────────────────────╮
│               C2-CHAMELEON v1.0                                           │
╰───────────────────────────────────────────────────────────────────────────╯
╭──── System Status ────╮╭─────────────────── Event Log ────────────────────╮
│  Metric        Value  ││ [13:28:11] [INFO] Starting C2-CHAMELEON listener │
│  Active        0      ││ [13:28:15] [WARN] Heartbeat missed: Agent-01     │
│  Agents               ││ [13:28:16] [AUTO] Switching channel to HTTPS...  │
│  Active        ● TCP  │╭─── 🧠 AI Tactical Advisor (Project Overmind) ────╮
│  Channel              ││ AI Advisor initialized. Monitoring tactical      │
│  Listeners     3      ││ logs for evasion opportunities...                │
│                       │╰───────────────────────────────────────────────────
╰───────────────────────╯
```

### 5. Vuln Oracle v2.0 (Hybrid Vulnerability Scanner)
Detect vulnerabilities and malware signatures in source code.

**Key Features:**
*   **Hybrid Detection:** Combines static analysis (regex), heuristic analysis (behavior), and AI analysis (LLM) for high accuracy.
*   **Multi-Language:** Supports scanning of Python, JavaScript, PHP, C/C++, Go, and Java files.
*   **Threat Detection:** Identifies SQL Injections, XSS, RCE, Buffer Overflows, and malware patterns (Ransomware, Keyloggers).
*   **Detailed Reporting:** unique feature that pinpoints specific line numbers and provides a risk score (0-100).

**Terminal Preview:**
```console
$ python vuln-oracle.py malware.py
╭──── ⚠ 4 THREATS DETECTED - Risk Score: 100 ─────────╮
│ ┏━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓ │
│ ┃ Type        ┃ Severity ┃   Line   ┃ Description ┃ │
│ ┡━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩ │
│ │ Ransomware  │ Critical │ 106, 115 │ Encryption  │ │
│ │ Pattern     │          │          │ logic       │ │
│ │ Backdoor    │ Critical │ 12       │ Socket exec │ │
│ └─────────────┴──────────┴──────────┴─────────────┘ │
╰─────────────────────────────────────────────────────╯
```

### 6. Defense Radar (Defense Detection)
Identify security defenses on target networks without triggering alerts.

**Key Features:**
*   **Stealth Scanning:** Uses socket-based scanning with fallback to nmap for maximizing stealth.
*   **Defense Fingerprinting:** specific signatures to detect Firewalls, EDR solutions (like Windows Defender), and WAFs.
*   **Service Enumeration:** Identifies running services and versions.
*   **AI Tactical Advice:** Provides actionable recommendations on attack vectors based on the detected defenses.

**Terminal Preview:**
```console
$ python defense-radar.py 192.168.1.1
[*] Scanning target: 192.168.1.1
[*] Phase 1: Port Discovery
⠸ Socket scanning 14 common ports...
[+] Found 3 open ports (socket scan)
[+] Detected Defenses:
    - Windows Defender (High Confidence)
    - Host Firewall (Medium Confidence)
[+] AI Tactical Advice:
    "Primary vector: SMB exploitations due to exposed port 445..."
```

---

## Installation

### Prerequisites

*   **Python 3.8+**
*   **System Tools:** `nmap` (recommended), `Go` (for payload generation)

### Setup

```bash
# Clone the repository
git clone https://github.com/darama22/Crimson-Toolkit.git
cd Crimson-Toolkit

# Install dependencies
pip install -r requirements.txt

# (Optional) pull Ollama model for AI features
ollama pull llama3.1:8b
```

---

## Usage

Each tool is located in its own directory with dedicated documentation.

**Example: Running the Vulnerability Scanner**
```bash
cd vuln-oracle
python vuln-oracle.py target_file.py
```

**Example: Running the C2 Server**
```bash
cd c2-chameleon
python c2-chameleon.py
```

---

## Project Structure

```
crimson-toolkit/
├── target-scout/          # OSINT tool
├── phish-forge/           # Phishing generator
├── payload-chef/          # Malware generator
├── c2-chameleon/          # C&C server
├── vuln-oracle/           # Vulnerability scanner
├── defense-radar/         # Defense scanner
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

---

## License

MIT License. See LICENSE file for details.

**Educational and authorized testing purposes only.**
