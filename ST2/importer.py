import importlib, bpy, time, os, sys
from subprocess import run
from pathlib import Path

coldtype_status = -2
C, ct, cb = None, None, None

REQUIRED_COLDTYPE = "0.12.2"

def do_import():
    global coldtype_status, C, ct, cb

    modified_path = False
    
    inlines = Path(__file__).parent / "inline-packages"

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    st2_venv_lib = Path(__file__).parent / f"st2_venv/lib/python{python_version}/site-packages"
    if not st2_venv_lib.exists():
        st2_venv_lib = Path(__file__).parent / f"st2_venv/Lib/site-packages"

    if inlines.exists() and "coldtype" not in sys.modules:
        modified_path = True
        sys.path.insert(0, str(inlines))
    
    if st2_venv_lib.exists() and "coldtype" not in sys.modules:
        print("attempting st2_venv...")
        modified_path = True
        print(st2_venv_lib)
        sys.path.insert(0, str(st2_venv_lib))

    def vt(v):
        return tuple([int(x.split("a")[0]) for x in v.split(".")])

    try:
        import coldtype as C
        import coldtype.text as ct
        import coldtype.blender as cb

        if vt(C.__version__) < vt(REQUIRED_COLDTYPE):
            C, ct, cb = None, None, None
            coldtype_status = 0
        else:
            coldtype_status = 1

    except ImportError as e:
        print("COLDTYPE IMPORT ERROR", e)
        C, ct, cb = None, None, None
        coldtype_status = -1

    if C:
        print("import:COLDTYPE", C.__version__, C.__file__)
    else:
        print("import:COLDTYPE:fail")
    
    try:
        import AppKit, CoreText
    except ImportError:
        print("NO APPKIT/CORETEXT")

    #import uharfbuzz as asdf
    #print(asdf)

    if modified_path:
        sys.path.pop(0)


def get_venv_python(delete=True):
    try:
        venv_location = Path(__file__).parent / "st2_venv"

        if delete:
            if venv_location.exists():
                from shutil import rmtree
                rmtree(venv_location)
                print("deleted", venv_location)
        
            run([sys.executable, "-m", "venv", venv_location])

        venv_python = venv_location / "bin/python"
        if not venv_python.exists():
            venv_python = venv_location / "Scripts/python.exe"
        
        return venv_location, venv_python
    
    except Exception as e:
        print("FAILURE TO VENV", e)


def install_coldtype(context, global_vars, required_version):
    print("---"*20)
    print("> INSTALLING COLDTYPE")
    print("---"*20)
    
    time.sleep(0.25)

    _, venv_python = get_venv_python()
    
    run([venv_python, "-m", "pip", "install", f"coldtype=={required_version}", "--no-cache-dir"])

    #run([venv_python, "-m", "pip", "install", "pyobjc"])
    
    run([venv_python, "-m", "pip", "freeze"])
    time.sleep(0.25)

    return

    print("---"*20)
    print("/installed coldtype")

    time.sleep(0.25)
    print("/imported successfully")

    import coldtype as C
    import coldtype.text as ct
    import coldtype.blender as cb
    importlib.reload(C)
    importlib.reload(cb)
    importlib.reload(ct)
    print(">>>", C.__version__)


def install_extras(context, global_vars):
    from subprocess import run
    
    print("---"*20)
    print("> INSTALLING EXTRAS")
    print("---"*20)
    
    time.sleep(0.25)
    
    venv_location = Path(__file__).parent / "st2_venv"
    venv_python = venv_location / "bin/python"

    if not venv_python.exists():
        venv_python = venv_location / "Scripts/python.exe"
    
    print(venv_python, venv_python.exists())

    run([venv_python, "-m", "pip", "install", "pyobjc", "ufo2ft"])
    
    run([venv_python, "-m", "pip", "freeze"])
    time.sleep(0.25)

    return


def editor_needs_coldtype(layout, status):
    if status < 0:
        download = "Install Coldtype"
        warning = """
        This addon could not load Coldtype.
        Please install it below or contact
        rob@goodhertz.com for assistance""".strip()
    else:
        download = "Update coldtype"
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
    layout.row().operator("st2.install_coldtype", icon="WORLD_DATA", text=download)


class ST2_OT_InstallST2(bpy.types.Operator):
    """In order to work properly, ST2 needs to download and install the coldtype python package. You can install that package by clicking this button"""

    bl_label = "ST2 Install coldtype"
    bl_idname = "st2.install_coldtype"
    
    def execute(self, context):
        install_coldtype(context, globals(), REQUIRED_COLDTYPE)
        bpy.ops.script.reload()
        return {"FINISHED"}


class ST2_OT_InstallExtras(bpy.types.Operator):
    """In order for extended functionality to work properly, you’ll need to install these extras via python’s pip"""

    bl_label = "ST2 Install Extras"
    bl_idname = "st2.install_extras"
    
    def execute(self, context):
        install_extras(context, globals())
        bpy.ops.script.reload()
        return {"FINISHED"}


class ST2_OT_PrintPackges(bpy.types.Operator):
    """Print currently-installed packages"""

    bl_label = "ST2 Print Packages"
    bl_idname = "st2.print_packages"
    
    def execute(self, context):
        _, venv_python = get_venv_python(delete=False)
        res = run([venv_python, "-m", "pip", "freeze"], capture_output=True, text=True)

        print("\n--- ST2 PACKAGES ---\n")
        for line in res.stdout.split("\n"):
            if line and not line.startswith("pyobjc-framework"):
                print(">", line)
        print("\n--- ST2 PACKAGES END ---\n")

        return {"FINISHED"}


class ST2InstallPanel(bpy.types.Panel):
    bl_label = "ST2 Setup"
    bl_idname = "ST2_PT_0_INSTALLPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        return C is None
    
    def draw(self, context):
        return editor_needs_coldtype(self.layout, coldtype_status)


classes = [
    ST2_OT_InstallST2,
    ST2_OT_InstallExtras,
    ST2_OT_PrintPackges,
]

panels = [
    ST2InstallPanel
]