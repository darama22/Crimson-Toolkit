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

*   LinkedIn employee enumeration
*   Email discovery (Hunter.io integration)
*   Domain/subdomain scanning
*   Social media profiling
*   Executive summary generation

### 2. Phish Forge (AI-Powered Phishing)
Create realistic phishing campaigns with AI-generated content.

*   44 pre-built templates (Instagram, Google, Microsoft, PayPal, etc.)
*   AI-generated personalized emails
*   Credential capture server
*   Web dashboard

### 3. Payload Chef (Polymorphic Malware Generator)
Generate evasive payloads with advanced anti-detection features.

*   Polymorphic code generation
*   AMSI bypass (memory patching)
*   Sandbox detection (CPU/RAM/timing checks)
*   Parent process spoofing
*   Output: Compiled Go binaries

### 4. C2 Chameleon (Command & Control)
Manage compromised agents with tactical assistance.

*   Terminal-based dashboard (TUI)
*   **Auto-channel switching** (TCP → HTTPS → DNS)
*   Multi-protocol listeners
*   **Tactical Advisor** (real-time recommendations via AI)
*   Event logging

### 5. Vuln Oracle v2.0 (Hybrid Vulnerability Scanner)
Detect vulnerabilities and malware detection in source code.

*   **Hybrid Detection Engine:** Static Analysis (regex) + Heuristic + AI Analysis
*   **Multi-language Support:** Python, JavaScript, PHP, C/C++, Go, Java
*   **Detections:** SQLi, XSS, Buffer Overflow, RCE, Ransomware, Keyloggers, Backdoors
*   Line-level reporting and risk scoring

### 6. Defense Radar (Defense Detection)
Identify security defenses on target networks.

*   Network port scanning (nmap with socket fallback)
*   Service fingerprinting
*   Defense detection: Firewalls, EDR, WAF, IDS/IPS
*   Attack vector suggestions

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
