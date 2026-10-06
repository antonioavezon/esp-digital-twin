import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from anatomy.client import EspCoreClient, EspCoreError

SCHEMATIC_IDS = (
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
)


def _component(component_id, name):
    return {
        "id": component_id,
        "name": name,
        "location": "downhole",
        "location_label": "Fondo del pozo",
        "category": "mechanical",
        "description": f"SENTINEL-DESC-{component_id}",
        "function": f"Funcion {component_id}",
        "input": "Entrada",
        "output": "Salida",
        "relation": f"Relacion {component_id}",
        "relations": [],
        "display_order": SCHEMATIC_IDS.index(component_id) + 1,
        "extensions": {
            "variables": None,
            "sensors": None,
            "states": None,
            "limits": None,
            "equations": None,
            "alarms": None,
            "events": None,
            "predictive_models": None,
        },
    }


def sample_pump():
    def part(part_type, motion, motion_label):
        return {
            "id": f"stage-1-{part_type}",
            "type": part_type,
            "name": "SENTINEL-IMPELLER" if part_type == "impeller" else "SENTINEL-DIFFUSER",
            "motion": motion,
            "motion_label": motion_label,
            "simple_explanation": f"SENTINEL-SIMPLE-{part_type}",
            "technical_explanation": f"SENTINEL-TECH-{part_type}",
            "receives": "recibe",
            "delivers": "entrega",
        }

    stage = {
        "id": "stage-1",
        "type": "pump_stage",
        "order": 1,
        "name": "SENTINEL-STAGE-1",
        "inlet": "entrada",
        "outlet": "salida",
        "next_label": "Etapa 2",
        "components": [
            part("impeller", "rotating", "GIRA · ROTATING"),
            part("diffuser", "stationary", "FIJO · STATIONARY"),
        ],
    }
    stages = []
    for number in (1, 2, 3):
        item = dict(stage)
        item["id"] = f"stage-{number}"
        item["name"] = f"SENTINEL-STAGE-{number}"
        item["order"] = number
        stages.append(item)
    return {
        "id": "pump-educational-1b",
        "name": "Bomba",
        "stage": "1B",
        "stage_label": "1B — Multistage Centrifugal Pump",
        "overview_component_id": "pump",
        "disclaimer": "Educational / Simulation Environment",
        "definition": "1 etapa = impulsor + difusor.",
        "why_multistage": "SENTINEL-WHY",
        "stage_count_note": "Educational representation — real ESP stage count depends on design.",
        "animation_note": "Conceptual animation — not physical RPM",
        "fluid_path_note": "SENTINEL-FLUID-NOTE",
        "energy_note": "Conceptual energy representation",
        "status": {
            "simulation": "Conceptual only",
            "physics_engine": "Not enabled",
            "realtime_control": "Not enabled",
            "ai_model": "Not enabled",
        },
        "capabilities": {
            "simulation": False,
            "physics_engine": False,
            "ai_model": False,
            "control": False,
        },
        "stages": stages,
        "flow_path": {
            "single_stage": {
                "id": "single-stage",
                "note": "una etapa",
                "steps": [
                    {"order": 1, "id": "intake", "label": "Admisión", "kind": "boundary", "summary": "SENTINEL-INTAKE"},
                    {"order": 2, "id": "impeller", "label": "Impulsor", "kind": "part", "summary": "imp"},
                    {"order": 3, "id": "diffuser", "label": "Difusor", "kind": "part", "summary": "dif"},
                    {"order": 4, "id": "next-stage", "label": "Etapa siguiente", "kind": "boundary", "summary": "next"},
                ],
            },
            "multistage": {
                "id": "multistage",
                "note": "tres etapas",
                "steps": [
                    {"order": 1, "id": "intake", "label": "Admisión", "kind": "boundary", "summary": "SENTINEL-INTAKE"},
                    {"order": 2, "id": "stage-1", "label": "Etapa 1", "kind": "stage", "summary": "s1"},
                    {"order": 3, "id": "stage-2", "label": "Etapa 2", "kind": "stage", "summary": "s2"},
                    {"order": 4, "id": "stage-3", "label": "Etapa 3", "kind": "stage", "summary": "s3"},
                    {"order": 5, "id": "discharge", "label": "Descarga", "kind": "boundary", "summary": "SENTINEL-DISCHARGE"},
                ],
            },
        },
        "energy_marks": [
            {"id": "intake", "label": "Admisión", "order": 1, "blocks": "█", "adds_energy": False},
            {"id": "stage-1", "label": "Etapa 1", "order": 2, "blocks": "██", "adds_energy": True},
        ],
        "quantitative_model": None,
    }


def sample_assembly():
    components = [
        _component(component_id, "SENTINEL-MOTOR" if component_id == "motor" else component_id)
        for component_id in SCHEMATIC_IDS
    ]
    return {
        "id": "esp-educational-1a",
        "name": "Conjunto ESP educativo",
        "stage": "1A",
        "stage_label": "1A — Anatomy",
        "mode": "educational",
        "disclaimer": "Educational / Simulation Environment",
        "capabilities": {
            "simulation": False,
            "physics_engine": False,
            "ai_model": False,
            "control": False,
        },
        "components": components,
        "flows": {
            "energy": {
                "id": "energy",
                "name": "ENERGY FLOW",
                "description": "SENTINEL-ENERGY-FLOW",
                "steps": [
                    {"order": 1, "component_id": "power-supply", "label": "SENTINEL-ENERGY-STEP"},
                    {"order": 2, "component_id": "pump", "label": "Bomba"},
                ],
            },
            "fluid": {
                "id": "fluid",
                "name": "FLUID FLOW",
                "description": "SENTINEL-FLUID-FLOW",
                "steps": [
                    {"order": 1, "component_id": "reservoir", "label": "SENTINEL-FLUID-STEP"},
                ],
            },
        },
    }


def sample_constants():
    request = {
        "intake_pressure": {"value": 100, "unit": "psi"},
        "discharge_pressure": {"value": 300, "unit": "psi"},
        "density": {"value": 1000.0, "unit": "kg/m3"},
        "flow_rate": {"value": 500, "unit": "m3/day"},
    }
    return {
        "physics_model": "hydraulics-v0.1",
        "mode": "static",
        "status": {
            "stage": "1C — Basic Hydraulics",
            "anatomy": "Enabled",
            "pump_internal_view": "Enabled",
            "physics_engine": "hydraulics-v0.1",
            "simulation": "Basic static calculations",
            "dynamic_simulation": "Not enabled",
            "ai_model": "Not enabled",
        },
        "gravity": {"value": 9.80665, "unit": "m/s²", "display": "SENTINEL-G", "source": "constant", "role": "constant"},
        "units": {"pressure": ["pa", "psi"], "flow": ["m3/day"], "density": ["kg/m3"]},
        "experiments": [
            {
                "id": "base-water",
                "name": "Experiment 1 — Base",
                "request": request,
            }
        ],
        "compare_fluids": {
            "fluids": [
                {"name": "Fluid A", "density": {"value": 1000, "unit": "kg/m3"}},
                {"name": "Fluid B", "density": {"value": 850, "unit": "kg/m3"}},
            ]
        },
    }


class CoreDouble:
    def __init__(self):
        self.requests = []
        payload = {
            "/api/v1/health": {
                "service": "esp-core",
                "status": "healthy",
                "stage": "2-1",
                "phase": "2",
                "foundation_stage": "1F",
                "physics": {"enabled": True, "model": "hydraulics-v0.1", "mode": "static"},
                "research": {"enabled": True, "stage": "2-1", "ai_model": False},
            },
            "/api/v1/research/status": {
                "enabled": True,
                "stage": "2-1",
                "ai_model": False,
                "physics_ai": False,
                "anomaly_detection": False,
                "availability": "ready",
                "datasets": ["001"],
            },
            "/api/v1/research/datasets/001": {
                "dataset_id": "001",
                "short_title": "ESP under Gassy Flow Conditions",
                "dataset_doi": "10.17632/fk2b4r69bs.1",
                "source_type": "experimental",
                "files": [
                    {
                        "filename": "Mapping Test Data_zero IPA.xlsx",
                        "size_bytes": 26687,
                        "sha256": "3b933ca84911484f5d912a44b025f5589abaf5ebc2b0426bf80c083869762bda",
                        "sheets": [
                            {
                                "name": "50psig",
                                "row_count": 50,
                                "column_count": 18,
                                "block_count": 2,
                            }
                        ],
                    }
                ],
            },
            "/api/v1/research/datasets/001/preview?file=Mapping%20Test%20Data_zero%20IPA.xlsx&sheet=50psig&block=1&limit=30": {
                "sheet": "50psig",
                "block": 1,
                "columns": [
                    {
                        "index": 1,
                        "name": "Flow rate",
                        "unit": None,
                        "inferred_type": "number",
                        "null_count": 0,
                        "empty": False,
                        "min": 1,
                        "max": 2,
                        "mean": 1.5,
                    }
                ],
                "rows": [[1.5]],
            },
            "/api/v1/research/variables": {"variables": []},
            "/api/v1/research/datasets/001/mapping": {
                "semantic_status": "mapping_in_progress",
                "coverage": {
                    "signatures": 1,
                    "validated": 0,
                    "candidate": 1,
                    "unmapped": 0,
                    "expected": [
                        {
                            "id": "rotary_speed",
                            "symbol": "N",
                            "raw_evidence": ["Rotary Speed (rpm)"],
                            "is_candidate": True,
                            "mapped": False,
                            "validated": False,
                            "state": "candidate",
                        }
                    ],
                },
                "variables": [
                    {
                        "signature_id": "S-rotary-speed-rpm-rpm",
                        "status": "candidate",
                        "confidence": "high",
                        "semantic_role": "condition",
                        "quantity_family": "rotational_speed",
                        "notes": "Condición de ensayo.",
                        "canonical": {"id": "rotary_speed", "symbol": "N", "si_unit": "rad/s"},
                        "raw_hint": None,
                        "evidence": [{"type": "explicit_header", "value": "Rotary Speed (rpm)"}],
                        "source": {
                            "raw_name": "Rotary Speed (rpm)",
                            "raw_unit": "rpm",
                            "group_labels": ["0.75Qbep"],
                            "context_labels": ["1800 rpm", "3500 rpm"],
                            "files": ["Surging Test Data_zero IPA.xlsx"],
                            "sheets": ["50psig"],
                            "occurrences": [
                                {
                                    "file": "Surging Test Data_zero IPA.xlsx",
                                    "sheet": "50psig",
                                    "block_id": "B01",
                                    "column_index": 1,
                                    "primitive_type": "empty",
                                    "example": None,
                                    "min": None,
                                    "max": None,
                                    "group_label": "0.75Qbep",
                                    "experimental_context": {"value": 1800, "unit": "rpm", "source": "header_stack"},
                                    "block_conditions": [],
                                }
                            ],
                        },
                    }
                ],
                "derivable_relations": [],
            },
            "/api/v1/research/datasets/001/stage-2-1-results": {
                "experimental_conditions": [
                    {"type": "sheet_pressure", "value": 50, "unit": "psig"},
                    {"type": "header_condition", "value": 1800, "unit": "rpm"},
                ],
                "experimental_groups": [
                    {"label": "0.75Qbep", "interpretation_status": "hypothesis"}
                ],
                "modeling_feasibility": [
                    {"id": "surging_regime", "status": "potentially_feasible"},
                    {"id": "dynamic_level", "status": "needs_additional_dataset"},
                ],
                "open_questions": [
                    {
                        "id": "Q002",
                        "text": "¿Qué significa exactamente GVF0 y su subíndice 0?",
                        "status": "open",
                        "related_raw": ["GVF0"],
                    }
                ],
            },
            "/api/v1/esp": sample_assembly(),
            "/api/v1/esp/components": {
                "stage": "1A",
                "components": sample_assembly()["components"],
            },
            "/api/v1/esp/flows": {"stage": "1A", "flows": sample_assembly()["flows"]},
            "/api/v1/esp/pump": sample_pump(),
            "/api/v1/esp/pump/stages": {
                "stage": "1B",
                "stage_count_note": sample_pump()["stage_count_note"],
                "definition": sample_pump()["definition"],
                "stages": sample_pump()["stages"],
            },
            "/api/v1/esp/pump/flow-path": {
                "stage": "1B",
                "animation_note": sample_pump()["animation_note"],
                "fluid_path_note": sample_pump()["fluid_path_note"],
                "single_stage": sample_pump()["flow_path"]["single_stage"],
                "multistage": sample_pump()["flow_path"]["multistage"],
            },
            "/api/v1/physics/constants": sample_constants(),
        }
        posts = {
            "/api/v1/physics/hydraulics": {
                "physics_model": "hydraulics-v0.1",
                "mode": "static",
                "inputs": {
                    "intake_pressure": {"display": "SENTINEL-INTAKE-P"},
                    "discharge_pressure": {"display": "SENTINEL-DISCHARGE-P"},
                    "density": {"display": "SENTINEL-RHO"},
                },
                "constants": {"gravity": {"display": "SENTINEL-G"}},
                "results": {
                    "pressure_difference": {"display": "SENTINEL-DP", "role": "calculated"},
                    "head": {"display": "SENTINEL-HEAD", "role": "calculated"},
                    "flow_rate": {"display": "SENTINEL-Q", "role": "input"},
                    "hydraulic_power": {"display": "SENTINEL-POWER", "role": "calculated"},
                    "stage_head": None,
                },
                "calculation_steps": [
                    {
                        "order": 1,
                        "title": "Presión diferencial",
                        "equation": "SENTINEL-EQ",
                        "substitution": "s",
                        "display": "d",
                        "interpretation": "i",
                    },
                    {
                        "order": 2,
                        "title": "Head",
                        "equation": "H",
                        "substitution": "s",
                        "display": "d",
                        "interpretation": "SENTINEL-HEAD-TEXT",
                    },
                ],
                "warnings": [],
            },
            "/api/v1/physics/charts": {
                "head_vs_pressure": {
                    "title": "Head frente a ΔP",
                    "note": "SENTINEL-CHART",
                    "points": [{"plot_x": 0, "plot_y": 0}],
                },
                "power_vs_flow": {
                    "title": "Potencia",
                    "note": "SENTINEL-POWER-CHART",
                    "points": [],
                },
            },
            "/api/v1/physics/compare": {
                "lesson": "SENTINEL-LESSON",
                "pressure_difference_same": True,
                "head_same": False,
                "cases": [],
            },
        }
        requests = self.requests

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                if self.path not in payload:
                    self.send_response(404)
                    self.end_headers()
                    return
                raw = json.dumps(payload[self.path]).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length:
                    self.rfile.read(length)
                requests.append(self.path)
                if self.path not in posts:
                    self.send_response(404)
                    self.end_headers()
                    return
                raw = json.dumps(posts[self.path]).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, fmt, *args):
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.httpd.server_address
        self.base_url = f"http://{host}:{port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


class EspCoreClientTests(SimpleTestCase):
    def setUp(self):
        self.core = CoreDouble()
        self.addCleanup(self.core.close)

    def test_client_reads_health_components_and_flows(self):
        client = EspCoreClient(base_url=self.core.base_url, timeout=2)
        health = client.get_health()
        assembly = client.get_esp()
        components = client.get_components()
        flows = client.get_flows()

        self.assertEqual(health["service"], "esp-core")
        self.assertEqual(assembly["stage"], "1A")
        self.assertEqual(components["components"][0]["id"], "surface")
        self.assertEqual(flows["flows"]["energy"]["name"], "ENERGY FLOW")
        self.assertEqual(
            self.core.requests,
            [
                "/api/v1/health",
                "/api/v1/esp",
                "/api/v1/esp/components",
                "/api/v1/esp/flows",
            ],
        )

    def test_client_reports_unreachable_core(self):
        client = EspCoreClient(base_url="http://127.0.0.1:1", timeout=0.4)
        with self.assertRaises(EspCoreError):
            client.get_health()


class PageTests(SimpleTestCase):
    def setUp(self):
        self.core = CoreDouble()
        self.addCleanup(self.core.close)

    def test_homepage_renders_core_contract(self):
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Entorno educativo, de simulación e investigación", content)
        self.assertIn('"stage": "1A"', content)
        self.assertIn("1A \\u2014 Anatomy", content)
        self.assertIn("1A — Anatomy", content)
        self.assertIn("Anatomía del conjunto - Recorridos", content)
        self.assertIn(">Recorridos</h2>", content)
        self.assertLess(content.find("Componentes - 1A Anatomy"), content.find('id="well-schematic"'))
        self.assertLess(content.find('id="well-schematic"'), content.find(">Recorridos</h2>"))
        self.assertLess(content.find('href="/config/"'), content.find('href="/about/"'))
        self.assertIn('class="app-name" href="/">ESP Digital Twin</a>', content)
        self.assertIn('href="/config/"', content)
        self.assertNotIn("No apto para controlar una ESP real", content)
        self.assertNotIn("Estos mandos no actúan sobre una ESP", content)
        self.assertIn("Recorrido de la electricidad hasta el giro de la bomba", content)
        self.assertIn("Recorrido del fluido desde el reservorio hasta superficie", content)
        self.assertNotIn("<h2>ESP DIGITAL TWIN</h2>", content)
        self.assertIn("Acerca de", content)
        self.assertIn("Laboratorio físico", content)
        self.assertIn("Curvas", content)
        self.assertIn('href="/curves/"', content)
        self.assertIn('href="/about/"', content)
        self.assertNotIn(">Physics Lab<", content)
        self.assertNotIn("Etapa 1A", content)
        self.assertNotIn("sin motor físico", content)
        self.assertNotIn("Etapa posterior", content)
        self.assertNotIn("Activar o ocultar", content)
        self.assertNotIn(">Componente</h2>", content)
        self.assertIn("Panel de control", content)
        self.assertIn('id="esp-start"', content)
        self.assertIn(">Iniciar<", content)
        self.assertIn(">Parar<", content)
        self.assertIn("Estado :", content)
        self.assertIn("Detenido", content)
        self.assertNotIn('id="esp-frequency"', content)
        self.assertNotIn("50 Hz", content)
        self.assertIn('title="Seleccione un componente del esquema o de la lista."', content)
        self.assertIn("Componentes - 1A Anatomy", content)
        self.assertNotIn('class="control-button" disabled', content)
        self.assertIn('id="well-schematic"', content)
        self.assertIn("Variador de frecuencia", content)
        self.assertIn("Sello del motor", content)
        self.assertIn("Eje de transmisión", content)
        self.assertIn("Ver el interior de la bomba", content)
        self.assertIn('href="/pump/"', content)
        self.assertIn("SENTINEL-MOTOR", content)
        self.assertIn("SENTINEL-DESC-motor", content)
        self.assertIn("SENTINEL-ENERGY-FLOW", content)
        self.assertIn("SENTINEL-ENERGY-STEP", content)
        self.assertIn("SENTINEL-FLUID-STEP", content)
        self.assertNotIn("disabled", content)
        for component_id in SCHEMATIC_IDS:
            self.assertIn(f'data-component="{component_id}"', content)
        self.assertIn("/api/v1/esp", "".join(self.core.requests))
        self.assertNotIn("BEP", content)
        self.assertNotIn("horsepower", content)

    def test_homepage_degrades_without_core(self):
        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se pudo obtener la definición de la ESP desde esp-core.")
        self.assertContains(response, "Recorridos")
        self.assertNotContains(response, "SENTINEL-MOTOR")

    def test_health_reflects_core(self):
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "esp-web")
        self.assertEqual(response.json()["esp_core"], "healthy")

        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            degraded = self.client.get("/health/")
        self.assertEqual(degraded.status_code, 503)
        self.assertEqual(degraded.json()["esp_core"], "unreachable")


class PumpPageTests(SimpleTestCase):
    def setUp(self):
        self.core = CoreDouble()
        self.addCleanup(self.core.close)

    def test_client_reads_pump_contract(self):
        client = EspCoreClient(base_url=self.core.base_url, timeout=2)
        pump = client.get_pump()
        stages = client.get_pump_stages()
        flow = client.get_pump_flow_path()
        self.assertEqual(pump["stage"], "1B")
        self.assertEqual(stages["stages"][0]["name"], "SENTINEL-STAGE-1")
        self.assertEqual(flow["single_stage"]["steps"][1]["id"], "impeller")
        self.assertEqual(
            self.core.requests,
            ["/api/v1/esp/pump", "/api/v1/esp/pump/stages", "/api/v1/esp/pump/flow-path"],
        )

    def test_pump_page_renders_core_contract(self):
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/pump/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("SENTINEL-STAGE-1", content)
        self.assertIn("SENTINEL-SIMPLE-impeller", content)
        self.assertIn("SENTINEL-SIMPLE-diffuser", content)
        self.assertIn("GIRA · ROTATING", content)
        self.assertIn("FIJO · STATIONARY", content)
        self.assertIn("Conceptual animation — not physical RPM", content)
        self.assertIn('id="motor"', content)
        self.assertIn('id="pump-drive-hz"', content)
        self.assertIn("pendiente de datos", content)
        self.assertIn("Restablecer 60 Hz", content)
        self.assertIn("Conceptual energy representation", content)
        self.assertIn("Educational representation — real ESP stage count depends on design.", content)
        self.assertIn("Conceptual only", content)
        self.assertIn("Reproducir", content)
        self.assertIn("Pausa", content)
        self.assertIn("Mostrar recorrido del fluido", content)
        self.assertIn("Anterior", content)
        self.assertIn("Siguiente", content)
        self.assertIn("Una etapa", content)
        self.assertIn("Vista multietapa", content)
        self.assertIn("Dibuja una sola etapa con impulsor giratorio y difusor fijo", content)
        self.assertIn("Apila tres etapas didácticas entre la admisión y la descarga", content)
        self.assertIn("Pieza fija que guía el fluido", content)
        self.assertIn('href="/physics/"', content)
        self.assertIn("Acerca de", content)
        self.assertIn('href="/about/"', content)
        self.assertIn("La admisión queda abajo y la descarga arriba. El fluido sube.", content)
        self.assertIn("ENTRADA · DESDE ABAJO", content)
        self.assertIn("SALIDA · SIGUIENTE ETAPA", content)
        self.assertIn("Recorrido de la bomba", content)
        self.assertIn("Avanza paso a paso por el recorrido de la bomba", content)
        self.assertNotIn("Back to ESP Overview", content)
        self.assertNotIn("Explore Physics", content)
        self.assertNotIn("<h2>ESP DIGITAL TWIN</h2>", content)
        self.assertIn("/api/v1/esp/pump", "".join(self.core.requests))

    def test_pump_page_degrades_without_core(self):
        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            response = self.client.get("/pump/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se pudo obtener la descripción de la bomba desde esp-core.")
        self.assertNotContains(response, "SENTINEL-STAGE-1")


class PhysicsPageTests(SimpleTestCase):
    def setUp(self):
        self.core = CoreDouble()
        self.addCleanup(self.core.close)

    def test_physics_page_renders_constants(self):
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/physics/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Laboratorio físico", content)
        self.assertIn('href="/curves/"', content)
        self.assertIn("Abrir Curvas", content)
        self.assertIn('id="lab-drive-hz"', content)
        self.assertIn("pendiente de datos", content)
        self.assertNotIn('id="show-head"', content)
        self.assertNotIn("Physics Lab", content)
        self.assertIn("Experiment 1 — Base", content)
        self.assertIn("Presión del fluido al entrar a la bomba", content)
        self.assertIn("Presión del fluido al salir de la bomba", content)
        self.assertIn("Masa de fluido por cada metro cúbico", content)
        self.assertIn("Caudal que atraviesa la bomba en el ensayo", content)
        self.assertIn("Número de etapas para repartir el head", content)
        self.assertIn("P_intake", content)
        self.assertIn("P_discharge", content)
        self.assertIn("P_hyd", content)
        self.assertIn("H_etapa", content)
        self.assertIn('<select id="stages-value"', content)
        self.assertIn('value="120"', content)
        self.assertIn("Head y potencia de referencia para este caso", content)
        self.assertNotIn("<h2>ESP DIGITAL TWIN</h2>", content)
        self.assertNotIn('class="role"', content)
        self.assertIn("Pulse calcular en Entradas", content)
        self.assertIn("Calcular", content)
        self.assertIn("Mostrar cálculo", content)
        self.assertIn("Comparar fluidos", content)
        self.assertIn("Presión ≠ head", content)
        self.assertNotIn(">ENTRADA<", content)
        self.assertNotIn(">CALCULADO<", content)
        self.assertNotIn(">CONSTANTE<", content)
        self.assertIn("Actividades", content)
        self.assertIn("Presiones alrededor de la bomba", content)
        self.assertNotIn("Volver al interior de la bomba", content)
        self.assertNotIn("Volver al esquema ESP", content)
        self.assertNotIn("Relaciones de la ecuación", content)
        self.assertNotIn("Recorrido pedagógico", content)
        self.assertIn("Acerca de", content)
        self.assertIn('href="/about/"', content)
        self.assertIn("SENTINEL-G", content)
        self.assertIn('value="1000.0"', content)
        self.assertNotIn("1000,0", content)
        self.assertIn("/api/v1/physics/constants", "".join(self.core.requests))

    def test_physics_page_degrades_without_core(self):
        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            response = self.client.get("/physics/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se pudo obtener el motor físico desde esp-core.")
        self.assertNotContains(response, "Experiment 1 — Base")

    def test_proxy_forwards_calculation(self):
        payload = {
            "intake_pressure": {"value": 1, "unit": "psi"},
            "discharge_pressure": {"value": 2, "unit": "psi"},
            "density": {"value": 1000, "unit": "kg/m3"},
            "flow_rate": {"value": 1, "unit": "m3/day"},
        }
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.post(
                "/physics/api/hydraulics/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["head"]["display"], "SENTINEL-HEAD")
        self.assertIn("/api/v1/physics/hydraulics", self.core.requests)

    def test_browser_scripts_do_not_implement_the_equations(self):
        folder = Path(__file__).resolve().parent / "static" / "anatomy" / "physics"
        source = "\n".join(path.read_text(encoding="utf-8") for path in folder.glob("*.js"))
        self.assertNotIn("9.80665", source)
        self.assertNotIn("6894", source)
        self.assertNotIn("86400", source)


class AboutPageTests(SimpleTestCase):
    def setUp(self):
        self.core = CoreDouble()
        self.addCleanup(self.core.close)

    def test_about_page_renders_public_credits(self):
        with override_settings(ESP_CORE_BASE_URL=self.core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("ESP Digital Twin", content)
        self.assertIn("Antonio Ralph Avezon Saavedra", content)
        self.assertIn("Ingeniero en Informática", content)
        self.assertIn("Estudiante del Magíster en Gestión de TI y Telecomunicaciones", content)
        self.assertIn("Universidad Andrés Bello", content)
        self.assertIn("Virtual Research Internship", content)
        self.assertIn(
            "Hybrid Physics-AI Model for Sensorless Monitoring and Anomaly Detection in Electrical Submersible Pump Systems",
            content,
        )
        self.assertIn("Institución de origen.", content)
        self.assertIn("Universidad de los Andes — Colombia", content)
        self.assertIn("Universidad que dirige y supervisa el estudio.", content)
        self.assertIn("Hemispheric University Consortium (HUC)", content)
        self.assertIn("Virtual Research Internship Program", content)
        self.assertIn("Profesor supervisor del proyecto", content)
        self.assertIn("Nicolás Rios Ratkovich — Universidad de los Andes, Colombia", content)
        self.assertIn("La autoría del software corresponde a Antonio Ralph Avezon Saavedra.", content)
        self.assertIn("Stage 2-1", content)
        self.assertIn("Etapa actual", content)
        self.assertIn("Dataset Audit &amp; Variable Mapping", content)
        self.assertIn("hydraulics-v0.1", content)
        self.assertIn("static", content)
        self.assertNotIn("Juan Pablo Vásconez", content)
        self.assertNotIn("Profesor guía UNAB", content)
        self.assertNotIn("Profesor líder VRI", content)
        self.assertNotIn("Project Credits — 1C.1", content)
        self.assertNotIn("Proyecto 12", content)
        self.assertNotIn("Project 12", content)
        self.assertNotIn("no atribuye autoría", content)
        self.assertIn("Python", content)
        self.assertIn("Django", content)
        self.assertIn("Podman", content)
        self.assertIn("Aprendizaje automático", content)
        self.assertIn("Completada", content)
        self.assertIn("Motor de fondo. Potencia, corriente y polos siguen pendientes de datos.", content)
        self.assertIn("Pump Performance Curves", content)
        self.assertIn("Esquema del conjunto sin valores de operación", content)
        self.assertIn("Curvas de la bomba frente al caudal", content)
        self.assertIn("Frecuencia de estudio. No calcula un punto de operación.", content)
        self.assertIn("Qué es la plataforma y cómo avanza por etapas.", content)
        self.assertIn('class="about-columns"', content)
        self.assertNotIn("Volver a ESP Digital Twin", content)
        self.assertNotIn("Back to ESP Digital Twin", content)
        self.assertIn('href="/about/"', content)
        self.assertIn("/api/v1/health", "".join(self.core.requests))
        self.assertNotIn("v1.0", content)
        self.assertNotIn("podman.sock", content)
        self.assertNotIn("DJANGO_SECRET", content)

    def test_about_page_degrades_without_core(self):
        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Antonio Ralph Avezon Saavedra")
        self.assertContains(response, "Stage 2-1")
        self.assertContains(response, "hydraulics-v0.1")


class CurvesPageTests(SimpleTestCase):
    def test_curves_page_offers_three_slots(self):
        response = self.client.get("/curves/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Curvas", content)
        self.assertIn('id="curve-manufacturer"', content)
        self.assertIn('id="curve-series"', content)
        self.assertIn('id="curve-model"', content)
        self.assertIn('id="curve-speed"', content)
        self.assertIn('id="curve-card"', content)
        self.assertNotIn('id="curve-include-1"', content)
        self.assertIn('id="show-head"', content)
        self.assertIn('id="show-power"', content)
        self.assertIn('id="show-eff"', content)
        self.assertIn("3 de 3", content)
        self.assertIn("Potencia de eje", content)
        self.assertIn("Tres curvas del mismo modelo", content)
        self.assertIn("bpd", content)
        self.assertIn(">ft<", content)
        self.assertIn(">hp<", content)
        self.assertIn('id="pump-curve-plot"', content)
        self.assertNotIn("Physics Lab calculated point", content)
        self.assertNotIn("Pump Performance Curves", content)


class ConfigPageTests(SimpleTestCase):
    def test_config_switches_language_and_theme(self):
        response = self.client.post("/config/", {"lang": "en", "theme": "light"})
        self.assertEqual(response.status_code, 302)
        page = self.client.get("/")
        content = page.content.decode()
        self.assertIn('data-theme="light"', content)
        self.assertIn("System anatomy - Tours", content)
        self.assertIn("Status :", content)
        self.assertIn(">Tours</h2>", content)
        self.assertIn("Settings", content)
        self.assertIn(">Curves<", content)
        self.assertIn(">Physics Lab<", content)
        about = self.client.get("/about/")
        self.assertContains(about, "The project")
        self.assertContains(about, "Completed")
        self.assertContains(about, "ESP Digital Twin")


class ResearchPageTests(SimpleTestCase):
    def test_research_page_reads_core_and_keeps_other_routes(self):
        core = CoreDouble()
        self.addCleanup(core.close)
        with override_settings(ESP_CORE_BASE_URL=core.base_url, ESP_CORE_TIMEOUT=2):
            response = self.client.get("/research/")
            content = response.content.decode()
            self.assertEqual(response.status_code, 200)
            self.assertIn("FASE 2", content)
            self.assertIn("2-1 — Auditoría del dataset y mapeo de variables", content)
            self.assertIn("ESP under Gassy Flow Conditions", content)
            self.assertIn("10.17632/fk2b4r69bs.1", content)
            self.assertIn("Mapping Test Data_zero IPA.xlsx", content)
            self.assertIn("3b933ca84911", content)
            self.assertIn("50psig", content)
            self.assertIn("Flow rate", content)
            self.assertIn("Gestor de datos", content)
            self.assertIn("Importar dataset", content)
            self.assertIn("Preproceso", content)
            self.assertIn("Mapeo de variables", content)
            self.assertIn("1800 rpm", content)
            self.assertIn("Factibilidad de investigación", content)
            self.assertIn("Potencialmente estudiable", content)
            self.assertIn("¿Qué significa exactamente GVF0 y su subíndice 0?", content)
            self.assertIn('class="research-split"', content)
            self.assertIn("Analizar", content)
            self.assertIn("Seleccionar archivos", content)
            self.assertIn("Copia RAW, tamaño y SHA-256.", content)
            self.assertNotIn("Estado del proyecto", content)
            self.assertNotIn("La fase 2 es un entorno experimental de investigación.", content)
            self.assertNotIn("1A–1F completado", content)
            for path in ("/", "/pump/", "/physics/", "/curves/", "/about/", "/config/"):
                page = self.client.get(path)
                self.assertEqual(page.status_code, 200, path)

    def test_research_page_degrades_without_core(self):
        with override_settings(ESP_CORE_BASE_URL="http://127.0.0.1:1", ESP_CORE_TIMEOUT=0.4):
            response = self.client.get("/research/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Los datos de investigación no están disponibles.")
        self.assertNotContains(response, "Estado del proyecto")
        self.assertNotContains(response, "La fase 2 es un entorno experimental de investigación.")
