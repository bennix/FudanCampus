"""Integrate the prepared unified source; accepts explicit source and report paths.

Run with the repository road-venv Python, or another Python with NumPy installed.
Source BLEND must match the independently exported and validated GLB's source hash.
The full rebuild entry is closeout-final/run_closeout.ps1.
"""
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'field-review/guanghua-refinement-v4/closeout-final/integrate.py'),run_name='__main__')
