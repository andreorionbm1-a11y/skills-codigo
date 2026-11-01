import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import random
import geo, graficas as G
C = G.COL
# 1. Oferta y demanda con excedentes
D = lambda q: 10 - q; S = lambda q: 2 + q
q = G.interseccion(D, S, 0, 10)[0]; p = D(q)
od = G.Plano(460, 330, (0, 10), (0, 11))
od.area(D, lambda v: p, 0, q, C['azul'], .2, r'EC').area(lambda v: p, S, 0, q, C['rojo'], .18, r'EP')
od.ejes('Q', 'P').curva(D, color=C['azul'], nombre='D').curva(S, color=C['rojo'], nombre='S').punto(q, p, 'Q^*', 'P^*')
# 2. Monopolio
Dm = lambda v: 12 - v; IMg = lambda v: 12 - 2 * v; CMg = lambda v: 2 + v; CMe = lambda v: 6 / v + 2 + v / 2
qm = G.interseccion(IMg, CMg, 0.1, 12)[0]; pm = Dm(qm)
mo = G.Plano(460, 330, (0, 12), (0, 13))
mo.area(lambda v: pm, lambda v: CMe(qm), 0, qm, C['verde'], .2, r'\pi')
mo.ejes('Q', r'\$').curva(Dm, color=C['azul'], nombre='D').curva(IMg, 0, 6, color=C['morado'], nombre=r'\text{IMg}')
mo.curva(CMg, color=C['rojo'], nombre=r'\text{CMg}').curva(CMe, 0.4, 12, color=C['ocre'], nombre=r'\text{CMe}')
mo.punto(qm, pm, 'Q^m', 'P^m').punto(qm, IMg(qm))
# 3. Árboles
sec = {'j': '1', 'a': {'Montaña': {'j': '2', 'a': {'Montaña': (2, 1), 'Playa': (0, 0)}},
                       'Playa':   {'j': '2', 'a': {'Montaña': (0, 0), 'Playa': (1, 2)}}}}
arb1, d1 = G.arbol(sec, jugadores={'1': 'Mujer', '2': 'Hombre'}, resolver=True)
sim = {'j': '1', 'a': {'Montaña': {'j': '2', 'info': 'h', 'a': {'Montaña': (2, 1), 'Playa': (0, 0)}},
                       'Playa':   {'j': '2', 'info': 'h', 'a': {'Montaña': (0, 0), 'Playa': (1, 2)}}}}
arb2, d2 = G.arbol(sim, jugadores={'1': 'Mujer', '2': 'Hombre'})
tres = {'j': '1', 'a': {'A': {'j': '2', 'a': {'C': (3, 1, 2), 'D': {'j': '3', 'a': {'E': (1, 2, 3), 'F': (2, 0, 1)}}}},
                        'B': {'j': '2', 'a': {'C': (0, 3, 1), 'D': (2, 2, 2)}}}}
arb3, d3 = G.arbol(tres, resolver=True)
# 4. Matriz
mat, dm = G.matriz_pagos(['Invertir', 'No invertir'], ['Invertir', 'No invertir'],
                         [[(15, 15), (45, -75)], [(-75, 45), (22, 22)]], 'Empresa 1', 'Empresa 2')
# 5. Estadística
r = random.Random(7); datos = [r.gauss(50, 10) for _ in range(120)]
hist = G.histograma(datos, nx='x', ny='f')
cj = G.caja({'Grupo A': [r.gauss(50, 8) for _ in range(40)] + [85], 'Grupo B': [r.gauss(58, 12) for _ in range(40)]})
xs = [r.uniform(0, 10) for _ in range(30)]; ys = [3 + 1.8 * x + r.gauss(0, 2) for x in xs]
disp, reg = G.dispersion(xs, ys, nx=r'\text{Horas}', ny=r'\text{Calif.}')
bino = G.binomial(10, 0.3, (2, 4))
cf = G.CurvaF(40, 170, 380, 120, 5, 12)
fs = ['<svg width="460" height="230" style="display:block">', f'<path d="{cf.area(3.11, 99)}" fill="{C["rojo"]}" fill-opacity=".3"/>',
      f'<path d="{cf.eje()}" stroke="{C["gris"]}" stroke-width="1.3"/>', f'<path d="{cf.trazo()}" fill="none" stroke="#1E3A8A" stroke-width="2.2"/>',
      f'<path d="{cf.corte(3.11)}" stroke="{C["tinta"]}" stroke-dasharray="4 3"/>']
ex, ey, anc = cf.etiqueta_cola(3.11, 'der', 14)
fs += [geo.formula_svg(ex, ey, r'\alpha = 0.05', 14, alinear='izq'), geo.formula_svg(cf.X(3.11), 194, r'F_{5,12;\,0.05}=3.11', 13),
       geo.formula_svg(cf.X(cf.b) + 14, 170, 'F', 14, alinear='izq'), '</svg>']
# 6. Línea de tiempo
lt = G.linea_tiempo([(1810, 'Inicio de la Independencia'), (1821, 'Consumación de la Independencia'),
                     (1824, 'Primera Constitución federal'), (1836, 'Independencia de Texas'),
                     (1846, 'Guerra con Estados Unidos'), (1857, 'Constitución liberal de 1857'),
                     (1858, 'Guerra de Reforma'), (1862, 'Batalla de Puebla'), (1867, 'Restauración de la República'),
                     (1876, 'Inicio del Porfiriato'), (1910, 'Revolución Mexicana'), (1917, 'Constitución de 1917')], ancho=960)
sec_ = lambda t, *c: f'<section><h2>{t}</h2><div class="fila">' + ''.join(f'<div>{x}</div>' for x in c) + '</div></section>'
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet">{geo.KATEX_HEAD}
<style>body{{font-family:Kalam,sans-serif;background:#fff;color:#1D1D1D;margin:24px;width:960px}} h2{{color:#C93636;font-size:21px;text-decoration:underline wavy #C93636 1.6px;text-underline-offset:.08em;margin:22px 0 8px}}
.fila{{display:flex;gap:36px;flex-wrap:wrap;align-items:flex-start}} .nota{{font-size:14px}}</style></head><body>
{sec_('Oferta y demanda', od.svg(), mo.svg())}
<p class="nota">Equilibrio: $Q^*={q:.0f}$, $P^*={p:.0f}$. Monopolio: $Q^m={qm:.2f}$, $P^m={pm:.2f}$.</p>
{sec_('Árboles en forma extensiva', arb1, arb2)}
<p class="nota">Estrategias: secuencial {d1['estrategias']}, simultáneo {d2['estrategias']}.</p>
{sec_('Árbol con tres jugadores', arb3)}
{sec_('Matriz de pagos', mat)}
<p class="nota">Nash: {dm['nash']} · Pareto: {dm['pareto']}</p>
{sec_('Histograma y diagrama de caja', hist, cj)}
{sec_('Regresión y binomial', disp, bino)}
{sec_('Distribución F', ''.join(fs))}
{sec_('Línea de tiempo', lt)}
</body></html>"""
open(sys.argv[1], 'w').write(html)
print('ok', d1, d3['estrategias'], dm, round(reg['r2'], 2))
