import time, os, sys


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

    time.sleep(0.25)
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
