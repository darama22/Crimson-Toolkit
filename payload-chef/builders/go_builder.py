#!/usr/bin/env python3
"""
Go Builder - Compiles Go templates into native executables
"""

import subprocess
import os
import shutil
from pathlib import Path

class GoBuilder:
    def __init__(self):
        self.check_go_installed()
    
    def check_go_installed(self):
        """Verify Go is installed, checking common paths"""
        try:
            # Try default path first
            subprocess.run(["go", "version"], capture_output=True, check=True)
            print(f"[+] Go detected in PATH")
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Check common Windows paths
            common_paths = [
                r"C:\Program Files\Go\bin",
                r"C:\Go\bin",
                os.path.expanduser(r"~\go\bin"),
                os.path.expanduser(r"~\sdk\go1.21.0\bin")
            ]
            
            found = False
            for path in common_paths:
                go_exe = os.path.join(path, "go.exe")
                if os.path.exists(go_exe):
                    print(f"[+] Go found at: {go_exe}")
                    # Add to PATH for this process
                    os.environ["PATH"] += os.pathsep + path
                    found = True
                    break
            
            if not found:
                # Last ditch effort: Try to use the full path in the command if we found it but adding to path failed for some reason? 
                # Actually, if we found it, we added it to os.environ, so resolving "go" should work for subprocess in subsequent calls 
                # IF we pass env=os.environ. But to be safe, we might need to verify.
                raise Exception(
                    "Go not found. Please install it or add to PATH.\n"
                    "Download: https://golang.org/dl/\n"
                    "Windows: winget install GoLang.Go"
                )
    
    def compile(self, source_file, output_name, options=None):
        """
        Compile Go source to executable
        
        Args:
            source_file: Path to .go file
            output_name: Output executable name
            options: Dict with compilation options
        """
        if options is None:
            options = {}
        
        # Default evasion flags
        ldflags = [
            "-s",  # Strip symbol table
            "-w",  # Strip DWARF debugging info
        ]
        
        # Windows-specific: hide console window
        if options.get("windows_gui", False):
            ldflags.append("-H windowsgui")
        
        # Build command
        cmd = [
            "go", "build",
            f"-ldflags={' '.join(ldflags)}",
            "-trimpath",  # Remove build paths from binary
            "-o", output_name,
            source_file
        ]
        
        # Cross-compilation support
        env = os.environ.copy()
        if options.get("target_os"):
            env["GOOS"] = options["target_os"]
        if options.get("target_arch"):
            env["GOARCH"] = options["target_arch"]
        
        print(f"[*] Compiling: {source_file} -> {output_name}")
        print(f"[*] Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check output file exists
            if os.path.exists(output_name):
                size = os.path.getsize(output_name) / 1024  # KB
                print(f"[+] Compilation successful! Size: {size:.1f} KB")
                return True
            else:
                print(f"[-] Output file not found: {output_name}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"[-] Compilation failed!")
            print(f"STDERR: {e.stderr}")
            return False

if __name__ == "__main__":
    # Quick test
    builder = GoBuilder()
    
    # Test compilation with a simple Go file
    test_code = '''package main
import "fmt"
func main() {
    fmt.Println("Hello from PAYLOAD-CHEF!")
}
'''
    
    # Write test file
    test_path = "test_build.go"
    with open(test_path, "w") as f:
        f.write(test_code)
    
    # Compile
    builder.compile(test_path, "test.exe", {"windows_gui": False})
    
    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)
