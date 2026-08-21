#!/usr/bin/env python3
"""
DEFENSE-RADAR - Security Posture Self-Assessment Scanner
=========================================================
An educational blue-team tool that audits the exposed attack surface of a host
or network you own/administer and reports concrete HARDENING recommendations.

This tool is intentionally DEFENSIVE:
  - It does NOT suggest attack vectors or evasion techniques.
  - It maps exposed services to RISK and REMEDIATION guidance.
  - It requires the operator to confirm authorization for the target.

Designed for coursework, lab environments, and auditing your own assets.
For authorized assessment of systems you own or have written permission to test.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import logging
import socket
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box
    _RICH = True
except ImportError:  # graceful fallback so the tool still runs bare
    _RICH = False

console = Console() if _RICH else None
log = logging.getLogger("defense-radar")


# --------------------------------------------------------------------------- #
# Knowledge base: port -> (service, risk weight, hardening guidance)
# Risk weight is 0-10 (loosely CVSS-flavoured exposure severity).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ServiceProfile:
    name: str
    risk: float
    encrypted: bool
    guidance: str


SERVICE_DB: dict[int, ServiceProfile] = {
    21:   ServiceProfile("FTP", 8.5, False,
          "FTP transmits credentials in cleartext. Replace with SFTP/FTPS or disable."),
    23:   ServiceProfile("Telnet", 9.5, False,
          "Telnet is cleartext remote shell. Disable immediately; use SSH."),
    25:   ServiceProfile("SMTP", 5.0, False,
          "Ensure STARTTLS is enforced and the server is not an open relay."),
    53:   ServiceProfile("DNS", 4.0, False,
          "Restrict recursion, enable DNSSEC, avoid exposing resolvers publicly."),
    80:   ServiceProfile("HTTP", 5.5, False,
          "Redirect all traffic to HTTPS (443) and enable HSTS."),
    110:  ServiceProfile("POP3", 6.0, False,
          "Cleartext mail retrieval. Enforce POP3S/TLS or migrate to IMAPS."),
    135:  ServiceProfile("MSRPC", 7.0, False,
          "Windows RPC should not be internet-exposed. Block at perimeter firewall."),
    139:  ServiceProfile("NetBIOS", 7.5, False,
          "Legacy SMB/NetBIOS. Disable and block at the network edge."),
    143:  ServiceProfile("IMAP", 5.5, False,
          "Enforce IMAPS/TLS; disable cleartext logins."),
    443:  ServiceProfile("HTTPS", 3.0, True,
          "Verify TLS >=1.2, strong ciphers, valid cert, and HSTS. Good baseline."),
    445:  ServiceProfile("SMB", 8.0, False,
          "SMB is a top ransomware vector. Never expose to internet; require SMB signing, disable SMBv1."),
    1433: ServiceProfile("MSSQL", 8.0, False,
          "Database should not be publicly reachable. Bind to localhost/VPN, enforce TLS + strong auth."),
    3306: ServiceProfile("MySQL", 8.0, False,
          "Database should not be publicly reachable. Bind to localhost/VPN, require TLS + strong auth."),
    3389: ServiceProfile("RDP", 8.5, True,
          "RDP is heavily brute-forced. Put behind VPN, enable NLA + MFA, restrict source IPs."),
    5432: ServiceProfile("PostgreSQL", 8.0, False,
          "Database should not be publicly reachable. Restrict pg_hba, require TLS + strong auth."),
    5900: ServiceProfile("VNC", 8.5, False,
          "VNC often lacks strong auth/encryption. Tunnel over SSH/VPN or disable."),
    6379: ServiceProfile("Redis", 9.0, False,
          "Redis often ships with no auth. Bind to localhost, set requirepass, never expose publicly."),
    8080: ServiceProfile("HTTP-Alt", 5.5, False,
          "Alternate HTTP port. Move behind TLS reverse proxy; ensure it is not an admin console."),
    8443: ServiceProfile("HTTPS-Alt", 3.5, True,
          "Alternate HTTPS/admin port. Restrict access and verify TLS config."),
    9200: ServiceProfile("Elasticsearch", 9.0, False,
          "Elasticsearch exposed = data leak risk. Bind to localhost, enable auth, firewall it."),
    27017:ServiceProfile("MongoDB", 9.0, False,
          "MongoDB exposed = data leak risk. Enable auth, bind to localhost/VPN."),
}

DEFAULT_PORTS = sorted(SERVICE_DB.keys())


# Security headers every web endpoint should send, with why they matter.
SECURITY_HEADERS: dict[str, str] = {
    "strict-transport-security":
        "HSTS missing — browsers may connect over plain HTTP (downgrade/MITM risk).",
    "content-security-policy":
        "CSP missing — no defence-in-depth against XSS/data injection.",
    "x-frame-options":
        "X-Frame-Options missing — page can be framed (clickjacking risk).",
    "x-content-type-options":
        "X-Content-Type-Options missing — MIME-sniffing not disabled.",
    "referrer-policy":
        "Referrer-Policy missing — full URLs may leak to third parties.",
}


@dataclass
class PortResult:
    port: int
    open: bool
    service: str = "unknown"
    banner: str = ""
    tls: bool = False
    risk: float = 0.0
    guidance: str = ""
    http_headers: dict = field(default_factory=dict)
    missing_headers: list = field(default_factory=list)


@dataclass
class ScanReport:
    target: str
    resolved_ip: str
    started: str
    finished: str = ""
    ports: list[PortResult] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    risk_score: float = 0.0
    grade: str = "N/A"


# --------------------------------------------------------------------------- #
# Output helpers (work with or without rich)
# --------------------------------------------------------------------------- #
def out(msg: str, style: str = "") -> None:
    if _RICH:
        console.print(f"[{style}]{msg}[/{style}]" if style else msg)
    else:
        # strip simple markup for plain terminals
        print(msg)


class PostureRadar:
    """Defensive posture scanner + hardening advisor."""

    def __init__(self, timeout: float = 1.0, workers: int = 100,
                 use_ai: bool = False, model: str = "llama3.1:8b"):
        self.timeout = timeout
        self.workers = workers
        self.model = model
        self.ollama = None
        if use_ai:
            try:
                import ollama
                self.ollama = ollama
                out("[+] Hardening advisor (local LLM) initialized", "green")
            except ImportError:
                out("[!] Hardening advisor disabled (Ollama not installed)", "yellow")

    # -- banner ------------------------------------------------------------- #
    def print_banner(self) -> None:
        banner = r"""
  ____  _____ _____ _____ _   _ ____  _____   ____      _    ____    _    ____
 |  _ \| ____|  ___| ____| \ | / ___|| ____| |  _ \    / \  |  _ \  / \  |  _ \
 | | | |  _| | |_  |  _| |  \| \___ \|  _|   | |_) |  / _ \ | | | |/ _ \ | |_) |
 | |_| | |___|  _| | |___| |\  |___) | |___  |  _ <  / ___ \| |_| / ___ \|  _ <
 |____/|_____|_|   |_____|_| \_|____/|_____| |_| \_\/_/   \_\____/_/   \_\_| \_\
        Security Posture Self-Assessment  ·  Blue-Team Edition  v2.0
"""
        out(banner, "bold cyan")
        out("  Audits YOUR exposed attack surface and recommends hardening.\n", "dim")

    # -- authorization gate ------------------------------------------------- #
    @staticmethod
    def confirm_authorization(target: str, assume_yes: bool) -> bool:
        if assume_yes:
            log.info("Authorization auto-confirmed via --yes for %s", target)
            return True
        out(f"\n[AUTHORIZATION] You are about to scan: {target}", "bold yellow")
        out("Only scan systems you own or are explicitly authorized to test.", "yellow")
        try:
            answer = input("Type 'I confirm' to proceed: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in ("i confirm", "iconfirm")

    # -- resolution --------------------------------------------------------- #
    @staticmethod
    def resolve(target: str) -> Optional[str]:
        try:
            ipaddress.ip_address(target)
            return target
        except ValueError:
            pass
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            return None

    # -- port scan (concurrent) -------------------------------------------- #
    def _probe(self, ip: str, port: int) -> PortResult:
        res = PortResult(port=port, open=False)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                if sock.connect_ex((ip, port)) != 0:
                    return res
                res.open = True
                profile = SERVICE_DB.get(port)
                if profile:
                    res.service = profile.name
                    res.risk = profile.risk
                    res.guidance = profile.guidance
                    res.tls = profile.encrypted
                res.banner = self._grab_banner(ip, port, sock)
        except OSError:
            pass
        # opportunistic TLS check for common secure ports
        if res.open and port in (443, 8443):
            res.tls = self._tls_check(ip, port)
        # security-header audit for web endpoints
        if res.open and port in (80, 443, 8080, 8443):
            res.http_headers = self._fetch_http_headers(ip, port, use_tls=res.tls)
            if res.http_headers:
                res.missing_headers = self.audit_http_headers(res.http_headers)
        return res

    def _grab_banner(self, ip: str, port: int, sock: socket.socket) -> str:
        """Passive banner grab. Never sends exploit payloads — read-only."""
        try:
            sock.settimeout(self.timeout)
            # nudge line-based services only
            if port in (80, 8080):
                sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
            data = sock.recv(256)
            return data.decode(errors="replace").strip().split("\r\n")[0][:120]
        except OSError:
            return ""

    @staticmethod
    def audit_http_headers(headers: dict) -> list[str]:
        """Pure check: return guidance for each missing security header."""
        present = {k.lower() for k in headers}
        return [msg for h, msg in SECURITY_HEADERS.items() if h not in present]

    def _fetch_http_headers(self, ip: str, port: int, use_tls: bool) -> dict:
        """Fetch response headers via a minimal HEAD request. Read-only."""
        headers: dict[str, str] = {}
        try:
            raw = socket.create_connection((ip, port), timeout=self.timeout)
            sock = raw
            if use_tls:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                sock = ctx.wrap_socket(raw, server_hostname=ip)
            with sock:
                sock.sendall(b"HEAD / HTTP/1.0\r\nHost: %b\r\n\r\n" % ip.encode())
                data = b""
                while b"\r\n\r\n" not in data and len(data) < 8192:
                    chunk = sock.recv(2048)
                    if not chunk:
                        break
                    data += chunk
            for line in data.decode(errors="replace").split("\r\n")[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip()] = v.strip()
        except OSError:
            pass
        return headers

    def _tls_check(self, ip: str, port: int) -> bool:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((ip, port), timeout=self.timeout) as raw:
                with ctx.wrap_socket(raw, server_hostname=ip) as tls:
                    return bool(tls.version())
        except OSError:
            return False

    def scan(self, target: str, ports: list[int]) -> ScanReport:
        ip = self.resolve(target)
        report = ScanReport(
            target=target,
            resolved_ip=ip or "unresolved",
            started=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        if ip is None:
            out(f"[-] Could not resolve target: {target}", "red")
            report.finished = report.started
            return report

        out(f"\n[*] Scanning {target} ({ip}) — {len(ports)} ports", "cyan")
        results: list[PortResult] = []

        def run() -> None:
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                futures = {pool.submit(self._probe, ip, p): p for p in ports}
                for fut in as_completed(futures):
                    pr = fut.result()
                    if pr.open:
                        results.append(pr)

        if _RICH:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                          BarColumn(), console=console) as progress:
                task = progress.add_task("[cyan]Probing ports...", total=None)
                run()
                progress.update(task, completed=True)
        else:
            run()

        results.sort(key=lambda r: r.port)
        report.ports = results
        report.finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._assess(report)
        return report

    # -- risk assessment ---------------------------------------------------- #
    def _assess(self, report: ScanReport) -> None:
        findings: list[dict] = []
        for pr in report.ports:
            profile = SERVICE_DB.get(pr.port)
            severity = "Low"
            if pr.risk >= 8:
                severity = "Critical"
            elif pr.risk >= 6:
                severity = "High"
            elif pr.risk >= 4:
                severity = "Medium"

            note = pr.guidance or "Review whether this exposure is necessary."
            if profile and not profile.encrypted and pr.tls:
                note += " (TLS detected — good.)"
            if profile and profile.encrypted and not pr.tls and pr.port in (443, 8443):
                note += " WARNING: expected TLS but handshake failed — verify certificate/config."

            if pr.missing_headers:
                note += (f" Missing {len(pr.missing_headers)} security "
                         f"header(s): {', '.join(h.split(' ')[0] for h in pr.missing_headers)}")

            findings.append({
                "port": pr.port,
                "service": pr.service,
                "severity": severity,
                "risk": pr.risk,
                "banner": pr.banner,
                "recommendation": note,
                "missing_headers": pr.missing_headers,
            })

        # aggregate risk: emphasise the worst exposures rather than a flat mean
        if findings:
            risks = sorted((f["risk"] for f in findings), reverse=True)
            weighted = sum(r / (i + 1) for i, r in enumerate(risks))
            max_possible = sum(10 / (i + 1) for i in range(len(risks)))
            score = round(10 * weighted / max_possible, 1) if max_possible else 0.0
        else:
            score = 0.0

        report.findings = findings
        report.risk_score = score
        report.grade = self._grade(score, len(findings))

    @staticmethod
    def _grade(score: float, n_findings: int) -> str:
        if n_findings == 0:
            return "A (no listening services detected)"
        if score < 3:
            return "A"
        if score < 5:
            return "B"
        if score < 7:
            return "C"
        if score < 8.5:
            return "D"
        return "F"

    # -- optional AI hardening advice (defensive only) ---------------------- #
    def hardening_advice(self, report: ScanReport) -> Optional[str]:
        if not self.ollama or not report.findings:
            return None
        summary = "\n".join(
            f"- Port {f['port']} ({f['service']}), severity {f['severity']}"
            for f in report.findings
        )
        prompt = (
            "You are a defensive security (blue team) hardening advisor. "
            "Given the following EXPOSED services on a host the operator owns, "
            "provide prioritized HARDENING and remediation steps to reduce risk. "
            "Do NOT describe how to attack or exploit anything.\n\n"
            f"Exposed services:\n{summary}\n\n"
            "Answer with a short prioritized checklist."
        )
        try:
            resp = self.ollama.chat(model=self.model,
                                    messages=[{"role": "user", "content": prompt}])
            return resp["message"]["content"]
        except Exception as exc:  # noqa: BLE001 - advisory feature, never fatal
            out(f"[!] Advisor unavailable: {exc}", "yellow")
            return None

    # -- reporting ---------------------------------------------------------- #
    def render(self, report: ScanReport, advice: Optional[str]) -> None:
        if not report.ports:
            out("\n[+] No listening services found on the scanned ports. "
                "Minimal exposure — good posture.", "green")
            return

        if _RICH:
            table = Table(title=f"Exposure Report — {report.target} ({report.resolved_ip})",
                          box=box.ROUNDED, header_style="bold cyan")
            table.add_column("Port", justify="right")
            table.add_column("Service")
            table.add_column("Severity")
            table.add_column("Recommendation", style="dim")
            sev_color = {"Critical": "bold red", "High": "red",
                         "Medium": "yellow", "Low": "green"}
            for f in report.findings:
                table.add_row(str(f["port"]), f["service"],
                              f"[{sev_color[f['severity']]}]{f['severity']}[/]",
                              f["recommendation"])
            console.print(table)
            console.print(Panel(
                f"Exposure risk score: [bold]{report.risk_score}/10[/bold]   "
                f"Posture grade: [bold]{report.grade}[/bold]\n"
                f"Open services: {len(report.findings)}",
                title="Summary", border_style="cyan"))
        else:
            print(f"\n=== Exposure Report: {report.target} ({report.resolved_ip}) ===")
            for f in report.findings:
                print(f"  [{f['severity']:8}] {f['port']:>5}/{f['service']:<12} "
                      f"-> {f['recommendation']}")
            print(f"\n  Risk score: {report.risk_score}/10   Grade: {report.grade}")

        if advice:
            if _RICH:
                console.print(Panel(advice, title="Hardening Checklist (AI)",
                                    border_style="green"))
            else:
                print("\n--- Hardening Checklist (AI) ---\n" + advice)

    # -- export ------------------------------------------------------------- #
    @staticmethod
    def export(report: ScanReport, path: Path) -> None:
        data = asdict(report)
        if path.suffix.lower() == ".md":
            lines = [
                f"# Security Posture Report — {report.target}",
                f"- Resolved IP: `{report.resolved_ip}`",
                f"- Scanned (UTC): {report.started} → {report.finished}",
                f"- **Risk score:** {report.risk_score}/10 — **Grade {report.grade}**",
                "",
                "| Port | Service | Severity | Recommendation |",
                "|-----:|---------|----------|----------------|",
            ]
            for f in report.findings:
                rec = f["recommendation"].replace("|", "\\|")
                lines.append(f"| {f['port']} | {f['service']} | {f['severity']} | {rec} |")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        out(f"[+] Report written to {path}", "green")


# --------------------------------------------------------------------------- #
def parse_ports(spec: Optional[str]) -> list[int]:
    if not spec:
        return DEFAULT_PORTS
    ports: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            lo, hi = chunk.split("-", 1)
            ports.update(range(int(lo), int(hi) + 1))
        elif chunk:
            ports.add(int(chunk))
    return sorted(p for p in ports if 0 < p < 65536)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DEFENSE-RADAR — defensive security posture self-assessment.")
    parser.add_argument("target", help="IP or hostname you own / are authorized to test")
    parser.add_argument("-p", "--ports", help="Ports, e.g. '22,80,443' or '1-1024'")
    parser.add_argument("-t", "--timeout", type=float, default=1.0, help="Per-port timeout (s)")
    parser.add_argument("-w", "--workers", type=int, default=100, help="Concurrent probes")
    parser.add_argument("-o", "--output", help="Write report to file (.json or .md)")
    parser.add_argument("--ai", action="store_true", help="Enable local LLM hardening advice")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip authorization prompt")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s")

    radar = PostureRadar(timeout=args.timeout, workers=args.workers, use_ai=args.ai)
    radar.print_banner()

    if not radar.confirm_authorization(args.target, args.yes):
        out("[-] Authorization not confirmed. Aborting.", "red")
        return 2

    report = radar.scan(args.target, parse_ports(args.ports))
    advice = radar.hardening_advice(report)
    radar.render(report, advice)

    if args.output:
        radar.export(report, Path(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
