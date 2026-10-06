"""Gera o portfólio em PDF (A4) a partir dos README.md dos projetos.

Uso:  python tools/gerar_pdf.py [caminho/saida.pdf]
Requer: pip install reportlab pymupdf pillow resvg-py
"""
import io
import pathlib
import re
import sys
import tempfile

import pymupdf as fitz
from PIL import Image as PILImage
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://gustavosilvestre874.github.io/portfolio-engenharia-civil/"
NOME = "Gustavo Rodrigo Silvestre da Silva"
EMAIL = "gustavorodrigosilvestre@gmail.com"
LINKEDIN = "linkedin.com/in/gustavo-silvestre-0649b1244"

# Mesma ordem e resumos dos cartões do site
PROJETOS = [
    ("projetos/sistemas-prediais/climatizacao-hvac-escritorio-brasilia", "Sistemas prediais · Poli-USP · 2026",
     "Climatização (HVAC) de escritório em Brasília", "assets/img/hvac.png",
     "Carga térmica de 66.276 W, 2 UTAs por andar, chiller de água gelada, dutos e diagrama unifilar."),
    ("projetos/projeto-completo/chacara-igarata", "Projeto completo · Profissional · 2025",
     "Chácara em Igaratá", "assets/img/igarata.jpg",
     "Residência de 117,75 m²: projeto arquitetônico, estrutural preliminar e esgoto sanitário."),
    ("projetos/arquitetura/residencia-unifamiliar-ifsp", "Arquitetura · IFSP",
     "Residência unifamiliar", "assets/img/residencia-ifsp.jpg",
     "Do programa de necessidades ao detalhamento, em 11 pranchas: plantas, fachadas, cortes, áreas molhadas, implantação e estrutura."),
    ("projetos/arquitetura/reforma-de-cozinha", "Interiores · Profissional · 2024",
     "Reforma de cozinha", "assets/img/cozinha.jpg",
     "Executivo em 12 folhas: 3D, plantas e vistas, marcenaria detalhada, quantitativo e marmoraria."),
    ("projetos/design-biofilico/escritorio-com-vista-para-jardim", "Design biofílico · Estudo pessoal",
     "Escritório com vista para o jardim", "assets/img/escritorio-jardim.jpg",
     "Home office com uma grande abertura para o jardim, baseado em estudos que associam a natureza a mais calma e concentração."),
    ("projetos/design-biofilico/dormitorio-para-descansar", "Design biofílico · Estudo pessoal",
     "Dormitório para descansar", "assets/img/dormitorio.jpg",
     "Quarto pensado para o descanso: luz quente e indireta, madeira, uma paisagem como ponto focal e tudo organizado."),
    ("projetos/arquitetura/condominio-residencial", "Arquitetura · 2024",
     "Condomínio residencial", "assets/img/condominio.jpg",
     "Planta humanizada de pavimento-tipo com duas unidades, modelada em Revit."),
    ("projetos/topografia/levantamento-topografico-poli-usp", "Topografia · Poli-USP · 2024",
     "Levantamento topográfico", "assets/img/topografia.jpg",
     "Trabalho em grupo: poligonal de 5.693 m² com 432 pontos de detalhe na Cidade Universitária."),
    ("projetos/desenho-tecnico/desenho-construcao-civil-ifsp", "Desenho técnico · IFSP · 2022",
     "Desenho de Construção Civil", "assets/img/desenho-construcao-civil.jpg",
     "Quatro pranchas de uma residência: plantas, cortes e gradil, vistas, detalhes e tabelas de esquadrias."),
    ("projetos/desenho-tecnico/escada-e-rampas-ifsp", "Desenho técnico · IFSP · 2021",
     "Escada e rampas", "assets/img/rampas.jpg",
     "Corte de escada (1:25) e estudo de rampas acessíveis (1:50)."),
]

# ---------- Visual ----------
NAVY = colors.HexColor("#0f2a44")
ORANGE = colors.HexColor("#e8833a")
ORANGE_INK = colors.HexColor("#b45a17")
TEXT = colors.HexColor("#141a22")
MUTED = colors.HexColor("#5a6473")
LINE = colors.HexColor("#e2e6ec")
CHIP = colors.HexColor("#edf1f6")

FONTS = pathlib.Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("UI", str(FONTS / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("UI-B", str(FONTS / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("UI-SB", str(FONTS / "seguisb.ttf")))
pdfmetrics.registerFont(TTFont("UI-I", str(FONTS / "segoeuii.ttf")))
pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-B", italic="UI-I", boldItalic="UI-B")

PAGE_W, PAGE_H = A4
M = 18 * mm
CW = PAGE_W - 2 * M  # largura útil

S = {
    "body": ParagraphStyle("body", fontName="UI", fontSize=9.6, leading=14, textColor=TEXT, spaceAfter=5),
    "muted": ParagraphStyle("muted", fontName="UI", fontSize=9, leading=13, textColor=MUTED),
    "h1": ParagraphStyle("h1", fontName="UI-B", fontSize=22, leading=27, textColor=TEXT, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="UI-B", fontSize=13.5, leading=18, textColor=TEXT, spaceBefore=12, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="UI-SB", fontSize=11, leading=15, textColor=TEXT, spaceAfter=4),
    "eyebrow": ParagraphStyle("eyebrow", fontName="UI-B", fontSize=8, leading=11, textColor=ORANGE_INK),
    "cell": ParagraphStyle("cell", fontName="UI", fontSize=8.8, leading=12, textColor=TEXT),
    "cellh": ParagraphStyle("cellh", fontName="UI-B", fontSize=7.6, leading=10, textColor=MUTED),
    "quote": ParagraphStyle("quote", fontName="UI-I", fontSize=8.8, leading=12.5, textColor=MUTED),
    "caption": ParagraphStyle("caption", fontName="UI", fontSize=7.8, leading=10, textColor=MUTED),
}

TMP = pathlib.Path(tempfile.mkdtemp(prefix="pdf_portfolio_"))


# ---------- Imagens ----------
def preparar_imagem(path, max_px=1700):
    """Reduz e converte para JPEG/PNG leve; SVG é rasterizado. Devolve (arquivo, largura, altura)."""
    path = pathlib.Path(path)
    out = TMP / (re.sub(r"\W", "_", str(path.relative_to(ROOT))) + ".png")
    if path.suffix.lower() == ".svg":
        try:  # resvg desenha degradês corretamente (ícones do Office)
            import resvg_py
            out.write_bytes(bytes(resvg_py.svg_to_bytes(svg_path=str(path), width=256)))
        except Exception:
            doc = fitz.open(path)
            page = doc[0]
            zoom = 256 / max(page.rect.width, page.rect.height)
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True).save(out)
        im = PILImage.open(out)
        return str(out), im.width, im.height
    im = PILImage.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = PILImage.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((max_px, max_px))
    out = out.with_suffix(".jpg")
    im.save(out, quality=85, optimize=True)
    return str(out), im.width, im.height


def imagem(path, max_w, max_h, moldura=True):
    arq, w, h = preparar_imagem(path)
    esc = min(max_w / w, max_h / h)
    img = Image(arq, width=w * esc, height=h * esc)
    if not moldura:
        return img
    t = Table([[img]], colWidths=[w * esc + 8])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


# ---------- Markdown -> flowables ----------
def inline(txt):
    txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", txt)
    txt = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", txt)
    txt = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", txt)
    return txt


def ler_readme(pasta):
    md = (pasta / "README.md").read_text(encoding="utf-8")
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    linhas = md.splitlines()
    titulo = next(l[2:].strip() for l in linhas if l.startswith("# "))
    meta, corpo, capa = [], [], None
    for l in linhas:
        if l.startswith("# "):
            continue
        m = re.match(r"^\*\*(.+?):\*\*\s*(.*?)\s*$", l)
        if m and not corpo:
            if m.group(2):
                meta.append((m.group(1), m.group(2)))
            continue
        im = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", l)
        if im and capa is None:
            capa = im.group(2)
            continue
        if corpo or l.strip():
            corpo.append(l)
    texto = "\n".join(corpo)
    texto = re.split(r"^## Arquivos\s*$", texto, flags=re.M)[0]  # arquivos ficam no site
    return titulo, meta, capa, texto


def tabela_md(linhas, pasta):
    rows = []
    for l in linhas:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    if not rows:
        return None
    so_imagens = all(re.fullmatch(r"!\[.*?\]\(.+?\)", c) or not c for r in rows for c in r)
    ncol = max(len(r) for r in rows)
    colw = CW / ncol
    data = []
    for i, r in enumerate(rows):
        linha = []
        for c in r + [""] * (ncol - len(r)):
            im = re.fullmatch(r"!\[.*?\]\((.+?)\)", c)
            if im:
                linha.append(imagem(pasta / im.group(1), colw - 14, 150, moldura=False))
            else:
                linha.append(Paragraph(inline(c), S["cellh"] if (i == 0 and not so_imagens) else S["cell"]))
        data.append(linha)
    if so_imagens:
        data = [d for d in data if any(not isinstance(x, Paragraph) or x.text for x in d)]
    t = Table(data, colWidths=[colw] * ncol, repeatRows=0 if so_imagens else 1)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 7)]
    if not so_imagens:
        st += [("BACKGROUND", (0, 0), (-1, 0), CHIP), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
               ("BOX", (0, 0), (-1, -1), 0.6, LINE)]
    t.setStyle(TableStyle(st))
    return t


def md_flowables(md, pasta):
    out, linhas, i = [], md.splitlines(), 0
    item = re.compile(r"^(\s*)(?:[-*]|\d+\.)\s+(.*)$")
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("## "):
            out.append(CondPageBreak(60))
            out.append(SectionTitle(l[3:].strip()))
            i += 1
        elif l.startswith("### "):
            out.append(Paragraph(inline(l[4:]), S["h3"]))
            i += 1
        elif l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i]); i += 1
            t = tabela_md(bloco, pasta)
            if t:
                out += [Spacer(1, 3), KeepTogether([t]) if len(bloco) <= 14 else t, Spacer(1, 8)]
        elif l.startswith(">"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith(">"):
                bloco.append(linhas[i].lstrip("> ")); i += 1
            q = Table([[Paragraph(inline(" ".join(bloco)), S["quote"])]], colWidths=[CW])
            q.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CHIP), ("LINEBEFORE", (0, 0), (0, -1), 2.5, ORANGE),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            out += [q, Spacer(1, 8)]
        elif re.match(r"^!\[.*?\]\(.+?\)\s*$", l):
            src = re.match(r"^!\[.*?\]\((.+?)\)", l).group(1)
            out += [Spacer(1, 4), imagem(pasta / src, CW, 250), Spacer(1, 8)]
            i += 1
        elif item.match(l):
            while i < len(linhas) and (item.match(linhas[i]) or (linhas[i].startswith("  ") and linhas[i].strip())):
                m = item.match(linhas[i])
                if m:
                    nivel = len(m.group(1)) // 2
                    st = ParagraphStyle("li", parent=S["body"], leftIndent=12 + 12 * nivel, bulletIndent=2 + 12 * nivel,
                                        spaceAfter=2.5)
                    marca = "•" if nivel == 0 else "–"
                    out.append(Paragraph(inline(m.group(2)), st, bulletText=marca))
                i += 1
            out.append(Spacer(1, 4))
        else:
            par = [l.strip()]
            i += 1
            while i < len(linhas) and linhas[i].strip() and not re.match(r"^(#|\||>|!\[|\s*[-*]\s|\s*\d+\.\s)", linhas[i]):
                par.append(linhas[i].strip()); i += 1
            out.append(Paragraph(inline(" ".join(par)), S["body"]))
    return out


# ---------- Elementos visuais ----------
class SectionTitle(Flowable):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.height = 26

    def wrap(self, aw, ah):
        return aw, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(ORANGE)
        c.roundRect(0, 6, 3.5, 13, 1.5, fill=1, stroke=0)
        c.setFillColor(TEXT)
        c.setFont("UI-B", 13.5)
        c.drawString(11, 8, self.text)


class ProjectHeader(Flowable):
    """Faixa azul com categoria, título e etiquetas do projeto."""
    def __init__(self, categoria, titulo, meta):
        super().__init__()
        self.cat, self.titulo, self.meta = categoria, titulo, meta

    def wrap(self, aw, ah):
        self.width = aw
        self.p = Paragraph(inline(self.titulo),
                           ParagraphStyle("pt", fontName="UI-B", fontSize=19, leading=23, textColor=colors.white))
        _, ph = self.p.wrap(aw - 36, ah)
        self.ph = ph
        self.height = ph + 76
        return aw, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        grade(c, 0, 0, self.width, self.height, clip_round=10)
        c.setFillColor(ORANGE)
        c.rect(18, self.height - 25, 16, 1.4, fill=1, stroke=0)
        c.setFont("UI-B", 7.8)
        c.drawString(40, self.height - 27.5, self.cat.upper())
        self.p.drawOn(c, 18, self.height - 38 - self.ph)
        x, y = 18, 14
        c.setFont("UI", 7.6)
        for _, v in self.meta:
            w = pdfmetrics.stringWidth(v, "UI", 7.6) + 14
            if x + w > self.width - 18:
                break
            c.setFillColor(colors.Color(1, 1, 1, alpha=0.12))
            c.roundRect(x, y, w, 15, 7.5, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.drawString(x + 7, y + 4.5, v)
            x += w + 6


def grade(c, x, y, w, h, clip_round=0):
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, clip_round) if clip_round else p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)
    for passo, alpha in ((12, 0.03), (48, 0.06)):
        c.setStrokeColor(colors.Color(1, 1, 1, alpha=alpha))
        c.setLineWidth(0.5)
        gx = x
        while gx <= x + w:
            c.line(gx, y, gx, y + h); gx += passo
        gy = y
        while gy <= y + h:
            c.line(x, gy, x + w, gy); gy += passo
    c.restoreState()


def planta(c, ox, oy, esc):
    """Mesma planta baixa do topo do site (coordenadas do SVG 800 x 560, y para baixo)."""
    X = lambda v: ox + v * esc
    Y = lambda v: oy - v * esc

    def ln(pts, cor, alpha, lw):
        c.setStrokeColor(colors.Color(*cor, alpha=alpha)); c.setLineWidth(lw)
        p = c.beginPath(); p.moveTo(X(pts[0][0]), Y(pts[0][1]))
        for px, py in pts[1:]:
            p.lineTo(X(px), Y(py))
        c.drawPath(p, stroke=1, fill=0)

    def rect(x, y, w, h, cor, alpha, lw):
        ln([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], cor, alpha, lw)

    def arco(cx, cy, r, a0, a1, alpha):
        c.setStrokeColor(colors.Color(1, 1, 1, alpha=alpha)); c.setLineWidth(0.7)
        c.arc(X(cx - r), Y(cy + r), X(cx + r), Y(cy - r), a0, a1 - a0)

    W, O = (1, 1, 1), (0.94, 0.58, 0.31)
    for x in (140, 380, 640):
        ln([(x, 54), (x, 520)], W, .18, .5)
    for y in (130, 330, 470):
        ln([(74, y), (730, y)], W, .18, .5)
    c.setFont("UI-SB", 7)
    for (cx, cy, t) in ((140, 40, "A"), (380, 40, "B"), (640, 40, "C"), (60, 130, "1"), (60, 330, "2"), (60, 470, "3")):
        c.setStrokeColor(colors.Color(1, 1, 1, alpha=.35)); c.setLineWidth(.6)
        c.circle(X(cx), Y(cy), 14 * esc, stroke=1, fill=0)
        c.setFillColor(colors.Color(1, 1, 1, alpha=.6)); c.drawCentredString(X(cx), Y(cy) - 2.4, t)
    rect(140, 130, 500, 340, W, .85, 1.2); rect(150, 140, 480, 320, W, .85, 1.2)
    for seg in (((375, 140), (375, 320)), ((385, 140), (385, 320)), ((150, 325), (520, 325)), ((150, 335), (515, 335)),
                ((515, 335), (515, 460)), ((525, 335), (525, 460)), ((520, 325), (630, 325))):
        ln(list(seg), W, .85, 1.2)
    for seg in (((210, 133), (300, 133)), ((210, 137), (300, 137)), ((450, 133), (560, 133)), ((450, 137), (560, 137)),
                ((143, 200), (143, 280)), ((147, 200), (147, 280)), ((637, 180), (637, 280)), ((633, 180), (633, 280)),
                ((385, 250), (425, 250)), ((300, 335), (300, 375)), ((420, 470), (420, 430))):
        ln(list(seg), W, .55, .7)
    arco(385, 250, 40, 270, 360, .55); arco(300, 335, 40, 180, 270, .55); arco(420, 470, 40, 0, 90, .55)
    rect(535, 345, 88, 105, W, .55, .7)
    for x in (547, 559, 571, 583, 595, 607):
        ln([(x, 345), (x, 450)], W, .5, .6)
    ln([(541, 398), (617, 398)], W, .55, .7); ln([(607, 391), (617, 398), (607, 405)], W, .55, .7)
    c.setStrokeColor(colors.Color(1, 1, 1, alpha=.55)); c.circle(X(510), Y(232), 34 * esc, stroke=1, fill=0)
    ln([(160, 150), (160, 300), (190, 300), (190, 180), (330, 180), (330, 150)], W, .55, .7)
    rect(180, 360, 80, 90, W, .55, .7); ln([(180, 380), (260, 380)], W, .55, .7)
    for seg in (((140, 120), (140, 88)), ((380, 120), (380, 88)), ((640, 120), (640, 88)), ((134, 95), (646, 95)),
                ((130, 130), (96, 130)), ((130, 330), (96, 330)), ((130, 470), (96, 470)), ((103, 124), (103, 476)),
                ((134, 505), (646, 505)), ((140, 480), (140, 512)), ((640, 480), (640, 512))):
        ln(list(seg), O, .9, .7)
    c.setFillColor(colors.Color(*O, alpha=.95)); c.setFont("UI-SB", 6.6)
    for (tx, ty, t) in ((260, 88, "4,80"), (510, 88, "5,20"), (390, 525, "10,00")):
        c.drawCentredString(X(tx), Y(ty), t)
    c.setFillColor(colors.Color(1, 1, 1, alpha=.75)); c.setFont("UI-SB", 7)
    for (tx, ty, t, a) in ((262, 250, "SALA", "18,40 m²"), (510, 290, "COZINHA", "12,60 m²"),
                           (340, 405, "DORMITÓRIO", "10,20 m²")):
        c.drawCentredString(X(tx), Y(ty), t)
        c.setFont("UI", 6); c.drawCentredString(X(tx), Y(ty + 16), a); c.setFont("UI-SB", 7)


# ---------- Páginas ----------
def capa(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    grade(c, 0, 0, PAGE_W, PAGE_H)
    c.setFillColor(ORANGE)
    c.rect(M, PAGE_H - 62 * mm, 22, 1.6, fill=1, stroke=0)
    c.setFont("UI-B", 9.5)
    c.drawString(M + 30, PAGE_H - 62 * mm - 3, "PORTFÓLIO · ENGENHARIA CIVIL")
    c.setFillColor(colors.white)
    c.setFont("UI-B", 34)
    c.drawString(M, PAGE_H - 80 * mm, "Gustavo Rodrigo")
    c.drawString(M, PAGE_H - 94 * mm, "Silvestre da Silva")
    p = Paragraph("Estudante de Engenharia Civil na Escola Politécnica da USP e Técnico em Edificações pelo IFSP. "
                  "Projetos executivos, modelagem BIM e desenho técnico em arquitetura, sistemas prediais, "
                  "estruturas e topografia.",
                  ParagraphStyle("lead", fontName="UI", fontSize=11.5, leading=17, textColor=colors.Color(1, 1, 1, .8)))
    _, h = p.wrap(CW * 0.82, 200)
    p.drawOn(c, M, PAGE_H - 104 * mm - h)
    esc = CW / 800
    planta(c, M, PAGE_H - 150 * mm, esc)
    c.setFillColor(colors.Color(1, 1, 1, .75))
    c.setFont("UI", 9)
    c.drawString(M, 22 * mm, EMAIL)
    c.drawString(M, 17 * mm, LINKEDIN)
    c.setFillColor(ORANGE)
    c.drawString(M, 12 * mm, SITE.replace("https://", ""))
    c.restoreState()


def rodape(c, doc):
    c.saveState()
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, 13 * mm, PAGE_W - M, 13 * mm)
    c.setFont("UI", 7.5)
    c.setFillColor(MUTED)
    c.drawString(M, 9 * mm, f"{NOME} · Portfólio de Engenharia Civil")
    c.drawRightString(PAGE_W - M, 9 * mm, f"{doc.page}")
    c.restoreState()


def bloco(titulo, conteudo, largura):
    t = Table([[Paragraph(titulo, S["h3"])]] + [[x] for x in conteudo], colWidths=[largura])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (0, 0), 11), ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
                           ("TOPPADDING", (0, 1), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -2), 3)]))
    return KeepTogether([t])


SOBRE_MIM = [
    "Sou estudante de Engenharia Civil na Escola Politécnica da USP, onde entrei em 2024, e Técnico em Edificações pelo "
    "IFSP desde 2022. Minha trajetória na construção civil começou no curso técnico: lá me qualifiquei como Desenhista de "
    "Construção Civil e Inspetor de Obras, e fui bolsista de monitoria em Sistemas Prediais Hidráulicos e Sanitários, "
    "elaborando projetos e ajudando alunos de Engenharia e do Técnico no AutoCAD.",
    "Desde então, desenvolvo projetos acadêmicos e para clientes, da arquitetura aos sistemas prediais, passando por "
    "estrutura e topografia. Tenho facilidade com projetos executivos e com o fluxo de trabalho BIM.",
    "Sou comunicativo, organizado e detalhista, e gosto de aprender coisas novas. Busco uma oportunidade na construção "
    "civil onde eu possa aprender e contribuir com a equipe.",
]


def pagina_sobre_mim():
    foto = imagem(ROOT / "assets/img/foto-gustavo.jpg", 150, 150, moldura=False)
    texto = [Paragraph(t, S["body"]) for t in SOBRE_MIM]
    texto.append(Paragraph("São Paulo – SP · Poli-USP · Técnico em Edificações (IFSP) · Espanhol avançado · Inglês intermediário",
                           ParagraphStyle("chips", parent=S["muted"], textColor=ORANGE_INK)))
    t = Table([[foto, texto]], colWidths=[165, CW - 165])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, 0), 15)]))
    return [Paragraph("SOBRE MIM", S["eyebrow"]), Spacer(1, 3), Paragraph("Quem sou", S["h1"]), t, Spacer(1, 22)]


def pagina_sobre():
    out = [Paragraph("SOBRE", S["eyebrow"]), Spacer(1, 3), Paragraph("Formação e habilidades", S["h1"])]
    logos = ROOT / "assets/img/logos"

    def formacao(logo, titulo, linhas):
        img = imagem(logos / logo, 40, 40, moldura=False)
        cx = Table([[img]], colWidths=[50], rowHeights=[50])
        cx.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        txt = [Paragraph(f"<b>{titulo}</b>", S["body"])] + [Paragraph(l, S["muted"]) for l in linhas]
        t = Table([[cx, txt]], colWidths=[60, CW - 24 - 60])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        return t

    out.append(bloco("Formação", [
        formacao("poli-usp.png", "Engenharia Civil", ["Escola Politécnica da USP · ingresso em 2024"]),
        formacao("ifsp.svg", "Técnico em Edificações", [
            "IFSP – Campus São Paulo · concluído em 2022",
            "Qualificações: Desenhista de Construção Civil (955,30 horas) e Inspetor de Obras (898,20 horas)"]),
    ], CW))
    out.append(Spacer(1, 12))
    out.append(bloco("Experiência", [
        Paragraph("<b>Bolsista de monitoria em Sistemas Prediais Hidráulicos e Sanitários Residenciais</b> · IFSP, "
                  "03/2022 – 12/2022", S["body"]),
        Paragraph("• Elaboração de projetos<br/>• Apoio a alunos de Engenharia e do curso Técnico no uso do AutoCAD",
                  S["muted"]),
        Spacer(1, 4),
        Paragraph("<b>Projetos como técnico em edificações</b>: projetos residenciais para clientes "
                  "(Chácara Igaratá e Reforma de cozinha)", S["body"]),
    ], CW))
    out.append(Spacer(1, 12))

    softwares = [("revit-icone.svg", "Revit Architecture"), ("revit-icone.svg", "Revit MEP"),
                 ("autocad-icone.svg", "AutoCAD"), ("inventor-icone.svg", "Inventor"), ("sketchup-icone.svg", "SketchUp"), ("vray-icone.png", "V-Ray"), ("excel.svg", "Excel"),
                 ("word.svg", "Word"), ("powerpoint.svg", "PowerPoint")]
    linhas_sw, linha = [], []
    for logo, nome in softwares:
        linha.append(Table([[imagem(logos / logo, 14, 14, moldura=False) if logo else "", Paragraph(nome, S["cell"])]],
                           colWidths=[20, 100], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                                       ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        if len(linha) == 3:
            linhas_sw.append(linha); linha = []
    if linha:
        linhas_sw.append(linha + [""] * (3 - len(linha)))
    grid = Table(linhas_sw, colWidths=[(CW - 24) / 3] * 3)
    grid.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    out.append(bloco("Softwares", [grid], CW))
    out.append(Spacer(1, 12))
    conhecimentos = ["Projeto arquitetônico: do programa de necessidades ao executivo",
                     "Cálculo de carga térmica e projeto de climatização (ABNT NBR 16401, ASHRAE Handbook)",
                     "Instalações hidrossanitárias (esgoto)",
                     "Concepção estrutural de residências (fundações, vigas, pilares)",
                     "Levantamento topográfico e planta planialtimétrica",
                     "Projeto de interiores e marcenaria", "Design biofílico: natureza e bem-estar nos ambientes", "Espanhol avançado", "Inglês intermediário"]
    out.append(bloco("Conhecimentos", [Paragraph("<br/>".join("• " + k for k in conhecimentos), S["muted"])], CW))
    return out


def pagina_sumario():
    out = [Paragraph("PROJETOS", S["eyebrow"]), Spacer(1, 3), Paragraph("Sumário de projetos", S["h1"]),
           Paragraph(f"Os arquivos completos de cada projeto (PDFs, planilhas e vídeos) estão disponíveis no portfólio "
                     f"online: <font color='#b45a17'>{SITE.replace('https://', '')}</font>", S["muted"]), Spacer(1, 10)]
    gap = 10
    cw = (CW - 2 * gap) / 3
    cards = []
    for i, (rel, cat, titulo, thumb, resumo) in enumerate(PROJETOS, 1):
        img = imagem(ROOT / thumb, cw - 16, 82, moldura=False)
        corpo = [img, Spacer(1, 6), Paragraph(cat.upper(), S["eyebrow"]),
                 Paragraph(f"<b>{i:02d} · {titulo}</b>", S["h3"]), Paragraph(resumo, S["muted"])]
        t = Table([[corpo]], colWidths=[cw], rowHeights=[200])
        t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                               ("TOPPADDING", (0, 0), (-1, -1), 8), ("BACKGROUND", (0, 0), (-1, -1), colors.white)]))
        cards.append(t)
    linhas = [cards[i:i + 3] + [""] * (3 - len(cards[i:i + 3])) for i in range(0, len(cards), 3)]
    g = Table(linhas, colWidths=[cw + gap, cw + gap, cw])
    g.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(g)
    return out


def paginas_projeto(rel, cat):
    pasta = ROOT / rel
    titulo, meta, capa_img, md = ler_readme(pasta)
    out = [ProjectHeader(cat, titulo, meta), Spacer(1, 12)]
    if capa_img:
        out += [imagem(pasta / capa_img, CW, 200), Spacer(1, 6)]
    out += md_flowables(md, pasta)
    # Galeria: imagens da pasta que não aparecem no texto (até 6)
    usados = set(re.findall(r"\]\((imagens/[^)]+)\)", (pasta / "README.md").read_text(encoding="utf-8")))
    extras = [p for p in sorted((pasta / "imagens").glob("*")) if p.suffix.lower() in (".png", ".jpg", ".jpeg")
              and f"imagens/{p.name}" not in usados][:6] if (pasta / "imagens").exists() else []
    if extras:
        out += [CondPageBreak(200), SectionTitle("Galeria")]
        cw = (CW - 10) / 2
        cells = [imagem(p, cw - 10, 150) for p in extras]
        linhas = [cells[i:i + 2] + [""] * (2 - len(cells[i:i + 2])) for i in range(0, len(cells), 2)]
        g = Table(linhas, colWidths=[cw + 10, cw])
        g.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        out.append(g)
    out.append(PageBreak())
    return out


def pagina_contato():
    qr = QrCodeWidget(SITE)
    b = qr.getBounds()
    tam = 110
    d = Drawing(tam, tam, transform=[tam / (b[2] - b[0]), 0, 0, tam / (b[3] - b[1]), 0, 0])
    d.add(qr)
    texto = [Paragraph("CONTATO", ParagraphStyle("e2", parent=S["eyebrow"], textColor=ORANGE)), Spacer(1, 4),
             Paragraph("Vamos conversar?", ParagraphStyle("c1", fontName="UI-B", fontSize=22, leading=27,
                                                          textColor=colors.white)),
             Spacer(1, 4),
             Paragraph("Em busca de oportunidades na área da construção civil.",
                       ParagraphStyle("c2", fontName="UI", fontSize=10.5, leading=15, textColor=colors.Color(1, 1, 1, .8))),
             Spacer(1, 12)]
    st = ParagraphStyle("c3", fontName="UI", fontSize=10, leading=17, textColor=colors.white)
    texto += [Paragraph(f"<b>E-mail:</b> {EMAIL}", st), Paragraph(f"<b>LinkedIn:</b> {LINKEDIN}", st),
              Paragraph(f"<b>Portfólio online:</b> <font color='#f0954f'>{SITE.replace('https://', '')}</font>", st)]
    qr_box = Table([[d], [Paragraph("Aponte a câmera para abrir o portfólio online", ParagraphStyle(
        "c4", fontName="UI", fontSize=7.5, leading=10, textColor=MUTED, alignment=1))]], colWidths=[130])
    qr_box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.white), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    t = Table([[texto, qr_box]], colWidths=[CW - 160, 160])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 22), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                           ("TOPPADDING", (0, 0), (-1, -1), 26), ("BOTTOMPADDING", (0, 0), (-1, -1), 26),
                           ("ROUNDEDCORNERS", [10, 10, 10, 10])]))
    nota = Paragraph("© 2026 Gustavo Rodrigo Silvestre da Silva. Todos os direitos reservados: é permitido visualizar e "
                     "citar com crédito. Projetos de clientes foram anonimizados; trabalhos em grupo estão identificados "
                     "como tal.", S["caption"])
    return [Spacer(1, 120), t, Spacer(1, 18), nota]


def gerar(saida):
    doc = BaseDocTemplate(str(saida), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=20 * mm,
                          title="Portfólio – Gustavo Rodrigo Silvestre da Silva", author=NOME,
                          subject="Portfólio de Engenharia Civil")
    frame = Frame(M, 20 * mm, CW, PAGE_H - M - 20 * mm, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("capa", [frame], onPage=capa),
                          PageTemplate("normal", [frame], onPage=rodape)])
    story = [NextPageTemplate("normal"), PageBreak()]
    story += pagina_sobre_mim() + pagina_sobre() + [PageBreak()]
    story += pagina_sumario() + [PageBreak()]
    for rel, cat, *_ in PROJETOS:
        story += paginas_projeto(rel, cat)
    story += pagina_contato()
    doc.build(story)
    return saida


if __name__ == "__main__":
    saida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/pdf/portfolio-gustavo-silvestre.pdf"
    gerar(saida)
    print(f"PDF gerado: {saida} ({saida.stat().st_size / 1e6:.1f} MB, {len(fitz.open(saida))} páginas)")
