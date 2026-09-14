#!/usr/bin/env python3
"""Build a print-ready 6x9 paperback interior PDF from manuscript.md (KDP)."""
import re
from reportlab.lib.pagesizes import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                Paragraph, Spacer, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

LIB = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Body", LIB+"LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", LIB+"LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", LIB+"LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", LIB+"LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-Italic", boldItalic="Body-BoldItalic")
pdfmetrics.registerFont(TTFont("Head", LIB+"LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("HeadR", LIB+"LiberationSans-Regular.ttf"))

PAGE_W, PAGE_H = 5.5*inch, 8.5*inch   # standard trade paperback trim
ML = MR = 0.65*inch         # symmetric margins (>> KDP minimums for this length)
MT, MB = 0.65*inch, 0.6*inch

BROWN = "#3a2418"
PLUM = "#3a2340"

styles = {
    "title": ParagraphStyle("title", fontName="Head", fontSize=30, leading=36,
                             alignment=TA_CENTER, textColor=PLUM, spaceBefore=90, spaceAfter=14),
    "subtitle": ParagraphStyle("subtitle", fontName="Body-Italic", fontSize=13.5, leading=19,
                               alignment=TA_CENTER, textColor=BROWN, spaceAfter=8),
    "byline": ParagraphStyle("byline", fontName="Body-Italic", fontSize=11, leading=16,
                             alignment=TA_CENTER, textColor="#6b4a3a", spaceBefore=24),
    "h1": ParagraphStyle("h1", fontName="Head", fontSize=19, leading=24, textColor=PLUM,
                         spaceBefore=6, spaceAfter=16, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="Head", fontSize=13, leading=17, textColor=BROWN,
                         spaceBefore=14, spaceAfter=5, keepWithNext=True),
    "h3": ParagraphStyle("h3", fontName="Head", fontSize=11, leading=15, textColor=BROWN,
                         spaceBefore=10, spaceAfter=3, keepWithNext=True),
    "body": ParagraphStyle("body", fontName="Body", fontSize=11.3, leading=16.5,
                           alignment=TA_JUSTIFY, spaceAfter=8),
    "bullet": ParagraphStyle("bullet", fontName="Body", fontSize=10.8, leading=14.5,
                             leftIndent=16, bulletIndent=3, spaceAfter=3),
    "num": ParagraphStyle("num", fontName="Body", fontSize=10.8, leading=14.5,
                          leftIndent=16, spaceAfter=3),
    "quote": ParagraphStyle("quote", fontName="Body-Italic", fontSize=10.4, leading=14.5,
                            leftIndent=20, rightIndent=20, alignment=TA_JUSTIFY,
                            spaceBefore=5, spaceAfter=8, textColor="#4a3526"),
    "center": ParagraphStyle("center", fontName="Body", fontSize=10.8, leading=15,
                             alignment=TA_CENTER, spaceAfter=7),
}

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return t

lines = open("manuscript.md", encoding="utf-8").read().split("\n")
flow = []
seen_chapter = False
first_h1_done = False

for raw in lines:
    t = raw.strip()
    if t == "" or t == "---":
        continue
    if t.startswith("# "):
        flow.append(Paragraph(inline(t[2:]), styles["title"]))
        continue
    if t.startswith("#### "):
        flow.append(Paragraph(inline(t[5:]), styles["h3"]))
        continue
    if t.startswith("### "):
        flow.append(Paragraph(inline(t[4:]), styles["subtitle" if not seen_chapter else "h2"]))
        continue
    if t.startswith("## "):
        flow.append(PageBreak())   # title page and each chapter start fresh
        seen_chapter = True
        flow.append(Paragraph(inline(t[3:]), styles["h1"]))
        continue
    if t.startswith("> "):
        flow.append(Paragraph(inline(t[2:]), styles["quote"]))
        continue
    m = re.match(r"^-\s*\[[ xX]?\]\s+(.*)$", t)
    if m:
        flow.append(Paragraph(inline(m[1]), styles["bullet"], bulletText="□"))
        continue
    m = re.match(r"^[-*]\s+(.*)$", t)
    if m:
        flow.append(Paragraph(inline(m[1]), styles["bullet"], bulletText="•"))
        continue
    m = re.match(r"^(\d+)\.\s+(.*)$", t)
    if m:
        flow.append(Paragraph("<b>%s.</b> %s" % (m[1], inline(m[2])), styles["num"]))
        continue
    # italic-only line (byline)
    if t.startswith("*") and t.endswith("*") and not seen_chapter:
        flow.append(Paragraph(inline(t), styles["byline"]))
        continue
    flow.append(Paragraph(inline(t), styles["body"]))

def footer(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setFont("HeadR", 9)
    canvas.setFillColor(BROWN)
    canvas.drawCentredString(PAGE_W/2, 0.34*inch, str(doc.page))
    canvas.restoreState()

frame = Frame(ML, MB, PAGE_W-ML-MR, PAGE_H-MT-MB, id="f")
doc = BaseDocTemplate("Cappadocia-Paperback-Interior.pdf",
                      pagesize=(PAGE_W, PAGE_H),
                      pageTemplates=[PageTemplate("main", [frame], onPage=footer)],
                      title="Cappadocia: The Complete Traveler's Guide")
doc.build(flow)
print("PAGES=%d" % doc.page)
