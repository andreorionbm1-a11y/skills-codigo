"""Corre otro generador con graficas.ESTILO = 'mano'.  Uso: gen_mano.py [--relleno mojado] gen_galeria.py salida.html [args...]"""
import sys, runpy, pathlib
aqui = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(aqui.parent))
import graficas as G
G.ESTILO = 'mano'
if sys.argv[1] == '--relleno': G.RELLENO = sys.argv[2]; del sys.argv[1:3]
sys.argv = [str(aqui / sys.argv[1])] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
