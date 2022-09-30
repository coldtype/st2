import platform, subprocess, re, sys

from pathlib import Path
from runpy import run_path

def _os(): return platform.system()
def on_windows(): return _os() == "Windows"
def on_mac(): return _os() == "Darwin"
def on_linux(): return _os() == "Linux"

root = Path(__file__).parent.parent

addon_source = (root / "ST2").absolute()
config = run_path(root / "config.py")

blender = config.get("BLENDER")
if not blender:
    if on_mac():
        blender = "/Applications/Blender.app/"

blender = Path(blender).expanduser().absolute()

if on_mac():
    res = blender / "Contents/Resources"
    version = None
    for p in res.iterdir():
        if p.is_dir() and re.match(r"3\.[0-9]{1,2}", p.name):
            version = p.name
        
    addon = (Path("~/Library/Application Support/Blender") / version / "scripts/addons/ST2").expanduser().absolute()
    bpy = blender / f"Contents/Resources/{version}/python/bin/python3.10"

    blender_executable = blender / "Contents/MacOS/Blender"