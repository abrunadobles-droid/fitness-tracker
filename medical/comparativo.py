#!/usr/bin/env python3
"""Genera el documento COMPARATIVO longitudinal (HTML + PDF) desde expediente.json.

Uso:  python medical/comparativo.py            -> medical/COMPARATIVO_<primer>_<ultimo>.html y .pdf
El PDF se produce con Chromium headless si está disponible (CHROME env var o rutas conocidas).
No contiene datos: todo sale del JSON (privado).
"""
import json, os, sys, subprocess, shutil, html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "expediente.json")
ESTABLE_REL = 0.05

# Paleta (dataviz reference, modo claro): 1 serie azul; estados reservados con icono + texto.
C = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#8a8985", grid="#e6e5e1",
         serie="#2a78d6", band="#eef1f5", good="#008300", warn="#c98500", bad="#e34948")

CATS = ["Metabolismo glucídico", "Perfil lipídico", "Función hepática", "Función renal", "Tiroides",
        "Próstata", "Otros", "Hemograma", "Cardiovascular", "Capacidad funcional", "Antropometría"]

def fmt(v):
    if v is None: return "—"
    if isinstance(v, float):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)

def rango(r):
    if r.get("ref_txt"): return r["ref_txt"]
    lo, hi = r.get("ref_lo"), r.get("ref_hi")
    if lo is not None and hi is not None: return f"{fmt(lo)} – {fmt(hi)}"
    if lo is not None: return f"> {fmt(lo)}"
    if hi is not None: return f"< {fmt(hi)}"
    return "—"

def estado(r):
    v, lo, hi = r["v"], r.get("ref_lo"), r.get("ref_hi")
    if not isinstance(v, (int, float)) or (lo is None and hi is None): return None
    if lo is not None and v < lo: return "bajo"
    if hi is not None and v > hi: return "alto"
    return "ok"

def _juicio(d, direccion):
    """Clasifica un cambio numérico d según la dirección favorable del marcador."""
    if direccion == "bajar": return ("favorable", "good") if d < 0 else ("desfavorable", "bad")
    if direccion == "subir": return ("favorable", "good") if d > 0 else ("desfavorable", "bad")
    return ("subió" if d > 0 else "bajó", "muted")

def tendencia(vals, direccion):
    """Devuelve (simbolo, texto, clase). Con ≥3 puntos detecta oscilación (bajó y volvió a subir, o al revés):
    el juicio favorable/desfavorable se hace sobre el último tramo, que es el que importa."""
    nums = [v for v in vals if isinstance(v, (int, float))]
    if len(nums) < 2: return ("", "único valor", "muted")
    a, b = nums[0], nums[-1]
    ref = abs(a) or 1
    if len(nums) >= 3:
        mid_min, mid_max = min(nums[1:-1]), max(nums[1:-1])
        if mid_min < min(a, b) and (min(a, b) - mid_min) / ref >= ESTABLE_REL:
            txt, cls = _juicio(b - mid_min, direccion)
            return ("▼▲", f"bajó y volvió a subir · {txt}", cls)
        if mid_max > max(a, b) and (mid_max - max(a, b)) / ref >= ESTABLE_REL:
            txt, cls = _juicio(b - mid_max, direccion)
            return ("▲▼", f"subió y volvió a bajar · {txt}", cls)
    d = b - a
    if abs(d) / ref < ESTABLE_REL: return ("→", "estable", "muted")
    txt, cls = _juicio(d, direccion)
    return ("▲" if d > 0 else "▼", txt, cls)

def relevancia(m, s, M):
    """Puntaje para ordenar el resumen: fuera de rango > desfavorable > oscilación > resto. Hemograma solo si está fuera de rango."""
    ds = sorted(s); vals = [s[d]["v"] for d in ds]
    sym, txt, cls = tendencia(vals, M[m]["direccion"])
    e = estado(s[ds[-1]])
    nums = [v for v in vals if isinstance(v, (int, float))]
    swing = (max(nums) - min(nums)) / (abs(nums[0]) or 1) if len(nums) >= 2 else 0
    if M[m]["categoria"] == "Hemograma" and e not in ("alto", "bajo"): return None
    if txt == "estable" and e not in ("alto", "bajo"): return None
    score = (3 if e in ("alto", "bajo") else 0) + (2 if cls == "bad" else 0) + (1 if "volvió" in txt else 0) + swing
    return score

def sparkline(points, lo, hi, w=150, h=40):
    """points: [(fecha, v)] numéricos. Banda gris = rango lab. Línea 2px azul, marcadores 7px, último valor etiquetado."""
    pts = [(f, v) for f, v in points if isinstance(v, (int, float))]
    if len(pts) < 2: return ""
    ys = [v for _, v in pts] + [x for x in (lo, hi) if x is not None]
    ymin, ymax = min(ys), max(ys)
    pad = (ymax - ymin) * 0.25 or abs(ymax) * 0.1 or 1
    ymin, ymax = ymin - pad, ymax + pad
    padl, padr, padt, padb = 8, 34, 7, 7
    def X(i): return padl + i * (w - padl - padr) / (len(pts) - 1)
    def Y(v): return padt + (ymax - v) * (h - padt - padb) / (ymax - ymin)
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="tendencia">']
    if lo is not None or hi is not None:
        y1 = Y(hi) if hi is not None else padt
        y2 = Y(lo) if lo is not None else h - padb
        out.append(f'<rect x="{padl}" y="{y1:.1f}" width="{w-padl-padr}" height="{max(y2-y1,1):.1f}" fill="{C["band"]}"/>')
    path = " ".join(f"{'M' if i==0 else 'L'}{X(i):.1f},{Y(v):.1f}" for i, (_, v) in enumerate(pts))
    out.append(f'<path d="{path}" fill="none" stroke="{C["serie"]}" stroke-width="2" stroke-linejoin="round"/>')
    for i, (_, v) in enumerate(pts):
        out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="{C["serie"]}" stroke="{C["surface"]}" stroke-width="2"/>')
    fx, fv = pts[-1]
    out.append(f'<text x="{X(len(pts)-1)+7:.1f}" y="{Y(fv)+4:.1f}" font-size="10" fill="{C["ink2"]}">{fmt(fv)}</text>')
    out.append("</svg>")
    return "".join(out)

def build(data):
    pac = data["paciente"]; M = data["marcadores"]
    exams = sorted(data["examenes"], key=lambda e: e["fecha"])
    labs = [e for e in exams if e["tipo"] == "laboratorio"]
    lab_dates = [e["fecha"] for e in labs]
    # serie por marcador (solo labs) -> {m: {fecha: r}}
    S = {}
    for e in labs:
        for r in e["resultados"]:
            S.setdefault(r["m"], {})[e["fecha"]] = r
    multi = {m: s for m, s in S.items() if len(s) >= 2}
    single = {m: s for m, s in S.items() if len(s) == 1}

    h = []
    h.append(f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Comparativo de exámenes</title>
<style>
@page {{ size: A4; margin: 14mm 12mm; }}
body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color:{C['ink']}; background:{C['surface']}; margin:0; font-size:11px; line-height:1.35; }}
h1 {{ font-size:20px; margin:0 0 2px; }} h2 {{ font-size:14px; margin:18px 0 6px; border-bottom:1px solid {C['grid']}; padding-bottom:3px; page-break-after:avoid; }}
h3 {{ font-size:12px; margin:12px 0 4px; color:{C['ink2']}; page-break-after:avoid; }}
.sub {{ color:{C['ink2']}; margin-bottom:10px; }}
table {{ border-collapse:collapse; width:100%; page-break-inside:auto; }} tr {{ page-break-inside:avoid; }}
th, td {{ text-align:left; padding:4px 6px; border-bottom:1px solid {C['grid']}; vertical-align:middle; }}
th {{ font-size:10px; color:{C['ink2']}; font-weight:600; text-transform:uppercase; letter-spacing:.02em; }}
td.num {{ text-align:right; font-variant-numeric: tabular-nums; white-space:nowrap; }}
.muted {{ color:{C['muted']}; }} .good {{ color:{C['good']}; }} .bad {{ color:{C['bad']}; }} .warn {{ color:{C['warn']}; }}
.flag {{ font-size:10px; white-space:nowrap; }}
.box {{ border:1px solid {C['grid']}; border-radius:6px; padding:8px 10px; margin:6px 0; page-break-inside:avoid; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
.kpi {{ font-size:18px; font-weight:600; }} .kpi small {{ font-size:10px; font-weight:400; color:{C['ink2']}; }}
.legend {{ font-size:10px; color:{C['ink2']}; margin:4px 0 10px; }}
.foot {{ font-size:9.5px; color:{C['muted']}; margin-top:16px; border-top:1px solid {C['grid']}; padding-top:6px; }}
</style></head><body>""")
    h.append(f"<h1>Comparativo de exámenes {lab_dates[0][:4]}–{lab_dates[-1][:4]}</h1>")
    h.append(f"<div class='sub'>{html.escape(pac['nombre'])} · nac. {pac['nacimiento']} · {pac['estatura_cm']} cm · generado {date.today().isoformat()} desde {len(exams)} estudios verificados contra documento original.</div>")
    h.append("<div class='legend'>Tendencia = primer vs último valor. ▲/▼ dirección numérica; <b>favorable / desfavorable</b> según el marcador; → cambio &lt; 5 %. "
             "Estado = contra el rango del laboratorio del último informe. Banda gris en la gráfica = rango del laboratorio.</div>")

    # ---- Resumen: qué se movió ----
    h.append("<h2>1. Qué se movió (marcadores con ≥ 2 mediciones; se omite el hemograma en rango)</h2>")
    movers = []
    for m, s in multi.items():
        sc = relevancia(m, s, M)
        if sc is None: continue
        vals = [s[d]["v"] for d in sorted(s)]
        sym, txt, cls = tendencia(vals, M[m]["direccion"])
        movers.append((sc, m, vals, sym, txt, cls))
    movers.sort(key=lambda x: -x[0])
    h.append("<div class='grid2'>")
    for sc, m, vals, sym, txt, cls in movers:
        last = S[m][max(S[m])]
        est = estado(last)
        est_txt = {"alto": "<span class='bad flag'>● alto vs rango lab</span>", "bajo": "<span class='warn flag'>● bajo vs rango lab</span>", "ok": "<span class='muted flag'>en rango</span>", None: ""}[est]
        h.append(f"<div class='box'><div style='display:flex;justify-content:space-between;align-items:center'><div><b>{M[m]['nombre']}</b> <span class='muted'>{M[m]['unidad']}</span><br>"
                 f"<span class='kpi'>{' → '.join(fmt(v) for v in vals)} <small>{M[m]['unidad']}</small></span><br>"
                 f"<span class='{cls} flag'>{sym} {txt}</span> &nbsp; {est_txt}</div>"
                 f"{sparkline([(d, S[m][d]['v']) for d in sorted(S[m])], last.get('ref_lo'), last.get('ref_hi'))}</div></div>")
    h.append("</div>")

    # ---- Tablas por categoría ----
    h.append("<h2>2. Tabla comparativa completa (laboratorios)</h2>")
    cols = "".join(f"<th class='num'>{d}</th>" for d in lab_dates)
    for cat in CATS:
        rows = [m for m in M if M[m]["categoria"] == cat and m in S]
        if not rows: continue
        h.append(f"<h3>{cat}</h3><table><thead><tr><th>Marcador</th><th>Unidad</th>{cols}<th>Δ total</th><th>Tendencia</th><th>Rango lab (último)</th><th>Estado</th><th>Gráfica</th></tr></thead><tbody>")
        for m in rows:
            s = S[m]; ds = sorted(s)
            vals = [s[d]["v"] for d in ds]
            cells = []
            for d in lab_dates:
                if d in s:
                    r = s[d]; e = estado(r)
                    mark = {"alto": " <span class='bad'>▲</span>", "bajo": " <span class='warn'>▼</span>"}.get(e, "")
                    cells.append(f"<td class='num'>{fmt(r['v'])}{mark}</td>")
                else:
                    cells.append("<td class='num muted'>—</td>")
            nums = [v for v in vals if isinstance(v, (int, float))]
            delta = f"{'+' if nums[-1]-nums[0] >= 0 else ''}{fmt(round(nums[-1]-nums[0], 2))}" if len(nums) >= 2 else "—"
            sym, txt, cls = tendencia(vals, M[m]["direccion"])
            last = s[ds[-1]]; e = estado(last)
            est_txt = {"alto": "<span class='bad'>● alto</span>", "bajo": "<span class='warn'>● bajo</span>", "ok": "<span class='muted'>en rango</span>", None: "<span class='muted'>—</span>"}[e]
            h.append(f"<tr><td><b>{M[m]['nombre']}</b></td><td class='muted'>{M[m]['unidad']}</td>{''.join(cells)}<td class='num'>{delta}</td>"
                     f"<td class='{cls} flag'>{sym} {txt}</td><td class='muted'>{rango(last)}</td><td class='flag'>{est_txt}</td>"
                     f"<td>{sparkline([(d, s[d]['v']) for d in ds], last.get('ref_lo'), last.get('ref_hi'), w=120, h=32)}</td></tr>")
        h.append("</tbody></table>")

    # ---- Estudios no de laboratorio ----
    others = [e for e in exams if e["tipo"] != "laboratorio"]
    if others:
        h.append("<h2>3. Estudios cardiovasculares y de capacidad funcional</h2>")
        for e in others:
            h.append(f"<div class='box'><b>{e['fecha']}</b> · {html.escape(e.get('laboratorio') or '')} · <span class='muted'>{e['tipo']}</span>")
            h.append("<table><thead><tr><th>Parámetro</th><th class='num'>Valor</th><th>Referencia / nota</th></tr></thead><tbody>")
            for r in e["resultados"]:
                h.append(f"<tr><td>{M[r['m']]['nombre']}</td><td class='num'>{fmt(r['v'])} <span class='muted'>{M[r['m']]['unidad']}</span></td><td class='muted'>{html.escape(rango(r))} {html.escape(r.get('nota',''))}</td></tr>")
            h.append("</tbody></table>")
            det = e.get("detalle", {})
            if det.get("conclusion_documentada"):
                h.append("<div style='margin-top:6px'><b>Conclusión documentada:</b> " + "; ".join(html.escape(x) for x in det["conclusion_documentada"]) + "</div>")
            if det.get("advertencia_documentada"):
                h.append(f"<div class='muted'>{html.escape(det['advertencia_documentada'])}</div>")
            h.append("</div>")

    # ---- Baselines ----
    if single:
        h.append("<h2>4. Marcadores con una sola medición (baseline, aún sin comparación)</h2><table><thead><tr><th>Marcador</th><th>Fecha</th><th class='num'>Valor</th><th>Rango lab</th><th>Estado</th></tr></thead><tbody>")
        for m in [m for m in M if m in single]:
            d = next(iter(single[m])); r = single[m][d]; e = estado(r)
            est_txt = {"alto": "<span class='bad'>● alto</span>", "bajo": "<span class='warn'>● bajo</span>", "ok": "<span class='muted'>en rango</span>", None: "<span class='muted'>—</span>"}[e]
            h.append(f"<tr><td><b>{M[m]['nombre']}</b></td><td>{d}</td><td class='num'>{fmt(r['v'])} <span class='muted'>{M[m]['unidad']}</span></td><td class='muted'>{html.escape(rango(r))}</td><td class='flag'>{est_txt}</td></tr>")
        h.append("</tbody></table>")

    h.append("<div class='foot'>Documento generado automáticamente desde el expediente estructurado. Los valores provienen de los informes originales de laboratorio y de los equipos; "
             "las clasificaciones favorable/desfavorable y en rango/fuera de rango son mecánicas (dirección del marcador y rango del propio laboratorio) y no constituyen interpretación médica. "
             "Los rangos de referencia cambian entre informes y laboratorios; se muestra el del último informe. Discutir con el médico tratante.</div>")
    h.append("</body></html>")
    return "\n".join(h), lab_dates

def main():
    data = json.load(open(DATA, encoding="utf-8"))
    doc, dates = build(data)
    base = os.path.join(HERE, f"COMPARATIVO_{dates[0][:4]}_{dates[-1][:4]}")
    with open(base + ".html", "w", encoding="utf-8") as f: f.write(doc)
    print("HTML:", base + ".html")
    chrome = os.environ.get("CHROME") or next((p for p in [
        "/opt/pw-browsers/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("chromium"), shutil.which("google-chrome")] if p and os.path.exists(p)), None)
    if not chrome:
        print("Chromium no encontrado: abre el HTML en el navegador y usa Imprimir → PDF."); return
    r = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                        f"--print-to-pdf={base}.pdf", "file://" + base + ".html"], capture_output=True, text=True, timeout=120)
    print("PDF:", base + ".pdf" if os.path.exists(base + ".pdf") else f"falló: {r.stderr[-400:]}")

if __name__ == "__main__":
    main()
