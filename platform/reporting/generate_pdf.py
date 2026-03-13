"""
generate_pdf.py — Génération PDF rapport MCO CG CONSEIL
CG CONSEIL — Format A4 professionnel

Prend un fichier Markdown MCO et génère un PDF mis en page avec :
  - Header : CG CONSEIL | Rapport MCO | Client | Date
  - Footer : Confidentiel - CG CONSEIL | Page X/N
  - Titres en #365F91
  - Alertes 🔴/🟠/🟢 colorées
  - Police DejaVu Sans (compatible Linux/Windows)

Usage :
  python generate_pdf.py rapport_test.md
  python generate_pdf.py rapport_test.md --output mon_rapport.pdf
  python generate_pdf.py rapport_test.md --client "Twenty Two Real Estate"
"""

import argparse
import io
import re
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout (Windows cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.frames import Frame

# ── Couleurs CG CONSEIL ───────────────────────────────────────────────────────
BLUE_CG       = colors.HexColor("#365F91")
BLUE_LIGHT    = colors.HexColor("#DCE6F1")
GREY_TEXT     = colors.HexColor("#404040")
GREY_LIGHT    = colors.HexColor("#F5F5F5")
GREY_BORDER   = colors.HexColor("#CCCCCC")

RED_ALERT     = colors.HexColor("#C0392B")
ORANGE_ALERT  = colors.HexColor("#E67E22")
GREEN_OK      = colors.HexColor("#27AE60")
RED_BG        = colors.HexColor("#FDECEA")
ORANGE_BG     = colors.HexColor("#FEF3E2")
GREEN_BG      = colors.HexColor("#EAFAF1")

WHITE         = colors.white
BLACK         = colors.black

# Noms de polices globaux — mis à jour après register_fonts()
_FONT_BODY  = "Helvetica"
_FONT_BOLD  = "Helvetica-Bold"
_FONT_ITALIC= "Helvetica-Oblique"
_FONT_MONO  = "Courier"


# ── Styles ────────────────────────────────────────────────────────────────────

def build_styles(use_dejavu: bool = True) -> dict:
    """Construit les styles. Fallback Helvetica si DejaVu non disponible."""
    F  = "DejaVuSans"       if use_dejavu else "Helvetica"
    FB = "DejaVuSans-Bold"  if use_dejavu else "Helvetica-Bold"
    FI = "DejaVuSans-Oblique" if use_dejavu else "Helvetica-Oblique"
    FM = "DejaVuSansMono"   if use_dejavu else "Courier"

    return {
        "h1": ParagraphStyle(
            "h1",
            fontName=FB,
            fontSize=14,
            textColor=BLUE_CG,
            spaceAfter=4,
            spaceBefore=12,
            leading=18,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=FB,
            fontSize=11,
            textColor=BLUE_CG,
            spaceAfter=4,
            spaceBefore=10,
            leading=15,
            borderPad=4,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName=FB,
            fontSize=10,
            textColor=GREY_TEXT,
            spaceAfter=3,
            spaceBefore=6,
            leading=14,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=F,
            fontSize=9,
            textColor=GREY_TEXT,
            spaceAfter=3,
            spaceBefore=0,
            leading=13,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=F,
            fontSize=9,
            textColor=GREY_TEXT,
            spaceAfter=2,
            spaceBefore=0,
            leading=13,
            leftIndent=12,
            bulletIndent=0,
        ),
        "code": ParagraphStyle(
            "code",
            fontName=FM,
            fontSize=8,
            textColor=GREY_TEXT,
            backColor=GREY_LIGHT,
            spaceAfter=2,
            spaceBefore=2,
            leading=11,
            leftIndent=8,
        ),
        "alert_red": ParagraphStyle(
            "alert_red",
            fontName=F,
            fontSize=9,
            textColor=RED_ALERT,
            spaceAfter=2,
            leading=13,
            leftIndent=12,
        ),
        "alert_orange": ParagraphStyle(
            "alert_orange",
            fontName=F,
            fontSize=9,
            textColor=ORANGE_ALERT,
            spaceAfter=2,
            leading=13,
            leftIndent=12,
        ),
        "alert_green": ParagraphStyle(
            "alert_green",
            fontName=F,
            fontSize=9,
            textColor=GREEN_OK,
            spaceAfter=2,
            leading=13,
            leftIndent=12,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName=F,
            fontSize=7,
            textColor=colors.HexColor("#888888"),
            leading=9,
        ),
        "header_text": ParagraphStyle(
            "header_text",
            fontName=FB,
            fontSize=8,
            textColor=WHITE,
            leading=11,
            alignment=TA_CENTER,
        ),
    }


# ── Enregistrement polices DejaVu ─────────────────────────────────────────────

def register_fonts() -> bool:
    """
    Enregistre les polices DejaVu.
    Cherche dans l'ordre :
      1. C:/Windows/Fonts (Windows)
      2. /usr/share/fonts (Linux VPS Ubuntu)
      3. reportlab/fonts (bundle reportlab)
    Retourne True si les polices sont enregistrées.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab

    font_map = {
        "DejaVuSans":         "DejaVuSans.ttf",
        "DejaVuSans-Bold":    "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVuSansMono":     "DejaVuSansMono.ttf",
    }

    search_dirs = [
        Path("C:/Windows/Fonts"),                                         # Windows
        Path("/usr/share/fonts/truetype/dejavu"),                         # Ubuntu
        Path("/usr/share/fonts/dejavu"),                                  # autres Linux
        Path(reportlab.__file__).parent / "fonts",                        # bundle reportlab
    ]

    def find_font(filename: str) -> Path | None:
        for d in search_dirs:
            p = d / filename
            if p.exists():
                return p
        return None

    registered = []
    for name, filename in font_map.items():
        path = find_font(filename)
        if path:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            registered.append(name)

    if len(registered) < 2:
        return False
    return True


# ── Parsing Markdown → éléments PDF ──────────────────────────────────────────

def detect_alert_color(line: str):
    """Retourne la couleur d'alerte si la ligne contient un marqueur [CRITIQUE]/[ALERTE]/[OK]."""
    stripped = line.lstrip("- *•0123456789.").strip()
    if "[CRITIQUE]" in stripped:
        return "red"
    if "[ALERTE]" in stripped:
        return "orange"
    if "[OK]" in stripped:
        return "green"
    return None


def inline_format(text: str, bold_font: str = "", mono_font: str = "") -> str:
    """Convertit le Markdown inline (**bold**, `code`) en tags ReportLab."""
    bf = bold_font or _FONT_BOLD
    mf = mono_font or _FONT_MONO
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r'<font name="' + bf + r'">\1</font>', text)
    # `code`
    text = re.sub(r"`(.+?)`", r'<font name="' + mf + r'" color="#555555">\1</font>', text)
    # Marqueurs alertes → texte coloré gras
    text = text.replace("[CRITIQUE]", '<font name="' + bf + '" color="#C0392B">[CRITIQUE]</font>')
    text = text.replace("[ALERTE]",   '<font name="' + bf + '" color="#E67E22">[ALERTE]</font>')
    text = text.replace("[OK]",       '<font name="' + bf + '" color="#27AE60">[OK]</font>')
    return text


def parse_markdown(md_text: str, styles: dict) -> list:
    """Convertit le Markdown MCO en liste de Flowables ReportLab."""
    elements = []
    lines = md_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Ligne vide
        if not stripped:
            elements.append(Spacer(1, 3))
            i += 1
            continue

        # Séparateur horizontal ---
        if re.match(r"^-{3,}$", stripped):
            elements.append(Spacer(1, 4))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=GREY_BORDER))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # H1 — #
        if line.startswith("# ") and not line.startswith("## "):
            text = inline_format(line[2:].strip())
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(text, styles["h1"]))
            elements.append(HRFlowable(width="100%", thickness=1.5, color=BLUE_CG))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # H2 — ##
        if line.startswith("## ") and not line.startswith("### "):
            text = inline_format(line[3:].strip())
            elements.append(Spacer(1, 4))
            # Fond coloré pour H2
            tbl = Table(
                [[Paragraph(text, styles["h2"])]],
                colWidths=["100%"],
            )
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 1, BLUE_CG),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # H3 — ###
        if line.startswith("### "):
            text = inline_format(line[4:].strip())
            elements.append(Paragraph(text, styles["h3"]))
            i += 1
            continue

        # Bullet — ligne commençant par - ou *
        if re.match(r"^(\s*[-*]\s+)", line):
            content = re.sub(r"^\s*[-*]\s+", "", line)
            alert = detect_alert_color(line)
            text = inline_format(content.strip())

            if alert == "red":
                style = styles["alert_red"]
                bg = RED_BG
            elif alert == "orange":
                style = styles["alert_orange"]
                bg = ORANGE_BG
            elif alert == "green":
                style = styles["alert_green"]
                bg = GREEN_BG
            else:
                style = styles["bullet"]
                bg = None

            if bg:
                tbl = Table(
                    [[Paragraph("• " + text, style)]],
                    colWidths=["100%"],
                )
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                elements.append(tbl)
            else:
                elements.append(Paragraph("• " + text, style))
            i += 1
            continue

        # Liste numérotée — 1. 2. 3.
        if re.match(r"^\d+\.\s+", line):
            m = re.match(r"^(\d+)\.\s+(.*)", line)
            num = m.group(1)
            content = m.group(2)
            alert = detect_alert_color(line)
            text = inline_format(content.strip())

            if alert == "red":
                style = styles["alert_red"]
                bg = RED_BG
            elif alert == "orange":
                style = styles["alert_orange"]
                bg = ORANGE_BG
            elif alert == "green":
                style = styles["alert_green"]
                bg = GREEN_BG
            else:
                style = styles["bullet"]
                bg = None

            label = f"{num}. {text}"
            if bg:
                tbl = Table(
                    [[Paragraph(label, style)]],
                    colWidths=["100%"],
                )
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                elements.append(tbl)
            else:
                elements.append(Paragraph(label, style))
            i += 1
            continue

        # Italique seul (_texte_)
        if stripped.startswith("_") and stripped.endswith("_"):
            text = stripped[1:-1]
            p_style = ParagraphStyle(
                "italic_body",
                parent=styles["body"],
                fontName=_FONT_ITALIC,
                textColor=colors.HexColor("#777777"),
                fontSize=8,
            )
            elements.append(Paragraph(inline_format(text), p_style))
            i += 1
            continue

        # Paragraphe normal
        text = inline_format(stripped)
        elements.append(Paragraph(text, styles["body"]))
        i += 1

    return elements


# ── Header / Footer callbacks ─────────────────────────────────────────────────

class CGConseilDocTemplate(SimpleDocTemplate):
    """Template avec header et footer personnalisés."""

    def __init__(self, filename, client, date_str, report_title, **kwargs):
        super().__init__(filename, **kwargs)
        self.client = client
        self.date_str = date_str
        self.report_title = report_title

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def afterPage(self):
        pass

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        margin_left = 2 * cm
        margin_right = w - 2 * cm
        content_width = margin_right - margin_left

        # ── HEADER ──────────────────────────────────────────────
        header_h = 1.1 * cm
        header_y = h - 1.5 * cm

        # Fond bleu
        canvas.setFillColor(BLUE_CG)
        canvas.rect(margin_left, header_y, content_width, header_h, fill=1, stroke=0)

        # Texte header en 3 colonnes
        canvas.setFillColor(WHITE)
        canvas.setFont(_FONT_BOLD, 8)
        col_w = content_width / 3

        canvas.drawString(margin_left + 6, header_y + 0.35 * cm, "CG CONSEIL")
        canvas.setFont(_FONT_BODY, 8)

        # Centré : titre rapport
        title_x = margin_left + col_w
        canvas.drawCentredString(title_x + col_w / 2, header_y + 0.35 * cm, self.report_title)

        # Droite : client + date
        right_text = f"{self.client}  |  {self.date_str}"
        canvas.drawRightString(margin_right - 6, header_y + 0.35 * cm, right_text)

        # ── FOOTER ──────────────────────────────────────────────
        footer_y = 1.0 * cm

        canvas.setStrokeColor(BLUE_CG)
        canvas.setLineWidth(0.5)
        canvas.line(margin_left, footer_y + 0.35 * cm, margin_right, footer_y + 0.35 * cm)

        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.setFont(_FONT_BODY, 7)
        canvas.drawString(margin_left, footer_y + 0.1 * cm, "Confidentiel — CG CONSEIL")
        canvas.drawRightString(
            margin_right,
            footer_y + 0.1 * cm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    def handle_pageEnd(self):
        self._draw_header_footer(self.canv, self)
        super().handle_pageEnd()


# ── Génération PDF ────────────────────────────────────────────────────────────

def generate_pdf(
    md_path: Path,
    pdf_path: Path,
    client: str = "Twenty Two Real Estate",
    report_title: str = "Rapport MCO",
    date_str: str | None = None,
) -> None:
    if date_str is None:
        date_str = datetime.now().strftime("%d/%m/%Y")

    # Enregistrement polices
    global _FONT_BODY, _FONT_BOLD, _FONT_ITALIC, _FONT_MONO
    fonts_ok = register_fonts()
    if fonts_ok:
        _FONT_BODY   = "DejaVuSans"
        _FONT_BOLD   = "DejaVuSans-Bold"
        _FONT_ITALIC = "DejaVuSans-Oblique"
        _FONT_MONO   = "DejaVuSansMono"
        print("Polices : DejaVu Sans")
    else:
        print("INFO: Polices DejaVu non trouvees — fallback Helvetica/Courier")

    # Lecture Markdown + normalisation emojis → marqueurs ASCII
    md_text = md_path.read_text(encoding="utf-8")
    md_text = md_text.replace("🔴", "[CRITIQUE]")
    md_text = md_text.replace("🟠", "[ALERTE]")
    md_text = md_text.replace("🟢", "[OK]")

    # Styles
    styles = build_styles(use_dejavu=fonts_ok)

    # Marges : top élargi pour header, bottom pour footer
    doc = CGConseilDocTemplate(
        str(pdf_path),
        client=client,
        date_str=date_str,
        report_title=report_title,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=3.0 * cm,
        bottomMargin=2.0 * cm,
        title=f"{report_title} — {client}",
        author="CG CONSEIL — Christian Grau",
        subject="Rapport MCO NetApp",
        creator="CG CONSEIL Reporting Platform",
    )

    # Parsing
    elements = parse_markdown(md_text, styles)

    # Génération
    doc.build(elements)
    print(f"PDF généré : {pdf_path}")
    print(f"Taille     : {pdf_path.stat().st_size:,} octets")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Génération PDF rapport MCO CG CONSEIL"
    )
    parser.add_argument("input", help="Fichier Markdown source (.md)")
    parser.add_argument("--output", help="Fichier PDF de sortie (défaut: même nom .pdf)")
    parser.add_argument(
        "--client", default="Twenty Two Real Estate",
        help="Nom du client pour le header"
    )
    parser.add_argument(
        "--title", default="Rapport MCO",
        help="Titre du rapport pour le header"
    )
    parser.add_argument(
        "--date", default=None,
        help="Date du rapport (défaut: aujourd'hui DD/MM/YYYY)"
    )
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"Erreur : fichier introuvable : {md_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        pdf_path = Path(args.output)
    else:
        pdf_path = md_path.with_suffix(".pdf")

    generate_pdf(
        md_path=md_path,
        pdf_path=pdf_path,
        client=args.client,
        report_title=args.title,
        date_str=args.date,
    )


if __name__ == "__main__":
    main()
