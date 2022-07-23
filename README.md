### Development

Make a file `config.py` at the root of this directory, with one line setting a `BLENDER` variable to the specific Blender app/version you'd like to use for development, i.e.:

```python
BLENDER = "~/Desktop/Blenders/Blender3.2.1.app"
```

Then you can run the install script:

`python3.10 scripts/install.py`

That should place a symlink to `Coldtype` in the correct addons folder.