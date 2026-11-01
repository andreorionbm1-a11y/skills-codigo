import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import geo
d = sys.argv[1]
f1 = '<p>La media muestral es un <span class="clave">estimador insesgado</span>.</p><div class="formula">$\\bar X = \\frac{1}{n}\\sum_{i=1}^n X_i$</div><p class="nota">ojo: n ≥ 30</p>'
open(f'{d}/pl_guia.html', 'w').write(geo.plantilla('guia', 'Estadística II', 'Guía final', [('Estimación', f1 * 3), ('Intervalos', f1 * 2)]))
bl = [(f'Tema {i}', '<div class="formula">$IC = \\bar X \\pm z_{\\alpha/2}\\,\\frac{\\sigma}{\\sqrt n}$</div><p>Se usa cuando σ es conocida...</p>') for i in range(1, 9)]
open(f'{d}/pl_formulario.html', 'w').write(geo.plantilla('formulario', 'Estadística II', 'Formulario parcial 2', bl))
cs = [(f'Concepto {i}', f'Definición breve del concepto {i} con $\\mu_{i}$') for i in range(1, 11)]
open(f'{d}/pl_tarjetas.html', 'w').write(geo.plantilla('tarjetas', 'Economía IV', contenido=cs))
open(f'{d}/pl_portada.html', 'w').write(geo.plantilla('portada', 'Economía IV', 'Teoría de juegos', subtitulo='Guía de estudio', autor='André', fecha='Noviembre 2026'))
open(f'{d}/pl_limpio.html', 'w').write(geo.plantilla('guia', 'Administración Internacional', 'Study guide', [('Trade theory', f1)], estilo='limpio'))
