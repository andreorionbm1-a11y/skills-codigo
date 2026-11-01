import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import sys
modo = sys.argv[1]  # mal | bien
bien = modo == 'bien'
lorem = ("La distribución muestral describe cómo varía un estadístico entre muestras repetidas del mismo tamaño. "
         "Con muestras grandes el teorema central del límite garantiza normalidad aproximada de la media muestral. ")
css = """
@page { size: A4; margin: 15mm 15mm 18mm; @bottom-center { content: "Estadística II · " counter(page) " / " counter(pages); font-family: 'Kalam'; font-size: 9pt; color: #55524B; } }
body { font-family: 'Kalam', cursive; font-size: 15px; line-height: 1.55; color: #1D1D1D; margin: 0; }
h1 { font-size: 26px; margin: 0 0 8px; } h2 { color: #C93636; font-size: 20px; margin: 16px 0 6px; }
.formula { border: 1.6px solid #2F6FD6; padding: 10px 14px; margin: 8px 0; }
table { border-collapse: collapse; width: 100%; } td, th { border: 1px solid #999; padding: 4px 8px; }
p { margin: 0 0 8px; }
"""
if bien:
    css += """
.tema { break-before: page; } .tema:first-of-type { break-before: auto; }
h1, h2, h3 { break-after: avoid; }
p { orphans: 3; widows: 3; }
.formula, figure, .bloque { break-inside: avoid; }
thead { display: table-header-group; } tr { break-inside: avoid; }
"""
P = lambda n: ''.join(f'<p>{lorem}</p>' for _ in range(n))
filas = ''.join(f'<tr><td>{i}</td><td>{1.96+i/100:.2f}</td><td>{0.95-i/1000:.3f}</td></tr>' for i in range(60))
cab = '<tr><th>n</th><th>z</th><th>p</th></tr>'
tabla = f'<table>{"<thead>"+cab+"</thead>" if bien else cab}<tbody>{filas}</tbody></table>'
html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap" rel="stylesheet"><style>{css}</style></head><body>
<section class="tema"><h1>Tema 1: Distribuciones muestrales</h1>{P(9)}
<h2>Fórmulas clave</h2><div class="formula">{P(2 if bien else 4)}</div>{P(5)}
<h2>Subtema que queda al pie</h2>{P(2 if bien else 4)}</section>
<section class="tema"><h1>Tema 2: Intervalos de confianza</h1>{P(3)}
<figure style="height:{'560' if not bien else '420'}px;border:1px solid #ccc;margin:0;break-inside:avoid">figura grande</figure>{P(2)}</section>
<section class="tema"><h1>Tema 3: Tabla de valores</h1>{tabla}</section>
</body></html>"""
open(sys.argv[2], 'w').write(html)
