"""Writable settings live beside the executable; bundled assets are read-only."""
import sys
from pathlib import Path


def app_dir():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent


def resource_dir():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
