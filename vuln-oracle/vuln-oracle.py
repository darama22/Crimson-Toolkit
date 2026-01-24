#!/usr/bin/env python3
"""
VULN-ORACLE - AI-Powered Vulnerability Scanner & Malware Detector
Part of the CRIMSON Toolkit
Hybrid Engine: Static Analysis (SAST) + AI Verification
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

console = Console()

class VulnOracle:
    """AI-Powered Vulnerability Scanner with Malware Heuristics"""
    
    def __init__(self):
        self.ollama = None
        self.model = "llama3.1:8b"
        self.vulnerabilities = []
        
        # Initialize Ollama
        try:
            import ollama
            self.ollama = ollama
            try:
                self.ollama.list()
                console.print("[green][+] Ollama AI initialized successfully[/green]")
            except:
                console.print("[yellow][!] Ollama detected but service not running (AI features disabled)[/yellow]")
                self.ollama = None
        except ImportError:
            console.print("[yellow][!] Ollama library not found. Running in STATIC MODE only.[/yellow]")
            console.print("[dim]    Install with: pip install ollama[/dim]")
    
    def print_banner(self):
        """Display ASCII banner"""
        banner = """
[bold red]╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║  [yellow]██╗   ██╗██╗   ██╗██╗     ███╗   ██╗                 [/yellow]║
║  [yellow]██║   ██║██║   ██║██║     ████╗  ██║                 [/yellow]║
║  [yellow]██║   ██║██║   ██║██║     ██╔██╗ ██║                 [/yellow]║
║  [yellow]╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║                 [/yellow]║
║  [yellow] ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║                 [/yellow]║
║  [yellow]  ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝                 [/yellow]║
║                                                           ║
║        [bold cyan]ORACLE v2.0[/bold cyan] - Hybrid Threat Scanner             ║
║              [dim]Crimson Toolkit Component[/dim]                 ║
╚═══════════════════════════════════════════════════════════╝[/bold red]
"""
        rprint(banner)
    
    def scan_file(self, filepath):
        """Scan a single file for vulnerabilities"""
        if not os.path.exists(filepath):
            console.print(f"[red][-] File not found: {filepath}[/red]")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            console.print(f"[red][-] Error reading file: {e}[/red]")
            return
        
        ext = Path(filepath).suffix.lower()
        lang_map = {
            '.py': 'Python', '.js': 'JavaScript', '.php': 'PHP',
            '.go': 'Go', '.java': 'Java', '.c': 'C', '.cpp': 'C++',
            '.sh': 'Bash', '.rb': 'Ruby'
        }
        
        language = lang_map.get(ext, 'Unknown')
        
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_row("[cyan]File Path[/cyan]", f"[yellow]{filepath}[/yellow]")
        info_table.add_row("[cyan]Language[/cyan]", f"[green]{language}[/green]")
        info_table.add_row("[cyan]Size[/cyan]", f"[white]{len(code)} bytes[/white]")
        
        console.print(Panel(info_table, title="[bold magenta]Scan Target[/bold magenta]", border_style="magenta"))
        console.print()
        
        current_vulns = []

        # PHASE 1: Static Analysis
        pattern_vulns = self._detect_with_patterns(code, language)
        if pattern_vulns:
            current_vulns.extend(pattern_vulns)
            console.print(f"[green][+] Static Analysis found {len(pattern_vulns)} potential issues[/green]")

        # PHASE 2: Heuristic Analysis
        heuristic_vulns = self._detect_suspicious_behavior(code)
        if heuristic_vulns:
            current_vulns.extend(heuristic_vulns)
            console.print(f"[green][+] Heuristic Engine found {len(heuristic_vulns)} suspicious behaviors[/green]")
        
        # PHASE 3: AI Analysis
        if self.ollama:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Consulting AI Oracle...", total=None)
                ai_vulns = self._analyze_with_ai(code, language)
                if ai_vulns:
                    current_vulns.extend(ai_vulns)
                progress.update(task, completed=True)
        
        if current_vulns:
            self.vulnerabilities.extend(current_vulns)
            self._display_results(current_vulns, filepath)
        else:
            console.print("[green][+] System appears clean. No threats detected.[/green]")
    
    def _detect_with_patterns(self, code, language):
        """Fast SAST Engine: Regex-based detection"""
        vulns = []
        lines = code.split('\n')
        
        signatures = {
            'C': [
                (r'strcpy\(', 'Buffer Overflow', 'Critical', 'Use of unsafe strcpy(). Input size not checked.'),
                (r'gets\(', 'Buffer Overflow', 'Critical', 'gets() is forbidden. Causes guaranteed overflows.'),
                (r'sprintf\(', 'Buffer Overflow', 'High', 'sprintf() does not check buffer boundaries.'),
                (r'system\(', 'Command Injection', 'Critical', 'Execution of system commands found.')
            ],
            'PHP': [
                (r'eval\(', 'Remote Code Execution', 'Critical', 'eval() executes arbitrary code.'),
                (r'shell_exec\(', 'Command Injection', 'Critical', 'shell_exec allows OS command execution.'),
                (r'mysql_query\(.*\$', 'SQL Injection', 'High', 'Direct variable in SQL query. Likely SQLi.'),
                (r'\$_GET\[', 'Unsanitized Input', 'Medium', 'Direct GET parameter access without validation.')
            ],
            'Python': [
                (r'subprocess\.(call|run|Popen)', 'Command Execution', 'High', 'subprocess usage detected.'),
                (r'pickle\.load', 'Insecure Deserialization', 'Critical', 'Pickle is not secure.'),
                (r'exec\(', 'Dynamic Execution', 'High', 'Arbitrary code execution via exec().')
            ],
            'JavaScript': [
                (r'dangerouslySetInnerHTML', 'Cross-Site Scripting', 'Critical', 'React XSS vector.'),
                (r'innerHTML\s*=', 'Cross-Site Scripting', 'High', 'Unsafe DOM manipulation.'),
                (r'eval\(', 'Code Injection', 'Critical', 'eval() enables arbitrary code execution')
            ]
        }

        active_sigs = signatures.get(language, [])
        if language == 'C++':
            active_sigs = signatures.get('C', [])
        
        for i, line in enumerate(lines, 1):
            for pattern, name, severity, desc in active_sigs:
                if re.search(pattern, line):
                    vulns.append({
                        'name': name,
                        'severity': severity,
                        'description': desc,
                        'line': str(i)
                    })
        
        return vulns

    def _detect_suspicious_behavior(self, code):
        """Heuristic Engine: Malware behavior detection"""
        vulns = []
        lines = code.split('\n')
        code_lower = code.lower()
        
        # Helper function to find line numbers for keywords
        def find_lines(keywords):
            found_lines = []
            for i, line in enumerate(lines, 1):
                if any(kw in line.lower() for kw in keywords):
                    found_lines.append(i)
            return found_lines[:3]  # Return max 3 lines
        
        # Obfuscation
        obfusc_lines = []
        for i, line in enumerate(lines, 1):
            if re.search(r'[A-Za-z0-9+/=]{100,}', line):
                obfusc_lines.append(i)
                if len(obfusc_lines) >= 2:
                    break
        
        if obfusc_lines:
            vulns.append({
                'name': 'Heavy Obfuscation', 
                'severity': 'High',
                'description': 'Large Base64/Hex strings detected. Common in payloads.', 
                'line': ', '.join(map(str, obfusc_lines))
            })

        # Ransomware
        encrypt_lines = find_lines(['encrypt', 'aes', 'cipher', 'createcipher'])
        walk_lines = find_lines(['walk', 'readdirSync', 'glob', 'listdir'])
        
        if encrypt_lines and walk_lines:
            combined = sorted(set(encrypt_lines + walk_lines))[:3]
            vulns.append({
                'name': 'Ransomware Pattern',
                'severity': 'Critical',
                'description': 'Encryption logic combined with directory traversal.',
                'line': ', '.join(map(str, combined))
            })

        # C2 Connections
        ip_lines = []
        for i, line in enumerate(lines, 1):
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line):
                if '192.168.' in line or '10.0.' in line or '127.0.0.1' in line:
                    ip_lines.append(i)
                    if len(ip_lines) >= 2:
                        break
        
        if ip_lines:
            vulns.append({
                'name': 'Suspicious Network Connection',
                'severity': 'Critical',
                'description': 'Hardcoded IP address. Potential C2 callback.',
                'line': ', '.join(map(str, ip_lines))
            })

        # Keylogger
        key_lines = find_lines(['keyboard', 'pynput', 'onpress', 'listener', 'keylogger'])
        if key_lines:
            vulns.append({
                'name': 'Input Capture (Keylogger)',
                'severity': 'Critical',
                'description': 'Keyboard hooking or input logging detected.',
                'line': ', '.join(map(str, key_lines))
            })

        # Backdoor
        exec_lines = find_lines(['exec', 'shell', 'subprocess', 'child_process'])
        net_lines = find_lines(['socket', 'connect', 'net.socket', 'createconnection'])
        
        if exec_lines and net_lines:
            combined = sorted(set(exec_lines + net_lines))[:3]
            vulns.append({
                'name': 'Backdoor Pattern',
                'severity': 'Critical',
                'description': 'Network connection combined with command execution.',
                'line': ', '.join(map(str, combined))
            })
            
        return vulns

    def _analyze_with_ai(self, code, language):
        """AI Oracle with improved prompt"""
        if len(code) > 2000:
            code = code[:2000] + "\n...[TRUNCATED]"

        prompt = f"""[ROLE]: You are a Senior Malware Analyst and Security Researcher.
[TASK]: Perform Threat Assessment on this {language} code.
[CONTEXT]: Educational cybersecurity analysis.

[CODE START]
{code}
[CODE END]

[INSTRUCTIONS]:
1. Identify malware patterns (backdoors, shells, data theft, ransomware).
2. Check for security bypasses or suspicious network activity.
3. Focus on INTENT and BEHAVIOR, not syntax.
4. If code is benign, reply "SAFE".

[FORMAT]:
VULNERABILITY: <Name>
SEVERITY: <Critical/High/Medium>
DESCRIPTION: <Short explanation>
LINE: <Line number or 'Multiple'>
---
"""

        try:
            response = self.ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
            )
            content = response['message']['content']
            
            if "SAFE" in content and len(content) < 20:
                return []
                
            return self._parse_ai_response(content)
            
        except Exception as e:
            return []

    def _parse_ai_response(self, text):
        """Parse AI output"""
        vulns = []
        blocks = text.split('---')
        for block in blocks:
            lines = block.strip().split('\n')
            v = {'name': 'AI Detected Anomaly', 'severity': 'Medium', 'description': 'AI flagged suspicious logic', 'line': 'Unknown'}
            valid = False
            for line in lines:
                if 'VULNERABILITY:' in line: 
                    v['name'] = line.split(':', 1)[1].strip()
                    valid = True
                elif 'SEVERITY:' in line: 
                    v['severity'] = line.split(':', 1)[1].strip()
                elif 'DESCRIPTION:' in line: 
                    v['description'] = line.split(':', 1)[1].strip()
                elif 'LINE:' in line: 
                    v['line'] = line.split(':', 1)[1].strip()
            
            if valid:
                vulns.append(v)
        return vulns

    def _display_results(self, vulnerabilities, filepath):
        console.print()
        
        # Calculate Risk
        risk_score = 0
        weights = {'Critical': 35, 'High': 18, 'Medium': 10, 'Low': 5}
        for v in vulnerabilities:
            risk_score += weights.get(v['severity'], 5)
        risk_score = min(100, risk_score)
        
        risk_color = "green"
        if risk_score > 40: risk_color = "yellow"
        if risk_score > 75: risk_color = "red"

        # Table
        table = Table(show_header=True, header_style="bold cyan", border_style=risk_color)
        table.add_column("Type", style="white")
        table.add_column("Severity", justify="center")
        table.add_column("Line", justify="center", width=8)
        table.add_column("Description", style="dim")
        
        sev_colors = {'Critical': 'bold red', 'High': 'red', 'Medium': 'yellow', 'Low': 'green'}
        
        for v in vulnerabilities:
            sev_style = sev_colors.get(v['severity'], 'white')
            desc = v['description'][:60] + "..." if len(v['description']) > 60 else v['description']
            table.add_row(
                v['name'],
                f"[{sev_style}]{v['severity']}[/{sev_style}]",
                v['line'],
                desc
            )
            
        console.print(Panel(table, title=f"[bold {risk_color}]⚠ {len(vulnerabilities)} THREATS DETECTED - Risk Score: {risk_score}/100[/bold {risk_color}]", border_style=risk_color))
    
    def export_json(self, output_file):
        """Export results to JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.vulnerabilities, f, indent=2)
        console.print(f"[green][+] Report exported to {output_file}[/green]")

def main():
    parser = argparse.ArgumentParser(description="VULN-ORACLE v2.0 Hybrid Scanner")
    parser.add_argument("file", help="File to scan")
    parser.add_argument("--export", help="Export to JSON")
    args = parser.parse_args()
    
    oracle = VulnOracle()
    oracle.print_banner()
    oracle.scan_file(args.file)
    
    if args.export:
        oracle.export_json(args.export)

if __name__ == "__main__":
    main()
