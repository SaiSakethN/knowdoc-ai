from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from knowdoc.config import settings


class BodyTooLarge(HTTPException):
    def __init__(self):
        super().__init__(413, "request_body_too_large")


class UploadBodyLimit:
    """Bound multipart bytes before Starlette spools an arbitrarily large request."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = settings().max_upload_bytes + 256 * 1024 if scope["path"] == "/api/v1/documents" else 64 * 1024
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = limit + 1
        if declared > limit:
            return await JSONResponse({"error": "request_body_too_large"}, 413)(scope, receive, send)
        total = 0

        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > limit:
                raise BodyTooLarge()
            return message
        try:
            await self.app(scope, bounded_receive, send)
        except BodyTooLarge:
            await JSONResponse({"error": "request_body_too_large"}, 413)(scope, receive, send)
