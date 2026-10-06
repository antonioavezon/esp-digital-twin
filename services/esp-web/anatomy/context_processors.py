from anatomy.i18n import TITLES, catalog
from anatomy.preferences import language_of, theme_of
from anatomy.project_metadata import public_context

CURVE_JS_KEYS = (
    "curve_of",
    "curve_head",
    "curve_power",
    "curve_eff",
    "curve_nearest",
    "curve_marker",
    "curve_per_stage",
    "curve_total",
    "curve_bep_sheet",
    "curve_approx",
    "curve_outside",
    "curve_no_compare",
    "curve_estimate",
    "curve_density",
    "curve_empty",
    "curve_wait",
    "curve_sg",
    "curve_source",
    "curve_range",
    "curve_incompatible",
    "curve_none",
    "curve_flow_unit",
)

DRIVE_JS_KEYS = (
    "vsd_current",
    "vsd_result",
    "vsd_empty",
    "vsd_invalid",
)


def project(request):
    lang = language_of(request)
    ui = catalog(lang)
    data = public_context()
    hints = {
        "1A": ui["hint_1a"],
        "1B": ui["hint_1b"],
        "1C": ui["hint_1c"],
        "1D": ui["hint_1d"],
        "1E": ui["hint_1e"],
        "1F": ui["hint_1f"],
        "2-0": ui["hint_20"],
        "2-1": ui["hint_21"],
    }
    statuses = {
        "done": ui["status_done"],
        "planned": ui["status_planned"],
        "current": ui["status_current"],
    }
    data["roadmap"] = [
        {**item, "hint": hints[item["id"]], "status_label": statuses[item["status"]]}
        for item in data["roadmap"]
    ]
    data["philosophy"] = [ui[key] for key in ("phil_1", "phil_2", "phil_3", "phil_4", "phil_5", "phil_6")]
    data["planned_capabilities"] = [ui[key] for key in ("cap_1", "cap_2", "cap_3", "cap_4")]
    return {
        "project": data,
        "ui": ui,
        "lang": lang,
        "theme": theme_of(request),
        "titles": TITLES["en"] if lang == "en" else TITLES["es"],
        "ui_js": {
            "detail_missing": ui["detail_missing"],
            "js_lab": ui["js_lab"],
            "js_compare": ui["js_compare"],
            "js_calc": ui["js_calc"],
            "js_invalid": ui["js_invalid"],
        },
        "curve_ui": {key: ui[key] for key in CURVE_JS_KEYS},
        "drive_ui": {key: ui[key] for key in DRIVE_JS_KEYS},
    }
