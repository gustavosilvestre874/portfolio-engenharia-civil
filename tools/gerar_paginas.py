"""Gera as páginas do site (projetos/**/index.html) a partir dos README.md de cada projeto.

Uso:  python tools/gerar_paginas.py
Requer: pip install markdown
Rode de novo sempre que editar um README de projeto.
"""
import html
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Ordem dos projetos (também usada na navegação "anterior / próximo")
PROJETOS = [
    "projetos/sistemas-prediais/climatizacao-hvac-escritorio-brasilia",
    "projetos/projeto-completo/chacara-igarata",
    "projetos/arquitetura/residencia-unifamiliar-ifsp",
    "projetos/arquitetura/reforma-de-cozinha",
    "projetos/design-biofilico/escritorio-com-vista-para-jardim",
    "projetos/arquitetura/condominio-residencial",
    "projetos/topografia/levantamento-topografico-poli-usp",
    "projetos/desenho-tecnico/desenho-construcao-civil-ifsp",
    "projetos/desenho-tecnico/escada-e-rampas-ifsp",
]
CATEGORIAS = {
    "sistemas-prediais": "Sistemas prediais",
    "projeto-completo": "Projeto completo",
    "arquitetura": "Arquitetura",
    "topografia": "Topografia",
    "desenho-tecnico": "Desenho técnico",
    "design-biofilico": "Design biofílico",
}
VERSAO = "11"  # aumente (e no index.html) ao mudar o CSS/JS, para os navegadores não usarem cache antigo
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def ler_readme(pasta):
    texto = (pasta / "README.md").read_text(encoding="utf-8")
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    linhas = texto.splitlines()

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
            capa = (im.group(2), im.group(1))
            continue
        if corpo or l.strip():
            corpo.append(l)
    return titulo, meta, capa, "\n".join(corpo)


def separar_arquivos(md):
    """Tira a seção '## Arquivos' do texto e devolve [(caminho, descrição)]."""
    partes = re.split(r"^## Arquivos\s*$", md, maxsplit=1, flags=re.M)
    if len(partes) == 1:
        return md, []
    antes, resto = partes
    secao, _, depois = resto.partition("\n## ")
    depois = ("\n## " + depois) if depois else ""
    arquivos = re.findall(r"^\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|\s*(.*?)\s*\|", secao, flags=re.M)
    sobra = "\n".join(l for l in secao.splitlines() if not l.startswith("|"))
    return antes + sobra + depois, arquivos


def md_para_html(md):
    # listas aninhadas: o README usa 2 espaços, a biblioteca espera 4
    md = re.sub(r"^( +)(?=[-*\d])", lambda m: m.group(1) * 2, md, flags=re.M)
    # o GitHub aceita lista logo após um parágrafo; a biblioteca exige uma linha em branco antes
    item = re.compile(r"^\s*([-*]|\d+\.)\s")
    linhas = md.split("\n")
    for i in range(len(linhas) - 1, 0, -1):
        ant = linhas[i - 1]
        if item.match(linhas[i]) and ant.strip() and not item.match(ant) and not ant.startswith(" "):
            linhas.insert(i, "")
    md = "\n".join(linhas)
    corpo = markdown.markdown(md, extensions=["tables", "sane_lists"])
    return corpo.replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")


def tamanho(p):
    b = p.stat().st_size
    return f"{b / 1e6:.1f} MB" if b >= 1e6 else f"{max(1, round(b / 1e3))} KB"


def pagina(i, rel):
    pasta = ROOT / rel
    cat = CATEGORIAS[rel.split("/")[1]]
    titulo, meta, capa, md = ler_readme(pasta)
    md, arquivos = separar_arquivos(md)
    corpo = md_para_html(md)
    raiz = "../../../"

    usados = set(re.findall(r'src="([^"]+)"', corpo)) | ({capa[0]} if capa else set())
    galeria = [p for p in sorted((pasta / "imagens").glob("*")) if p.suffix.lower() in IMG_EXT
               and f"imagens/{p.name}" not in usados] if (pasta / "imagens").exists() else []
    videos = sorted((pasta / "videos").glob("*.mp4")) if (pasta / "videos").exists() else []

    e = html.escape
    chips = "".join(f"<li>{e(v)}</li>" for _, v in meta)
    fatos = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in meta)

    lista = []
    for caminho, desc in arquivos:
        alvo = pasta / caminho
        if caminho.endswith("/") or not alvo.is_file():
            continue
        ext = alvo.suffix[1:].upper()
        lista.append(f'<li><a href="{e(caminho)}" download><span class="ext">{ext}</span>'
                     f'<span class="name">{e(desc)}<small>{e(alvo.name)} · {tamanho(alvo)}</small></span></a></li>')
    bloco_arquivos = (f'<div class="panel"><h3>Arquivos</h3><ul class="files">{"".join(lista)}</ul></div>'
                      if lista else "")

    capa_html = ""
    if capa:
        capa_html = (f'<div class="wrap cover"><figure><img src="{e(capa[0])}" alt="{e(capa[1])}"></figure></div>')

    extra = ""
    if galeria:
        itens = "".join(f'<button type="button" aria-label="Ampliar imagem"><img src="imagens/{e(p.name)}" '
                        f'alt="{e(p.stem.replace("-", " "))}" loading="lazy"></button>' for p in galeria)
        extra += f'<h2>Galeria</h2><div class="gallery">{itens}</div>'
    if videos:
        itens = "".join(f'<video controls preload="metadata" src="videos/{e(v.name)}"></video>' for v in videos)
        extra += f'<h2>Vídeos</h2><div class="videos">{itens}</div>'

    ant = PROJETOS[i - 1] if i > 0 else None
    prox = PROJETOS[i + 1] if i + 1 < len(PROJETOS) else None
    def link(r, rotulo, cls):
        if not r:
            return "<span></span>"
        t = ler_readme(ROOT / r)[0]
        return f'<a class="{cls}" href="{raiz}{r}/"><small>{rotulo}</small>{e(t)}</a>'
    pager = f'<nav class="pager">{link(ant, "← Projeto anterior", "prev")}{link(prox, "Próximo projeto →", "next")}</nav>'

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} · Gustavo Silvestre</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{raiz}assets/css/style.css?v={VERSAO}">
</head>
<body>
<!-- Página gerada por tools/gerar_paginas.py a partir do README.md. Edite o README e rode o script. -->
<header class="hero project">
  <div class="wrap">
    <a class="crumb" href="{raiz}#projetos">← Todos os projetos</a>
    <p class="eyebrow" style="margin-top:28px">{e(cat)}</p>
    <h1>{e(titulo)}</h1>
    <ul class="chips">{chips}</ul>
  </div>
</header>
{capa_html}
<main class="wrap">
  <div class="layout">
    <article class="prose">{corpo}{extra}</article>
    <aside class="aside">
      <div class="panel"><h3>Ficha do projeto</h3><dl class="facts">{fatos}</dl></div>
      {bloco_arquivos}
    </aside>
  </div>
  {pager}
</main>
<footer class="wrap">© 2026 Gustavo Rodrigo Silvestre da Silva · Conteúdo com todos os direitos reservados · <a href="mailto:gustavorodrigosilvestre@gmail.com">gustavorodrigosilvestre@gmail.com</a> · <a href="https://www.linkedin.com/in/gustavo-silvestre-0649b1244" target="_blank" rel="noopener">LinkedIn</a></footer>
<div class="lightbox" role="dialog" aria-label="Imagem ampliada"><button type="button" aria-label="Fechar">×</button><img alt=""></div>
<script src="{raiz}assets/js/site.js?v={VERSAO}"></script>
</body>
</html>
"""


if __name__ == "__main__":
    for i, rel in enumerate(PROJETOS):
        destino = ROOT / rel / "index.html"
        destino.write_text(pagina(i, rel), encoding="utf-8")
        print("gerado:", destino.relative_to(ROOT))
