#!/usr/bin/env python3
"""Herramientas del expediente médico longitudinal.

Datos: medical/expediente.json (PRIVADO, gitignored). Este script no contiene datos.

Uso (desde el root del repo):
  python medical/expediente_tools.py render            # regenera las tablas en HISTORIAL_MEDICO.md
  python medical/expediente_tools.py tabla ldl         # imprime la tabla de un marcador
  python medical/expediente_tools.py resumen           # último valor de cada marcador + estado
  python medical/expediente_tools.py nuevo             # plantilla JSON para agregar un examen
  python medical/expediente_tools.py check             # valida el JSON

Flujo para un examen nuevo: agregar el examen a expediente.json (ver `nuevo`),
correr `check` y luego `render`. Las tablas del historial se reescriben solas
entre los marcadores <!-- TABLAS:INICIO --> y <!-- TABLAS:FIN -->.
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "expediente.json")
HIST = os.path.join(HERE, "HISTORIAL_MEDICO.md")
INI, FIN = "<!-- TABLAS:INICIO -->", "<!-- TABLAS:FIN -->"
ESTABLE_REL = 0.05   # cambio relativo < 5% se considera "→ estable"

ORDEN_CATEGORIAS = ["Metabolismo glucídico", "Perfil lipídico", "Función hepática", "Función renal",
                    "Tiroides", "Próstata", "Otros", "Hemograma", "Cardiovascular",
                    "Capacidad funcional", "Antropometría"]


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s
    return str(v)


def rango_txt(r):
    if r.get("ref_txt"):
        return r["ref_txt"]
    lo, hi = r.get("ref_lo"), r.get("ref_hi")
    if lo is not None and hi is not None:
        return f"{fmt(lo)} – {fmt(hi)}"
    if lo is not None:
        return f"> {fmt(lo)}"
    if hi is not None:
        return f"< {fmt(hi)}"
    return "sin rango"


def fuera_de_rango(r):
    v, lo, hi = r["v"], r.get("ref_lo"), r.get("ref_hi")
    if not isinstance(v, (int, float)):
        return None
    if lo is not None and v < lo:
        return "bajo"
    if hi is not None and v > hi:
        return "alto"
    if lo is None and hi is None:
        return None
    return "ok"


def tendencia(prev, cur, direccion):
    if prev is None:
        return "—", ""
    d = cur - prev
    rel = abs(d) / abs(prev) if prev else (0 if d == 0 else 1)
    if rel < ESTABLE_REL:
        return "→", "estable"
    flecha = "↑" if d > 0 else "↓"
    if direccion == "bajar":
        return flecha, "favorable" if d < 0 else "desfavorable"
    if direccion == "subir":
        return flecha, "favorable" if d > 0 else "desfavorable"
    return flecha, ""


def series(data):
    """{marcador: [(fecha, resultado_dict, examen_id), ...]} ordenado por fecha."""
    out = {}
    for ex in sorted(data["examenes"], key=lambda e: e["fecha"]):
        for r in ex.get("resultados", []):
            out.setdefault(r["m"], []).append((ex["fecha"], r, ex["id"]))
    return out


def tabla_md(data, mk):
    m = data["marcadores"][mk]
    rows = series(data).get(mk, [])
    if not rows:
        return ""
    lines = [f"**{m['nombre']}** ({m['unidad'] or 'sin unidad'})", "",
             "| Fecha | Resultado | Cambio vs anterior | Rango lab | Tendencia | Nota |",
             "|---|---|---|---|---|---|"]
    prev = None
    for fecha, r, _ in rows:
        v = r["v"]
        num = isinstance(v, (int, float))
        cambio = "—"
        if num and prev is not None:
            d = v - prev
            cambio = f"{'+' if d >= 0 else ''}{fmt(round(d, 3))}"
        fl, jz = tendencia(prev, v, m["direccion"]) if num else ("", "")
        fr = fuera_de_rango(r)
        notas = []
        if fr in ("alto", "bajo"):
            notas.append(f"⚠ {fr} vs rango lab")
        if jz:
            notas.append(jz)
        if r.get("nota"):
            notas.append(r["nota"])
        lines.append(f"| {fecha} | {fmt(v)} | {cambio} | {rango_txt(r)} | {fl} | {'; '.join(notas)} |")
        prev = v if num else prev
    return "\n".join(lines) + "\n"


def render_tablas(data):
    s = series(data)
    cats = {}
    for mk, m in data["marcadores"].items():
        if mk in s:
            cats.setdefault(m["categoria"], []).append(mk)
    out = ["", "_Tablas generadas automáticamente por `expediente_tools.py render` desde `expediente.json`. "
           "No editar a mano; editar el JSON y regenerar._", "",
           "Flechas = dirección numérica. Favorable/desfavorable según el marcador. "
           "`[doc]` = verificado en documento original; `[reportado]` = dictado de memoria; "
           "`[doc-hist]` = tomado de la sección de históricos de un informe posterior.", ""]
    for cat in ORDEN_CATEGORIAS + [c for c in cats if c not in ORDEN_CATEGORIAS]:
        if cat not in cats:
            continue
        out.append(f"### {cat}\n")
        for mk in cats[cat]:
            out.append(tabla_md(data, mk))
    return "\n".join(out)


def cmd_render():
    data = load()
    with open(HIST, encoding="utf-8") as f:
        txt = f.read()
    if INI not in txt or FIN not in txt:
        sys.exit(f"Faltan los marcadores {INI} / {FIN} en {HIST}")
    a, b = txt.index(INI) + len(INI), txt.index(FIN)
    txt = txt[:a] + "\n" + render_tablas(data) + "\n" + txt[b:]
    with open(HIST, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"OK: tablas regeneradas en {HIST}")


def cmd_tabla(mk):
    data = load()
    if mk not in data["marcadores"]:
        sys.exit(f"Marcador desconocido: {mk}. Disponibles: {', '.join(sorted(data['marcadores']))}")
    print(tabla_md(data, mk) or "(sin resultados)")


def cmd_resumen():
    data = load()
    s = series(data)
    print("| Marcador | Último | Fecha | Rango lab | Estado |")
    print("|---|---|---|---|---|")
    for mk, m in data["marcadores"].items():
        if mk not in s:
            continue
        fecha, r, _ = s[mk][-1]
        fr = fuera_de_rango(r)
        estado = {"alto": "⚠ alto", "bajo": "⚠ bajo", "ok": "en rango", None: "sin rango"}[fr]
        print(f"| {m['nombre']} | {fmt(r['v'])} {m['unidad']} | {fecha} | {rango_txt(r)} | {estado} |")


def cmd_nuevo():
    print(json.dumps({
        "id": "AAAA-MM-DD-lab", "fecha": "AAAA-MM-DD", "tipo": "laboratorio | imagen | prueba_cardio | composicion | presion_arterial",
        "laboratorio": "nombre del lab / centro", "orden": "número de orden",
        "verificacion": "documento | reportado | parcial", "fuente": "nombre del PDF",
        "documento": "MEDICO/archivo.pdf",
        "resultados": [
            {"m": "ldl", "v": 0, "ref_lo": None, "ref_hi": 116, "ref_txt": "< 116", "nota": "[doc]"},
            {"m": "apob", "v": 0, "ref_lo": 49, "ref_hi": 173},
        ],
        "detalle": {"texto libre": "conclusiones documentadas, médico, técnica..."},
    }, ensure_ascii=False, indent=2))
    print("\nMarcadores válidos:", ", ".join(sorted(load()["marcadores"])))


def cmd_check():
    data = load()
    ok = True
    ids = set()
    for ex in data["examenes"]:
        for k in ("id", "fecha", "tipo", "resultados"):
            if k not in ex:
                print(f"ERROR: examen sin '{k}': {ex.get('id')}"); ok = False
        if ex.get("id") in ids:
            print(f"ERROR: id duplicado {ex['id']}"); ok = False
        ids.add(ex.get("id"))
        for r in ex.get("resultados", []):
            if r["m"] not in data["marcadores"]:
                print(f"ERROR: marcador desconocido '{r['m']}' en {ex['id']}"); ok = False
            if not isinstance(r.get("v"), (int, float, str)):
                print(f"ERROR: valor inválido en {ex['id']} / {r['m']}"); ok = False
    print("OK" if ok else "Hay errores")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    cmd = args[0]
    if cmd == "render": cmd_render()
    elif cmd == "tabla" and len(args) > 1: cmd_tabla(args[1])
    elif cmd == "resumen": cmd_resumen()
    elif cmd == "nuevo": cmd_nuevo()
    elif cmd == "check": cmd_check()
    else: print(__doc__); sys.exit(1)
