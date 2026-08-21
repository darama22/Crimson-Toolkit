#!/usr/bin/env python3
"""
PHISH-ANALYZER - Phishing Page Indicator Scanner (Blue-Team / Educational)
==========================================================================
Static analyzer that inspects HTML/PHP/JS files and reports the technical
INDICATORS that reveal a credential-harvesting phishing page.

Purpose: teach students and defenders to *recognize* phishing kits by the
artifacts they leave behind — NOT to build or improve them.

Typical use in a lab:
    python phish_analyzer.py ../phish-forge/.sites/facebook
    python phish_analyzer.py ../phish-forge/.sites -o findings.md

Each finding includes: what was found, why it is a red flag, and how a
defender/user would spot it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None


# --------------------------------------------------------------------------- #
# Indicator rules. Each rule is a regex + severity + educational explanation.
# 'lesson' is what we teach the learner to look for.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Rule:
    id: str
    pattern: str
    severity: str          # Critical / High / Medium / Info
    title: str
    why: str               # why it indicates phishing
    lesson: str            # how a user/defender spots it
    flags: int = re.IGNORECASE


RULES: list[Rule] = [
    Rule("CRED-STORE-FILE", r"file_put_contents\s*\(\s*['\"][^'\"]*\.(txt|log|dat)",
         "Critical", "Credentials written to a flat file",
         "Legitimate logins never dump raw passwords to a local text file; this is harvesting.",
         "On the server side, a .txt/.log receiving POST fields is a hallmark of a phishing kit."),
    Rule("CRED-POST-FIELDS", r"\$_(POST|GET|REQUEST)\s*\[\s*['\"](pass|password|passwd|pwd|email|username|user|login)['\"]\s*\]",
         "High", "Raw credential fields read from the request",
         "The page grabs username/password directly from the form to store or forward them.",
         "Real sites hash/verify server-side; kits just read $_POST['pass'] and save it."),
    Rule("REDIRECT-REAL-SITE", r"header\s*\(\s*['\"]\s*Location:\s*https?://(www\.)?(facebook|google|instagram|paypal|microsoft|netflix|linkedin|discord|apple|amazon)\.",
         "High", "Redirect to the real brand after capture",
         "After stealing credentials the kit bounces the victim to the genuine site to avoid suspicion.",
         "A login that 'fails' then lands you on the real homepage is a classic phishing tell."),
    Rule("MAIL-EXFIL", r"\bmail\s*\(|smtplib|sendmail|PHPMailer",
         "High", "Credentials emailed to the operator",
         "Captured data is exfiltrated by email to the attacker.",
         "Outbound mail from a 'login' page is never normal."),
    Rule("TELEGRAM-EXFIL", r"api\.telegram\.org|bot[0-9]+:[A-Za-z0-9_-]{20,}",
         "Critical", "Exfiltration to a Telegram bot",
         "Modern kits send stolen creds to a Telegram bot for instant delivery.",
         "A Telegram Bot API URL embedded in a login page is a definitive phishing indicator."),
    Rule("IP-LOGGER", r"\$_SERVER\s*\[\s*['\"](REMOTE_ADDR|HTTP_X_FORWARDED_FOR|HTTP_USER_AGENT)['\"]\s*\]",
         "Medium", "Visitor IP / user-agent logging",
         "Kits log victim IP and device to profile who took the bait.",
         "Silent visitor logging on a login page suggests tracking of phished users."),
    Rule("EVAL-OBFUSC", r"\beval\s*\(|base64_decode\s*\(|gzinflate\s*\(|str_rot13\s*\(",
         "High", "Obfuscated / packed server code",
         "Obfuscation hides the harvesting logic from casual inspection.",
         "Legit login pages are not eval(base64_decode(...))-packed."),
    Rule("JS-EVAL-PACK", r"eval\(function\(p,a,c,k,e|atob\s*\(|unescape\s*\(",
         "Medium", "Obfuscated client-side JavaScript",
         "Packed JS conceals what the page does with your input.",
         "Heavily packed JS on a simple login form is suspicious."),
    Rule("EXTERNAL-FORM-ACTION", r"<form[^>]+action\s*=\s*['\"]https?://(?!(www\.)?(facebook|google|instagram|paypal|microsoft|apple|amazon)\.com)[^'\"]+",
         "High", "Form posts to a third-party host",
         "Credentials are sent to a domain unrelated to the impersonated brand.",
         "Check the form's action/URL: real logins post to the brand's own domain."),
    Rule("PASSWORD-INPUT-PLAINPOST", r"<input[^>]+type\s*=\s*['\"]password['\"]",
         "Info", "Password input present",
         "Not malicious alone, but combined with the above it confirms a login-capture page.",
         "Context matters: a password box plus any harvesting indicator = phishing."),
    Rule("LOOKALIKE-TITLE", r"<title>[^<]*(faceb00k|g00gle|paypa1|micros0ft|secure[- ]?login|verify[- ]?account|account[- ]?suspended)",
         "Medium", "Look-alike or scare-wording in the page title",
         "Typo-squatted brand names and urgency wording are social-engineering tells.",
         "Read the title/URL carefully: 'faceb00k', 'verify-account', 'suspended' are bait."),
    Rule("NO-CSRF", r"<form(?![^>]*csrf)[^>]*>",
         "Info", "Login form without CSRF token",
         "Real modern login forms include anti-CSRF tokens; kits usually omit them.",
         "Missing hidden security tokens can hint at a cloned page."),
]

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Info": 3}
SCAN_EXTS = {".php", ".html", ".htm", ".js", ".phtml"}


@dataclass
class Finding:
    file: str
    rule_id: str
    severity: str
    title: str
    line: int
    snippet: str
    why: str
    lesson: str


@dataclass
class Report:
    root: str
    files_scanned: int = 0
    findings: list[dict] = field(default_factory=list)
    verdict: str = ""
    score: int = 0


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    for rule in RULES:
        for m in re.finditer(rule.pattern, text, rule.flags):
            line_no = text.count("\n", 0, m.start()) + 1
            raw = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else m.group(0)
            findings.append(Finding(
                file=str(path), rule_id=rule.id, severity=rule.severity,
                title=rule.title, line=line_no,
                snippet=(raw[:140] + "…") if len(raw) > 140 else raw,
                why=rule.why, lesson=rule.lesson))
    return findings


def scan_path(root: Path) -> Report:
    report = Report(root=str(root))
    targets = [root] if root.is_file() else [
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SCAN_EXTS]

    all_findings: list[Finding] = []
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        report.files_scanned += 1
        all_findings.extend(scan_text(path, text))

    all_findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line))
    report.findings = [asdict(f) for f in all_findings]

    # weighted phishing-likelihood score (0-100)
    weights = {"Critical": 40, "High": 20, "Medium": 8, "Info": 2}
    seen_rules = {f.rule_id for f in all_findings}
    raw = sum(weights[r.severity] for r in RULES if r.id in seen_rules)
    report.score = min(100, raw)
    if report.score >= 60:
        report.verdict = "PHISHING — high confidence credential-harvesting page"
    elif report.score >= 30:
        report.verdict = "SUSPICIOUS — multiple phishing indicators present"
    elif report.score > 0:
        report.verdict = "LOW — a few weak indicators; review manually"
    else:
        report.verdict = "CLEAN — no known phishing indicators found"
    return report


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def render(report: Report) -> None:
    if _RICH:
        console.print(f"\n[bold cyan]PHISH-ANALYZER[/bold cyan]  root=[white]{report.root}[/white]  "
                      f"files=[white]{report.files_scanned}[/white]")
        if not report.findings:
            console.print("[green]No phishing indicators found.[/green]")
        else:
            table = Table(box=box.ROUNDED, header_style="bold cyan")
            table.add_column("Severity")
            table.add_column("File", overflow="fold")
            table.add_column("Ln", justify="right")
            table.add_column("Indicator")
            table.add_column("How to spot it", style="dim", overflow="fold")
            color = {"Critical": "bold red", "High": "red",
                     "Medium": "yellow", "Info": "green"}
            for f in report.findings:
                rel = f["file"].replace(report.root, "").lstrip("\\/") or f["file"]
                table.add_row(f"[{color[f['severity']]}]{f['severity']}[/]",
                              rel, str(f["line"]), f["title"], f["lesson"])
            console.print(table)
        console.print(f"\n[bold]Phishing likelihood:[/bold] {report.score}/100  "
                      f"→ [bold yellow]{report.verdict}[/bold yellow]\n")
    else:
        print(f"\nPHISH-ANALYZER  root={report.root}  files={report.files_scanned}")
        for f in report.findings:
            print(f"  [{f['severity']:8}] {f['file']}:{f['line']}  {f['title']}")
            print(f"             spot it: {f['lesson']}")
        print(f"\nPhishing likelihood: {report.score}/100 -> {report.verdict}\n")


def export(report: Report, path: Path) -> None:
    if path.suffix.lower() == ".md":
        lines = [f"# Phishing Analysis — `{report.root}`",
                 f"- Files scanned: {report.files_scanned}",
                 f"- **Likelihood: {report.score}/100 — {report.verdict}**", "",
                 "| Severity | File | Line | Indicator | Why it's a red flag |",
                 "|----------|------|-----:|-----------|---------------------|"]
        for f in report.findings:
            why = f["why"].replace("|", "\\|")
            lines.append(f"| {f['severity']} | `{f['file']}` | {f['line']} | "
                         f"{f['title']} | {why} |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    msg = f"[+] Report written to {path}"
    console.print(f"[green]{msg}[/green]") if _RICH else print(msg)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Scan HTML/PHP/JS for phishing (credential-harvesting) indicators.")
    ap.add_argument("path", help="File or directory to analyze")
    ap.add_argument("-o", "--output", help="Write report to .json or .md")
    ap.add_argument("--min-severity", choices=["Critical", "High", "Medium", "Info"],
                    default="Info", help="Hide findings below this severity")
    args = ap.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    report = scan_path(root)
    threshold = SEVERITY_ORDER[args.min_severity]
    report.findings = [f for f in report.findings
                       if SEVERITY_ORDER[f["severity"]] <= threshold]
    render(report)
    if args.output:
        export(report, Path(args.output))
    # exit code communicates verdict for CI/lab pipelines
    return 1 if report.score >= 30 else 0


if __name__ == "__main__":
    sys.exit(main())
