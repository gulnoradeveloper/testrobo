"""PDF hisobot (ReportLab, A4, o‘zbekcha harflar uchun Open Sans shrifti)."""
from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..messages import DISCLAIMER, GRADCAM_NOTE, KL_REFERENCE, KL_SOURCE, LIMITATIONS, PROBABILITY_NOTE

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
PRIMARY = colors.HexColor("#123A63")
ACCENT = colors.HexColor("#1877C9")
TEXT = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#66788A")
BORDER = colors.HexColor("#E1E8F0")
FOOTER_TEXT = "Ushbu hisobot sun’iy intellekt algoritmining ilmiy-tadqiqot natijasidir. U shifokor tashxisi o‘rnini bosmaydi."
# Toshkent vaqti — UTC+5, yozgi vaqt yo‘q. Qat’iy siljish ishlatiladi: Windows’da IANA vaqt zonalari
# bazasi (tzdata) bo‘lmasligi mumkin, ZoneInfo("Asia/Tashkent") esa u yerda xato beradi.
TZ = timezone(timedelta(hours=5), "Toshkent")

_fonts_ready = False


def _register_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    pdfmetrics.registerFont(TTFont("OpenSans", str(FONT_DIR / "OpenSans-400.ttf")))
    pdfmetrics.registerFont(TTFont("OpenSans-Bold", str(FONT_DIR / "OpenSans-700.ttf")))
    pdfmetrics.registerFontFamily("OpenSans", normal="OpenSans", bold="OpenSans-Bold")
    _fonts_ready = True


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="OpenSans", fontSize=9.5, leading=13.5, textColor=TEXT)
    return {
        "brand": ParagraphStyle("brand", parent=base, fontName="OpenSans-Bold", fontSize=18, leading=22, textColor=PRIMARY),
        "title": ParagraphStyle("title", parent=base, fontName="OpenSans-Bold", fontSize=11.5, leading=15, textColor=ACCENT),
        "h2": ParagraphStyle("h2", parent=base, fontName="OpenSans-Bold", fontSize=11, leading=15, textColor=PRIMARY,
                             spaceBefore=8, spaceAfter=4),
        "body": base,
        "small": ParagraphStyle("small", parent=base, fontSize=8, leading=11, textColor=MUTED),
        "big": ParagraphStyle("big", parent=base, fontName="OpenSans-Bold", fontSize=16, leading=20, textColor=PRIMARY),
    }


def _fit_image(path: Path, max_w: float, max_h: float) -> Image:
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(max_w / w, max_h / h)
    return Image(str(path), width=w * scale, height=h * scale)


def _prob_chart(probs: list[float], labels: list[str], highlight: int) -> Drawing:
    d = Drawing(170 * mm, 40 * mm)
    ch = HorizontalBarChart()
    ch.x, ch.y, ch.width, ch.height = 18 * mm, 3 * mm, 140 * mm, 35 * mm
    ch.data = [[p * 100 for p in reversed(probs)]]
    ch.categoryAxis.categoryNames = list(reversed(labels))
    ch.categoryAxis.labels.fontName = "OpenSans"
    ch.valueAxis.valueMin, ch.valueAxis.valueMax, ch.valueAxis.valueStep = 0, 100, 20
    ch.valueAxis.labels.fontName = "OpenSans"
    ch.valueAxis.labelTextFormat = "%d%%"
    ch.bars.strokeColor = None
    ch.bars[0].fillColor = colors.HexColor("#9DB7D3")
    n = len(probs)
    ch.bars[(0, n - 1 - highlight)].fillColor = ACCENT
    d.add(ch)
    return d


def build_report(analysis: dict, original_path: Path, overlay_path: Path | None) -> bytes:
    """analysis — API javobidagi kabi lug‘at (schemas.AnalysisOut.model_dump())."""
    _register_fonts()
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=22 * mm, title="Bo‘g‘imTahlil hisoboti", author="Bo‘g‘imTahlil 1.0")
    pred = analysis["prediction"]
    created = datetime.fromisoformat(str(analysis["created_at"])).astimezone(TZ)
    model = analysis["model"]
    titles = [Paragraph("BO‘G‘IMTAHLIL", st["brand"]),
              Paragraph("TIZZA BO‘G‘IMI RENTGEN TASVIRINING SUN’IY INTELLEKT TAHLILI", st["title"])]
    logo = FONT_DIR.parent / "logo.png"
    if logo.is_file():
        head = Table([[_fit_image(logo, 30 * mm, 27 * mm), titles]], colWidths=[34 * mm, 140 * mm])
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
        flow = [head, Spacer(1, 3 * mm)]
    else:
        flow = [*titles, Spacer(1, 4 * mm)]
    meta = [
        ["Tahlil raqami", analysis["number"]],
        ["Tahlil identifikatori", analysis["id"]],
        ["Tahlil sanasi", created.strftime("%d.%m.%Y %H:%M") + " (Toshkent vaqti)"],
        ["Tasvir identifikatori", analysis["image"]["image_id"]],
        ["Tasvir o‘lchami", f"{analysis['image']['width']} × {analysis['image']['height']} piksel"],
    ]
    t = Table([[Paragraph(a, st["small"]), Paragraph(str(b), st["body"])] for a, b in meta], colWidths=[45 * mm, 129 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    flow += [t, Spacer(1, 4 * mm)]

    imgs = [_fit_image(original_path, 70 * mm, 70 * mm)]
    caps = [Paragraph("Rentgen tasviri", st["small"])]
    if overlay_path is not None and overlay_path.is_file():
        imgs.append(_fit_image(overlay_path, 70 * mm, 70 * mm))
        caps.append(Paragraph("Sun’iy intellektning rangli faollik xaritasi (Grad-CAM)", st["small"]))
    else:
        imgs.append(Paragraph("Faollik xaritasi mavjud emas.", st["small"]))
        caps.append(Paragraph("", st["small"]))
    it = Table([imgs, caps], colWidths=[87 * mm, 87 * mm])
    it.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "MIDDLE")]))
    flow += [it, Paragraph(GRADCAM_NOTE, st["small"])]

    flow += [
        Paragraph("Sun’iy intellekt bahosi", st["h2"]),
        Paragraph(f"Bashorat qilingan daraja: {pred['label']}", st["big"]),
        Paragraph(f"<b>{pred['title']}</b>", st["body"]),
        Spacer(1, 1.5 * mm),
        Paragraph(pred["description"], st["body"]),
        Paragraph(f"Manba: {KL_SOURCE} Ushbu ta’rif darajaning umumiy tavsifi bo‘lib, model aynan shu tasvirda "
                  "sanab o‘tilgan belgilarni alohida aniqlaganini bildirmaydi.", st["small"]),
    ]

    probs = analysis["probabilities"]
    rows = [[Paragraph("<b>Daraja</b>", st["body"]), Paragraph("<b>Nomlanishi</b>", st["body"]),
             Paragraph("<b>Model ehtimolligi</b>", st["body"])]]
    rows += [[p["label"], Paragraph(p["title"], st["body"]), f"{p['probability'] * 100:.1f}%"] for p in probs]
    pt = Table(rows, colWidths=[22 * mm, 102 * mm, 50 * mm])
    pt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "OpenSans"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT), ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F6F9FC")),
        ("BACKGROUND", (0, pred["kl_grade"] + 1), (-1, pred["kl_grade"] + 1), colors.HexColor("#E8F1FB")),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flow += [KeepTogether([Paragraph("Barcha darajalar bo‘yicha model ehtimolliklari", st["h2"]), pt,
                           _prob_chart([p["probability"] for p in probs], [p["label"] for p in probs], pred["kl_grade"]),
                           Paragraph(PROBABILITY_NOTE, st["small"])])]

    status_note = "" if model["training_status"] == "trained" else \
        " — DIQQAT: ushbu checkpoint o‘qitilgan model emas (test uchun), natija ma’noga ega emas"
    flow += [
        Paragraph("Model", st["h2"]),
        Paragraph(f"{model['name']} · arxitektura: {model['architecture']} · versiya: {model['version']}{status_note}",
                  st["body"]),
        Paragraph(f"Checkpoint SHA-256: {model['checkpoint_sha256']}", st["small"]),
        Paragraph("Tahlilning cheklovlari", st["h2"]),
        *[Paragraph(f"• {x}", st["body"]) for x in LIMITATIONS],
        Paragraph("Tibbiy ogohlantirish", st["h2"]),
        Paragraph(DISCLAIMER, st["body"]),
    ]

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
        canvas.setFont("OpenSans", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10.5 * mm, FOOTER_TEXT)
        canvas.drawRightString(A4[0] - 18 * mm, 6.5 * mm, f"Bo‘g‘imTahlil 1.0 · {doc_.page}-sahifa")
        canvas.restoreState()

    doc.build(flow, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
