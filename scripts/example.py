from coldtype import *

def modify(st2:dict, kwargs:dict):
    return (StSt(st2.text, st2.font_path, 1, wdth=0)
        .pen()
        .unframe()
        .layer(5)
        .stack(0.5)
        .centerZero()
        )