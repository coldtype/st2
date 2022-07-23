import zipfile
from pathlib import Path

VERSION = (0, 1)
mj, mn = VERSION

root = Path(__file__).parent.parent
releases = root / "releases"
releases.mkdir(exist_ok=True, parents=True)

release:Path = releases / f"Coldtype-for-Blender-v{mj}-{mn}.zip"
if release.exists():
    release.unlink()

zf = zipfile.ZipFile(release, "w")
for file in Path("Coldtype").iterdir():
    if not file.is_dir():
        zf.write(file)
zf.close()