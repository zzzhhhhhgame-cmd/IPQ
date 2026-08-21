# -*- coding: utf-8 -*-
"""
为 IPQ 项目生成 5 篇论文的中文总结 PDF。
统一模板：简洁封面（Canvas 绘制）+ 正文（ReportLab Flowables）。
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 字体注册（CJK）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pdfmetrics.registerFont(TTFont('NotoSans', 'C:/Windows/Fonts/NotoSansSC-VF.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansBd', 'C:/Windows/Fonts/msyhbd.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('NotoSerif', 'C:/Windows/Fonts/NotoSerifSC-VF.ttf'))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配色方案（来自 palette.cascade --mode minimal，针对学术研究主题）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE_BG       = colors.HexColor('#FFFFFF')
SECTION_BG    = colors.HexColor('#F4F5F7')
CARD_BG       = colors.HexColor('#F0F2F5')
TABLE_STRIPE  = colors.HexColor('#F6F7F9')
HEADER_FILL   = colors.HexColor('#1F3A5F')   # 深学术蓝
COVER_BLOCK   = colors.HexColor('#16304E')
BORDER        = colors.HexColor('#D4D9E0')
ICON          = colors.HexColor('#3E5C8A')
ACCENT        = colors.HexColor('#2C6FB5')   # 学术蓝
ACCENT_2      = colors.HexColor('#C97B2E')   # 暖色强调（S曲线/对比）
TEXT_PRIMARY  = colors.HexColor('#1A1A1A')
TEXT_MUTED    = colors.HexColor('#6B7280')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 页面与边距
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE_W, PAGE_H = A4
MARGIN_L = 22 * mm
MARGIN_R = 22 * mm
MARGIN_T = 22 * mm
MARGIN_B = 20 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 段落样式
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def make_styles():
    s = {}
    s['CoverKicker'] = ParagraphStyle('CoverKicker', fontName='NotoSans', fontSize=11,
        textColor=colors.HexColor('#9AA7B8'), alignment=TA_LEFT, leading=14,
        spaceAfter=6)
    s['CoverTitleCN'] = ParagraphStyle('CoverTitleCN', fontName='NotoSansBd', fontSize=26,
        textColor=colors.white, alignment=TA_LEFT, leading=36)
    s['CoverTitleEN'] = ParagraphStyle('CoverTitleEN', fontName='NotoSerif', fontSize=13,
        textColor=colors.HexColor('#B8C5D6'), alignment=TA_LEFT, leading=18,
        spaceBefore=10)
    s['CoverMeta'] = ParagraphStyle('CoverMeta', fontName='NotoSans', fontSize=10.5,
        textColor=colors.HexColor('#C8D2DF'), alignment=TA_LEFT, leading=16)
    s['CoverSummary'] = ParagraphStyle('CoverSummary', fontName='NotoSans', fontSize=10,
        textColor=colors.HexColor('#7E8C9E'), alignment=TA_LEFT, leading=17)

    s['H1'] = ParagraphStyle('H1', fontName='NotoSansBd', fontSize=16, textColor=HEADER_FILL,
        alignment=TA_LEFT, leading=22, spaceBefore=6, spaceAfter=6)
    s['H2'] = ParagraphStyle('H2', fontName='NotoSansBd', fontSize=12.5, textColor=ACCENT,
        alignment=TA_LEFT, leading=18, spaceBefore=10, spaceAfter=4)
    s['Body'] = ParagraphStyle('Body', fontName='NotoSans', fontSize=10.3, textColor=TEXT_PRIMARY,
        alignment=TA_JUSTIFY, leading=17.5, spaceAfter=6, wordWrap='CJK',
        firstLineIndent=0)
    s['BodyTight'] = ParagraphStyle('BodyTight', fontName='NotoSans', fontSize=10.3,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=17, spaceAfter=4, wordWrap='CJK')
    s['Bullet'] = ParagraphStyle('Bullet', fontName='NotoSans', fontSize=10.3,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=17, spaceAfter=4,
        wordWrap='CJK', leftIndent=14, bulletIndent=2)
    s['Quote'] = ParagraphStyle('Quote', fontName='NotoSerif', fontSize=9.8,
        textColor=TEXT_MUTED, alignment=TA_LEFT, leading=16, spaceAfter=6,
        leftIndent=10, rightIndent=10, borderColor=BORDER, borderWidth=0,
        backColor=SECTION_BG, borderPadding=8)
    s['Caption'] = ParagraphStyle('Caption', fontName='NotoSans', fontSize=9,
        textColor=TEXT_MUTED, alignment=TA_LEFT, leading=13, spaceAfter=8)
    s['TableCell'] = ParagraphStyle('TableCell', fontName='NotoSans', fontSize=9.5,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=14, wordWrap='CJK')
    s['TableHead'] = ParagraphStyle('TableHead', fontName='NotoSansBd', fontSize=9.8,
        textColor=colors.white, alignment=TA_LEFT, leading=14, wordWrap='CJK')
    return s

STYLES = make_styles()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 封面绘制（on_first_page 回调）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def draw_cover(canv, doc, meta):
    """绘制深色封面背景 + 文字层。"""
    W, H = PAGE_W, PAGE_H
    # Layer 0: 深色背景填充
    canv.setFillColor(COVER_BLOCK)
    canv.rect(0, 0, W, H, fill=1, stroke=0)

    # Layer 1: 装饰几何元素（被裁剪到页面内）
    canv.saveState()
    # 右上角细线装饰
    canv.setStrokeColor(colors.HexColor('#2A4A6E'))
    canv.setLineWidth(0.6)
    for i, x_off in enumerate([0, 8, 16]):
        canv.line(W - 60*mm + x_off, H - 25*mm, W - 18*mm + x_off, H - 25*mm)
    # 左侧垂直强调线
    canv.setStrokeColor(ACCENT)
    canv.setLineWidth(2.2)
    canv.line(MARGIN_L, H - 65*mm, MARGIN_L, H - 120*mm)
    # 底部水印大数字
    canv.setFillColor(colors.HexColor('#1E3A5C'))
    canv.setFont('NotoSansBd', 140)
    canv.drawString(W - 95*mm, 18*mm, meta.get('num', ''))
    canv.restoreState()

    # Layer 2: 顶部 Kicker
    canv.setFillColor(colors.HexColor('#9AA7B8'))
    canv.setFont('NotoSans', 10)
    canv.drawString(MARGIN_L, H - 30*mm, "IPQ 研究项目  ·  文献综述总结")

    # Layer 3: 文字层
    # Kicker 小标签
    canv.setFillColor(ACCENT_2)
    canv.setFont('NotoSansBd', 10.5)
    canv.drawString(MARGIN_L, H - 58*mm, "PAPER  SUMMARY")

    # 中文标题（自动换行）
    canv.setFillColor(colors.white)
    canv.setFont('NotoSansBd', 25)
    title_cn = meta['title_cn']
    _draw_wrapped(canv, title_cn, MARGIN_L, H - 78*mm, CONTENT_W, 34, 'NotoSansBd', 25, colors.white)

    # 英文原标题（斜体感用 Serif）
    canv.setFillColor(colors.HexColor('#B8C5D6'))
    canv.setFont('NotoSerif', 12.5)
    _draw_wrapped(canv, meta['title_en'], MARGIN_L, H - 78*mm - (34*_count_lines(title_cn, CONTENT_W, 25)+1)*mm - 6*mm,
                  CONTENT_W, 17, 'NotoSerif', 12.5, colors.HexColor('#B8C5D6'))

    # 分隔线
    canv.setStrokeColor(colors.HexColor('#3A567A'))
    canv.setLineWidth(0.5)
    canv.line(MARGIN_L, H - 135*mm, MARGIN_L + 40*mm, H - 135*mm)

    # Meta 信息（作者/出处/年份）
    canv.setFillColor(colors.HexColor('#C8D2DF'))
    canv.setFont('NotoSans', 10.5)
    y = H - 148*mm
    for line in meta['meta_lines']:
        canv.drawString(MARGIN_L, y, line)
        y -= 16

    # 一句话核心结论
    canv.setFillColor(colors.HexColor('#7E8C9E'))
    canv.setFont('NotoSans', 9.5)
    _draw_wrapped(canv, "核心一句话：" + meta['oneliner'], MARGIN_L, 60*mm,
                  CONTENT_W, 16, 'NotoSans', 9.5, colors.HexColor('#9DABC0'))

    # 底部 footer
    canv.setFillColor(colors.HexColor('#5A6B82'))
    canv.setFont('NotoSans', 8.5)
    canv.drawString(MARGIN_L, 12*mm,
                    "A Quantitative Comparison of Jerk-Limited S-Curve and PID Control "
                    "for Smoother and More Energy-Efficient Mobile Robot Motion")
    canv.drawRightString(W - MARGIN_R, 12*mm, "2026.07")


def _count_lines(text, max_w, font_size, font='NotoSansBd'):
    """粗略估算中文换行行数。"""
    # 中文字符宽度近似等于 font_size
    avg_char_w = font_size
    chars_per_line = max(1, int(max_w / avg_char_w))
    import math
    return max(1, math.ceil(len(text) / chars_per_line))


def _draw_wrapped(canv, text, x, y, max_w, line_h, font, size, color):
    """简单中文换行绘制（按字符宽度切分）。"""
    canv.setFillColor(color)
    canv.setFont(font, size)
    # 按字符粗略估算（CJK 等宽近似）
    char_w = size  # CJK 全角近似
    cur = ""
    cy = y
    lines = []
    buf = ""
    for ch in text:
        if ch == '\n':
            lines.append(buf)
            buf = ""
            continue
        # 估算宽度：CJK 全角=size，ASCII 半角=size/2
        w = size if ord(ch) > 127 else size * 0.55
        if pdfmetrics.stringWidth(buf + ch, font, size) > max_w:
            lines.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        lines.append(buf)
    for i, ln in enumerate(lines):
        canv.drawString(x, cy - i * line_h, ln)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 正文页眉/页脚
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def make_later_page(title_short):
    def _draw(canv, doc):
        W, H = PAGE_W, PAGE_H
        # 顶部细线
        canv.setStrokeColor(BORDER)
        canv.setLineWidth(0.5)
        canv.line(MARGIN_L, H - 14*mm, W - MARGIN_R, H - 14*mm)
        # 页眉文字
        canv.setFillColor(TEXT_MUTED)
        canv.setFont('NotoSans', 8.5)
        canv.drawString(MARGIN_L, H - 11*mm, "IPQ 项目 · 论文总结")
        canv.drawRightString(W - MARGIN_R, H - 11*mm, title_short)
        # 页脚
        canv.setStrokeColor(BORDER)
        canv.line(MARGIN_L, 13*mm, W - MARGIN_R, 13*mm)
        canv.setFillColor(TEXT_MUTED)
        canv.setFont('NotoSans', 8.5)
        canv.drawString(MARGIN_L, 9*mm, "Jerk-Limited S-Curve vs. PID Control — Mobile Robot Motion")
        canv.drawRightString(W - MARGIN_R, 9*mm, "第 %d 页" % canv.getPageNumber())
    return _draw


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 内容构件工厂
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def h1(text):
    return KeepTogether([Spacer(1, 4), Paragraph(text, STYLES['H1']),
                         HRFlowable(width='100%', thickness=1.2, color=ACCENT,
                                    spaceBefore=2, spaceAfter=8)])

def h2(text):
    return KeepTogether([Paragraph(text, STYLES['H2'])])

def p(text):
    return Paragraph(text, STYLES['Body'])

def bullet(text):
    return Paragraph(f"• {text}", STYLES['Bullet'])

def quote(text):
    return Paragraph(text, STYLES['Quote'])

def info_table(rows, col_widths=None):
    """两列信息表（标签-值）。"""
    if col_widths is None:
        col_widths = [CONTENT_W * 0.28, CONTENT_W * 0.72]
    data = [[Paragraph(f"<b>{k}</b>", STYLES['TableCell']),
             Paragraph(v, STYLES['TableCell'])] for k, v in rows]
    t = Table(data, colWidths=col_widths, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), SECTION_BG),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.4, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER),
    ]))
    return t

def data_table(headers, rows, col_ratios=None):
    """数据表（带表头）。"""
    n = len(headers)
    if col_ratios is None:
        col_ratios = [1.0 / n] * n
    total = sum(col_ratios)
    col_widths = [CONTENT_W * r / total for r in col_ratios]
    head_row = [Paragraph(h, STYLES['TableHead']) for h in headers]
    body_rows = []
    for r in rows:
        body_rows.append([Paragraph(str(c), STYLES['TableCell']) for c in r])
    data = [head_row] + body_rows
    t = Table(data, colWidths=col_widths, hAlign='CENTER', repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, HEADER_FILL),
        ('GRID', (0, 1), (-1, -1), 0.3, BORDER),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), TABLE_STRIPE))
    t.setStyle(TableStyle(style))
    return t


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PDF 构建主函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_pdf(out_path, meta, body_flowables, title_short):
    """生成单篇总结 PDF。"""
    doc = BaseDocTemplate(
        out_path, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title=meta['title_cn'], author='ZCode (IPQ 项目)',
        subject='论文研究总结', creator='ReportLab',
    )
    # 封面页模板（无内容 frame，全部由 onPage 绘制）
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id='cover')
    cover_tpl = PageTemplate(id='Cover', frames=[cover_frame],
                             onPage=lambda c, d: draw_cover(c, d, meta))

    # 正文模板
    body_frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W,
                       PAGE_H - MARGIN_T - MARGIN_B, id='body',
                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    body_tpl = PageTemplate(id='Body', frames=[body_frame],
                            onPage=make_later_page(title_short))

    doc.addPageTemplates([cover_tpl, body_tpl])

    # 封面占位（一个不可见 flowable 触发封面页 + 跳到正文模板）
    story = []
    from reportlab.platypus.flowables import PageBreakIfNotEmpty
    from reportlab.platypus.doctemplate import NextPageTemplate
    # 用一个 Spacer 占据封面页，然后切换到 Body 模板
    story.append(Spacer(1, 1))
    story.append(NextPageTemplate('Body'))
    story.append(PageBreakIfNotEmpty())
    story.extend(body_flowables)

    doc.build(story)
    size = os.path.getsize(out_path)
    print(f"  ✓ 已生成: {out_path}  ({size/1024:.1f} KB)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 五篇论文的内容定义
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def paper1():
    """Control BLDC Motor Speed using PID Controller (Mahmud et al., 2020)"""
    meta = {
        'num': '01',
        'title_cn': '基于 PID 控制器的无刷直流电机（BLDC）转速控制',
        'title_en': 'Control BLDC Motor Speed using PID Controller',
        'meta_lines': [
            '作者：Md Mahmud, S. M. A. Motakabber, A. H. M. Zahirul Alam, Anis Nurashikin Nordin',
            '机构：马来西亚国际伊斯兰大学 电气与计算机工程系',
            '出处：International Journal of Advanced Computer Science and Applications (IJACSA), Vol. 11, No. 3, 2020',
            '方法类别：闭环 PID 控制（电机调速）',
        ],
        'oneliner': '在 BLDC 电机中，PID 控制器相比 PI 与模糊控制器具有更小的超调、更快的整定，综合性能最佳。',
    }
    body = [
        h1('一、研究背景与问题'),
        p('在绿色技术与清洁能源的大趋势下，电动机是把电能转换为机械能的核心装置。其中<b>无刷直流电机（BLDC）</b>因维护成本低、结构紧凑、效率高（常超过 95%），被广泛用于电动汽车、变频驱动等工业场景。然而，BLDC 的性能高度依赖其控制电路，设计高性能控制电路一直是研究难点。'),
        p('论文指出：传统的 <b>PI/PID</b> 控制器虽然结构简单、易于实现，但参数整定并不简单；尤其在负载波动、非线性因素存在时，难以在所有工况下都获得最优响应。本文的目标是通过<b>改进的 PID 控制方案</b>实现对 BLDC 电机转速的有效调节，并在负载变化时维持恒定转速。'),

        h1('二、核心方法'),
        h2('1. 系统结构'),
        p('采用<b>双闭环控制</b>：内环用于检测电源极性与换相，外环用于转速控制。系统包含 DC 电源、PID 控制器、逆变器（DC→AC，因 BLDC 需类三相交流电压）、霍尔传感器（检测转子位置）以及电机本体。'),
        h2('2. PID 控制器建模'),
        p('PID 传递函数为：G(s) = Kp + Ki/s + Kd·s。控制律 U(t) = Kp·e(t) + Ki∫e(t)dt + Kd·de(t)/dt。本文所用关键参数：'),
        data_table(
            ['方法', 'Kp', 'Ki', 'Kd'],
            [['PID（本文）', '100', '0.5', '500']],
            col_ratios=[1.6, 1, 1, 1]
        ),
        Spacer(1, 6),
        h2('3. 仿真平台'),
        p('基于 <b>MATLAB/Simulink</b> 搭建三相 BLDC 电机控制系统完整模型，包含解码器真值表（顺时针/逆时针换相）、反电动势（BEMF）生成、逆变器开关逻辑等，并在 2500 rpm 参考转速下进行空载测试。'),

        h1('三、主要结果'),
        p('在 2500 rpm 参考转速、空载条件下，对 PI、PID、模糊逻辑三种控制器进行对比，关键性能指标如下：'),
        data_table(
            ['指标', 'PI 控制器', 'PID 控制器', '模糊控制器'],
            [
                ['整定时间', '15.20 ms', '约 18 ms', '9.2 ms'],
                ['超调量', '32.67%', '0.4%', '30.92%'],
                ['欠调量', '1.68%', '1.9%', '3.2%'],
                ['转换速率', '621.35 ms', '92.27 ms', '598.15 ms'],
                ['预调节', '0.66%', '2.5%', '0.67%'],
            ],
            col_ratios=[1.3, 1.2, 1.2, 1.2]
        ),
        Spacer(1, 6),
        p('可见 <b>PID 控制器的超调量（0.4%）远低于 PI（32.67%）和模糊（30.92%）</b>，转换速率也明显更优。约 0.018 s 后电机即稳定在 2500 rpm；电磁转矩、三相定子电流、反电动势均在约 0.030 s 后稳定。'),

        h1('四、结论与对本研究的启示'),
        bullet('<b>核心结论</b>：在所对比的三种控制器中，PID 控制器为 BLDC 电机提供了最佳综合控制性能。'),
        bullet('<b>方法局限</b>：仅空载仿真，未在变负载、变惯量工况下验证；参数为手工给定，未给出系统化整定方法。'),
        bullet('<b>对本研究的关联</b>：本文属于"PID 控制器在电机运动控制中的经典应用与性能上限"的代表性工作。在我们的 IPQ 研究中，PID 是<b>对照基线（baseline）</b>——它代表了"传统反馈控制"路径；而 S 曲线属于"前馈轨迹规划"路径。该论文提供的超调、整定时间等量化指标，可作为我们评估 PID 路径平滑性与能耗时的参照。'),

        h1('五、文献信息'),
        quote('Mahmud, M., Motakabber, S. M. A., Alam, A. H. M. Z., & Nordin, A. N. (2020). '
              'Control BLDC Motor Speed using PID Controller. International Journal of Advanced '
              'Computer Science and Applications (IJACSA), 11(3), 477–481.'),
    ]
    return meta, body, 'BLDC PID 控制 (Mahmud 2020)'


def paper2():
    """Design and implementation speed control system of DC Motor based on PID (Hammoodi et al., 2020)"""
    meta = {
        'num': '02',
        'title_cn': '基于 PID 控制与 MATLAB/Simulink 的直流电机调速系统设计与实现',
        'title_en': 'Design and Implementation Speed Control System of DC Motor based on PID Control and Matlab Simulink',
        'meta_lines': [
            '作者：Salman Jasim Hammoodi, Kareem Sayegh Flayyih, Ahmed Refaat Hamad',
            '机构：Middle Technical University / Southern Technical University（伊拉克）',
            '出处：International Journal of Power Electronics and Drive Systems (IJPEDS), Vol. 11, No. 1, 2020, pp. 127–134',
            '方法类别：闭环 PID 调速 + PWM 斩波电路',
        ],
        'oneliner': '用 PID + 斩波晶体管电路构建直流电机闭环调速系统，可在负载扰动下自动维持转速恒定。',
    }
    body = [
        h1('一、研究背景与动机'),
        p('工业中大部分电机直接由电网供电，其行为取决于负载特性：轻载时转速高、转矩小；重载时转速低、转矩大。交流变频器成本低廉，但<b>直流电机的可调速驱动器价格昂贵</b>，许多需要它的行业难以负担。本文目标是设计一套经济可行、易于实现、可移植到任意 DC 电机的<b>自有 PID 调速系统</b>。'),

        h1('二、核心方法'),
        h2('1. DC 电机建模'),
        p('将电机分为<b>电气部分</b>（电枢：电阻 R、电感 L、反电动势 Kb）与<b>机械部分</b>（转子：转动惯量 J、粘性摩擦系数 b、转矩 T）。关键方程：'),
        quote('V_dc = E_am + I_am·R_a + V_brush；  E_am = K_m·I_f·ω；  T = P_out/ω = K_m·I_a·I_f'),
        h2('2. PID 控制器'),
        p('控制器接收输入信号与测速发电机输出之差作为误差，经放大后送入被控对象。PID 传递函数：Gc(s) = Kp + Kd·s + Ki/s。论文给出四种 PID 形式：理想型、串联型、并联型、工业型，并提及 Ziegler–Nichols 整定法则。'),
        h2('3. 仿真实现'),
        p('使用 <b>MATLAB/Simulink</b> 搭建他励直流电机模型，由 DC 源经 <b>GTO-1 晶闸管斩波电路</b>供电。PID 参数取 <b>P = 4, I = 0.01, D = 0.5</b>。系统通过转速闭环：测量实际转速，与参考转速比较，确定所需的电枢电流。'),

        h1('三、主要结果'),
        bullet('转速响应（wr 相对参考转速）：PID 控制下响应<b>快速</b>，能迅速跟踪参考值。'),
        bullet('负载转矩（TL）与电枢电流：均展现出<b>快速响应</b>特性，验证了扰动抑制能力。'),
        bullet('PWM 信号：给出了 GTO-1 晶闸管的触发波形，形成完整的斩波驱动链路。'),
        p('结论：PID 控制器在伺服机构或调节系统中均能提供良好的动态行为；但不同厂商的 PID 算法实现存在差异，更换控制器时必须重新计算参数。'),

        h1('四、关键洞察与对本研究的启示'),
        bullet('<b>双时间常数模型</b>：论文用电气时间常数 Ta 与机电时间常数 Tem 描述电机（Ta ≪ Tem），简化后传递函数 ω(s)/Va(s) = (1/Km)/[(1+sTem)(1+sTa)]，是建模移动机器人驱动轮电机的经典起点。'),
        bullet('<b>PID + PWM 斩波</b>是移动机器人底层驱动的事实标准方案，本文提供了该方案的完整 Simulink 实现，可作为本研究"PID 基线"的工程参考。'),
        bullet('<b>局限</b>：论文聚焦"转速跟踪"而非"轨迹平滑"——它能让转速快速跟上阶跃参考，但<b>参考本身若不光滑（阶跃），仍会产生冲击（jerk）与机械振动</b>。这正是本研究引入 S 曲线前馈规划要解决的核心问题。'),
        bullet('<b>桥接点</b>：本文回答"如何快速到达目标转速"；本研究要回答"如何让到达目标转速的<b>过程</b>更平滑、更节能"——PID 解决"快与准"，S 曲线解决"稳与省"。'),

        h1('五、文献信息'),
        quote('Hammoodi, S. J., Flayyih, K. S., & Hamad, A. R. (2020). Design and implementation '
              'speed control system of DC Motor based on PID control and Matlab Simulink. '
              'International Journal of Power Electronics and Drive Systems (IJPEDS), 11(1), 127–134. '
              'DOI: 10.11591/ijpeds.v11.i1.pp127-134'),
    ]
    return meta, body, 'DC电机 PID 调速 (Hammoodi 2020)'


def paper3():
    """Optimized S-Curve Motion Profiles for Minimum Residual Vibration (Meckl et al., 1998)"""
    meta = {
        'num': '03',
        'title_cn': '面向最小残余振动的 S 曲线运动轨迹优化',
        'title_en': 'Optimized S-Curve Motion Profiles for Minimum Residual Vibration',
        'meta_lines': [
            '作者：Peter H. Meckl, Peter B. Arestides, Matthew C. Woods',
            '机构：School of Mechanical Engineering, Purdue University（美国）',
            '出处：Proceedings of the American Control Conference, Philadelphia, PA, June 1998, pp. 2627–2631',
            '方法类别：S 曲线 + 频域优化（减振）',
        ],
        'oneliner': '通过频域分析最优选择 S 曲线的"加速上升时间"，使残余振动降低近一个数量级，且对频率不确定性具有鲁棒性。',
    }
    body = [
        h1('一、研究背景与核心问题'),
        p('在制造与机器人领域，<b>"快速运动且无残余振动"</b>是普遍挑战。简单的<b>梯形速度曲线</b>（匀加速→匀速→匀减速）虽然快，但由于加速度在切换时刻发生<b>跳变</b>，jerk（加速度的导数）趋于无穷，会激发系统残余振动，需等待振动衰减才能精确到位。'),
        p('<b>S 曲线速度轨迹</b>通过让加速度"缓升缓降"产生 S 形速度曲线，使 jerk 保持有限，从而降低振动倾向。但论文指出一个关键空白：<b>此前没有系统方法来最优地选择 S 曲线的"上升时间" ta</b>——它直接决定了运动速度与残余振动的权衡。本文用<b>频域分析</b>填补这一空白。'),

        h1('二、核心方法：频域驱动的上升时间优化'),
        h2('1. 系统模型'),
        p('采用<b>无阻尼双质量系统</b>（自然频率 ωn = √(k·(m1+m2)/(m1·m2))）模拟柔性负载。该模型适用于阻尼比 ζ < 0.1 的轻阻尼系统（大多数实际系统如此）。'),
        h2('2. 关键无量纲参数'),
        bullet('<b>无量纲上升时间</b> ta* = ta / tsp（tsp 为 S 曲线达到峰值速度的总时间）'),
        bullet('<b>无量纲响应时间</b> ωn·tr / 2π（矩形脉冲持续期内的振荡周期数），反映系统柔性与响应速度的组合影响。'),
        h2('3. 残余振动公式'),
        p('论文推导出 S 曲线力输入产生的无量纲残余加速度 a* 的解析表达式（eq.3），它强烈依赖于 ta*。通过绘制 a* 随 ta* 变化的曲线，发现<b>存在使 a* 极小的"下凹点（dip）"</b>。选取最小的下凹点对应的 ta*，即可在保证最快响应的同时最小化残余振动。'),
        h2('4. 鲁棒性考量'),
        p('当 ωn·tr/2π 为整数且 ta*=0 时理论残余振动为零，但实际频率稍有偏差（如 2.01）即产生显著振动。因此<b>对整数点选择"下一个下凹点"（如 ωn·tr/2π=2 时取 ta*=0.332）</b>以获得鲁棒性。'),

        h1('三、主要结果'),
        p('对三种输入进行对比：梯形（ta*=0）、经验法则 S 曲线（ta*=1/6）、优化 S 曲线（按 ta*~ωn·tr/2π 关系选取）。残余加速度（dB）对比：'),
        data_table(
            ['对比项', '梯形轨迹', '经验 S 曲线 (ta*=1/6)', '优化 S 曲线'],
            [
                ['理想（频率精确）', '基准', '多数情况改善', '全范围最优'],
                ['频率偏差 10%', '残余振动大', '改善有限', '低 ωn·tr/2π 区改善约 20 dB'],
            ],
            col_ratios=[1.4, 1.1, 1.3, 1.1]
        ),
        Spacer(1, 6),
        bullet('<b>理想情况下</b>，优化 S 曲线在全 ωn·tr/2π 范围内残余振动最低。'),
        bullet('<b>频率偏差 10% 时</b>，优化 S 曲线残余振动仍显著低于梯形与经验 S 曲线，<b>改善接近一个数量级</b>。'),
        bullet('改善在<b>低 ωn·tr/2π（低自然频率或极快运动）</b>区域最显著——这正是减振最困难的工况。'),

        h1('四、对本研究的核心价值'),
        bullet('<b>理论根基</b>：本文是 S 曲线减振机理的<b>奠基性理论工作</b>，给出了"为什么 S 曲线能减振"的频域解释——通过塑造输入力函数的频率内容，使其在系统自然频率处的激励能量最小。'),
        bullet('<b>设计准则</b>：提供了"S 曲线上升时间应如何选择"的量化方法，而非凭经验取 ta*=1/6。这为本研究的 S 曲线参数设计提供了直接的方法论依据。'),
        bullet('<b>对比维度</b>：本研究关注的"平滑性"指标——残余振动、超调——正是本文的优化目标。可沿用其频域评估框架量化 S 曲线相对 PID（无前馈整形）的平滑性优势。'),
        bullet('<b>局限与延伸</b>：本文针对<b>单自由度、点对点开环</b>运动；本研究需扩展到移动机器人（多自由度、闭环跟踪、连续轨迹），并新增"能耗"维度——本文未涉及能耗评估。'),

        h1('五、文献信息'),
        quote('Meckl, P. H., Arestides, P. B., & Woods, M. C. (1998). Optimized S-curve motion '
              'profiles for minimum residual vibration. Proceedings of the American Control '
              'Conference, Philadelphia, PA, pp. 2627–2631.'),
    ]
    return meta, body, 'S曲线减振优化 (Meckl 1998)'


def paper4():
    """Speed Control of DC Motor Using Fuzzy PID Controller (Bansal & Narvey, 2013)"""
    meta = {
        'num': '04',
        'title_cn': '基于模糊 PID 控制器的直流电机调速',
        'title_en': 'Speed Control of DC Motor Using Fuzzy PID Controller',
        'meta_lines': [
            '作者：Umesh Kumar Bansal, Rakesh Narvey',
            '机构：M.I.T.S. Gwalior 电气工程系（印度）',
            '出处：Advance in Electronic and Electric Engineering, Vol. 3, No. 9, 2013, pp. 1209–1220',
            '方法类别：模糊自整定 PID（智能控制）',
        ],
        'oneliner': '用模糊逻辑在线自整定 PID 三个增益，使 DC 电机在动态响应与稳态精度上均优于传统定参 PID。',
    }
    body = [
        h1('一、研究背景'),
        p('DC 电机因结构简单、可靠性高、调速性能优越，长期是工业、机器人与家电的骨干。性能电机驱动系统必须具备良好的动态转速跟踪与负载调节能力。<b>PID 控制器占工业过程控制应用的 95% 以上</b>，但在 DC 电机中，饱和、摩擦等<b>非线性特性</b>会显著降低传统 PID 的性能，且精确的非线性模型难以获得。'),
        p('论文引入<b>模糊逻辑控制（FLC）</b>——它不依赖精确系统模型，仅根据人工经验的"IF-THEN"规则即可对复杂非线性系统实施控制，是与传统控制互补的新思路。'),

        h1('二、核心方法：模糊自整定 PID'),
        h2('1. DC 电机建模'),
        p('建立电枢电压方程与转矩平衡方程，经拉氏变换与简化（电气时间常数 Ta ≪ 机电时间常数 Tem），得到传递函数：'),
        quote('ω(s)/Va(s) = (1/Km) / [(1+s·Tem)(1+s·Ta)]'),
        p('电机参数：Ra=0.5Ω, La=0.02H, Va=200V, Jm=0.1 kg·m², Bm=0.008, K=1.25, 额定 1500 rpm。'),
        h2('2. 模糊控制器结构'),
        p('采用<b>双输入三输出</b>结构：'),
        bullet('<b>输入</b>：转速误差 eω(k) 与误差变化率 deω(k)。'),
        bullet('<b>输出</b>：PID 的三个增益 Kp、Ki、Kd。'),
        bullet('<b>模糊化</b>：三角隶属函数，论域分为 7 档（NL/NM/NS/ZE/PS/PM/PL），零点附近更密以提高稳态精度。'),
        bullet('<b>规则库</b>：每个增益 25 条规则（5×5），形如"IF eω is NL AND deω is NL THEN Kp is PV"。'),
        bullet('<b>推理与解模糊</b>：Max-product 推理，输出由模糊变量还原为精确量。'),
        h2('3. 自整定原理'),
        p('核心是找出 PID 三参数与 (e, de) 之间的模糊关系，在不同误差状态下<b>实时修改</b>三参数，使控制对象兼顾动态与稳态性能。稳态附近细化隶属函数以获得精细控制分辨率，远离零点处展宽以获得快速响应。'),

        h1('三、主要结果'),
        p('通过 MATLAB/Simulink 仿真对比<b>传统定参 PID</b>与<b>模糊自整定 PID</b>，结论：'),
        data_table(
            ['性能维度', '传统 PID', '模糊自整定 PID'],
            [
                ['动态响应', '一般', '更好'],
                ['上升时间 Tr', '较长', '更短'],
                ['整定时间', '较长', '更短'],
                ['最大超调 Mp', '较大', '更小'],
                ['稳态误差 SSE', '较大', '更小，精度更高'],
            ],
            col_ratios=[1.2, 1.2, 1.6]
        ),
        Spacer(1, 6),
        p('论文总结：模糊自整定 PID 同时具备<b>PID 的精确性</b>与<b>模糊控制的灵活性</b>，在瞬态与稳态两方面均优于传统 PID。'),

        h1('四、对本研究的启示'),
        bullet('<b>第三条对照路径</b>：除 PID 与 S 曲线外，模糊自整定 PID 是"反馈控制"家族中性能更强的成员。本研究若仅对比 PID vs S 曲线，可能被质疑"PID 整定不够好"；引入模糊 PID 可作为<b>强化 baseline</b>，使 S 曲线的优势结论更有说服力。'),
        bullet('<b>仍然属于"反馈"范式</b>：模糊 PID 本质仍是"误差驱动的反馈控制"，它优化的是"如何更快消除误差"，而<b>不改变参考轨迹本身的平滑性</b>。因此它无法解决"阶跃参考带来的初始 jerk"问题——这正是 S 曲线（前馈规划）的不可替代价值。'),
        bullet('<b>方法借鉴</b>：模糊规则的"零点附近细化"思想，与 S 曲线"在加减速阶段细化时间"异曲同工，都强调在关键过渡区提升分辨率。本研究可在轨迹规划层借鉴这种"非均匀精度"思想。'),
        bullet('<b>局限</b>：依赖专家经验设计规则库，可移植性受限；论文为纯仿真，无能耗分析。'),

        h1('五、文献信息'),
        quote('Bansal, U. K., & Narvey, R. (2013). Speed Control of DC Motor Using Fuzzy PID '
              'Controller. Advance in Electronic and Electric Engineering, 3(9), 1209–1220. '
              'ISSN 2231-1297.'),
    ]
    return meta, body, '模糊PID调速 (Bansal 2013)'


def paper5():
    """On Algorithms for Planning S-curve Motion Profiles (Nguyen et al., 2008)"""
    meta = {
        'num': '05',
        'title_cn': '关于 S 曲线运动轨迹规划的算法研究',
        'title_en': 'On Algorithms for Planning S-curve Motion Profiles',
        'meta_lines': [
            '作者：Kim Doang Nguyen, Teck-Chew Ng, I-Ming Chen',
            '机构：Robotics Research Center, Nanyang Technological University（新加坡）',
            '出处：International Journal of Advanced Robotic Systems, Vol. 5, No. 1, 2008, pp. 99–106',
            '方法类别：多项式 S 曲线 + 三角 S 曲线（轨迹规划算法）',
        ],
        'oneliner': '首次系统给出 n 阶多项式 S 曲线的递推广义模型与时间最优规划算法，并提出性能媲美 5 阶多项式的三角模型。',
    }
    body = [
        h1('一、研究背景与空白'),
        p('运动控制广泛应用于制造、定位、机器人等领域，其挑战始终是<b>"如何以最小振动与超调实现精确运动"</b>。梯形速度模型虽快，但加速度在切换时刻跳变导致 jerk 无穷大，会激发残余振动——这对精密系统是致命问题。'),
        p('尽管 S 曲线已有不少研究（Meckl 1998 的优化、Tsay & Lin 2005 的非对称输入、Macfarlane & Croft 2003 的在线 jerk 有界规划等），但论文指出一个关键空白：<b>此前没有人对"多项式 S 曲线的通用模型"做过系统研究</b>。本文正是填补这一空白：给出 n 阶多项式 S 曲线的<b>递推广义模型</b>，并配套<b>时间最优规划算法</b>，外加一个新颖的<b>三角模型</b>。'),

        h1('二、核心方法'),
        h2('1. 多项式 S 曲线的递推广义模型'),
        p('论文以"位置的最高阶导数（峰值有限）"为<b>模板（template）</b>，通过对模板逐次积分得到 jerk、加速度、速度、位置等运动学量。各阶模型如下：'),
        data_table(
            ['模型', '模板阶数', '轨迹段数', ' jerk 特性'],
            [
                ['梯形速度（2阶）', '2', '4', '无穷大（跳变）'],
                ['3 阶 S 曲线', '3', '8', '有限（矩形脉冲）'],
                ['4 阶 S 曲线', '4', '16', '连续'],
                ['n 阶 S 曲线', 'n', '2ⁿ', '更高阶光滑'],
            ],
            col_ratios=[1.4, 1, 1, 1.4]
        ),
        Spacer(1, 6),
        p('通过递推关系 Mn = ∫Mn₋₁，统一了任意阶多项式 S 曲线的构造。'),
        h2('2. 时间最优规划算法'),
        p('问题定义：给定各阶运动学量的峰值上限（X0_peak 位置, X1_peak 速度, …, Xn_peak），设计光滑、模板有限且不违反任何峰值的 S 曲线，并优化运动时间。'),
        p('算法核心是迭代求解各常数输入段的时间周期 Tp：先由位置峰值估算 Tp，再计算各阶最大值并与输入峰值比较；若超出则用多项式方程（仅有唯一正实根）重算 Tp，直至无峰值被违反。'),
        h2('3. 三角 jerk 模型'),
        p('提出一种新模型：用三角函数（sin）替换 3 阶 S 曲线 jerk 中的矩形脉冲，使 jerk 在整个运动期间<b>绝对光滑</b>。轨迹分 7 段，运动学量通过对 jerk 模型逐次积分得到。'),

        h1('三、实验验证'),
        p('在<b>直线电机系统</b>（气浮导轨、PMDi MC4000 Pro 八轴 DSP 控制卡、Renishaw 激光编码器反馈）上实测 3/4/5 阶多项式 S 曲线及三角模型：'),
        bullet('生成的速度与位置轨迹全程<b>光滑</b>，未违反峰值约束（速度 60 mm/s、位置 50 mm）。'),
        bullet('<b>模型阶数越高，性能越好</b>：3→4→5 阶位置误差递减。'),
        bullet('<b>三角模型</b>虽简单如 3 阶，性能却<b>媲美 5 阶多项式模型</b>——因两者的 jerk 均光滑，一阶导数仅在连接时刻有尖锐边。'),

        h1('四、对本研究的核心价值（最相关文献）'),
        bullet('<b>最直接的方法论来源</b>：本文是本研究 S 曲线轨迹规划的<b>主要算法依据</b>。其递推广义模型让我们可统一实现任意阶 S 曲线（推荐 3 阶起步，平衡光滑性与计算量），时间最优算法可直接用于移动机器人的轨迹生成。'),
        bullet('<b>jerk 有界 = 平滑性保证</b>：论文明确指出 jerk 有界是减少振动与超调的根本。本研究量化"平滑性"时，jerk 的峰值与连续性是核心指标。'),
        bullet('<b>能耗可延伸方向</b>：论文在结论中明确提到<b>未来将评估所规划运动轨迹的能耗</b>，并合理推测"光滑且 jerk 有界的运动可最优地节省能量"——这恰好是本研究的核心命题之一，可作为我们能耗分析的<b>理论引用依据</b>。'),
        bullet('<b>移动机器人适配</b>：论文将"扩展到移动机器人"列为未来工作。本研究正是把 S 曲线算法应用于移动机器人运动，是对该论文方向的直接推进。'),
        bullet('<b>三角模型选项</b>：若计算资源受限，可用三角模型以 3 阶复杂度获得 5 阶性能，是工程实现的优质折中。'),

        h1('五、文献信息'),
        quote('Nguyen, K. D., Ng, T.-C., & Chen, I.-M. (2008). On Algorithms for Planning S-curve '
              'Motion Profiles. International Journal of Advanced Robotic Systems, 5(1), 99–106. '
              'ISSN 1729-8806.'),
    ]
    return meta, body, 'S曲线规划算法 (Nguyen 2008)'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    out_dir = "D:/IPQ/summaries"
    os.makedirs(out_dir, exist_ok=True)

    papers = [
        ('01_BLDC_PID_Mahmud_2020.pdf', paper1),
        ('02_DC_Motor_PID_Hammoodi_2020.pdf', paper2),
        ('03_S_Curve_Vibration_Meckl_1998.pdf', paper3),
        ('04_Fuzzy_PID_Bansal_2013.pdf', paper4),
        ('05_S_Curve_Planning_Nguyen_2008.pdf', paper5),
    ]
    print("=" * 64)
    print("IPQ 项目 · 5 篇论文总结 PDF 生成")
    print("=" * 64)
    for fname, fn in papers:
        meta, body, title_short = fn()
        out_path = os.path.join(out_dir, fname)
        print(f"\n▶ 生成: {fname}")
        build_pdf(out_path, meta, body, title_short)
    print("\n" + "=" * 64)
    print(f"全部完成！输出目录: {out_dir}")
    print("=" * 64)


if __name__ == '__main__':
    main()
