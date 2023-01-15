export BLENDER_PATH="~/Desktop/Blenders/Blender3.4.app"
alias bpy=$(b3denv bpy)
alias blender=$(b3denv blender)

rm -rf venv
python3.10-intel64 -m venv venv
source venv/bin/activate
echo $(python --version)
pip install "coldtype[blender]==0.10.1"
pip install pyobjc-framework-Cocoa pyobjc-framework-CoreText
deactivate

rm -rf ST2/inline-packages
b3denv inline ST2
b3denv release ST2 suffix=mac_m1


rm -rf venv
bpy -m venv venv
source venv/bin/activate
echo $(python --version)
pip install "coldtype[blender]==0.10.1"
pip install pyobjc-framework-Cocoa pyobjc-framework-CoreText
deactivate

rm -rf ST2/inline-packages
b3denv inline ST2

b3denv release ST2 suffix=mac_intel