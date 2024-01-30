#export BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

rm -rf ST2/inline-packages
rm -rf venv

b3denv python -m venv venv
source venv/Scripts/activate
pip install -r requirements_win.txt
deactivate

b3denv inline ST2
b3denv release ST2 suffix=win