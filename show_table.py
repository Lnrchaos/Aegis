#!/usr/bin/env python3
"""
Script to demonstrate where the rainbow table is stored
"""

import sys
sys.path.insert(0, '.')

from aegis.env import make_global_env
from aegis.repl import _action_generate_table

# Create environment
env = make_global_env()

# Generate a table
_action_generate_table(env, [])

# Show where it's stored
try:
    table = env.get("LAST_GENERATED")
    print("Rainbow Table Location:")
    print(f"  Variable: LAST_GENERATED")
    print(f"  Type: {type(table)}")
    print(f"  Content: {table}")
    print(f"  Memory Address: {id(table)}")
except Exception as e:
    print(f"Error: {e}")
