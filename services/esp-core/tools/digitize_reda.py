"""Digitaliza fichas REDA desde trazos vectoriales del PDF.

No inventa puntos. Lee ejes y polilíneas con poppler (pdftotext, pdftocairo).
Una ficha entra al catálogo solo si el BEP impreso cae sobre las tres trazas.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FT_TO_M = 0.3048
HP_TO_W = 745.6998715822702
BARREL_M3 = 0.158987294928
SECONDS_PER_DAY = 86400.0

MODEL_RE = re.compile(
    r"([A-Z][A-Z0-9./-]{2,})\s+(\d+)\s*Hz\s*/\s*(\d+)\s*RPM",
)
SERIES_RE = re.compile(r"(\d+)\s*Series")
STAGE_RE = re.compile(r"(\d+)\s*Stage")
SG_RE = re.compile(r"Sp\.\s*Gr\.\s*([0-9.]+)")
RANGE_RE = re.compile(
    r"Optimum Operating Range\s+([0-9,]+)\s*-\s*([0-9,]+)\s*bpd",
)
REV_RE = re.compile(r"Rev\.\s*(\S+)")
WORD_RE = re.compile(
    r'<word xMin="([^"]+)" yMin="([^"]+)" xMax="([^"]+)" yMax="([^"]+)">([^<]*)</word>'
)


def _run(cmd: list[str]) -> str:
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return completed.stdout


def page_count(pdf: Path) -> int:
    info = _run(["pdfinfo", str(pdf)])
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not match:
        raise RuntimeError("pdfinfo no informó el número de páginas")
    return int(match.group(1))


def layout_pages(pdf: Path) -> list[str]:
    text = _run(["pdftotext", "-layout", str(pdf), "-"])
    return [page for page in text.split("\f") if page.strip()]


def bbox_words(pdf: Path, page: int) -> list[tuple[float, float, float, float, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "page.html"
        subprocess.run(
            ["pdftotext", "-bbox-layout", "-f", str(page), "-l", str(page), str(pdf), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        html = target.read_text(errors="replace")
    words = []
    for x0, y0, x1, y1, raw in WORD_RE.findall(html):
        words.append((float(x0), float(y0), float(x1), float(y1), raw.strip()))
    return words


def svg_body(pdf: Path, page: int) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "page.svg"
        subprocess.run(
            ["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(pdf), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        text = target.read_text(errors="replace")
    return text.split("</defs>", 1)[-1]


def _attr(tag: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]*)"', tag)
    return match.group(1) if match else ""


def _apply_transform(tag: str, x_pos: float, y_pos: float) -> tuple[float, float]:
    raw = _attr(tag, "transform")
    if not raw.startswith("matrix("):
        return x_pos, y_pos
    a_coef, b_coef, c_coef, d_coef, e_coef, f_coef = [
        float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", raw)
    ]
    return (
        a_coef * x_pos + c_coef * y_pos + e_coef,
        b_coef * x_pos + d_coef * y_pos + f_coef,
    )


def stroked_segments(body: str) -> dict[str, list[tuple[tuple[float, float], tuple[float, float]]]]:
    paths = re.findall(r"<path\b([^>]*)/?>", body)
    groups: dict[str, list] = {}
    for tag in paths:
        stroke = _attr(tag, "stroke")
        if not stroke:
            continue
        numbers = [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", _attr(tag, "d"))]
        pairs = [_apply_transform(tag, x_pos, y_pos) for x_pos, y_pos in zip(numbers[0::2], numbers[1::2])]
        bucket = groups.setdefault(stroke, [])
        bucket.extend(zip(pairs, pairs[1:]))
    return groups


def _nearest(values: list[float], target: float) -> float:
    return min(values, key=lambda item: abs(item - target))


def _fit_two(p0: tuple[float, float], p1: tuple[float, float]):
    x0, y0 = p0
    x1, y1 = p1
    if abs(x1 - x0) < 1e-6:
        raise ValueError("eje sin longitud")
    slope = (y1 - y0) / (x1 - x0)
    intercept = y0 - slope * x0
    return intercept, slope


def polyline(segments, short_only: bool) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for start, end in segments:
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        if dx < 0.4 and dy < 0.4:
            continue
        if short_only and not (2.0 <= dx <= 45.0):
            continue
        points.extend((start, end))
    if not points:
        return []
    ordered = sorted(points, key=lambda item: (item[0], item[1]))
    merged: list[tuple[float, float]] = []
    for x_pos, y_pos in ordered:
        if merged and abs(merged[-1][0] - x_pos) < 0.6:
            prev_x, prev_y = merged[-1]
            merged[-1] = (prev_x, (prev_y + y_pos) / 2)
            continue
        merged.append((x_pos, y_pos))
    return merged


def _interp(points: list[tuple[float, float]], x_pos: float) -> float | None:
    if len(points) < 2 or x_pos < points[0][0] or x_pos > points[-1][0]:
        return None
    for left, right in zip(points, points[1:]):
        if left[0] <= x_pos <= right[0] and right[0] != left[0]:
            span = (x_pos - left[0]) / (right[0] - left[0])
            return left[1] + span * (right[1] - left[1])
    return None


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def parse_sheet(layout: str) -> dict | None:
    model = MODEL_RE.search(layout)
    stages = STAGE_RE.search(layout)
    series = SERIES_RE.search(layout)
    gravity = SG_RE.search(layout)
    if not (model and stages and series and gravity):
        return None
    if int(stages.group(1)) != 1:
        return None
    values = {}
    for key in ("Q", "H", "P", "E"):
        match = re.search(rf"{key}\s*=\s*([0-9,.]+)", layout)
        if not match:
            return None
        values[key] = _number(match.group(1))
    operating = RANGE_RE.search(layout)
    revision = REV_RE.search(layout)
    manufacturer = "REDA Production Systems" if "REDA Production Systems" in layout else None
    if manufacturer is None:
        return None
    return {
        "model": model.group(1),
        "frequency_hz": int(model.group(2)),
        "speed_rpm": int(model.group(3)),
        "series": series.group(1),
        "stage_count_reference": 1,
        "specific_gravity_reference": float(gravity.group(1)),
        "bep": {
            "flow_bpd": values["Q"],
            "head_ft": values["H"],
            "power_hp": values["P"],
            "efficiency_percent": values["E"],
            "origin": "sheet",
        },
        "operating_range": None
        if operating is None
        else {
            "name": "Optimum Operating Range",
            "flow_min_bpd": _number(operating.group(1)),
            "flow_max_bpd": _number(operating.group(2)),
        },
        "source_revision": None if revision is None else f"Rev. {revision.group(1)}",
        "manufacturer": manufacturer,
    }


def _fit_labels(ticks: list[tuple[float, float]], guides: list[float], horizontal: bool) -> tuple[float, float]:
    if len(ticks) < 2:
        raise ValueError("escala con menos de dos marcas")
    ordered = sorted(ticks, key=lambda item: item[0])
    low = ordered[0]
    high = ordered[-1]
    if horizontal:
        axis_low = _nearest(guides, low[1])
        axis_high = _nearest(guides, high[1])
        return _fit_two((axis_low, low[0]), (axis_high, high[0]))
    axis_low = _nearest(guides, low[1])
    axis_high = _nearest(guides, high[1])
    return _fit_two((axis_low, low[0]), (axis_high, high[0]))


def calibrate(words, segments) -> dict:
    horizontals = []
    verticals = []
    for start, end in segments.get("rgb(0%, 0%, 0%)", []):
        if abs(start[1] - end[1]) < 0.8 and abs(start[0] - end[0]) > 100:
            horizontals.append((start[1] + end[1]) / 2)
        if abs(start[0] - end[0]) < 0.8 and abs(start[1] - end[1]) > 80:
            verticals.append((start[0] + end[0]) / 2)
    if len(horizontals) < 4 or len(verticals) < 4:
        raise ValueError("grilla insuficiente")

    def center(word):
        return ((word[0] + word[2]) / 2, (word[1] + word[3]) / 2)

    head_ticks = []
    power_ticks = []
    eff_ticks = []
    flow_ticks = []
    for word in words:
        label = word[4]
        x_mid, y_mid = center(word)
        if word[1] > 500 and re.fullmatch(r"[0-9,]+", label):
            flow_ticks.append((_number(label), x_mid))
            continue
        if word[2] < 95 and word[1] < 500 and re.fullmatch(r"\d+", label):
            head_ticks.append((float(label), y_mid))
            continue
        if 700 < word[0] < 760 and re.fullmatch(r"\d+\.\d+", label):
            power_ticks.append((_number(label), y_mid))
            continue
        if word[0] > 750 and re.fullmatch(r"\d+%", label):
            eff_ticks.append((_number(label.replace("%", "")), y_mid))
    head_fit = _fit_labels(head_ticks, horizontals, True)
    power_fit = _fit_labels(power_ticks, horizontals, True)
    eff_fit = _fit_labels(eff_ticks, horizontals, True)
    flow_fit = _fit_labels(flow_ticks, verticals, False)
    return {"head": head_fit, "power": power_fit, "efficiency": eff_fit, "flow": flow_fit}


def series_at_flow(points, flow_bpd, flow_fit, value_fit) -> float | None:
    flow_intercept, flow_slope = flow_fit
    if abs(flow_slope) < 1e-9:
        return None
    x_pos = (flow_bpd - flow_intercept) / flow_slope
    y_pos = _interp(points, x_pos)
    if y_pos is None:
        return None
    intercept, slope = value_fit
    return intercept + slope * y_pos


def digitize_page(pdf: Path, page: int, layout: str) -> dict:
    meta = parse_sheet(layout)
    if meta is None:
        raise ValueError("metadatos incompletos")
    words = bbox_words(pdf, page)
    segments = stroked_segments(svg_body(pdf, page))
    axes = calibrate(words, segments)
    black = polyline(segments.get("rgb(0%, 0%, 0%)", []), True)
    blue = polyline(segments.get("rgb(0%, 0%, 100%)", []), False)
    red = polyline(segments.get("rgb(100%, 0%, 0%)", []), False)
    traces = {"black": black, "blue": blue, "red": red}
    if min(len(black), len(blue), len(red)) < 8:
        raise ValueError("una traza no tiene puntos suficientes")
    bep = meta["bep"]
    targets = {
        "head_ft": (bep["head_ft"], axes["head"]),
        "power_hp": (bep["power_hp"], axes["power"]),
        "efficiency_percent": (bep["efficiency_percent"], axes["efficiency"]),
    }
    assignment = {}
    used = set()
    residuals = {}
    for name, (target, value_fit) in targets.items():
        best = None
        for color, points in traces.items():
            if color in used:
                continue
            reading = series_at_flow(points, bep["flow_bpd"], axes["flow"], value_fit)
            if reading is None:
                continue
            error = abs(reading - target)
            if best is None or error < best[0]:
                best = (error, color, reading)
        if best is None:
            raise ValueError(f"no se pudo leer {name} en el caudal del BEP")
        limit = 1.5 if name == "head_ft" else (0.2 if name == "power_hp" else 4.0)
        if best[0] > limit:
            raise ValueError(f"{name} digitalizado {best[2]:.3g} difiere del BEP {target}")
        used.add(best[1])
        assignment[name] = best[1]
        residuals[name] = {"digitized": best[2], "sheet": target, "absolute_error": best[0]}

    value_fits = {
        "head_ft": axes["head"],
        "power_hp": axes["power"],
        "efficiency_percent": axes["efficiency"],
    }

    def pack(color: str, kind: str) -> list[dict]:
        packed = []
        flow_intercept, flow_slope = axes["flow"]
        intercept, slope = value_fits[kind]
        for x_pos, y_pos in traces[color]:
            flow_bpd = flow_intercept + flow_slope * x_pos
            source = intercept + slope * y_pos
            if flow_bpd < -1:
                continue
            packed.append({"flow_bpd": round(flow_bpd, 1), "source": round(source, 4)})
        packed.sort(key=lambda item: item["flow_bpd"])
        return packed

    curves = {
        "head_ft": pack(assignment["head_ft"], "head_ft"),
        "power_hp": pack(assignment["power_hp"], "power_hp"),
        "efficiency_percent": pack(assignment["efficiency_percent"], "efficiency_percent"),
    }
    meta.update(
        {
            "page": page,
            "curve_basis": "per_stage",
            "assignment": assignment,
            "bep_check": residuals,
            "curves": curves,
        }
    )
    return meta


def to_catalog(sheets: list[dict], rejected: list[dict]) -> dict:
    curves = []
    for sheet in sheets:
        curve_id = (
            f"reda-{sheet['model'].lower()}-{sheet['series']}-"
            f"{sheet['frequency_hz']}hz-{sheet['speed_rpm']}rpm-p{sheet['page']}"
        )
        head = []
        power = []
        efficiency = []
        for point in sheet["curves"]["head_ft"]:
            flow_m3s = point["flow_bpd"] * BARREL_M3 / SECONDS_PER_DAY
            head.append(
                {
                    "flow_source": point["flow_bpd"],
                    "value_source": point["source"],
                    "flow_m3_s": flow_m3s,
                    "value_si": point["source"] * FT_TO_M,
                }
            )
        for point in sheet["curves"]["power_hp"]:
            flow_m3s = point["flow_bpd"] * BARREL_M3 / SECONDS_PER_DAY
            power.append(
                {
                    "flow_source": point["flow_bpd"],
                    "value_source": point["source"],
                    "flow_m3_s": flow_m3s,
                    "value_si": point["source"] * HP_TO_W,
                }
            )
        for point in sheet["curves"]["efficiency_percent"]:
            flow_m3s = point["flow_bpd"] * BARREL_M3 / SECONDS_PER_DAY
            efficiency.append(
                {
                    "flow_source": point["flow_bpd"],
                    "value_source": point["source"],
                    "flow_m3_s": flow_m3s,
                    "value_si": point["source"] / 100.0,
                }
            )
        bep = sheet["bep"]
        curves.append(
            {
                "id": curve_id,
                "manufacturer": sheet["manufacturer"],
                "series": sheet["series"],
                "model": sheet["model"],
                "frequency_hz": sheet["frequency_hz"],
                "speed_rpm": sheet["speed_rpm"],
                "stage_count_reference": 1,
                "curve_basis": "per_stage",
                "specific_gravity_reference": sheet["specific_gravity_reference"],
                "flow_unit_source": "bpd",
                "head_unit_source": "ft",
                "power_unit_source": "hp",
                "efficiency_unit_source": "%",
                "source_document": "514839319-Pump-Curve-REDA.pdf",
                "source_page": sheet["page"],
                "source_revision": sheet["source_revision"],
                "source_url": None,
                "source_method": "vector_digitized",
                "data_quality": "approximate_digitization",
                "digitization": {
                    "method": (
                        "Trazos vectoriales del PDF (pdftocairo) calibrados con las "
                        "marcas de caudal, head, hp y eficiencia de la misma ficha."
                    ),
                    "bep_check": sheet["bep_check"],
                    "trace_colors": sheet["assignment"],
                    "warning": "Digitalizada desde curva publicada - valor educativo aproximado",
                    "stated_precision": None,
                },
                "head_flow_points": head,
                "shaft_power_flow_points": power,
                "efficiency_flow_points": efficiency,
                "bep": {
                    "origin": "sheet",
                    "flow_bpd": bep["flow_bpd"],
                    "head_ft": bep["head_ft"],
                    "power_hp": bep["power_hp"],
                    "efficiency_percent": bep["efficiency_percent"],
                    "flow_m3_s": bep["flow_bpd"] * BARREL_M3 / SECONDS_PER_DAY,
                    "head_m": bep["head_ft"] * FT_TO_M,
                    "power_w": bep["power_hp"] * HP_TO_W,
                    "efficiency_fraction": bep["efficiency_percent"] / 100.0,
                },
                "operating_range": sheet["operating_range"],
            }
        )
    return {
        "model": "pump-curves-v0.1",
        "source_document": "514839319-Pump-Curve-REDA.pdf",
        "source_note": (
            "Catálogo digitalizado desde el PDF localizado en el equipo del autor. "
            "No es una curva certificada del fabricante."
        ),
        "curves": curves,
        "rejected_pages": rejected,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python digitize_reda.py RUTA_AL_PDF")
    pdf = Path(sys.argv[1])
    if not pdf.is_file():
        raise SystemExit(f"No se encontró el PDF: {pdf}")
    layouts = layout_pages(pdf)
    accepted = []
    rejected = []
    for index, layout in enumerate(layouts, start=1):
        try:
            accepted.append(digitize_page(pdf, index, layout))
            print(f"OK {index} {accepted[-1]['model']}")
        except Exception as exc:  # noqa: BLE001 — informe de ficha, no de servicio
            rejected.append({"page": index, "reason": str(exc)})
            print(f"NO {index} {exc}")
    catalog = to_catalog(accepted, rejected)
    destination = Path(__file__).resolve().parents[1] / "app" / "curves" / "data" / "reda.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"accepted {len(accepted)} rejected {len(rejected)} -> {destination}")


if __name__ == "__main__":
    main()
