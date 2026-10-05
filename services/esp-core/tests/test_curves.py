"""Curvas de desempeño: catálogo REDA verificado y reglas de comparación."""

import pytest

from app.curves.catalog import curve_by_id, index_payload
from app.curves.evaluate import CurveRequestError, interpolate, lab_comparison, present_curve
from app.physics.units import from_metres, from_watts, to_metres
from fastapi.testclient import TestClient

from app.main import app

FIXTURE = {
    "id": "fixture-per-stage",
    "manufacturer": "Fixture",
    "series": "T",
    "model": "TEST",
    "frequency_hz": 60,
    "speed_rpm": 3500,
    "stage_count_reference": 1,
    "curve_basis": "per_stage",
    "specific_gravity_reference": 1.0,
    "source_document": "fixture",
    "source_page": 0,
    "source_revision": None,
    "source_method": "user_supplied",
    "source_url": None,
    "data_quality": "user_supplied",
    "digitization": {"warning": "fixture"},
    "head_flow_points": [
        {"flow_m3_s": 0.01, "value_si": 10.0},
        {"flow_m3_s": 0.02, "value_si": 8.0},
    ],
    "shaft_power_flow_points": [
        {"flow_m3_s": 0.01, "value_si": 1000.0},
        {"flow_m3_s": 0.02, "value_si": 1200.0},
    ],
    "efficiency_flow_points": [
        {"flow_m3_s": 0.01, "value_si": 0.5},
        {"flow_m3_s": 0.02, "value_si": 0.4},
    ],
    "bep": {
        "origin": "sheet",
        "flow_m3_s": 0.01,
        "head_m": 10.0,
        "power_w": 1000.0,
        "efficiency_percent": 50.0,
    },
    "operating_range": {"name": "Optimum Operating Range", "flow_min_bpd": 1000.0, "flow_max_bpd": 2000.0},
}


def test_catalog_lists_only_verified_reda_curves():
    payload = index_payload()
    assert payload["model"] == "pump-curves-v0.1"
    assert payload["curves"]
    manufacturers = {item["manufacturer"] for item in payload["curves"]}
    assert manufacturers == {"REDA Production Systems"}
    for item in payload["curves"]:
        assert item["data_quality"] == "approximate_digitization"
        assert item["source_document"] == "514839319-Pump-Curve-REDA.pdf"
        assert item["source_page"] >= 1
        assert "head_flow_points" not in item


def test_d5800n_matches_the_first_sheet():
    curve = curve_by_id("reda-d5800n-400-60hz-3500rpm-p1")
    assert curve is not None
    assert curve["model"] == "D5800N"
    assert curve["series"] == "400"
    assert curve["frequency_hz"] == 60
    assert curve["speed_rpm"] == 3500
    assert curve["curve_basis"] == "per_stage"
    assert curve["stage_count_reference"] == 1
    assert curve["specific_gravity_reference"] == 1.0
    assert curve["source_page"] == 1
    assert curve["source_revision"] == "Rev. -B"
    assert curve["bep"]["origin"] == "sheet"
    assert curve["bep"]["flow_bpd"] == 5820
    assert curve["bep"]["head_ft"] == 22.63
    assert curve["operating_range"]["name"] == "Optimum Operating Range"
    head = interpolate(curve["head_flow_points"], curve["bep"]["flow_m3_s"])
    power = interpolate(curve["shaft_power_flow_points"], curve["bep"]["flow_m3_s"])
    efficiency = interpolate(curve["efficiency_flow_points"], curve["bep"]["flow_m3_s"])
    assert from_metres(head, "ft") == pytest.approx(22.63, abs=1.5)
    assert from_watts(power, "hp") == pytest.approx(1.38, abs=0.2)
    assert efficiency * 100 == pytest.approx(70.17, abs=4)


def test_dependent_filter_keeps_real_frequency_pairs():
    series_400 = [
        item for item in index_payload()["curves"] if item["series"] == "400" and item["model"] == "D5800N"
    ]
    assert len(series_400) == 1
    assert (series_400[0]["frequency_hz"], series_400[0]["speed_rpm"]) == (60, 3500)


def test_stage_scaling_does_not_multiply_efficiency_or_flow():
    single = present_curve(FIXTURE, stages=1, flow_unit="m3/s", head_unit="m", power_unit="kW")
    scaled = present_curve(FIXTURE, stages=3, flow_unit="m3/s", head_unit="m", power_unit="kW")
    assert scaled["series"]["head"][0]["flow"] == pytest.approx(single["series"]["head"][0]["flow"])
    assert scaled["series"]["head"][0]["value"] == pytest.approx(single["series"]["head"][0]["value"] * 3)
    assert scaled["series"]["shaft_power"][0]["value"] == pytest.approx(single["series"]["shaft_power"][0]["value"] * 3)
    assert scaled["series"]["efficiency"][0]["value"] == pytest.approx(single["series"]["efficiency"][0]["value"])
    assert scaled["bep"]["efficiency_percent"] == 50
    assert scaled["basis"]["code"] == "total_estimate"
    assert single["basis"]["code"] == "per_stage"


def test_missing_stage_count_blocks_total_head_comparison():
    result = lab_comparison(
        FIXTURE,
        stages=None,
        flow_unit="m3/s",
        head_unit="m",
        power_unit="kW",
        flow_m3_s=0.01,
        head_m=30.0,
        hydraulic_power_w=100.0,
        density_kg_m3=1000.0,
    )
    assert result["marker"]["comparable"] is False
    assert any(item["code"] == "per_stage_without_count" for item in result["warnings"])


def test_shaft_estimate_uses_efficiency_and_does_not_replace_curve_power():
    result = lab_comparison(
        FIXTURE,
        stages=2,
        flow_unit="m3/s",
        head_unit="m",
        power_unit="kW",
        flow_m3_s=0.01,
        head_m=20.0,
        hydraulic_power_w=100.0,
        density_kg_m3=1000.0,
    )
    estimate = result["marker"]["shaft_power_estimate"]
    assert estimate["method"] == "Pshaft_estimated = P_hyd / η"
    assert estimate["efficiency_fraction"] == pytest.approx(0.5)
    assert estimate["value"] == pytest.approx(0.2)
    assert result["marker"]["shaft_power_from_curve"] == pytest.approx(2.0)
    assert result["marker"]["hydraulic_power"] == pytest.approx(0.1)
    assert result["marker"]["head"] == pytest.approx(20.0)


def test_outside_range_does_not_extrapolate():
    assert interpolate(FIXTURE["head_flow_points"], 0.05) is None
    result = lab_comparison(
        FIXTURE,
        stages=1,
        flow_unit="m3/s",
        head_unit="m",
        power_unit="kW",
        flow_m3_s=0.05,
        head_m=10.0,
        hydraulic_power_w=100.0,
        density_kg_m3=1000.0,
    )
    assert result["marker"]["shaft_power_estimate"] is None
    assert any(item["code"] == "outside_flow_range" for item in result["warnings"])


def test_unknown_unit_is_rejected():
    with pytest.raises(CurveRequestError):
        present_curve(FIXTURE, stages=1, flow_unit="gpm", head_unit="m", power_unit="kW")


def test_api_returns_three_series_for_d5800n():
    client = TestClient(app)
    response = client.get("/api/v1/physics/curves/reda-d5800n-400-60hz-3500rpm-p1")
    assert response.status_code == 200
    body = response.json()
    assert set(body["series"]) == {"head", "shaft_power", "efficiency"}
    assert len(body["series"]["head"]) >= 8
    assert body["source"]["quality"] == "approximate_digitization"
    assert body["bep"]["origin"] == "sheet"
    assert to_metres(1, "ft") == pytest.approx(0.3048)
