"""PPTX ga kirish animatsiyalari va slayd o'tishlarini qo'shish.

    python animate.py deck.pptx

Obyekt nomi "a<N>_<effekt>_..." bo'lsa, u N-bosqichda paydo bo'ladi (bir bosqichdagilar birga).
Effektlar: fade (so'nish), up (pastdan ko'tarilish), left (chapdan suzish), zoom (kattalashish).
Animatsiyalar slayd ochilishi bilan avtomatik ("oldingisidan keyin") ishga tushadi.
"""
import re
import shutil
import sys
import tempfile
import zipfile

from lxml import etree

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
P = "{%s}" % NS["p"]
NAME_RE = re.compile(r"^a(\d+)_(fade|up|left|zoom)_")
EFFECT_MS = 550
STEP_GAP_MS = 380
PRESET = {"fade": ("10", "0"), "up": ("42", "0"), "left": ("10", "0"), "zoom": ("53", "16")}


class Ids:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return str(self.n)


def set_visible(nid, spid):
    return (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
            f'</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>')


def fade(nid, spid):
    return (f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="{EFFECT_MS}"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>')


def anim(nid, spid, attr, frm, to):
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{nid()}" dur="{EFFECT_MS}" decel="100000" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{frm}"/></p:val></p:tav>'
            f'<p:tav tm="100000"><p:val><p:strVal val="{to}"/></p:val></p:tav></p:tavLst></p:anim>')


def behaviours(kind, nid, spid):
    out = set_visible(nid, spid) + fade(nid, spid)
    if kind == "up":
        out += anim(nid, spid, "ppt_x", "#ppt_x", "#ppt_x") + anim(nid, spid, "ppt_y", "#ppt_y+0.06", "#ppt_y")
    elif kind == "left":
        out += anim(nid, spid, "ppt_x", "#ppt_x-0.06", "#ppt_x") + anim(nid, spid, "ppt_y", "#ppt_y", "#ppt_y")
    elif kind == "zoom":
        out += anim(nid, spid, "ppt_w", "#ppt_w*0.75", "#ppt_w") + anim(nid, spid, "ppt_h", "#ppt_h*0.75", "#ppt_h")
    return out


def build_timing(steps):
    nid = Ids()
    root_id, seq_id, click_id = nid(), nid(), nid()
    pars, t = [], 0
    for step in sorted(steps):
        inner = []
        for i, (spid, kind) in enumerate(steps[step]):
            preset, sub = PRESET[kind]
            node = "afterEffect" if i == 0 else "withEffect"
            cid = nid()
            inner.append(f'<p:par><p:cTn id="{cid}" presetID="{preset}" presetClass="entr" presetSubtype="{sub}" fill="hold" nodeType="{node}">'
                         f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{behaviours(kind, nid, spid)}</p:childTnLst></p:cTn></p:par>')
        pars.append(f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="{t}"/></p:stCondLst>'
                    f'<p:childTnLst>{"".join(inner)}</p:childTnLst></p:cTn></p:par>')
        t += STEP_GAP_MS
    xml = (f'<p:timing xmlns:p="{NS["p"]}"><p:tnLst><p:par><p:cTn id="{root_id}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
           f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
           f'<p:par><p:cTn id="{click_id}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
           f'<p:cond evt="onBegin" delay="0"><p:tn val="{seq_id}"/></p:cond></p:stCondLst>'
           f'<p:childTnLst>{"".join(pars)}</p:childTnLst></p:cTn></p:par>'
           f'</p:childTnLst></p:cTn>'
           f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
           f'</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    return etree.fromstring(xml)


def process_slide(data):
    root = etree.fromstring(data)
    steps = {}
    for c in root.iter("{%s}cNvPr" % NS["p"]):
        m = NAME_RE.match(c.get("name", ""))
        if m:
            steps.setdefault(int(m.group(1)), []).append((c.get("id"), m.group(2)))
    # Slayd o'tishi: silliq so'nish
    for old in root.findall(P + "transition"):
        root.remove(old)
    clr = root.find(P + "clrMapOvr")
    trans = etree.fromstring(f'<p:transition xmlns:p="{NS["p"]}" spd="slow"><p:fade/></p:transition>')
    idx = list(root).index(clr) + 1 if clr is not None else 1
    root.insert(idx, trans)
    if steps and root.find(P + "timing") is None:
        root.insert(idx + 1, build_timing(steps))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), sum(len(v) for v in steps.values())


def main(path):
    tmp = tempfile.mktemp(suffix=".pptx")
    total = 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.is_dir():
                continue
            data = zin.read(item.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
                data, n = process_slide(data)
                total += n
            zout.writestr(item, data)
    shutil.move(tmp, path)
    print(f"animatsiya qo'shildi: {total} ta obyekt")


if __name__ == "__main__":
    main(sys.argv[1])
