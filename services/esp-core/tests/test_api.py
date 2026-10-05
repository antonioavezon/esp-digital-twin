FORBIDDEN_KEYS = {
    "head",
    "efficiency",
    "bep",
    "flow_rate",
    "pressure",
    "frequency",
    "horsepower",
    "rpm",
    "affinity",
    "cavitation",
}

EXPECTED_IDS = {
    "surface",
    "power-supply",
    "vsd",
    "electrical-cable",
    "well",
    "tubing",
    "pump",
    "intake",
    "protector",
    "shaft",
    "motor",
    "reservoir",
    "production-flow",
}

REQUIRED_FIELDS = {
    "id",
    "name",
    "location",
    "location_label",
    "category",
    "description",
    "function",
    "input",
    "output",
    "relation",
    "relations",
    "display_order",
    "extensions",
}


def _keys(value, found):
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(key)
            _keys(item, found)
    elif isinstance(value, list):
        for item in value:
            _keys(item, found)


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "esp-core",
        "status": "healthy",
        "stage": "1C",
        "physics": {"enabled": True, "model": "hydraulics-v0.1", "mode": "static"},
    }


def test_esp_assembly_is_educational_only(client):
    response = client.get("/api/v1/esp")
    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "1A"
    assert body["stage_label"] == "1A — Anatomy"
    assert body["mode"] == "educational"
    assert body["capabilities"] == {
        "simulation": False,
        "physics_engine": False,
        "ai_model": False,
        "control": False,
    }
    assert "Educational / Simulation Environment" in body["disclaimer"]
    assert {item["id"] for item in body["components"]} == EXPECTED_IDS


def test_components_contract(client):
    response = client.get("/api/v1/esp/components")
    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "1A"
    components = body["components"]
    assert {item["id"] for item in components} == EXPECTED_IDS
    for component in components:
        assert REQUIRED_FIELDS <= set(component)
        assert component["extensions"] == {
            "variables": None,
            "sensors": None,
            "states": None,
            "limits": None,
            "equations": None,
            "alarms": None,
            "events": None,
            "predictive_models": None,
        }
        assert component["description"]
        assert component["function"]
    motor = next(item for item in components if item["id"] == "motor")
    assert motor["name"] == "Motor eléctrico"
    assert motor["location_label"] == "Fondo del pozo"
    assert motor["function"] == "Transforma energía eléctrica en energía mecánica."
    assert motor["input"] == "Energía eléctrica."
    assert motor["output"] == "Movimiento rotacional del eje."
    assert motor["relation"] == "Acciona la bomba mediante el eje del conjunto ESP."
    keys = set()
    _keys(body, keys)
    assert keys.isdisjoint(FORBIDDEN_KEYS)


def test_flows_contract(client):
    response = client.get("/api/v1/esp/flows")
    assert response.status_code == 200
    flows = response.json()["flows"]
    energy = [step["component_id"] for step in flows["energy"]["steps"]]
    fluid = [step["component_id"] for step in flows["fluid"]["steps"]]
    assert energy == [
        "power-supply",
        "vsd",
        "electrical-cable",
        "motor",
        "shaft",
        "pump",
    ]
    assert fluid == ["reservoir", "well", "intake", "pump", "tubing", "surface"]
    assert flows["energy"]["steps"][4]["label"] == "Rotación mecánica"
    assert "potencia ni velocidad" in flows["energy"]["description"]
    assert "caudal ni presión" in flows["fluid"]["description"]


def test_relations_point_at_known_components(client):
    components = client.get("/api/v1/esp/components").json()["components"]
    known = {item["id"] for item in components}
    for component in components:
        assert set(component["relations"]) <= known
        assert component["id"] not in component["relations"]
