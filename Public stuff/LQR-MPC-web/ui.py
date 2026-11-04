"""Small helpers shared by the pages: sliders, tables and SVG plots (no matplotlib)."""

import math

import numpy as np
from pyodide.ffi import create_proxy
from pyscript import document


def el(id):
    return document.getElementById(id)


def val(id):
    return float(el(id).value)


def bind(ids, fn, fmt=None):
    """Call fn() on load and whenever any slider or select in ids changes.

    A slider with a <span id="<id>-val"> next to it gets its number shown there.
    """
    fmt = fmt or {}

    def update(*_):
        for i in ids:
            out = el(i + "-val")
            if out is not None:
                f = fmt.get(i, "{:g}")
                out.textContent = f.format(float(el(i).value))
        fn()

    proxy = create_proxy(update)
    for i in ids:
        el(i).addEventListener("input", proxy)
    update()


def done():
    """Reveal the page once the first computation has finished."""
    el("loading").style.display = "none"
    el("app").style.display = ""


def table(header, rows, classes=None):
    out = ["<table><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr>"]
    for i, row in enumerate(rows):
        cls = f' class="{classes[i]}"' if classes and classes[i] else ""
        out.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</table>")
    return "".join(out)


def _ticks(lo, hi, n=5):
    span = hi - lo or 1.0
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 5, 10) if m * mag >= raw), default=mag)
    first = math.ceil(lo / step - 1e-9) * step
    out, x = [], first
    while x <= hi + 1e-9:
        out.append(round(x, 10))
        x += step
    return out


def line_plot(series, xlabel, ylabel, band=None, width=640, height=250,
              ymin=None, ymax=None):
    """series: [(xs, ys, css_class)]. band: half-width of the green 'sensor window'."""
    L, R, T, B = 52, 12, 10, 34
    xs_all = np.concatenate([np.asarray(s[0], float) for s in series])
    ys_all = np.concatenate([np.asarray(s[1], float) for s in series])
    x0, x1 = float(xs_all.min()), float(xs_all.max())
    y0 = float(ys_all.min()) if ymin is None else ymin
    y1 = float(ys_all.max()) if ymax is None else ymax
    if band is not None:
        y0, y1 = min(y0, -band * 1.2), max(y1, band * 1.2)
    pad = 0.06 * ((y1 - y0) or 1.0)
    y0, y1 = (y0 - pad, y1 + pad) if ymin is None else (y0, y1 + pad)
    if x1 == x0:
        x1 = x0 + 1

    def X(x): return L + (x - x0) / (x1 - x0) * (width - L - R)
    def Y(y): return T + (1 - (y - y0) / (y1 - y0)) * (height - T - B)

    p = [f'<svg class="plot" viewBox="0 0 {width} {height}" role="img" aria-label="{ylabel} against {xlabel}">']
    for t in _ticks(y0, y1):
        p.append(f'<line class="gridline" x1="{L}" x2="{width - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
                 f'<text x="{L - 6}" y="{Y(t) + 4:.1f}" text-anchor="end">{t:g}</text>')
    for t in _ticks(x0, x1):
        p.append(f'<text x="{X(t):.1f}" y="{height - B + 16}" text-anchor="middle">{t:g}</text>')
    if band is not None:
        p.append(f'<rect class="band" x="{L}" y="{Y(band):.1f}" width="{width - L - R}" '
                 f'height="{Y(-band) - Y(band):.1f}"/>'
                 f'<line class="limit" x1="{L}" x2="{width - R}" y1="{Y(band):.1f}" y2="{Y(band):.1f}"/>'
                 f'<line class="limit" x1="{L}" x2="{width - R}" y1="{Y(-band):.1f}" y2="{Y(-band):.1f}"/>')
    p.append(f'<line class="axis" x1="{L}" x2="{L}" y1="{T}" y2="{height - B}"/>'
             f'<line class="axis" x1="{L}" x2="{width - R}" y1="{height - B}" y2="{height - B}"/>')
    for xs, ys, cls in series:
        d = "M" + " L".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(xs, ys))
        p.append(f'<path class="s {cls}" d="{d}"/>')
    p.append(f'<text x="{(L + width - R) / 2}" y="{height - 4}" text-anchor="middle">{xlabel}</text>'
             f'<text transform="translate(12,{(T + height - B) / 2}) rotate(-90)" text-anchor="middle">{ylabel}</text>')
    p.append("</svg>")
    return "".join(p)


def track_plot(track, paths, width=640, height=300):
    """The track centerline (grey) with each robot path on top. paths: [(x, y, css_class)]."""
    _, tx, ty, _ = track.geometry()
    allx = np.concatenate([tx] + [np.asarray(p[0]) for p in paths])
    ally = np.concatenate([ty] + [np.asarray(p[1]) for p in paths])
    pad = 30
    x0, x1, y0, y1 = allx.min(), allx.max(), ally.min(), ally.max()
    scale = min((width - 2 * pad) / max(x1 - x0, 1), (height - 2 * pad) / max(y1 - y0, 1))
    ox = (width - scale * (x1 - x0)) / 2
    oy = (height - scale * (y1 - y0)) / 2

    def pts(xs, ys):
        return "M" + " L".join(f"{ox + (a - x0) * scale:.1f},{height - oy - (b - y0) * scale:.1f}"
                               for a, b in zip(xs[::2], ys[::2]))

    p = [f'<svg class="plot" viewBox="0 0 {width} {height}" role="img" aria-label="Track and robot paths">',
         f'<path class="s trk" d="{pts(tx, ty)}"/>']
    for xs, ys, cls in paths:
        p.append(f'<path class="s {cls}" d="{pts(np.asarray(xs), np.asarray(ys))}"/>')
    p.append("</svg>")
    return "".join(p)


def legend(*items):
    return '<p class="legend">' + "".join(
        f'<span><i class="swatch {c}"></i>{t}</span>' for c, t in items) + "</p>"
