#!/usr/bin/env python3
"""
Aegis Code Formatter
Formats Aegis source code with consistent style.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple


class AegisFormatter:
    def __init__(self):
        self.indent_size = 4
        self.max_line_length = 100
        self.quote_style = '"'  # prefer double quotes
        
    def format_file(self, file_path: Path) -> str:
        """Format a single file and return formatted content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.format_string(content)
        
    def format_string(self, content: str) -> str:
        """Format a string of Aegis code."""
        lines = content.split('\n')
        formatted_lines = []
        indent_level = 0
        in_string = False
        string_char = None
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            if not line:
                formatted_lines.append('')
                continue
                
            # Handle comments
            if line.startswith('~'):
                formatted_lines.append(line)
                continue
                
            # Handle string literals
            if not in_string:
                # Check for string start
                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                        in_string = True
                        string_char = char
                        break
            else:
                # Check for string end
                for i, char in enumerate(line):
                    if char == string_char and (i == 0 or line[i-1] != '\\'):
                        in_string = False
                        string_char = None
                        break
                        
            if in_string:
                formatted_lines.append(' ' * (indent_level * self.indent_size) + line)
                continue
                
            # Handle indentation changes
            if line.endswith('{'):
                formatted_lines.append(' ' * (indent_level * self.indent_size) + line)
                indent_level += 1
            elif line.startswith('}'):
                indent_level = max(0, indent_level - 1)
                formatted_lines.append(' ' * (indent_level * self.indent_size) + line)
            else:
                formatted_lines.append(' ' * (indent_level * self.indent_size) + line)
                
        return '\n'.join(formatted_lines)
        
    def format_directory(self, directory: Path, recursive: bool = True) -> None:
        """Format all .aeg files in a directory."""
        pattern = "**/*.aeg" if recursive else "*.aeg"
        for file_path in directory.glob(pattern):
            self.format_single_file(file_path)
            
    def format_single_file(self, file_path: Path) -> None:
        """Format a single file in place."""
        try:
            formatted = self.format_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted)
            print(f"Formatted {file_path}")
        except Exception as e:
            print(f"Error formatting {file_path}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: aegfmt <file_or_directory> [options]")
        print("Options:")
        print("  --check    Check formatting without modifying files")
        print("  --recursive    Format directories recursively")
        return
        
    formatter = AegisFormatter()
    target = Path(sys.argv[1])
    
    if target.is_file():
        if target.suffix == '.aeg':
            if '--check' in sys.argv:
                original = target.read_text()
                formatted = formatter.format_string(original)
                if original != formatted:
                    print(f"{target} needs formatting")
                    sys.exit(1)
                else:
                    print(f"{target} is properly formatted")
            else:
                formatter.format_single_file(target)
    elif target.is_dir():
        recursive = '--recursive' in sys.argv
        formatter.format_directory(target, recursive)
    else:
        print(f"Target {target} not found")


if __name__ == "__main__":
    main()
