#!/usr/bin/env python3
"""
TARGET-SCOUT - OSINT & Intelligence Gathering Tool
Part of the CRIMSON Toolkit
"""

import argparse
import json
import sys
import os
from datetime import datetime
from colorama import init, Fore, Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

# Initialize
init(autoreset=True)
console = Console()

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import real scanner modules
try:
    from modules import GitHubScanner, DomainScanner, LinkedInScanner
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] Warning: Scanner modules not found. Using fallback mode.{Style.RESET_ALL}")

# Initialize colorama for cross-platform colored output
# init(autoreset=True) # Moved up

class TargetScout:
    """Main class for TARGET-SCOUT operations"""
    
    def __init__(self, company_name, domain=None, github_token=None, verbose=False):
        self.company_name = company_name
        self.domain = domain
        self.github_token = github_token
        self.verbose = verbose
        self.results = {
            "company": company_name,
            "scan_date": datetime.now().isoformat(),
            "linkedin": {},
            "github": {},
            "domains": {},
            "summary": {}
        }
    
    def print_banner(self):
        """Display ASCII art banner"""
        banner = f"""
{Fore.RED}╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   {Fore.YELLOW}████████╗ █████╗ ██████╗  ██████╗ ███████╗████████╗ {Fore.RED}║
║   {Fore.YELLOW}╚══██╔══╝██╔══██╗██╔══██╗██╔════╝ ██╔════╝╚══██╔══╝ {Fore.RED}║
║   {Fore.YELLOW}   ██║   ███████║██████╔╝██║  ███╗█████╗     ██║    {Fore.RED}║
║   {Fore.YELLOW}   ██║   ██╔══██║██╔══██╗██║   ██║██╔══╝     ██║    {Fore.RED}║
║   {Fore.YELLOW}   ██║   ██║  ██║██║  ██║╚██████╔╝███████╗   ██║    {Fore.RED}║
║   {Fore.YELLOW}   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝    {Fore.RED}║
║                                                       ║
║              {Fore.CYAN}OSINT & Intelligence Gathering{Fore.RED}          ║
║              {Fore.WHITE}Part of CRIMSON Toolkit v2.0{Fore.RED}            ║
╚═══════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
    
    def log(self, message, level="info"):
        """Formatted logging"""
        prefix = {
            "info": f"{Fore.BLUE}[*]{Style.RESET_ALL}",
            "success": f"{Fore.GREEN}[+]{Style.RESET_ALL}",
            "warning": f"{Fore.YELLOW}[!]{Style.RESET_ALL}",
            "error": f"{Fore.RED}[-]{Style.RESET_ALL}"
        }
        print(f"{prefix.get(level, '[*]')} {message}")
    
    def scan_linkedin(self):
        """Scrape LinkedIn for company information"""
        self.log(f"Scanning LinkedIn for: {self.company_name}")
        
        if not MODULES_AVAILABLE:
            self.results["linkedin"] = {"error": "Modules not loaded"}
            return
        
        try:
            scanner = LinkedInScanner(self.company_name)
            self.results["linkedin"] = scanner.scan()
            self.log("LinkedIn scan complete", "success")
        except Exception as e:
            self.log(f"LinkedIn scan error: {str(e)}", "error")
            self.results["linkedin"] = {"error": str(e)}
    
    def scan_github(self):
        """Analyze GitHub repositories"""
        self.log(f"Searching GitHub repositories for: {self.company_name}")
        
        if not MODULES_AVAILABLE:
            self.results["github"] = {"error": "Modules not loaded"}
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Scanning GitHub for {self.company_name}...", total=None)
                
                scanner = GitHubScanner(self.company_name, self.github_token)
                data = scanner.scan()
                self.results["github"] = data
                progress.update(task, completed=100)
            
            # Display summary table
            if isinstance(data.get("repositories"), list) and data["repositories"]:
                repo_count = len(data['repositories'])
                self.log(f"Found {repo_count} public repositories", "success")
                
                table = Table(title=f"[bold cyan]Top GitHub Repositories for {self.company_name}[/bold cyan]")
                table.add_column("Name", style="green")
                table.add_column("Language", style="magenta")
                table.add_column("Stars", style="yellow")
                table.add_column("Description", style="white")
                
                for repo in data["repositories"][:5]:  # Show top 5
                    desc = repo.get('description', 'No description')
                    if desc and len(desc) > 50:
                        desc = desc[:47] + "..."
                    table.add_row(
                        repo['name'], 
                        repo.get('language', 'Unknown'), 
                        str(repo.get('stars', 0)),
                        desc or "N/A"
                    )
                
                console.print(table)
                if repo_count > 5:
                    console.print(f"[dim]...and {repo_count - 5} more repositories[/dim]\n")
            else:
                self.log("No public repositories found", "warning")
            
        except Exception as e:
            self.log(f"GitHub scan error: {str(e)}", "error")
            self.results["github"] = {"error": str(e)}
    
    def scan_domains(self):
        """Enumerate subdomains and services"""
        self.log(f"Enumerating domains for: {self.company_name}")
        
        if not MODULES_AVAILABLE:
            self.results["domains"] = {"error": "Modules not loaded"}
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Scanning domains for {self.company_name}...", total=None)
                
                scanner = DomainScanner(self.company_name)
                data = scanner.scan()
                self.results["domains"] = data
                progress.update(task, completed=100)
            
            # Display summary
            if data.get("domain_exists"):
                console.print(f"[bold green][+] Domain {data['guessed_domain']} resolves![/bold green]")
                
                if data.get("subdomains"):
                    sub_count = len(data['subdomains'])
                    self.log(f"Found {sub_count} active subdomains", "success")
                    
                    table = Table(title=f"[bold cyan]Discovered Subdomains[/bold cyan]")
                    table.add_column("Subdomain", style="green")
                    table.add_column("Status", style="yellow")
                    
                    for sub in data["subdomains"][:10]: # Show top 10
                        table.add_row(sub, "Active")
                        
                    console.print(table)
                    if sub_count > 10:
                        console.print(f"[dim]...and {sub_count - 10} more subdomains[/dim]\n")
            else:
                self.log(f"Domain {data['guessed_domain']} does not resolve", "warning")
            
        except Exception as e:
            self.log(f"Domain scan error: {str(e)}", "error")
            self.results["domains"] = {"error": str(e)}
    
    def generate_summary(self):
        """Generate executive summary"""
        summary = {
            "target": self.company_name,
            "findings": []
        }
        
        # GitHub summary
        github_data = self.results.get("github", {})
        if isinstance(github_data.get("repositories"), list):
            repo_count = len(github_data["repositories"])
            if repo_count > 0:
                summary["findings"].append(f"Found {repo_count} public GitHub repositories")
                tech = github_data.get("tech_stack", {}).get("primary_languages", {})
                if tech:
                    top_lang = list(tech.keys())[0] if tech else "Unknown"
                    summary["findings"].append(f"Primary tech stack: {top_lang}")
        
        # Domain summary
        domain_data = self.results.get("domains", {})
        if domain_data.get("domain_exists"):
            sub_count = len(domain_data.get("subdomains", []))
            summary["findings"].append(f"Domain active with {sub_count} discovered subdomains")
        
        self.results["summary"] = summary
    
    def generate_report(self, output_file=None):
        """Generate final intelligence report"""
        self.log("Generating intelligence report...")
        
        self.generate_summary()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            console.print(Panel(f"Report saved to: [bold]{output_file}[/bold]", title="[bold green]Success[/bold green]", border_style="green"))
        else:
            findings_text = ""
            for finding in self.results["summary"].get("findings", []):
                findings_text += f"• {finding}\n"
            
            if not findings_text:
                findings_text = "No significant findings."
                
            console.print(Panel(
                findings_text.strip(),
                title="[bold cyan]INTELLIGENCE SUMMARY[/bold cyan]",
                border_style="cyan"
            ))
            console.print("\n")
    
    def run(self, modules=None):
        """Execute the scan"""
        self.print_banner()
        
        if not modules or "linkedin" in modules:
            self.scan_linkedin()
        
        if not modules or "github" in modules:
            self.scan_github()
        
        if not modules or "domains" in modules:
            self.scan_domains()
        
        self.log("Scan complete!", "success")


def main():
    parser = argparse.ArgumentParser(
        description="TARGET-SCOUT - OSINT Intelligence Gathering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python target-scout.py --company "Microsoft"
  python target-scout.py --company "OpenAI" --modules github,domains
  python target-scout.py --company "Google" --output report.json --verbose
  python target-scout.py --company "GitHub" --github-token YOUR_TOKEN
        """
    )
    
    parser.add_argument(
        "--company",
        required=True,
        help="Target company name"
    )
    
    parser.add_argument(
        "--domain",
        help="Specific domain to scan (overrides auto-detection)",
        default=None
    )
    
    parser.add_argument(
        "--modules",
        help="Comma-separated list of modules (linkedin,github,domains)",
        default=None
    )
    
    parser.add_argument(
        "--github-token",
        help="GitHub Personal Access Token (increases API rate limits)",
        default=None
    )
    
    parser.add_argument(
        "--output",
        help="Output file for JSON report",
        default=None
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Parse modules
    modules = args.modules.split(",") if args.modules else None
    
    # Run the scanner
    scout = TargetScout(
        args.company,
        domain=args.domain,
        github_token=args.github_token,
        verbose=args.verbose
    )
    scout.run(modules)
    scout.generate_report(args.output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
