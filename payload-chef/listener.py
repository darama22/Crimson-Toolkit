#!/usr/bin/env python3
"""
Simple TCP Listener - Alternative to Netcat for Windows (Fixed Version)
"""

import socket
import sys
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

def start_listener(port=4444):
    """Start TCP listener on specified port"""
    
    console.print(Panel(
        f"[cyan]Listening on[/cyan] [yellow]0.0.0.0:{port}[/yellow]\n"
        f"[dim]Waiting for reverse shell connection...[/dim]",
        title="[bold green]TCP Listener Active[/bold green]",
        border_style="green"
    ))
    
    # Create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', port))
        server.listen(1)
        
        console.print(f"[yellow]Press Ctrl+C to stop[/yellow]\n")
        
        # Wait for connection
        client, addr = server.accept()
        
        console.print(Panel(
            f"[green]Connection received from[/green] [yellow]{addr[0]}:{addr[1]}[/yellow]",
            border_style="green"
        ))
        
        console.print("[cyan]Interactive shell active. Type commands:[/cyan]\n")
        
        # Set non-blocking mode with timeout
        client.settimeout(1.0)
        
        # Interactive loop
        while True:
            try:
                # Get command from user
                command = input(f"\n[{addr[0]}]> ")
                
                if command.lower() in ['exit', 'quit']:
                    console.print("[yellow]Closing connection...[/yellow]")
                    client.send(b"exit\n")
                    break
                
                if not command.strip():
                    continue
                
                # Send command
                client.send((command + "\n").encode())
                
                # Wait a bit for execution
                time.sleep(0.2)
                
                # Receive response with timeout
                response = b""
                start_time = time.time()
                
                while time.time() - start_time < 3.0:  # Max 3 seconds
                    try:
                        chunk = client.recv(4096)
                        if chunk:
                            response += chunk
                            # Reset timeout if we're getting data
                            start_time = time.time()
                        else:
                            break
                    except socket.timeout:
                        # If we have some data and timeout, we're probably done
                        if response:
                            break
                        continue
                    except Exception:
                        break
                
                # Display response
                if response:
                    output = response.decode('utf-8', errors='ignore')
                    print(output, end='')
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                break
            except EOFError:
                console.print("\n[yellow]Connection closed[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                break
        
        client.close()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Listener stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        server.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4444
    
    console.print("""
[bold cyan]═══════════════════════════════════════[/bold cyan]
[bold cyan]     TCP Listener (Netcat Alternative)[/bold cyan]
[bold cyan]═══════════════════════════════════════[/bold cyan]
    """)
    
    start_listener(port)
