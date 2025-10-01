#!/usr/bin/env python3
"""
Test script to verify Aegis installation and entry points.
"""

import subprocess
import sys
from pathlib import Path

def test_command(command, expected_output=None):
    """Test if a command works."""
    try:
        result = subprocess.run([command, "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 or "Usage:" in result.stdout or "usage:" in result.stdout:
            print(f"[OK] {command} command works")
            return True
        else:
            print(f"[FAIL] {command} command failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {command} command timed out")
        return False
    except FileNotFoundError:
        print(f"[FAIL] {command} command not found")
        return False
    except Exception as e:
        print(f"[FAIL] {command} command error: {e}")
        return False

def main():
    print("Testing Aegis installation...")
    print("=" * 50)
    
    # Test commands
    commands = ["aegis", "aegpm", "aegfmt", "aegtest"]
    results = []
    
    for cmd in commands:
        results.append(test_command(cmd))
    
    print("=" * 50)
    
    if all(results):
        print("All commands working! Installation successful!")
        print("\nYou can now use:")
        print("  aegis          - Start the Aegis REPL")
        print("  aegpm init     - Initialize a new project")
        print("  aegfmt file.aeg - Format Aegis code")
        print("  aegtest run    - Run tests")
        return 0
    else:
        print("Some commands failed. Check installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
