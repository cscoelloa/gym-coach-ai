# Fuentes

Archivos binarios comiteados a propósito. La CSP declara `font-src: 'self'`, así que un
enlace a Google Fonts quedaría bloqueado en producción sin dejar más rastro que una tipografía que
no es la que se pidió.

| Archivo | Familia | Licencia |
|---|---|---|
| `Inter-Variable-latin.woff2`, `Inter-Variable-latin-ext.woff2` | [Inter](https://github.com/rsms/inter) — variable, ejes `wght` 400–700 y `opsz` 14–32 | SIL Open Font License 1.1 |

La OFL permite redistribuir y alojar los archivos; lo que prohíbe es venderlos sueltos y reutilizar
los nombres reservados en versiones modificadas. Aquí no se modifica ninguno.

Son dos archivos porque la familia va subdividida en `latin` y `latin-ext`: el navegador descarga
solo el rango que necesita, y el español cabe entero en `latin`. `latin-ext` está por los nombres de
ejercicio que vienen del catálogo en otros idiomas.

**Ya no hay fuente mono.** Las cifras van en Inter con `tabular-nums`, que necesita el rasgo
`tnum` de la fuente. El subconjunto de Google lo conserva; si al regenerarlas se perdiera, las
columnas de kg empezarían a bailar. Lo vigila el recorrido «la tipografía autoalojada se aplica»
de `frontend/e2e/humo.spec.ts`, que compara el ancho de «111» y «888».

## Regenerarlas

Se descargan aparte y se comitean.

```bash
python - <<'PY'
import re, urllib.request, pathlib

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
api = "https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&display=swap"
# El User-Agent NO es opcional: sin uno moderno, la API devuelve TTF en vez de woff2.
css = urllib.request.urlopen(urllib.request.Request(api, headers={"User-Agent": UA})).read().decode()

out = pathlib.Path("static/fonts"); out.mkdir(parents=True, exist_ok=True)
for subset, body in re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
    if subset not in {"latin", "latin-ext"}:
        continue
    url = re.search(r"url\((https://[^)]+)\)", body).group(1)
    nombre = f"Inter-Variable-{subset}.woff2"
    (out / nombre).write_bytes(
        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()
    )
    print(nombre)
PY
```

Si cambian los nombres de archivo o los `unicode-range`, hay que actualizar los `@font-face` de
`assets/app.css` y reconstruir el bundle. `apps/common/tests/test_design_system.py` comprueba que
cada `url()` apunta a un archivo que existe y que no queda ningún `.woff2` sin usar.
