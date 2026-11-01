"""Gráficas académicas sobre geo.py (skill maquetacion): curvas de densidad, economía, teoría de juegos, estadística y líneas de tiempo.
Todo se calcula; nada se coloca a ojo. Cada función devuelve texto SVG/HTML listo para insertar."""
import math, random, re
import geo
from geo import _f, formula_svg

COL = dict(azul='#2F6FD6', rojo='#C93636', verde='#237A3E', ocre='#86672A', morado='#6847F0',
           tinta='#1D1D1D', gris='#8A8A8A', tenue='#CFCAC0')
FUENTE = "Kalam"

def _t(x, y, s, tam=13, anc='middle', color=None, peso=400):
    return (f'<text x="{_f(x)}" y="{_f(y)}" text-anchor="{anc}" font-size="{tam}" font-weight="{peso}" '
            f'font-family="{FUENTE}, sans-serif" fill="{color or COL["tinta"]}">{s}</text>')

def marcas(a, b, n=5):
    """Marcas 'bonitas' (1, 2, 5 × 10^k) entre a y b."""
    if b <= a: return [a]
    paso = (b - a) / n; e = 10 ** math.floor(math.log10(paso))
    paso = min((m * e for m in (1, 2, 2.5, 5, 10) if m * e >= paso), default=10 * e)
    v, out = math.ceil(a / paso) * paso, []
    while v <= b + paso * 1e-9: out.append(round(v, 10)); v += paso
    return out

def _num(v): return f"{v:g}" if abs(v) >= 1e-9 else "0"


# ═════════════ Curvas de densidad y conjuntos (siempre calculados) ═════════════

def _pdf_normal(z): return math.exp(-z*z/2)/math.sqrt(2*math.pi)

def _pdf_t(z, df):
    c = math.gamma((df+1)/2)/(math.sqrt(df*math.pi)*math.gamma(df/2))
    return c*(1+z*z/df)**(-(df+1)/2)

def _pdf_chi2(x, df):
    if x <= 0: return 0.0
    return x**(df/2-1)*math.exp(-x/2)/(2**(df/2)*math.gamma(df/2))

class Curva:
    """Densidad real dibujada en un rectángulo de píxeles.
    tipo: 'normal' | 't' | 'chi2'. Para normal/t el eje va de -rango a +rango (en z).
    Uso: c = Curva(x=40, y_base=200, ancho=400, alto=140); c.trazo(); c.area(-3.5, -1.96); c.X(1.96); c.Y(1.96)
    """
    def __init__(self, x, y_base, ancho, alto, tipo='normal', df=10, rango=3.6, pasos=160):
        self.x0, self.yb, self.w, self.h, self.tipo, self.df, self.pasos = x, y_base, ancho, alto, tipo, df, pasos
        if tipo == 'chi2':
            self.a, self.b = 0.0, max(df + 4*math.sqrt(2*df), 8)
        else:
            self.a, self.b = -rango, rango
        self._max = max(self.f(self.a+(self.b-self.a)*i/400) for i in range(401))
    def f(self, z):
        return {'normal': lambda: _pdf_normal(z), 't': lambda: _pdf_t(z, self.df), 'chi2': lambda: _pdf_chi2(z, self.df)}[self.tipo]()
    def X(self, z): return self.x0 + (z-self.a)/(self.b-self.a)*self.w
    def Y(self, z): return self.yb - self.f(z)/self._max*self.h
    def _pts(self, z1, z2):
        n = max(8, int(self.pasos*(z2-z1)/(self.b-self.a)))
        return [(self.X(z1+(z2-z1)*i/n), self.Y(z1+(z2-z1)*i/n)) for i in range(n+1)]
    def trazo(self):
        """Contorno de la campana completa (path d)."""
        p = self._pts(self.a, self.b)
        return "M" + " L".join(f"{_f(x)},{_f(y)}" for x, y in p)
    def area(self, z1, z2):
        """Región sombreada bajo la curva entre z1 y z2 (path d cerrado sobre el eje)."""
        z1, z2 = max(z1, self.a), min(z2, self.b)
        p = self._pts(z1, z2)
        return (f"M{_f(self.X(z1))},{_f(self.yb)} L" + " L".join(f"{_f(x)},{_f(y)}" for x, y in p)
                + f" L{_f(self.X(z2))},{_f(self.yb)} Z")
    def corte(self, z, hueco=None):
        """Línea vertical del eje a la curva exactamente (path d). Nunca más alta que la curva.
        hueco=(y_arriba, y_abajo): interrumpe la línea donde va una etiqueta (ej. "1 − α" sobre el centro)."""
        x, y0, y1 = _f(self.X(z)), self.yb, self.Y(z)
        if not hueco: return f"M{x},{_f(y0)} L{x},{_f(y1)}"
        return f"M{x},{_f(y0)} L{x},{_f(hueco[1])} M{x},{_f(hueco[0])} L{x},{_f(y1)}"
    def etiqueta_area(self, z1, z2):
        """Punto (x, y) para escribir el nombre de un área central: centro horizontal, a media altura dentro del área."""
        zm = (z1+z2)/2
        return self.X(zm), self.yb - (self.yb - self.Y(zm))*0.42
    def etiqueta_cola(self, z_corte, lado='izq', sep=10):
        """Punto (x, y, anchor) para la etiqueta de una cola: FUERA de la curva, arriba y hacia afuera, nunca sobre el trazo."""
        z = (z_corte + (self.a if lado == 'izq' else self.b))/2
        x, y = self.X(z), self.Y(z)
        return (x - sep, y - sep, 'end') if lado == 'izq' else (x + sep, y - sep, 'start')
    def eje(self, extra=12):
        return f"M{_f(self.x0-extra)},{_f(self.yb)} L{_f(self.x0+self.w+extra)},{_f(self.yb)}"


def puntos_en_elipse(cx, cy, rx, ry, n, margen=10, sep=18, semilla=1, evitar=()):
    """Puntos dentro de una elipse, con margen al borde y separación mínima entre sí (muestreo de disco de Poisson).
    evitar: lista de (cx, cy, rx, ry) — elipses internas de las que también se mantienen fuera (con margen)."""
    rnd, pts, intentos = random.Random(semilla), [], 0
    def dentro(px, py, ex, ey, erx, ery, m):
        return ((px-ex)/(erx-m))**2 + ((py-ey)/(ery-m))**2 <= 1 if erx > m and ery > m else False
    def lejos(px, py, ex, ey, erx, ery, m):
        return ((px-ex)/(erx+m))**2 + ((py-ey)/(ery+m))**2 > 1
    while len(pts) < n and intentos < 20000:
        intentos += 1
        px, py = cx + rnd.uniform(-rx, rx), cy + rnd.uniform(-ry, ry)
        if not dentro(px, py, cx, cy, rx, ry, margen): continue
        if any(not lejos(px, py, *e, margen) for e in evitar): continue
        if any(math.hypot(px-qx, py-qy) < sep for qx, qy in pts): continue
        pts.append((px, py))
    if len(pts) < n:
        raise ValueError(f"Solo cupieron {len(pts)} de {n} puntos: agranda la elipse o reduce sep")
    return pts



# ═════════════ Plano cartesiano (economía, estadística) ═════════════

DERIVADAS = ('IMg', 'CMg', 'IMe', 'CMe', 'CVMe', 'CFMe', 'CVMg', 'PMg', 'PMe', 'UMg', 'Img', 'Cmg')
def es_derivada(nombre):
    """Curva que se obtiene de otra (marginales y medias: IMg de IT, CMg y CMe de CT, PMg de PT...): va punteada."""
    return bool(nombre) and any(k in nombre for k in DERIVADAS)

class Plano:
    """Área de dibujo con escala de datos. (x, y) = esquina superior izquierda del área de la gráfica en px.
    xr, yr = rangos de datos (min, max). Todo lo que se dibuja se acumula en self.partes; .svg() devuelve el SVG."""
    def __init__(s, ancho=460, alto=320, xr=(0, 10), yr=(0, 10), margen=(30, 30, 46, 52)):
        s.mt, s.mr, s.mb, s.ml = margen
        s.W, s.H = ancho, alto
        s.x, s.y, s.w, s.h = s.ml, s.mt, ancho - s.ml - s.mr, alto - s.mt - s.mb
        s.xr, s.yr = xr, yr
        s.partes, s._etq, s._pend, s._trazos = [], [], [], []
        s._tr_list, s._guias, s._polis, s._xlab, s._ylab, s._pend_curvas, s._pend_puntos = [], [], [], [], [], [], []
    def X(s, v): return s.x + (v - s.xr[0]) / (s.xr[1] - s.xr[0]) * s.w
    def Y(s, v): return s.y + s.h - (v - s.yr[0]) / (s.yr[1] - s.yr[0]) * s.h
    def _libre(s, x0, y0, w, h):
        """Busca un hueco para una etiqueta (desplaza en vertical hasta no chocar con otras)."""
        for k in range(12):
            for sgn in (1, -1):
                yy = y0 + sgn * k * (h + 3)
                if all(x0 + w < a or x0 > a + aw or yy + h < b or yy > b + bh for a, b, aw, bh in s._etq):
                    s._etq.append((x0, yy, w, h)); return yy
        s._etq.append((x0, y0, w, h)); return y0
    def etiqueta(s, x, y, tex, tam=14, alinear='izq', color=None):
        """Fórmula KaTeX sin chocar con otras etiquetas del plano."""
        w = max(18, len(tex.replace('\\', '').replace('{', '').replace('}', '')) * tam * 0.6 + 10); h = tam * 1.6
        x0 = x if alinear == 'izq' else (x - w if alinear == 'der' else x - w / 2)
        yy = s._libre(x0, y - h / 2, w, h) + h / 2
        s.partes.append(formula_svg(x, yy, tex, tam, ancho=w, alinear=alinear, color=color or COL['tinta']))
    def ejes(s, nx='Q', ny='P', marcas_x=None, marcas_y=None, cuadricula=False, flechas=True):
        """Ejes desde el origen del rango, con flechas, nombres (fórmula) y marcas opcionales (True = automáticas)."""
        x0, y0 = s.X(s.xr[0]), s.Y(s.yr[0])
        mk = (f'<defs><marker id="fl{id(s)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
              f'<path d="M1,1 L9,5 L1,9" fill="none" stroke="{COL["tinta"]}" stroke-width="1.5"/></marker></defs>')
        fin = f' marker-end="url(#fl{id(s)})"' if flechas else ''
        s.partes += [mk, f'<path d="M{_f(x0)},{_f(y0)} L{_f(s.x + s.w + 12)},{_f(y0)}" stroke="{COL["tinta"]}" stroke-width="1.4" fill="none"{fin}/>',
                     f'<path d="M{_f(x0)},{_f(y0)} L{_f(x0)},{_f(s.y - 12)}" stroke="{COL["tinta"]}" stroke-width="1.4" fill="none"{fin}/>']
        s.partes.append(formula_svg(s.x + s.w + 22, y0, nx, 15, alinear='izq'))
        s.partes.append(formula_svg(x0, s.y - 24, ny, 15))
        s._etq += [(s.x + s.w + 18, y0 - 13, 34, 26), (x0 - 20, s.y - 37, 40, 26)]
        s._ejes_segs = [((x0, y0), (s.x + s.w + 12, y0)), ((x0, y0), (x0, s.y - 12))]
        if marcas_x:
            for v in (marcas(*s.xr) if marcas_x is True else marcas_x):
                if v == s.xr[0]: continue
                s.partes.append(f'<path d="M{_f(s.X(v))},{_f(y0)} L{_f(s.X(v))},{_f(y0 + 5)}" stroke="{COL["tinta"]}"/>')
                s.partes.append(_t(s.X(v), y0 + 19, _num(v), 12))
                if cuadricula: s.partes.insert(0, f'<path d="M{_f(s.X(v))},{_f(s.y)} L{_f(s.X(v))},{_f(y0)}" stroke="{COL["tenue"]}" stroke-width=".7"/>')
        if marcas_y:
            for v in (marcas(*s.yr) if marcas_y is True else marcas_y):
                if v == s.yr[0]: continue
                s.partes.append(f'<path d="M{_f(x0 - 5)},{_f(s.Y(v))} L{_f(x0)},{_f(s.Y(v))}" stroke="{COL["tinta"]}"/>')
                s.partes.append(_t(x0 - 9, s.Y(v) + 4, _num(v), 12, 'end'))
                if cuadricula: s.partes.insert(0, f'<path d="M{_f(x0)},{_f(s.Y(v))} L{_f(s.x + s.w)},{_f(s.Y(v))}" stroke="{COL["tenue"]}" stroke-width=".7"/>')
        return s
    def _tramos(s, f, a, b, n=200):
        tr, act = [], []
        for i in range(n + 1):
            v = a + (b - a) * i / n
            try: w = f(v)
            except (ZeroDivisionError, ValueError, OverflowError): w = None
            if w is not None and s.yr[0] <= w <= s.yr[1]: act.append((s.X(v), s.Y(w)))
            elif act: tr.append(act); act = []
        if act: tr.append(act)
        return tr
    def curva(s, f, a=None, b=None, color=None, nombre=None, grosor=2.2, punteada=None):
        """Curva y = f(x) recortada al rango; 'nombre' (LaTeX) se escribe al final de la curva, fuera del trazo."""
        a = s.xr[0] if a is None else a; b = s.xr[1] if b is None else b
        color = color or COL['azul']
        if punteada is None: punteada = es_derivada(nombre)
        da = ' stroke-dasharray="7 5"' if punteada else ''
        for tr in s._tramos(f, a, b):
            s._trazos += tr; s._tr_list.append(tr)
            s.partes.append(f'<path d="M' + ' L'.join(f'{_f(x)},{_f(y)}' for x, y in tr) +
                            f'" fill="none" stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round"{da}/>')
        if nombre:
            tr = s._tramos(f, a, b)
            if tr: s._pend_curvas.append((tr[-1], nombre, color))
        return s
    def vertical(s, xv, color=None, nombre=None, punteada=False):
        x = s.X(xv); da = ' stroke-dasharray="6 4"' if punteada else ''
        s.partes.append(f'<path d="M{_f(x)},{_f(s.Y(s.yr[0]))} L{_f(x)},{_f(s.y)}" stroke="{color or COL["rojo"]}" stroke-width="2.2"{da}/>')
        if nombre: s.etiqueta(x + 6, s.y + 8, nombre, 14, 'izq', color or COL['rojo'])
        return s
    def area(s, f, g, a, b, color=None, opacidad=.22, nombre=None, pos=None):
        """Región entre f (arriba) y g (abajo) de a a b (excedentes, ingreso, pérdida irrecuperable).
        Relleno uniforme sin borde. El nombre va dentro si cabe completo con aire; si la región es chica,
        va afuera, en un hueco libre, con línea guía. Nunca con fondo o recuadro encima de la región."""
        n = 80; xs = [a + (b - a) * i / n for i in range(n + 1)]
        top = [(s.X(v), s.Y(min(max(f(v), s.yr[0]), s.yr[1]))) for v in xs]
        bot = [(s.X(v), s.Y(min(max(g(v), s.yr[0]), s.yr[1]))) for v in reversed(xs)]
        pol = top + bot; s._polis.append(pol)
        s.partes.insert(0, '<polygon points="' + ' '.join(f'{_f(x)},{_f(y)}' for x, y in pol) +
                        f'" fill="{color or COL["azul"]}" fill-opacity="{opacidad}" stroke="none"/>')
        if nombre:
            if pos: s.partes.append(s._rotulo(s.X(pos[0]), s.Y(pos[1]), nombre))
            else: s._pend.append((pol, nombre))
        return s
    def punto(s, xv, yv, etq_x=None, etq_y=None, color=None, nombre=None, guias=None):
        """Punto con punteadas a los ejes. guias=None: vertical solo si hay etq_x y horizontal solo si hay etq_y
        (así una punteada nunca atraviesa áreas sin motivo); guias='xy', 'x', 'y' o '' para forzar.
        Las etiquetas de eje se alinean en columna (eje y, a la derecha) y fila (eje x) y se separan si chocan."""
        X, Y, x0, y0 = s.X(xv), s.Y(yv), s.X(s.xr[0]), s.Y(s.yr[0])
        c = color or COL['tinta']
        g = guias if guias is not None else ('x' if etq_x else '') + ('y' if etq_y else '')
        if 'x' in g:
            s.partes.append(f'<path d="M{_f(X)},{_f(Y)} L{_f(X)},{_f(y0)}" stroke="{c}" stroke-width="1.1" stroke-dasharray="4 3"/>')
            s._guias.append(((X, Y), (X, y0)))
        if 'y' in g:
            s.partes.append(f'<path d="M{_f(X)},{_f(Y)} L{_f(x0)},{_f(Y)}" stroke="{c}" stroke-width="1.1" stroke-dasharray="4 3"/>')
            s._guias.append(((X, Y), (x0, Y)))
        s.partes.append(f'<circle cx="{_f(X)}" cy="{_f(Y)}" r="4" fill="{c}"/>')
        if etq_x: s._xlab.append((X, etq_x))
        if etq_y: s._ylab.append((Y, etq_y))
        if nombre: s._pend_puntos.append((X, Y, nombre, c))
        return s
    # ── colocación de rótulos ──
    @staticmethod
    def _plano_txt(t):
        m = re.fullmatch(r'\\text\{([^{}]*)\}', t)
        if m: return m.group(1)
        return None if re.search(r'[\\^_{}]', t) else t
    def _medida(s, t, tam=14):
        p = s._plano_txt(t)
        if p is not None:
            try: w = geo.medir([p], FUENTE, tam)[0]
            except Exception: w = len(p) * tam * 0.62
            return w + 8, tam * 1.6
        return max(18, len(re.sub(r'\\(text|mathrm|operatorname)|[\\{}^_]', '', t)) * tam * 0.62 + 8), tam * 1.6
    def _rotulo(s, x, y, t, tam=14, color=None):
        # texto simple en la fuente del documento; lo matemático con KaTeX
        p = s._plano_txt(t)
        if p is not None: return _t(x, y + tam * 0.29, p, tam, 'middle', color)
        return formula_svg(x, y, t, tam, color=color or COL['tinta'])
    def _segmentos(s):
        segs = [(a, b) for tr in s._tr_list for a, b in zip(tr, tr[1:])] + list(s._guias)
        return segs
    @staticmethod
    def _dseg(p, a, b):
        (px, py), (ax, ay), (bx, by) = p, a, b
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    @staticmethod
    def _dentro(p, pol):
        x, y = p; r = False
        for (x1, y1), (x2, y2) in zip(pol, pol[1:] + pol[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: r = not r
        return r
    @staticmethod
    def _cruce(p, q, a, b):
        d = (q[0] - p[0]) * (b[1] - a[1]) - (q[1] - p[1]) * (b[0] - a[0])
        if abs(d) < 1e-9: return None
        t = ((a[0] - p[0]) * (b[1] - a[1]) - (a[1] - p[1]) * (b[0] - a[0])) / d
        u = ((a[0] - p[0]) * (q[1] - p[1]) - (a[1] - p[1]) * (q[0] - p[0])) / d
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])) if 0 <= t <= 1 and 0 <= u <= 1 else None
    def _guia_ok(s, p, q, ed):
        """La línea guía solo puede cruzar el borde de su propia región (una vez), nunca otra curva."""
        cruces = []
        for tr in s._tr_list:
            for a, b in zip(tr, tr[1:]):
                c = s._cruce(p, q, a, b)
                if c:
                    if min(s._dseg(c, e1, e2) for e1, e2 in ed) > 2.5: return False
                    if all(math.hypot(c[0] - k[0], c[1] - k[1]) > 4 for k in cruces): cruces.append(c)
        if len(cruces) > 1: return False
        return True
    def _caja_libre(s, cx, cy, w, h, segs, aire=4):
        x0, y0 = cx - w / 2, cy - h / 2
        if x0 < s.x + 2 or x0 + w > s.x + s.w or y0 < s.y - 6 or y0 + h > s.y + s.h - 2: return False
        if any(not (x0 + w + 3 < a or x0 > a + aw + 3 or y0 + h + 3 < b or y0 > b + bh + 3) for a, b, aw, bh in s._etq): return False
        return not any(s._corta_caja(a, b, x0 - aire, y0 - aire, x0 + w + aire, y0 + h + aire) for a, b in segs)
    def _corta_caja(s, a, b, x1, y1, x2, y2):
        """¿El segmento a-b toca el rectángulo (x1, y1)-(x2, y2)?"""
        if max(a[0], b[0]) < x1 or min(a[0], b[0]) > x2 or max(a[1], b[1]) < y1 or min(a[1], b[1]) > y2: return False
        if any(x1 <= p[0] <= x2 and y1 <= p[1] <= y2 for p in (a, b)): return True
        lados = [((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))]
        return any(s._cruce(a, b, p, q) for p, q in lados)
    def _colocar_areas(s):
        segs = s._segmentos()
        for pol, nombre in s._pend:
            w, h = s._medida(nombre)
            ed = list(zip(pol, pol[1:] + pol[:1]))
            xs_, ys_ = [p[0] for p in pol], [p[1] for p in pol]
            mejor, best, polo, dpolo = None, -1, None, -1
            for i in range(1, 30):
                for j in range(1, 30):
                    c = (min(xs_) + (max(xs_) - min(xs_)) * i / 30, min(ys_) + (max(ys_) - min(ys_)) * j / 30)
                    if not s._dentro(c, pol): continue
                    d = min(s._dseg(c, a, b) for a, b in ed + segs)
                    if d > dpolo: dpolo, polo = d, c
                    caja = [(c[0] + dx * w / 2, c[1] + dy * h / 2) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
                    if all(s._dentro(p, pol) for p in caja) and s._caja_libre(c[0], c[1], w, h, segs + ed, 6) and d > best:
                        best, mejor = d, c
            if not mejor:      # región angosta: segunda pasada con la caja justa de la letra (sin achicarla)
                hc = 19
                for i in range(1, 60):
                    for j in range(1, 30):
                        c = (min(xs_) + (max(xs_) - min(xs_)) * i / 60, min(ys_) + (max(ys_) - min(ys_)) * j / 30)
                        caja = [(c[0] + dx * w / 2, c[1] + dy * hc / 2) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
                        if not all(s._dentro(p, pol) for p in caja) or not s._caja_libre(c[0], c[1], w, hc, segs + ed, 2): continue
                        d = min(s._dseg(c, a, b) for a, b in ed + segs)
                        if d > best: best, mejor = d, c
            if mejor:
                s._etq.append((mejor[0] - w / 2, mejor[1] - h / 2, w, h))
                s.partes.append(s._rotulo(mejor[0], mejor[1], nombre)); continue
            # no cabe: afuera, en el hueco libre más cercano, con línea guía desde el interior de la región
            ax, ay = polo; hecho = False
            for r, sobre in [(r, False) for r in range(int(max(w, h) / 2 + 24), 260, 8)] + \
                            [(r, True) for r in range(int(max(w, h) / 2 + 14), 100, 6)]:
                for k in range(24):
                    ang = math.radians(-60 + 15 * k)
                    cx, cy = ax + r * math.cos(ang), ay + r * math.sin(ang)
                    if not sobre and any(s._dentro((cx + dx * w / 2, cy + dy * h / 2), p) for p in s._polis for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                        continue
                    if sobre:
                        mu = [(cx + dx * w / 2, cy + dy * h / 2) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
                        if s._dentro((cx, cy), pol) or not any(all(s._dentro(m, p2) for m in mu) for p2 in s._polis if p2 is not pol):
                            continue
                    if not s._caja_libre(cx, cy, w, h, segs, 5): continue
                    gw, gh = w / 2 - 3, 14 * 0.55
                    ex = max(cx - gw, min(ax, cx + gw)); ey = max(cy - gh, min(ay, cy + gh))
                    L = math.hypot(ex - ax, ey - ay) or 1
                    fx, fy = ex - (ex - ax) / L * 4, ey - (ey - ay) / L * 4
                    if not s._guia_ok((ax, ay), (fx, fy), ed): continue
                    s._etq.append((cx - w / 2, cy - h / 2, w, h))
                    s.partes += [f'<path d="M{_f(ax)},{_f(ay)} L{_f(fx)},{_f(fy)}" stroke="{COL["tinta"]}" stroke-width="1"/>',
                                 f'<circle cx="{_f(ax)}" cy="{_f(ay)}" r="2" fill="{COL["tinta"]}"/>',
                                 s._rotulo(cx, cy, nombre)]
                    hecho = True; break
                if hecho: break
            if not hecho: raise ValueError(f"No hay hueco para la etiqueta {nombre!r}: agranda el lienzo o usa pos=")
        s._pend = []
    def _ejes_etq(s):
        x0, y0 = s.X(s.xr[0]), s.Y(s.yr[0])
        ys = sorted(s._ylab); colocadas = []
        for Y, t in ys:
            h = 16
            yy = max(Y, colocadas[-1][0] + h) if colocadas else Y
            colocadas.append((yy, Y, t))
        for yy, Y, t in colocadas:
            if abs(yy - Y) > 1: s.partes.append(f'<path d="M{_f(x0 - 4)},{_f(Y)} L{_f(x0 - 9)},{_f(yy)}" stroke="{COL["gris"]}" stroke-width=".8"/>')
            s.partes.append(formula_svg(x0 - 12, yy, t, 14, alinear='der'))
        xs = sorted(s._xlab); px = None
        for X, t in xs:
            w, _ = s._medida(t)
            xx = X if px is None else max(X, px + w + 4); px = xx
            s.partes.append(formula_svg(xx, y0 + 30, t, 14))
        s._ylab, s._xlab = [], []
    def _colocar_curvas(s):
        """Nombre de cada curva en el primer lugar libre: al final del trazo si no toca un eje; si no, a lo largo
        de la curva, del lado más despejado. Nunca encima de otra curva, eje o etiqueta."""
        segs = s._segmentos() + getattr(s, '_ejes_segs', [])
        x0, y0 = s.X(s.xr[0]), s.Y(s.yr[0])
        for X, Y, nombre, color in s._pend_puntos:          # nombre de un punto (EN, S, A...): alrededor, sin tocar nada
            w, h = s._medida(nombre, 13); h = 20
            cand = [(X + math.cos(math.radians(a)) * (r + w / 2), Y - math.sin(math.radians(a)) * (r + h / 2 - 4))
                    for r in (8, 14, 22, 32) for a in (45, 135, 0, 180, 315, 225, 90, 270)]
            sitio = s._mejor(cand, w, h, segs, 12)
            s._etq.append((sitio[0] - w / 2, sitio[1] - h / 2, w, h))
            s.partes.append(s._rotulo(sitio[0], sitio[1], nombre, 13, color))
        s._pend_puntos = []
        for tr, nombre, color in s._pend_curvas:
            w, h = s._medida(nombre); h = 20
            cand = []
            xe, ye = tr[-1]
            if ye < y0 - 14 and xe > x0 + 14:
                cand += [(xe + 8 + w / 2, ye - 10), (xe + 8 + w / 2, ye + 12), (xe + 6 + w / 2, ye)]
            L = [0]
            for p, q in zip(tr, tr[1:]): L.append(L[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
            for fr in [k / 20 for k in range(18, 1, -1)]:
                t = fr * L[-1]; i = max(k for k in range(len(L)) if L[k] <= t); i = min(i, len(tr) - 2)
                (ax, ay), (bx, by) = tr[i], tr[i + 1]; dl = math.hypot(bx - ax, by - ay) or 1
                px, py = ax + (bx - ax) * (t - L[i]) / dl, ay + (by - ay) * (t - L[i]) / dl
                nx_, ny_ = -(by - ay) / dl, (bx - ax) / dl
                for sg in (-1, 1):
                    for extra in (7, 16):
                        d = abs(nx_) * w / 2 + abs(ny_) * h / 2 + extra
                        cand.append((px + sg * nx_ * d, py + sg * ny_ * d))
            sitio = s._mejor(cand, w, h, segs, 22) or tr[-1]
            s._etq.append((sitio[0] - w / 2, sitio[1] - h / 2, w, h))
            col = '#55524B' if color == COL['gris'] else color
            s.partes.append(s._rotulo(sitio[0], sitio[1], nombre, 14, col) if nombre.startswith('\\text')
                            else formula_svg(sitio[0], sitio[1], nombre, 14, ancho=w, color=col))
        s._pend_curvas = []
    def _mejor(s, cand, w, h, segs, tope):
        """Entre los candidatos libres (primero fuera de áreas), el de más aire (hasta 'tope' px); a igual aire, el primero."""
        for sobre in (False, True):
            libres = [(min(s._holgura(cx, cy, w, h, segs), tope) - 0.01 * i, (cx, cy)) for i, (cx, cy) in enumerate(cand)
                      if s._hueco(cx, cy, w, h, segs, sobre)]
            if libres: return max(libres)[1]
        return max(cand, key=lambda c: s._holgura(c[0], c[1], w, h, segs)) if cand else None
    def _holgura(s, cx, cy, w, h, segs):
        pts = [(cx - w / 2 + w * i / 4, cy - h / 2 + h * j / 2) for i in range(5) for j in range(3)]
        x0, y0 = s.X(s.xr[0]), s.Y(s.yr[0])
        if cx - w / 2 < x0 + 3 or cy + h / 2 > y0 - 3 or cy - h / 2 < 2 or cx + w / 2 > s.W - 2: return -99
        if any(not (cx - w / 2 + w + 3 < a or cx - w / 2 > a + aw + 3 or cy - h / 2 + h + 3 < b or cy - h / 2 > b + bh + 3) for a, b, aw, bh in s._etq): return -50
        return min(s._dseg(p, a, b) for p in pts for a, b in segs)
    def _hueco(s, cx, cy, w, h, segs, sobre=False):
        x0, y0 = s.X(s.xr[0]), s.Y(s.yr[0])
        bx0, by0 = cx - w / 2, cy - h / 2
        if bx0 < x0 + 3 or bx0 + w > s.W - 2 or by0 < 2 or by0 + h > y0 - 3: return False
        if any(not (bx0 + w + 3 < a or bx0 > a + aw + 3 or by0 + h + 3 < b or by0 > b + bh + 3) for a, b, aw, bh in s._etq): return False
        pts = [(bx0 + w * i / 4, by0 + h * j / 2) for i in range(5) for j in range(3)]
        if not sobre and any(s._dentro(p, pol) for p in pts for pol in s._polis): return False
        return not any(s._corta_caja(a, b, bx0 - 4, by0 - 4, bx0 + w + 4, by0 + h + 4) for a, b in segs)
    def svg(s):
        s._colocar_curvas(); s._colocar_areas(); s._ejes_etq()
        return f'<svg width="{s.W}" height="{s.H}" viewBox="0 0 {s.W} {s.H}" style="display:block;overflow:visible">' + ''.join(s.partes) + '</svg>'

def interseccion(f, g, a, b, n=400):
    """Todas las x en [a, b] donde f = g (bisección)."""
    h = lambda v: f(v) - g(v); out = []
    xs = [a + (b - a) * i / n for i in range(n + 1)]
    for u, v in zip(xs, xs[1:]):
        try: hu, hv = h(u), h(v)
        except (ZeroDivisionError, ValueError): continue
        if hu == 0: out.append(u)
        elif hu * hv < 0:
            for _ in range(60):
                m = (u + v) / 2
                if h(u) * h(m) <= 0: v = m
                else: u = m
            out.append((u + v) / 2)
    return out


# ═════════════ Teoría de juegos: árbol en forma extensiva ═════════════

def _hojas(n):
    return 1 if isinstance(n, tuple) else sum(_hojas(c) for c in n['a'].values())

def arbol(raiz, nivel=None, sep=None, jugadores=None, subjuegos=True, resolver=False, tam=13, orientacion='horizontal'):
    """Árbol de forma extensiva acomodado solo. orientacion='horizontal' (raíz a la izquierda, pagos en columna
    a la derecha; así lo presentan en clase) o 'vertical' (raíz arriba).
    raiz: {'j': '1', 'a': {'Montaña': nodo_o_pago, ...}, 'info': 'h1'(opcional)}; pagos = tuplas (u1, u2, ...).
    Nodos con la misma 'info' forman un conjunto de información (recuadro azul punteado).
    subjuegos: recuadro verde punteado alrededor de cada subjuego propio. resolver: marca el ENPS (solo info perfecta).
    Devuelve (svg, datos): datos['estrategias'], datos['enps'] = [(jugador, historia, acción), ...], datos['info_perfecta']."""
    H = orientacion == 'horizontal'
    def _pagos(n): return [n] if isinstance(n, tuple) else [p for c in n['a'].values() for p in _pagos(c)]
    txt_pago = lambda p: '(' + ', '.join(_num(v) for v in p) + ')'
    wmax = max(len(txt_pago(p)) * tam * 0.55 for p in _pagos(raiz))
    if H:
        nivel = nivel or 150; sep = sep or max(58, tam * 4.4)
    else:
        nivel = nivel or 86; sep = max(sep or 78, wmax + 46)
    nodos, hojas = [], []
    def colocar(n, prof, x0, padre=None, accion=None):
        if isinstance(n, tuple):
            hojas.append({'pago': n, 'x': x0 + sep / 2, 'prof': prof}); d = hojas[-1]
        else:
            hijos, xa = [], x0
            d = {'n': n, 'prof': prof, 'hijos': hijos, 'ruta': (padre['ruta'] + (accion,)) if padre else ()}
            for acc, h in n['a'].items():
                k = _hojas(h); hijos.append((acc, colocar(h, prof + 1, xa, d, acc))); xa += k * sep
            d['x'] = sum(c['x'] for _, c in hijos) / len(hijos)
            nodos.append(d)
        return d
    rd = colocar(raiz, 0, 0)
    pmax = max(h['prof'] for h in hojas)
    if H:
        X0, Y0 = 70, 20
        P = lambda d: (X0 + (pmax if 'pago' in d else d['prof']) * nivel, Y0 + d['x'])
    else:
        X0, Y0 = 40, 36
        P = lambda d: (X0 + d['x'], Y0 + (pmax if 'pago' in d else d['prof']) * nivel)
    infos = {}
    for d in nodos: infos.setdefault(d['n'].get('info', id(d)), []).append(d)
    perfecta = all(len(v) == 1 for v in infos.values())
    elegido = {}
    def valor(d):
        if 'pago' in d: return d['pago']
        if d['n']['j'] == 'N':                          # Naturaleza: valor esperado con sus probabilidades
            pr = d['n'].get('p', {})
            vs = [(pr.get(a, 1 / len(d['hijos'])), valor(c)) for a, c in d['hijos']]
            return tuple(sum(p * v[i] for p, v in vs) for i in range(len(vs[0][1])))
        j = int(d['n']['j']) - 1
        mejor = max(d['hijos'], key=lambda ac: valor(ac[1])[j])
        elegido[id(d)] = mejor[0]
        return valor(mejor[1])
    if resolver and perfecta: valor(rd)
    out, cajas = [], {}          # cajas[id] = lista de rectángulos (x1, y1, x2, y2) que debe abarcar un subjuego
    def caja(d, r): cajas.setdefault(id(d), []).append(r)
    # etiquetas de acción: separadas en perpendicular a la rama, del lado de afuera
    etq = []
    for d in nodos:
        x1, y1 = P(d)
        for acc, c in d['hijos']:
            x2, y2 = P(c); dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1
            if H:
                t = 0.4 if 'pago' not in c else min(0.5, nivel * 0.5 / max(1, dx))
                afuera = dy > 0                                  # rama que baja: etiqueta abajo
                nx_, ny_ = ((-dy / L, dx / L) if afuera else (dy / L, -dx / L))
                if abs(dy) < 1: nx_, ny_ = 0, -1
            else:
                t = 0.42 if 'pago' not in c else min(0.42, nivel * 0.42 / max(1, dy))
                afuera = dx < 0
                nx_, ny_ = ((-dy / L, dx / L) if afuera else (dy / L, -dx / L))
            mx, my = x1 + dx * t, y1 + dy * t
            ex, ey = mx + nx_ * 15, my + ny_ * 15
            if d['n']['j'] == 'N' and acc in d['n'].get('p', {}): acc = f"{acc} ({_num(d['n']['p'][acc])})"
            w = len(acc) * tam * 0.56
            anc = 'end' if (H or afuera) else 'start'
            if H and abs(dy) < 1: anc = 'middle'
            bx1 = ex - w if anc == 'end' else (ex - w / 2 if anc == 'middle' else ex)
            yb = ey + tam * 0.35 + (tam * 0.5 if H and afuera else 0)
            etq.append((d, acc, ex, yb, anc))
            caja(d, (bx1, yb - tam, bx1 + w, yb + 4))
    # pagos
    pagos_pos = []
    for h in hojas:
        x, y = P(h); w = len(txt_pago(h['pago'])) * tam * 0.55
        if H: px, py, anc, r = x + 10, y + tam * 0.35, 'start', (x, y - tam, x + 10 + w, y + tam * 0.6)
        else: px, py, anc, r = x, y + 24, 'middle', (x - w / 2, y, x + w / 2, y + 30)
        pagos_pos.append((h, px, py, anc, r))
    nombres = []                 # (x, y, texto, anclaje) de cada jugador; cuentan para los recuadros de subjuego
    for d in nodos:
        x, y = P(d)
        grupo = infos[d['n'].get('info', id(d))]
        nombre = (jugadores or {}).get(d['n']['j'], 'Naturaleza' if d['n']['j'] == 'N' else f"J{d['n']['j']}")
        if d is rd:
            pos = (x - 12, y + 5, 'end') if H else (x, y - 13, 'middle')
        elif len(grupo) > 1:
            if d is not min(grupo, key=lambda g: g['x']): continue
            pos = (x - 20, P(d)[1] - 20, 'end') if H else (x - 22, y + 5, 'end')
        else:
            padre = next(p for p in nodos if any(c is d for _, c in p['hijos']))
            if H:
                abajo = P(padre)[1] < y               # la rama llega desde arriba: nombre abajo
                pos = (x - 4, y + 20, 'end') if abajo else (x - 4, y - 10, 'end')
            else:
                derecha = P(padre)[0] < x
                pos = (x + 12, y + 5, 'start') if derecha else (x - 12, y + 5, 'end')
        nombres.append((d, nombre) + pos)
        w = len(nombre) * (tam + 1) * 0.6
        bx = pos[0] - w if pos[2] == 'end' else (pos[0] - w / 2 if pos[2] == 'middle' else pos[0])
        caja(d, (bx, pos[1] - tam - 2, bx + w, pos[1] + 4))
    def sub(d):
        r = [d] if 'pago' not in d else []
        for _, c in d.get('hijos', []): r += sub(c)
        return r
    def es_sub(d):
        if d is rd or len(infos[d['n'].get('info', id(d))]) > 1: return False
        dd = sub(d); return all(all(m in dd for m in infos[m['n'].get('info', id(m))]) for m in dd)
    raices_sub = [d for d in nodos if es_sub(d)]
    if subjuegos:
        rects = []
        for d in sorted(raices_sub, key=lambda d: d['prof']):
            dentro = sub(d)
            rs = [(P(m)[0] - 8, P(m)[1] - 8, P(m)[0] + 8, P(m)[1] + 8) for m in dentro]
            for m in dentro: rs += cajas.get(id(m), [])
            rs += [r for h, *_, r in pagos_pos if any(h is c for m in dentro for _, c in m['hijos'])]
            anid = max([sum(1 for e in dentro if e is not d and e in raices_sub and m in sub(e)) for m in dentro] or [0])
            pad = 10 + 8 * anid
            rects.append([min(r[0] for r in rs) - pad, min(r[1] for r in rs) - pad,
                          max(r[2] for r in rs) + pad, max(r[3] for r in rs) + pad, set(map(id, dentro))])
        # recuadros hermanos (no anidados) nunca se tocan: se reparte el hueco entre ambos
        for a in rects:
            for b in rects:
                if a is b or a[4] & b[4]: continue
                if a[0] < b[2] and b[0] < a[2]:
                    k = 1 if H else 0                       # eje en que se apilan los hermanos
                    if a[k] < b[k] and a[k + 2] > b[k] - 8:
                        m = (a[k + 2] + b[k]) / 2; a[k + 2], b[k] = m - 4, m + 4
        for x1, y1, x2, y2, _ in rects:
            out.append(f'<rect x="{_f(x1)}" y="{_f(y1)}" width="{_f(x2 - x1)}" height="{_f(y2 - y1)}" rx="12" fill="none" '
                       f'stroke="{COL["verde"]}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    for d in nodos:
        x1, y1 = P(d)
        for acc, c in d['hijos']:
            x2, y2 = P(c)
            marcado = elegido.get(id(d)) == acc
            out.append(f'<path d="M{_f(x1)},{_f(y1)} L{_f(x2)},{_f(y2)}" stroke="{COL["rojo"] if marcado else COL["tinta"]}" '
                       f'stroke-width="{3 if marcado else 1.5}" fill="none"/>')
    for _, acc, ex, ey, anc in etq: out.append(_t(ex, ey, acc, tam, anc))
    for clave, ds in infos.items():
        if len(ds) < 2: continue
        xs = [P(d)[0] for d in ds]; ys = [P(d)[1] for d in ds]
        out.append(f'<rect x="{_f(min(xs) - 16)}" y="{_f(min(ys) - 16)}" width="{_f(max(xs) - min(xs) + 32)}" '
                   f'height="{_f(max(ys) - min(ys) + 32)}" rx="16" fill="none" stroke="{COL["azul"]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    for d in nodos:
        x, y = P(d)
        if d['n']['j'] == 'N': out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="6" fill="#FFFFFF" stroke="{COL["tinta"]}" stroke-width="1.8"/>')
        else: out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="5" fill="{COL["rojo"]}"/>')
    for d, nombre, x, y, anc in nombres:
        nat = d['n']['j'] == 'N'
        out.append(_t(x, y, nombre, tam + 1, anc, COL['tinta'] if nat else COL['rojo'], 400 if nat else 700))
    for h, px, py, anc, r in pagos_pos:
        x, y = P(h)
        out.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="2.5" fill="{COL["tinta"]}"/>')
        out.append(_t(px, py, txt_pago(h['pago']), tam, anc))
    if H:
        ancho = int(X0 + pmax * nivel + 10 + wmax + 40)
        alto = int(Y0 * 2 + len(hojas) * sep + 10)
    else:
        ancho = int(X0 * 2 + len(hojas) * sep)
        alto = int(Y0 + pmax * nivel + 50)
    estr = {}
    for clave, ds in infos.items():
        j = ds[0]['n']['j']
        if j != 'N': estr[j] = estr.get(j, 1) * len(ds[0]['n']['a'])
    enps = [((jugadores or {}).get(d['n']['j'], 'J' + d['n']['j']), ' → '.join(d['ruta']) or 'inicio', elegido[id(d)])
            for d in sorted(nodos, key=lambda d: (d['prof'], d['x'])) if id(d) in elegido]
    datos = {'estrategias': estr, 'enps': enps if resolver and perfecta else None, 'info_perfecta': perfecta}
    return (f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" style="display:block;overflow:visible">' + ''.join(out) + '</svg>', datos)


# ═════════════ Teoría de juegos: matriz de pagos ═════════════

def matriz_pagos(filas, columnas, pagos, jug_fila='Jugador 1', jug_col='Jugador 2', leyenda=True, dominadas=False, mixtas=False):
    """Matriz m×n con mejores respuestas subrayadas (verde = fila, rojo = columna), Equilibrio de Nash en óvalo
    y 'OP' (óptimo de Pareto) en su fila reservada. pagos[i][j] = (u_fila, u_col). Devuelve (html, datos).
    dominadas=True: eliminación iterada de estrategias estrictamente dominadas (tachadas, con su orden).
    mixtas=True (2×2): equilibrio en estrategias mixtas; p y 1 − p bajo las filas, q y 1 − q bajo las columnas."""
    m, n = len(filas), len(columnas)
    vivas_f, vivas_c, orden = list(range(m)), list(range(n)), []
    if dominadas:
        cambio = True
        while cambio:
            cambio = False
            for i in list(vivas_f):
                if any(all(pagos[k][j][0] > pagos[i][j][0] for j in vivas_c) for k in vivas_f if k != i):
                    vivas_f.remove(i); orden.append(('fila', i)); cambio = True; break
            if cambio: continue
            for j in list(vivas_c):
                if any(all(pagos[i][k][1] > pagos[i][j][1] for i in vivas_f) for k in vivas_c if k != j):
                    vivas_c.remove(j); orden.append(('columna', j)); cambio = True; break
    num = {('fila', i): k + 1 for k, (t, i) in enumerate(orden) if t == 'fila'}
    num.update({('columna', j): k + 1 for k, (t, j) in enumerate(orden) if t == 'columna'})
    mix = None
    if mixtas and m == 2 and n == 2:
        a = [[pagos[i][j][0] for j in range(2)] for i in range(2)]; b = [[pagos[i][j][1] for j in range(2)] for i in range(2)]
        dq = a[0][0] - a[0][1] - a[1][0] + a[1][1]; dp = b[0][0] - b[1][0] - b[0][1] + b[1][1]
        if dq and dp:
            q = (a[1][1] - a[0][1]) / dq; p = (b[1][1] - b[1][0]) / dp
            if 0 < p < 1 and 0 < q < 1: mix = {'p': p, 'q': q}
    mr_f = {(i, j) for j in range(n) for i in range(m) if pagos[i][j][0] == max(pagos[k][j][0] for k in range(m))}
    mr_c = {(i, j) for i in range(m) for j in range(n) if pagos[i][j][1] == max(pagos[i][k][1] for k in range(n))}
    en = mr_f & mr_c
    celdas = [(i, j) for i in range(m) for j in range(n)]
    def domina(a, b):
        pa, pb = pagos[a[0]][a[1]], pagos[b[0]][b[1]]
        return all(x >= y for x, y in zip(pa, pb)) and any(x > y for x, y in zip(pa, pb))
    op = {c for c in celdas if not any(domina(o, c) for o in celdas if o != c)}
    css = (f'<style>.mp{{border-collapse:collapse;font-family:{FUENTE},sans-serif;break-inside:avoid;margin:6px 0}}'
           f'.mp th{{font-weight:400;font-size:13px;padding:2px 10px;white-space:nowrap}}'
           f'.mp td.c{{border:1.5px solid {COL["tinta"]};padding:3px 14px 10px;min-width:92px;text-align:center;vertical-align:top;font-size:16px}}'
           f'.mp .op{{height:15px;font-size:11px;line-height:15px;color:{COL["azul"]};text-align:right;margin-right:-8px}}'
           f'.mp .uf{{text-decoration:underline solid {COL["verde"]} 2px;text-underline-offset:.1em}}'
           f'.mp .uc{{text-decoration:underline solid {COL["rojo"]} 2px;text-underline-offset:.1em}}'
           f'.mp .en{{display:inline-block;border:1.5px solid {COL["tinta"]};border-radius:50%;padding:3px 12px 9px}}'
           f'.mpl{{font-family:{FUENTE},sans-serif;font-size:13px;color:{COL["tinta"]}}}'
           f'.mp .tach{{text-decoration:line-through {COL["rojo"]} 2px}} .mp td.x{{color:#55524B;background:#F6F3EA}}'
           f'.mp .ord{{font-size:11px;color:{COL["rojo"]};margin-left:3px}} .mp .pr{{display:block;font-size:11px;color:{COL["azul"]}}}</style>')
    h = [css, '<table class="mp"><tr><th></th><th></th>',
         f'<th colspan="{n}" style="color:{COL["rojo"]};font-size:14px">{jug_col}</th></tr><tr><th></th><th></th>']
    def cab(txt, tipo, k):
        t = f'<span class="tach">{txt}</span><span class="ord">{num[(tipo, k)]}</span>' if (tipo, k) in num else txt
        if mix: t += f'<span class="pr">{("p" if k == 0 else "1−p") if tipo == "fila" else ("q" if k == 0 else "1−q")} = {(mix["p"] if k == 0 else 1 - mix["p"]) if tipo == "fila" else (mix["q"] if k == 0 else 1 - mix["q"]):.3g}</span>'
        return t
    h += [f'<th style="color:{COL["rojo"]}">{cab(c, "columna", j)}</th>' for j, c in enumerate(columnas)] + ['</tr>']
    for i, f in enumerate(filas):
        h.append('<tr>')
        if i == 0: h.append(f'<th rowspan="{m}" style="color:{COL["verde"]};font-size:14px;writing-mode:vertical-rl;transform:rotate(180deg)">{jug_fila}</th>')
        h.append(f'<th style="color:{COL["verde"]};text-align:right">{cab(f, "fila", i)}</th>')
        for j in range(n):
            a, b = pagos[i][j]
            if dominadas and (i not in vivas_f or j not in vivas_c):
                h.append(f'<td class="c x"><div class="op"></div>{_num(a)}, {_num(b)}</td>'); continue
            sa = f'<span class="uf">{_num(a)}</span>' if (i, j) in mr_f else _num(a)
            sb = f'<span class="uc">{_num(b)}</span>' if (i, j) in mr_c else _num(b)
            par = f'{sa}, {sb}'
            if (i, j) in en: par = f'<span class="en">{par}</span>'
            h.append(f'<td class="c"><div class="op">{"OP" if (i, j) in op else ""}</div>{par}</td>')
        h.append('</tr>')
    h.append('</table>')
    if leyenda:
        h.append(f'<div class="mpl">○ = EN · <span style="color:{COL["verde"]}">verde</span> = mejor resp. fila · '
                 f'<span style="color:{COL["rojo"]}">rojo</span> = mejor resp. columna · <span style="color:{COL["azul"]}">OP</span> = óptimo de Pareto</div>')
    if leyenda and orden:
        h.append('<div class="mpl">Eliminación de dominadas: ' + ' · '.join(
            f'{k + 1}) {filas[i] if t == "fila" else columnas[i]}' for k, (t, i) in enumerate(orden)) + '</div>')
    if leyenda and mix:
        h.append(f'<div class="mpl">Equilibrio en mixtas: <span style="color:{COL["azul"]}">p</span> hace indiferente a {jug_col}; '
                 f'<span style="color:{COL["azul"]}">q</span> hace indiferente a {jug_fila}</div>')
    datos = {'nash': [(filas[i], columnas[j]) for i, j in sorted(en)], 'pareto': [(filas[i], columnas[j]) for i, j in sorted(op)],
             'eliminadas': [(t, filas[i] if t == 'fila' else columnas[i]) for t, i in orden],
             'sobreviven': ([filas[i] for i in vivas_f], [columnas[j] for j in vivas_c]), 'mixta': mix}
    return ''.join(h), datos


# ═════════════ Estadística ═════════════

def _cuantil(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = math.floor(k); c = math.ceil(k)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def histograma(datos, clases=None, ancho=460, alto=300, color=None, nx='x', ny='f'):
    a, b = min(datos), max(datos)
    k = clases or max(5, round(1 + 3.322 * math.log10(len(datos))))
    paso = (b - a) / k or 1
    cuentas = [0] * k
    for v in datos: cuentas[min(k - 1, int((v - a) / paso))] += 1
    p = Plano(ancho, alto, (a, b), (0, max(cuentas) * 1.15))
    for i, c in enumerate(cuentas):
        x1, x2 = p.X(a + i * paso), p.X(a + (i + 1) * paso)
        p.partes.append(f'<rect x="{_f(x1 + 1)}" y="{_f(p.Y(c))}" width="{_f(x2 - x1 - 2)}" height="{_f(p.Y(0) - p.Y(c))}" '
                        f'fill="{color or COL["azul"]}" fill-opacity=".75"/>')
    p.ejes(nx, ny, marcas_x=True, marcas_y=True, flechas=False)
    return p.svg()

def caja(grupos, ancho=460, alto=None, color=None, nx='x'):
    """Diagrama de caja horizontal. grupos: {'nombre': [datos], ...}. Bigotes a 1.5·RIC; atípicos como puntos."""
    alto = alto or 70 + 56 * len(grupos)
    todos = [v for g in grupos.values() for v in g]
    lo, hi = min(todos), max(todos); pad = (hi - lo) * 0.08 or 1
    p = Plano(ancho, alto, (lo - pad, hi + pad), (0, len(grupos)), margen=(20, 30, 46, 90))
    for k, (nom, g) in enumerate(grupos.items()):
        q1, me, q3 = _cuantil(g, .25), _cuantil(g, .5), _cuantil(g, .75); ric = q3 - q1
        bi = min(v for v in g if v >= q1 - 1.5 * ric); bs = max(v for v in g if v <= q3 + 1.5 * ric)
        yc = p.Y(k + .5); hh = 16; c = color or COL['azul']
        p.partes += [f'<path d="M{_f(p.X(bi))},{_f(yc)} L{_f(p.X(q1))},{_f(yc)} M{_f(p.X(q3))},{_f(yc)} L{_f(p.X(bs))},{_f(yc)}" stroke="{COL["tinta"]}" stroke-width="1.4"/>',
                     f'<path d="M{_f(p.X(bi))},{_f(yc - 8)} L{_f(p.X(bi))},{_f(yc + 8)} M{_f(p.X(bs))},{_f(yc - 8)} L{_f(p.X(bs))},{_f(yc + 8)}" stroke="{COL["tinta"]}" stroke-width="1.4"/>',
                     f'<rect x="{_f(p.X(q1))}" y="{_f(yc - hh)}" width="{_f(p.X(q3) - p.X(q1))}" height="{2 * hh}" fill="{c}" fill-opacity=".25" stroke="{c}" stroke-width="1.6"/>',
                     f'<path d="M{_f(p.X(me))},{_f(yc - hh)} L{_f(p.X(me))},{_f(yc + hh)}" stroke="{COL["rojo"]}" stroke-width="2.4"/>']
        for v in g:
            if v < bi or v > bs: p.partes.append(f'<circle cx="{_f(p.X(v))}" cy="{_f(yc)}" r="3.5" fill="none" stroke="{COL["rojo"]}" stroke-width="1.5"/>')
        p.partes.append(_t(p.x - 12, yc + 4, nom, 13, 'end'))
    p.ejes(nx, '', marcas_x=True, flechas=False)
    return p.svg()

def dispersion(xs, ys, ancho=460, alto=320, recta=True, nx='x', ny='y', color=None):
    """Dispersión con recta de mínimos cuadrados y su ecuación. Devuelve (svg, {'b0','b1','r2'})."""
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys)); sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    b1 = sxy / sxx; b0 = my - b1 * mx; r2 = sxy ** 2 / (sxx * syy)
    padx = (max(xs) - min(xs)) * .08; pady = (max(ys) - min(ys)) * .12
    p = Plano(ancho, alto, (min(xs) - padx, max(xs) + padx), (min(ys) - pady, max(ys) + pady), margen=(30, 120, 46, 52))
    p.ejes(nx, ny, marcas_x=True, marcas_y=True, flechas=False, cuadricula=True)
    for a, b in zip(xs, ys):
        p.partes.append(f'<circle cx="{_f(p.X(a))}" cy="{_f(p.Y(b))}" r="3.6" fill="{color or COL["azul"]}" fill-opacity=".8"/>')
    if recta:
        p.curva(lambda v: b0 + b1 * v, color=COL['rojo'], grosor=2)
        p.etiqueta(p.x + p.w + 6, p.Y(b0 + b1 * p.xr[1]) - 6, rf'\hat y = {b0:.2f} {"+" if b1 >= 0 else "-"} {abs(b1):.2f}\,x', 13, 'izq', COL['rojo'])
        p.etiqueta(p.x + p.w + 6, p.Y(b0 + b1 * p.xr[1]) + 22, rf'R^2 = {r2:.2f}', 13, 'izq')
    return p.svg(), {'b0': b0, 'b1': b1, 'r2': r2}

def binomial(n, prob, resaltar=None, ancho=460, alto=300):
    """Barras de la binomial B(n, p). resaltar=(k1, k2) sombrea P(k1 ≤ X ≤ k2) y escribe su valor."""
    pm = [math.comb(n, k) * prob ** k * (1 - prob) ** (n - k) for k in range(n + 1)]
    p = Plano(ancho, alto, (-0.6, n + 0.6), (0, max(pm) * 1.2))
    w = p.w / (n + 1.2) * 0.7
    for k, v in enumerate(pm):
        dentro = resaltar and resaltar[0] <= k <= resaltar[1]
        p.partes.append(f'<rect x="{_f(p.X(k) - w / 2)}" y="{_f(p.Y(v))}" width="{_f(w)}" height="{_f(p.Y(0) - p.Y(v))}" '
                        f'fill="{COL["rojo"] if dentro else COL["azul"]}" fill-opacity="{.8 if dentro else .45}"/>')
    paso = max(1, round(n / 10))
    p.ejes('k', r'\mathbb{P}(X=k)', marcas_x=list(range(0, n + 1, paso)), marcas_y=True, flechas=False)
    if resaltar:
        s = sum(pm[resaltar[0]:resaltar[1] + 1])
        p.etiqueta(p.x + p.w - 4, p.y + 6, rf'\mathbb{{P}}({resaltar[0]}\le X\le {resaltar[1]}) = {s:.4f}', 13, 'der', COL['rojo'])
    return p.svg()

class CurvaF(Curva):
    """Densidad F de Fisher con (d1, d2) grados de libertad; misma interfaz que Curva."""
    def __init__(s, x, y_base, ancho, alto, d1, d2, xmax=None, pasos=200):
        s.d1, s.d2 = d1, d2
        s.x0, s.yb, s.w, s.h, s.tipo, s.df, s.pasos = x, y_base, ancho, alto, 'f', (d1, d2), pasos
        s.a, s.b = 0.0, xmax or max(4.0, 5 * (d2 / (d2 - 2) if d2 > 2 else 2))
        s._max = max(s.f(s.a + (s.b - s.a) * i / 400) for i in range(1, 401))
    def f(s, x):
        if x <= 0: return 0.0
        d1, d2 = s.d1, s.d2
        ln = (0.5 * d1 * math.log(d1 * x) + 0.5 * d2 * math.log(d2) - 0.5 * (d1 + d2) * math.log(d1 * x + d2)
              - math.log(x) - (math.lgamma(d1 / 2) + math.lgamma(d2 / 2) - math.lgamma((d1 + d2) / 2)))
        return math.exp(ln)


# ═════════════ Línea de tiempo ═════════════

def linea_tiempo(eventos, ancho=900, tam=13, ancho_etq=150, color=None):
    """Eventos [(año, 'texto'), ...] a escala; etiquetas alternadas arriba/abajo en niveles para que nunca choquen.
    El texto se parte con medición real (geo.envolver). Devuelve el SVG con la altura justa."""
    eventos = sorted(eventos)
    a, b = eventos[0][0], eventos[-1][0]; pad = (b - a) * 0.04 or 1
    x0, x1 = 30, ancho - 30
    X = lambda v: x0 + (v - (a - pad)) / ((b + pad) - (a - pad)) * (x1 - x0)
    lineas = [geo.envolver(t, ancho_etq, FUENTE, tam) for _, t in eventos]
    todas = [l for ls in lineas for l in ls] + [str(y) for y, _ in eventos]
    w_med = dict(zip(todas, geo.medir(todas, FUENTE, tam)))
    lh = tam * 1.7; cajas = []
    def cubre(q, x, m=6): return q['izq'] - m <= x <= q['izq'] + q['w'] + m
    def choca(p_, q): return not (p_['izq'] + p_['w'] + 10 < q['izq'] or p_['izq'] > q['izq'] + q['w'] + 10)
    def valido(q):
        if q['izq'] < 4 or q['izq'] + q['w'] > ancho - 4: return False
        for o in cajas:
            if o['lado'] != q['lado']: continue
            if o['nv'] == q['nv'] and choca(o, q): return False
            if o['nv'] < q['nv'] and cubre(o, q['gx']): return False
            if o['nv'] > q['nv'] and cubre(q, o['gx']): return False
        return True
    for k, ((anio, _), ls) in enumerate(zip(eventos, lineas)):
        w = max([w_med[l] for l in ls] + [w_med[str(anio)]]) + 12
        h = (len(ls) + 1) * lh + 8
        cx = X(anio); colocada = None
        # guía recta (gx = cx) si se puede; si no, guía con codo hacia una columna libre cercana
        for gdist in [0] + [d * s for d in range(14, 260, 14) for s in (1, -1)]:
            for nv in range(6 if gdist else 12):
                for lado in ((1, -1) if k % 2 == 0 else (-1, 1)):
                    gx = cx + gdist
                    for izq in sorted({gx - w / 2} | {gx - w + 8 + t for t in range(0, int(w - 15), 10)}, key=lambda v: abs(v + w / 2 - gx)):
                        nb = dict(anio=anio, ls=ls, cx=cx, gx=gx, izq=izq, w=w, h=h, lado=lado, nv=nv)
                        if valido(nb): colocada = nb; break
                    if colocada: break
                if colocada: break
            if colocada: break
        if not colocada:
            colocada = dict(anio=anio, ls=ls, cx=cx, gx=cx, izq=min(max(cx - w / 2, 4), ancho - 4 - w), w=w, h=h, lado=1,
                            nv=1 + max([c['nv'] for c in cajas if c['lado'] == 1], default=-1))
        cajas.append(colocada)
    caj = [(c['anio'], c['ls'], c['cx'], c['izq'], c['w'], c['h'], c['lado'], c['nv'], c['gx']) for c in cajas]
    hmax = max(c[5] for c in caj)
    nmax = {sd: max([c[7] for c in caj if c[6] == sd], default=-1) for sd in (1, -1)}
    arriba = (nmax[1] + 1) * (hmax + 14) + 20
    abajo = (nmax[-1] + 1) * (hmax + 14) + 20
    ye = arriba + 10; alto = int(ye + abajo + 10)
    c0 = color or COL['azul']
    out = [f'<path d="M{x0},{_f(ye)} L{x1},{_f(ye)}" stroke="{COL["tinta"]}" stroke-width="2"/>']
    for anio, ls, cx, izq, w, h, lado, nv, gx in caj:
        top = ye - 20 - nv * (hmax + 14) - h if lado == 1 else ye + 20 + nv * (hmax + 14)
        yl = top + h if lado == 1 else top
        yc = ye - 10 * lado
        guia = f'M{_f(cx)},{_f(ye)} L{_f(gx)},{_f(yl)}' if abs(gx - cx) < 1 else \
               f'M{_f(cx)},{_f(ye)} L{_f(cx)},{_f(yc)} L{_f(gx)},{_f(yc)} L{_f(gx)},{_f(yl)}'
        out += [f'<path d="{guia}" stroke="{COL["gris"]}" stroke-width="1" fill="none"/>',
                f'<circle cx="{_f(cx)}" cy="{_f(ye)}" r="5" fill="{c0}"/>',
                f'<rect x="{_f(izq)}" y="{_f(top)}" width="{_f(w)}" height="{_f(h)}" rx="6" fill="#FFFFFF" stroke="{COL["tenue"]}"/>',
                _t(izq + 6, top + lh, str(anio), tam, 'start', COL['rojo'], 700)]
        for i, l in enumerate(ls): out.append(_t(izq + 6, top + lh * (i + 2), l, tam, 'start'))
    return f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" style="display:block">' + ''.join(out) + '</svg>'


# ═════════════ Oligopolio ═════════════

def oligopolio(a, b, c1, c2=None, modelos=('cournot', 'stackelberg'), lider=1, ancho=460, alto=420, colusion=False):
    """Cournot / Stackelberg con demanda inversa P = a − b·Q y costos marginales constantes c1, c2.
    Dibuja en el plano (q1, q2) las funciones de reacción R1(q2) y R2(q1), el equilibrio de Cournot (EN)
    y, si se pide, el de Stackelberg (líder = 1 o 2) sobre la reacción del seguidor y la recta de colusión.
    Devuelve (svg, datos) con cantidades, precio y beneficios de cada modelo."""
    c2 = c1 if c2 is None else c2
    R1 = lambda q2: (a - c1 - b * q2) / (2 * b)        # q1 óptima dada q2
    R2 = lambda q1: (a - c2 - b * q1) / (2 * b)
    datos = {}
    def resumen(q1, q2):
        P = a - b * (q1 + q2)
        return {'q1': q1, 'q2': q2, 'Q': q1 + q2, 'P': P, 'pi1': (P - c1) * q1, 'pi2': (P - c2) * q2}
    q1c = (a - 2 * c1 + c2) / (3 * b); q2c = (a - 2 * c2 + c1) / (3 * b)
    datos['cournot'] = resumen(q1c, q2c)
    if 'stackelberg' in modelos:
        if lider == 1: q1s = (a - 2 * c1 + c2) / (2 * b); q2s = R2(q1s)
        else: q2s = (a - 2 * c2 + c1) / (2 * b); q1s = R1(q2s)
        datos['stackelberg'] = resumen(q1s, q2s)
    m1, m2 = (a - c1) / b, (a - c2) / b                 # cortes con los ejes
    top = max(m1, m2) * 1.05
    g = Plano(ancho, alto, xr=(0, top), yr=(0, top), margen=(30, 70, 50, 56))
    g.curva(lambda q1: (a - c1 - 2 * b * q1) / b, 0, (a - c1) / (2 * b), color=COL['azul'], nombre='R_1(q_2)')
    g.curva(R2, 0, m2, color=COL['rojo'], nombre='R_2(q_1)')
    if colusion:
        qm = (a - min(c1, c2)) / (2 * b)
        g.curva(lambda q1: qm - q1, 0, qm, color=COL['gris'], nombre=r'\text{Colusión}', punteada=True)
        datos['colusion'] = {'Q': qm, 'P': a - b * qm}
    g.ejes('q_1', 'q_2')
    g.punto(q1c, q2c, 'q_1^C', 'q_2^C', nombre=r'\text{EN}')
    if 'stackelberg' in modelos:
        s = datos['stackelberg']
        g.punto(s['q1'], s['q2'], 'q_1^S', 'q_2^S', color=COL['verde'], nombre=r'\text{S}')
    return g.svg(), datos

def bertrand(alfa, beta, gamma, c1, c2=None, ancho=460, alto=420):
    """Bertrand con producto diferenciado: q_i = α − β·p_i + γ·p_j. Reacciones en precios
    p_i = (α + β·c_i + γ·p_j) / (2β); equilibrio en su cruce. (Producto homogéneo: P = c, ver datos['homogeneo'].)"""
    c2 = c1 if c2 is None else c2
    A1, A2 = (alfa + beta * c1) / (2 * beta), (alfa + beta * c2) / (2 * beta); k = gamma / (2 * beta)
    p1 = (A1 + k * A2) / (1 - k * k); p2 = A2 + k * p1
    top = max(p1, p2) * 1.8
    g = Plano(ancho, alto, xr=(0, top), yr=(0, top), margen=(30, 70, 50, 56))
    g.curva(lambda x: (x - A1) / k if k else top * 2, A1, top, color=COL['azul'], nombre='R_1(p_2)')
    g.curva(lambda x: A2 + k * x, 0, top, color=COL['rojo'], nombre='R_2(p_1)')
    g.ejes('p_1', 'p_2').punto(p1, p2, 'p_1^B', 'p_2^B', nombre=r'\text{EN}')
    q1 = alfa - beta * p1 + gamma * p2; q2 = alfa - beta * p2 + gamma * p1
    return g.svg(), {'p1': p1, 'p2': p2, 'q1': q1, 'q2': q2, 'pi1': (p1 - c1) * q1, 'pi2': (p2 - c2) * q2,
                     'homogeneo': {'P': max(c1, c2) if c1 != c2 else c1}}


# ═════════════ Pruebas de hipótesis ═════════════

def _cdf(f, x, a, n=2000):
    """Integral numérica (Simpson) de f desde a hasta x."""
    if x <= a: return 0.0
    n += n % 2; h = (x - a) / n
    s = f(a) + f(x) + sum((4 if i % 2 else 2) * f(a + i * h) for i in range(1, n))
    return s * h / 3

def cdf(x, dist='normal', df=10):
    if dist == 'normal': return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    if dist == 't': return 0.5 + math.copysign(_cdf(lambda z: _pdf_t(z, df), abs(x), 0), x)
    if dist == 'chi2': return _cdf(lambda z: _pdf_chi2(z, df), x, 1e-9)
    raise ValueError(dist)

def cuantil(p, dist='normal', df=10):
    lo, hi = (-12.0, 12.0) if dist != 'chi2' else (0.0, df + 40 * math.sqrt(2 * df) + 40)
    for _ in range(70):
        m = (lo + hi) / 2
        if cdf(m, dist, df) < p: lo = m
        else: hi = m
    return (lo + hi) / 2

def prueba_hipotesis(estadistico, alfa=0.05, cola='bilateral', dist='normal', df=10, ancho=520, alto=230, nombre=None):
    """Prueba de hipótesis completa en una línea: campana real, región de rechazo sombreada en rojo, valores
    críticos bajo el eje, α (o α/2) en cada cola, 1 − α en el centro, el estadístico en azul con su valor p.
    cola = 'bilateral' | 'izq' | 'der'; dist = 'normal' | 't' | 'chi2' (chi² solo 'der' o 'izq').
    Devuelve (svg, datos) con criticos, p, decision ('Se rechaza H0' / 'No se rechaza H0')."""
    sim = {'normal': 'z', 't': 't', 'chi2': r'\chi^2'}[dist]
    nombre = nombre or sim + '_0'
    if cola == 'bilateral':
        cs = [cuantil(alfa / 2, dist, df), cuantil(1 - alfa / 2, dist, df)]
        Fx = cdf(estadistico, dist, df); p = 2 * min(Fx, 1 - Fx)
    elif cola == 'izq': cs = [cuantil(alfa, dist, df)]; p = cdf(estadistico, dist, df)
    else: cs = [cuantil(1 - alfa, dist, df)]; p = 1 - cdf(estadistico, dist, df)
    rech = p < alfa
    x0, yb, w, h = 40, alto - 62, ancho - 80, alto - 120
    rango = max(3.6, abs(estadistico) + 0.6) if dist != 'chi2' else 3.6
    c = Curva(x0, yb, w, h, 'normal' if dist == 'normal' else dist, df, rango=rango)
    if dist == 'chi2' and estadistico + 1 > c.b:
        c = Curva(x0, yb, w, h, 'chi2', df); c.b = estadistico * 1.15; c._max = max(c.f(c.a + (c.b - c.a) * i / 400) for i in range(401))
    out = [f'<path d="{c.area(c.a, cs[0])}" fill="{COL["rojo"]}" fill-opacity=".35"/>' if cola in ('bilateral', 'izq') else '',
           f'<path d="{c.area(cs[-1], c.b)}" fill="{COL["rojo"]}" fill-opacity=".35"/>' if cola in ('bilateral', 'der') else '',
           f'<path d="{c.eje()}" stroke="{COL["tinta"]}" stroke-width="1.4"/>',
           f'<path d="{c.trazo()}" fill="none" stroke="{COL["tinta"]}" stroke-width="2"/>']
    a_txt = r'\alpha/2' if cola == 'bilateral' else r'\alpha'
    sub = {'normal': 'z', 't': 't', 'chi2': r'\chi^2'}[dist]
    xs_ocupadas = []
    for k, z in enumerate(cs):
        out.append(f'<path d="{c.corte(z)}" stroke="{COL["rojo"]}" stroke-width="1.6"/>')
        q = (alfa / 2 if cola == 'bilateral' else alfa)
        etq = f'{sub}_{{{_num(round(1 - q, 4)) if z > (c.a + c.b) / 2 else _num(round(q, 4))}}} = {z:.3f}'
        out.append(formula_svg(c.X(z), yb + 20, etq, 12)); xs_ocupadas.append(c.X(z))
        lado = 'izq' if z < (c.a + c.b) / 2 else 'der'
        lx, ly, anc = c.etiqueta_cola(z, lado, 12)
        ly = min(ly, yb - 30)
        if abs(c.X(estadistico) - lx) < 46: ly -= 30
        out.append(formula_svg(lx, ly, a_txt, 14, alinear='der' if anc == 'end' else 'izq', color=COL['rojo']))
    z1, z2 = (cs[0], cs[1]) if cola == 'bilateral' else ((c.a, cs[0]) if cola == 'der' else (cs[0], c.b))
    mx, my = c.etiqueta_area(z1, z2)
    if abs(c.X(estadistico) - mx) < 40: mx += 60 if c.X(estadistico) <= mx else -60
    out.append(formula_svg(mx, my, r'1-\alpha', 14))
    X = c.X(estadistico); ytop = c.Y(estadistico) if c.a <= estadistico <= c.b else yb
    yt = yb - h - 14                                       # siempre arriba de la campana: nunca toca la curva
    out += [f'<path d="M{_f(X)},{_f(yb)} L{_f(X)},{_f(yt + 12)}" stroke="{COL["azul"]}" stroke-width="2.2" stroke-dasharray="5 3"/>',
            f'<circle cx="{_f(X)}" cy="{_f(yb)}" r="4" fill="{COL["azul"]}"/>',
            formula_svg(X, yt, f'{nombre} = {estadistico:g}', 14, color=COL['azul'])]
    if all(abs(X - xo) > 50 for xo in xs_ocupadas):
        out.append(formula_svg(X, yb + 40, f'p = {p:.4f}', 12, color=COL['azul']))
        pie = ''
    else: pie = f'p = {p:.4f}'
    dec = 'Se rechaza H₀' if rech else 'No se rechaza H₀'
    out.append(_t(x0 + w, 16, f'{dec}' + (f'  ({pie})' if pie else ''), 13, 'end', COL['rojo'] if rech else COL['verde'], 700))
    svg = f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" style="display:block;overflow:visible">' + ''.join(out) + '</svg>'
    return svg, {'criticos': cs, 'p': p, 'decision': 'Se rechaza H0' if rech else 'No se rechaza H0'}

def errores_tipo(mu0, mu1, sigma, alfa=0.05, ancho=560, alto=300, nx=r'\bar X'):
    """Error tipo I y II: H0 ~ N(mu0, sigma) y H1 ~ N(mu1, sigma) (sigma = error estándar del estimador).
    Prueba de cola en dirección de mu1. Sombrea α bajo H0 (rojo), β bajo H1 (azul) y marca el valor crítico.
    Leyenda debajo con α, β y potencia 1 − β. Devuelve (svg, datos)."""
    der = mu1 > mu0
    z = cuantil(1 - alfa) if der else cuantil(alfa)
    cv = mu0 + z * sigma
    beta = cdf((cv - mu1) / sigma) if der else 1 - cdf((cv - mu1) / sigma)
    lo, hi = min(mu0, mu1) - 3.8 * sigma, max(mu0, mu1) + 3.8 * sigma
    x0, yb, w, h = 30, alto - 112, ancho - 60, alto - 160
    X = lambda v: x0 + (v - lo) / (hi - lo) * w
    pdf = lambda v, m: _pdf_normal((v - m) / sigma)
    Y = lambda v, m: yb - pdf(v, m) / _pdf_normal(0) * h
    def tramo(m, a, b, n=120): return [(X(a + (b - a) * i / n), Y(a + (b - a) * i / n, m)) for i in range(n + 1)]
    def area(m, a, b): return f'M{_f(X(a))},{_f(yb)} L' + ' L'.join(f'{_f(x)},{_f(y)}' for x, y in tramo(m, a, b)) + f' L{_f(X(b))},{_f(yb)} Z'
    linea = lambda m: 'M' + ' L'.join(f'{_f(x)},{_f(y)}' for x, y in tramo(m, lo, hi, 240))
    ra, rb = (cv, hi) if der else (lo, cv)                 # región de rechazo
    na, nb = (lo, cv) if der else (cv, hi)
    out = [f'<path d="{area(mu1, na, nb)}" fill="{COL["azul"]}" fill-opacity=".30"/>',
           f'<path d="{area(mu0, ra, rb)}" fill="{COL["rojo"]}" fill-opacity=".45"/>',
           f'<path d="M{x0 - 8},{_f(yb)} L{_f(x0 + w + 8)},{_f(yb)}" stroke="{COL["tinta"]}" stroke-width="1.4"/>',
           f'<path d="{linea(mu0)}" fill="none" stroke="{COL["tinta"]}" stroke-width="2"/>',
           f'<path d="{linea(mu1)}" fill="none" stroke="{COL["tinta"]}" stroke-width="2" stroke-dasharray="7 5"/>',
           f'<path d="M{_f(X(cv))},{_f(yb)} L{_f(X(cv))},{_f(yb - h + 4)}" stroke="{COL["rojo"]}" stroke-width="1.6"/>',
           formula_svg(X(mu0), yb - h - 16, 'H_0', 14), formula_svg(X(mu1), yb - h - 16, 'H_1', 14),
           formula_svg(X(mu0), yb + 18, f'\\mu_0 = {_num(mu0)}', 12), formula_svg(X(mu1), yb + 18, f'\\mu_1 = {_num(mu1)}', 12),
           formula_svg(X(cv), yb + 38, f'c = {cv:.3f}', 12, color=COL['rojo']),
           formula_svg(x0 + w + 14, yb, nx, 14, alinear='izq')]
    ly = yb + 66
    items = [(COL['rojo'], .45, rf'\alpha = {alfa:g}', 'error tipo I: rechazar H₀ siendo cierta'),
             (COL['azul'], .30, rf'\beta = {beta:.4f}', 'error tipo II: no rechazar H₀ siendo falsa')]
    for i, (col, op, tex, txt) in enumerate(items):
        y = ly + i * 22
        out += [f'<rect x="{x0}" y="{_f(y - 7)}" width="16" height="12" fill="{col}" fill-opacity="{op}" stroke="{col}"/>',
                formula_svg(x0 + 24, y, tex, 13, alinear='izq', ancho=110), _t(x0 + 140, y + 4, txt, 13, 'start')]
    out.append(formula_svg(x0, ly + 46, rf'\text{{Potencia}} = 1-\beta = {1 - beta:.4f}', 13, alinear='izq', ancho=260))
    svg = f'<svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" style="display:block;overflow:visible">' + ''.join(out) + '</svg>'
    return svg, {'critico': cv, 'alfa': alfa, 'beta': beta, 'potencia': 1 - beta}


# ═════════════ Incertidumbre ═════════════

def _inversa(f, y, a, b):
    for _ in range(80):
        m = (a + b) / 2
        if f(m) < y: a = m
        else: b = m
    return (a + b) / 2

def incertidumbre(w1, w2, p, u=None, ancho=520, alto=400, nu='U(w)'):
    """Agente averso al riesgo: riqueza w1 con probabilidad p y w2 con 1 − p; u cóncava (por omisión √w).
    Dibuja U(w), la cuerda entre los dos resultados, E[w], E[U], U(E[w]), el equivalente cierto (EC) y la
    prima de riesgo PR = E[w] − EC en rojo. Devuelve (svg, datos)."""
    u = u or math.sqrt
    u1, u2 = u(w1), u(w2)
    Ew = p * w1 + (1 - p) * w2; EU = p * u1 + (1 - p) * u2
    EC = _inversa(u, EU, 0, w2 * 2); PR = Ew - EC
    g = Plano(ancho, alto, xr=(0, w2 * 1.12), yr=(0, u(w2 * 1.12) * 1.08), margen=(30, 60, 50, 74))
    g.curva(u, 0, w2 * 1.12, color=COL['azul'], nombre=nu)
    cuerda = lambda w: u1 + (u2 - u1) * (w - w1) / (w2 - w1)
    g.curva(cuerda, w1, w2, color=COL['gris'], grosor=1.6, punteada=True)
    g.ejes('w', 'U')
    g.punto(w1, u1, 'w_1', None); g.punto(w2, u2, 'w_2', None)
    g.punto(Ew, u(Ew), None, 'U(E[w])', guias='y')
    g.punto(Ew, EU, 'E[w]', 'E[U]', color=COL['tinta'])
    g.punto(EC, EU, r'\text{EC}', None, color=COL['verde'])
    y = g.Y(EU) + 7
    g.partes.append(f'<path d="M{_f(g.X(EC))},{_f(y)} L{_f(g.X(Ew))},{_f(y)}" stroke="{COL["rojo"]}" stroke-width="3"/>')
    g._guias.append(((g.X(EC), y), (g.X(Ew), y)))
    g._pend_puntos.append(((g.X(EC) + g.X(Ew)) / 2, y + 4, r'\text{PR}', COL['rojo']))
    return g.svg(), {'Ew': Ew, 'EU': EU, 'EC': EC, 'PR': PR, 'U_Ew': u(Ew)}


# ═════════════ Más mercados ═════════════

def externalidad(D, CMg, social, xr, yr, tipo='negativa', ancho=520, alto=380):
    """Externalidad. tipo='negativa': social = CMg social (arriba del privado); se produce de más.
    tipo='positiva': social = beneficio marginal social (arriba de la demanda); se produce de menos.
    Marca el equilibrio de mercado (Q^m) y el óptimo social (Q^*), y la PBS entre ambos. Devuelve (svg, datos)."""
    Qm = interseccion(D, CMg, *xr)[0]
    Qs = interseccion(D if tipo == 'negativa' else social, social if tipo == 'negativa' else CMg, *xr)[0]
    g = Plano(ancho, alto, xr=xr, yr=yr)
    if tipo == 'negativa':
        g.area(social, D, Qs, Qm, COL['rojo'], .3, r'\text{PBS}')
        g.curva(D, color=COL['azul'], nombre='D').curva(CMg, color=COL['rojo'], nombre=r'\text{CMg}_P').curva(social, color=COL['ocre'], nombre=r'\text{CMg}_S')
        Ps = D(Qs)
    else:
        g.area(social, CMg, Qm, Qs, COL['rojo'], .3, r'\text{PBS}')
        g.curva(D, color=COL['azul'], nombre=r'\text{BMg}_P').curva(social, color=COL['ocre'], nombre=r'\text{BMg}_S').curva(CMg, color=COL['rojo'], nombre=r'\text{CMg}')
        Ps = CMg(Qs)
    g.ejes('Q', 'P').punto(Qm, D(Qm), 'Q^m', 'P^m').punto(Qs, Ps, 'Q^*', 'P^*')
    return g.svg(), {'Qm': Qm, 'Pm': D(Qm), 'Qs': Qs, 'Ps': Ps}

def control_precio(D, S, precio, xr, yr, ancho=520, alto=380):
    """Precio máximo (debajo del equilibrio → escasez) o mínimo (arriba → excedente), con la PBS.
    Devuelve (svg, datos) con Qd, Qs, faltante o sobrante."""
    q0 = interseccion(D, S, *xr)[0]; p0 = D(q0)
    Qd = interseccion(D, lambda q: precio, *xr)[0]; Qs = interseccion(S, lambda q: precio, *xr)[0]
    maximo = precio < p0
    g = Plano(ancho, alto, xr=xr, yr=yr)
    a, b = (Qs, q0) if maximo else (Qd, q0)
    g.area(D, S, a, b, COL['rojo'], .3, r'\text{PBS}')
    g.curva(D, color=COL['azul'], nombre='D').curva(S, color=COL['rojo'], nombre='S')
    g.curva(lambda q: precio, color=COL['tinta'], grosor=1.8, nombre=r'P_{\max}' if maximo else r'P_{\min}', punteada=False)
    g.ejes('Q', 'P').punto(q0, p0, 'Q^*', 'P^*')
    g.punto(Qs if maximo else Qd, precio, 'Q^S' if maximo else 'Q^D', None)
    g.punto(Qd if maximo else Qs, precio, 'Q^D' if maximo else 'Q^S', None)
    xm = (g.X(Qs) + g.X(Qd)) / 2
    g._pend_puntos.append((xm, g.Y(precio), r'\text{Escasez}' if maximo else r'\text{Excedente}', COL['tinta']))
    return g.svg(), {'Q*': q0, 'P*': p0, 'Qd': Qd, 'Qs': Qs, ('faltante' if maximo else 'sobrante'): abs(Qd - Qs)}

def arancel(D, S, Pw, t, xr, yr, ancho=560, alto=400):
    """Arancel t sobre el precio mundial Pw: importaciones antes y después, ingreso arancelario (azul) y las dos
    PBS (producción y consumo, rojas). Devuelve (svg, datos)."""
    Qs1 = interseccion(S, lambda q: Pw, *xr)[0]; Qd1 = interseccion(D, lambda q: Pw, *xr)[0]
    Qs2 = interseccion(S, lambda q: Pw + t, *xr)[0]; Qd2 = interseccion(D, lambda q: Pw + t, *xr)[0]
    g = Plano(ancho, alto, xr=xr, yr=yr)
    g.area(lambda q: Pw + t, lambda q: Pw, Qs2, Qd2, COL['azul'], .25, r'\text{R}')
    g.area(S, lambda q: Pw, Qs1, Qs2, COL['rojo'], .3, r'\text{PBS}')
    g.area(D, lambda q: Pw, Qd2, Qd1, COL['rojo'], .3, r'\text{PBS}')
    g.curva(D, color=COL['azul'], nombre='D').curva(S, color=COL['rojo'], nombre='S')
    g.curva(lambda q: Pw, color=COL['tinta'], grosor=1.6, nombre='P_w', punteada=False)
    g.curva(lambda q: Pw + t, color=COL['tinta'], grosor=1.6, nombre='P_w + t', punteada=False)
    g.ejes('Q', 'P')
    for q, e in ((Qs1, 'Q^S_1'), (Qs2, 'Q^S_2'), (Qd2, 'Q^D_2'), (Qd1, 'Q^D_1')):
        g.punto(q, Pw if e.endswith('1') else Pw + t, e, None)
    return g.svg(), {'importaciones_antes': Qd1 - Qs1, 'importaciones_despues': Qd2 - Qs2, 'ingreso_arancel': t * (Qd2 - Qs2),
                     'pbs': 0.5 * t * (Qs2 - Qs1) + 0.5 * t * (Qd1 - Qd2)}


# ═════════════ Intervalos de confianza ═════════════

def intervalos_confianza(mu, sigma, n, k=20, nivel=0.95, semilla=1, ancho=520, alto=None, nx=r'\bar X'):
    """k intervalos de confianza de muestras simuladas de tamaño n alrededor de la media verdadera μ (línea azul).
    Los que no contienen a μ van en rojo. Ilustra qué significa el nivel de confianza. Devuelve (svg, datos)."""
    rnd = random.Random(semilla); se = sigma / math.sqrt(n); z = cuantil(1 - (1 - nivel) / 2)
    xs = [rnd.gauss(mu, se) for _ in range(k)]
    alto = alto or 90 + k * 14
    g = Plano(ancho, alto, xr=(mu - 4.2 * se, mu + 4.2 * se), yr=(0, k + 1), margen=(40, 30, 46, 30))
    dentro = 0
    for i, x in enumerate(xs):
        ok = x - z * se <= mu <= x + z * se; dentro += ok
        c = COL['tinta'] if ok else COL['rojo']; y = g.Y(k - i)
        g.partes += [f'<path d="M{_f(g.X(x - z * se))},{_f(y)} L{_f(g.X(x + z * se))},{_f(y)}" stroke="{c}" stroke-width="{1.6 if ok else 2.4}"/>',
                     f'<circle cx="{_f(g.X(x))}" cy="{_f(y)}" r="2.6" fill="{c}"/>']
    g.vertical(mu, color=COL['azul'], punteada=True)
    g.partes.append(formula_svg(g.X(mu), g.y - 22, r'\mu', 15, color=COL['azul']))
    g.ejes(nx, '', marcas_x=[round(mu + d * se, 3) for d in (-3, -2, -1, 0, 1, 2, 3)], flechas=False)
    g.partes.append(_t(g.x + g.w, 16, f'{dentro} de {k} contienen a μ (nivel {nivel:.0%})', 13, 'end', COL['rojo'] if dentro < k else COL['verde'], 700))
    return g.svg(), {'contienen': dentro, 'k': k, 'margen': z * se}


# ═════════════ Consumidor y productor ═════════════

def consumidor(a, px, py, I, ancho=480, alto=420):
    """Cobb-Douglas U = x^a·y^(1−a) con restricción px·x + py·y = I: recta presupuestaria, tres curvas de
    indiferencia (la del óptimo tangente) y la canasta óptima A. Devuelve (svg, datos)."""
    xo, yo = a * I / px, (1 - a) * I / py; Uo = xo ** a * yo ** (1 - a)
    g = Plano(ancho, alto, xr=(0, I / px * 1.25), yr=(0, I / py * 1.25), margen=(30, 60, 50, 56))
    for k, (U, nom) in enumerate(((Uo * .65, 'U_1'), (Uo, 'U_2'), (Uo * 1.4, 'U_3'))):
        g.curva(lambda x, U=U: (U / x ** a) ** (1 / (1 - a)) if x > 0 else 1e9, 0.02, I / px * 1.25,
                color=COL['azul'] if k == 1 else COL['gris'], grosor=2.2 if k == 1 else 1.5, nombre=nom)
    g.curva(lambda x: (I - px * x) / py, 0, I / px, color=COL['rojo'], nombre=r'\text{RP}')
    g.ejes('x', 'y').punto(xo, yo, 'x^*', 'y^*', nombre=r'\text{A}')
    return g.svg(), {'x': xo, 'y': yo, 'U': Uo, 'TMS': a / (1 - a) * yo / xo}

def productor(a, b, w, r, Q, ancho=480, alto=420):
    """Cobb-Douglas Q = L^a·K^b: isocuanta de Q, isocosto mínimo tangente y dos isocostos de referencia.
    Devuelve (svg, datos) con L*, K* y el costo mínimo."""
    c = (b * w) / (a * r); L = (Q / c ** b) ** (1 / (a + b)); K = c * L; C = w * L + r * K
    g = Plano(ancho, alto, xr=(0, C / w * 1.3), yr=(0, C / r * 1.3), margen=(30, 60, 50, 56))
    g.curva(lambda l: (Q / l ** a) ** (1 / b) if l > 0 else 1e9, 0.02, C / w * 1.3, color=COL['azul'], nombre='Q_0')
    for f, nom in ((0.7, 'C_1'), (1.0, 'C^*'), (1.35, 'C_2')):
        g.curva(lambda l, f=f: (C * f - w * l) / r, 0, C * f / w, color=COL['rojo'] if f == 1 else COL['gris'],
                grosor=2.2 if f == 1 else 1.5, nombre=nom, punteada=f != 1)
    g.ejes('L', 'K').punto(L, K, 'L^*', 'K^*', nombre=r'\text{E}')
    return g.svg(), {'L': L, 'K': K, 'C': C}
