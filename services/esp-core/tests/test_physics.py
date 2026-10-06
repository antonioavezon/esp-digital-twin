import pytest

from app.physics.constants import STANDARD_GRAVITY_M_S2
from app.physics.hydraulics import (
    hydraulic_power_from_delta_p,
    hydraulic_power_from_head,
    pressure_difference,
    pressure_to_head,
)
from app.physics.units import (
    BAR_TO_PA,
    BARREL_M3,
    PSI_TO_PA,
    SECONDS_PER_DAY,
    from_cubic_metres_per_second,
    from_pascal,
    to_cubic_metres_per_second,
    to_pascal,
)

BASE = {
    "intake_pressure": {"value": 100, "unit": "psi"},
    "discharge_pressure": {"value": 300, "unit": "psi"},
    "density": {"value": 1000, "unit": "kg/m3"},
    "flow_rate": {"value": 500, "unit": "m3/day"},
}


def test_pressure_difference_identity():
    assert pressure_difference(300.0, 100.0) == 200.0


def test_head_equation():
    delta_p = 10.0 * 1000.0 * STANDARD_GRAVITY_M_S2
    head = pressure_to_head(delta_p, 1000.0, STANDARD_GRAVITY_M_S2)
    assert head == pytest.approx(10.0)


def test_hydraulic_power_equation():
    density = 1000.0
    flow = 0.02
    head = 12.5
    expected = density * STANDARD_GRAVITY_M_S2 * flow * head
    assert hydraulic_power_from_head(density, STANDARD_GRAVITY_M_S2, flow, head) == pytest.approx(expected)


def test_power_equivalence():
    density = 850.0
    flow = 0.004
    delta_p = 250_000.0
    head = pressure_to_head(delta_p, density, STANDARD_GRAVITY_M_S2)
    from_head = hydraulic_power_from_head(density, STANDARD_GRAVITY_M_S2, flow, head)
    from_pressure = hydraulic_power_from_delta_p(flow, delta_p)
    assert from_head == pytest.approx(from_pressure, rel=1e-12)


def test_unit_conversions():
    assert to_pascal(1, "psi") == pytest.approx(PSI_TO_PA)
    assert from_pascal(PSI_TO_PA, "psi") == pytest.approx(1.0)
    assert to_pascal(1, "bar") == pytest.approx(BAR_TO_PA)
    assert from_pascal(BAR_TO_PA, "kPa") == pytest.approx(100.0)
    assert to_cubic_metres_per_second(SECONDS_PER_DAY, "m3/day") == pytest.approx(1.0)
    assert from_cubic_metres_per_second(1.0, "m3/day") == pytest.approx(SECONDS_PER_DAY)
    assert to_cubic_metres_per_second(1, "bpd") == pytest.approx(BARREL_M3 / SECONDS_PER_DAY)
    assert to_pascal(1, "Pa") == pytest.approx(1.0)


def test_hydraulics_api_base_case(client):
    response = client.post("/api/v1/physics/hydraulics", json=BASE)
    assert response.status_code == 200
    body = response.json()
    assert body["physics_model"] == "hydraulics-v0.1"
    assert body["mode"] == "static"
    delta = body["results"]["pressure_difference"]["si_value"]
    head = body["results"]["head"]["si_value"]
    power = body["results"]["hydraulic_power"]["si_value"]
    flow = body["inputs"]["flow_rate"]["si_value"]
    density = body["inputs"]["density"]["si_value"]
    assert delta == pytest.approx(200 * PSI_TO_PA)
    assert head == pytest.approx(delta / (density * STANDARD_GRAVITY_M_S2))
    assert power == pytest.approx(density * STANDARD_GRAVITY_M_S2 * flow * head)
    assert power == pytest.approx(flow * delta, rel=1e-12)
    assert body["inputs"]["intake_pressure"]["source"] == "user_input"
    assert body["inputs"]["intake_pressure"]["role"] == "input"
    assert body["constants"]["gravity"]["source"] == "constant"
    assert body["results"]["head"]["source"] == "physics_model"
    assert body["results"]["head"]["role"] == "calculated"
    assert [step["order"] for step in body["calculation_steps"]] == [1, 2, 3]
    assert "ΔP = P_discharge − P_intake" in body["calculation_steps"][0]["equation"]
    assert body["warnings"] == []
    assert body["results"]["stage_head"] is None
    assert body["notes"]["flow_rate_origin"] == "user_input"


def test_stage_split_is_labeled_as_ideal(client):
    payload = {**BASE, "stages": 4}
    body = client.post("/api/v1/physics/hydraulics", json=payload).json()
    stage = body["results"]["stage_head"]
    assert stage["n_stages"] == 4
    assert stage["si_value"] == pytest.approx(body["results"]["head"]["si_value"] / 4)
    assert "Simplificación ideal" in stage["assumption"]


def test_discharge_not_above_intake_warns(client):
    payload = {
        **BASE,
        "intake_pressure": {"value": 300, "unit": "psi"},
        "discharge_pressure": {"value": 100, "unit": "psi"},
    }
    response = client.post("/api/v1/physics/hydraulics", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["results"]["pressure_difference"]["si_value"] < 0
    assert body["warnings"][0]["code"] == "discharge_not_above_intake"


def test_invalid_inputs_do_not_crash(client):
    negative = client.post(
        "/api/v1/physics/hydraulics",
        json={**BASE, "density": {"value": 0, "unit": "kg/m3"}},
    )
    assert negative.status_code == 422
    flow = client.post(
        "/api/v1/physics/hydraulics",
        json={**BASE, "flow_rate": {"value": -1, "unit": "m3/day"}},
    )
    assert flow.status_code == 422
    unknown = client.post(
        "/api/v1/physics/hydraulics",
        json={**BASE, "intake_pressure": {"value": 10, "unit": "atm"}},
    )
    assert unknown.status_code == 422
    missing = client.post("/api/v1/physics/hydraulics", json={"intake_pressure": {"value": 1, "unit": "psi"}})
    assert missing.status_code == 422
    text = client.post(
        "/api/v1/physics/hydraulics",
        json={**BASE, "flow_rate": {"value": "mucho", "unit": "m3/day"}},
    )
    assert text.status_code == 422
    vacuum = client.post(
        "/api/v1/physics/hydraulics",
        json={**BASE, "intake_pressure": {"value": -2, "unit": "bar"}},
    )
    assert vacuum.status_code == 422


def test_constants_and_compare(client):
    constants = client.get("/api/v1/physics/constants")
    assert constants.status_code == 200
    payload = constants.json()
    assert payload["physics_model"] == "hydraulics-v0.1"
    assert payload["status"]["stage"] == "1C — Basic Hydraulics"
    assert payload["status"]["dynamic_simulation"] == "Not enabled"
    assert len(payload["experiments"]) == 3
    assert "sensor" in payload["reserved_sources"]
    assert "experimental" in payload["reserved_sources"]
    compare_body = {
        "intake_pressure": payload["compare_fluids"]["intake_pressure"],
        "discharge_pressure": payload["compare_fluids"]["discharge_pressure"],
        "flow_rate": payload["compare_fluids"]["flow_rate"],
        "fluids": payload["compare_fluids"]["fluids"],
    }
    compared = client.post("/api/v1/physics/compare", json=compare_body)
    assert compared.status_code == 200
    report = compared.json()
    assert report["pressure_difference_same"] is True
    assert report["head_same"] is False
    heads = [case["result"]["results"]["head"]["si_value"] for case in report["cases"]]
    assert heads[1] > heads[0]


def test_charts_follow_the_same_equations(client):
    response = client.post("/api/v1/physics/charts", json=BASE)
    assert response.status_code == 200
    chart = response.json()
    assert "No es una curva H-Q de bomba." in chart["head_vs_pressure"]["note"]
    point = chart["head_vs_pressure"]["points"][3]
    assert point["y"] == pytest.approx(pressure_to_head(point["x"], 1000.0, STANDARD_GRAVITY_M_S2))
    assert "plot_x" in point
    power_point = chart["power_vs_flow"]["points"][2]
    solved = client.post("/api/v1/physics/hydraulics", json=BASE).json()
    head = solved["results"]["head"]["si_value"]
    assert power_point["y"] == pytest.approx(
        hydraulic_power_from_head(1000.0, STANDARD_GRAVITY_M_S2, power_point["x"], head)
    )


def test_anatomy_and_pump_remain(client):
    assert client.get("/api/v1/esp").json()["stage"] == "1A"
    pump = client.get("/api/v1/esp/pump").json()
    assert pump["stage"] == "1B"
    assert pump["quantitative_model"] is None
