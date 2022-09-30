import sys
sys.path.insert(0, ".")

from scripts.blender import *

if on_mac():
    if addon.exists(): addon.unlink()
    subprocess.run(["ln", "-s", addon_source, addon])
    sys.stdout.write(str(blender_executable))