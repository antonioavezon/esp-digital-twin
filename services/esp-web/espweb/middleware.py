import logging

logger = logging.getLogger("esp.web")


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if path.startswith("/static/") or path == "/health/":
            return response
        logger.info("%s %s", request.method, path if path else "/")
        return response
