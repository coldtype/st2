import importlib, bpy, time, os, sys
from pathlib import Path

coldtype_status = -2
C, ct, cb = None, None, None

REQUIRED_COLDTYPE = "0.10.21"

def do_import():
    global coldtype_status, C, ct, cb

    modified_path = False
    
    inlines = Path(__file__).parent / "inline-packages"

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    st2_venv_lib = Path(__file__).parent / f"st2_venv/lib/python{python_version}/site-packages"

    if inlines.exists() and "coldtype" not in sys.modules:
        modified_path = True
        sys.path.insert(0, str(inlines))
    
    if st2_venv_lib.exists() and "coldtype" not in sys.modules:
        print("attempting st2_venv...")
        modified_path = True
        sys.path.insert(0, str(st2_venv_lib))

    # apparently if you require this twice, it'll work the second time (??)
    try:
        from ufo2ft.featureCompiler import FeatureCompiler
    except ImportError:
        print("-- failed FeatureCompiler --")
        pass

    def vt(v):
        return tuple(map(int, (v.split("."))))

    #coldtype_status = 1

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

    if modified_path:
        sys.path.pop(0)


def install_coldtype(context, global_vars, required_version):
    from subprocess import run

    args = [f"coldtype[blender]=={required_version}"]
    
    print("---"*20)
    print("> INSTALLING COLDTYPE")
    print(args)
    print("---"*20)
    time.sleep(1)
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    #run([sys.executable, "-m", "pip", "install", *args], check=1, env=environ_copy)
    venv_location = Path(__file__).parent / "st2_venv"
    if venv_location.exists():
        from shutil import rmtree
        rmtree(venv_location)
        print("deleted", venv_location)
    run([sys.executable, "-m", "venv", venv_location])
    print("made", venv_location)
    venv_python = venv_location / "bin/python"
    if not venv_python.exists():
        venv_python = venv_location / "Scripts/python.exe"
    print(venv_python, venv_python.exists())
    run([venv_python, "-m", "pip", "install", "coldtype[blender]"])
    time.sleep(1)

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
]

panels = [
    ST2InstallPanel
]