BLENDER_PATH="~/Desktop/BLENDERS/Blender4.1.1.app/" b3denv release suffix=mac_silicon
BLENDER_PATH="~/Desktop/BLENDERS/Blender4.2.app/" b3denv release suffix=mac_silicon

# # Intel Build

# b3denv clean ST2
# rm -rf venv

# # TODO use an actual intel Blender build for this env?
# python3.10-intel64 -m venv venv
# source venv/bin/activate
# pip install -r requirements_mac.txt
# deactivate

# b3denv inline ST2
# b3denv release ST2 suffix=mac_intel

# # AMD64 Build

# b3denv clean ST2
# rm -rf venv

# b3denv python -m venv venv
# source venv/bin/activate
# pip install -r requirements_mac.txt
# deactivate

# b3denv inline ST2
# b3denv release ST2 suffix=mac_silicon

# #mkdir -p ~/Coldtype/coldtype.xyz/site/st2/downloads
# #ditto _releases ~/Coldtype/coldtype.xyz/site/st2/downloads