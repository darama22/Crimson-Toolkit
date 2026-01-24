# VULN-ORACLE

AI-Powered Vulnerability Scanner - Part of CRIMSON Toolkit

## Features
- 🧠 AI-powered code analysis using Ollama
- 🔍 Detects SQL Injection, XSS, Command Injection, etc.
- 📊 Risk scoring system (0-100)
- 📄 JSON export for CI/CD integration
- 🎨 Professional hacker-style UI

## Usage

### Scan a single file
```bash
python vuln-oracle.py scan --file vulnerable_app.py
```

### Scan entire directory
```bash
python vuln-oracle.py scan --dir ./project --export report.json
```

## Supported Languages
- Python (.py)
- JavaScript (.js)
- PHP (.php)
- Go (.go)
- Java (.java)

## Requirements
- Python 3.8+
- Ollama (local AI)
- rich library

## Installation
```bash
pip install ollama rich
```
