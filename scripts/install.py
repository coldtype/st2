import platform, os, subprocess, re

from pathlib import Path
from runpy import run_path

def os(): return platform.system()
def on_windows(): return os() == "Windows"
def on_mac(): return os() == "Darwin"
def on_linux(): return os() == "Linux"

root = Path(__file__).parent.parent

coldtype = (root / "Coldtype").absolute()
config = run_path(root / "config.py")

blender = config.get("BLENDER")
if not blender:
    if on_mac():
        blender = "/Applications/Blender.app/"

blender = Path(blender).expanduser().absolute()

print("---")
print(coldtype)
print(blender)
print("---")

if on_mac():
    res = blender / "Contents/Resources"
    version = None
    for p in res.iterdir():
        if p.is_dir() and re.match(r"3\.[0-9]{1,2}", p.name):
            version = p.name
        
    dst = (Path("~/Library/Application Support/Blender") / version / "scripts/addons/Coldtype").expanduser().absolute()
    subprocess.run(["ln", "-s", coldtype, dst])
