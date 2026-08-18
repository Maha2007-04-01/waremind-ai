"""
conftest.py — auto-loaded by pytest before any test file.
Adds backend/ to sys.path so 'app', 'database.seed', etc. resolve correctly
both at runtime AND in IDEs that honour conftest for path discovery.
"""
import sys
import os

# Make backend/ importable without needing sys.path in every test file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
