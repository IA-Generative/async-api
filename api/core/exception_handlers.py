from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.responses import JSONResponse

from api.core.logger import logger
from api.schemas.errors import AppException, InternalServerError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(exc_class_or_status_code=AppException)
    def base_exception_handler(request: Request, exc: AppException) -> JSONResponse:  # noqa: ARG001
        return exc.to_response()

    @app.exception_handler(exc_class_or_status_code=HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(
            f"HTTPException {exc.status_code} on {request.method} {request.url.path} "
            f"| Content-Type={request.headers.get('content-type')} "
            f"| Content-Length={request.headers.get('content-length')} "
            f"| Detail={exc.detail}",
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(exc_class_or_status_code=RequestValidationError)
    def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            f"Validation error on {request.method} {request.url.path} "
            f"| Content-Type={request.headers.get('content-type')} "
            f"| Content-Length={request.headers.get('content-length')} "
            f"| Errors={exc.errors()}",
        )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(exc_class_or_status_code=Exception)
    def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        )
        return InternalServerError(details="Internal server error").to_response()
