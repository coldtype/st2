from coldtype import *

# make sure to select hobeaux borders otf
# in the ST2 font picker in Blender
# (or else this script won’t work)

styles = [
    "Aa ", "B  ", "Cc3", "Dd4", "Ee5",
    "Ff6", "Gg ", "Hh8", "Ii9", "Jj0",
    "Kk!", "Ll@", "Mm#", "Nn$", "Oo%",
    "Pp^", "Qq&", "Rr ", "Ss(", "Tt)",
    "Uu-", "Vv=", "Ww_", "Xx+", "Yy ",
]

def hobeauxBorder(r, text, font, fs=2):
    b, c, m = [StSt(x, font, fs).pen() for x in text[:3]]
    bw, cw = [e.ambit().w for e in (b, c)]
    
    nh, nv = int(r.w/bw/2), int(r.h/bw/2)
    bx = Rect(bw*nh*2+cw*2, bw*nv*2).align(r)

    return (b.layer(
        lambda p: p
            .layer(nh)
            .append(c)
            .distribute()
            .append(m)
            .mirrorx()
            .translate(*bx.pn)
            .mirrory(bx.pc),
        lambda p: p
            .layer(nv)
            .distribute()
            .append(m.copy())
            .rotate(90, point=(0, 0))
            .translate(cw, 0)
            .mirrory()
            .translate(*bx.pw)
            .mirrorx(bx.pc))
        .pen()
        .unframe())

def modify(st2:dict, kwargs:dict):
    try:
        txt = styles[int(st2.text)]
    except:
        txt = st2.text
    
    w = kwargs.get("width", 4)
    h = kwargs.get("height", w)
    fs = kwargs.get("fontSize", 4)
    
    return (hobeauxBorder(Rect(w, h), txt, st2.font_path, fs)
        .centerZero())