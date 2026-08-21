"""Launcher script for the RDMA configuration GUI.

Run this file from any working directory:
    python guiLauncher.py
"""

import sys
import os

# Ensure the Python package root is on the path regardless of working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_sharing_framework_config_api.gui.app import main

if __name__ == "__main__":
    main()
