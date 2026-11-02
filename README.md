# skills-codigo

Código de las skills **maquetacion** y **graficas-academicas** de André.

| Archivo | Qué hace |
|---|---|
| `geo.py` | Geometría (polígonos, curvas, conectores), medición de texto, KaTeX, CSS de impresión, tipografía española y plantillas (guía, formulario, tarjetas, portada) |
| `verificar.py` | Verificador visual con Playwright: choques, desbordes, contraste, fórmulas, subrayados, páginas impresas, blanco y negro, daltonismo y consistencia |
| `graficas.py` | Gráficas académicas: economía (`Plano`), oligopolio, árboles de juegos, matrices de pagos, pruebas de hipótesis, errores tipo I/II, campanas, estadística descriptiva, líneas de tiempo. `ESTILO = 'mano'` = trazo de lápiz fino |

Las skills descargan estos tres archivos al inicio de cada sesión.

## Cómo se actualiza

| Paso | Comando |
|---|---|
| 1. Cambiar el código | Editar `geo.py`, `verificar.py` o `graficas.py` |
| 2. Probar todo | `python3 probar.py` → debe terminar en **TODO BIEN** |
| 3. Subir | `git push origin main` |
| 4. Publicar para las skills | `git push origin main:estable` (solo con las pruebas en verde) |

Las skills descargan la rama **`estable`**, nunca `main`: un cambio a medias no rompe ningún chat.
