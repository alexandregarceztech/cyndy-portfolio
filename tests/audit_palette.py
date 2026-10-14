#!/usr/bin/env python3
"""
Auditoria Automatizada da Paleta Sky Blue & Limpeza de Cores Antigas.

Varre index.html, style.css e script.js em busca de literais de cor
(#hex, rgb/rgba, hsl/hsla), classifica cada cor por matiz (HSL) e sinaliza
cores "legadas" — tons quentes saturados (vermelho/laranja/rosa/pimenta)
que não pertencem à paleta Sky Blue oficial.

Uso:
    python tests/audit_palette.py          # apenas auditoria (exit 1 se houver legado)
    python tests/audit_palette.py --fix    # substitui cores legadas pelo token Sky Blue mais próximo
"""
import colorsys
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ["style.css", "index.html", "script.js"]

# Paleta oficial Sky Blue (hex -> luminosidade aproximada para mapeamento)
SKY = {
    "base": (0x0E, 0xA5, 0xE9),   # #0ea5e9
    "hover": (0x38, 0xBD, 0xF8),  # #38bdf8
    "deep": (0x02, 0x84, 0xC7),   # #0284c7
    "dark": (0x03, 0x69, 0xA1),   # #0369a1
}

HEX_RE = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([\d.]+%?)\s*)?\)")
HSL_RE = re.compile(r"hsla?\(\s*([\d.]+)(?:deg)?\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*(?:,\s*([\d.]+%?)\s*)?\)")


def parse_hex(h):
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def is_legacy(rgb):
    """Tom quente saturado = cor legada (vermelho/laranja/rosa)."""
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if s < 0.35 or l < 0.12 or l > 0.92:
        return False  # neutros (pretos, off-whites, cinzas quentes) são permitidos
    return hue < 45 or hue > 300


def nearest_sky(rgb):
    _, l, _ = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    name = min(SKY, key=lambda k: abs(colorsys.rgb_to_hls(*(c / 255 for c in SKY[k]))[1] - l))
    return SKY[name]


def scan(fix=False):
    findings, total = [], 0
    for fname in TARGETS:
        path = ROOT / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new_lines = []
        for ln, line in enumerate(text.splitlines(keepends=True), 1):
            def sub_hex(m):
                nonlocal total
                total += 1
                rgb = parse_hex(m.group(1))
                if is_legacy(rgb):
                    findings.append((fname, ln, m.group(0)))
                    if fix:
                        return "#%02x%02x%02x" % nearest_sky(rgb)
                return m.group(0)

            def sub_rgb(m):
                nonlocal total
                total += 1
                rgb = tuple(int(m.group(i)) for i in (1, 2, 3))
                if is_legacy(rgb):
                    findings.append((fname, ln, m.group(0)))
                    if fix:
                        r, g, b = nearest_sky(rgb)
                        a = m.group(4)
                        return f"rgba({r}, {g}, {b}, {a})" if a else f"rgb({r}, {g}, {b})"
                return m.group(0)

            def sub_hsl(m):
                nonlocal total
                total += 1
                h, s, l = float(m.group(1)), float(m.group(2)) / 100, float(m.group(3)) / 100
                rgb = tuple(round(c * 255) for c in colorsys.hls_to_rgb(h / 360, l, s))
                if is_legacy(rgb):
                    findings.append((fname, ln, m.group(0)))
                    if fix:
                        r, g, b = nearest_sky(rgb)
                        a = m.group(4)
                        return f"rgba({r}, {g}, {b}, {a})" if a else f"rgb({r}, {g}, {b})"
                return m.group(0)

            line = HEX_RE.sub(sub_hex, line)
            line = RGB_RE.sub(sub_rgb, line)
            line = HSL_RE.sub(sub_hsl, line)
            new_lines.append(line)
        if fix:
            path.write_text("".join(new_lines), encoding="utf-8")
    return total, findings


def main():
    fix = "--fix" in sys.argv
    total, findings = scan(fix)
    print("=" * 65)
    print(" [AUDITORIA DA PALETA SKY BLUE] - PORTFOLIO CYNDY PIMENTEL")
    print("=" * 65)
    print(f"Literais de cor analisados : {total}")
    print(f"Cores legadas encontradas  : {len(findings)}")
    for f, ln, c in findings:
        print(f"  [{'FIX' if fix else 'LEGADO'}] {f}:{ln} -> {c}")
    if fix and findings:
        print("\nCores legadas substituidas pelo token Sky Blue mais proximo.")
        _, rest = scan(False)
        print(f"Re-auditoria: {len(rest)} cores legadas restantes.")
        return 0 if not rest else 1
    if not findings:
        print("\nPALETA 100% CONFORME! Nenhuma cor legada detectada.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
