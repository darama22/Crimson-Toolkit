# DEFENSE-RADAR

**Security Posture Self-Assessment Scanner — Blue-Team Edition**

A defensive tool that audits the exposed attack surface of a host or network
**you own or are authorized to test**, then reports concrete **hardening**
recommendations. Unlike offensive recon tools, DEFENSE-RADAR never suggests
attack vectors or evasion techniques — it maps exposure to *risk* and
*remediation*.

## What it does
- 🔍 Concurrent TCP port discovery (pure-Python, no external tools required)
- 🛡️ Maps each open service to a curated **risk profile** (0–10 exposure severity)
- 🔐 Passive banner grab + TLS presence check (read-only; sends no exploit payloads)
- 🧱 **HTTP security-header audit** on web ports (HSTS, CSP, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy) with per-header remediation guidance
- 📊 Aggregate **risk score** and posture **grade (A–F)**
- 🧾 Exports reports to **JSON** or **Markdown** for your coursework write-up
- 🧠 Optional local-LLM (Ollama) **hardening checklist** — defensive advice only
- ✅ Explicit **authorization gate** before any scan

## Usage

```bash
# Scan your own host across the built-in service list
python defense-radar.py 127.0.0.1

# Specify ports and export a Markdown report
python defense-radar.py 192.168.1.10 -p 1-1024 -o report.md

# Non-interactive (labs/CI) — skips the authorization prompt
python defense-radar.py 10.0.0.5 -p 22,80,443 -y

# With local LLM hardening advice
python defense-radar.py myserver.lab --ai
```

### Options
| Flag | Meaning |
|------|---------|
| `-p, --ports` | Ports: `22,80,443` or ranges `1-1024` (default: curated list) |
| `-t, --timeout` | Per-port timeout in seconds (default 1.0) |
| `-w, --workers` | Concurrent probes (default 100) |
| `-o, --output` | Write report to `.json` or `.md` |
| `--ai` | Enable Ollama-based hardening checklist |
| `-y, --yes` | Skip the interactive authorization prompt |
| `-v, --verbose` | Debug logging |

## Requirements
- Python 3.9+
- `rich` (optional — the tool degrades gracefully to plain text without it)
- `ollama` (optional — only for the `--ai` hardening advisor)

```bash
pip install rich ollama
```

## Output example
```
| Port | Service | Severity | Recommendation                                  |
|-----:|---------|----------|-------------------------------------------------|
| 3306 | MySQL   | Critical | Database should not be publicly reachable...    |
| 445  | SMB     | Critical | SMB is a top ransomware vector; require signing |
| 80   | HTTP    | Medium   | Redirect all traffic to HTTPS and enable HSTS   |

Risk score: 8.4/10   Grade: F
```

## Legal & ethical use
For **authorized** self-assessment only. Scan systems you own or have written
permission to test. Unauthorized scanning is illegal in most jurisdictions.
