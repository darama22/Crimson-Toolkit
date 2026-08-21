# VULN-ORACLE

**Static Application Security Testing (SAST) + Malware Heuristics — v3.0**

A defensive code scanner that flags insecure code patterns and malware-like
behaviour, each mapped to a **CWE** identifier, with an optional local-LLM
second opinion. Built to audit your own code and to gate CI/CD pipelines.

## Engines
1. **Signature SAST** — language-aware regex rules (Python, JavaScript/TS, PHP,
   Java, Go, C/C++, Bash, Ruby), CWE-tagged.
2. **Heuristic engine** — cross-language malware behaviour (obfuscation,
   ransomware pattern, keylogger, backdoor, hardcoded C2 IP).
3. **Entropy engine** — Shannon-entropy analysis flags high-randomness strings
   (API keys, tokens) that no fixed regex would catch (CWE-798).
4. **AI verification** *(optional, `--ai`)* — Ollama second opinion; off by default.

## Usage
```bash
# Scan a single file
python vuln-oracle.py app.py

# Scan a whole directory (recursive)
python vuln-oracle.py ./project

# Only show High/Critical issues
python vuln-oracle.py ./project --min-severity High

# Export machine-readable reports
python vuln-oracle.py ./project -o report.json     # JSON
python vuln-oracle.py ./project -o report.md       # Markdown
python vuln-oracle.py ./project -o report.sarif    # SARIF 2.1.0 (GitHub code scanning)

# CI gate: exit non-zero if any High+ finding exists
python vuln-oracle.py ./project --fail-on High

# Enable the optional AI second opinion
python vuln-oracle.py app.py --ai
```

## Options
| Flag | Meaning |
|------|---------|
| `-o, --export` | Write report; format inferred from extension (`.json`/`.md`/`.sarif`) |
| `--min-severity` | Hide findings below this level (`Critical`…`Info`) |
| `--fail-on` | Exit code 1 if a finding at/above this severity exists (CI gating) |
| `--ai` | Enable Ollama-based second opinion |
| `--no-banner` | Suppress the ASCII banner (cleaner CI logs) |

## Detections (examples)
| Language | Rule | CWE |
|----------|------|-----|
| Python | `subprocess(..., shell=True)`, `pickle.load`, `yaml.load`, `verify=False`, hardcoded secret | CWE-78/502/295/798 |
| PHP | `eval`, `shell_exec`, SQLi, LFI/RFI, `unserialize` | CWE-95/78/89/98/502 |
| JS/TS | `eval`, `innerHTML`, `dangerouslySetInnerHTML`, `child_process` | CWE-95/79/78 |
| C/C++ | `gets`, `strcpy`, `sprintf`, `system` | CWE-242/120/78 |
| Bash | `curl … | sh`, `eval`, `chmod 777` | CWE-494/78/732 |

Plus heuristic malware patterns (ransomware, keylogger, backdoor, C2).

## Output
- A colourised findings table with a **risk score (0–100)**.
- Exit code integrates with CI when `--fail-on` is set.
- SARIF output uploads directly to GitHub code scanning.

## Requirements
- Python 3.9+
- `rich` (optional — degrades to plain text)
- `ollama` (optional — only for `--ai`)

## Note on antivirus false positives
Test fixtures use deliberately benign snippets so real-time AV protection does
not quarantine them. If you write your own malicious-looking test samples,
your AV may flag them — that is expected behaviour, not a bug.
