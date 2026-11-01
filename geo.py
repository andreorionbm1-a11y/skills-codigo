"""Kit de geometría SVG. Cada función devuelve el atributo d de un <path> (o un fragmento SVG)."""
import math, random

def _f(v): return f"{v:.1f}".rstrip('0').rstrip('.')

def poligono(cx, cy, R, n, rot=-90):
    """Vértices de un polígono regular (n=3 triángulo, 6 hexágono…)."""
    return [(cx+R*math.cos(math.radians(rot+360*i/n)), cy+R*math.sin(math.radians(rot+360*i/n))) for i in range(n)]

def estrella(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for i in range(2*n):
        a = math.radians(rot+180*i/n); rr = R if i % 2 == 0 else r
        pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
    return pts

def redondeado(pts, r):
    """Polígono cualquiera con esquinas redondeadas de radio r (curvas cuadráticas)."""
    n, d = len(pts), []
    for i in range(n):
        p0, p1, p2 = pts[i-1], pts[i], pts[(i+1) % n]
        def hacia(a, b):
            dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy) or 1; k = min(r, L/2)/L
            return (a[0]+dx*k, a[1]+dy*k)
        a, b = hacia(p1, p0), hacia(p1, p2)
        d.append(("M" if i == 0 else "L") + f"{_f(a[0])},{_f(a[1])} Q{_f(p1[0])},{_f(p1[1])} {_f(b[0])},{_f(b[1])}")
    return " ".join(d) + " Z"

def mancha(cx, cy, R, semilla=1, puntos=7, variacion=0.22):
    """Forma orgánica cerrada y suave (blob), reproducible con la semilla."""
    rnd = random.Random(semilla)
    pts = [(cx+R*(1+rnd.uniform(-variacion, variacion))*math.cos(2*math.pi*i/puntos),
            cy+R*(1+rnd.uniform(-variacion, variacion))*math.sin(2*math.pi*i/puntos)) for i in range(puntos)]
    return suave(pts, cerrado=True)

def suave(pts, cerrado=False, t=0.5):
    """Curva Catmull-Rom que pasa por todos los puntos."""
    n = len(pts); P = (lambda i: pts[i % n]) if cerrado else (lambda i: pts[max(0, min(n-1, i))])
    d = [f"M{_f(pts[0][0])},{_f(pts[0][1])}"]
    for i in range(n if cerrado else n-1):
        p0, p1, p2, p3 = P(i-1), P(i), P(i+1), P(i+2)
        c1 = (p1[0]+(p2[0]-p0[0])*t/3, p1[1]+(p2[1]-p0[1])*t/3)
        c2 = (p2[0]-(p3[0]-p1[0])*t/3, p2[1]-(p3[1]-p1[1])*t/3)
        d.append(f"C{_f(c1[0])},{_f(c1[1])} {_f(c2[0])},{_f(c2[1])} {_f(p2[0])},{_f(p2[1])}")
    return " ".join(d) + (" Z" if cerrado else "")

def onda(x1, x2, y, amp=2.5, largo=10):
    """Subrayado ondulado (como el de las guías)."""
    d, x, s = [f"M{_f(x1)},{_f(y)}"], x1, 1
    while x < x2:
        nx = min(x+largo/2, x2)
        d.append(f"Q{_f((x+nx)/2)},{_f(y-amp*s)} {_f(nx)},{_f(y)}"); x, s = nx, -s
    return " ".join(d)

def curva(x1, y1, x2, y2, curvatura=0.25):
    """Conector curvo; curvatura positiva dobla a la izquierda del sentido de avance."""
    mx, my = (x1+x2)/2, (y1+y2)/2; dx, dy = x2-x1, y2-y1
    cx, cy = mx-dy*curvatura, my+dx*curvatura
    return f"M{_f(x1)},{_f(y1)} Q{_f(cx)},{_f(cy)} {_f(x2)},{_f(y2)}"

def codo(x1, y1, x2, y2, r=10, vertical_primero=False):
    """Conector ortogonal con un doblez redondeado."""
    if vertical_primero:
        sy = 1 if y2 > y1 else -1; sx = 1 if x2 > x1 else -1; r = min(r, abs(x2-x1)/2, abs(y2-y1))
        return f"M{_f(x1)},{_f(y1)} L{_f(x1)},{_f(y2-sy*r)} Q{_f(x1)},{_f(y2)} {_f(x1+sx*r)},{_f(y2)} L{_f(x2)},{_f(y2)}"
    sx = 1 if x2 > x1 else -1; sy = 1 if y2 > y1 else -1; r = min(r, abs(x2-x1), abs(y2-y1)/2)
    return f"M{_f(x1)},{_f(y1)} L{_f(x2-sx*r)},{_f(y1)} Q{_f(x2)},{_f(y1)} {_f(x2)},{_f(y1+sy*r)} L{_f(x2)},{_f(y2)}"

def globo(x, y, w, h, r=14, cola_x=None, cola=14, lado='abajo'):
    """Globo de diálogo / llamada con cola."""
    cx = x+w*0.3 if cola_x is None else cola_x
    if lado == 'abajo':
        return (f"M{_f(x+r)},{_f(y)} H{_f(x+w-r)} Q{_f(x+w)},{_f(y)} {_f(x+w)},{_f(y+r)} V{_f(y+h-r)} "
                f"Q{_f(x+w)},{_f(y+h)} {_f(x+w-r)},{_f(y+h)} H{_f(cx+cola)} L{_f(cx)},{_f(y+h+cola)} L{_f(cx)},{_f(y+h)} "
                f"H{_f(x+r)} Q{_f(x)},{_f(y+h)} {_f(x)},{_f(y+h-r)} V{_f(y+r)} Q{_f(x)},{_f(y)} {_f(x+r)},{_f(y)} Z")
    return (f"M{_f(x+r)},{_f(y)} H{_f(cx)} L{_f(cx)},{_f(y-cola)} L{_f(cx+cola)},{_f(y)} H{_f(x+w-r)} Q{_f(x+w)},{_f(y)} {_f(x+w)},{_f(y+r)} "
            f"V{_f(y+h-r)} Q{_f(x+w)},{_f(y+h)} {_f(x+w-r)},{_f(y+h)} H{_f(x+r)} Q{_f(x)},{_f(y+h)} {_f(x)},{_f(y+h-r)} V{_f(y+r)} Q{_f(x)},{_f(y)} {_f(x+r)},{_f(y)} Z")

def anillo(cx, cy, r_ext, r_int, a1, a2, hueco=0):
    """Segmento de anillo (ciclos, ruedas, gráficas de dona). Ángulos en grados, 0 = arriba."""
    a1, a2 = a1+hueco/2, a2-hueco/2
    P = lambda r, a: (cx+r*math.sin(math.radians(a)), cy-r*math.cos(math.radians(a)))
    g = 1 if a2-a1 > 180 else 0
    p1, p2, p3, p4 = P(r_ext, a1), P(r_ext, a2), P(r_int, a2), P(r_int, a1)
    return (f"M{_f(p1[0])},{_f(p1[1])} A{_f(r_ext)},{_f(r_ext)} 0 {g} 1 {_f(p2[0])},{_f(p2[1])} "
            f"L{_f(p3[0])},{_f(p3[1])} A{_f(r_int)},{_f(r_int)} 0 {g} 0 {_f(p4[0])},{_f(p4[1])} Z")

def a_mano(d_pts, semilla=3, temblor=1.2, pasadas=2):
    """Trazo a mano alzada: recorre puntos con temblor y doble pasada (lista de (x,y))."""
    rnd, salida = random.Random(semilla), []
    for _ in range(pasadas):
        pts = [(x+rnd.uniform(-temblor, temblor), y+rnd.uniform(-temblor, temblor)) for x, y in d_pts]
        salida.append(suave(pts))
    return salida

def rect_a_mano(x, y, w, h, semilla=3, temblor=1.2):
    pts, paso = [], 24
    for (ax, ay, bx, by) in [(x, y, x+w, y), (x+w, y, x+w, y+h), (x+w, y+h, x, y+h), (x, y+h, x, y)]:
        L = math.hypot(bx-ax, by-ay); k = max(2, int(L/paso))
        pts += [(ax+(bx-ax)*i/k, ay+(by-ay)*i/k) for i in range(k)]
    pts.append((x, y))
    return a_mano(pts, semilla, temblor)

DEFS = """<defs>
<marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="context-stroke" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>
<marker id="punta_llena" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="context-stroke"/></marker>
<marker id="punto" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5"><circle cx="5" cy="5" r="4" fill="context-stroke"/></marker>
<pattern id="puntos" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="currentColor" opacity=".25"/></pattern>
<pattern id="rayas" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="currentColor" stroke-width="2" opacity=".18"/></pattern>
<pattern id="cuadricula" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20,0 L0,0 0,20" fill="none" stroke="currentColor" stroke-width=".6" opacity=".18"/></pattern>
</defs>"""

_MED = {}
def medir(textos, fuente="Inter", tam=16, peso=400):
    """Ancho real en px de cada texto con la fuente indicada (usa el navegador). Devuelve lista."""
    from playwright.sync_api import sync_playwright
    try:
        from verificar import ruta_fuentes
    except Exception:
        ruta_fuentes = None
    clave = (tuple(textos), fuente, tam, peso)
    if clave in _MED: return _MED[clave]
    fam = fuente.replace(' ', '+')
    html = (f"<html><head><link rel='stylesheet' href='https://fonts.googleapis.com/css2?family={fam}:wght@{peso}&display=swap'>"
            f"</head><body style=\"font-family:'{fuente}';font-size:{tam}px;font-weight:{peso}\"></body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        if ruta_fuentes: pg.route('**/fonts.googleapis.com/**', ruta_fuentes)
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False); tmp.write(html); tmp.close()
        pg.goto('file://' + tmp.name); pg.wait_for_load_state('networkidle'); os.unlink(tmp.name)
        r = pg.evaluate("""async (t) => { await document.fonts.load(getComputedStyle(document.body).font); await document.fonts.ready;
            const c = document.createElement('canvas').getContext('2d'); c.font = getComputedStyle(document.body).font;
            return t.map(x => c.measureText(x).width); }""", list(textos))
        b.close()
    _MED[clave] = r
    return r

def envolver(texto, ancho_max, fuente="Inter", tam=16, peso=400):
    """Parte un texto en líneas que caben en ancho_max px (una sola medición en el navegador)."""
    palabras = texto.split()
    if not palabras: return []
    anchos = medir(palabras + [" "], fuente, tam, peso); esp = anchos[-1]
    lineas, actual, w_act = [], [], 0.0
    for p, w in zip(palabras, anchos):
        nuevo = w if not actual else w_act + esp + w
        if actual and nuevo > ancho_max:
            lineas.append(" ".join(actual)); actual, w_act = [p], w
        else:
            actual.append(p); w_act = nuevo
    lineas.append(" ".join(actual))
    return lineas


# ───────────── Notación matemática (KaTeX) ─────────────

KATEX_HEAD = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', () => {
  renderMathInElement(document.body, {delimiters: [
    {left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false}], throwOnError: false});
  document.querySelectorAll('[data-tex]').forEach(e =>
    katex.render(e.getAttribute('data-tex'), e, {throwOnError: false, displayMode: false}));
});
</script>
<style>
.katex { font-size: 1.08em; }                 /* fórmulas un poco más grandes que el texto manuscrito */
.katex-display { margin: .5em 0; overflow-x: auto; overflow-y: hidden; padding: .15em 0; }
.formula .katex-display { margin: 0; }
svg .fx { display: flex; align-items: center; height: 100%; line-height: 1; }
</style>"""

def formula_svg(x, y, tex, tam=15, ancho=None, alinear='centro', color='#1D1D1D'):
    """Fórmula real (KaTeX) dentro de un SVG. (x, y) = punto de anclaje en la línea media del texto.
    alinear: 'centro' | 'izq' (x es el borde izquierdo) | 'der' (x es el borde derecho).
    Requiere KATEX_HEAD en el <head>. Ancho estimado si no se da; el verificador confirma que no choque."""
    limpio = tex
    for c in ['\\frac', '\\sqrt', '\\bar', '\\hat', '\\left', '\\right', '{', '}', '\\,', '\\']: limpio = limpio.replace(c, '')
    w = ancho or max(24, len(limpio) * tam * 0.62 + 12)
    h = tam * (3.0 if '\\frac' in tex else 2.0)
    x0 = x - w/2 if alinear == 'centro' else (x if alinear == 'izq' else x - w)
    just = {'centro': 'center', 'izq': 'flex-start', 'der': 'flex-end'}[alinear]
    tex_attr = tex.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
    return (f'<foreignObject x="{_f(x0)}" y="{_f(y - h/2)}" width="{_f(w)}" height="{_f(h)}">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="fx" style="justify-content:{just};font-size:{tam}px;color:{color}">'
            f'<span data-tex="{tex_attr}"></span></div></foreignObject>')


# ───────────── Páginas impresas ─────────────

def css_impresion(materia, temas=(), fuente="Kalam", color="#55524B", margen="15mm 15mm 18mm", tam="9pt"):
    """CSS de impresión listo: A4, márgenes, pie con materia · tema · página n / N, y reglas de saltos.
    temas: lista de nombres; el i-ésimo tema debe ir en <section class="tema tema-i"> (i desde 1).
    Cada tema arranca en página nueva y su nombre aparece en el pie de sus páginas."""
    def esc(t): return t.replace('\\', '\\\\').replace('"', '\\"')
    pie = f"font-family: '{fuente}'; font-size: {tam}; color: {color};"
    css = [f"""@page {{ size: A4; margin: {margen};
  @bottom-left {{ content: "{esc(materia)}"; {pie} }}
  @bottom-right {{ content: counter(page) " / " counter(pages); {pie} }} }}"""]
    for i, t in enumerate(temas, 1):
        css.append(f""".tema-{i} {{ page: tema-{i}; }}
@page tema-{i} {{ @bottom-center {{ content: "{esc(t)}"; {pie} }} }}""")
    css.append(CSS_TIPOGRAFIA)
    css.append("""p, li { orphans: 3; widows: 3; }
.tema { break-before: page; } .tema:first-of-type { break-before: auto; }
h1, h2, h3, h4 { break-after: avoid; }
.formula, .bloque, figure, svg, table.chica, blockquote, pre, .katex-display { break-inside: avoid; }
thead { display: table-header-group; } tr { break-inside: avoid; }""")
    return "\n".join(css)


# ───────────── Tipografía fina en español ─────────────

CSS_TIPOGRAFIA = """html { hyphens: auto; -webkit-hyphens: auto; }
p, li, td { text-wrap: pretty; }
h1, h2, h3, h4, figcaption { text-wrap: balance; hyphens: manual; }
.formula, .katex, code, pre { hyphens: manual; }"""

def tipografia(html):
    """Corrige signos en el texto (no toca etiquetas HTML ni fórmulas $...$):
    ... → …, comillas rectas → “ ”, guion entre espacios → raya —, rangos 1990-2000 → 1990–2000,
    menos ante número → −, número y unidad/% unidos con espacio no separable."""
    import re
    trozos = re.split(r'(<[^>]+>|\$\$.*?\$\$|\$[^$]+\$)', html, flags=re.S)
    abierta = [True]
    def comillas(m):
        r = '“' if abierta[0] else '”'; abierta[0] = not abierta[0]; return r
    for i, t in enumerate(trozos):
        if i % 2 or not t: continue
        t = t.replace('...', '…')
        t = re.sub(r'"', comillas, t)
        t = re.sub(r'(?<=\S) - (?=\S)', ' — ', t)
        t = re.sub(r'(?<=\d)-(?=\d)', '–', t)
        t = re.sub(r'(^|[\s(=\[])-(?=\d)', lambda m: m.group(1) + '−', t)
        t = re.sub(r'(\d) (%|mm|cm|km|kg|g|pt|px|MXN|USD|°C|años|pp)\b', lambda m: m.group(1) + ' ' + m.group(2), t)
        t = re.sub(r'(\d) %', lambda m: m.group(1) + ' %', t)
        trozos[i] = t
    return ''.join(trozos)


# ═════════════ Plantillas listas ═════════════

ESTILOS_PLANTILLA = {
    'apuntes': dict(gf='Kalam:wght@400;700', fam="'Kalam', cursive", fuente='Kalam', tinta='#1D1D1D', sec='#55524B',
                    fondo='#FFFFFF', titulo='#C93636', clave='#237A3E', formula='#2F6FD6', marca='#FFE45C', linea='#CFCAC0', onda=True),
    'limpio': dict(gf='Inter:wght@400;600;700', fam="'Inter', sans-serif", fuente='Inter', tinta='#18181B', sec='#52525B',
                   fondo='#FFFFFF', titulo='#1D4ED8', clave='#0F766E', formula='#1D4ED8', marca='#DBEAFE', linea='#E4E4E7', onda=False),
}

def _css_base(e, tam=15):
    sub = 'wavy' if e['onda'] else 'solid'
    return f"""body {{ font-family: {e['fam']}; font-size: {tam}px; line-height: 1.5; color: {e['tinta']}; background: {e['fondo']}; margin: 0; }}
h1 {{ font-size: {tam + 11}px; font-weight: 700; display: inline-block; line-height: 1.6; padding: 0 8px; margin: 0 0 6px; border-radius: 4px;
     background: linear-gradient(to bottom, transparent 26%, {e['marca']} 26%, {e['marca']} 80%, transparent 80%); }}
h2 {{ font-size: {tam + 6}px; font-weight: 700; color: {e['titulo']}; text-decoration: underline {sub} {e['titulo']} 1.6px; text-underline-offset: 0.08em; margin: 14px 0 8px; }}
h3 {{ font-size: {tam + 2}px; font-weight: 700; margin: 10px 0 4px; }}
.clave {{ text-decoration: underline {sub} {e['clave']} 1.4px; text-underline-offset: 0.08em; }}
.nota {{ color: {e['clave']}; font-size: {tam - 2.5}px; }}
.num {{ color: {e['titulo']}; font-weight: 700; margin-right: 4px; }}
.formula {{ display: inline-block; border: 1.6px solid {e['formula']}; border-radius: 3px; padding: 3px 12px 5px; margin: 4px 0; }}
.sep {{ border: 0; border-top: 1.6px dashed {e['tinta']}; margin: 16px 0; }}
.paso {{ border: 0; border-top: 1.4px dashed {e['clave']}; margin: 10px 0; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 28px; }}
.bloque {{ break-inside: avoid; }}
table {{ border-collapse: collapse; }} th, td {{ border: 1px solid {e['linea']}; padding: 4px 8px; text-align: left; vertical-align: top; }}
th {{ color: {e['titulo']}; font-weight: 700; }}"""

def plantilla(tipo, materia='', titulo='', contenido=None, estilo='apuntes', autor='', fecha='', subtitulo='', tam=None):
    """HTML completo y listo para imprimir (A4) en el estilo dado ('apuntes' = formato de guías de André, 'limpio').
    tipo='guia'       contenido = [(nombre_tema, html), ...]  → cada tema en página nueva, pie materia · tema · n/N
    tipo='formulario' contenido = [(titulo_bloque, html), ...] → dos columnas compactas, bloques sin partir
    tipo='tarjetas'   contenido = [(frente, reverso), ...]  → 8 por hoja; la hoja de reversos va espejada para
                      imprimir a doble cara (borde largo) y recortar por las líneas punteadas
    tipo='portada'    usa titulo, subtitulo, materia, autor, fecha
    El texto pasa por tipografia(); las fórmulas van en $...$ (KaTeX)."""
    e = ESTILOS_PLANTILLA[estilo]
    tam = tam or (12.5 if tipo == 'formulario' else 15)
    head = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{titulo or materia}</title>'
            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={e["gf"]}&display=swap">{KATEX_HEAD}<style>')
    css = _css_base(e, tam)
    T = lambda h: tipografia(h or '')
    if tipo == 'guia':
        temas = contenido or []
        css += '\n' + css_impresion(materia, [n for n, _ in temas], e['fuente'], e['sec'])
        cuerpo = (f'<header class="bloque"><h1>{T(titulo)}</h1></header>' if titulo else '') + ''.join(
            f'<section class="tema tema-{i}"><h2>{T(n)}</h2>{T(h)}</section>' for i, (n, h) in enumerate(temas, 1))
    elif tipo == 'formulario':
        css += '\n' + css_impresion(materia, [], e['fuente'], e['sec'], margen='10mm 10mm 13mm')
        css += f"""
.formulario {{ column-count: 2; column-gap: 8mm; column-rule: 1.2px dashed {e['linea']}; }}
.formulario .bloque {{ margin: 0 0 8px; }} .formulario h2 {{ font-size: {tam + 3}px; margin: 4px 0; }}
.cabeza {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1.6px solid {e['tinta']}; margin-bottom: 8px; }}
.cabeza h1 {{ font-size: {tam + 8}px; margin: 0; }} .formulario .formula {{ font-size: {tam + 1.5}px; }}"""
        cuerpo = (f'<div class="cabeza"><h1>{T(titulo or "Formulario")}</h1><span class="nota">{T(materia)}</span></div>'
                  '<div class="formulario">' + ''.join(f'<div class="bloque"><h2>{T(t)}</h2>{T(h)}</div>' for t, h in (contenido or [])) + '</div>')
    elif tipo == 'tarjetas':
        css += f"""
@page {{ size: A4; margin: 10mm; }}
.hoja {{ display: grid; grid-template-columns: 95mm 95mm; grid-auto-rows: 68mm; break-after: page; }}
.hoja:last-child {{ break-after: auto; }}
.t {{ border: 1px dashed {e['linea']}; padding: 6mm; display: flex; flex-direction: column; justify-content: center; align-items: center;
      text-align: center; position: relative; overflow: hidden; }}
.t .n {{ position: absolute; top: 2.5mm; left: 3mm; font-size: 10px; color: {e['sec']}; }}
.frente {{ font-size: {tam + 5}px; font-weight: 700; color: {e['titulo']}; }}
.reverso {{ font-size: {tam}px; }}"""
        cards = list(contenido or []); cuerpo = ''
        for k in range(0, len(cards), 8):
            lote = cards[k:k + 8] + [('', '')] * (8 - len(cards[k:k + 8]))
            cuerpo += '<div class="hoja">' + ''.join(
                f'<div class="t frente">' + (f'<span class="n">{k + i + 1}</span>' if f else '') + f'{T(f)}</div>' for i, (f, _) in enumerate(lote)) + '</div>'
            esp = [lote[i + 1 - 2 * (i % 2)] for i in range(8)]           # columnas intercambiadas para doble cara
            idx = [k + i + 2 - 2 * (i % 2) for i in range(8)]
            cuerpo += '<div class="hoja">' + ''.join(
                f'<div class="t reverso">' + (f'<span class="n">{n}</span>' if r else '') + f'{T(r)}</div>' for n, (_, r) in zip(idx, esp)) + '</div>'
    elif tipo == 'portada':
        css += f"""
@page {{ size: A4; margin: 0; }}
.portada {{ height: 297mm; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 10mm; }}
.portada h1 {{ font-size: 44px; }} .portada .sub {{ font-size: 22px; color: {e['titulo']}; }}
.portada .datos {{ font-size: 16px; color: {e['sec']}; line-height: 1.8; }}"""
        cuerpo = (f'<div class="portada"><h1>{T(titulo)}</h1>' + (f'<div class="sub">{T(subtitulo)}</div>' if subtitulo else '') +
                  '<div class="datos">' + '<br>'.join(T(x) for x in (materia, autor, fecha) if x) + '</div></div>')
    else:
        raise ValueError("tipo = 'guia' | 'formulario' | 'tarjetas' | 'portada'")
    return head + css + '</style></head><body>' + cuerpo + '</body></html>'
