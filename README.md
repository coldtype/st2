# ST2

![The ST2 UI](assets/uipreview2.jpg)

### Download

Grab the latest zip from [coldtype.xyz/st2](https://coldtype.xyz/st2)

### Why?

Blender is a very cool program that does a ton of things very well. One of the things it does _not_ do very well is typography (for example, even basic typographical features like kerning are not supported).

That’s why ST2 exists: an add-on to help you set 3D type with the full range of modern typographical features — among them OpenType stylistics sets, ligatures, and, yes, kerning. ST2 also provides support for typesetting all kinds of languages (not just Latin-based ones).

Also Blender does not have support for variable fonts; this add-on adds support for those, along with support for keyframing variable font axes. (This is a little experimental though, as Blender will sometimes crash if you change meshes too often, particularly on macOS. To get around this, the ST2 add-on provides an "export" mechanism that will create a new object for every frame of your animation, and then show that instance on the appropriate frame only.)

### Installing

Using a Blender version 3.0 or later, grab the latest release from [the home page](https://coldtype.xyz/st2), download the zip, then open Blender, open the Blender preferences, head to "Add-ons," then hit "Install..." in the top-bar and navigate to the ST2 zip you downloaded and hit "Install Add-on" — this should bring up ST2 in the Add-ons view (if it doesn't, try searching for "ST2"); once you see it listed with a checkbox, enable the extension by hitting the checkbox.

### Development

First, make sure to install [`b3denv`](https://github.com/coldtype/b3denv)

- macOS
    - `b3denv python -m venv venv`
    - `source venv/bin/activate`
    - `pip install -r requirements_mac.txt`
- Windows
    - `b3denv python -m venv venv`
    - `source venv/Scripts/activate`
    - `pip install -r requirements_win.txt`
- Inline venv dependencies so addon can be bundled:
    - `b3denv inline ST2`
- Install the extension via symlink:
    - `b3denv install ST2`
- Launch Blender from the command-line:
    - `b3denv`
