# -*- coding: utf-8 -*-
"""IPQ: 5-paper experiment extraction report (main framework)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreakIfNotEmpty)
from reportlab.platypus.doctemplate import NextPageTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('NotoSans', 'C:/Windows/Fonts/NotoSansSC-VF.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansBd', 'C:/Windows/Fonts/msyhbd.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('NotoSerif', 'C:/Windows/Fonts/NotoSerifSC-VF.ttf'))

SECTION_BG = colors.HexColor('#F4F5F7')
TABLE_STRIPE = colors.HexColor('#F6F8FB')
HEADER_FILL = colors.HexColor('#1F3A5F')
COVER_BLOCK = colors.HexColor('#142A47')
BORDER = colors.HexColor('#D4D9E0')
ACCENT = colors.HexColor('#2C6FB5')
ACCENT_2 = colors.HexColor('#C97B2E')
ACCENT_3 = colors.HexColor('#3E8E5A')
TEXT_PRIMARY = colors.HexColor('#1A1A1A')
TEXT_MUTED = colors.HexColor('#6B7280')
CV_BG = colors.HexColor('#FFF4E6')
IV_BG = colors.HexColor('#E8F0FE')
DV_BG = colors.HexColor('#E8F5ED')

PAGE_W, PAGE_H = A4
ML = 20 * mm; MR = 20 * mm; MT = 22 * mm; MB = 20 * mm
CW = PAGE_W - ML - MR

S = {}
S['PT'] = ParagraphStyle('PT', fontName='NotoSansBd', fontSize=14.5, textColor=colors.white, alignment=TA_LEFT, leading=20)
S['PS'] = ParagraphStyle('PS', fontName='NotoSans', fontSize=9.5, textColor=colors.HexColor('#C8D2DF'), alignment=TA_LEFT, leading=14)
S['DT'] = ParagraphStyle('DT', fontName='NotoSansBd', fontSize=20, textColor=HEADER_FILL, alignment=TA_LEFT, leading=28, spaceAfter=4)
S['H1'] = ParagraphStyle('H1', fontName='NotoSansBd', fontSize=15, textColor=HEADER_FILL, alignment=TA_LEFT, leading=21, spaceBefore=4, spaceAfter=4)
S['H2'] = ParagraphStyle('H2', fontName='NotoSansBd', fontSize=11.5, textColor=ACCENT, alignment=TA_LEFT, leading=16, spaceBefore=8, spaceAfter=3)
S['Body'] = ParagraphStyle('Body', fontName='NotoSans', fontSize=10, textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, leading=16.5, spaceAfter=5, wordWrap='CJK')
S['Bul'] = ParagraphStyle('Bul', fontName='NotoSans', fontSize=10, textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=16, spaceAfter=3, wordWrap='CJK', leftIndent=14)
S['Note'] = ParagraphStyle('Note', fontName='NotoSans', fontSize=9.3, textColor=TEXT_MUTED, alignment=TA_LEFT, leading=14, spaceAfter=4, leftIndent=8, rightIndent=8)
S['Form'] = ParagraphStyle('Form', fontName='NotoSerif', fontSize=10, textColor=TEXT_PRIMARY, alignment=TA_CENTER, leading=16, spaceAfter=5, backColor=SECTION_BG, borderPadding=6)
S['TC'] = ParagraphStyle('TC', fontName='NotoSans', fontSize=9.2, textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=13.5, wordWrap='CJK')
S['TCc'] = ParagraphStyle('TCc', fontName='NotoSans', fontSize=9.2, textColor=TEXT_PRIMARY, alignment=TA_CENTER, leading=13.5, wordWrap='CJK')
S['TH'] = ParagraphStyle('TH', fontName='NotoSansBd', fontSize=9.5, textColor=colors.white, alignment=TA_CENTER, leading=13.5, wordWrap='CJK')
S['THL'] = ParagraphStyle('THL', fontName='NotoSansBd', fontSize=9.5, textColor=colors.white, alignment=TA_LEFT, leading=13.5, wordWrap='CJK')
S['Cite'] = ParagraphStyle('Cite', fontName='NotoSerif', fontSize=9, textColor=TEXT_MUTED, alignment=TA_LEFT, leading=14, spaceAfter=4, leftIndent=8, rightIndent=8)


def draw_cover(c, d):
    W, H = PAGE_W, PAGE_H
    c.setFillColor(COVER_BLOCK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.saveState()
    c.setStrokeColor(colors.HexColor('#2A4A6E')); c.setLineWidth(0.6)
    for xo in [0, 8, 16]:
        c.line(W - 60*mm + xo, H - 25*mm, W - 18*mm + xo, H - 25*mm)
    c.setStrokeColor(ACCENT); c.setLineWidth(2.5)
    c.line(ML, H - 70*mm, ML, H - 130*mm)
    c.setFillColor(colors.HexColor('#1B345A')); c.setFont('NotoSansBd', 120)
    c.drawString(W - 78*mm, 22*mm, "EXP")
    c.restoreState()
    c.setFillColor(colors.HexColor('#9AA7B8')); c.setFont('NotoSans', 10)
    c.drawString(ML, H - 30*mm, "IPQ \u7814\u7a76\u9879\u76ee  \u00b7  \u6587\u732e\u5b9e\u9a8c\u63d0\u53d6\u62a5\u544a")
    c.setFillColor(ACCENT_2); c.setFont('NotoSansBd', 11)
    c.drawString(ML, H - 60*mm, "EXPERIMENT  EXTRACTION")
    c.setFillColor(colors.white); c.setFont('NotoSansBd', 28)
    for i, ln in enumerate(["\u4e94\u7bc7\u8bba\u6587\u7684\u5b9e\u9a8c", "\u6570\u636e \u00b7 \u65b9\u6cd5 \u00b7 \u8fc7\u7a0b \u00b7 \u7ed3\u8bba"]):
        c.drawString(ML, H - 85*mm - i*12*mm, ln)
    c.setFillColor(colors.HexColor('#B8C5D6')); c.setFont('NotoSerif', 12)
    c.drawString(ML, H - 115*mm, "Experimental Extraction from 5 Papers on PID & S-Curve Motion Control")
    c.setStrokeColor(colors.HexColor('#3A567A')); c.setLineWidth(0.5)
    c.line(ML, H - 128*mm, ML + 50*mm, H - 128*mm)
    c.setFillColor(colors.HexColor('#8C9AB0')); c.setFont('NotoSans', 10)
    for i, ln in enumerate(["\u672c\u62a5\u544a\u7cfb\u7edf\u63d0\u53d6 5 \u7bc7\u53c2\u8003\u6587\u732e\u4e2d\u6240\u6709\u5b9e\u9a8c\u7684\uff1a", "  \u00b7  \u8be6\u7ec6\u5b9e\u9a8c\u6570\u636e\uff08\u91cf\u5316\u6307\u6807\uff09", "  \u00b7  \u63a7\u5236\u53d8\u91cf\u4e0e\u81ea\u53d8\u91cf\u8bbe\u8ba1", "  \u00b7  \u5b9e\u9a8c\u8fc7\u7a0b\uff08\u5e73\u53f0 / \u6b65\u9aa4 / \u5de5\u51b5\uff09", "  \u00b7  \u5b9e\u9a8c\u7ed3\u8bba", "\u5e76\u9644\u8de8\u8bba\u6587\u5b9e\u9a8c\u65b9\u6cd5\u5bf9\u6bd4\u77e9\u9635\u3002"]):
        c.drawString(ML, H - 145*mm - i*6.5*mm, ln)
    c.setFillColor(colors.HexColor('#5A6B82')); c.setFont('NotoSans', 8.5)
    c.drawString(ML, 12*mm, "A Quantitative Comparison of Jerk-Limited S-Curve and PID Control for Smoother and More Energy-Efficient Mobile Robot Motion")
    c.drawRightString(W - MR, 12*mm, "2026.07")


def draw_later(c, d):
    W, H = PAGE_W, PAGE_H
    c.setStrokeColor(BORDER); c.setLineWidth(0.5)
    c.line(ML, H - 14*mm, W - MR, H - 14*mm)
    c.setFillColor(TEXT_MUTED); c.setFont('NotoSans', 8.5)
    c.drawString(ML, H - 11*mm, "IPQ \u9879\u76ee \u00b7 \u6587\u732e\u5b9e\u9a8c\u63d0\u53d6\u62a5\u544a")
    c.drawRightString(W - MR, H - 11*mm, "PID & S-Curve Motion Control")
    c.line(ML, 13*mm, W - MR, 13*mm)
    c.setFillColor(TEXT_MUTED); c.setFont('NotoSans', 8.5)
    c.drawString(ML, 9*mm, "5 \u7bc7\u8bba\u6587\u5b9e\u9a8c\u6570\u636e \u00b7 \u65b9\u6cd5 \u00b7 \u8fc7\u7a0b \u00b7 \u7ed3\u8bba")
    c.drawRightString(W - MR, 9*mm, "\u7b2c %d \u9875" % c.getPageNumber())


def banner(num, tc, en, ci):
    cell = Paragraph('<font color="#FFB66E" size="22"><b>' + num + '</b></font>&nbsp;&nbsp;<font color="white">' + tc + '</font>', S['PT'])
    sub = Paragraph(en + '<br/><font color="#8FA0B8">' + ci + '</font>', S['PS'])
    t = Table([[cell], [sub]], colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), HEADER_FILL), ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12), ('TOPPADDING', (0, 0), (0, 0), 8), ('BOTTOMPADDING', (0, 0), (0, 0), 2), ('TOPPADDING', (0, 1), (0, 1), 0), ('BOTTOMPADDING', (0, 1), (-1, -1), 8), ('LINEBEFORE', (0, 0), (0, -1), 4, ACCENT_2)]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 8)])


def h1(t):
    return KeepTogether([Spacer(1, 4), Paragraph(t, S['H1']), HRFlowable(width='100%', thickness=1.1, color=ACCENT, spaceBefore=2, spaceAfter=6)])

def h2(t): return Paragraph(t, S['H2'])
def p(t): return Paragraph(t, S['Body'])
def b(t): return Paragraph("\u2022 " + t, S['Bul'])
def formula(t): return Paragraph(t, S['Form'])
def note(t): return Paragraph(t, S['Note'])
def cite(t): return Paragraph(t, S['Cite'])


def dtable(headers, rows, cr=None, fcl=True):
    n = len(headers)
    if cr is None: cr = [1.0/n]*n
    tot = sum(cr); cw = [CW*r/tot for r in cr]
    hr = [Paragraph(h, S['THL'] if (i == 0 and fcl) else S['TH']) for i, h in enumerate(headers)]
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            cells.append(Paragraph(str(c), S['TC'] if (i == 0 and fcl) else S['TCc']))
        body.append(cells)
    data = [hr] + body
    t = Table(data, colWidths=cw, hAlign='CENTER', repeatRows=1)
    st = [('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('GRID', (0, 1), (-1, -1), 0.3, BORDER)]
    for i in range(1, len(data)):
        if i % 2 == 0: st.append(('BACKGROUND', (0, i), (-1, i), TABLE_STRIPE))
    t.setStyle(TableStyle(st))
    return t


def hbox(title, items, bg, bc):
    rows = [[Paragraph(title, S['TC'])]]
    for it in items:
        rows.append([Paragraph("\u2022 " + it, S['TC'])])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg), ('BOX', (0, 0), (-1, -1), 0.6, bc), ('LINEBEFORE', (0, 0), (0, -1), 3, bc), ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return KeepTogether([t, Spacer(1, 6)])


def cv(title, items):
    return hbox("<b>\u63a7\u5236\u53d8\u91cf\uff08Constants\uff09</b> &nbsp;" + title, items, CV_BG, ACCENT_2)

def iv(title, items):
    return hbox("<b>\u81ea\u53d8\u91cf\uff08Independent Variable\uff09</b> &nbsp;" + title, items, IV_BG, ACCENT)

def dv(items):
    return hbox("<b>\u56e0\u53d8\u91cf / \u6d4b\u91cf\u6307\u6807\uff08Dependent Variables\uff09</b>", items, DV_BG, ACCENT_3)


# Load content (paper1_exp ... comparison) from external file
exec(open("D:/IPQ/_exp_content.py", encoding="utf-8").read())


def main():
    out = "D:/IPQ/Experiment_Extraction_Report.pdf"
    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB, title="IPQ Experiment Extraction", author="ZCode (IPQ)", subject="Experiment Extraction", creator="ReportLab")
    cf = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='cover')
    ct = PageTemplate(id='Cover', frames=[cf], onPage=draw_cover)
    bf = Frame(ML, MB, CW, PAGE_H - MT - MB, id='body', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    bt = PageTemplate(id='Body', frames=[bf], onPage=draw_later)
    doc.addPageTemplates([ct, bt])
    story = [Spacer(1, 1), NextPageTemplate('Body'), PageBreakIfNotEmpty()]
    story.extend(intro())
    story.extend(paper1_exp())
    story.extend(paper2_exp())
    story.extend(paper3_exp())
    story.extend(paper4_exp())
    story.extend(paper5_exp())
    story.extend(comparison())
    doc.build(story)
    print("OK: " + out + "  (" + str(round(os.path.getsize(out)/1024, 1)) + " KB)")


if __name__ == '__main__':
    main()
