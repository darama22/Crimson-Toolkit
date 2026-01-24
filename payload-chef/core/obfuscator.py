#!/usr/bin/env python3
"""
Source-Level Obfuscator for Go Code
Applies transformations BEFORE compilation
"""

import random
import string
import re

class GoObfuscator:
    def __init__(self, level="medium"):
        self.level = level
        self.var_map = {}  # Maps original names to obfuscated names
        
    def obfuscate(self, go_source):
        """Apply all obfuscation techniques"""
        source = go_source
        
        if self.level in ["medium", "high"]:
            source = self.rename_variables(source)
            source = self.inject_junk_code(source)
        
        if self.level == "high":
            source = self.encrypt_strings(source)
            source = self.add_dead_branches(source)
        
        return source
    
    def rename_variables(self, source):
        """Rename variables and functions to random names"""
        # Find all function names (except main)
        func_pattern = r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        for match in re.finditer(func_pattern, source):
            func_name = match.group(1)
            if func_name not in ['main', 'init']:
                new_name = self._random_name()
                self.var_map[func_name] = new_name
                source = re.sub(r'\b' + func_name + r'\b', new_name, source)
        
        # Find local variables
        var_pattern = r'\b(var|:=)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        vars_to_rename = []
        
        for match in re.finditer(var_pattern, source):
            var_name = match.group(2)
            # Skip common Go keywords and imported package names
            if var_name not in ['err', 'main', 'conn', 'cmd'] and len(var_name) > 1:
                vars_to_rename.append(var_name)
        
        # Rename variables
        for var_name in set(vars_to_rename):
            new_name = self._random_name(6)
            source = re.sub(r'\b' + var_name + r'\b', new_name, source)
        
        return source
    
    def inject_junk_code(self, source):
        """Add random unused code"""
        junk_functions = [
            '''
func {name}() int {{
    x := {num1} * {num2}
    if x > 1000 {{
        return x % {num3}
    }}
    return 0
}}
''',
            '''
func {name}(a, b int) bool {{
    return (a + b) > {num1}
}}
''',
        ]
        
        # Insert junk functions before main()
        main_index = source.find('func main()')
        if main_index != -1:
            junk_code = ""
            for i in range(random.randint(2, 4)):
                template = random.choice(junk_functions)
                junk_code += template.format(
                    name=self._random_name(),
                    num1=random.randint(10, 99),
                    num2=random.randint(10, 99),
                    num3=random.randint(2, 10)
                )
            
            source = source[:main_index] + junk_code + source[main_index:]
        
        return source
    
    def encrypt_strings(self, source):
        """Encrypt string literals with XOR, avoiding imports"""
        
        # 1. Identify import blocks and create a mask efficiently
        # We'll use a list of (start, end) tuples for protected regions
        protected_regions = []
        
        # Match multi-line import (...)
        for match in re.finditer(r'import\s*\((.*?)\)', source, re.DOTALL):
            protected_regions.append(match.span())
            
        # Match single-line import "..."
        for match in re.finditer(r'import\s+"[^"]+"', source):
            protected_regions.append(match.span())

        # Find all string literals
        string_pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'

        # We need to construct the result manually to handle the conditional replacement logic
        # because re.sub doesn't provide easy access to the match position
        
        result = []
        last_pos = 0
        
        for match in re.finditer(string_pattern, source):
            start, end = match.span()
            
            # Check if this string is in a protected region
            is_protected = False
            for p_start, p_end in protected_regions:
                if start >= p_start and end <= p_end:
                    is_protected = True
                    break
            
            # Additional check: Skip if it looks like a config placeholder
            text = match.group(1)
            if text.startswith('{{') or len(text) < 3:
                is_protected = True

            # Append text before this match
            result.append(source[last_pos:start])
            
            if is_protected:
                # Keep original string
                result.append(match.group(0))
            else:
                # Encrypt
                key = random.randint(1, 255)
                try:
                    encrypted = [ord(c) ^ key for c in text]
                    array = ', '.join([f'0x{b:02x}' for b in encrypted])
                    result.append(f'string(xorDecrypt([]byte{{{array}}}, 0x{key:02x}))')
                except:
                   # Fallback on encoding error
                   result.append(match.group(0))
            
            last_pos = end
            
        # Append remaining text
        result.append(source[last_pos:])
        source = "".join(result)

        # Add decrypt function if not present
        if 'func xorDecrypt' not in source:
            decrypt_func = '''
func xorDecrypt(data []byte, key byte) []byte {
	result := make([]byte, len(data))
	for i, b := range data {
		result[i] = b ^ key
	}
	return result
}
'''
            # Insert before main
            main_index = source.find('func main()')
            if main_index != -1:
                source = source[:main_index] + decrypt_func + source[main_index:]
        
        return source
    
    def add_dead_branches(self, source):
        """Add conditional code that never executes"""
        dead_code_templates = [
            '''
	if {var} := {num1} * {num2}; {var} < 0 {{
		// This never executes (positive * positive can't be negative)
		return
	}}
''',
            '''
	if false {{
		var x = "{random_str}"
		_ = x
	}}
''',
        ]
        
        # Insert dead code in main() function
        main_body_match = re.search(r'func main\(\)\s*\{', source)
        if main_body_match:
            insert_pos = main_body_match.end()
            
            dead_code = random.choice(dead_code_templates).format(
                var=self._random_name(4),
                num1=random.randint(10, 50),
                num2=random.randint(10, 50),
                random_str=''.join(random.choices(string.ascii_letters, k=8))
            )
            
            source = source[:insert_pos] + dead_code + source[insert_pos:]
        
        return source
    
    def _random_name(self, length=8):
        """Generate random identifier name"""
        # Start with letter, then alphanumeric
        first = random.choice(string.ascii_lowercase)
        rest = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-1))
        return first + rest

if __name__ == "__main__":
    # Test obfuscator
    test_code = '''package main
import "fmt"

func greet(name string) {
    message := "Hello, " + name
    fmt.Println(message)
}

func main() {
    greet("World")
}
'''
    
    obf = GoObfuscator(level="high")
    obfuscated = obf.obfuscate(test_code)
    
    print("=== OBFUSCATED CODE ===")
    print(obfuscated)
