import bpy
from coldtype import *

obj = bpy.data.objects["vcme_cropped"]
dim = obj.dimensions
loc = obj.location

dst = bpy.data.objects["DynamicOutline"]

dst.location.x = loc.x
dst.location.y = loc.y
dst.location.z = loc.z

def modify(st2:dict, kwargs:dict, p:P, funcs):
    topbar = 0.092
    out = 0.005

    pimage = P().rect(Rect(dim.x, dim.y)).centerZero()
    r = pimage.ambit().inset(-out, -out-topbar/2)
    shape = (P().rr(r, 0.08, scale=False)
        .t(0, topbar/2))
    
    piece = kwargs.get("piece", 0)
    
    if piece == 1:
        return shape.outline(out)
    elif piece == 2:
        return shape.difference(P(r.drop(topbar/4, "N")))