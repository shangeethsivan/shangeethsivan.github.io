#!/usr/bin/env python3
"""Build 16:9 PPTX (and notes) for the Shipaton Apple-simple keynote."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
BANNER_WEBP = ROOT / "assets" / "devfest-chennai-2026-banner.webp"
QR_PNG = ROOT / "assets" / "shipaton-sheet-qr.png"
PPTX_PATH = ROOT / "shipaton-kug-chennai-2026.pptx"

BG = RGBColor(0xF5, 0xF5, 0xF7)
INK = RGBColor(0x1D, 0x1D, 0x1F)
MUTED = RGBColor(0x6E, 0x6E, 0x73)
CHIP = RGBColor(0xE8, 0xE8, 0xED)
DARK = RGBColor(0x07, 0x07, 0x10)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1DZ7OSphlY8llxWisVc_FcLGeu9Psj_fvfxR2F7ohxcM/edit?usp=sharing"


def notes_from_html() -> list[dict]:
    html = HTML.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="speaker-notes">\s*(.*?)\s*</script>',
        html,
        re.S,
    )
    if not match:
        raise SystemExit("speaker-notes JSON island missing from index.html")
    notes = json.loads(match.group(1))
    if len(notes) != 10:
        raise SystemExit(f"expected 10 notes, got {len(notes)}")
    blob = html.lower()
    if "microsaas" in blob:
        raise SystemExit("forbidden term found in index.html")
    if "sheet_link_placeholder" in blob:
        raise SystemExit("SHEET_LINK_PLACEHOLDER still present")
    return notes


def set_run(run, text, size, color, bold=False, name="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = name


def add_textbox(slide, l, t, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT):
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


def paint_bg(slide, color=BG):
    fill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    shape_fill(fill, color)
    spTree = slide.shapes._spTree
    sp = fill._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def chips(slide, items, top=6.35, left=0.7, align_center=False):
    widths = [0.34 + 0.105 * len(item) for item in items]
    x = left
    if align_center:
        total = sum(widths) + 0.18 * (len(items) - 1)
        x = (13.333 - total) / 2
    for item, width in zip(items, widths):
        sh = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(top), Inches(width), Inches(0.42)
        )
        shape_fill(sh, CHIP)
        add_textbox(slide, sh.left, sh.top + Inches(0.04), sh.width, Inches(0.36), item, 12, INK, True, PP_ALIGN.CENTER)
        x += width + 0.18


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def title_sub(slide, title, sub=None, top=2.15, size=40, center=False):
    align = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    left = Inches(0.85)
    width = Inches(11.6)
    add_textbox(slide, left, Inches(top), width, Inches(2.2), title, size, INK, True, align)
    if sub:
        add_textbox(slide, left, Inches(top + 2.15), width, Inches(1.1), sub, 24, MUTED, False, align)


def build_pptx(notes: list[dict]) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    s1 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s1)
    title_sub(s1, "What's stopping us from getting paid?", "We know how to build.", 1.7, 40, True)
    chips(s1, ["Getting paid takes resilience"], align_center=True)

    s2 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s2)
    title_sub(s2, "You don't need a big team.", "Or months. Or an ad budget.", 1.55, 40)
    chips(s2, ["Super Meme", "DroidClaw"], left=0.85)

    s3 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s3)
    title_sub(s3, "You don't need the next Instagram.", "One problem. A few people.", 1.55, 38, True)
    chips(s3, ["Puzzle game", "Resume formatter", "Invoice reminders", "CI dashboard"], align_center=True)

    s4 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s4)
    title_sub(s4, "Your first paying customer beats another feature.", "Too simple is why it stays in GitHub.", 1.35, 32)
    chips(s4, ["₹99–₹499", "₹199/month", "Freemium"], left=0.85)

    s5 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s5)
    title_sub(s5, "Five people × ₹199.", "Your first ₹1,000.", 1.7, 44, True)
    chips(s5, ["₹199 extension", "₹299 app", "₹499/month", "Level pack"], align_center=True)

    s6 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s6)
    title_sub(s6, "Build anything. Ship something.", "Solo or team.", 1.7, 40, True)
    chips(s6, ["Game", "App", "Site", "Tool"], align_center=True)

    s7 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s7)
    add_textbox(s7, Inches(0.7), Inches(2.2), Inches(6.4), Inches(2.6), "One sheet. Set Review Ready.", 36, INK, True)
    s7.shapes.add_picture(str(QR_PNG), Inches(8.35), Inches(1.55), width=Inches(4.2), height=Inches(4.2))

    s8 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s8)
    title_sub(s8, "Thursday. Make it live.", None, 2.2, 44, True)
    chips(s8, ["Deployed", "Usable", "Payments work"], align_center=True)

    s9 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s9)
    add_textbox(s9, Inches(0.85), Inches(1.15), Inches(11.6), Inches(1.3), "Ship it. Get reviewed.", 40, INK, True)
    add_textbox(
        s9,
        Inches(0.85),
        Inches(2.6),
        Inches(11.4),
        Inches(2.3),
        "We're going to see 10 person billion-dollar companies pretty soon.",
        26,
        INK,
        True,
    )
    add_textbox(s9, Inches(0.85), Inches(5.0), Inches(11.4), Inches(0.4), "Sam Altman", 14, MUTED, True)
    chips(s9, ["DevFest tickets"], left=0.85)

    s10 = prs.slides.add_slide(prs.slide_layouts[6]); paint_bg(s10, DARK)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        Image.open(BANNER_WEBP).save(tmp.name, "PNG")
        banner_png = Path(tmp.name)
    slide_w = Inches(13.333)
    img_h = Inches(13.333 * 1080 / 2160)
    top = (Inches(7.5) - img_h) / 2
    s10.shapes.add_picture(str(banner_png), Inches(0), top, width=slide_w, height=img_h)
    banner_png.unlink(missing_ok=True)

    slides = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]
    if len(prs.slides) != 10:
        raise SystemExit(f"expected 10 pptx slides, got {len(prs.slides)}")
    for slide, note in zip(slides, notes):
        add_notes(slide, note["text"])
        if "microsaas" in note["text"].lower() or "microsaas" in note["html"].lower():
            raise SystemExit("forbidden term in notes")
        if not slide.notes_slide.notes_text_frame.text.strip():
            raise SystemExit("missing notes")
    if SHEET_URL not in notes[6]["text"] or SHEET_URL not in notes[6]["html"]:
        raise SystemExit("sheet URL missing from slide 7 notes")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s7.shapes):
        raise SystemExit("slide 7 missing QR picture")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s10.shapes):
        raise SystemExit("slide 10 missing banner picture")
    prs.save(PPTX_PATH)
    print(f"wrote {PPTX_PATH} ({len(prs.slides)} slides)")


def main() -> None:
    notes = notes_from_html()
    if not BANNER_WEBP.exists():
        raise SystemExit(f"missing {BANNER_WEBP}")
    if not QR_PNG.exists():
        raise SystemExit(f"missing {QR_PNG}")
    im = Image.open(BANNER_WEBP)
    if im.size != (2160, 1080):
        raise SystemExit(f"banner size {im.size}, expected 2160x1080")
    build_pptx(notes)


if __name__ == "__main__":
    main()
