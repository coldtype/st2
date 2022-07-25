import sys
sys.path.insert(0, ".")

import zipfile
from pathlib import Path
from runpy import run_path
from scripts.blender import *

metadata = run_path(root / "Coldtype/metadata.py")
mj, mn = metadata["bl_info"]["version"]

releases = root / "_releases"
releases.mkdir(exist_ok=True, parents=True)

release:Path = releases / f"Coldtype-for-Blender-v{mj}-{mn}.zip"
if release.exists():
    release.unlink()

zf = zipfile.ZipFile(release, "w")
for file in Path("Coldtype").iterdir():
    if not file.is_dir():
        zf.write(file)
zf.close()