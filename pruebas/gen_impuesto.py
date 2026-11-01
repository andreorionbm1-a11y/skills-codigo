import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import geo, graficas as G
D = lambda q: 12 - q; S = lambda q: 0.6*q; t = float(sys.argv[3]) if len(sys.argv) > 3 else 2
St = lambda q: S(q) + t
qt = G.interseccion(D, St, 0, 12)[0]; qc = G.interseccion(D, S, 0, 12)[0]
pd, ps = D(qt), S(qt)
g = G.Plano(int(sys.argv[4]) if len(sys.argv) > 4 else 820, 360, xr=(0, 12), yr=(0, 13))
g.area(D, lambda v: pd, 0, qt, '#E3C34F', .4, r'\text{EC}')
g.area(lambda v: pd, lambda v: ps, 0, qt, G.COL['azul'], .28, r'\text{R}')
g.area(lambda v: ps, S, 0, qt, '#B48A4E', .35, r'\text{EP}')
g.area(D, S, qt, qc, G.COL['rojo'], .35, r'\text{PBS}')
g.ejes('Q', 'P').curva(D, color=G.COL['tinta'], nombre='D').curva(S, color=G.COL['tinta'], nombre='S').curva(St, color=G.COL['azul'], nombre='S+t')
g.punto(qt, pd, 'Q^t', 'P_D'); g.punto(qt, ps, None, 'P_S'); g.punto(qc, D(qc), 'Q^{CP}')
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">{geo.KATEX_HEAD}
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet">
<style>body{{font-family:Kalam;background:#FFFEFA;margin:20px}}</style></head><body>
<h3 style="text-align:center">Impuesto por unidad: incidencia y PBS</h3>{g.svg()}</body></html>"""
open(sys.argv[1], 'w').write(html)
