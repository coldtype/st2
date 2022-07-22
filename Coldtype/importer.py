import importlib.util as iu
import time, os, sys

def require_coldtype(global_vars):
    if iu.find_spec("coldtype"):
        #from coldtype.text import StSt, Glyphwise, Style, Font, FontNotFoundException
        #from coldtype.blender import BpyObj
        import coldtype.text as ct
        import coldtype.blender as cb
        global_vars["coldtype_found"] = True
        global_vars["ct"] = ct
        global_vars["cb"] = cb
    else:
        global_vars["coldtype_found"] = False


def install_coldtype(context, global_vars):
    from subprocess import run
    
    args = ["coldtype[blender]"]
    #if True:
    #    args = ["-e", str(Path("~/Goodhertz/coldtype[blender]").expanduser())]
    
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

    time.sleep(1)
    #globals()["coldtype"] = importlib.import_module("coldtype")

    require_coldtype(global_vars)
    print("imported successfully")


def editor_needs_coldtype(layout):
    warning = """This addon requires Coldtype
        (coldtype.xyz) as a Python package.
        -
        Clicking the button below will
        download and install Coldtype.
        It should only take a few moments
        to install."""
    
    for line in warning.splitlines():
        if line.strip() == "-":
            layout.row().separator()
        else:
            row = layout.row()
            row.scale_y = 0.6
            row.label(text=line.strip())
    
    layout.row().separator()
    layout.row().operator("ctxyz.install_coldtype", icon="WORLD_DATA", text="Download & Install Coldtype")
