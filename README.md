# ST2

![The ST2 UI](assets/uipreview.png)

### Why?

Blender is a very cool program that does a ton of things very well. One of the things it does _not_ do very well is typography (for example, even basic typographical features like kerning are not supported).

That’s why ST2 exists: an add-on to help you set 3D type with the full range of modern typographical features — among them OpenType stylistics sets, ligatures, and, yes, kerning. ST2 also provides support for typesetting all kinds of languages (not just Latin-based ones).

Also Blender does not have support for variable fonts; this add-on adds support for those, along with support for keyframing variable font axes. (This is a little experimental though, as Blender will sometimes crash if you change meshes too often, particularly on macOS. To get around this, the ST2 add-on provides an "export" mechanism that will create a new object for every frame of your animation, and then show that instance on the appropriate frame only.)

### Installing

Using a Blender version 3.0 or later, grab the latest release from [the releases page](https://github.com/coldtype/st2/releases), download the zip, then open Blender, open the Blender preferences, head to "Add-ons," then hit "Install..." in the top-bar and navigate to the ST2 zip you download and hit "Install Add-on" — this should bring up ST2 in the Add-ons view (if it doesn't, try searching for "ST2"); once you see it listed with a checkbox, enable the extension by hitting the checkbox.

__N.B.__ On Windows, the first time you use the ST2 addon, you’ll need to run Blender as administrator (i.e. right-click and Run as Administrator).

### Development

Make a file `config.py` at the root of this directory, with one line setting a `BLENDER` variable to the specific Blender app/version you'd like to use for development, i.e.:

```python
BLENDER = "~/Desktop/Blenders/Blender3.2.1.app"
```

Then you can run the install script:

`python3.10 scripts/install.py`

That should place a symlink to `ST2` in the correct addons folder.