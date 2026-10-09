#!/usr/bin/env python3
"""Build 16:9 PPTX (and notes) for the 20-slide Shipaton keynote."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
KUG_JPG = ROOT / "assets" / "kug-chennai-banner.jpg"
TITLE_PNG = ROOT / "assets" / "shipaton-title-card.png"
QR_PNG = ROOT / "assets" / "shipaton-sheet-qr.png"
YC_QR = ROOT / "assets" / "startup-school-qr.png"
PPTX_PATH = ROOT / "shipaton-kug-chennai-2026.pptx"
ASSETS = ROOT / "assets"
YC_URL = "https://www.startupschool.org/"

BG = RGBColor(0xF5, 0xF5, 0xF7)
INK = RGBColor(0x1D, 0x1D, 0x1F)
MUTED = RGBColor(0x6E, 0x6E, 0x73)
CHIP = RGBColor(0xE8, 0xE8, 0xED)
DARK = RGBColor(0x07, 0x07, 0x10)
VIOLET = RGBColor(0x7C, 0x5C, 0xFF)
CYAN = RGBColor(0x1E, 0xC8, 0xE6)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1DZ7OSphlY8llxWisVc_FcLGeu9Psj_fvfxR2F7ohxcM/edit?usp=sharing"


def notes_from_html() -> list[dict]:
    html = HTML.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="speaker-notes">\s*(.*?)\s*</script>',
        html,
        re.S,
    )
    if not match:
        raise SystemExit("speaker-notes JSON island missing")
    notes = json.loads(match.group(1))
    if len(notes) != 20:
        raise SystemExit(f"expected 20 notes, got {len(notes)}")
    blob = html.lower()
    if "microsaas" in blob:
        raise SystemExit("forbidden term found in index.html")
    if "sheet_link_placeholder" in blob:
        raise SystemExit("SHEET_LINK_PLACEHOLDER still present")
    if "learnwithrajesh" in blob:
        raise SystemExit("do not print learnwithrajesh")
    return notes


def set_run(run, text, size, color, bold=False):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Calibri"


def add_textbox(slide, l, t, w, h, text, size, color, bold=False, align=PP_ALIGN.CENTER):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    set_run(run, text, size, color, bold)
    return box


def shape_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def stroke(shape, color, width=2.0):
    shape.fill.background()
    shape.line.color.rgb = color
    shape.line.width = Pt(width)


def paint_bg(slide, color=BG):
    fill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    shape_fill(fill, color)
    spTree = slide.shapes._spTree
    sp = fill._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def chips(slide, items, top=6.2):
    widths = [0.34 + 0.105 * len(item) for item in items]
    total = sum(widths) + 0.18 * (len(items) - 1)
    x = (13.333 - total) / 2
    for item, width in zip(items, widths):
        sh = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(top), Inches(width), Inches(0.42)
        )
        shape_fill(sh, CHIP)
        add_textbox(slide, sh.left, sh.top + Inches(0.04), sh.width, Inches(0.36), item, 12, INK, True)
        x += width + 0.18


def title_sub(slide, title, sub=None, top=1.85, size=36):
    add_textbox(slide, Inches(0.7), Inches(top), Inches(11.9), Inches(1.9), title, size, INK, True)
    if sub:
        add_textbox(slide, Inches(0.7), Inches(top + 1.95), Inches(11.9), Inches(0.85), sub, 22, MUTED, False)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def contain_picture(slide, path, img_w, img_h):
    slide_w = 13.333
    slide_h = 7.5
    aspect = img_w / img_h
    slide_aspect = slide_w / slide_h
    if aspect > slide_aspect:
        w = slide_w
        h = slide_w / aspect
        left = 0
        top = (slide_h - h) / 2
    else:
        h = slide_h
        w = slide_h * aspect
        top = 0
        left = (slide_w - w) / 2
    slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(w), height=Inches(h))


def line(slide, x1, y1, x2, y2, color, width=2.2):
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)


def graphic_product(slide):
    phone = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.15), Inches(4.05), Inches(1.05), Inches(1.55))
    stroke(phone, VIOLET, 2.2)
    screen = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.32), Inches(4.25), Inches(0.71), Inches(0.95))
    stroke(screen, CYAN, 1.8)
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.58), Inches(5.28), Inches(0.18), Inches(0.18))
    shape_fill(dot, VIOLET)
    charm = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(5.15), Inches(4.55), Inches(0.55), Inches(0.55))
    stroke(charm, VIOLET, 2)
    line(slide, 5.42, 4.12, 5.42, 4.55, CYAN, 2)


def graphic_checkout(slide):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.05), Inches(4.15), Inches(3.2), Inches(1.35))
    stroke(card, VIOLET, 2.2)
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.05), Inches(4.15), Inches(3.2), Inches(0.32))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.fill.fore_color.brightness = 0.55
    bar.line.fill.background()
    line(slide, 5.4, 5.05, 6.35, 5.05, CYAN, 2.2)
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.55), Inches(4.72), Inches(0.42), Inches(0.42))
    stroke(ring, VIOLET, 2)


def graphic_chart(slide):
    line(slide, 5.15, 4.15, 5.15, 5.55, VIOLET, 2)
    line(slide, 5.15, 5.55, 8.2, 5.55, VIOLET, 2)
    bars = [(5.4, 5.05, 0.55, CYAN), (6.15, 4.7, 0.85, VIOLET), (6.9, 4.9, 0.65, CYAN), (7.65, 4.4, 1.15, VIOLET)]
    for x, y, h, color in bars:
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(0.38), Inches(h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.fill.fore_color.brightness = 0.35
        bar.line.fill.background()


def graphic_chat(slide):
    left = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.15), Inches(4.15), Inches(1.7), Inches(0.85))
    stroke(left, VIOLET, 2.2)
    right = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.5), Inches(4.85), Inches(1.7), Inches(0.72))
    stroke(right, CYAN, 2.2)
    for i, color in enumerate((CYAN, VIOLET, CYAN)):
        dot = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(5.45 + i * 0.32), Inches(4.45), Inches(0.18), Inches(0.18)
        )
        shape_fill(dot, color)


def add_shots(slide, names, top=3.85, height=2.05):
    paths = [ASSETS / f"shot-{name}.jpg" for name in names]
    n = len(paths)
    gap = 0.18
    w = 3.55 if n >= 3 else (4.4 if n == 2 else 5.4)
    total = n * w + gap * (n - 1)
    x = (13.333 - total) / 2
    for path in paths:
        slide.shapes.add_picture(str(path), Inches(x), Inches(top), width=Inches(w), height=Inches(height))
        x += w + gap


def build_pptx(notes: list[dict]) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slides = []

    def add():
        s = prs.slides.add_slide(prs.slide_layouts[6])
        paint_bg(s)
        slides.append(s)
        return s

    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, DARK)
    contain_picture(s, TITLE_PNG, 3840, 2160)
    slides.append(s)

    s = add()
    title_sub(s, "What's stopping us from getting paid?", "We know how to build.", 1.55, 36)
    chips(s, ["Getting paid takes resilience"], 5.85)

    s = add()
    add_textbox(s, Inches(0.7), Inches(0.7), Inches(11.9), Inches(1.15), "Take Startup School.", 36, INK, True)
    add_textbox(s, Inches(0.7), Inches(1.9), Inches(11.9), Inches(0.55), "Free. Online. From YC.", 22, MUTED, False)
    s.shapes.add_picture(str(YC_QR), Inches(4.55), Inches(2.55), width=Inches(4.2), height=Inches(4.2))

    s = add()
    title_sub(s, "You don't need a big team.", "Or months. Or an ad budget.", 0.55, 32)
    add_shots(s, ["supermeme", "droidclaw"], 3.55)
    chips(s, ["Super Meme", "DroidClaw"], 6.35)

    s = add()
    title_sub(s, "You don't need the next Instagram.", "One problem. A few people.", 1.7, 34)
    chips(s, ["Puzzle game", "Resume formatter", "Invoice reminders", "CI dashboard"], 5.55)

    s = add()
    title_sub(s, "These already exist.", "One job. A real price.", 0.45, 32)
    add_shots(s, ["maaa", "luckycharm", "carrd"], 3.45, 1.95)
    chips(s, ["Maaa", "Lucky Charm", "Carrd"], 6.35)

    s = add()
    title_sub(s, "You don't have to invent it.", "A better version is enough.", 0.55, 32)
    add_shots(s, ["dunsocial"], 3.35, 2.35)

    s = add()
    title_sub(s, "One job. People know these.", "A launcher. An editor. A store.", 0.45, 32)
    add_shots(s, ["raycast", "photopea", "gumroad"], 3.45, 1.95)

    s = add()
    title_sub(s, "Start with the product.", "A game, a charm, or a tiny app.", 1.15)
    graphic_product(s)

    s = add()
    title_sub(s, "Then take payment.", "One price. One checkout.", 1.15)
    graphic_checkout(s)
    chips(s, ["₹99–₹499", "₹199/month"], 6.35)

    s = add()
    title_sub(s, "Then watch what they do.", "One analytics tool is enough.", 1.15)
    graphic_chart(s)
    chips(s, ["PostHog"], 6.35)

    s = add()
    title_sub(s, "Then give them a place to talk.", "Discord is enough.", 1.25, 32)
    graphic_chat(s)

    s = add()
    title_sub(s, "They stay when you solve the next problem.", "Likes are not customers.", 2.05, 30)

    s = add()
    title_sub(s, "Your first paying customer beats another feature.", "Too simple is why it stays in GitHub.", 1.45, 28)

    s = add()
    title_sub(s, "Five people × ₹199.", "Your first ₹1,000.", 1.7, 40)
    chips(s, ["₹199 extension", "₹299 app", "₹499/month", "Level pack"], 6.35)

    s = add()
    title_sub(s, "Build anything. Ship something.", "Solo or team.", 1.95)
    chips(s, ["Game", "App", "Site", "Tool"], 5.95)

    s = add()
    add_textbox(s, Inches(0.7), Inches(0.7), Inches(11.9), Inches(1.25), "One sheet. Set Review Ready.", 34, INK, True)
    s.shapes.add_picture(str(QR_PNG), Inches(4.55), Inches(2.15), width=Inches(4.2), height=Inches(4.2))

    s = add()
    title_sub(s, "Thursday. Make it live.", None, 2.05, 40)
    chips(s, ["Deployed", "Usable", "Payments work"], 5.75)

    s = add()
    add_textbox(s, Inches(0.7), Inches(1.15), Inches(11.9), Inches(1.1), "Ship it. Get reviewed.", 36, INK, True)
    add_textbox(
        s,
        Inches(0.9),
        Inches(2.55),
        Inches(11.5),
        Inches(2.0),
        "We're going to see 10 person billion-dollar companies pretty soon.",
        24,
        INK,
        True,
    )
    add_textbox(s, Inches(0.7), Inches(4.7), Inches(11.9), Inches(0.4), "Sam Altman", 14, MUTED, True)
    chips(s, ["DevFest tickets"], 5.75)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, DARK)
    contain_picture(s, KUG_JPG, 2560, 1440)
    slides.append(s)

    if len(prs.slides) != 20:
        raise SystemExit(f"expected 20 pptx slides, got {len(prs.slides)}")
    for slide, note in zip(slides, notes):
        add_notes(slide, note["text"])
        if "microsaas" in note["text"].lower() or "microsaas" in note["html"].lower():
            raise SystemExit("forbidden term in notes")
        if not slide.notes_slide.notes_text_frame.text.strip():
            raise SystemExit("missing notes")
        if "Tanglish" not in note["html"]:
            raise SystemExit(f"missing Tanglish: {note['title']}")
        if "<a href" not in note["html"]:
            raise SystemExit(f"missing clickable source: {note['title']}")
    if SHEET_URL not in notes[16]["text"]:
        raise SystemExit("sheet URL missing from slide 17 notes")
    if YC_URL not in notes[2]["text"]:
        raise SystemExit("Startup School URL missing from slide 3 notes")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[0].shapes):
        raise SystemExit("slide 1 missing title card")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[2].shapes):
        raise SystemExit("slide 3 missing Startup School QR")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[16].shapes):
        raise SystemExit("slide 17 missing sheet QR")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[19].shapes):
        raise SystemExit("slide 20 missing KUG banner")
    prs.save(PPTX_PATH)
    print(f"wrote {PPTX_PATH} ({len(prs.slides)} slides)")


def main() -> None:
    notes = notes_from_html()
    shots = [
        ASSETS / f"shot-{name}.jpg"
        for name in ("supermeme", "droidclaw", "maaa", "luckycharm", "carrd", "dunsocial", "raycast", "photopea", "gumroad")
    ]
    for path in (KUG_JPG, QR_PNG, TITLE_PNG, YC_QR, *shots):
        if not path.exists():
            raise SystemExit(f"missing {path}")
    title = Image.open(TITLE_PNG)
    if title.size != (3840, 2160):
        raise SystemExit(f"title card size {title.size}, expected 3840x2160")
    kug = Image.open(KUG_JPG)
    if kug.size != (2560, 1440):
        raise SystemExit(f"kug size {kug.size}, expected 2560x1440")
    build_pptx(notes)


if __name__ == "__main__":
    main()
