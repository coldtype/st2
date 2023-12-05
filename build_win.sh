export BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
alias bpy=$(py.exe -m b3denv print python)
alias blender=$(py.exe -m b3denv print blender)

rm -rf ST2/inline-packages
rm -rf venv

bpy -m venv venv
source venv/Scripts/activate
pip install -r requirements_win.txt
deactivate

py.exe -m b3denv inline ST2
py.exe -m b3denv release ST2 suffix=win