import importlib
import time, os, sys


def install_coldtype(context, global_vars, required_version):
    from subprocess import run
    
    args = [f"coldtype[blender]>={required_version}"]
    
    print("---"*20)
    print("> INSTALLING COLDTYPE")
    print(args)
    print("---"*20)
    time.sleep(1)
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"
    run([sys.executable, "-m", "pip", "install", *args], check=1, env=environ_copy)
    print("---"*20)
    print("/installed coldtype")

    time.sleep(0.25)
    print("/imported successfully")

    import coldtype as C
    importlib.reload(C)
    print(">>>", C.__version__)


def editor_needs_coldtype(layout, status):
    if status < 0:
        download = "Download & Install Coldtype"
        warning = """This addon requires Coldtype
            (coldtype.xyz) as a Python package.
            -
            Clicking the button below will
            download and install Coldtype.
            It should only take a few moments
            to install."""
    else:
        download = "Update Coldtype"
        warning = """This version requires an update
            to the coldtype python package
            -
            Clicking the button below will download
            and install an updated coldtype-python.
            It should only take a few moments."""
    
    for line in warning.splitlines():
        if line.strip() == "-":
            layout.row().separator()
        else:
            row = layout.row()
            row.scale_y = 0.6
            row.label(text=line.strip())
    
    layout.row().separator()
    layout.row().operator("ctxyz.install_coldtype", icon="WORLD_DATA", text=download)
