from coldtype import *
from coldtype.web.site import *

header: jinja_html = """
<div class="wrapper">
    <h1 id="var">ST2</h1>
    <ul class="link-list">{% for k,v in info["externals"].items() %}
        <li><a href="{{v}}">{{k}}</a></li>
    {% endfor %}</ul>
</div>
"""
index: jinja_html = """
<p><strong><em>ST2 is a typography addon for Blender.</em></strong></p>
<p>Why does it exist?</p>
<ul>
    <li>Blender is awesome, but its built-in text tool is extremely basic (no kerning, no OpenType, no variable fonts).</li>
    <li>ST2 is a Blender addon that makes the latest in font-rendering technology available directly inside Blender.</li>
    <li>If you want to get the most from your fonts: install the ST2 addon for Blender.</li>
    <li>⚠️ ST2 is still in beta, so there might be (plenty of) bugs. If you find one, please file an issue on our Github page.</li>
</ul>
<hr/>
<div class="downloads">
<h2>Downloads</h2>
<!--<h3>Platform-agnostic</h3>-->
<p>Install via the Blender Addons preferences screen (not the extensions screen if you’re on Blender >= 4.2)</p>
<ul>
    <li><a href="releases/ST2-v0-17b.zip">ST2-v0-17.zip</a></li>
</ul>
<!--<h3>macOS</h3>
<ul>
    <li><a href="assets/releases/ST2-v0-16_Blender4.0_mac_silicon.zip">ST2-v0-16_Blender4.0_mac_silicon.zip</a></li>
    <li><a href="assets/releases/ST2-v0-16_Blender4.1_mac_silicon.zip">ST2-v0-16_Blender4.1_mac_silicon.zip</a></li>
    <li><a href="assets/releases/ST2-v0-16_Blender4.2_mac_silicon.zip">ST2-v0-16_Blender4.2_mac_silicon.zip</a></li>
</ul>
<h3 style="margin-top:20px">Linux</h3>
<ul>
    <li><a href="releases/ST2-v0-15_Blender4.2_linux.zip">ST2-v0-15_Blender4.2_linux.zip</a></li>
</ul>
<h3 style="margin-top:20px">Windows</h3>
<ul>
    <li><a href="releases/ST2-v0-16_blender41_win.zip">ST2-v0-16_blender41_win.zip</a></li>
</ul>-->
</div>
<hr/>
<p>Here’s a talk about ST2:</p>
<ul>
    <li><a href="https://youtu.be/gV2laWd727U">The How & Why of ST2</a> (inScript 2022)</li>
</ul>
"""
footer: jinja_html = """
<p>ST2 is a project of <a href="https://coldtype.xyz">Coldtype</a>;<br/>development is led by <a href="https://robstenson.com">Rob Stenson</a>.</p>
"""

style: css = """
* { box-sizing: border-box; }
:root { --border-color: #eee; }
html, body { height: 100%; }
body {
    background: hsl(330, 80%, 98%);
    background: white;
    color: #222;
    font-family: var(--text-font);
    display: flex;
    flex-direction: column;
}
em { font-style: normal; --text-font: fvs(ital=1); }
strong em { font-style: normal; --text-font: fvs(wght=0.75, ital=1); }
a { color: royalblue; text-decoration: none; }
h1 { --text-font: fvs(wght=1, ital=1); }
h2 { --text-font: fvs(wght=0.75); text-align: center; margin-bottom: 10px; }
h3 { --text-font: fvs(wght=0.65, ital=1); margin-bottom: 10px; }

/* header { border-bottom: 1px solid var(--border-color); }
footer { border-top: 1px solid var(--border-color); } */

header, footer, main {
    flex: 1;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
}
header, footer {
    text-align: center;
    max-height: 300px;
    min-height: 200px;
}
.wrapper { max-width: 500px; }

.link-list {
    list-style: none;
    display: flex;
    flex-wrap: wrap;
    margin-top: 16px;
    justify-content: center;
    row-gap: 12px;
}
.link-list li:not(:last-child)::after { content: "///"; color: #ccc; }
.link-list li a { padding: 4px 7px; background: hotpink; color: white; }
.link-list li a:hover { background: lightpink; }

main p { margin-bottom: 16px; }
main strong { --text-font: fvs(wght=0.7); }
main hr {
    border: none;
    border-top: 2px solid #eee;
    margin-bottom: 20px;
    margin: 26px 60px 30px;
}
main ul { margin-left: 20px; }
main li { margin-bottom: 10px; }
main li a { --text-font: fvs(wght=0.75); }

.downloads h3 {
    margin-top: 40px;
}
.downloads ul {
    margin-bottom: 30px;
}
"""

script: js = """
//const el = document.getElementById("var");
//const ff = window.getComputedStyle(el).fontFamily.split(",")[0];
//const data = fontdata[ff];

//window.addEventListener("mousemove", function(event) {
//  fvs_text_font(el, event.clientX / window.innerWidth, 1);
//});
"""

info = dict(
    title="ST2",
    description="ST2 is a Blender add-on for doing advanced typography",
    style=style,
    script=script,
    templates=dict(_header=header, _footer=footer, index=index),
    externals={
        "github": "https://github.com/coldtype/st2",
        "coldtype": "https://coldtype.xyz",
        #"youtube": "https://www.youtube.com/channel/UCIRaiGAVFaM-pSErJG1UZFA",
        #"tutorials": "https://coldtype.goodhertz.com/",
        # "q&a forum": "https://github.com/goodhertz/coldtype/discussions",
    },
)


@site(ººsiblingºº(".")
      , port=8008
      , livereload=True
      , info=info
      , fonts={"text-font": dict(regular="MDIO-VF")})
def website(_):
    website.build()


def release(_):
    website.upload("coldtype.xyz/st2", "us-west-1", "personal")