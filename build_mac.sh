#export BLENDER_PATH="~/Desktop/Blenders/Blender3.4.app"

# Intel Build

rm -rf ST2/inline-packages
rm -rf venv

# TODO use an actual intel Blender build for this env?
python3.10-intel64 -m venv venv
source venv/bin/activate
pip install -r requirements_mac.txt
deactivate

b3denv inline ST2
b3denv release ST2 suffix=mac_intel

# AMD64 Build

rm -rf ST2/inline-packages
rm -rf venv

b3denv python -m venv venv
source venv/bin/activate
pip install -r requirements_mac.txt
deactivate

b3denv inline ST2
b3denv release ST2 suffix=mac_silicon

mkdir -p ~/Coldtype/coldtype.xyz/site/st2/downloads
ditto _releases ~/Coldtype/coldtype.xyz/site/st2/downloads