"""Gera o portfólio em PDF (A4), versão apresentação: 1–2 páginas por projeto.

Fichas vêm dos README.md; destaques, números e imagens ficam no dicionário DADOS.

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
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image,
                                KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://gustavosilvestre874.github.io/portfolio-engenharia-civil/"
NOME = "Gustavo Rodrigo Silvestre da Silva"
EMAIL = "gustavorodrigosilvestre@gmail.com"
LINKEDIN = "linkedin.com/in/gustavo-silvestre-0649b1244"

# Ordem do PDF: projetos mais fortes primeiro
PROJETOS = [
    ("projetos/sistemas-prediais/climatizacao-hvac-escritorio-brasilia", "Sistemas prediais · Poli-USP · 2026",
     "Climatização (HVAC) de escritório em Brasília", "assets/img/hvac.png",
     "Carga térmica de 66.276 W, 2 UTAs por andar, chiller de água gelada, dutos e diagrama unifilar."),
    ("projetos/projeto-completo/chacara-igarata", "Projeto completo · Profissional · 2025",
     "Chácara em Igaratá", "assets/img/igarata.jpg",
     "Residência de 117,75 m²: projeto arquitetônico, estrutural preliminar e esgoto sanitário."),
    ("projetos/arquitetura/reforma-de-cozinha", "Interiores · Profissional · 2024",
     "Reforma de cozinha", "assets/img/cozinha.jpg",
     "Executivo em 12 folhas: 3D, plantas e vistas, marcenaria detalhada, quantitativo e marmoraria."),
    ("projetos/arquitetura/residencia-unifamiliar-ifsp", "Arquitetura · IFSP",
     "Residência unifamiliar", "assets/img/residencia-ifsp.jpg",
     "Do programa de necessidades ao detalhamento, em 11 pranchas: plantas, fachadas, cortes, áreas molhadas, implantação e estrutura."),
    ("projetos/design-biofilico/escritorio-com-vista-para-jardim", "Design biofílico · Estudo pessoal",
     "Escritório com vista para o jardim", "assets/img/escritorio-jardim.jpg",
     "Home office com uma grande abertura para o jardim, baseado em estudos que associam a natureza a mais calma e concentração."),
    ("projetos/design-biofilico/dormitorio-para-descansar", "Design biofílico · Estudo pessoal",
     "Dormitório para descansar", "assets/img/dormitorio.jpg",
     "Quarto pensado para o descanso: luz quente e indireta, madeira, uma paisagem como ponto focal e tudo organizado."),
    ("projetos/topografia/levantamento-topografico-poli-usp", "Topografia · Poli-USP · 2024",
     "Levantamento topográfico", "assets/img/topografia.jpg",
     "Trabalho em grupo: poligonal de 5.693 m² com 432 pontos de detalhe na Cidade Universitária."),
    ("projetos/arquitetura/condominio-residencial", "Arquitetura · 2024",
     "Condomínio residencial", "assets/img/condominio.jpg",
     "Planta humanizada de pavimento-tipo com duas unidades, modelada em Revit."),
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
def preparar_imagem(path, max_px=1500):
    """Reduz e converte para JPEG/PNG leve; SVG é rasterizado. Devolve (arquivo, largura, altura)."""
    path = pathlib.Path(path)
    nome = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.stem
    out = TMP / (re.sub(r"\W", "_", nome) + ".png")
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
    im.save(out, quality=80, optimize=True)
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


def url_projeto(rel):
    return SITE + rel + "/"


# Conteúdo resumido de cada projeto para o PDF (mesmos dados dos README, em formato de apresentação)
DADOS = {
    "projetos/sistemas-prediais/climatizacao-hvac-escritorio-brasilia": {
        "hero": "imagens/rede-de-dutos-3d.png",
        "numeros": [("66.276 W", "carga térmica de pico (2º andar)"), ("25,6 TR", "capacidade das serpentinas (2º andar)"),
                    ("2.376 m²", "área climatizada em 3 pavimentos"), ("11", "zonas térmicas")],
        "destaques": [
            "Carga térmica pelo método CLTD/CLF (ASHRAE) e pela NBR 16401, com variação horária por fachada.",
            "Vazões de insuflamento por zona, a partir de balanços de energia e de massa.",
            "Seleção de difusores Trox ADLQ e grelhas GRH com critério acústico NC ≤ 35.",
            "2 UTAs por andar, chiller Carrier AquaSmart e filtragem G4 + F7.",
            "Dutos dimensionados por perda de carga constante e diagrama unifilar do sistema.",
            "Fachada oeste identificada como condição crítica (até 1.950 W por janela).",
        ],
        "galeria": [("imagens/carga-termica-por-ambiente.png", "Carga térmica por ambiente e por fonte"),
                    ("imagens/diagrama-unifilar.png", "Diagrama unifilar do sistema AVAC"),
                    ("imagens/fachada-oeste.png", "Variação horária da carga: fachada oeste"),
                    ("imagens/carga-termica-teto.png", "Carga térmica de cobertura por zona")],
    },
    "projetos/projeto-completo/chacara-igarata": {
        "hero": "imagens/arquitetonico-preliminar.png",
        "numeros": [("117,75 m²", "área construída"), ("601,01 m²", "terreno"),
                    ("41,22%", "de solo permeável"), ("3", "disciplinas integradas")],
        "destaques": [
            "Projeto profissional para cliente, como técnico projetista (abril a julho de 2025).",
            "Arquitetônico preliminar: planta 1:50, corte e perspectiva 3D.",
            "Estrutural: brocas Ø30, sapatas, baldrames 20×30, pilares 15×20 e vigas 15×40.",
            "Esgoto: tubulações de 40, 50 e 100 mm com caimento de 1–2%, caixas de inspeção e de gordura.",
            "Tabelas automáticas de conexões e peças hidrossanitárias extraídas do modelo.",
        ],
        "galeria": [("imagens/estrutural-preliminar-concepcao.png", "Concepção estrutural: planta, cortes e 3D"),
                    ("imagens/estrutural-fundacoes-vigas-pilares.png", "Fundações, baldrames, pilares e vigas"),
                    ("imagens/esgoto-sanitario.png", "Esgoto sanitário: planta, detalhes e isométricos")],
    },
    "projetos/arquitetura/reforma-de-cozinha": {
        "hero": "imagens/capa-3d.jpg",
        "numeros": [("12", "folhas de projeto executivo"), ("5", "folhas de marcenaria"),
                    ("3,80 × 1,80 m", "área do ambiente")],
        "destaques": [
            "Bancada em \"L\", torre quente para forno e micro-ondas e nicho iluminado em LED.",
            "Marcenaria detalhada módulo a módulo (1:10 e 1:20), com notas de execução.",
            "Quantitativo das peças de MDF extraído do modelo no SketchUp, com estimativa de chapas e custo.",
            "Marmoraria: bancada em mármore preto com recortes para cuba e cooktop.",
            "Pontos elétricos previstos para eletrodomésticos, LED e depurador.",
        ],
        "galeria": [("pranchas/02-planta.jpg", "Folha 02: planta 1:20"),
                    ("pranchas/04-vista.jpg", "Folha 04: vista cotada 1:20"),
                    ("pranchas/08-marcenaria-torre-quente.jpg", "Folha 08: marcenaria da torre quente"),
                    ("pranchas/12-marmoraria.jpg", "Folha 12: marmoraria")],
    },
    "projetos/arquitetura/residencia-unifamiliar-ifsp": {
        "hero": "imagens/capa-pav2.jpg",
        "numeros": [("11", "pranchas"), ("2", "pavimentos"), ("10 × 29 m", "lote")],
        "destaques": [
            "Programa de necessidades a partir de entrevista com as clientes: 3 dormitórios, suíte com closet.",
            "Estudo volumétrico e setorização em áreas social, íntima, de serviços e circulação.",
            "Plantas 1:50 com teto verde e laje acessível; fachadas, cortes e detalhes 1:20.",
            "Elevações de áreas molhadas com tabelas de metais e louças; implantação 1:100.",
            "Estrutura: pilares e vigas 20×40, lajes h = 14 cm e detalhamento de armaduras.",
        ],
        "galeria": [("pranchas/02-estudo-volumetrico.jpg", "Estudo volumétrico"),
                    ("pranchas/07-fachadas-e-isometrica.jpg", "Fachadas e isométrica"),
                    ("pranchas/08-cortes-e-detalhes.jpg", "Cortes e detalhes"),
                    ("pranchas/11-estrutura.jpg", "Estrutura e armaduras")],
    },
    "projetos/design-biofilico/escritorio-com-vista-para-jardim": {
        "hero": "imagens/render-1.jpg",
        "numeros": [("+15%", "produtividade com plantas (Nieuwenhuis et al., 2014)"),
                    ("40 s", "de vista verde melhoram a atenção (Lee et al., 2015)")],
        "destaques": [
            "Conceito: design biofílico, com a natureza sempre no campo de visão de quem trabalha.",
            "Abertura para o jardim ocupando a parede ao lado da mesa.",
            "Luz quente e indireta em LED, madeira e tons terrosos.",
            "Base científica: Ulrich (1984), Kaplan (1995), Nieuwenhuis et al. (2014) e Lee et al. (2015).",
        ],
        "galeria": [("imagens/render-2.jpg", "Mesa de trabalho com o jardim ao lado"),
                    ("imagens/render-3.jpg", "Detalhe do jardim e da mesa")],
    },
    "projetos/design-biofilico/dormitorio-para-descansar": {
        "hero": "imagens/render-1.jpg",
        "numeros": [("≈ 90 min", "a menos de melatonina com luz ambiente antes de dormir (Gooley et al., 2011)")],
        "destaques": [
            "Iluminação em camadas, com LED quente e indireto para a noite.",
            "Painel ripado de madeira e marcenaria no mesmo tom, equilibrados com tons neutros.",
            "Paisagem natural como ponto focal no lugar da TV.",
            "Organização com nichos e armário de vidro fumê.",
            "Base científica: Gooley et al. (2011), Tsunetsugu et al. (2007), Saxbe e Repetti (2010).",
        ],
        "galeria": [("imagens/render-2.jpg", "Painel ripado e armário com vidro fumê"),
                    ("imagens/render-3.jpg", "Painel de madeira com nichos iluminados")],
    },
    "projetos/topografia/levantamento-topografico-poli-usp": {
        "hero": "imagens/planta-topografica.png",
        "numeros": [("5.693 m²", "área da poligonal"), ("432", "pontos de detalhe"),
                    ("107", "árvores levantadas"), ("7", "integrantes")],
        "destaques": [
            "Levantamento planialtimétrico na Cidade Universitária, entre o Prédio da Engenharia Civil e o Biênio.",
            "Poligonal de 8 vértices referenciada à RN2008.",
            "Pontos de detalhe por irradiação, codificados por tipo de elemento.",
            "Processamento das coordenadas (E, N, cota) e planta topográfica em CAD (1:500).",
        ],
        "galeria": [],
    },
    "projetos/arquitetura/condominio-residencial": {
        "hero": "docs/planta-nivel-1.pdf",
        "numeros": [("39,86 m²", "sala"), ("34,51 m²", "varanda gourmet"), ("2", "elevadores")],
        "destaques": [
            "Edifício residencial com duas unidades por pavimento e circulação vertical central.",
            "Modelagem BIM em Revit, com planta humanizada 1:50 e áreas dos ambientes.",
            "Unidade-tipo com suíte, dois dormitórios, cozinha, lavanderia e varanda gourmet.",
        ],
        "galeria": [],
    },
    "projetos/desenho-tecnico/desenho-construcao-civil-ifsp": {
        "hero": "pranchas/01-plantas-inferior-superior-cobertura.jpg",
        "numeros": [("4", "folhas"), ("14", "janelas especificadas"), ("16", "portas especificadas")],
        "destaques": [
            "Plantas, cortes e gradil, vistas, detalhes e tabelas de uma residência de dois pavimentos.",
            "Especificação de revestimentos, soleiras, peitoris e alvenaria.",
            "Detalhes construtivos: rufo, vergas, contrapiso, impermeabilização e calha.",
        ],
        "galeria": [("pranchas/02-cortes-e-gradil.jpg", "Folha 02: cortes e gradil"),
                    ("pranchas/03-vistas.jpg", "Folha 03: vistas"),
                    ("pranchas/04-detalhes-e-tabelas.jpg", "Folha 04: detalhes e tabelas")],
    },
    "projetos/desenho-tecnico/escada-e-rampas-ifsp": {
        "hero": "docs/rampas-planta.pdf",
        "numeros": [("7,83%", "inclinação das rampas acessíveis"), ("1:25", "corte da escada")],
        "destaques": [
            "Corte AA de escada com numeração dos degraus e níveis de piso.",
            "Estudo de rampas com guia de balizamento, guarda-corpo e sinalização de acessibilidade.",
        ],
        "galeria": [("docs/escada-corte-AA.pdf", "Corte AA da escada (1:25)")],
    },
}


class Marcador(Flowable):
    """Registra em que página um projeto começa (para o índice)."""
    def __init__(self, chave):
        super().__init__()
        self.chave = chave

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        PAGINAS[self.chave] = self.canv.getPageNumber()


PAGINAS = {}


def qr(url, tam):
    w = QrCodeWidget(url)
    b = w.getBounds()
    d = Drawing(tam, tam, transform=[tam / (b[2] - b[0]), 0, 0, tam / (b[3] - b[1]), 0, 0])
    d.add(w)
    return d


def caixa(conteudo, largura, fundo=colors.white, pad=10):
    t = Table([[conteudo]], colWidths=[largura])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), fundo),
                           ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                           ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def pagina_indice(com_paginas):
    out = [Paragraph("PROJETOS", S["eyebrow"]), Spacer(1, 3), Paragraph("Índice", S["h1"]),
           Paragraph(f"Cada projeto tem uma página completa no portfólio online, com todas as pranchas, planilhas e "
                     f"vídeos: <font color='#b45a17'>{SITE.replace('https://', '')}</font>", S["muted"]),
           Spacer(1, 12)]
    linhas = []
    st_num = ParagraphStyle("n", fontName="UI-B", fontSize=20, leading=22, textColor=ORANGE)
    st_tit = ParagraphStyle("t", fontName="UI-B", fontSize=10.5, leading=13, textColor=TEXT)
    st_pg = ParagraphStyle("p", fontName="UI-B", fontSize=11, leading=13, textColor=NAVY, alignment=2)
    for i, (rel, cat, titulo, thumb, resumo) in enumerate(PROJETOS, 1):
        pg = str(PAGINAS.get(rel, "")) if com_paginas else ""
        linhas.append([Paragraph(f"{i:02d}", st_num), imagem(ROOT / thumb, 74, 50, moldura=False),
                       [Paragraph(titulo, st_tit), Paragraph(cat.upper(), S["eyebrow"]), Paragraph(resumo, S["caption"])],
                       Paragraph(pg, st_pg)])
    t = Table(linhas, colWidths=[34, 84, CW - 34 - 84 - 34, 34])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                           ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    out.append(t)
    return out


def pagina_sobre_compacta():
    out = [Paragraph("SOBRE MIM", S["eyebrow"]), Spacer(1, 3), Paragraph("Quem sou", S["h1"])]
    corpo = ParagraphStyle("b2", parent=S["body"], fontSize=9, leading=13, spaceAfter=4)
    foto = imagem(ROOT / "assets/img/foto-gustavo.jpg", 118, 118, moldura=False)
    texto = [Paragraph(t, corpo) for t in SOBRE_MIM]
    texto.append(Paragraph("São Paulo – SP · Espanhol avançado · Inglês intermediário",
                           ParagraphStyle("c", parent=S["muted"], textColor=ORANGE_INK)))
    t = Table([[foto, texto]], colWidths=[132, CW - 132])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    out += [t, Spacer(1, 12)]

    logos = ROOT / "assets/img/logos"
    meia = (CW - 12) / 2

    def form(logo, titulo, linhas):
        img = imagem(logos / logo, 30, 30, moldura=False)
        return Table([[img, [Paragraph(f"<b>{titulo}</b>", corpo)] + [Paragraph(l, S["caption"]) for l in linhas]]],
                     colWidths=[38, meia - 20 - 38],
                     style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])
    formacao = [Paragraph("Formação", S["h3"]),
                form("poli-usp.png", "Engenharia Civil", ["Escola Politécnica da USP · ingresso em 2024"]),
                form("ifsp.svg", "Técnico em Edificações", ["IFSP – Campus São Paulo · concluído em 2022",
                     "Qualificações: Desenhista de Construção Civil (955,30 h) e Inspetor de Obras (898,20 h)"])]
    experiencia = [Paragraph("Experiência", S["h3"]),
                   Paragraph("<b>Bolsista de monitoria</b> em Sistemas Prediais Hidráulicos e Sanitários Residenciais, "
                             "IFSP (03/2022 – 12/2022): elaboração de projetos e apoio a alunos no AutoCAD.", corpo),
                   Paragraph("<b>Técnico projetista:</b> projetos residenciais para clientes "
                             "(Chácara Igaratá e Reforma de cozinha).", corpo)]
    duas = Table([[caixa(formacao, meia - 20), caixa(experiencia, meia - 20)]], colWidths=[meia + 12, meia])
    duas.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    out += [duas, Spacer(1, 12)]

    softwares = [("revit-icone.svg", "Revit Architecture"), ("revit-icone.svg", "Revit MEP"),
                 ("autocad-icone.svg", "AutoCAD"), ("inventor-icone.svg", "Inventor"),
                 ("sketchup-icone.svg", "SketchUp"), ("vray-icone.png", "V-Ray"), ("excel.svg", "Excel"),
                 ("word.svg", "Word"), ("powerpoint.svg", "PowerPoint")]
    cel = [Table([[imagem(logos / l, 12, 12, moldura=False), Paragraph(n, S["cell"])]], colWidths=[17, (meia - 20) / 2 - 20],
                 style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])
           for l, n in softwares]
    grid = Table([cel[i:i + 2] + [""] * (2 - len(cel[i:i + 2])) for i in range(0, len(cel), 2)], colWidths=[(meia - 20) / 2] * 2)
    grid.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    conhec = ["Projeto arquitetônico, do programa ao executivo", "Carga térmica e climatização (NBR 16401, ASHRAE)",
              "Instalações hidrossanitárias", "Concepção estrutural de residências", "Levantamento topográfico",
              "Interiores, marcenaria e quantitativos", "Design biofílico"]
    c2 = Paragraph("<br/>".join("• " + k for k in conhec), ParagraphStyle("k", parent=S["caption"], fontSize=8.4, leading=12))
    duas2 = Table([[caixa([Paragraph("Softwares", S["h3"]), grid], meia - 20),
                    caixa([Paragraph("Conhecimentos", S["h3"]), c2], meia - 20)]], colWidths=[meia + 12, meia])
    duas2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    out.append(duas2)
    return out


def imagem_projeto(pasta, caminho, max_w, max_h, moldura=True):
    p = pasta / caminho
    if p.suffix.lower() == ".pdf":  # desenhos em PDF: renderiza a primeira página
        out = TMP / (re.sub(r"\W", "_", str(p.relative_to(ROOT))) + "_render.png")
        if not out.exists():
            pg = fitz.open(p)[0]
            z = 1600 / max(pg.rect.width, pg.rect.height)
            pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False).save(out)
        p = out
    return imagem(p, max_w, max_h, moldura)


def paginas_apresentacao(num, rel, cat):
    pasta = ROOT / rel
    titulo, meta, _, _ = ler_readme(pasta)
    dados = DADOS[rel]
    compacto = 0 < len(dados["galeria"]) <= 2
    out = [Marcador(rel), ProjectHeader(f"{num:02d} · {cat}", titulo, meta), Spacer(1, 10),
           imagem_projeto(pasta, dados["hero"], CW, 150 if compacto else 250), Spacer(1, 12)]

    # Coluna esquerda: destaques. Coluna direita: números, ficha e QR.
    esq_w, dir_w = CW * 0.58, CW * 0.42 - 12
    st_li = ParagraphStyle("li2", parent=S["body"], fontSize=9.2, leading=13, leftIndent=11, bulletIndent=0, spaceAfter=4)
    esq = [SectionTitle("Destaques")] + [Paragraph(inline(d), st_li, bulletText="•") for d in dados["destaques"]]
    st_n = ParagraphStyle("nn", fontName="UI-B", fontSize=16, leading=19, textColor=NAVY)
    st_nl = ParagraphStyle("nl", fontName="UI", fontSize=7.6, leading=9.5, textColor=MUTED)
    nums = [[Paragraph(v, st_n), Paragraph(l, st_nl)] for v, l in dados["numeros"]]
    ncols = 2 if len(nums) > 1 else 1
    linhas_n = [nums[i:i + ncols] + [""] * (ncols - len(nums[i:i + ncols])) for i in range(0, len(nums), ncols)]
    tn = Table(linhas_n, colWidths=[dir_w / ncols] * ncols)
    tn.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), CHIP),
                            ("GRID", (0, 0), (-1, -1), 2, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    st_fk = ParagraphStyle("fk", fontName="UI-B", fontSize=7, leading=9, textColor=MUTED)
    st_fv = ParagraphStyle("fv", fontName="UI", fontSize=8.4, leading=11, textColor=TEXT)
    ficha = []
    for k, v in meta:
        if k == "Entrega":
            continue
        ficha += [Paragraph(k.upper(), st_fk), Paragraph(inline(v), st_fv), Spacer(1, 3)]
    link = Table([[qr(url_projeto(rel), 50),
                   Paragraph("<b>Projeto completo</b><br/>Todas as pranchas e arquivos no portfólio online. "
                             "Aponte a câmera para o código.", S["caption"])]],
                 colWidths=[58, dir_w - 58],
                 style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])
    dir_ = [tn, Spacer(1, 10), caixa(ficha, dir_w - 20, pad=9), Spacer(1, 8), link]
    corpo = Table([[esq, dir_]], colWidths=[esq_w + 12, dir_w])
    corpo.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (0, 0), 12)]))
    out.append(corpo)

    if dados["galeria"]:
        titulo_g = [Spacer(1, 6), SectionTitle("Imagens e pranchas")]
        if not compacto:
            out += [CondPageBreak(230)] + titulo_g
        cw = (CW - 12) / 2
        cels = []
        for cam, leg in dados["galeria"]:
            cels.append([imagem_projeto(pasta, cam, cw - 10, 108 if compacto else 175), Spacer(1, 3), Paragraph(leg, S["caption"])])
        linhas = [cels[i:i + 2] + [""] * (2 - len(cels[i:i + 2])) for i in range(0, len(cels), 2)]
        g = Table(linhas, colWidths=[cw + 12, cw])
        g.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
        out += [KeepTogether(titulo_g + [g])] if compacto else [g]
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


def montar(saida, com_paginas):
    doc = BaseDocTemplate(saida if isinstance(saida, io.BytesIO) else str(saida), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=20 * mm,
                          title="Portfólio – Gustavo Rodrigo Silvestre da Silva", author=NOME,
                          subject="Portfólio de Engenharia Civil")
    frame = Frame(M, 20 * mm, CW, PAGE_H - M - 20 * mm, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("capa", [frame], onPage=capa),
                          PageTemplate("normal", [frame], onPage=rodape)])
    story = [NextPageTemplate("normal"), PageBreak()]
    story += pagina_sobre_compacta() + [PageBreak()]
    story += pagina_indice(com_paginas) + [PageBreak()]
    for i, (rel, cat, *_) in enumerate(PROJETOS, 1):
        story += paginas_apresentacao(i, rel, cat)
    story += pagina_contato()
    doc.build(story)


def gerar(saida):
    montar(io.BytesIO(), com_paginas=False)  # 1ª passada: registra a página de cada projeto
    montar(saida, com_paginas=True)
    return saida


if __name__ == "__main__":
    saida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/pdf/portfolio-gustavo-silvestre.pdf"
    gerar(saida)
    print(f"PDF gerado: {saida} ({saida.stat().st_size / 1e6:.1f} MB, {len(fitz.open(saida))} páginas)")
