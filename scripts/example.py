#import bpy
from coldtype import *


def modify(st2:dict, kwargs:dict, p:P, funcs):
    #font = Font.Find(st2.font_path)
    #axis1_tag = list(font.variations().values())[0].get("axisTag")

    return (Glyphwise((st2.text+"\n")*3, lambda x:
        Style(st2.font_path, 2, **{"wdth":ez(funcs.fe(-x.i*11), "seio", 1)}))
        .lead(0.1)
        .xalign()
        .pen()
        .unframe()
        .centerZero())