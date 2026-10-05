from app.domain.pump import FORBIDDEN_KEYS, get_pump


def _keys(value, found):
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(key)
            _keys(item, found)
    elif isinstance(value, list):
        for item in value:
            _keys(item, found)


def test_pump_contract(client):
    response = client.get("/api/v1/esp/pump")
    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "1B"
    assert body["stage_label"] == "1B — Multistage Centrifugal Pump"
    assert body["overview_component_id"] == "pump"
    assert body["definition"] == "1 etapa = impulsor + difusor."
    assert body["quantitative_model"] is None
    assert body["status"]["simulation"] == "Conceptual only"
    assert body["status"]["physics_engine"] == "Not enabled"
    assert body["status"]["realtime_control"] == "Not enabled"
    assert body["status"]["ai_model"] == "Not enabled"
    assert body["capabilities"]["physics_engine"] is False
    assert body["animation_note"] == "Conceptual animation — not physical RPM"
    assert "Educational representation" in body["stage_count_note"]
    assert body["energy_note"] == "Conceptual energy representation"
    assert len(body["stages"]) == 3
    impeller = body["stages"][0]["components"][0]
    diffuser = body["stages"][0]["components"][1]
    assert impeller["motion"] == "rotating"
    assert diffuser["motion"] == "stationary"
    assert impeller["simple_explanation"] == "El impulsor gira y entrega energía al fluido."
    assert diffuser["simple_explanation"].startswith("El difusor permanece fijo")
    assert "toda la presión" not in diffuser["technical_explanation"]
    keys = set()
    _keys(body, keys)
    assert keys.isdisjoint(FORBIDDEN_KEYS)


def test_pump_stages_and_flow_path(client):
    stages = client.get("/api/v1/esp/pump/stages")
    flow = client.get("/api/v1/esp/pump/flow-path")
    assert stages.status_code == 200
    assert flow.status_code == 200
    assert [item["id"] for item in stages.json()["stages"]] == [
        "stage-1",
        "stage-2",
        "stage-3",
    ]
    assert [step["id"] for step in flow.json()["single_stage"]["steps"]] == [
        "intake",
        "impeller",
        "diffuser",
        "next-stage",
    ]
    assert [step["id"] for step in flow.json()["multistage"]["steps"]] == [
        "intake",
        "stage-1",
        "stage-2",
        "stage-3",
        "discharge",
    ]


def test_anatomy_contract_remains_available(client):
    response = client.get("/api/v1/esp")
    assert response.status_code == 200
    assert response.json()["stage"] == "1A"
    assert response.json()["stage_label"] == "1A — Anatomy"
