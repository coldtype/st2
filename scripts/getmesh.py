from pathlib import Path

TYPO = Path(__file__).parent.parent

CT = TYPO.parent
meshtable = CT / "MESH/mesh/__init__.py"

dst = TYPO / "Coldtype/meshtable.py"
dst.write_text("# AUTOMATED FILE COPY\n" + meshtable.read_text())