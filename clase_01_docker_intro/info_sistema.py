#!/usr/bin/env python3
import os
import sys
import platform

print(f"Python: {sys.version}")
print(f"Sistema: {platform.system()} {platform.version()}")
print(f"CPUs disponibles: {os.cpu_count()}")
print("Variables PYTHON:")
for key, value in os.environ.items():
    if key.startswith("PYTHON"):
        print(f"  {key}={value}")
