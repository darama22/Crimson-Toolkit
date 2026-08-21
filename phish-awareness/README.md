# PHISH-AWARENESS

**Anti-phishing training & detection toolkit — Blue-Team / Educational**

The ethical counterpart to a phishing kit. Instead of *building* credential
harvesters, this module teaches people and defenders to **recognize** them.

Two tools:

## 1. `phish_analyzer.py` — Phishing indicator scanner
Static analyzer that inspects HTML/PHP/JS and flags the technical artifacts of
credential-harvesting pages, each with an educational explanation.

```bash
# Analyze a single kit
python phish_analyzer.py ../phish-forge/.sites/facebook

# Analyze a whole directory and export a Markdown report
python phish_analyzer.py ../phish-forge/.sites -o findings.md

# Only show serious findings
python phish_analyzer.py ./suspect_page --min-severity High
```

Detects, among others:
- Credentials written to flat files (`file_put_contents(... .txt)`)
- Raw `$_POST['pass']` / `$_POST['email']` capture
- Post-capture redirect to the genuine brand site
- Exfiltration via email or Telegram bot
- Obfuscated server/client code (`eval(base64_decode(...))`, packed JS)
- Forms posting to third-party hosts
- Look-alike titles / urgency wording

Output includes a **phishing-likelihood score (0–100)** and a verdict, plus a
per-finding *"how to spot it"* lesson. Exit code is non-zero when the page is
suspicious — handy for lab pipelines/CI.

## 2. `lookalike_check.py` — Typosquatting & homoglyph domain detector
Given a URL/domain, decides whether it is a look-alike of a known brand using
homoglyph normalisation (`paypa1.com`, Cyrillic `аpple.com`), Levenshtein
edit-distance, and structural red flags (punycode, brand-in-subdomain, urgency
keywords). Pure offline analysis — it never contacts the domain.

```bash
python lookalike_check.py http://paypa1.com/login          # -> LIKELY PHISHING
python lookalike_check.py login.microsoft.account-verify.ru
python lookalike_check.py https://google.com --json        # -> LEGITIMATE
```
Exit code is non-zero for suspicious/phishing domains (usable in mail/URL filters).

## 3. `safe_trainer.py` — Safe awareness simulator
Generates a self-contained HTML page that *looks* like a login prompt but
**captures nothing**. When the learner submits, it reveals the phishing red
flags and scores their awareness.

```bash
python safe_trainer.py --brand "Acme Corp" -o training.html
# then open training.html in a browser
```

**Safety guarantees:**
- No credentials are stored, transmitted, or logged — ever.
- No network calls, no backend, no `localStorage`. Input is discarded on submit.
- Purely educational: the page exists to *train*, not to deceive.

## Why this belongs in a security course
Recognizing an attack is a core blue-team skill. Analyzing a real phishing kit's
artifacts (module 1) and experiencing the deception safely (module 2) teaches
the *defensive* half of the phishing topic — exactly what an assessment should
reward.

## Requirements
- Python 3.9+
- `rich` (optional; degrades to plain text without it)

## Ethical use
This module never captures real credentials and must not be used to. Use it to
educate, to analyze kits in a lab you control, and to build detection skills.
