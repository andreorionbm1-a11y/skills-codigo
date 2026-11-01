import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import geo, graficas as G
p = []
s, d = G.oligopolio(100, 1, 10, 10, colusion=True); p.append(('Cournot y Stackelberg', s))
s, d = G.bertrand(100, 2, 1, 10); p.append(('Bertrand diferenciado', s))
s, d = G.prueba_hipotesis(2.1); p.append(('Bilateral normal', s))
s, d = G.prueba_hipotesis(-1.2, 0.05, 'izq', 't', 12); p.append(('Cola izquierda t', s))
s, d = G.prueba_hipotesis(13.4, 0.05, 'der', 'chi2', 6); p.append(('Cola derecha chi²', s))
s, d = G.prueba_hipotesis(0.8, 0.10, 'der'); p.append(('Estadístico dentro de la zona de no rechazo', s))
s, d = G.errores_tipo(100, 103, 1.5); p.append(('Errores tipo I y II', s))
juego = {'j': 'N', 'p': {'Fuerte': 0.6, 'Débil': 0.4}, 'a': {
    'Fuerte': {'j': '1', 'a': {'Entrar': (-2, 3), 'No entrar': (0, 5)}},
    'Débil':  {'j': '1', 'a': {'Entrar': (4, -1), 'No entrar': (0, 5)}}}}
s, d = G.arbol(juego, jugadores={'1': 'Entrante'}, resolver=True); p.append(('Árbol con Naturaleza', s))
cuerpo = ''.join(f'<h2>{t}</h2><div class="bloque">{s}</div>' for t, s in p)
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">{geo.KATEX_HEAD}
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet">
<style>body{{font-family:Kalam;background:#FFFEFA;margin:24px;width:900px}} h2{{color:#C93636;font-size:20px;margin:22px 0 8px}}</style></head><body>{cuerpo}</body></html>"""
open(sys.argv[1], 'w').write(html)
