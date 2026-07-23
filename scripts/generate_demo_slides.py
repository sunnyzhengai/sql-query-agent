"""Generate AIVIA Demo Slide Deck.

Run: python3 scripts/generate_demo_slides.py
Output: presentation/aivia_demo.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

# Color palette
NAVY = RGBColor(0x1B, 0x2A, 0x4A)
TEAL = RGBColor(0x00, 0x96, 0x88)
LIGHT_TEAL = RGBColor(0x4D, 0xB6, 0xAC)
ORANGE = RGBColor(0xFF, 0x7A, 0x2F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
MEDIUM_GRAY = RGBColor(0x75, 0x75, 0x75)
RED = RGBColor(0xE5, 0x3E, 0x3E)
GREEN = RGBColor(0x4C, 0xAF, 0x50)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SLIDE_W = Inches(13.333)


def add_bg(slide, color=NAVY):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def text(slide, left, top, width, height, txt, size=18,
         color=WHITE, bold=False, align=PP_ALIGN.LEFT, font="Calibri"):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = txt
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    return box


def multi_text(slide, left, top, width, height, items, size=18, color=WHITE, spacing=8):
    """Add multiple paragraphs with bullet styling."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        if isinstance(item, tuple):
            run_b = p.add_run()
            run_b.text = item[0]
            run_b.font.size = Pt(size)
            run_b.font.color.rgb = color
            run_b.font.bold = True
            run_b.font.name = "Calibri"
            run_r = p.add_run()
            run_r.text = item[1]
            run_r.font.size = Pt(size)
            run_r.font.color.rgb = color
            run_r.font.name = "Calibri"
        else:
            run = p.add_run()
            run.text = item
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = "Calibri"
    return box


def rounded_rect(slide, left, top, width, height, fill_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    return shape


def rect(slide, left, top, width, height, fill_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    return shape


# ============================================================
# SLIDE 1 — The Problem
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY)

# Title area
text(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.8),
     "The Hidden Treasure Problem", size=40, color=WHITE, bold=True)

rect(slide, Inches(0.8), Inches(1.3), Inches(4), Pt(4), fill_color=TEAL)

# Left column — the treasure
text(slide, Inches(0.8), Inches(1.8), Inches(5.5), Inches(0.5),
     "What your organization already has:", size=20, color=TEAL, bold=True)

multi_text(slide, Inches(0.8), Inches(2.5), Inches(5.5), Inches(3.5), [
    ("Thousands", " of SQL-based reports"),
    ("Built by", " highly skilled BI developers"),
    ("Requested by", " clinicians based on real clinical needs"),
    ("Validated", " and in production"),
    ("= Millions of dollars", " of invested business logic"),
], size=19, color=WHITE)

# Right column — the problem
box = rounded_rect(slide, Inches(7.0), Inches(1.8), Inches(5.5), Inches(4.8),
                   fill_color=RGBColor(0x2A, 0x1A, 0x1A))

text(slide, Inches(7.3), Inches(2.0), Inches(5), Inches(0.5),
     "But...", size=22, color=RED, bold=True)

multi_text(slide, Inches(7.3), Inches(2.7), Inches(5), Inches(3.8), [
    ("No governance", " — nobody knows what's in each report"),
    ("No visibility", " into the logic behind each report name"),
    ("Outdated reports", " sitting next to current ones"),
    ("Conflicting duplicates", " — same metric, different numbers"),
    ("Clinicians can't trust", " which number is right"),
    ("Result:", " another report request. Weeks of waiting. More distrust."),
], size=17, color=WHITE)

# Bottom callout
rect(slide, Inches(0), Inches(6.5), SLIDE_W, Inches(1), fill_color=TEAL)
text(slide, Inches(1), Inches(6.6), Inches(11), Inches(0.6),
     "This is the cycle we break.", size=28, color=WHITE, bold=True,
     align=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 2 — The Solution (Architecture)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY)

text(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.8),
     "AIVIA: Turn Technical Debt into Self-Service Intelligence",
     size=36, color=WHITE, bold=True)

rect(slide, Inches(0.8), Inches(1.3), Inches(4), Pt(4), fill_color=TEAL)

text(slide, Inches(0.8), Inches(1.8), Inches(11), Inches(0.6),
     "Take your existing SQL reports and automatically extract the business logic",
     size=20, color=LIGHT_TEAL)

# Pipeline boxes
pipeline = [
    ("SQL Sources", "Stored Procedures\nViews\nScripts", Inches(0.3), MEDIUM_GRAY),
    ("ScriptDom\nParser", "Microsoft's own\nT-SQL engine\n99% accuracy", Inches(3.0), TEAL),
    ("Knowledge\nGraph", "Business Metrics\nLogic Steps\nSource Tables", Inches(5.7), RGBColor(0x26, 0xA6, 0x9A)),
    ("Data Agent", "Ask questions\nin plain English\nGet instant answers", Inches(8.4), RGBColor(0x00, 0x79, 0x6B)),
    ("Purview\nCollibra\nPower BI", "Auto-documented\nAuto-governed\nAlways current", Inches(11.1), ORANGE),
]

for label, desc, left, color in pipeline:
    box = rounded_rect(slide, left, Inches(2.8), Inches(2.2), Inches(2.5), fill_color=color)
    text(slide, left + Inches(0.1), Inches(2.9), Inches(2.0), Inches(0.8),
         label, size=16, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, left + Inches(0.1), Inches(3.7), Inches(2.0), Inches(1.2),
         desc, size=12, color=WHITE, align=PP_ALIGN.CENTER)

# Arrows
for x in [Inches(2.5), Inches(5.2), Inches(7.9), Inches(10.6)]:
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, Inches(3.8), Inches(0.5), Inches(0.3))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = WHITE
    arrow.line.fill.background()

# Bottom stat
rect(slide, Inches(0), Inches(5.8), SLIDE_W, Inches(1.5), fill_color=RGBColor(0x0D, 0x1B, 0x2A))
text(slide, Inches(1), Inches(5.9), Inches(3.5), Inches(1.2),
     "1,300+", size=54, color=ORANGE, bold=True, align=PP_ALIGN.CENTER)
text(slide, Inches(1), Inches(6.7), Inches(3.5), Inches(0.4),
     "SQL sources parsed", size=18, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)

text(slide, Inches(4.8), Inches(5.9), Inches(3.5), Inches(1.2),
     "99%", size=54, color=GREEN, bold=True, align=PP_ALIGN.CENTER)
text(slide, Inches(4.8), Inches(6.7), Inches(3.5), Inches(0.4),
     "parse accuracy", size=18, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)

text(slide, Inches(8.6), Inches(5.9), Inches(3.5), Inches(1.2),
     "0", size=54, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
text(slide, Inches(8.6), Inches(6.7), Inches(3.5), Inches(0.4),
     "parse errors", size=18, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 3 — Live Demo (placeholder)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY)

text(slide, Inches(1), Inches(2.5), Inches(11), Inches(1.0),
     "Live Demo", size=48, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
text(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.6),
     "Ask the Data Agent anything about your metrics — in plain English",
     size=24, color=LIGHT_TEAL, align=PP_ALIGN.CENTER)
text(slide, Inches(1), Inches(5.0), Inches(11), Inches(0.5),
     "[Switch to Fabric Data Agent screen recording]",
     size=18, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 4 — Knowledge Graph Visual (placeholder)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY)

text(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.8),
     "The Knowledge Graph Behind Every Answer", size=36, color=WHITE, bold=True)

rect(slide, Inches(0.8), Inches(1.3), Inches(4), Pt(4), fill_color=TEAL)

# Three layers
layers = [
    ("BUSINESS METRICS", "Certified definitions: ER Length of Stay, Census Dashboard, Readmission Rate...",
     Inches(2.0), TEAL),
    ("CALCULATION LOGIC", "SQL fragments: DATEDIFF, COUNT, AVG, GROUP BY, WHERE filters...",
     Inches(3.5), RGBColor(0x26, 0xA6, 0x9A)),
    ("SOURCE TABLES", "Physical tables: CLARITY_ADT, PATIENT, PAT_ENC, CLARITY_DEP...",
     Inches(5.0), RGBColor(0x00, 0x60, 0x56)),
]

for label, desc, top, color in layers:
    box = rounded_rect(slide, Inches(2), top, Inches(9), Inches(1.2), fill_color=color)
    text(slide, Inches(2.3), top + Inches(0.1), Inches(8.4), Inches(0.4),
         label, size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, Inches(2.3), top + Inches(0.5), Inches(8.4), Inches(0.5),
         desc, size=14, color=WHITE, align=PP_ALIGN.CENTER)

for y in [Inches(3.2), Inches(4.7)]:
    arrow = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(6.3), y, Inches(0.4), Inches(0.3))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = ORANGE
    arrow.line.fill.background()

text(slide, Inches(1), Inches(6.5), Inches(11), Inches(0.5),
     "Every answer traces from business question → calculation logic → source table",
     size=18, color=MEDIUM_GRAY, align=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 5 — Roadmap & Close
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, NAVY)

text(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.8),
     "What's Next", size=40, color=WHITE, bold=True)

rect(slide, Inches(0.8), Inches(1.3), Inches(4), Pt(4), fill_color=TEAL)

roadmap = [
    ("1", "Metadata Sync", "Auto-populate Purview & Power BI descriptions\nfrom the knowledge graph",
     TEAL),
    ("2", "Governance Flywheel", "Every question strengthens the knowledge base\nHigh-demand metrics promoted to dashboards",
     RGBColor(0x26, 0xA6, 0x9A)),
    ("3", "Multi-Dialect Support", "Oracle PL/SQL, Snowflake — native parsers\nfor each platform. 100% accuracy per dialect.",
     RGBColor(0x00, 0x60, 0x56)),
]

for i, (num, title, desc, color) in enumerate(roadmap):
    top = Inches(2.0) + Inches(1.5) * i
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.0), top + Inches(0.1),
                                  Inches(0.6), Inches(0.6))
    circ.fill.solid()
    circ.fill.fore_color.rgb = color
    circ.line.fill.background()
    text(slide, Inches(1.0), top + Inches(0.12), Inches(0.6), Inches(0.6),
         num, size=22, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(slide, Inches(1.9), top, Inches(10), Inches(0.5),
         title, size=24, color=WHITE, bold=True)
    text(slide, Inches(1.9), top + Inches(0.5), Inches(10), Inches(0.8),
         desc, size=17, color=LIGHT_TEAL)

# Close
rect(slide, Inches(0), Inches(6.2), SLIDE_W, Inches(1.3), fill_color=TEAL)
text(slide, Inches(1), Inches(6.3), Inches(11), Inches(0.5),
     "Entirely inside your Microsoft Fabric tenant. No data ever leaves.",
     size=20, color=WHITE, align=PP_ALIGN.CENTER)
text(slide, Inches(1), Inches(6.8), Inches(11), Inches(0.5),
     "www.aiviaapp.com", size=24, color=WHITE, bold=True, align=PP_ALIGN.CENTER)


# ============================================================
# Save
# ============================================================
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "presentation")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "aivia_demo.pptx")
prs.save(output_path)
print(f"Saved to: {output_path}")
print(f"Slides: {len(prs.slides)}")
