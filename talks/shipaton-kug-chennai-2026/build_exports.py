#!/usr/bin/env python3
"""Build editable 16:9 PPTX and a 10-page PDF for the Shipaton keynote."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
BANNER_WEBP = ROOT / "assets" / "devfest-chennai-2026-banner.webp"
PPTX_PATH = ROOT / "shipaton-kug-chennai-2026.pptx"
PDF_PATH = ROOT / "shipaton-kug-chennai-2026.pdf"

BG = RGBColor(0x07, 0x07, 0x10)
WHITE = RGBColor(0xF7, 0xF8, 0xFF)
MUTED = RGBColor(0xC9, 0xD0, 0xEE)
CYAN = RGBColor(0x5C, 0xE1, 0xFF)
VIOLET = RGBColor(0xB7, 0x94, 0xFF)
VIOLET_DEEP = RGBColor(0x7C, 0x3A, 0xED)
GOLD = RGBColor(0xFF, 0xD2, 0x7A)
CARD = RGBColor(0x12, 0x14, 0x28)


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
    return notes


def set_run(run, text, size, color, bold=False, name="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = name


def add_textbox(slide, l, t, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT, name="Calibri"):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    set_run(run, text, size, color, bold, name)
    return box


def text_frame_set(tf, lines, size, color, bold=False, align=PP_ALIGN.LEFT):
    tf.word_wrap = True
    tf.clear()
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        run = p.add_run()
        set_run(run, line, size, color, bold)


def shape_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def card(slide, l, t, w, h, fill=CARD):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shape_fill(sh, fill)
    sh.line.color.rgb = RGBColor(0x2A, 0x30, 0x55)
    return sh


def paint_bg(slide, color=BG):
    fill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    shape_fill(fill, color)
    spTree = slide.shapes._spTree
    sp = fill._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def kicker(slide, text):
    add_textbox(slide, Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.35), text, 12, CYAN, True, name="Consolas")


def headline(slide, text, top=0.6, size=36, width=12.2, height=1.35):
    add_textbox(slide, Inches(0.55), Inches(top), Inches(width), Inches(height), text, size, WHITE, True)


def add_notes(slide, text):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


def slide1(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "KUG CHENNAI  ·  SHIPATON — ROAD TO DEVFEST, KOTLIN EDITION")
    headline(s, "What's Stopping Us from Shipping Great Products and Monetizing Them?", 0.7, 34, 7.4, 2.6)
    add_textbox(s, Inches(0.55), Inches(3.45), Inches(7.3), Inches(0.9), "We know how to build. But do we know how to sell?", 22, WHITE)
    add_textbox(s, Inches(0.55), Inches(4.4), Inches(7.3), Inches(1.1), "Vibe coding is easy. Getting someone to pay takes resilience.", 18, CYAN, True)
    dead = ["Puzzle Drop", "InvoiceBot", "FitTrack", "QuizNight", "LogLens", "ResumeFix", "HabitKit", "DashLite"]
    for i, name in enumerate(dead):
        col, row = i % 3, i // 3
        if row == 1 and col == 1:
            continue
        x = Inches(8.15 + col * 1.6)
        y = Inches(1.15 + row * 1.55)
        c = card(s, x, y, Inches(1.48), Inches(1.38), RGBColor(0x16, 0x18, 0x2C))
        add_textbox(s, x, y + Inches(0.35), Inches(1.48), Inches(0.7), name, 11, MUTED, True, PP_ALIGN.CENTER)
    alive = card(s, Inches(9.75), Inches(2.7), Inches(1.48), Inches(1.38), RGBColor(0x0A, 0x2A, 0x36))
    add_textbox(s, Inches(9.75), Inches(2.95), Inches(1.48), Inches(0.9), "TinyInvoice\nlive", 12, CYAN, True, PP_ALIGN.CENTER)
    add_textbox(s, Inches(8.15), Inches(6.35), Inches(4.7), Inches(0.4), "→ paying customers", 14, CYAN, True)
    return s


def slide2(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "SMALL PRODUCTS CAN BECOME REAL BUSINESSES")
    headline(s, "You don't need the next Instagram.", 0.62, 36, 12.2, 0.85)
    add_textbox(s, Inches(0.55), Inches(1.45), Inches(12.2), Inches(0.4), "Even a tiny utility solving one meaningful problem can become a sellable product.", 16, CYAN)
    cols = [
        ("Mini Games", "Daily puzzle · word guess\nmultiplayer quiz · browser", "Paid levels, cosmetics, ads"),
        ("Mini Apps", "Supermeme.ai · DroidClaw\nresume · PDF · expense", "One-time, credits, subs"),
        ("Micro-SaaS", "Invoice reminders · scheduling\ninventory · booking · dashboards", "Monthly, usage, licenses"),
        ("Developer Tools", "Android perf · CI/CD\nAPI tests · log analysis", "Hosted, team, one-time"),
    ]
    for i, (title, body, money) in enumerate(cols):
        x = Inches(0.5 + i * 3.2)
        card(s, x, Inches(2.05), Inches(3.0), Inches(4.7))
        add_textbox(s, x + Inches(0.15), Inches(2.2), Inches(2.7), Inches(0.6), title, 20, WHITE, True)
        add_textbox(s, x + Inches(0.15), Inches(2.9), Inches(2.7), Inches(2.2), body, 14, MUTED)
        add_textbox(s, x + Inches(0.15), Inches(5.5), Inches(2.7), Inches(1.0), money, 13, CYAN, True)
    return s


def slide3(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "START MONETIZING, NOT JUST CODING")
    headline(s, "Your first paying customer matters more than another unfinished feature.", 0.58, 28, 12.2, 1.15)
    stages = ["Idea", "MVP", "Real user", "Payment", "Feedback", "Better"]
    for i, name in enumerate(stages):
        x = Inches(0.45 + i * 2.15)
        card(s, x, Inches(1.95), Inches(2.0), Inches(1.15), RGBColor(0x10, 0x1A, 0x2C))
        add_textbox(s, x, Inches(2.2), Inches(2.0), Inches(0.7), name, 16, WHITE, True, PP_ALIGN.CENTER)
    chips = ["₹99–₹499 one-time", "₹199/month", "Freemium", "Credits", "Team plans", "Preorders", "Memberships"]
    for i, chip in enumerate(chips):
        x = Inches(0.45 + i * 1.83)
        c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.35), Inches(1.72), Inches(0.42))
        shape_fill(c, RGBColor(0x2A, 0x18, 0x4A))
        add_textbox(s, x, Inches(3.38), Inches(1.72), Inches(0.38), chip, 10, WHITE, True, PP_ALIGN.CENTER)
    for i, label in enumerate(["Landing", "Pricing", "Checkout", "Confirmation"]):
        x = Inches(0.45 + i * 3.2)
        card(s, x, Inches(4.05), Inches(3.0), Inches(2.7))
        add_textbox(s, x + Inches(0.15), Inches(4.2), Inches(2.7), Inches(0.4), f"0{i+1}  {label}", 12, CYAN, True)
        add_textbox(
            s,
            x + Inches(0.15),
            Inches(4.7),
            Inches(2.7),
            Inches(1.6),
            ["Problem + price", "Pick a plan", "Razorpay / Stripe / IAP", "Receipt + access"][i],
            16,
            WHITE,
            True,
        )
    return s


def slide4(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "SHIP, TRACK, LEARN, REPEAT")
    headline(s, "A launch without feedback is just a deployment.", 0.58, 32, 12.2, 1.0)
    loop = ["Launch", "Analytics", "Feedback", "Improve", "Retention", "Revenue"]
    for i, name in enumerate(loop):
        x = Inches(0.45 + (i % 3) * 2.15)
        y = Inches(1.85 + (i // 3) * 1.15)
        card(s, x, y, Inches(2.0), Inches(0.95), RGBColor(0x10, 0x1A, 0x2C))
        add_textbox(s, x, y + Inches(0.25), Inches(2.0), Inches(0.5), name, 16, WHITE, True, PP_ALIGN.CENTER)
    boxes = [
        ("Analytics", "PostHog · Firebase Analytics · Mixpanel · Plausible"),
        ("Support", "Discord · GitHub Discussions · email · forms"),
        ("Distribution", "X · LinkedIn · Reddit · Product Hunt · YouTube · Instagram · SEO"),
        ("Quality", "Sentry · Firebase Crashlytics · user-reported issues"),
    ]
    for i, (title, body) in enumerate(boxes):
        y = Inches(1.85 + i * 1.2)
        card(s, Inches(7.0), y, Inches(5.8), Inches(1.1))
        add_textbox(s, Inches(7.15), y + Inches(0.08), Inches(5.5), Inches(0.35), title, 13, CYAN, True)
        add_textbox(s, Inches(7.15), y + Inches(0.42), Inches(5.5), Inches(0.55), body, 13, WHITE)
    add_textbox(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.4), "Nobody needs every tool. Shipping starts the loop.", 16, CYAN, True)
    return s


def slide5(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "YOUR SIMPLEST PATH TO REVENUE")
    headline(s, "Can you earn your first ₹1,000?", 0.55, 36, 12.2, 0.8)
    add_textbox(s, Inches(0.55), Inches(1.4), Inches(12.2), Inches(0.85), "5  ×  ₹199  =  ₹995", 44, CYAN, True)
    add_textbox(s, Inches(0.55), Inches(2.25), Inches(12.2), Inches(0.4), "Illustrative gross revenue — before taxes and fees. Payment ≠ product-market fit.", 14, MUTED)
    steps = [
        "Identify one painful problem",
        "Build the smallest useful solution",
        "Landing page + pricing",
        "Appropriate payment method",
        "Share with potential users",
        "Measure and collect feedback",
        "Improve from real behavior",
    ]
    for i, step in enumerate(steps):
        x = Inches(0.4 + i * 1.84)
        card(s, x, Inches(2.8), Inches(1.74), Inches(2.55))
        add_textbox(s, x + Inches(0.08), Inches(2.95), Inches(1.58), Inches(0.35), f"0{i+1}", 12, CYAN, True)
        add_textbox(s, x + Inches(0.08), Inches(3.35), Inches(1.58), Inches(1.8), step, 13, WHITE, True)
    examples = [("₹199", "browser extension"), ("₹299", "mobile utility"), ("₹499/mo", "small-business tool"), ("Paid pack", "mini-game levels")]
    for i, (price, label) in enumerate(examples):
        x = Inches(0.45 + i * 3.2)
        card(s, x, Inches(5.55), Inches(3.0), Inches(1.35), RGBColor(0x0A, 0x2A, 0x36))
        add_textbox(s, x + Inches(0.15), Inches(5.65), Inches(2.7), Inches(0.45), price, 18, CYAN, True)
        add_textbox(s, x + Inches(0.15), Inches(6.15), Inches(2.7), Inches(0.5), label, 14, WHITE)
    return s


def slide6(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "THE SHIPATON CHALLENGE")
    headline(s, "BUILD ANYTHING. SHIP SOMETHING.", 0.58, 40, 12.2, 0.9)
    add_textbox(s, Inches(0.55), Inches(1.5), Inches(12.2), Inches(0.5), "Solo or team? We don't care.", 24, CYAN, True)
    tiles = ["Mini game", "Mobile app", "Web product", "AI tool", "Micro-SaaS", "Dev tool"]
    for i, name in enumerate(tiles):
        x = Inches(0.45 + (i % 3) * 2.5)
        y = Inches(2.2 + (i // 3) * 2.15)
        card(s, x, y, Inches(2.35), Inches(1.95), RGBColor(0x16, 0x12, 0x30))
        add_textbox(s, x, y + Inches(0.7), Inches(2.35), Inches(0.6), name, 16, WHITE, True, PP_ALIGN.CENTER)
    rules = [
        "Individuals and teams are both welcome.",
        "Existing products and brand-new ideas.",
        "Any suitable stack. Any policy-compliant payment provider.",
        "RevenueCat is a collaborator — not a requirement.",
        "A workable monetization model counts. Big revenue this week is not required.",
    ]
    for i, rule in enumerate(rules):
        y = Inches(2.2 + i * 0.9)
        card(s, Inches(8.0), y, Inches(4.85), Inches(0.8))
        add_textbox(s, Inches(8.15), y + Inches(0.18), Inches(4.55), Inches(0.5), rule, 13, WHITE)
    return s


def slide7(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "SUBMISSION + REVIEW")
    headline(s, "One shared sheet. One place to track your progress.", 0.55, 30, 12.2, 0.85)
    headers = ["Product", "Team", "Category", "URL", "₹ model", "Pay", "Review", "Thu ready"]
    row = ["TinyInvoice", "Solo", "Micro-SaaS", "example.com", "₹199/mo", "Live", "Review Ready", "Yes"]
    for i, h in enumerate(headers):
        x = Inches(0.4 + i * 1.22)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.55), Inches(1.18), Inches(0.42))
        shape_fill(bar, RGBColor(0x18, 0x80, 0x38))
        add_textbox(s, x, Inches(1.58), Inches(1.18), Inches(0.38), h, 9, WHITE, True, PP_ALIGN.CENTER)
        cell = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.97), Inches(1.18), Inches(0.5))
        shape_fill(cell, RGBColor(0xF4, 0xF6, 0xFB))
        add_textbox(s, x, Inches(2.05), Inches(1.18), Inches(0.38), row[i], 9, RGBColor(0x1B, 0x24, 0x33), True, PP_ALIGN.CENTER)
    add_textbox(
        s,
        Inches(0.45),
        Inches(2.65),
        Inches(12.3),
        Inches(0.7),
        "Also: Repository URL · Payment Integration (Live / Test / Planned) · Deployment Status · Notes",
        13,
        MUTED,
    )
    flow = [
        "1. Fill the shared sheet.",
        "2. Update progress and product URLs.",
        "3. You set Review Status → Review Ready.",
        "4. Organizers review only those rows.",
        "5. Organizers record the outcome.",
        "Review Ready is your signal, not approval.",
        "Sheet: SHEET_LINK_PLACEHOLDER",
    ]
    for i, line in enumerate(flow):
        y = Inches(3.35 + i * 0.5)
        add_textbox(s, Inches(0.55), y, Inches(12.2), Inches(0.45), line, 16, WHITE if i < 6 else GOLD, True)
    return s


def slide8(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "THE PRODUCTION-READY DEADLINE")
    headline(s, "Thursday is your shipping deadline.", 0.55, 36, 12.2, 0.8)
    days = [
        ("Challenge week", "Build", "Start new or improve what you have."),
        ("Anytime", "Review Ready", "You ask organizers to look."),
        ("Deadline", "Thursday", "Deployed and production-ready."),
        ("After", "Reviewed", "Organizers score execution."),
    ]
    for i, (k, title, body) in enumerate(days):
        x = Inches(0.4 + i * 3.22)
        fill = RGBColor(0x0A, 0x2A, 0x36) if title == "Thursday" else CARD
        card(s, x, Inches(1.55), Inches(3.05), Inches(2.15), fill)
        add_textbox(s, x + Inches(0.15), Inches(1.65), Inches(2.75), Inches(0.3), k.upper(), 11, CYAN, True)
        add_textbox(s, x + Inches(0.15), Inches(1.95), Inches(2.75), Inches(0.5), title, 20, WHITE, True)
        add_textbox(s, x + Inches(0.15), Inches(2.5), Inches(2.75), Inches(0.95), body, 13, MUTED)
    card(s, Inches(0.4), Inches(3.9), Inches(6.2), Inches(1.45))
    add_textbox(s, Inches(0.6), Inches(4.0), Inches(5.9), Inches(0.4), "Review Ready", 18, CYAN, True)
    add_textbox(s, Inches(0.6), Inches(4.45), Inches(5.9), Inches(0.7), "You want organizers to review. Participant-controlled. Not the same as shipped.", 14, WHITE)
    card(s, Inches(6.8), Inches(3.9), Inches(6.1), Inches(1.45))
    add_textbox(s, Inches(7.0), Inches(4.0), Inches(5.8), Inches(0.4), "Production Ready by Thursday", 18, CYAN, True)
    add_textbox(s, Inches(7.0), Inches(4.45), Inches(5.8), Inches(0.7), "Deployed and usable. Extra prize eligibility — not an automatic win.", 14, WHITE)
    checks = [
        "Working production URL or accessible release",
        "Core functionality works",
        "Usable onboarding",
        "No critical blockers",
        "Clear monetization approach",
        "Payment flow functioning when applicable",
        "Basic analytics or feedback collection",
        "Enough information for organizers to test",
    ]
    for i, item in enumerate(checks):
        x = Inches(0.5 + (i % 2) * 6.4)
        y = Inches(5.5 + (i // 2) * 0.42)
        add_textbox(s, x, y, Inches(6.2), Inches(0.4), "▸  " + item, 13, WHITE)
    return s


def slide9(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s)
    kicker(s, "TICKETS, PRIZES, RECOGNITION")
    headline(s, "SHIP IT. GET REVIEWED. WIN BIG.", 0.55, 36, 12.2, 0.8)
    card(s, Inches(0.45), Inches(1.55), Inches(5.5), Inches(3.55), RGBColor(0x1A, 0x16, 0x22))
    add_textbox(s, Inches(0.7), Inches(1.75), Inches(5.1), Inches(0.35), "ADMIT ONE  ·  DEVFEST CHENNAI", 12, GOLD, True)
    add_textbox(s, Inches(0.7), Inches(2.2), Inches(5.1), Inches(1.6), "Selected winners get DevFest tickets", 28, WHITE, True)
    add_textbox(s, Inches(0.7), Inches(4.0), Inches(5.1), Inches(0.7), "Sat 17 Oct 2026 · IITM Research Park", 16, GOLD)
    prizes = [
        "Organizers review products. Selected winners receive DevFest Chennai tickets.",
        "Prizes are also awarded at DevFest itself.",
        "Thursday production-ready teams are considered for an additional prize — eligibility, not a guarantee.",
        "We recognize execution, utility, quality, monetization thinking, and the ability to ship.",
    ]
    for i, line in enumerate(prizes):
        y = Inches(1.55 + i * 0.9)
        card(s, Inches(6.2), y, Inches(6.65), Inches(0.8))
        add_textbox(s, Inches(6.4), y + Inches(0.15), Inches(6.3), Inches(0.55), line, 13, WHITE)
    add_textbox(
        s,
        Inches(0.55),
        Inches(5.3),
        Inches(12.2),
        Inches(0.4),
        "Usefulness  ·  Execution  ·  UX  ·  Monetization potential  ·  Real deployment  ·  Learning",
        14,
        VIOLET,
        True,
    )
    add_textbox(
        s,
        Inches(0.55),
        Inches(5.85),
        Inches(12.2),
        Inches(1.15),
        "Don't just build another side project. Build something people can use, ship it to the world, and see if someone is willing to pay for it.",
        18,
        WHITE,
        True,
    )
    return s


def slide10(prs, banner_png: Path):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    paint_bg(s, BG)
    # 2160x1080 is 2:1; 16:9 slide letterboxes vertically with object-fit contain.
    slide_w = Inches(13.333)
    img_h = Inches(13.333 * 1080 / 2160)
    top = (Inches(7.5) - img_h) / 2
    s.shapes.add_picture(str(banner_png), Inches(0), top, width=slide_w, height=img_h)
    return s


def build_pptx(notes: list[dict]) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    builders = [slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9]
    slides = [fn(prs) for fn in builders]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        Image.open(BANNER_WEBP).save(tmp.name, "PNG")
        banner_png = Path(tmp.name)
    slides.append(slide10(prs, banner_png))
    if len(prs.slides) != 10:
        raise SystemExit(f"expected 10 pptx slides, got {len(prs.slides)}")
    for slide, note in zip(slides, notes):
        add_notes(slide, note["text"])
        tf = slide.notes_slide.notes_text_frame
        if not tf.text.strip():
            raise SystemExit("missing notes on a slide")
    prs.save(PPTX_PATH)
    banner_png.unlink(missing_ok=True)
    print(f"wrote {PPTX_PATH} ({len(prs.slides)} slides)")


def verify_pptx(notes: list[dict]) -> None:
    from pptx import Presentation as P

    prs = P(PPTX_PATH)
    if len(prs.slides) != 10:
        raise SystemExit("PPTX slide count != 10")
    for i, slide in enumerate(prs.slides, 1):
        text = slide.notes_slide.notes_text_frame.text.strip()
        if not text:
            raise SystemExit(f"PPTX slide {i} has empty notes")
        if text != notes[i - 1]["text"]:
            raise SystemExit(f"PPTX notes mismatch on slide {i}")
    # Slide 10 should contain a picture
    pics = [sh for sh in prs.slides[9].shapes if sh.shape_type is not None and sh.has_text_frame is False]
    if not any(getattr(sh, "image", None) for sh in prs.slides[9].shapes if hasattr(sh, "image")):
        # fallback: at least one picture-like shape
        from pptx.enum.shapes import MSO_SHAPE_TYPE

        if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in prs.slides[9].shapes):
            raise SystemExit("slide 10 is missing the banner picture")
    print("PPTX verified: 10 slides, notes on every slide, banner picture on 10")


def main() -> None:
    notes = notes_from_html()
    if not BANNER_WEBP.exists():
        raise SystemExit(f"missing {BANNER_WEBP}")
    im = Image.open(BANNER_WEBP)
    if im.size != (2160, 1080):
        raise SystemExit(f"banner size {im.size}, expected 2160x1080")
    build_pptx(notes)
    verify_pptx(notes)


if __name__ == "__main__":
    main()
