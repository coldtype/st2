import platform, re, os
from runpy import run_path

def _os(): return platform.system()
def on_windows(): return _os() == "Windows"
def on_mac(): return _os() == "Darwin"
def on_linux(): return _os() == "Linux"

root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

addon_source = os.path.join(root, "ST2")
config = run_path(os.path.join(root, "config.py"))

blender = config.get("BLENDER")
if not blender:
    if on_mac():
        blender = "/Applications/Blender.app/"

blender = os.path.abspath(os.path.expanduser(blender))

if on_mac():
    res = os.path.join(blender, "Contents/Resources")
    version = None
    for p in os.listdir(res):
        if os.path.isdir(os.path.join(res, p)):
            name = os.path.basename(p)
            if re.match(r"[23]{1}\.[0-9]{1,2}", name):
                version = name
    
    addon_path = "".join(["~/Library/Application Support/Blender/", version, "/scripts/addons"])
    addon_path = os.path.abspath(os.path.expanduser(addon_path))
    addon = os.path.join(addon_path, "ST2")
    
    python_folder = os.path.join(blender, "Contents/Resources", version, "python/bin")
    python = None

    for f in os.listdir(python_folder):
        name = os.path.basename(f)
        if name.startswith("python"):
            python = os.path.join(python_folder, f)

    bpy = python

    blender_executable = os.path.join(blender, "Contents/MacOS/Blender")
