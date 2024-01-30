#export BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

b3denv clean ST2
rm -rf venv

b3denv python -m venv venv
source venv/Scripts/activate
pip install -r requirements_win.txt
deactivate

b3denv inline ST2
b3denv release ST2 suffix=win