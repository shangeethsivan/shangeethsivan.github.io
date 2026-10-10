#!/usr/bin/env python3
"""Build 16:9 PPTX (and notes) for the 27-slide Shipaton keynote."""

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
DROIDCON_PNG = ROOT / "assets" / "droidcon-india-partner-card.png"
VOLUNTEER_QR = ROOT / "assets" / "kug-volunteer-qr.png"
PRIZE_PNG = ROOT / "assets" / "shipaton-prize-pool.png"
PHONE_JPG = ROOT / "assets" / "shot-luckycharm-phone.jpg"
TALKS_HTML = ROOT.parent / "index.html"
PPTX_PATH = ROOT / "whats-stopping-us-from-building-great-products-and-monetizing-them.pptx"
ASSETS = ROOT / "assets"
YC_URL = "https://www.startupschool.org/"
VOLUNTEER_URL = "https://forms.gle/bpL3rYXffdDWCMK89"

BG = RGBColor(0xF5, 0xF5, 0xF7)
INK = RGBColor(0x1D, 0x1D, 0x1F)
MUTED = RGBColor(0x6E, 0x6E, 0x73)
CHIP = RGBColor(0xE8, 0xE8, 0xED)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x07, 0x07, 0x10)
QUOTE = RGBColor(0xF5, 0xF5, 0xF7)
QUOTE_MUTED = RGBColor(0xA1, 0xA1, 0xA6)
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
    if len(notes) != 27:
        raise SystemExit(f"expected 27 notes, got {len(notes)}")
    indexes = re.findall(r'data-index="(\d+)"', html)
    if indexes != [str(i) for i in range(27)]:
        raise SystemExit(f"expected HTML data-index 0-26, got {indexes}")
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


def add_exist_shots(slide):
    maaa = ASSETS / "shot-maaa.jpg"
    phone = PHONE_JPG
    carrd = ASSETS / "shot-carrd.jpg"
    land_w, land_h = 3.35, 1.88
    phone_h = 2.55
    phone_w = phone_h * (360 / 640)
    gap = 0.22
    total = land_w + gap + phone_w + gap + land_w
    x = (13.333 - total) / 2
    top = 3.35
    phone_top = top - 0.12
    slide.shapes.add_picture(str(maaa), Inches(x), Inches(top), width=Inches(land_w), height=Inches(land_h))
    x += land_w + gap
    slide.shapes.add_picture(str(phone), Inches(x), Inches(phone_top), width=Inches(phone_w), height=Inches(phone_h))
    x += phone_w + gap
    slide.shapes.add_picture(str(carrd), Inches(x), Inches(top), width=Inches(land_w), height=Inches(land_h))


def growth_cards(slide):
    cards = [
        ("Ads", "Google Ads. Meta ads. Apple Search Ads."),
        ("Experiments", "PostHog experiments. GrowthBook. Firebase A/B Testing."),
        ("The stream", "Events you already track. A flag ships a variant. Keep the winner."),
    ]
    w, h, gap = 3.55, 2.05, 0.22
    total = 3 * w + 2 * gap
    x = (13.333 - total) / 2
    top = 3.8
    for title, body in cards:
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(top), Inches(w), Inches(h))
        shape_fill(sh, WHITE)
        add_textbox(slide, Inches(x + 0.15), Inches(top + 0.28), Inches(w - 0.3), Inches(0.45), title, 18, INK, True)
        add_textbox(slide, Inches(x + 0.18), Inches(top + 0.85), Inches(w - 0.36), Inches(1.25), body, 14, MUTED, False)
        x += w + gap


def fund_cards(slide):
    cards = [
        ("Creedom", "AI for creators. ₹1.9 crore deployed."),
        ("GrooveBook", "Photo app. Acquired for $14.5M."),
        ("Scholly", "Scholarship app. Shark Tank, later acquired."),
    ]
    w, h, gap = 3.55, 2.15, 0.22
    total = 3 * w + 2 * gap
    x = (13.333 - total) / 2
    top = 3.55
    for title, body in cards:
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(top), Inches(w), Inches(h))
        shape_fill(sh, WHITE)
        add_textbox(slide, Inches(x + 0.15), Inches(top + 0.35), Inches(w - 0.3), Inches(0.55), title, 20, INK, True)
        add_textbox(slide, Inches(x + 0.18), Inches(top + 1.0), Inches(w - 0.36), Inches(0.85), body, 14, MUTED, False)
        x += w + gap


def provider_lines(slide):
    lines = [
        "Razorpay",
        "Stripe, where available",
        "RevenueCat — mobile subscriptions",
        "Google Pay — wallet, including UPI",
        "Apple Pay — wallet, where available",
    ]
    top = 3.05
    for text in lines:
        add_textbox(slide, Inches(0.7), Inches(top), Inches(11.9), Inches(0.48), text, 22, INK, True)
        top += 0.55


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
    title_sub(s, "You don't need a big team.", "Or months. Or an ad budget.", 0.55, 32)
    add_shots(s, ["supermeme", "droidclaw"], 3.55)
    chips(s, ["Super Meme", "DroidClaw"], 6.35)

    s = add()
    title_sub(s, "You don't need the next Instagram.", "One problem. A few people.", 1.7, 34)
    chips(s, ["Puzzle game", "Resume formatter", "Invoice reminders", "CI dashboard"], 5.55)

    s = add()
    title_sub(s, "These already exist.", "One job. A real price.", 0.45, 32)
    add_exist_shots(s)
    chips(s, ["Maaa", "Lucky Charm", "Carrd"], 6.35)

    s = add()
    title_sub(s, "You don't have to invent it.", "A better version is enough.", 0.55, 32)
    add_shots(s, ["dunsocial"], 3.35, 2.35)

    s = add()
    title_sub(s, "One job. People know these.", "A launcher. An editor. A store.", 0.45, 32)
    add_shots(s, ["raycast", "photopea", "gumroad"], 3.45, 1.95)

    s = add()
    title_sub(s, "You don't need Shark Tank.", "We have Startup Singam.", 0.55, 32)
    fund_cards(s)

    s = add()
    title_sub(s, "Start with the product.", "A game, a charm, or a tiny app.", 1.15)
    graphic_product(s)

    s = add()
    title_sub(s, "Pick one.", "Any of these is fine.", 0.45, 34)
    provider_lines(s)

    s = add()
    title_sub(s, "Then take payment.", "One price. One checkout.", 1.15)
    graphic_checkout(s)
    chips(s, ["₹99–₹499", "₹199/month"], 6.35)

    s = add()
    title_sub(s, "Then watch what they do.", "One analytics tool is enough.", 0.45, 32)
    graphic_chart(s)
    chips(
        s,
        [
            "PostHog",
            "Google Analytics",
            "Plausible",
            "Firebase Analytics",
            "Crashlytics",
            "Performance Monitoring",
        ],
        5.85,
    )
    add_textbox(
        s,
        Inches(0.7),
        Inches(6.45),
        Inches(11.9),
        Inches(0.5),
        "Most of these Firebase products are free.",
        16,
        MUTED,
        False,
    )

    s = add()
    title_sub(s, "Growth is a system you can learn.", "Ads, experiments, and the event stream.", 0.28, 28)
    add_textbox(
        s,
        Inches(0.7),
        Inches(2.72),
        Inches(11.9),
        Inches(0.45),
        "Grow the product first. Then revenue, like ads.",
        18,
        INK,
        True,
    )
    add_textbox(
        s,
        Inches(0.7),
        Inches(3.18),
        Inches(11.9),
        Inches(0.45),
        "Run ads to sell the product. Don't put ads inside it.",
        18,
        INK,
        True,
    )
    growth_cards(s)

    s = add()
    title_sub(s, "Then give them a place to talk.", "Discord is enough.", 1.25, 32)
    graphic_chat(s)
    chips(s, ["Discord", "email", "GitHub Discussions"], 6.35)

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
    add_textbox(s, Inches(0.7), Inches(0.7), Inches(11.9), Inches(1.15), "Take Startup School.", 36, INK, True)
    add_textbox(s, Inches(0.7), Inches(1.9), Inches(11.9), Inches(0.55), "Free. Online. From YC.", 22, MUTED, False)
    s.shapes.add_picture(str(YC_QR), Inches(4.55), Inches(2.55), width=Inches(4.2), height=Inches(4.2))

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

    s = add()
    title_sub(s, "Just follow these for now.", "Don't get overwhelmed.", 1.7, 34)
    chips(s, ["X", "Product Hunt", "Startup School"], 5.55)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, DARK)
    contain_picture(s, KUG_JPG, 2560, 1440)
    slides.append(s)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, DARK)
    contain_picture(s, DROIDCON_PNG, 1200, 628)
    slides.append(s)

    s = add()
    add_textbox(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(1.25), "KUG Chennai Volunteer Interest Form", 30, INK, True)
    s.shapes.add_picture(str(VOLUNTEER_QR), Inches(4.35), Inches(1.95), width=Inches(4.6), height=Inches(4.6))

    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, DARK)
    s.shapes.add_picture(str(PRIZE_PNG), Inches(0.35), Inches(0.45), width=Inches(6.6), height=Inches(6.6))
    add_textbox(
        s,
        Inches(7.15),
        Inches(1.15),
        Inches(5.7),
        Inches(2.35),
        "The people who are crazy enough to think they can change the world are the ones who do.",
        22,
        QUOTE,
        True,
        align=PP_ALIGN.LEFT,
    )
    add_textbox(s, Inches(7.15), Inches(3.55), Inches(5.7), Inches(0.4), "Steve Jobs", 14, QUOTE_MUTED, True, align=PP_ALIGN.LEFT)
    add_textbox(
        s,
        Inches(7.15),
        Inches(4.15),
        Inches(5.7),
        Inches(2.3),
        "Today's prize pool is this. Nothing else is stopping you from a $1 billion company very soon. Think of the next $1 billion as your next hackathon-winning prize.",
        16,
        QUOTE,
        True,
        align=PP_ALIGN.LEFT,
    )
    slides.append(s)

    if len(prs.slides) != 27:
        raise SystemExit(f"expected 27 pptx slides, got {len(prs.slides)}")
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
    if SHEET_URL not in notes[19]["text"]:
        raise SystemExit("sheet URL missing from sheet notes")
    if YC_URL not in notes[18]["text"]:
        raise SystemExit("Startup School URL missing from Startup School notes")
    if VOLUNTEER_URL not in notes[25]["text"]:
        raise SystemExit("volunteer form URL missing from volunteer notes")
    checkout = notes[9]["text"]
    checkout_slide = " ".join(shape.text_frame.text for shape in slides[9].shapes if shape.has_text_frame)
    if "Pick one." not in checkout_slide:
        raise SystemExit("checkout headline missing Pick one.")
    if "Any of these is fine." not in checkout_slide:
        raise SystemExit("checkout subline missing Any of these is fine.")
    if re.search(r"\brequired\b", checkout_slide, re.I):
        raise SystemExit("checkout slide still says required")
    if re.search(r"none of these is required|none of the five is required|none is required", checkout, re.I):
        raise SystemExit("checkout notes still say none is required")
    if re.search(r"none of these is required|none of the five is required|none is required", notes[9]["html"], re.I):
        raise SystemExit("checkout html notes still say none is required")
    if "You do not need all five" not in checkout:
        raise SystemExit("checkout notes must say you do not need all five")
    if "The next slide is one price and that checkout" not in checkout:
        raise SystemExit("checkout notes must point at the next slide")
    for name in ("Razorpay", "Stripe", "RevenueCat", "Google Pay", "Apple Pay"):
        if name not in checkout:
            raise SystemExit(f"{name} missing from checkout notes")
        if name.split()[0] not in checkout_slide and name not in checkout_slide:
            raise SystemExit(f"{name} missing from checkout slide")
    if "developers.google.com/pay" not in checkout or "developer.apple.com/apple-pay" not in checkout:
        raise SystemExit("Google Pay or Apple Pay source missing from checkout notes")
    analytics = notes[11]["text"]
    for name in ("PostHog", "Google Analytics", "Plausible", "Firebase Analytics", "Crashlytics", "Performance Monitoring"):
        if name not in analytics:
            raise SystemExit(f"{name} missing from analytics notes")
    if "firebase.google.com/pricing" not in analytics:
        raise SystemExit("Firebase pricing source missing from analytics notes")
    if "Do not say all of Firebase is free" not in analytics:
        raise SystemExit("Firebase free-vs-paid caveat missing from analytics notes")
    if "Firestore" not in analytics:
        raise SystemExit("Firestore paid caveat missing from analytics notes")
    growth = notes[12]["text"]
    for name in ("Google Ads", "Meta ads", "Apple Search Ads", "PostHog experiments", "GrowthBook", "Firebase A/B Testing"):
        if name not in growth:
            raise SystemExit(f"{name} missing from growth notes")
    growth_slide = " ".join(shape.text_frame.text for shape in slides[12].shapes if shape.has_text_frame)
    if "Grow the product first. Then revenue, like ads." not in growth_slide:
        raise SystemExit("growth-first line missing from the growth slide")
    if "Run ads to sell the product. Don't put ads inside it." not in growth_slide:
        raise SystemExit("sell-the-product ads line missing from the growth slide")
    if "Do not skip the earlier payment slides" not in notes[12]["text"]:
        raise SystemExit("growth notes must keep the payment slides")
    if "Customer checkout and ad revenue are different" not in notes[12]["text"]:
        raise SystemExit("growth notes must distinguish checkout from ads")
    if "reaching buyers" not in notes[12]["text"] or "bloatware" not in notes[12]["text"]:
        raise SystemExit("growth notes must say ads sell the product, not sit inside it")
    if "Google Optimize" in growth_slide:
        raise SystemExit("Google Optimize must not appear on the growth slide")
    if "Kafka" in growth_slide:
        raise SystemExit("Kafka must not appear on the growth slide")
    follow = notes[22]["text"]
    for name in ("X", "Product Hunt", "Startup School"):
        if name not in follow:
            raise SystemExit(f"{name} missing from follow notes")
    follow_slide = " ".join(shape.text_frame.text for shape in slides[22].shapes if shape.has_text_frame)
    if "LinkedIn" in follow_slide or "Reddit" in follow_slide or "YouTube" in follow_slide:
        raise SystemExit("follow slide named extra networks")
    if any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[22].shapes):
        raise SystemExit("follow slide must not have a QR")
    thursday = " ".join(shape.text_frame.text for shape in slides[20].shapes if shape.has_text_frame)
    if re.search(r"\b20\d{2}\b|\bOct|\bOctober\b|\b\d{1,2}/\d{1,2}\b", thursday):
        raise SystemExit(f"Thursday slide printed a calendar date: {thursday!r}")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[0].shapes):
        raise SystemExit("slide 1 missing title card")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[4].shapes):
        raise SystemExit("slide 5 missing product shots")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[18].shapes):
        raise SystemExit("slide 19 missing Startup School QR")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[19].shapes):
        raise SystemExit("slide 20 missing sheet QR")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[23].shapes):
        raise SystemExit("slide 24 missing KUG banner")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[24].shapes):
        raise SystemExit("slide 25 missing DroidCon card")
    droidcon_text = " ".join(shape.text_frame.text for shape in slides[24].shapes if shape.has_text_frame)
    if droidcon_text.strip():
        raise SystemExit(f"DroidCon slide must have no title overlay: {droidcon_text!r}")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[25].shapes):
        raise SystemExit("slide 26 missing volunteer QR")
    volunteer_slide = " ".join(shape.text_frame.text for shape in slides[25].shapes if shape.has_text_frame)
    if "KUG Chennai Volunteer Interest Form" not in volunteer_slide:
        raise SystemExit("volunteer slide missing form title")
    jobs_slide = " ".join(shape.text_frame.text for shape in slides[26].shapes if shape.has_text_frame)
    if "Steve Jobs" not in jobs_slide:
        raise SystemExit("Jobs quote must stay last")
    if "The people who are crazy enough to think they can change the world are the ones who do." not in jobs_slide:
        raise SystemExit("Jobs quote missing from the last slide")
    if "Today's prize pool is this." not in jobs_slide:
        raise SystemExit("billion line missing from the last slide")
    if "₹12,000" in jobs_slide or "12000" in jobs_slide:
        raise SystemExit("do not retype the prize-pool number as a second headline")
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slides[26].shapes):
        raise SystemExit("last slide missing prize-pool poster")
    if "₹12,000 is today's prize pool" not in notes[26]["text"]:
        raise SystemExit("last-slide notes must name today's prize pool as printed")
    if "Do not split it" not in notes[26]["text"] or "promise the billion" not in notes[26]["text"]:
        raise SystemExit("last-slide notes must not promise the billion")
    if notes[18]["title"] != "Take Startup School.":
        raise SystemExit("Startup School must sit immediately after Build anything")
    if notes[26]["title"] != "Steve Jobs":
        raise SystemExit("Jobs notes must stay last")
    talks = TALKS_HTML.read_text(encoding="utf-8")
    if "What's Stopping Us from Shipping Great Products and Monetizing Them?" not in talks:
        raise SystemExit("talks card title changed")
    if "whats-stopping-us-from-building-great-products-and-monetizing-them.pptx?v=31" not in talks:
        raise SystemExit("PPTX download missing ?v=31")
    if "whats-stopping-us-from-building-great-products-and-monetizing-them.pdf?v=31" not in talks:
        raise SystemExit("PDF download missing ?v=31")
    prs.save(PPTX_PATH)
    print(f"wrote {PPTX_PATH} ({len(prs.slides)} slides)")


def main() -> None:
    notes = notes_from_html()
    shots = [
        ASSETS / f"shot-{name}.jpg"
        for name in ("supermeme", "droidclaw", "maaa", "carrd", "dunsocial", "raycast", "photopea", "gumroad")
    ]
    for path in (KUG_JPG, QR_PNG, TITLE_PNG, YC_QR, DROIDCON_PNG, VOLUNTEER_QR, PRIZE_PNG, PHONE_JPG, *shots):
        if not path.exists():
            raise SystemExit(f"missing {path}")
    title = Image.open(TITLE_PNG)
    if title.size != (3840, 2160):
        raise SystemExit(f"title card size {title.size}, expected 3840x2160")
    kug = Image.open(KUG_JPG)
    if kug.size != (2560, 1440):
        raise SystemExit(f"kug size {kug.size}, expected 2560x1440")
    droidcon = Image.open(DROIDCON_PNG)
    if droidcon.size != (1200, 628):
        raise SystemExit(f"droidcon size {droidcon.size}, expected 1200x628")
    prize = Image.open(PRIZE_PNG)
    if prize.size != (2160, 2160):
        raise SystemExit(f"prize poster size {prize.size}, expected 2160x2160")
    phone = Image.open(PHONE_JPG)
    if phone.size != (360, 640):
        raise SystemExit(f"lucky charm phone size {phone.size}, expected 360x640")
    build_pptx(notes)


if __name__ == "__main__":
    main()
