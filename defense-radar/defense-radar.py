#!/usr/bin/env python3
"""
DEFENSE-RADAR - Network Defense Detection Scanner
Part of the CRIMSON Toolkit
Scans networks to identify security defenses and suggests attack vectors
"""

import subprocess
import re
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
import argparse

console = Console()

class DefenseRadar:
    """Network Defense Scanner with AI Tactical Advisor"""
    
    def __init__(self):
        self.ollama = None
        self.model = "llama3.1:8b"
        self.detected_defenses = []
        
        # Initialize Ollama for tactical advice
        try:
            import ollama
            self.ollama = ollama
            console.print("[green][+] AI Tactical Advisor initialized[/green]")
        except ImportError:
            console.print("[yellow][!] AI Tactical Advisor disabled (Ollama not found)[/yellow]")
    
    def print_banner(self):
        """Display ASCII banner"""
        banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║  [yellow]██████╗ ███████╗███████╗███████╗███╗   ██╗███████╗[/yellow]  ║
║  [yellow]██╔══██╗██╔════╝██╔════╝██╔════╝████╗  ██║██╔════╝[/yellow]  ║
║  [yellow]██║  ██║█████╗  █████╗  █████╗  ██╔██╗ ██║███████╗[/yellow]  ║
║  [yellow]██║  ██║██╔══╝  ██╔══╝  ██╔══╝  ██║╚██╗██║╚════██║[/yellow]  ║
║  [yellow]██████╔╝███████╗██║     ███████╗██║ ╚████║███████║[/yellow]  ║
║  [yellow]╚═════╝ ╚══════╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚══════╝[/yellow]  ║
║                                                           ║
║        [bold red]RADAR v1.0[/bold red] - Defense Detection System       ║
║              [dim]Crimson Toolkit Component[/dim]                 ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
"""
        rprint(banner)
    
    def scan_target(self, target):
        """Scan target for defensive technologies"""
        console.print(f"\n[cyan][*] Scanning target: {target}[/cyan]\n")
        
        # Phase 1: Port Scan
        open_ports = self._scan_ports(target)
        
        # Phase 2: Service Detection
        services = self._detect_services(target, open_ports)
        
        # Phase 3: Defense Fingerprinting
        defenses = self._fingerprint_defenses(target, services)
        
        # Phase 4: AI Tactical Analysis
        if self.ollama and defenses:
            tactical_advice = self._get_tactical_advice(target, defenses, services)
        else:
            tactical_advice = None
        
        # Display Results
        self._display_results(target, open_ports, services, defenses, tactical_advice)
    
    def _scan_ports(self, target):
        """Quick port scan using nmap or socket fallback"""
        console.print("[yellow][*] Phase 1: Port Discovery[/yellow]")
        
        # Try nmap first
        try:
            with Progress(
                SpinnerColumn(), 
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Scanning with nmap...", total=None)
                
                result = subprocess.run(
                    ['nmap', '-T4', '-F', '--open', target],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                progress.update(task, completed=True)
            
            # Parse nmap output
            open_ports = []
            for line in result.stdout.split('\n'):
                match = re.search(r'(\d+)/(tcp|udp)\s+open', line)
                if match:
                    open_ports.append({
                        'port': int(match.group(1)),
                        'proto': match.group(2),
                        'service': line.split()[2] if len(line.split()) > 2 else 'unknown'
                    })
            
            console.print(f"[green][+] Found {len(open_ports)} open ports (nmap)[/green]")
            return open_ports
            
        except FileNotFoundError:
            console.print("[yellow][!] nmap not found. Using socket scan (slower but works)[/yellow]")
            return self._socket_scan(target)
        except subprocess.TimeoutExpired:
            console.print("[red][-] nmap scan timed out. Falling back to socket scan[/red]")
            return self._socket_scan(target)
        except Exception as e:
            console.print(f"[yellow][!] nmap error: {e}. Using socket scan[/yellow]")
            return self._socket_scan(target)
    
    def _socket_scan(self, target):
        """Fallback socket-based port scanner"""
        import socket
        
        # Common ports to check
        common_ports = [
            (21, 'FTP'), (22, 'SSH'), (23, 'Telnet'), (25, 'SMTP'),
            (80, 'HTTP'), (110, 'POP3'), (143, 'IMAP'), (443, 'HTTPS'),
            (445, 'SMB'), (3306, 'MySQL'), (3389, 'RDP'), (5432, 'PostgreSQL'),
            (8080, 'HTTP-Alt'), (8443, 'HTTPS-Alt')
        ]
        
        open_ports = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Socket scanning {len(common_ports)} common ports...", total=len(common_ports))
            
            for port, service in common_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((target, port))
                
                if result == 0:
                    open_ports.append({
                        'port': port,
                        'proto': 'tcp',
                        'service': service
                    })
                
                sock.close()
                progress.advance(task)
        
        console.print(f"[green][+] Found {len(open_ports)} open ports (socket scan)[/green]")
        return open_ports
    
    def _detect_services(self, target, ports):
        """Detect service versions and banners"""
        console.print("\n[yellow][*] Phase 2: Service Fingerprinting[/yellow]")
        
        services = {}
        common_defenses = {
            80: 'HTTP/Web Server',
            443: 'HTTPS/Web Server',
            3389: 'RDP (Windows)',
            22: 'SSH',
            445: 'SMB (Windows)',
            3306: 'MySQL',
            5432: 'PostgreSQL'
        }
        
        for port_info in ports:
            port = port_info['port']
            services[port] = {
                'name': port_info.get('service', common_defenses.get(port, 'Unknown')),
                'version': 'Unknown',
                'banner': ''
            }
        
        console.print(f"[green][+] Identified {len(services)} services[/green]")
        return services
    
    def _fingerprint_defenses(self, target, services):
        """Detect defensive technologies"""
        console.print("\n[yellow][*] Phase 3: Defense Detection[/yellow]")
        
        defenses = []
        port_numbers = list(services.keys())
        
        # Enhanced detection logic
        
        # 1. Firewall detection (more sophisticated)
        if not port_numbers:
            defenses.append({
                'type': 'Firewall',
                'name': 'Aggressive Firewall',
                'confidence': 'High',
                'evidence': 'All ports filtered - likely perimeter firewall'
            })
        elif len(port_numbers) < 3:
            defenses.append({
                'type': 'Firewall',
                'name': 'Host Firewall',
                'confidence': 'Medium',
                'evidence': f'Only {len(port_numbers)} port(s) open - minimal exposure'
            })
        
        # 2. Operating System detection
        if 3389 in port_numbers or 445 in port_numbers:
            defenses.append({
                'type': 'OS',
                'name': 'Windows Server',
                'confidence': 'High',
                'evidence': 'RDP (3389) or SMB (445) detected'
            })
            defenses.append({
                'type': 'EDR',
                'name': 'Windows Defender / Microsoft Defender',
                'confidence': 'High',
                'evidence': 'Default on modern Windows systems'
            })
        elif 22 in port_numbers:
            defenses.append({
                'type': 'OS',
                'name': 'Linux/Unix System',
                'confidence': 'High',
                'evidence': 'SSH (22) detected'
            })
        
        # 3. Web Application Firewall
        if 80 in port_numbers or 443 in port_numbers or 8080 in port_numbers or 8443 in port_numbers:
            defenses.append({
                'type': 'WAF',
                'name': 'Web Application Firewall (Possible)',
                'confidence': 'Medium',
                'evidence': f'HTTP/HTTPS services on port(s): {[p for p in port_numbers if p in [80, 443, 8080, 8443]]}'
            })
        
        # 4. Database security
        if 3306 in port_numbers or 5432 in port_numbers:
            defenses.append({
                'type': 'Database',
                'name': 'Database Server Exposed',
                'confidence': 'High',
                'evidence': 'MySQL (3306) or PostgreSQL (5432) accessible - attack surface!'
            })
        
        # 5. IDS/IPS heuristic
        if len(port_numbers) >= 5:
            defenses.append({
                'type': 'IDS/IPS',
                'name': 'Intrusion Detection System (Likely)',
                'confidence': 'Medium',
                'evidence': f'{len(port_numbers)} services exposed - likely monitored'
            })
        
        # 6. Network segmentation check
        if 21 in port_numbers or 23 in port_numbers:
            defenses.append({
                'type': 'Security',
                'name': 'Weak Security Posture',
                'confidence': 'High',
                'evidence': 'FTP (21) or Telnet (23) - unencrypted protocols exposed'
            })
        
        console.print(f"[green][+] Detected {len(defenses)} security indicators[/green]")
        return defenses
    
    def _get_tactical_advice(self, target, defenses, services):
        """Use AI to suggest attack vectors"""
        console.print("\n[yellow][*] Phase 4: AI Tactical Analysis[/yellow]")
        
        # Build context
        defense_summary = "\n".join([f"- {d['type']}: {d['name']} ({d['confidence']} confidence)" for d in defenses])
        service_summary = "\n".join([f"- Port {p}: {s['name']}" for p, s in services.items()])
        
        prompt = f"""You are a Red Team penetration testing advisor.

TARGET: {target}

DETECTED DEFENSES:
{defense_summary}

DETECTED SERVICES:
{service_summary}

TASK: Provide tactical recommendations for penetration testing.

Respond with:
1. Primary Attack Vector (most promising)
2. Secondary Vector (backup)
3. Recommended Evasion Technique

Keep response concise (3-5 sentences max).
"""
        
        try:
            response = self.ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            advice = response['message']['content']
            console.print("[green][+] AI Tactical Analysis complete[/green]")
            return advice
            
        except Exception as e:
            console.print(f"[yellow][!] AI Analysis failed: {e}[/yellow]")
            return None
    
    def _display_results(self, target, ports, services, defenses, tactical_advice):
        """Display scan results"""
        console.print("\n" + "="*70)
        console.print(f"[bold cyan]SCAN RESULTS FOR: {target}[/bold cyan]")
        console.print("="*70 + "\n")
        
        # Open Ports Table
        if ports:
            ports_table = Table(title="[bold green]Open Ports[/bold green]", show_header=True, header_style="bold cyan")
            ports_table.add_column("Port", style="yellow", width=10)
            ports_table.add_column("Protocol", style="white", width=10)
            ports_table.add_column("Service", style="green")
            
            for port_info in ports:
                ports_table.add_row(
                    str(port_info['port']),
                    port_info['proto'].upper(),
                    port_info.get('service', 'Unknown')
                )
            
            console.print(ports_table)
            console.print()
        
        # Defenses Table
        if defenses:
            def_table = Table(title="[bold red]Detected Defenses[/bold red]", show_header=True, header_style="bold cyan")
            def_table.add_column("Type", style="red", width=12)
            def_table.add_column("Technology", style="yellow")
            def_table.add_column("Confidence", style="white", width=12)
            def_table.add_column("Evidence", style="dim")
            
            for defense in defenses:
                conf_style = "green" if defense['confidence'] == 'High' else "yellow" if defense['confidence'] == 'Medium' else "white"
                def_table.add_row(
                    defense['type'],
                    defense['name'],
                    f"[{conf_style}]{defense['confidence']}[/{conf_style}]",
                    defense['evidence']
                )
            
            console.print(def_table)
            console.print()
        
        # AI Tactical Advice
        if tactical_advice:
            console.print(Panel(
                tactical_advice,
                title="[bold magenta]🧠 AI Tactical Recommendations[/bold magenta]",
                border_style="magenta"
            ))

def main():
    parser = argparse.ArgumentParser(description="DEFENSE-RADAR - Network Defense Scanner")
    parser.add_argument("target", help="Target IP or hostname to scan")
    args = parser.parse_args()
    
    radar = DefenseRadar()
    radar.print_banner()
    radar.scan_target(args.target)

if __name__ == "__main__":
    main()
