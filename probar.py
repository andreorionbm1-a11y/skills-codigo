#!/usr/bin/env python3
"""Pruebas de regresión de las skills maquetacion y graficas-academicas.

Uso:  python3 probar.py            (todas)      python3 probar.py galeria nuevas   (solo esas)
Dibuja todas las muestras, las pasa por verificar.py y compara con lo esperado. Sale con código 1 si algo cambió.
Correrlo SIEMPRE antes de subir un cambio y antes de mover la rama `estable`."""
import json, subprocess, sys, tempfile
from pathlib import Path

R = Path(__file__).resolve().parent
P = R / 'pruebas'
# nombre: (comando que genera el HTML (o None si ya existe), archivo, argumentos de verificar, problemas esperados)
CASOS = {
    'galeria':        (['gen_galeria.py', '{o}/galeria.html'], 'galeria.html', ['--ancho', '1000'], 0),
    'estadistica':    (['gen_stats.py', '{o}/stats.html'], 'stats.html', ['--ancho', '900'], 0),
    'impuesto':       (['gen_impuesto.py', '{o}/imp.html', '-', '2', '820'], 'imp.html', ['--ancho', '900'], 0),
    'impuesto_chico': (['gen_impuesto.py', '{o}/imp2.html', '-', '0.8', '600'], 'imp2.html', ['--ancho', '900'], 0),
    'nuevas':         (['gen_nuevas.py', '{o}/nuevas.html'], 'nuevas.html', ['--ancho', '960'], 0),
    'extra':          (['gen_extra.py', '{o}/extra.html'], 'extra.html', ['--ancho', '960'], 0),
    'guia':           (['gen_plantillas.py', '{o}'], 'pl_guia.html', ['--ancho', '794', '--pdf'], 0),
    'formulario':     (None, 'pl_formulario.html', ['--ancho', '794', '--pdf'], 0),
    'tarjetas':       (None, 'pl_tarjetas.html', ['--ancho', '794', '--pdf'], 0),
    'paginas_bien':   (['gen_paginas.py', 'bien', '{o}/pag_bien.html'], 'pag_bien.html', ['--ancho', '794', '--pdf'], 0),
    'paginas_mal':    (['gen_paginas.py', 'mal', '{o}/pag_mal.html'], 'pag_mal.html', ['--ancho', '794', '--pdf'], 7),
    'pie':            ('casos', 'pie.html', ['--ancho', '794', '--pdf'], 0),
    'mal':            ('casos', 'mal.html', ['--ancho', '900'], 3),
    'notacion':       ('casos', 'notacion.html', ['--ancho', '900'], 3),
    'consistencia':   ('casos', 'consistencia.html', ['--ancho', '900'], 0),
}

def main():
    pedidos = sys.argv[1:] or list(CASOS)
    o = Path(tempfile.mkdtemp(prefix='pruebas_'))
    fallas = 0
    for nombre in pedidos:
        gen, archivo, args, esperado = CASOS[nombre]
        if gen == 'casos':
            ruta = P / 'casos' / archivo
        else:
            if gen:
                cmd = [sys.executable, str(P / gen[0])] + [a.format(o=o) for a in gen[1:]]
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode:
                    print(f'✗ {nombre}: el generador falló\n{r.stderr[-600:]}'); fallas += 1; continue
            ruta = o / archivo
        r = subprocess.run([sys.executable, str(R / 'verificar.py'), str(ruta), '--salida', str(o / (nombre + '_rev'))] + args,
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except Exception:
            print(f'✗ {nombre}: el verificador falló\n{r.stderr[-600:]}'); fallas += 1; continue
        ok = d['problemas'] == esperado
        fallas += not ok
        print(f"{'✓' if ok else '✗'} {nombre}: {d['problemas']} problemas (esperado {esperado})")
        if not ok:
            for x in d['detalle'][:6]: print('   ', x['tipo'], '·', x['detalle'][:100])
    print(f'\nImágenes en {o}')
    print('TODO BIEN' if not fallas else f'{fallas} CASO(S) CAMBIARON')
    sys.exit(1 if fallas else 0)

if __name__ == '__main__':
    main()
