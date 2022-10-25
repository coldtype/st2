import sys, subprocess
sys.path.insert(0, ".")

from scripts.blender import *

if on_mac():
    if os.path.exists(addon): os.unlink(addon)
    subprocess.run(["ln", "-s", addon_source, addon])
    sys.stdout.write(str(blender_executable))