import json
import uuid
import urllib.error
import urllib.request

from django.conf import settings


class EspCoreError(Exception):
    """esp-core no respondió con el contrato esperado."""


class EspCoreClient:
    """Cliente HTTP hacia el dominio. La web no redefine la ESP."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        configured = base_url if base_url is not None else settings.ESP_CORE_BASE_URL
        self.base_url = configured.rstrip("/")
        self.timeout = settings.ESP_CORE_TIMEOUT if timeout is None else timeout

    def get_health(self) -> dict:
        return self._get("/api/v1/health")

    def get_esp(self) -> dict:
        return self._get("/api/v1/esp")

    def get_components(self) -> dict:
        return self._get("/api/v1/esp/components")

    def get_flows(self) -> dict:
        return self._get("/api/v1/esp/flows")

    def get_pump(self) -> dict:
        return self._get("/api/v1/esp/pump")

    def get_pump_stages(self) -> dict:
        return self._get("/api/v1/esp/pump/stages")

    def get_pump_flow_path(self) -> dict:
        return self._get("/api/v1/esp/pump/flow-path")

    def get_physics_constants(self) -> dict:
        return self._get("/api/v1/physics/constants")

    def get(self, path: str) -> dict:
        return self._get(path)

    def post_json(self, path: str, payload: dict) -> tuple[dict, int]:
        url = f"{self.base_url}{path}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return self._parse(url, response.read().decode("utf-8")), response.status
        except urllib.error.HTTPError as exc:
            return self._parse(url, exc.read().decode("utf-8")), exc.code
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EspCoreError(f"{url}: {exc}") from exc

    def post_files(self, path: str, files: list[tuple[str, bytes, str]]) -> tuple[dict, int]:
        boundary = uuid.uuid4().hex
        chunks: list[bytes] = []
        for name, data, content_type in files:
            safe = name.replace('"', "").replace("\r", "").replace("\n", "")
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="files"; filename="{safe}"\r\n'
                f"Content-Type: {content_type or 'application/octet-stream'}\r\n\r\n"
            )
            chunks.append(header.encode("utf-8"))
            chunks.append(data)
            chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(chunks)
        url = f"{self.base_url}{path}"
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return self._parse(url, response.read().decode("utf-8")), response.status
        except urllib.error.HTTPError as exc:
            return self._parse(url, exc.read().decode("utf-8") or "{}"), exc.code
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EspCoreError(f"{url}: {exc}") from exc

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise EspCoreError(f"{url}: {exc}") from exc
        return self._parse(url, raw)

    def _parse(self, url: str, raw: str) -> dict:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EspCoreError(f"{url}: respuesta JSON inválida") from exc
        if not isinstance(data, dict):
            raise EspCoreError(f"{url}: se esperaba un objeto JSON")
        return data
