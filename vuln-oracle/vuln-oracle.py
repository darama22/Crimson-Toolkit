#!/usr/bin/env python3
"""
VULN-ORACLE - Static Application Security Testing (SAST) + Malware Heuristics
============================================================================
A defensive code scanner that flags insecure code patterns and malware-like
behaviour, mapped to CWE identifiers, with an optional local-LLM second opinion.

Hybrid engine:
  1. Signature SAST   - language-aware regex rules (CWE-tagged)
  2. Heuristic engine - cross-language malware behaviour patterns
  3. AI verification  - optional Ollama pass (off by default; --ai to enable)

Outputs a risk score, a findings table, and machine-readable reports
(JSON / Markdown / SARIF) suitable for CI/CD gating.

Educational / defensive use: audit your own code, teach secure coding, and
integrate into a pipeline to catch issues before they ship.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
SEVERITY_WEIGHT = {"Critical": 35, "High": 18, "Medium": 10, "Low": 5, "Info": 2}
SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}

LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "JavaScript", ".jsx": "JavaScript",
    ".php": "PHP", ".go": "Go", ".java": "Java", ".c": "C", ".h": "C",
    ".cpp": "C", ".cc": "C", ".hpp": "C", ".sh": "Bash", ".bash": "Bash",
    ".rb": "Ruby",
}


@dataclass
class Finding:
    file: str
    name: str
    severity: str
    cwe: str
    line: int
    snippet: str
    description: str
    engine: str  # sast / heuristic / ai


@dataclass
class Report:
    findings: list[dict] = field(default_factory=list)
    files_scanned: int = 0
    risk_score: int = 0

    def add(self, f: Finding) -> None:
        self.findings.append(asdict(f))


# --------------------------------------------------------------------------- #
# Signature database  (pattern, name, severity, CWE, description)
# --------------------------------------------------------------------------- #
Sig = tuple[str, str, str, str, str]

SIGNATURES: dict[str, list[Sig]] = {
    "C": [
        (r"\bgets\s*\(", "Buffer Overflow", "Critical", "CWE-242", "gets() cannot bound input; guaranteed overflow risk."),
        (r"\bstrcpy\s*\(", "Buffer Overflow", "High", "CWE-120", "strcpy() does not check destination size."),
        (r"\bstrcat\s*\(", "Buffer Overflow", "High", "CWE-120", "strcat() does not check destination size."),
        (r"\bsprintf\s*\(", "Buffer Overflow", "High", "CWE-120", "sprintf() does not bound output; use snprintf()."),
        (r"\bsystem\s*\(", "Command Injection", "Critical", "CWE-78", "system() runs a shell; validate/avoid untrusted input."),
        (r"\b(scanf)\s*\([^,]*\"%s\"", "Buffer Overflow", "High", "CWE-120", "scanf(\"%s\") is unbounded; use width specifiers."),
    ],
    "PHP": [
        (r"\beval\s*\(", "Remote Code Execution", "Critical", "CWE-95", "eval() executes arbitrary PHP."),
        (r"\b(shell_exec|exec|passthru|proc_open|popen)\s*\(", "Command Injection", "Critical", "CWE-78", "OS command execution sink."),
        (r"(mysql_query|mysqli_query)\s*\([^)]*\$", "SQL Injection", "High", "CWE-89", "Variable concatenated into SQL query."),
        (r"\$(_GET|_POST|_REQUEST)\s*\[[^\]]+\]", "Unsanitized Input", "Medium", "CWE-20", "User input used without validation."),
        (r"\b(include|require)(_once)?\s*\(\s*\$", "File Inclusion", "High", "CWE-98", "Dynamic include of user-controlled path (LFI/RFI)."),
        (r"\bunserialize\s*\(", "Insecure Deserialization", "High", "CWE-502", "unserialize() on untrusted data is dangerous."),
        (r"\bmd5\s*\(", "Weak Hash", "Low", "CWE-327", "MD5 is unsuitable for passwords/integrity."),
    ],
    "Python": [
        (r"\bsubprocess\.(call|run|Popen|check_output)\s*\([^)]*shell\s*=\s*True", "Command Injection", "Critical", "CWE-78", "subprocess with shell=True and dynamic input."),
        (r"\bos\.system\s*\(", "Command Injection", "High", "CWE-78", "os.system() runs a shell command."),
        (r"\bpickle\.(load|loads)\s*\(", "Insecure Deserialization", "Critical", "CWE-502", "pickle executes code on load; untrusted data unsafe."),
        (r"\byaml\.load\s*\((?![^)]*Loader)", "Insecure Deserialization", "High", "CWE-502", "yaml.load without SafeLoader can execute code."),
        (r"\b(exec|eval)\s*\(", "Dynamic Execution", "High", "CWE-95", "exec()/eval() run arbitrary code."),
        (r"\bhashlib\.md5\s*\(", "Weak Hash", "Low", "CWE-327", "MD5 is weak; use SHA-256+ or a KDF."),
        (r"verify\s*=\s*False", "TLS Verification Disabled", "High", "CWE-295", "Certificate verification disabled."),
        (r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded Secret", "High", "CWE-798", "Possible hardcoded credential."),
    ],
    "JavaScript": [
        (r"\beval\s*\(", "Code Injection", "Critical", "CWE-95", "eval() enables arbitrary code execution."),
        (r"\bdangerouslySetInnerHTML\b", "Cross-Site Scripting", "High", "CWE-79", "React raw HTML injection vector."),
        (r"\.innerHTML\s*=", "Cross-Site Scripting", "High", "CWE-79", "Unsafe DOM sink; use textContent/sanitize."),
        (r"\bchild_process\b|\bexec(Sync)?\s*\(", "Command Injection", "Critical", "CWE-78", "Node command execution sink."),
        (r"\bnew Function\s*\(", "Code Injection", "High", "CWE-95", "Function constructor evaluates strings as code."),
        (r"(password|secret|apiKey|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]", "Hardcoded Secret", "High", "CWE-798", "Possible hardcoded credential."),
    ],
    "Java": [
        (r"Runtime\.getRuntime\(\)\.exec\s*\(", "Command Injection", "Critical", "CWE-78", "Runtime.exec() with dynamic input."),
        (r"Statement\s+\w+\s*=|createStatement\s*\(", "SQL Injection", "Medium", "CWE-89", "Prefer PreparedStatement over Statement."),
        (r"new ObjectInputStream\s*\(", "Insecure Deserialization", "High", "CWE-502", "Java deserialization of untrusted data."),
        (r'MessageDigest\.getInstance\s*\(\s*"MD5"', "Weak Hash", "Low", "CWE-327", "MD5 is weak."),
    ],
    "Go": [
        (r"exec\.Command\s*\(", "Command Execution", "Medium", "CWE-78", "os/exec with untrusted input can inject commands."),
        (r"InsecureSkipVerify\s*:\s*true", "TLS Verification Disabled", "High", "CWE-295", "TLS certificate verification disabled."),
        (r"md5\.New\s*\(", "Weak Hash", "Low", "CWE-327", "MD5 is weak."),
    ],
    "Bash": [
        (r"\beval\s+", "Command Injection", "High", "CWE-78", "eval on dynamic strings is dangerous."),
        (r"curl\s+[^|]*\|\s*(sudo\s+)?(ba)?sh", "Remote Code Execution", "Critical", "CWE-494", "Piping remote content straight to a shell."),
        (r"chmod\s+777", "Insecure Permissions", "Medium", "CWE-732", "World-writable permissions."),
    ],
    "Ruby": [
        (r"\beval\s*\(", "Code Injection", "Critical", "CWE-95", "eval() runs arbitrary Ruby."),
        (r"`[^`]*#\{", "Command Injection", "High", "CWE-78", "Interpolated backtick shell command."),
        (r"\b(system|exec)\s*\(", "Command Execution", "Medium", "CWE-78", "Shell command execution sink."),
    ],
}


# --------------------------------------------------------------------------- #
# Entropy-based secret detection (finds keys/tokens that no fixed regex catches)
# --------------------------------------------------------------------------- #
def shannon_entropy(s: str) -> float:
    """Shannon entropy in bits per character (0 for uniform, ~higher for random)."""
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


# tokens worth checking: long-ish base64/hex-like blobs
_TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_\-]{20,}")
# obvious non-secrets to skip (urls, common words repeated, etc.)
_ENTROPY_THRESHOLD = 4.0          # bits/char; random base64 ~5.0-6.0
_ASSIGN_HINT = re.compile(r"(key|secret|token|passwd|password|api|auth|cred|bearer|sig)",
                          re.IGNORECASE)


def find_high_entropy_secrets(path: str, code: str):
    """Yield Finding-like dicts for high-entropy strings that look like secrets."""
    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(("#", "//", "*")):
            continue
        for m in _TOKEN_RE.finditer(line):
            tok = m.group(0)
            if len(tok) > 128:            # huge blobs are handled by obfuscation rule
                continue
            ent = shannon_entropy(tok)
            hinted = bool(_ASSIGN_HINT.search(line))
            # require either high entropy, or medium entropy near a secret-like name
            if ent >= 4.5 or (ent >= _ENTROPY_THRESHOLD and hinted):
                sev = "High" if hinted else "Medium"
                yield Finding(
                    path, "High-Entropy Secret", sev, "CWE-798", i,
                    (tok[:12] + "…" + tok[-4:]) if len(tok) > 20 else tok,
                    f"Possible hardcoded secret (entropy {ent:.1f} bits/char). "
                    "Move to a secrets manager / environment variable.",
                    "entropy")


class VulnOracle:
    def __init__(self, use_ai: bool = False, model: str = "llama3.1:8b"):
        self.model = model
        self.ollama = None
        if use_ai:
            try:
                import ollama
                ollama.list()
                self.ollama = ollama
                self._msg("[+] Ollama AI second-opinion enabled", "green")
            except ImportError:
                self._msg("[!] ollama not installed — static mode only", "yellow")
            except Exception:
                self._msg("[!] Ollama service not running — static mode only", "yellow")

    # -- output helpers ----------------------------------------------------- #
    @staticmethod
    def _msg(text: str, style: str = "") -> None:
        if _RICH:
            console.print(f"[{style}]{text}[/{style}]" if style else text)
        else:
            print(text)

    def print_banner(self) -> None:
        banner = r"""
 __      __  _   _  _      _   _        ___   ___    _    ___  _     ___
 \ \    / / | | | || |    | \ | |  ___ / _ \ | _ \  /_\  / __|| |   | __|
  \ \/\/ /  | |_| || |__  |  \| | |___| (_) ||   / / _ \| (__ | |__ | _|
   \_/\_/    \___/ |____| |_|\_|      \___/ |_|_\/_/ \_\\___||____||___|
        SAST + Malware Heuristics  ·  CWE-tagged  ·  v3.0
"""
        self._msg(banner, "bold cyan")

    # -- core scanning ------------------------------------------------------ #
    def scan_path(self, path: Path, min_severity: str = "Info") -> Report:
        report = Report()
        if path.is_dir():
            targets = [p for p in path.rglob("*")
                       if p.is_file() and p.suffix.lower() in LANG_MAP]
        else:
            targets = [path]

        for target in targets:
            self._scan_file(target, report)

        # filter + rank
        threshold = SEVERITY_RANK[min_severity]
        report.findings = sorted(
            (f for f in report.findings if SEVERITY_RANK[f["severity"]] <= threshold),
            key=lambda f: (SEVERITY_RANK[f["severity"]], f["file"], f["line"]))
        report.files_scanned = len(targets)
        report.risk_score = min(100, sum(SEVERITY_WEIGHT[f["severity"]]
                                         for f in report.findings))
        return report

    def _scan_file(self, path: Path, report: Report) -> None:
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            self._msg(f"[-] cannot read {path}: {exc}", "red")
            return
        language = LANG_MAP.get(path.suffix.lower(), "Unknown")

        for f in self._sast(path, code, language):
            report.add(f)
        for f in self._heuristics(path, code):
            report.add(f)
        for f in find_high_entropy_secrets(str(path), code):
            report.add(f)
        if self.ollama:
            for f in self._ai(path, code, language):
                report.add(f)

    # -- engine 1: signature SAST ------------------------------------------ #
    def _sast(self, path: Path, code: str, language: str):
        sigs = SIGNATURES.get(language, [])
        if not sigs:
            return
        lines = code.splitlines()
        # skip comment-only lines to cut false positives
        comment_prefixes = ("#", "//", "*", "/*")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(comment_prefixes):
                continue
            for pattern, name, severity, cwe, desc in sigs:
                if re.search(pattern, line):
                    yield Finding(str(path), name, severity, cwe, i,
                                  stripped[:140], desc, "sast")

    # -- engine 2: malware heuristics -------------------------------------- #
    def _heuristics(self, path: Path, code: str):
        lines = code.splitlines()

        def find_lines(keywords):
            hits = [i for i, ln in enumerate(lines, 1)
                    if any(k in ln.lower() for k in keywords)]
            return hits[:3]

        # heavy obfuscation
        obf = [i for i, ln in enumerate(lines, 1)
               if re.search(r"[A-Za-z0-9+/=]{100,}", ln)][:2]
        if obf:
            yield Finding(str(path), "Heavy Obfuscation", "High", "CWE-506",
                          obf[0], "long encoded blob", "Large Base64/hex blob; common in packed payloads.",
                          "heuristic")

        enc = find_lines(["encrypt", "aes", "cipher", "fernet", "createcipher"])
        walk = find_lines(["os.walk", "readdirsync", "glob", "listdir", "rglob"])
        if enc and walk:
            yield Finding(str(path), "Ransomware Pattern", "Critical", "CWE-506",
                          sorted(set(enc + walk))[0], "encrypt + fs traversal",
                          "Encryption combined with directory traversal.", "heuristic")

        ext_ip = [i for i, ln in enumerate(lines, 1)
                  if re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", ln)
                  and not re.search(r"\b(127\.0\.0\.1|0\.0\.0\.0|255\.)", ln)][:2]
        if ext_ip:
            yield Finding(str(path), "Hardcoded IP / Possible C2", "Medium", "CWE-506",
                          ext_ip[0], "hardcoded IP", "Hardcoded IP address; review for C2 callback.",
                          "heuristic")

        keylog = find_lines(["pynput", "keyboard", "onpress", "setwindowshookex", "keylogger"])
        if keylog:
            yield Finding(str(path), "Input Capture (Keylogger)", "Critical", "CWE-506",
                          keylog[0], "keyboard hook", "Keyboard hooking / input logging detected.",
                          "heuristic")

        ex = find_lines(["exec", "shell", "subprocess", "child_process", "runtime.exec"])
        net = find_lines(["socket", "connect", "createconnection", "net.dial"])
        if ex and net:
            yield Finding(str(path), "Backdoor Pattern", "Critical", "CWE-506",
                          sorted(set(ex + net))[0], "net + exec",
                          "Network connection combined with command execution.", "heuristic")

    # -- engine 3: optional AI second opinion ------------------------------ #
    def _ai(self, path: Path, code: str, language: str):
        snippet = code[:2000] + ("\n...[TRUNCATED]" if len(code) > 2000 else "")
        prompt = (
            f"You are a defensive security code reviewer. Analyze this {language} "
            "code for security vulnerabilities and malware-like behaviour. "
            "For each issue output exactly:\n"
            "VULNERABILITY: <name>\nSEVERITY: <Critical/High/Medium/Low>\n"
            "DESCRIPTION: <short>\nLINE: <number or Multiple>\n---\n"
            "If the code is safe, reply only SAFE.\n\n"
            f"[CODE]\n{snippet}\n[/CODE]")
        try:
            resp = self.ollama.chat(model=self.model,
                                    messages=[{"role": "user", "content": prompt}])
            content = resp["message"]["content"]
        except Exception:
            return
        if content.strip().upper().startswith("SAFE"):
            return
        for block in content.split("---"):
            v = {"name": None, "severity": "Medium", "description": "", "line": "0"}
            for ln in block.splitlines():
                for key, field_ in (("VULNERABILITY:", "name"), ("SEVERITY:", "severity"),
                                    ("DESCRIPTION:", "description"), ("LINE:", "line")):
                    if key in ln:
                        v[field_] = ln.split(":", 1)[1].strip()
            if v["name"]:
                sev = v["severity"] if v["severity"] in SEVERITY_WEIGHT else "Medium"
                try:
                    line_no = int(re.search(r"\d+", v["line"]).group())
                except (AttributeError, ValueError):
                    line_no = 0
                yield Finding(str(path), v["name"], sev, "CWE-noinfo", line_no,
                              "", v["description"], "ai")

    # -- reporting ---------------------------------------------------------- #
    def render(self, report: Report) -> None:
        if not report.findings:
            self._msg(f"\n[+] Scanned {report.files_scanned} file(s). No issues found.", "green")
            return
        color = "green" if report.risk_score <= 40 else "yellow" if report.risk_score <= 75 else "red"
        if _RICH:
            table = Table(box=box.ROUNDED, header_style="bold cyan", border_style=color)
            table.add_column("Severity")
            table.add_column("CWE")
            table.add_column("Type")
            table.add_column("File:Line", overflow="fold")
            table.add_column("Description", style="dim", overflow="fold")
            sev_c = {"Critical": "bold red", "High": "red", "Medium": "yellow",
                     "Low": "green", "Info": "cyan"}
            for f in report.findings:
                loc = f"{Path(f['file']).name}:{f['line']}"
                table.add_row(f"[{sev_c[f['severity']]}]{f['severity']}[/]",
                              f["cwe"], f["name"], loc, f["description"])
            console.print(Panel(
                table,
                title=f"[bold {color}]{len(report.findings)} findings · "
                      f"Risk {report.risk_score}/100 · {report.files_scanned} file(s)[/]",
                border_style=color))
        else:
            print(f"\n{len(report.findings)} findings · Risk {report.risk_score}/100")
            for f in report.findings:
                print(f"  [{f['severity']:8}] {f['cwe']:9} {f['name']} "
                      f"({Path(f['file']).name}:{f['line']})")
                print(f"           {f['description']}")

    # -- export ------------------------------------------------------------- #
    def export(self, report: Report, path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix == ".md":
            path.write_text(self._to_markdown(report), encoding="utf-8")
        elif suffix == ".sarif":
            path.write_text(json.dumps(self._to_sarif(report), indent=2), encoding="utf-8")
        else:
            path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        self._msg(f"[+] Report written to {path}", "green")

    @staticmethod
    def _to_markdown(report: Report) -> str:
        out = [f"# VULN-ORACLE report",
               f"- Files scanned: {report.files_scanned}",
               f"- Findings: {len(report.findings)}",
               f"- **Risk score: {report.risk_score}/100**", "",
               "| Severity | CWE | Type | File:Line | Description |",
               "|----------|-----|------|-----------|-------------|"]
        for f in report.findings:
            desc = f["description"].replace("|", "\\|")
            out.append(f"| {f['severity']} | {f['cwe']} | {f['name']} | "
                       f"`{f['file']}:{f['line']}` | {desc} |")
        return "\n".join(out) + "\n"

    @staticmethod
    def _to_sarif(report: Report) -> dict:
        level = {"Critical": "error", "High": "error", "Medium": "warning",
                 "Low": "note", "Info": "note"}
        results = [{
            "ruleId": f["cwe"],
            "level": level[f["severity"]],
            "message": {"text": f"{f['name']}: {f['description']}"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": f["file"]},
                "region": {"startLine": max(1, f["line"])}}}],
        } for f in report.findings]
        return {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "VULN-ORACLE", "version": "3.0"}},
                      "results": results}],
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="VULN-ORACLE v3.0 — SAST + malware heuristics.")
    ap.add_argument("path", help="File or directory to scan")
    ap.add_argument("-o", "--export", help="Write report (.json / .md / .sarif)")
    ap.add_argument("--min-severity", choices=list(SEVERITY_RANK), default="Info",
                    help="Hide findings below this severity")
    ap.add_argument("--ai", action="store_true", help="Enable Ollama second opinion")
    ap.add_argument("--fail-on", choices=list(SEVERITY_RANK), default=None,
                    help="Exit non-zero if a finding at/above this severity exists")
    ap.add_argument("--no-banner", action="store_true")
    args = ap.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"error: path not found: {target}", file=sys.stderr)
        return 2

    oracle = VulnOracle(use_ai=args.ai)
    if not args.no_banner:
        oracle.print_banner()

    if _RICH and args.ai:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                      console=console) as p:
            p.add_task("[cyan]Scanning...", total=None)
            report = oracle.scan_path(target, args.min_severity)
    else:
        report = oracle.scan_path(target, args.min_severity)

    oracle.render(report)
    if args.export:
        oracle.export(report, Path(args.export))

    if args.fail_on:
        gate = SEVERITY_RANK[args.fail_on]
        if any(SEVERITY_RANK[f["severity"]] <= gate for f in report.findings):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
