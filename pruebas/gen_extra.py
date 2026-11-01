import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import geo, graficas as G
D = lambda q: 20 - q; S = lambda q: 2 + q
p = []
p.append(('Incertidumbre', G.incertidumbre(16, 100, 0.5)[0]))
p.append(('Externalidad negativa', G.externalidad(D, lambda q: 2 + q, lambda q: 6 + q, (0, 20), (0, 22))[0]))
p.append(('Externalidad positiva', G.externalidad(D, S, lambda q: 26 - q, (0, 20), (0, 28), tipo='positiva')[0]))
p.append(('Precio máximo', G.control_precio(D, S, 8, (0, 20), (0, 22))[0]))
p.append(('Precio mínimo', G.control_precio(D, S, 15, (0, 20), (0, 22))[0]))
p.append(('Arancel', G.arancel(D, S, 6, 3, (0, 20), (0, 22))[0]))
p.append(('Intervalos de confianza', G.intervalos_confianza(50, 10, 25, semilla=int(sys.argv[2]) if len(sys.argv) > 2 else 1)[0]))
p.append(('Consumidor', G.consumidor(.5, 2, 4, 100)[0]))
p.append(('Productor', G.productor(.5, .5, 4, 1, 20)[0]))
h3, _ = G.matriz_pagos(['A', 'B', 'C'], ['X', 'Y', 'Z'], [[(3, 3), (2, 1), (4, 0)], [(1, 2), (1, 1), (2, 3)], [(0, 4), (3, 2), (1, 1)]], dominadas=True)
p.append(('Matriz 3×3 con dominadas', h3))
hm, _ = G.matriz_pagos(['Cara', 'Cruz'], ['Cara', 'Cruz'], [[(1, -1), (-1, 1)], [(-1, 1), (1, -1)]], 'Jugador 1', 'Jugador 2', mixtas=True)
p.append(('Estrategias mixtas', hm))
cuerpo = ''.join(f'<h2>{t}</h2><div class="bloque">{s}</div>' for t, s in p)
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">{geo.KATEX_HEAD}
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet">
<style>body{{font-family:Kalam;background:#FFFEFA;margin:24px;width:900px}} h2{{color:#C93636;font-size:20px;margin:22px 0 8px}}</style></head><body>{cuerpo}</body></html>"""
open(sys.argv[1], 'w').write(html)
